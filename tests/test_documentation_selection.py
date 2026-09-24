"""Portable offline tests for opt-in qualified sections and legacy prompt parity."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from workflow.ablation import digest, load
from workflow.condition_context import public_context
from workflow.condition_setup import freeze_conditions, _controller
from workflow.documentation_selection import (markdown_sections, select_qualified_sections,
                                               validate_documentation_selection)
from workflow.evaluation import CONDITIONS, select_documentation, run_evaluation
from workflow.evaluation_setup import freeze_evaluation, read_config, open_frozen

A = 'example.Feature.append'
B = 'example.RasterMetadata.rescale'
C = 'example.RasterMetadata.numTiles'


def policy(*apis):
    return {'policy': 'qualified_sections', 'api_headings': {
        a: a + (' [object]' if a == A else ' [class]') for a in apis}}


def section(api, body, kind='class'):
    return f'## API Test: `{api} [{kind}]`\n{body}\n'


class QualifiedSectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.document = self.root / 'README.md'

    def select(self, text, apis, cap=8000):
        self.document.write_text(text)
        return select_qualified_sections([self.document], apis, cap, policy(*apis))

    def test_exact_receiver_beats_repeated_bare_mentions(self):
        unrelated = section('other.Type.append', 'append ' * 2000)
        correct = section(A, 'CORRECT_RECEIVER', 'object')
        delivered, receipt = self.select(unrelated + correct, [A])
        self.assertEqual(delivered, correct)
        self.assertEqual(receipt['targets'][A]['match'], 'exact_heading')
        self.assertEqual(receipt['targets'][A]['coverage'], 'full')

    def test_companion_and_instance_are_distinct_even_with_same_canonical_name(self):
        wrong = section(B, (B + ' ') * 200, 'object')
        correct = section(B, 'INSTANCE_CONTRACT')
        delivered, _ = self.select(wrong + correct, [B])
        self.assertEqual(delivered, correct)

    def test_other_qualified_owner_cannot_substitute_for_absent_heading(self):
        delivered, receipt = self.select(section(B, 'rescale works here', 'object'), [B])
        self.assertEqual(receipt['mode'], 'ordered_prefix_no_match')
        self.assertEqual(receipt['targets'][B]['match'], 'absent')
        self.assertEqual(receipt['targets'][B]['coverage'], 'absent')
        self.assertIn('[object]', delivered)  # Prefix exposure is not reported as target coverage.

    def test_two_long_targets_share_budget_and_record_partial_ranges(self):
        text = section(B, 'b' * 12000) + section(C, 'c' * 12000)
        delivered, receipt = self.select(text, [B, C])
        self.assertEqual(len(delivered), 8000)
        self.assertIn(B, delivered)
        self.assertIn(C, delivered)
        for api in (B, C):
            self.assertEqual(receipt['targets'][api]['coverage'], 'clipped')
            self.assertEqual(receipt['targets'][api]['delivered_characters'], 3999)
        for entry in receipt['selected_sections']:
            start, end = entry['source_start_character'], entry['delivered_end_character']
            self.assertEqual(entry['delivered_sha256'], digest(text[start:end]))

    def test_short_quota_is_redistributed_without_unrelated_filler(self):
        short = section(C, 'short')
        long = section(B, 'b' * 12000)
        delivered, receipt = self.select(short + long + section(A, 'UNRELATED', 'object'), [B, C])
        self.assertEqual(len(delivered), 8000)
        self.assertEqual(receipt['targets'][C]['coverage'], 'full')
        self.assertEqual(receipt['targets'][B]['delivered_characters'], 7998 - len(short))
        self.assertNotIn('UNRELATED', delivered)

    def test_fenced_headings_never_start_sections(self):
        text = ('## First\n````scala\n## fake one\n```\n## still fake\n````\n'
                '~~~text\n## fake two\n~~~~\n## Second\nreal\n')
        parsed = markdown_sections(text)
        self.assertEqual([s['heading'] for s in parsed], ['First', 'Second'])
        self.assertEqual(''.join(s['text'] for s in parsed), text)

    def test_duplicate_exact_heading_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate exact'):
            self.select(section(B, 'one') + section(B, 'two'), [B])

    def test_original_fallback_prioritizes_receiver_over_bare_frequency(self):
        text = '## Bare\n' + 'rescale ' * 1000 + '\n## Example\nRasterMetadata.rescale calls the receiver.\n'
        delivered, receipt = self.select(text, [B])
        self.assertTrue(delivered.startswith('## Example'))
        self.assertEqual(receipt['targets'][B]['match'], 'lexical_fallback')
        self.assertEqual(receipt['targets'][B]['coverage'], 'full')

    def test_zero_match_preserves_original_document_order_and_marks_absent(self):
        self.document.write_text('## First\nABCDEFGHIJ\n## Second\nKLMNOP\n')
        other = self.root / 'other.md'
        other.write_text('## Third\nQRST\n')
        whole = self.document.read_text() + '\n\n' + other.read_text()
        delivered, receipt = select_qualified_sections([self.document, other], [B], 27, policy(B))
        self.assertEqual(delivered, whole[:27])
        self.assertEqual(receipt['targets'][B]['coverage'], 'absent')
        self.assertTrue(receipt['selected_sections'][-1]['clipped'])

    def test_empty_document_prefix_offsets_are_exact(self):
        self.document.write_text('')
        other = self.root / 'other.md'
        other.write_text('## Untargeted\n012345\n')
        delivered, receipt = select_qualified_sections([self.document, other], [B], 8, policy(B))
        self.assertEqual(delivered, '\n\n## Unt')
        self.assertEqual(receipt['selected_sections'][0]['delivered_characters'], 6)

    def test_legacy_selector_keeps_its_existing_exact_prefix_and_receipt(self):
        text = '# Start\nintro\n## Small\nTarget\n## Large\nTarget Target\n' + 'z' * 200
        self.document.write_text(text)
        delivered, receipt = select_documentation([self.document], ['Target'], 50)
        expected = text[text.index('## Large'):][:48]
        self.assertEqual(delivered, expected)
        self.assertEqual(receipt, {'source_characters': len(text), 'delivered_characters': 48,
                                  'selected_section_indices': [2], 'truncated': True,
                                  'delivered_sha256': digest(expected)})
        full, full_receipt = select_documentation([self.document], ['Target'], 1000)
        self.assertEqual(full, text)
        self.assertEqual(full_receipt['selected_section_indices'], [0, 1, 2])
        self.assertNotIn('policy', full_receipt)

    def test_condition_context_uses_canonical_targets_only_for_opt_in(self):
        self.document.write_text(section(B, 'RIGHT') + section(B, 'wrong ' * 500, 'object'))
        cfg = {'conditions': {'original': {'documents': [str(self.document)]}},
               'common': {'documentation_max_characters': 100, 'documentation_selection': policy(B)}}
        case = {'prompt': 'Use the API.', 'target_apis': [B]}
        prompt, receipt = public_context({'config': cfg}, 'original', case)
        self.assertIn('RIGHT', prompt)
        self.assertNotIn('wrong', prompt)
        self.assertEqual(set(receipt['documentation']['targets']), {B})
        self.assertEqual(receipt['hint_characters'], 0)

    def test_policy_rejects_forged_missing_extra_and_unknown_fields(self):
        values = [None, [], {}, {'policy': 'other', 'api_headings': {B: B + ' [class]'}},
                  {'policy': 'qualified_sections', 'api_headings': {B: A + ' [class]'}},
                  {'policy': 'qualified_sections', 'api_headings': {B: B + ' [guess]'}},
                  {'policy': 'qualified_sections', 'api_headings': {B: B + ' [class]\n'}},
                  {**policy(B), 'unexpected': True}, policy(A), policy(A, B)]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_documentation_selection(value, [B])


class FreezePolicyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.api = 'example.Type.f'
        for name, value in [('source.txt', 'pinned'), ('reference.txt', 'good'), ('negative.txt', 'bad'),
                            ('no_target.txt', 'no_target'), ('oracle.json', '{"answer":"good"}')]:
            (self.root / name).write_text(value)
        (self.root / 'README.md').write_text(section(self.api, 'CORRECT_SECTION'))
        (self.root / 'checker.py').write_text('import json,sys\nr=json.load(sys.stdin)\nprint(json.dumps(dict(execution_pass=True,oracle_pass=r["code"] in ("good","no_target"),target_reached=r["code"]!="no_target")))\n')
        (self.root / 'model.py').write_text('import json\nprint(json.dumps({"code":"good"}))\n')
        cases = [{'id': k, 'kind': k, 'split': 'held_out', 'prompt': 'Call f.', 'target_apis': [self.api],
                  'reference': 'reference.txt', 'oracle': 'oracle.json', 'negative_controls': ['negative.txt'],
                  'target_negative_controls': ['no_target.txt']} for k in ('micro', 'puzzle')]
        (self.root / 'bank.json').write_text(json.dumps({'api_names': [self.api], 'cases': cases}))
        self.common = {'temperature': 0, 'max_output_tokens': 100, 'provider_attempt_limit': 1,
                       'execution_timeout_s': 5, 'provider_timeout_s': 5, 'max_snippet_fixes': 0,
                       'trial_ids': ['trial_01'], 'documentation_max_characters': 100,
                       'documentation_selection': policy(self.api)}
        self.model = {'name': 'synthetic', 'command': [sys.executable, str(self.root / 'model.py')],
                      'artifacts': ['model.py']}
        self.config = {'readme_evaluation': {'bank': 'bank.json',
                       'documents': {k: ['README.md'] for k in CONDITIONS},
                       'adapter': {'command': [sys.executable, str(self.root / 'checker.py')], 'artifacts': ['checker.py']},
                       'model': self.model, 'source': {'revision': 'synthetic', 'artifacts': ['source.txt']},
                       'common': self.common, 'holdout_review': 'Synthetic offline fixture.'}}
        self.path = self.root / 'study.yaml'

    def write(self, value=None):
        self.path.write_text(yaml.safe_dump(value or self.config))

    def test_invalid_map_rejected_before_any_control_or_output_for_both_protocols(self):
        for mapping in ({}, {'unrelated.f': 'unrelated.f [class]'}, {self.api: 'forged.Type.f [class]'}):
            for condition_protocol in (False, True):
                cfg = deepcopy(self.config)
                cfg['readme_evaluation']['common']['documentation_selection']['api_headings'] = mapping
                if condition_protocol:
                    original = cfg['readme_evaluation']
                    cfg = {'condition_evaluation': {**original, 'schema_version': 1, 'design': 'refactor_pair',
                           'conditions': {'original': {}, 'refactor_only': {}}}}
                self.write(cfg)
                output = self.root / 'never_created'
                with patch('workflow.evaluation_setup.invoke') as old, patch('workflow.condition_setup.invoke') as new:
                    with self.assertRaisesRegex(ValueError, 'api_headings'):
                        (freeze_conditions if condition_protocol else freeze_evaluation)(self.path, output)
                    old.assert_not_called()
                    new.assert_not_called()
                self.assertFalse(output.exists())

    def test_opt_in_helper_is_bound_and_synthetic_three_readme_run_uses_it(self):
        self.write()
        payload = read_config(self.path)
        self.assertIn('documentation_selection.py', payload['controller_sha256'])
        self.assertIn('documentation_selection.py', _controller({'common': self.common}))
        self.assertNotIn('documentation_selection.py', _controller({'common': {}}))
        frozen = freeze_evaluation(self.path, self.root / 'frozen')['frozen']
        self.assertEqual(open_frozen(frozen)['config']['common']['documentation_selection'], policy(self.api))
        run_evaluation(frozen, self.root / 'run')
        exposures = [load(p) for p in (self.root / 'run').rglob('documentation_exposure.json')]
        self.assertEqual(len(exposures), 6)
        self.assertTrue(all(e['policy'] == 'qualified_sections' for e in exposures))
        self.assertTrue(all(e['targets'][self.api]['coverage'] == 'full' for e in exposures))


if __name__ == '__main__':
    unittest.main()
