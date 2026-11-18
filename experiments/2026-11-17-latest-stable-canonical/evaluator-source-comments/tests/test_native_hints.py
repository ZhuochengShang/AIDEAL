"""Execute message-only patches and prove repair prompts do not retrieve hints."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from workflow.ablation import bind, load
from workflow.native_hints import (patch_message, patch_messages, prepare_native_hints, validate_native_hints,
                                  verify_native_validation, install_native_hints, native_feedback_receipt)

SOURCE = ('def resize(width, height):\n'
          '    if width <= 0:\n'
          '        raise ValueError("Width must be positive.")\n'
          '    if height <= 0:\n'
          '        raise ValueError("Height must be positive.")\n'
          '    return [width, height]\n')

ADAPTER = r'''
import hashlib, json, pathlib, sys
request = json.load(sys.stdin)
source = pathlib.Path(request['source_root']) / 'lib.py'
if request['source_overrides']:
    source = pathlib.Path(request['source_overrides']['lib.py']['path'])
namespace = {}
exec(compile(source.read_text(), str(source), 'exec'), namespace)
target = namespace['resize']
reached = [False]
def tracked(*args):
    reached[0] = True
    return target(*args)
namespace['resize'] = tracked
context = json.loads(pathlib.Path(request['checker_context_path']).read_text())
try:
    exec(compile(request['code'], '<candidate>', 'exec'), namespace)
    result = namespace['result']
    payload = {'execution_pass': True, 'oracle_pass': result == context[request['role']],
               'error_type': '', 'error_message': '', 'public_feedback': '',
               'result_sha256': hashlib.sha256(json.dumps(result).encode()).hexdigest()}
except Exception as exc:
    payload = {'execution_pass': False, 'oracle_pass': False,
               'error_type': type(exc).__name__, 'error_message': str(exc),
               'public_feedback': type(exc).__name__ + ': ' + str(exc)}
payload['target_reached'] = reached[0]
payload['request_sha256'] = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
print(json.dumps(payload))
'''


class NativeHintTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-native-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.baseline = self.root / 'baseline'
        self.baseline.mkdir()
        self.source = self.baseline / 'lib.py'
        self.source.write_text(SOURCE)
        self.hint = {'function_id': 'lib.py:1:resize', 'requirement_id': 'positive_width',
                     'error_line': 3, 'original_message': 'Width must be positive.',
                     'action': 'Pass a width greater than zero.', 'evidence_id': 'dev-width',
                     'source_quote': 'if width <= 0:', 'trigger_code': 'result = resize(0, 5)',
                     'corrected_code': 'result = resize(10, 5)'}
        self.spec = self.root / 'spec.json'
        self.spec.write_text(json.dumps({'schema_version': 1, 'split': 'development',
                                        'source_sha256': {'lib.py': bind(self.source)['sha256']}, 'hints': [self.hint]}))
        self.adapter = self.root / 'adapter.py'
        self.adapter.write_text(ADAPTER)
        self.valid, self.nearby, self.context = [self.root / p for p in ('valid.py', 'nearby.py', 'oracle.json')]
        self.valid.write_text('result = resize(8, 4)')
        self.nearby.write_text('result = resize(5, 0)')
        self.context.write_text(json.dumps({'corrected': [10, 5], 'valid': [8, 4]}))
        self.plan = self.root / 'plan.json'
        self.plan.write_text(json.dumps({'schema_version': 1, 'split': 'development',
            'adapter': {'command': [sys.executable, str(self.adapter)], 'timeout_s': 10, 'artifacts': [bind(self.adapter)]},
            'controls': {'dev-width': {'valid_code': bind(self.valid), 'nearby_code': bind(self.nearby),
                                      'checker_context': bind(self.context)}}}))

    def prepare(self):
        return prepare_native_hints(self.baseline, self.spec, self.root / 'proposal')['proposal']

    def validate(self):
        proposal = self.prepare()
        result = validate_native_hints(proposal, self.plan, self.root / 'validation')
        self.assertEqual(result['status'], 'validated')
        return result['validation']

    def test_real_execution_preserves_valid_results_and_unrelated_error(self):
        validation = self.validate()
        receipt = load(validation)
        self.assertEqual(len(receipt['records']), 8)
        self.assertTrue(all(row['valid'] for row in receipt['checks']))
        proposal = verify_native_validation(validation)
        self.assertEqual(self.source.read_text(), SOURCE)
        edited = Path(proposal['sources'][0]['candidate']['path']).read_text()
        self.assertIn('raise ValueError("Width must be positive. [AIDEAL fix:positive_width]', edited)
        self.assertIn('raise ValueError("Height must be positive.")', edited)

    def test_rejects_wrong_output_correction(self):
        proposal = self.prepare()
        self.context.write_text(json.dumps({'corrected': [999, 999], 'valid': [8, 4]}))
        plan = load(self.plan)
        plan['controls']['dev-width']['checker_context'] = bind(self.context)
        self.plan.write_text(json.dumps(plan))
        result = validate_native_hints(proposal, self.plan, self.root / 'bad-validation')
        self.assertEqual(result['status'], 'rejected')
        with self.assertRaisesRegex(ValueError, 'successful development'):
            verify_native_validation(result['validation'])

    def test_rejects_source_changes_after_validation(self):
        validation = self.validate()
        self.source.write_text(SOURCE.replace('return [width, height]', 'return [1, 2]'))
        with self.assertRaisesRegex(ValueError, 'changed'):
            verify_native_validation(validation)

    def test_dynamic_python_message_is_not_rewritten(self):
        with self.assertRaisesRegex(ValueError, 'literal'):
            patch_message(SOURCE.replace('"Width must be positive."', 'f"Width is {width}"'), 'lib.py', self.hint)

    def test_wrong_function_or_error_site_is_rejected(self):
        for fields in ({'function_id': 'lib.py:1:missing'}, {'error_line': 6}, {'original_message': 'different'}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                patch_message(SOURCE, 'lib.py', {**self.hint, **fields})

    def test_python_local_function_cannot_claim_an_importable_identity(self):
        source = ('def outer():\n    def resize(width):\n'
                  '        raise ValueError("Width must be positive.")\n    return resize\n')
        for identity in ('lib.py:2:resize', 'lib.py:2:lib.resize'):
            with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, 'declaration'):
                patch_message(source, 'lib.py', {**self.hint, 'function_id': identity})

    def test_java_runtime_message_but_not_comments_or_other_method(self):
        source = ('class Image {\n  public void size(int width) {\n'
                  '    if (width < 1) {\n      throw new IllegalArgumentException("Width must be positive.");\n'
                  '    }\n  }\n}\n')
        hint = {**self.hint, 'function_id': 'Image.java:2:size', 'error_line': 4}
        edited, message = patch_message(source, 'Image.java', hint)
        self.assertIn(message, edited)
        self.assertEqual(edited.replace(message, hint['original_message']), source)
        with self.assertRaises(ValueError):
            patch_message(source.replace('      throw', '      // throw'), 'Image.java', hint)

    def test_heldout_spec_and_duplicate_source_are_rejected(self):
        spec = load(self.spec)
        spec['split'] = 'held_out'
        self.spec.write_text(json.dumps(spec))
        with self.assertRaisesRegex(ValueError, 'development'):
            self.prepare()

    def test_multiple_error_sites_and_functions_share_a_file(self):
        height = {**self.hint, 'requirement_id': 'positive_height', 'error_line': 5,
                  'original_message': 'Height must be positive.', 'action': 'Pass a positive height.'}
        edited = patch_messages(SOURCE, 'lib.py', [self.hint, height, self.hint])
        self.assertEqual(edited.count('[AIDEAL fix:'), 2)
        first, _ = patch_message(SOURCE, 'lib.py', self.hint)
        self.assertEqual(patch_message(first, 'lib.py', height)[0], edited)
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            patch_messages(SOURCE, 'lib.py', [self.hint, {**self.hint, 'action': 'A different correction.'}])

    def test_abstract_java_method_cannot_claim_next_method_error(self):
        source = ('abstract class Image {\n  public abstract void size(int w);\n'
                  '  public void other() {\n    throw new IllegalArgumentException("Width must be positive.");\n  }\n}\n')
        with self.assertRaises(ValueError):
            patch_message(source, 'Image.java', {**self.hint, 'function_id': 'Image.java:2:size', 'error_line': 4})

    def test_nested_java_method_cannot_claim_outer_function_identity(self):
        source = ('class Image {\n  public void size(int w) {\n'
                  '    class Nested { void other() {\n      throw new IllegalArgumentException("Width must be positive.");\n'
                  '    } }\n  }\n}\n')
        with self.assertRaisesRegex(ValueError, 'Nested'):
            patch_message(source, 'Image.java', {**self.hint, 'function_id': 'Image.java:2:size', 'error_line': 4})

    def test_native_prompt_uses_only_returned_feedback(self):
        from workflow.evaluation_context import public_context
        document = self.root / 'README.md'
        document.write_text('Use resize(width, height).')
        frozen = {'config': {'schema_version': 3, 'common': {},
                  'conditions': {'error_hints_only': {'documents': [str(document)]}}}}
        case = {'prompt': 'Resize an image.', 'target_apis': ['resize']}
        feedback = 'ValueError: Width must be positive. [AIDEAL fix:positive_width] Pass a width greater than zero.'
        with patch('workflow.evaluation_legacy_hints.append_legacy_guidance', side_effect=AssertionError('No retrieval allowed')):
            initial, receipt0 = public_context(frozen, 'error_hints_only', case)
            prompt, receipt = public_context(frozen, 'error_hints_only', case, {'code': 'resize(0, 5)', 'feedback': feedback})
        self.assertNotIn('[AIDEAL fix:', initial)
        self.assertEqual(prompt.count(feedback), 1)
        self.assertNotIn('SOURCE-EMBEDDED REPAIR GUIDANCE', prompt)
        self.assertFalse(receipt['native_diagnostics']['guidance_retrieved'])
        self.assertEqual(receipt['hint_characters'], 0)
        self.assertEqual(receipt['native_diagnostics']['observed_requirement_ids'], ['positive_width'])

    def test_no_hint_injection_for_compiler_error(self):
        self.assertEqual(native_feedback_receipt('error: type mismatch;')['observed_requirement_ids'], [])

    def test_native_mode_rejects_old_hint_configuration(self):
        from workflow.evaluation_context import public_context
        with self.assertRaisesRegex(ValueError, 'cannot also retrieve'):
            public_context({'config': {'schema_version': 3, 'common': {},
                           'conditions': {'error_hints_only': {'source_hints': ['lib.py']}}}},
                           'error_hints_only', {'target_apis': ['resize']})


if __name__ == '__main__':
    unittest.main()
