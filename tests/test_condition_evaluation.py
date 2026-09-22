"""Offline matched-condition protocol tests, using tiny Git fixtures and JSON adapters."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from workflow.ablation import digest, load
from workflow.condition_context import public_context
from workflow.condition_evaluation import run_conditions
from workflow.condition_inputs import DESIGNS
from workflow.condition_reporting import report_conditions
from workflow.condition_setup import freeze_conditions, open_conditions, read_condition_config


class ConditionEvaluationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-conditions-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.base = self.root / 'base'
        self.base.mkdir()
        self.git(self.base, 'init', '-q')
        (self.base / 'lib.py').write_text('def f(x):\n    return x + 1\n')
        (self.base / 'README.md').write_text('ORIGINAL_DOC')
        self.git(self.base, 'add', '.')
        self.git(self.base, 'commit', '-qm', 'Synthetic baseline')
        self.adapter = self.root / 'checker.py'
        self.adapter.write_text('''import json,sys,subprocess
from pathlib import Path
r=json.load(sys.stdin)
c=json.loads(Path(sys.argv[1]).read_text())
root=Path(c['root'])
actual=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
receipt=r['backend']['sha256'] if str(root)==r['backend']['worktree'] and actual==r['backend']['revision'] else 'WRONG_BACKEND'
oracle=json.loads(Path(r['oracle_path']).read_text())
correct=r['code']==oracle['answer'] or r['code']=='no_target' or (r['code']=='alias' and (root/'aliases.py').is_file())
print(json.dumps({'execution_pass':True,'oracle_pass':correct,
 'target_reached':r['code'] in ('correct','wrong','alias'),'backend_sha256':receipt,
 'public_feedback':'All checks passed' if correct else 'TypeError: expected numeric argument'}))
''')
        self.model = self.root / 'model.py'
        self.model.write_text('''import json,sys
r=json.load(sys.stdin)
assert 'PRIVATE_EXPECTATION' not in str(r) and 'oracle_path' not in str(r) and 'backend' not in r
p=r['prompt']
code='correct' if 'BETTER_DOCS' in p or 'FIX_HINT' in p else 'alias' if 'USE_ALIAS' in p else 'wrong'
print(json.dumps({'code':code,'usage':{'input_tokens':7,'output_tokens':3}}))
''')
        for name, text in (('reference.txt', 'correct'), ('wrong.txt', 'wrong'), ('no_target.txt', 'no_target')):
            (self.root / name).write_text(text)
        self.write_json(self.root / 'oracle.json', {'answer': 'correct', 'private': 'PRIVATE_EXPECTATION'})
        cases = [dict(id=kind, kind=kind, split='held_out', target_apis=['f'], prompt='Compute f(x).',
                      public_context='Return a candidate identifier.', reference='reference.txt',
                      negative_controls=['wrong.txt'], target_negative_controls=['no_target.txt'], oracle='oracle.json')
                 for kind in ('micro', 'puzzle')]
        self.write_json(self.root / 'bank.json', {'api_names': ['f'], 'cases': cases,
                                               'scope_note': 'Synthetic software tests, never research scores.'})
        hints = {'schema_version': 1, 'status': 'unverified', 'hints': [
            {'function_id': 'lib:f', 'error_contains': 'expected numeric argument', 'likely_cause': 'FIX_HINT',
             'fix_steps': ['Use the correct candidate.'], 'suggested_fix_code': '', 'validation': 'Recheck.'},
            {'function_id': 'other:g', 'error_contains': 'expected numeric argument', 'likely_cause': 'WRONG_FUNCTION',
             'fix_steps': ['Do not deliver.'], 'validation': 'Recheck.'}]}
        self.conditions = {}
        for arm in DESIGNS['six_arm']:
            root = self.root / arm
            self.git(self.root, 'clone', '-q', '--no-hardlinks', str(self.base), str(root))
            branch = 'aideal/' + arm.replace('_', '-')
            self.git(root, 'checkout', '-qb', branch)
            treatment = root / '.aideal/treatments'
            treatment.mkdir(parents=True)
            if arm in ('alias_only', 'combined'):
                (root / 'aliases.py').write_text('from lib import f\ndef easier_f(x): return f(x)\n')
                (treatment / 'ALIASES.md').write_text('USE_ALIAS: an additive interface to canonical f.')
            if arm == 'refactor_only':
                (root / 'lib.py').write_text('def f(x):\n    result = x + 1\n    return result\n')
            if arm in ('readme_only', 'combined'):
                (treatment / 'README.md').write_text('BETTER_DOCS')
            if arm in ('error_hints_only', 'combined'):
                self.write_json(treatment / 'error_hints.json', hints)
            self.git(root, 'add', '.')
            self.git(root, 'commit', '--allow-empty', '-qm', 'Synthetic ' + arm)
            config = self.root / (arm + '.runtime.json')
            self.write_json(config, {'root': str(root)})
            condition = {'documents': [str(treatment / 'README.md' if arm in ('readme_only', 'combined') else root / 'README.md')],
                         'adapter': {'command': [sys.executable, str(self.adapter), str(config)],
                                     'artifacts': [str(self.adapter), str(config)]},
                         'source': {'worktree': str(root), 'revision': self.git(root, 'rev-parse', 'HEAD'),
                                    'branch': branch, 'artifacts': [str(root / 'lib.py')]}}
            if arm in ('alias_only', 'combined'):
                condition['alias_interface'] = str(treatment / 'ALIASES.md')
            if arm in ('error_hints_only', 'combined'):
                condition['error_hints'] = str(treatment / 'error_hints.json')
            self.conditions[arm] = condition
        self.cfg = {'condition_evaluation': {
            'schema_version': 1, 'design': 'six_arm', 'bank': 'bank.json',
            'conditions': self.conditions, 'api_function_ids': {'f': 'lib:f'},
            'model': {'name': 'synthetic-no-model', 'command': [sys.executable, str(self.model)],
                      'artifacts': [str(self.model)]},
            'common': {'temperature': 0, 'max_output_tokens': 100, 'provider_attempt_limit': 1,
                       'execution_timeout_s': 5, 'provider_timeout_s': 5, 'max_snippet_fixes': 1,
                       'trial_ids': ['trial_01'], 'documentation_max_characters': 100,
                       'alias_max_characters': 100, 'hint_max_characters': 500},
            'holdout_review': 'Synthetic offline controls only.'}}
        self.config = self.root / 'study.yaml'
        self.write_config()

    @staticmethod
    def git(root, *args):
        result = subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture',
                                 '-c', 'user.email=fixture@localhost', '-c', 'commit.gpgsign=false',
                                 '-c', 'core.hooksPath=/dev/null', *args], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value, indent=2) + '\n')

    def write_config(self):
        self.config.write_text(yaml.safe_dump(self.cfg, sort_keys=False))

    def freeze(self):
        return Path(freeze_conditions(self.config, self.root / 'freeze')['frozen'])

    def test_all_six_conditions_route_backends_match_hints_and_resume(self):
        study = self.freeze()
        frozen = open_conditions(study)
        self.assertEqual(36, len(frozen['validation']['controls']))
        for record in frozen['validation']['controls']:
            self.assertEqual(frozen['backends'][record['arm']]['sha256'], record['backend_sha256'])
        out = self.root / 'run'
        summary = run_conditions(study, out)
        self.assertTrue(summary['all_complete'])
        expected = {'original': 0, 'readme_only': 1, 'alias_only': 1,
                    'error_hints_only': 1, 'combined': 1, 'refactor_only': 0}
        for arm, passes in expected.items():
            for metrics in summary['metrics'][arm].values():
                self.assertEqual(passes, metrics['correct_within_budget'])
                self.assertEqual(passes if arm != 'error_hints_only' else 0, metrics['first_attempt_correct'])
        for request in out.glob('*/**/provider_*/request.json'):
            text = request.read_text()
            self.assertNotIn('PRIVATE_EXPECTATION', text)
            self.assertNotIn('oracle_path', text)
            self.assertNotIn('WRONG_FUNCTION', text)
            if 'round_00' in str(request):
                self.assertNotIn('FIX_HINT', text)
            if request.parts[-5] in ('original', 'readme_only', 'alias_only', 'refactor_only'):
                self.assertNotIn('POST-FAILURE DEVELOPMENT HINTS', text)
        hint_receipt = load(out / 'error_hints_only/micro--trial_01/round_01/context_exposure.json')
        self.assertEqual(1, len(hint_receipt['hints']['delivered']))
        self.assertIn('FIX_HINT', hint_receipt['hints']['text'])
        calls = sorted(out.glob('*/**/provider_*/process.json'))
        self.assertEqual(summary, run_conditions(study, out))
        self.assertEqual(calls, sorted(out.glob('*/**/provider_*/process.json')))

    def test_five_arm_and_separate_refactor_pair_are_explicit_designs(self):
        for design in ('five_arm', 'refactor_pair'):
            self.cfg['condition_evaluation']['design'] = design
            self.cfg['condition_evaluation']['conditions'] = {a: self.conditions[a] for a in DESIGNS[design]}
            self.write_config()
            payload = read_condition_config(self.config)
            self.assertEqual(list(DESIGNS[design]), list(payload['config']['conditions']))

    def test_missing_or_wrong_backend_controls_cannot_freeze(self):
        config = self.root / 'alias_only.runtime.json'
        self.write_json(config, {'root': str(self.root / 'original')})
        with self.assertRaisesRegex(ValueError, 'Condition controls failed'):
            self.freeze()
        self.assertFalse((self.root / 'freeze/frozen.json').exists())
        last = load(self.root / 'freeze/validation/validation.json')['controls'][-1]
        self.assertEqual('alias_only', last['arm'])
        self.assertFalse(last['valid'])

    def test_missing_control_record_and_edited_backend_refuse_resume(self):
        study = self.freeze()
        original = load(study)
        edited = deepcopy(original)
        edited['validation']['controls'].pop()
        edited['study_sha256'] = digest({k: v for k, v in edited.items() if k != 'study_sha256'})
        self.write_json(study, edited)
        with self.assertRaisesRegex(ValueError, 'Missing condition control'):
            open_conditions(study)
        self.write_json(study, original)
        target = self.root / 'alias_only/aliases.py'
        target.write_text(target.read_text() + '# Uncommitted change\n')
        with self.assertRaisesRegex(ValueError, 'tracked/source edit'):
            open_conditions(study)

    def test_contaminated_documents_mixed_artifacts_and_missing_controls_reject_before_invoke(self):
        baseline = deepcopy(self.cfg)
        cases = load(self.root / 'bank.json')
        changes = [
            lambda: self.cfg['condition_evaluation']['conditions']['alias_only'].update(documents=self.conditions['readme_only']['documents']),
            lambda: self.cfg['condition_evaluation']['conditions']['original'].update(alias_interface=self.conditions['alias_only']['alias_interface']),
            lambda: self.cfg['condition_evaluation']['conditions']['combined'].update(documents=self.conditions['original']['documents']),
            lambda: self.cfg['condition_evaluation']['common'].update(hint_max_characters=True),
            lambda: self.cfg['condition_evaluation'].update(design=[]),
        ]
        for change in changes:
            self.cfg = deepcopy(baseline)
            change()
            self.write_config()
            with patch('workflow.condition_setup.invoke') as invoke:
                with self.assertRaises(ValueError):
                    self.freeze()
                invoke.assert_not_called()
            self.assertFalse((self.root / 'freeze').exists())
        self.cfg = baseline
        self.write_config()
        cases['cases'][0]['target_negative_controls'] = []
        self.write_json(self.root / 'bank.json', cases)
        with self.assertRaisesRegex(ValueError, 'target_negative_controls'):
            self.freeze()

    def test_checked_failure_only_hints_have_shared_caps_and_exact_exposure(self):
        payload = read_condition_config(self.config)
        case = payload['bank']['cases'][0]
        payload['config']['common']['alias_max_characters'] = 8
        payload['config']['common']['hint_max_characters'] = 70
        prompt, receipt = public_context(payload, 'combined', case)
        self.assertEqual(8, receipt['alias_characters'])
        self.assertEqual(0, receipt['hint_characters'])
        self.assertNotIn('POST-FAILURE', prompt)
        no_match, receipt = public_context(payload, 'error_hints_only', case, {'code': 'wrong', 'feedback': 'unrelated'})
        self.assertEqual([], receipt['hints']['matched'])
        prompt, receipt = public_context(payload, 'error_hints_only', case,
                                         {'code': 'wrong', 'feedback': 'TypeError: expected numeric argument'})
        self.assertEqual(70, receipt['hint_characters'])
        self.assertTrue(receipt['hints']['truncated'])
        self.assertIn(receipt['hints']['text'], prompt)
        self.assertEqual(digest(prompt), receipt['public_prompt_sha256'])

    def test_wrong_backend_receipt_stays_unresolved_and_stops_batch(self):
        study = self.freeze()
        bad = {'status': 'ok', 'payload': {'execution_pass': True, 'oracle_pass': True,
                                         'target_reached': True, 'backend_sha256': 'wrong'}}
        with patch('workflow.condition_setup.invoke', return_value=bad):
            summary = run_conditions(study, self.root / 'run')
        self.assertFalse(summary['all_complete'])
        self.assertEqual(12, sum(m['unresolved'] for kinds in summary['metrics'].values() for m in kinds.values()))
        self.assertEqual(1, sum(r['provider_calls'] for r in summary['resources'].values()))

    def test_result_row_cannot_override_saved_checker_verdict(self):
        study = self.freeze()
        out = self.root / 'run'
        run_conditions(study, out, condition='original', max_units=1)
        result = next(out.glob('original/*/result.json'))
        row = load(result)
        missing_exposure = deepcopy(row)
        missing_exposure.pop('context_exposures')
        self.write_json(result, missing_exposure)
        with patch('workflow.condition_evaluation._request_solution') as model:
            with self.assertRaisesRegex(ValueError, 'public-context exposure'):
                run_conditions(study, out)
            model.assert_not_called()
        row.update(status='pass', execution_pass=True, oracle_pass=True, target_reached=True,
                   first_attempt_pass=False, first_pass_round=1)
        self.write_json(result, row)
        with patch('workflow.condition_evaluation._request_solution') as model:
            with self.assertRaisesRegex(ValueError, 'checker verdict'):
                run_conditions(study, out)
            model.assert_not_called()

    def test_partial_scores_use_full_denominators_and_hold_blocks_commands(self):
        payload = read_condition_config(self.config)
        payload['study_sha256'] = 'synthetic'
        row = {'arm': 'readme_only', 'case_id': 'micro', 'trial_id': 'trial_01', 'study_sha256': 'synthetic',
               'backend_sha256': payload['backends']['readme_only']['sha256'], 'status': 'pass',
               'first_attempt_pass': True, 'first_pass_round': 0,
               'execution_pass': True, 'oracle_pass': True, 'target_reached': True}
        summary = report_conditions(payload, [row])
        self.assertEqual(11, sum(m['unresolved'] for kinds in summary['metrics'].values() for m in kinds.values()))
        self.assertTrue(all(p['final_lift_percentage_points'] is None for p in summary['paired_comparisons']))
        self.write_json(self.root / 'REVIEW_HOLD.json', {'reason': 'Synthetic hold'})
        with patch('workflow.condition_setup.invoke') as checker:
            with self.assertRaisesRegex(ValueError, 'paused'):
                self.freeze()
            checker.assert_not_called()


if __name__ == '__main__':
    unittest.main()
