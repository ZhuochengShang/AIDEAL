"""Adapter-declared nested evidence must survive validation and execution reuse."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workflow.ablation import bind
from workflow.condition_setup import checked_outcome, execute_condition


class ConditionAdjudicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-adjudication-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.trace = self.root / 'trace.txt'
        self.trace.write_text('trusted target event\n')
        self.process = {'status': 'ok', 'payload': {'execution_pass': True, 'oracle_pass': True,
                         'target_reached': True, 'backend_sha256': 'backend',
                         'public_feedback': 'Independent checks passed.'}}

    def with_refs(self, refs):
        result = deepcopy(self.process)
        result['payload']['adjudication_artifacts'] = refs
        return result

    def test_optional_evidence_preserves_synthetic_adapter_contract(self):
        self.assertIs(checked_outcome(self.process, 'backend'), True)
        self.process['payload']['oracle_pass'] = False
        self.assertIs(checked_outcome(self.process, 'backend'), False)

    def test_existing_bound_evidence_including_empty_logs_accepts_checked_outcome(self):
        empty = self.root / 'stderr.txt'
        empty.write_text('')
        result = self.with_refs([bind(self.trace), bind(empty)])
        self.assertIs(checked_outcome(result, 'backend'), True)
        result['payload']['oracle_pass'] = False
        self.assertIs(checked_outcome(result, 'backend'), False)

    def test_changed_or_deleted_nested_evidence_is_unverified(self):
        result = self.with_refs([bind(self.trace)])
        self.trace.write_text('altered target event\n')  # Same length; hash, not size, must decide.
        self.assertIsNone(checked_outcome(result, 'backend'))
        self.trace.unlink()
        self.assertIsNone(checked_outcome(result, 'backend'))

    def test_malformed_duplicate_and_noncanonical_bindings_fail_closed(self):
        ref = bind(self.trace)
        malformed = [None, {}, [], [None], [str(self.trace)], [{'path': str(self.trace)}],
                     [dict(ref, bytes=True)], [dict(ref, bytes=-1)], [dict(ref, bytes=ref['bytes'] + 1)],
                     [dict(ref, sha256='invalid')], [dict(ref, path='trace.txt')], [ref, ref],
                     [dict(ref, extra='ambiguous')], [dict(ref, path=str(self.root))],
                     [dict(ref, path=str(self.root / 'absent.txt'))]]
        alias = self.root / 'alias.txt'
        alias.symlink_to(self.trace)
        malformed.append([dict(ref, path=str(alias))])
        for refs in malformed:
            with self.subTest(refs=refs):
                self.assertIsNone(checked_outcome(self.with_refs(refs), 'backend'))

    def test_missing_nested_evidence_cannot_reuse_cached_execution(self):
        parent = self.root / 'round_00'
        first = parent / 'execution_001'
        first.mkdir(parents=True)
        saved = first / 'process.json'
        saved.write_text(json.dumps(self.with_refs([bind(self.trace)])))
        before = saved.read_bytes()
        self.trace.unlink()
        payload = {'backends': {'original': {'sha256': 'backend'}},
                   'config': {'conditions': {'original': {'adapter': {'command': ['synthetic-checker']}}},
                              'common': {'execution_timeout_s': 1}}}
        case = {'id': 'synthetic', 'oracle': 'not-read', 'target_apis': ['f']}
        with patch('workflow.condition_setup.invoke', return_value={'status': 'adapter_error'}) as invoke:
            destination, _ = execute_condition(payload, 'original', case, 'candidate', parent)
        self.assertEqual(parent / 'execution_002', destination)
        self.assertEqual(destination, invoke.call_args.args[2])
        self.assertEqual(before, saved.read_bytes())

    def test_terminal_resume_checks_nested_adapter_evidence(self):
        import test_condition_evaluation as fixtures
        from workflow.ablation import load
        from workflow.condition_evaluation import run_conditions

        fixture = fixtures.ConditionEvaluationTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        cfg = fixture.cfg['condition_evaluation']
        cfg['design'] = 'refactor_pair'
        cfg['conditions'] = {arm: cfg['conditions'][arm] for arm in ('original', 'refactor_only')}
        cfg['common']['max_snippet_fixes'] = 0
        fixture.write_config()
        script = fixture.adapter.read_text()
        script = script.replace("print(json.dumps({'execution_pass':True,", """import hashlib
proof=Path.cwd()/'nested_trace.txt'
proof.write_text('Synthetic observed target event')
evidence={'path':str(proof),'sha256':hashlib.sha256(proof.read_bytes()).hexdigest(),'bytes':proof.stat().st_size}
print(json.dumps({'adjudication_artifacts':[evidence],'execution_pass':True,""")
        fixture.adapter.write_text(script)
        study = fixture.freeze()
        output = fixture.root / 'run'
        run_conditions(study, output, condition='original', max_units=1)
        result = next(output.glob('original/*/result.json'))
        row = load(result)
        process_path = Path(row['adjudication']['process']['path'])
        process_before = process_path.read_bytes()
        nested = Path(load(process_path)['payload']['adjudication_artifacts'][0]['path'])
        nested.unlink()
        with patch('workflow.condition_evaluation._request_solution') as model:
            with self.assertRaisesRegex(ValueError, 'checker verdict'):
                run_conditions(study, output, condition='original')
            model.assert_not_called()
        self.assertEqual(process_before, process_path.read_bytes())


if __name__ == '__main__':
    unittest.main()
