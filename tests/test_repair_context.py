from pathlib import Path
import tempfile
import unittest

from workflow.repair_context import compact_previous, distill_documentation, public_failure, render_guidance


class RepairContextTests(unittest.TestCase):
    def test_latest_code_and_exact_diagnostic_survive_dedup(self):
        diagnostic = 'Candidate.scala:3: error: type mismatch;\n found: Double\n required: Int\n metadata.rescale(9.5, 7)\n                  ^'
        code = 'val metadata: RasterMetadata = input\n' + 'println(1)\n' * 1000
        result, receipt = compact_previous({'code': code, 'feedback': diagnostic + '\n\n' + diagnostic,
                                            'history': ['PRIVATE_EXPECTATION']})
        self.assertEqual(result, {'code': code, 'feedback': diagnostic})
        self.assertEqual(receipt['repeated_paragraphs_removed'], 1)
        self.assertFalse(receipt['code_truncated'])
        self.assertNotIn('PRIVATE_EXPECTATION', str(result))

    def test_whole_document_blocks_do_not_cut_a_signature_or_fence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'README.md'
            code = '```scala\ndef rescale(width: Int, height: Int): RasterMetadata\n```\n'
            path.write_text(('Background paragraph. ' * 100) + '\n\n' + code + '\nOther notes.\n')
            text, receipt = distill_documentation([path], ['rescale'], 100)
            self.assertIn(code, text)
            self.assertEqual(text.count('```'), 2)
            self.assertTrue(receipt['omitted'])
            self.assertFalse(receipt['truncated'])

    def test_public_failure_requires_public_diagnostic_and_only_approved_fields(self):
        public = {'function_id': 'lib.py:1:f', 'requirement_id': 'numeric', 'diagnostic': 'required numeric'}
        self.assertEqual(public_failure({'public_failure': public, 'public_feedback': 'required numeric'}), public)
        self.assertIsNone(public_failure({'public_failure': public, 'public_feedback': None}))
        self.assertIsNone(public_failure({'public_failure': public, 'public_feedback': 'generic failure'}))
        self.assertIsNone(public_failure({'public_failure': {**public, 'expected': 'SECRET'}, 'public_feedback': 'required numeric'}))

    def test_source_guidance_is_whole_or_explicitly_omitted(self):
        hint = {'function_id': 'lib.py:1:f', 'requirement_id': 'numeric', 'signature': 'def f(x: int)',
                'requirement': 'x must be an integer', 'action': 'Pass an integer.', 'validation': 'Rerun checks.'}
        selection = {'matched': [hint], 'diagnosis': {'status': 'identified'}, 'reason': 'matched'}
        text, receipt = render_guidance(selection, 1000)
        for field in ('signature', 'requirement', 'action'):
            self.assertIn(hint[field], text)
        text, receipt = render_guidance(selection, 10)
        self.assertEqual(text, '')
        self.assertEqual(len(receipt['omitted']), 1)
        self.assertFalse(receipt['truncated'])

    def test_nested_shorter_fence_stays_in_one_atomic_block(self):
        from workflow.repair_context import _blocks
        block = '````markdown\n```scala\n\ndef f(x: Int)\n```\n````\n'
        self.assertEqual(_blocks(block), [block])
