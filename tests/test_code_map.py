"""Static navigation must resolve real links without executing project code."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    'build_code_map', Path(__file__).resolve().parents[1] / 'scripts/build_code_map.py')
code_map = importlib.util.module_from_spec(spec)
spec.loader.exec_module(code_map)


class CodeMapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)

    def records(self):
        data = code_map.build_map(self.root)
        return data, {row['id']: row for row in data['functions']}

    def test_facade_imports_link_to_implementation_without_importing_code(self):
        self.write('workflow/implementation.py', '''raise AssertionError('Must not execute')
def helper():
    return 1
''')
        self.write('workflow/facade.py', 'from .implementation import helper as exported\n')
        self.write('workflow/entry.py', '''from .facade import exported
def main():
    return exported()
''')
        data, rows = self.records()
        self.assertEqual(['workflow.implementation:helper'], rows['workflow.entry:main']['calls'])
        self.assertEqual(['workflow.entry:main'], rows['workflow.implementation:helper']['called_by'])
        self.assertEqual('workflow.implementation:helper', data['aliases']['workflow.facade:exported'])

    def test_nested_functions_and_shadowed_names_are_not_false_parent_edges(self):
        self.write('workflow/logic.py', '''def helper():
    return 1
def outer():
    def inner():
        return helper()
    return inner()
def shadowed(helper):
    return helper()
class Worker:
    def run(self):
        return self.check()
    def check(self):
        return True
''')
        _, rows = self.records()
        self.assertEqual(['workflow.logic:outer.inner'], rows['workflow.logic:outer']['calls'])
        self.assertEqual(['workflow.logic:helper'], rows['workflow.logic:outer.inner']['calls'])
        self.assertEqual([], rows['workflow.logic:shadowed']['calls'])
        self.assertIn('helper', rows['workflow.logic:shadowed']['unresolved_calls'])
        self.assertEqual(['workflow.logic:Worker.check'], rows['workflow.logic:Worker.run']['calls'])

    def test_prompt_keys_and_decorators_are_visible(self):
        self.write('vendor/aideal_engine/src/aideal/prompts.py', 'def load(*args, **kwargs):\n    pass\n')
        self.write('vendor/aideal_engine/src/aideal/author.py', '''@locked
def author(cfg):
    from .prompts import load as prompt
    return prompt(cfg, 'aideal/readme_entry', api_name='f')
''')
        _, rows = self.records()
        author = rows['aideal.author:author']
        self.assertEqual(['aideal/readme_entry'], author['prompts'])
        self.assertEqual(['aideal.prompts:load'], author['calls'])
        self.assertEqual(1, author['line'])
        self.assertTrue(author['source'].startswith('@locked'))

    def test_generated_html_keeps_source_as_data_and_contains_complete_index(self):
        self.write('workflow/example.py', 'def example():\n    return "</script><script>bad()</script>"\n')
        self.write('templates/code_map.html', '<script type="application/json">__CODE_MAP_DATA__</script>')
        data = code_map.generate(self.root)
        html = (self.root / 'docs/CODE_MAP.html').read_text()
        self.assertNotIn('<script>bad()', html)
        self.assertIn('\\u003c/script', html)
        saved = json.loads((self.root / 'docs/function_map.json').read_text())
        self.assertEqual(data, saved)
        self.assertIn('workflow/example.py:1', (self.root / 'docs/FUNCTION_INDEX.md').read_text())

    def test_guided_path_resolves_aliases_and_keeps_unlinked_functions(self):
        self.write('workflow/engine.py', '''def main():
    return helper()
def helper():
    return True
def callback():
    return 'may be called dynamically'
''')
        self.write('workflow/facade.py', 'from .engine import main\n')
        self.write('docs/pipeline_reference.json', json.dumps({
            'stages': [{'id': 'current'}],
            'review_paths': [{'id': 'evaluation', 'extra_stage_ids': [], 'entries': [
                {'id': 'run', 'function': 'workflow.facade:main',
                 'stage_ids': ['current'], 'status': 'implemented'},
                {'id': 'future', 'function': None, 'stage_ids': [],
                 'status': 'not_implemented_end_to_end'}]}]}))
        data, rows = self.records()
        entries = data['review_paths'][0]['entries']
        self.assertEqual('workflow.engine:main', entries[0]['function'])
        self.assertEqual(['workflow.engine:helper'], entries[0]['helper_ids'])
        self.assertEqual([], entries[1]['helper_ids'])
        self.assertIn('workflow.engine:callback', rows)

    def test_github_links_use_real_line_anchors_encode_paths_and_omit_local_root(self):
        self.write('workflow/example file.py', '# leading comment\ndef example():\n    return 1\n')
        self.write('templates/code_map.html', '<script type="application/json">__CODE_MAP_DATA__</script>')
        base = 'https://github.com/ZhuochengShang/AIDEAL/blob/main'
        data = code_map.generate(self.root, github_url=base + '/')
        expected = base + '/workflow/example%20file.py#L2'
        self.assertEqual(expected, data['functions'][0]['source_url'])
        self.assertEqual(base, data['source_base_url'])
        self.assertNotIn('source_root', data)
        for name in ('FUNCTION_INDEX.md', 'function_map.json', 'CODE_MAP.html'):
            content = (self.root / 'docs' / name).read_text()
            self.assertIn(expected, content)
            self.assertNotIn(str(self.root), content)

    def test_github_link_mode_rejects_ambiguous_or_credential_bearing_locations(self):
        for value in ('https://github.com/owner/repo', 'https://secret@github.com/owner/repo/blob/main',
                      'file:///Users/private/repo', 'https://github.com/owner/repo/blob/main?token=secret'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                code_map.generate(self.root, github_url=value)
        self.assertFalse((self.root / 'docs').exists())
        with self.assertRaisesRegex(ValueError, 'not both'):
            code_map.generate(self.root, source_root=self.root,
                              github_url='https://github.com/owner/repo/blob/main')

    def test_guided_path_rejects_broken_or_misleading_entry_points(self):
        data = {'functions': [{'id': 'workflow.engine:main', 'calls': []}],
                'aliases': {}, 'pipeline': {'stages': [{'id': 'current'}]}}
        for entry in [
            {'function': 'workflow.missing:main', 'stage_ids': ['current'], 'status': 'implemented'},
            {'function': 'workflow.engine:main', 'stage_ids': ['missing'], 'status': 'implemented'},
            {'function': None, 'stage_ids': ['current'], 'status': 'implemented'},
        ]:
            with self.subTest(entry=entry):
                data['pipeline']['review_paths'] = [{'id': 'evaluation', 'extra_stage_ids': [],
                    'entries': [{'id': 'run', **entry}]}]
                with self.assertRaises(ValueError):
                    code_map.review_paths(data)


if __name__ == '__main__':
    unittest.main()
