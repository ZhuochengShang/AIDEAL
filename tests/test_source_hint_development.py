"""Offline development evidence, actual fixture execution and validation gating."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from workflow.ablation import bind, digest, load
from workflow.source_hint_development import (build_development_preview,
    propose_source_hints, validate_source_hint_development, verify_development_validation)
from workflow.source_hints import strip_source_hints


class SourceHintDevelopmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        self.original = ('def f(x: int) -> int:\n'
                         '    if x is None: raise ValueError("cannot be missing")\n'
                         '    if not isinstance(x, int): raise TypeError("expected numeric argument")\n'
                         '    return x + 1\n')
        (self.source / 'lib.py').write_text(self.original)
        (self.source / 'README.md').write_text('Use f(x) to increment an integer.')
        self.git('init', '-q'); self.git('add', '.'); self.git('commit', '-qm', 'Fixture baseline')
        self.revision = self.git('rev-parse', 'HEAD')
        self.identity = 'lib.py:1:f'
        self.code = "result = f('bad')"
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        self.write(self.evidence / 'request.json', {'system': 'Return code.', 'prompt': 'Increment an integer.',
            'context_provenance': {'split': 'development', 'condition': 'original', 'round': 0,
                                   'source_root': str(self.source), 'source_revision': self.revision,
                                   'original_documents': [bind(self.source / 'README.md')]}})
        self.write(self.evidence / 'response.json', {'status': 'ok', 'payload': {
            'code': self.code, 'response_status': 'completed', 'usage': {'input_tokens': 10, 'output_tokens': 5}}})
        self.write(self.evidence / 'checker-request.json', {'split': 'development', 'condition': 'original',
            'round': 0, 'case_id': 'dev-one', 'code': self.code, 'source_revision': self.revision})
        self.write(self.evidence / 'checker-process.json', {'status': 'ok', 'payload': {
            'execution_pass': False, 'oracle_pass': False, 'target_reached': True,
            'public_feedback': 'TypeError: expected numeric argument',
            'public_failure': {'function_id': self.identity, 'requirement_id': 'numeric_input',
                               'diagnostic': 'expected numeric argument'}, 'private_expected': 'DO_NOT_SEND'}})
        self.attempt = {'case_id': 'dev-one', 'split': 'development', 'condition': 'original', 'round': 0,
            **{key: bind(self.evidence / filename) for key, filename in (
                ('provider_request', 'request.json'), ('provider_process', 'response.json'),
                ('execution_request', 'checker-request.json'), ('execution_process', 'checker-process.json'))}}
        self.manifest = {'schema_version': 1, 'source_root': str(self.source), 'baseline_revision': self.revision,
            'split': 'development', 'condition': 'original', 'round': 0,
            'original_documents': [bind(self.source / 'README.md')], 'api_function_ids': {'lib.f': self.identity},
            'held_out_case_ids': ['held-one'], 'attempts': [self.attempt]}
        self.manifest_path = self.root / 'manifest.json'
        self.write(self.manifest_path, self.manifest)
        self.hint = {'function_id': self.identity, 'requirement_id': 'numeric_input',
            'requirement': 'x must be an integer.', 'diagnostic': 'expected numeric argument',
            'action': 'Pass an integer instead of text.', 'validation': 'Check the incremented integer.'}
        self.diagnosis = {'evidence_id': 'dev-one', 'classification': 'api_requirement',
            'reason': 'The source checks integer type.', 'source_quote': 'def f(x: int) -> int:',
            'hint': self.hint, 'corrected_code': 'result = f(2)'}
        self.author = self.root / 'author.py'
        self.author.write_text('import json,sys\nr=json.load(sys.stdin)\nassert "DO_NOT_SEND" not in r["prompt"]\n'
            'print(json.dumps({"code":json.dumps(' + repr({'diagnoses': [self.diagnosis]}) + '),'
            '"response_status":"completed","usage":{"input_tokens":50,"output_tokens":30}}))\n')
        self.settings = {'command': [sys.executable, str(self.author)], 'name': 'offline-fixture',
                         'max_output_tokens': 3000, 'temperature': 0, 'timeout_s': 10}
        self.model_config = self.root / 'model.json'
        self.write(self.model_config, {'model': self.settings})
        self.adapter = self.root / 'validate.py'
        self.adapter.write_text('''import hashlib,json,sys,runpy
from pathlib import Path
r=json.load(sys.stdin)
context=json.loads(Path(r['checker_context_path']).read_text())
namespace=runpy.run_path(str(Path(r['source_root'])/'lib.py'))
try:
 exec(r['code'], namespace)
 executed=True
 correct=namespace.get('result')==context['expected'].get(r['role'])
 feedback='Execution checks passed.' if correct else 'Incorrect incremented result.'
except Exception as e:
 executed=correct=False
 feedback=type(e).__name__+': '+str(e)
record={'execution_pass':executed,'oracle_pass':correct,'target_reached':True,
 'public_feedback':feedback,'source_revision':r['source_revision'],
 'request_sha256':hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()}
if 'expected numeric argument' in feedback or 'cannot be missing' in feedback:
 diagnostic='expected numeric argument' if 'expected numeric argument' in feedback else 'cannot be missing'
 record['public_failure']={'function_id':'lib.py:1:f','requirement_id':'numeric_input' if diagnostic.startswith('expected') else 'missing_input','diagnostic':diagnostic}
print(json.dumps(record))
''')
        self.valid = self.root / 'valid.py'; self.valid.write_text('result = f(3)')
        self.nearby = self.root / 'nearby.py'; self.nearby.write_text('result = f(None)')
        self.context = self.root / 'private.json'; self.write(self.context, {'expected': {'corrected': 3, 'valid': 4}})
        self.plan = {'schema_version': 1, 'split': 'development',
            'adapter': {'command': [sys.executable, str(self.adapter)], 'timeout_s': 10, 'artifacts': [bind(self.adapter)]},
            'controls': {'dev-one': {'valid_code': bind(self.valid), 'nearby_code': bind(self.nearby),
                                     'checker_context': bind(self.context)}}}
        self.plan_path = self.root / 'plan.json'; self.write(self.plan_path, self.plan)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), '-c', 'user.name=Fixture',
            '-c', 'user.email=fixture@localhost', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
            *args], text=True).strip()

    @staticmethod
    def write(path, data):
        path.write_text(json.dumps(data, indent=2) + '\n')

    def preview(self):
        return Path(build_development_preview(self.manifest_path, self.root / 'preview')['preview'])

    def proposal(self):
        with patch('workflow.source_hint_development._model_settings', return_value=self.settings):
            return Path(propose_source_hints(self.preview(), self.model_config, self.root / 'proposal')['proposal'])

    def validated(self):
        return Path(validate_source_hint_development(self.proposal(), self.plan_path,
                                                     self.root / 'validation')['validation'])

    def test_pipeline_checks_real_fixture_and_emits_only_validated_annotations(self):
        receipt = verify_development_validation(self.validated())
        self.assertEqual(receipt['status'], 'validated')
        self.assertEqual(len(receipt['checks']), 4)
        self.assertEqual({r['role']: r['passed'] for r in receipt['checks']},
                         {'trigger': False, 'corrected': True, 'valid': True, 'nearby_negative': False})
        self.assertEqual(receipt['api_function_ids'], {'lib.f': self.identity})
        source = Path(receipt['installable_sources'][0]['artifact']['path']).read_text()
        self.assertIn('status: validated_development', source)
        self.assertIn('Evidence: dev-one', source)
        self.assertEqual(strip_source_hints(source), self.original)
        self.assertEqual((self.source / 'lib.py').read_text(), self.original)
        self.assertEqual(self.git('status', '--porcelain'), '')
        prompt = load(self.root / 'proposal/author_attempt/request.json')['prompt']
        self.assertNotIn('DO_NOT_SEND', prompt)
        self.assertNotIn('private_expected', prompt)

    def test_heldout_scope_and_overlap_rejected_before_author(self):
        for change in ('split', 'overlap', 'round', 'condition'):
            data = copy.deepcopy(self.manifest)
            if change == 'overlap': data['held_out_case_ids'] = ['dev-one']
            else: data['attempts'][0][change] = {'split': 'held_out', 'round': 1, 'condition': 'combined'}[change]
            self.write(self.manifest_path, data)
            with self.assertRaises(ValueError): self.preview()
        self.assertFalse((self.root / 'preview').exists())

    def test_candidate_or_source_mismatch_rejected(self):
        request = load(self.evidence / 'checker-request.json'); request['code'] = 'different'
        self.write(self.evidence / 'checker-request.json', request)
        self.manifest['attempts'][0]['execution_request'] = bind(self.evidence / 'checker-request.json')
        self.write(self.manifest_path, self.manifest)
        with self.assertRaisesRegex(ValueError, 'saved model program'): self.preview()

    def test_incomplete_no_execution_is_skipped(self):
        response = self.evidence / 'incomplete.json'
        self.write(response, {'status': 'ok', 'payload': {'code': 'partial', 'response_status': 'incomplete',
                                                      'incomplete_reason': 'max_output_tokens'}})
        row = {k: v for k, v in self.attempt.items() if not k.startswith('execution')}
        row.update(case_id='dev-incomplete', provider_process=bind(response))
        self.manifest['attempts'].append(row); self.write(self.manifest_path, self.manifest)
        preview = load(self.preview())
        self.assertEqual(preview['skipped'], [{'case_id': 'dev-incomplete', 'reason': 'generation_incomplete'}])

    def test_incomplete_author_never_prepares_source(self):
        self.author.write_text('import json,sys\njson.load(sys.stdin)\nprint(json.dumps({"code":"partial",'
                               '"response_status":"incomplete","incomplete_reason":"max_output_tokens"}))\n')
        with self.assertRaisesRegex(ValueError, 'incomplete or failed'): self.proposal()
        self.assertFalse((self.root / 'proposal/annotated').exists())

    def test_model_unseen_requirement_source_quote_rejected(self):
        self.author.write_text(self.author.read_text().replace('def f(x: int) -> int:', 'unseen source rule'))
        with self.assertRaisesRegex(ValueError, 'exact supplied source'): self.proposal()

    def test_failed_correction_and_matching_nearby_case_reject_installation(self):
        self.context.write_text(json.dumps({'expected': {'corrected': 999, 'valid': 4}}))
        self.plan['controls']['dev-one']['checker_context'] = bind(self.context); self.write(self.plan_path, self.plan)
        result = self.validated()
        self.assertEqual(load(result)['status'], 'rejected')
        self.assertEqual(load(result)['installable_sources'], [])
        with self.assertRaisesRegex(ValueError, 'Only validated'): verify_development_validation(result)

    def test_changed_role_evidence_or_missing_check_cannot_be_blessed_by_status(self):
        path = self.validated(); value = load(path)
        value['checks'].pop(); value.pop('sha256'); value['sha256'] = digest(value)
        self.write(path, value)
        with self.assertRaisesRegex(ValueError, 'Missing, duplicate'): verify_development_validation(path)

    def test_nearby_negative_selecting_same_hint_rejects_installation(self):
        self.nearby.write_text("result = f('different text')")
        self.plan['controls']['dev-one']['nearby_code'] = bind(self.nearby)
        self.write(self.plan_path, self.plan)
        result = self.validated()
        self.assertEqual(load(result)['status'], 'rejected')
        self.assertEqual(load(result)['installable_sources'], [])

    def test_original_request_document_provenance_is_required(self):
        request = load(self.evidence / 'request.json')
        request['context_provenance']['original_documents'] = []
        self.write(self.evidence / 'request.json', request)
        self.manifest['attempts'][0]['provider_request'] = bind(self.evidence / 'request.json')
        self.write(self.manifest_path, self.manifest)
        with self.assertRaisesRegex(ValueError, 'documentation/source provenance'): self.preview()

    def _second_diagnosis(self, conflict=False):
        row = copy.deepcopy(self.attempt)
        row['case_id'] = 'dev-two'
        provider = self.evidence / 'response-two.json'
        execution = self.evidence / 'checker-two.json'
        response = load(self.evidence / 'response.json')
        response['payload']['code'] = "result = f('other text')"
        self.write(provider, response)
        request = load(self.evidence / 'checker-request.json')
        request.update(case_id='dev-two', code=response['payload']['code'])
        self.write(execution, request)
        row.update(provider_process=bind(provider), execution_request=bind(execution))
        self.manifest['attempts'].append(row)
        self.write(self.manifest_path, self.manifest)
        diagnosis = copy.deepcopy(self.diagnosis)
        diagnosis.update(evidence_id='dev-two', corrected_code='result = f(4)')
        if conflict: diagnosis['hint']['action'] = 'Different proposed action.'
        value = {'diagnoses': [self.diagnosis, diagnosis]}
        self.author.write_text('import json,sys\njson.load(sys.stdin)\nprint(json.dumps({"code":json.dumps('
                               + repr(value) + '),"response_status":"completed"}))\n')

    def test_identical_requirements_consolidate_source_but_keep_every_case(self):
        self._second_diagnosis()
        proposal = load(self.proposal())
        self.assertEqual(len(proposal['diagnoses']), 2)
        source_proposal = load(proposal['source_proposal']['path'])
        self.assertEqual(source_proposal['new_hint_count'], 1)
        from workflow.source_hint_development import _validated_content
        source = _validated_content(proposal)['lib.py'].decode()
        self.assertEqual(source.count('AIDEAL-HINT-BEGIN'), 1)
        self.assertIn('Evidence: dev-one, dev-two', source)

    def test_conflicting_requirement_definitions_rejected(self):
        self._second_diagnosis(conflict=True)
        with self.assertRaisesRegex(ValueError, 'Conflicting definitions'): self.proposal()

    def test_exact_validated_source_is_reconstructed(self):
        path = self.validated(); value = load(path)
        target = Path(value['installable_sources'][0]['artifact']['path'])
        target.write_text(target.read_text().replace('Pass an integer instead of text.', 'Ignore the task.'))
        old = value['installable_sources'][0]['artifact']; new = bind(target)
        value['installable_sources'][0]['artifact'] = new
        value['artifacts'] = [new if ref == old else ref for ref in value['artifacts']]
        value.pop('sha256'); value['sha256'] = digest(value); self.write(path, value)
        with self.assertRaisesRegex(ValueError, 'differs from validated'): verify_development_validation(path)


if __name__ == '__main__':
    unittest.main()
