"""No-model checks for source annotations, diagnosis and requirement selection."""
from pathlib import Path
import tempfile
import unittest

from workflow.source_hints import (index_source_hints, insert_source_hint,
                                   render_source_hint, select_source_hints,
                                   strip_source_hints)


class SourceHintTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.original = ('package example\nclass RasterMetadata {\n'
                         '  def rescale(width: Int, height: Int): RasterMetadata = {\n'
                         '    this\n  }\n}\n')
        self.identity = 'RasterMetadata.scala:3:rescale'
        self.fields = {'requirement_id': 'integer_dimensions',
                       'requirement': 'The dimensions must have type Int.',
                       'diagnostic': 'required: Int',
                       'action': 'Pass integer width and height; choose any rounding explicitly.',
                       'validation': 'Compile and verify the resulting dimensions.'}
        self.path = self.root / 'RasterMetadata.scala'
        self.path.write_text(insert_source_hint(self.original, self.identity, self.fields))
        self.mapping = {'example.RasterMetadata.rescale': self.identity}
        self.index = index_source_hints(self.root, ['RasterMetadata.scala'], self.mapping)
        self.code = ('val metadata: RasterMetadata = createMetadata()\n'
                     'metadata.rescale(9.5, 7)\n')
        self.feedback = ('Candidate.scala:2: error: type mismatch;\n'
                         ' found: Double(9.5)\n required: Int\n'
                         'metadata.rescale(9.5, 7)\n                 ^\n')

    def test_signature_coverage_and_source_preserved(self):
        hint = self.index['records'][0]
        self.assertEqual(hint['signature'],
                         '  def rescale(width: Int, height: Int): RasterMetadata')
        self.assertEqual(hint['function_id'], self.identity)
        self.assertEqual(hint['requirement_id'], 'integer_dimensions')
        self.assertEqual(self.index['coverage']['covered_functions'], 1)
        self.assertEqual(strip_source_hints(self.path.read_text()), self.original)
        self.assertIn('    this\n', hint['source_window'])

    def test_compiler_caret_identifies_receiver_and_requirement(self):
        result = select_source_hints(self.index, {'code': self.code, 'feedback': self.feedback})
        self.assertEqual(result['reason'], 'matched')
        self.assertEqual(result['diagnosis']['function_id'], self.identity)
        self.assertEqual(len(result['matched']), 1)

    def test_unit_array_error_does_not_match_integer_requirement(self):
        feedback = self.feedback.replace('Double(9.5)', 'Unit').replace('required: Int', 'required: Array[Double]')
        result = select_source_hints(self.index, {'code': self.code, 'feedback': feedback})
        self.assertEqual(result['reason'], 'requirement_not_covered')
        self.assertEqual(result['matched'], [])

    def test_wrong_owner_same_method_is_not_target_matched(self):
        self.index['api_function_ids']['example.Other.rescale'] = 'Other.scala:3:rescale'
        wrong_code = self.code.replace('RasterMetadata', 'Other')
        result = select_source_hints(self.index, {'code': wrong_code, 'feedback': self.feedback,
                                               'target_apis': list(self.mapping)})
        self.assertEqual(result['reason'], 'function_not_covered')
        self.assertEqual(result['diagnosis']['function_id'], 'Other.scala:3:rescale')
        self.assertEqual(result['matched'], [])

    def test_ambiguous_short_owner_fails_closed(self):
        self.index['api_function_ids']['different.RasterMetadata.rescale'] = 'Other.scala:3:rescale'
        result = select_source_hints(self.index, {'code': self.code, 'feedback': self.feedback})
        self.assertEqual(result['reason'], 'ambiguous_function')
        self.assertEqual(result['matched'], [])

    def test_generic_feedback_and_task_target_are_insufficient(self):
        result = select_source_hints(self.index, {'code': self.code, 'feedback': 'type mismatch;',
                                               'target_apis': list(self.mapping)})
        self.assertEqual(result['reason'], 'unresolved_function')
        with self.assertRaisesRegex(ValueError, 'specific requirement'):
            render_source_hint({**self.fields, 'function_id': self.identity, 'diagnostic': 'type mismatch;'})

    def test_qualified_runtime_frame_localizes_function(self):
        result = select_source_hints(self.index, {'code': self.code,
            'feedback': 'IllegalArgumentException: required: Int\n at example.RasterMetadata.rescale(RasterMetadata.scala:17)'})
        self.assertEqual(result['reason'], 'matched')
        self.assertEqual(result['diagnosis']['evidence'][0]['kind'], 'qualified_stack_frame')

    def test_public_adapter_requirement_must_match_and_remain_public(self):
        public = {'function_id': self.identity, 'requirement_id': 'integer_dimensions',
                  'diagnostic': 'required: Int', 'private_expected': 'MUST_NOT_APPEAR'}
        previous = {'code': self.code, 'feedback': 'required: Int', 'public_failure': public}
        result = select_source_hints(self.index, previous)
        self.assertEqual(result['reason'], 'matched')
        self.assertNotIn('MUST_NOT_APPEAR', str(result))
        public['requirement_id'] = 'different_requirement'
        self.assertEqual(select_source_hints(self.index, previous)['reason'], 'requirement_not_covered')
        public['diagnostic'] = 'private expected value'
        self.assertEqual(select_source_hints(self.index, previous)['reason'], 'invalid_public_failure')

    def test_incomplete_or_empty_program_never_gets_api_hint(self):
        previous = {'code': self.code, 'feedback': self.feedback, 'incomplete': True}
        self.assertEqual(select_source_hints(self.index, previous)['reason'], 'incomplete_model_output')
        previous = {'code': '', 'feedback': self.feedback}
        self.assertEqual(select_source_hints(self.index, previous)['reason'], 'empty_candidate')

    def test_coverage_lists_missing_apis(self):
        mapping = {**self.mapping, 'example.Other.f': 'Other.scala:1:f'}
        coverage = index_source_hints(self.root, [self.path], mapping)['coverage']
        self.assertEqual(coverage['total_functions'], 2)
        self.assertEqual(coverage['uncovered_function_ids'], ['Other.scala:1:f'])

    def test_path_escape_and_symlink_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            other = Path(outside) / 'external.scala'
            other.write_text(self.original)
            (self.root / 'link.scala').symlink_to(other)
            for path in [other, 'link.scala']:
                with self.assertRaisesRegex(ValueError, 'escapes worktree'):
                    index_source_hints(self.root, [path], self.mapping)
        with self.assertRaisesRegex(ValueError, 'inside worktree'):
            insert_source_hint(self.original, '../RasterMetadata.scala:3:rescale', self.fields)

    def test_slash_guidance_rejects_compiler_unicode_escapes_when_rendering(self):
        # Java expands these before recognizing // comments. Even apparently
        # escaped spellings are rejected rather than trusting raw-text equality.
        for escape in (r'\u000a', r'\uuuu000A', r'\u000d', r'\\u000a', r'\u002f'):
            with self.subTest(escape=escape):
                fields = {**self.fields, 'function_id': self.identity,
                          'action': escape + ' static { System.out.println("INJECTED"); } //'}
                with self.assertRaisesRegex(ValueError, 'Unicode escape'):
                    render_source_hint(fields)
                with self.assertRaisesRegex(ValueError, 'Unicode escape'):
                    insert_source_hint(self.original, self.identity, fields)

    def test_existing_slash_guidance_cannot_hide_code_in_unicode_escapes(self):
        for escape in (r'\u000a', r'\uu000D', r'\\u000a'):
            with self.subTest(escape=escape):
                text = self.path.read_text().replace(
                    '// action:', '// action: ' + escape + ' static { runInjected(); } //')
                with self.assertRaisesRegex(ValueError, 'Unicode escape'):
                    strip_source_hints(text)
                self.path.write_text(text)
                with self.assertRaisesRegex(ValueError, 'Unicode escape'):
                    index_source_hints(self.root, [self.path], self.mapping)
                self.path.write_text(insert_source_hint(self.original, self.identity, self.fields))

    def test_python_comment_unicode_text_stays_literal(self):
        original = 'def f(x):\n    return x + 1\n'
        fields = {**self.fields, 'action': r'The literal escape \u000a is input text.'}
        annotated = insert_source_hint(original, 'lib.py:1:f', fields)
        self.assertIn(r'\u000a', annotated)
        self.assertEqual(strip_source_hints(annotated), original)

    def test_code_inside_marker_block_is_rejected(self):
        unsafe = self.path.read_text().replace('// action:', 'runDangerous(); // action:')
        with self.assertRaisesRegex(ValueError, 'only whole-line comments'):
            strip_source_hints(unsafe)

    def test_markers_inside_strings_are_never_stripped(self):
        strings = [
            'text = """\n# AIDEAL-HINT-BEGIN\n# AIDEAL-HINT-END\n"""\n',
            'val text = """\n// AIDEAL-HINT-BEGIN\n// AIDEAL-HINT-END\n"""\n',
            'let text = r#"\n// AIDEAL-HINT-BEGIN\n// AIDEAL-HINT-END\n"#;\n',
            '/*\n// AIDEAL-HINT-BEGIN\n// AIDEAL-HINT-END\n*/\n']
        for source in strings:
            self.assertEqual(strip_source_hints(source), source)

    def test_marker_not_adjacent_to_declaration_rejected(self):
        text = self.path.read_text().replace('  def rescale(', '  val sneaky = 1\n  def rescale(')
        self.path.write_text(text)
        with self.assertRaisesRegex(ValueError, 'between source hint and declaration'):
            index_source_hints(self.root, [self.path], self.mapping)

    def test_missing_duplicate_and_oversized_annotations_rejected(self):
        with self.assertRaisesRegex(ValueError, 'already contains'):
            insert_source_hint(self.path.read_text(), self.identity, self.fields)
        with self.assertRaisesRegex(ValueError, 'Unpaired'):
            strip_source_hints('// AIDEAL-HINT-BEGIN\n')
        text = self.path.read_text().replace('The dimensions must have type Int.', 'x' * 13_000)
        with self.assertRaisesRegex(ValueError, 'bounded annotation'):
            strip_source_hints(text)


    def test_multiple_requirements_share_exact_original_declaration(self):
        text = insert_source_hint(self.path.read_text(), self.identity,
                                  {**self.fields, 'requirement_id': 'positive_dimensions',
                                   'diagnostic': 'dimensions must be positive'})
        self.path.write_text(text)
        index = index_source_hints(self.root, [self.path], self.mapping)
        self.assertEqual(len(index['records']), 2)
        self.assertEqual(len({r['declaration_line'] for r in index['records']}), 1)
        self.assertEqual(strip_source_hints(text), self.original)

    def test_same_method_wrong_baseline_line_is_rejected(self):
        text = self.path.read_text().replace('RasterMetadata.scala:3:rescale',
                                           'RasterMetadata.scala:99:rescale')
        self.path.write_text(text)
        with self.assertRaisesRegex(ValueError, 'baseline line'):
            index_source_hints(self.root, [self.path], self.mapping)

    def test_compiler_wrong_source_echo_does_not_borrow_candidate_location(self):
        feedback = self.feedback.replace('metadata.rescale(9.5, 7)', 'other.different(9.5, 7)')
        result = select_source_hints(self.index, {'code': self.code, 'feedback': feedback})
        self.assertEqual(result['reason'], 'unresolved_function')

    def test_compiler_wrapper_offset_uses_unique_exact_source_echo(self):
        feedback = self.feedback.replace('Candidate.scala:2:', 'DevelopmentProbe.scala:99:')
        result = select_source_hints(self.index, {'code': self.code, 'feedback': feedback})
        self.assertEqual(result['reason'], 'matched')
        location = result['diagnosis']['evidence'][0]
        self.assertEqual(location['line'], 2)
        self.assertEqual(location['diagnostic_line'], 99)

    def test_comments_strings_and_shadowed_types_do_not_supply_receiver_types(self):
        for prefix in ['// val metadata: RasterMetadata = createMetadata()',
                       'val text = "val metadata: RasterMetadata = createMetadata()"',
                       'val metadata: RasterMetadata = createMetadata()\nmetadata = unknownReceiver']:
            code = prefix + '\nmetadata.rescale(9.5, 7)\n'
            result = select_source_hints(self.index, {'code': code, 'feedback': self.feedback})
            self.assertEqual(result['reason'], 'unresolved_function')

    def test_conflicting_compiler_and_stack_attribution_is_ambiguous(self):
        self.index['api_function_ids']['example.Other.rescale'] = 'Other.scala:3:rescale'
        feedback = self.feedback + '\n at example.Other.rescale(Other.scala:17)'
        result = select_source_hints(self.index, {'code': self.code, 'feedback': feedback})
        self.assertEqual(result['reason'], 'ambiguous_function')

    def test_python_java_rust_annotation_insertions_leave_body_intact(self):
        examples = [('sample.py', 'def f(x: int) -> int:\n    return x\n', 'def f(x: int) -> int'),
                    ('Sample.java', 'public static int f(int x) {\n  return x;\n}\n', 'public static int f(int x)'),
                    ('sample.rs', 'pub fn f(x: i32) -> i32 {\n  x\n}\n', 'pub fn f(x: i32) -> i32')]
        for path, original, signature in examples:
            identity = path + ':1:f'
            text = insert_source_hint(original, identity, self.fields)
            (self.root / path).write_text(text)
            index = index_source_hints(self.root, [path], {'sample.f': identity})
            self.assertEqual(strip_source_hints(text), original)
            self.assertEqual(index['records'][0]['signature'], signature)


if __name__ == '__main__':
    unittest.main()
