"""Duplicate evidence is static, conservative, and comparable only within its scope."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from workflow.source_duplicates import compare_duplicate_reports, scan_duplicates


PYTHON_BODY = '''def NAME(value, scale=2):
    result = transform(value, scale)
    audit(result)
    return result
'''
LEXICAL = {
    'scala': '''def NAME(x: Int): Int = {
    val shifted = x + 2
    val scaled = shifted * GLOBAL
    println("evidence { preserved }")
    scaled + 4
  }''',
    'java': '''public int NAME(int x) {
    int shifted = x + 2;
    int scaled = shifted * GLOBAL;
    log("evidence { preserved }");
    return scaled + 4;
  }''',
    'rust': '''pub fn NAME(x: i32) -> i32 {
    let shifted = x + 2;
    let scaled = shifted * GLOBAL;
    log(r#"evidence { preserved }"#);
    scaled + 4
}''',
}


class SourceDuplicateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-duplicates-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def python_pair(self, name='src/api.py'):
        return self.write(name, PYTHON_BODY.replace('NAME', 'first') + '\n' +
                          PYTHON_BODY.replace('NAME', 'second'))

    def test_python_keeps_free_names_literals_signatures_and_never_executes_source(self):
        text = 'raise AssertionError("target code must never run")\n'
        text += PYTHON_BODY.replace('NAME', 'first') + PYTHON_BODY.replace('NAME', 'second')
        text += PYTHON_BODY.replace('NAME', 'different_global').replace('transform(', 'other_transform(')
        text += PYTHON_BODY.replace('NAME', 'different_default').replace('scale=2', 'scale=3')
        text += PYTHON_BODY.replace('NAME', 'renamed_argument').replace('value', 'other_value')
        text += '@decorated\n' + PYTHON_BODY.replace('NAME', 'different_decorator')
        text += PYTHON_BODY.replace('NAME', 'different_type_comment').replace('scale=2):', 'scale=2):  # type: (str, int) -> str')
        text += 'def delegate(value, scale=2):\n    return first(value, scale)\n'
        text += 'def empty():\n    pass\n'
        path = self.write('src/api.py', text)
        original = path.read_bytes()
        report = scan_duplicates(self.root)
        self.assertEqual([], report['errors'])
        self.assertEqual(1, report['counts']['duplicate_groups'])
        group = report['groups'][0]
        self.assertEqual({'first', 'second'}, {m['name'] for m in group['members']})
        self.assertEqual('exact_ast_signature_and_body', group['method'])
        self.assertTrue(group['requires_semantic_review'])
        self.assertIn('thin delegation', group['suggestion']['alias_policy'])
        self.assertEqual(3, len(group['suggestion']['required_checks']))
        self.assertTrue(all(m['path'] == 'src/api.py' and m['end_line'] > m['line'] for m in group['members']))
        self.assertEqual(2, report['coverage']['by_language']['python']['trivial_or_abstract_functions_skipped'])
        self.assertEqual(original, path.read_bytes())
        json.dumps(report)  # Public reports are directly serializable, with no AST/Path objects.

    def test_methods_preserve_receiver_and_return_annotations(self):
        method = '''    def NAME(self, value: int) -> int:
        result = self.transform(value)
        self.audit(result)
        return result
'''
        self.write('ops.py', 'class Ops:\n' + method.replace('NAME', 'first') +
                   method.replace('NAME', 'second') + method.replace('NAME', 'different').replace('-> int', '-> str'))
        report = scan_duplicates(self.root)
        self.assertEqual({'Ops.first', 'Ops.second'}, {m['name'] for m in report['groups'][0]['members']})
        self.assertTrue(all(m['kind'] == 'method' for m in report['functions']))

    def test_lexical_languages_keep_literals_globals_and_signature_tokens(self):
        for language, body in LEXICAL.items():
            functions = [body.replace('NAME', 'first'), body.replace('NAME', 'second'),
                         body.replace('NAME', 'different_literal').replace('x + 2', 'x + 3'),
                         body.replace('NAME', 'different_global').replace('GLOBAL', 'OTHER_GLOBAL'),
                         body.replace('NAME', 'different_signature').replace('x: Int', 'x: Long').replace('int x', 'long x').replace('x: i32', 'x: i64')]
            source = '\n'.join(functions)
            if language != 'rust':
                source = ('object' if language == 'scala' else 'class') + ' Ops {\n' + source + '\n}'
            self.write('Ops.' + {'rust': 'rs'}.get(language, language), source)
        report = scan_duplicates(self.root)
        self.assertEqual([], report['errors'])
        self.assertEqual(3, report['counts']['duplicate_groups'])
        self.assertEqual({'scala', 'java', 'rust'}, {g['language'] for g in report['groups']})
        for group in report['groups']:
            self.assertEqual({'first', 'second'}, {m['name'] for m in group['members']})
            self.assertTrue(group['requires_semantic_review'])
            self.assertEqual('partial_braced_extraction', report['coverage']['by_language'][group['language']]['coverage'])

    def test_after_thin_delegation_reports_observed_reduction_without_proving_semantics(self):
        path = self.python_pair()
        before = scan_duplicates(self.root, source_globs=['src/**/*.py'])
        path.write_text(PYTHON_BODY.replace('NAME', '_shared') + '''
def first(value, scale=2):
    return _shared(value, scale)
def second(value, scale=2):
    return _shared(value, scale)
''')
        after = scan_duplicates(self.root, source_globs=['src/**/*.py'])
        comparison = compare_duplicate_reports(before, after)
        self.assertTrue(comparison['comparable'])
        self.assertEqual(1, comparison['before']['duplicate_groups'])
        self.assertEqual(0, comparison['after']['duplicate_groups'])
        self.assertEqual({'duplicate_groups': 1, 'functions_in_groups': 2, 'redundant_instances': 1}, comparison['reduction'])
        self.assertNotEqual(before['input_sha256'], after['input_sha256'])
        self.assertIn('does not prove equivalent behavior', comparison['interpretation'])
        self.assertEqual(2, after['coverage']['by_language']['python']['trivial_or_abstract_functions_skipped'])

    def test_scope_globs_exclusions_and_symlink_escapes(self):
        self.python_pair('src/api.py')
        self.python_pair('src/nested/api.py')
        for directory in ('vendor', '.aideal', 'build', 'target', '.git'):
            if directory != '.git':  # An invalid Git repository must be rejected, not treated as a source tree.
                self.python_pair(directory + '/hidden.py')
        report = scan_duplicates(self.root, source_globs=['src/*.py'])
        self.assertEqual(['src/api.py'], [f['path'] for f in report['inputs']])
        recursive = scan_duplicates(self.root, source_globs=['src/**/*.py'])
        self.assertEqual(2, recursive['coverage']['scanned_files'])
        with tempfile.TemporaryDirectory() as outside:
            foreign = Path(outside) / 'foreign.py'
            foreign.write_text(PYTHON_BODY.replace('NAME', 'foreign'))
            (self.root / 'escape.py').symlink_to(foreign)
            (self.root / 'escape_directory').symlink_to(outside, target_is_directory=True)
            report = scan_duplicates(self.root)
        self.assertEqual(2, report['coverage']['scanned_files'])
        self.assertEqual({'escape.py', 'escape_directory'}, {e['path'] for e in report['errors']})
        self.assertTrue(all(r['sha256'] is None for r in report['inputs'] if r['status'] == 'error'))

    @unittest.skipUnless(shutil.which('git'), 'Git is needed for tracked-source selection')
    def test_git_scans_only_tracked_working_tree_sources(self):
        self.python_pair('src/api.py')
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.root), 'add', 'src/api.py'], check=True, capture_output=True)
        self.python_pair('untracked.py')
        self.python_pair('vendor/hidden.py')
        report = scan_duplicates(self.root)
        self.assertEqual('git_tracked_worktree', report['scope']['selection'])
        self.assertEqual(['src/api.py'], [f['path'] for f in report['inputs']])
        self.assertIsNone(report['repository']['git_revision'])  # An unborn repo remains a tracked scan.
        (self.root / 'src/api.py').unlink()
        missing = scan_duplicates(self.root)
        comparison = compare_duplicate_reports(report, missing)
        self.assertFalse(comparison['comparable'])
        self.assertIsNone(comparison['reduction'])

    def test_comparison_rejects_parse_failure_and_changed_analyzer_settings_scope(self):
        path = self.python_pair()
        before = scan_duplicates(self.root)
        path.write_text('def broken(:\n')
        failed = scan_duplicates(self.root)
        self.assertEqual('SyntaxError', failed['errors'][0]['type'])
        comparison = compare_duplicate_reports(before, failed)
        self.assertFalse(comparison['comparable'])
        self.assertIsNone(comparison['reduction'])
        self.assertEqual(0, comparison['after']['duplicate_groups'])
        for field in ('analyzer', 'settings', 'scope'):
            changed = deepcopy(before)
            changed[field]['changed'] = True
            with self.subTest(field=field):
                comparison = compare_duplicate_reports(before, changed)
                self.assertFalse(comparison['comparable'])
                self.assertIn('Incompatible or missing ' + field, comparison['reasons'])
        malformed = deepcopy(before)
        malformed['counts'] = {}
        self.assertFalse(compare_duplicate_reports(before, malformed)['comparable'])
        moved = deepcopy(before)
        moved['repository']['root'] = '/another/worktree'
        self.assertTrue(compare_duplicate_reports(before, moved)['comparable'])

    def test_lexical_errors_empty_scope_and_bad_globs_do_not_claim_success(self):
        empty = scan_duplicates(self.root)
        self.assertFalse(compare_duplicate_reports(empty, empty)['comparable'])
        self.write('broken.java', 'class Broken { public int f(int x) { return x;')
        self.write('broken.rs', 'fn f() { let x = r#"not closed; }')
        failed = scan_duplicates(self.root)
        self.assertEqual(2, failed['coverage']['failed_files'])
        self.assertIsNone(compare_duplicate_reports(failed, failed)['reduction'])
        for globs in ('*.py', [], ['../outside.py'], ['/absolute.py'], ['']):
            with self.subTest(globs=globs), self.assertRaises(ValueError):
                scan_duplicates(self.root, source_globs=globs)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'Platform does not provide named pipes')
    def test_special_files_are_reported_without_blocking_on_read(self):
        os.mkfifo(self.root / 'input.py')
        report = scan_duplicates(self.root)
        self.assertEqual(1, report['coverage']['failed_files'])
        self.assertIn('not a regular file', report['errors'][0]['message'])
        self.assertIsNone(report['inputs'][0]['sha256'])


if __name__ == '__main__':
    unittest.main()
