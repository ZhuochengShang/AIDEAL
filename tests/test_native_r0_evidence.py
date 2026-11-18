"""Recorded native evidence only: no subject imports, execution, or real model."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml
from aideal.config import load_config
from aideal.doc_check_provenance import _sha256_files
from workflow.ablation import bind, digest, load
from workflow.native_r0_evidence import PROTOCOL
from workflow.source_hint_development import build_development_preview
from workflow.native_hints import propose_native_hints


class NativeR0EvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='aideal-native-intake-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.source = self.root / 'source'; self.source.mkdir()
        self.text = ('raise RuntimeError("FIXTURE MUST NEVER BE IMPORTED")\n\n'
            'def f(x):\n    if x < 0:\n        raise ValueError("Input must be nonnegative.")\n'
            '    return x\n\ndef g(x):\n    return f(x)\n')
        (self.source / 'lib.py').write_text(self.text)
        (self.source / 'README.md').write_text('f and g accept a nonnegative integer.')
        self.git('init', '-q'); self.git('add', '.'); self.git('commit', '-qm', 'Pinned fixture')
        self.revision = self.git('rev-parse', 'HEAD')
        self.run = self.root / 'run'; (self.run / 'configs').mkdir(parents=True)
        (self.run / 'inputs').mkdir()
        self.inventory = self.run / 'inputs/inventory.json'
        self.write(self.inventory, {'kind': 'qualified_source_api_inventory', 'source_commit': self.revision})
        self.config = self.run / 'configs/aideal.yaml'
        self.raw = {'project': {'name': 'fixture', 'language': 'Python'},
            'codebase': {'identity_mode': 'qualified', 'api_inventory': 'inputs/inventory.json',
                         'api_inventory_sha256': bind(self.inventory)['sha256']},
            'files': {'original_readme': str(self.source / 'README.md')},
            'comprehension': {'execute': {'test_filename': 'Generated.py', 'success_marker': 'DONE',
                'correctness_marker': '__CHECK__', 'require_correctness_check': True}}}
        self.config.write_text(yaml.safe_dump(self.raw))
        self.names = ['python:lib.f', 'python:lib.g']
        self.rows = [{'api_id': api, 'name': api.rsplit('.', 1)[-1], 'qualified_name': api[7:],
            'owner': 'lib', 'file': str(self.source / 'lib.py'), 'line': line,
            'source_sha256': bind(self.source / 'lib.py')['sha256'], 'signature': 'def '+api[-1]+'(x)',
            'public_access_paths': [api[7:]]} for api, line in zip(self.names, [3, 8])]
        registry = patch('aideal.api_discovery.public_api_details', side_effect=lambda cfg: deepcopy(self.rows))
        registry.start(); self.addCleanup(registry.stop)
        self.write(self.run / 'inputs/api_manifest.json', self.names)
        self.write(self.run / 'launch.json', {'documentation': 'original', 'source': str(self.source)})
        self.result = {'check': 'comprehension', 'mode': 'execute', 'doc_source': 'original',
            'run': {'run_id': 'fixture-r0', 'manifest_sha256': hashlib.sha256('\n'.join(self.names).encode()).hexdigest(),
                    'checkpoint': str(self.run/'execution/comprehension_progress.jsonl')},
            'metrics': {}}
        self.manifest = {'schema_version': 1, 'evidence_protocol': PROTOCOL,
            'source_root': str(self.source), 'baseline_revision': self.revision,
            'split': 'development', 'condition': 'original', 'round': 0,
            'original_documents': [bind(self.source / 'README.md')], 'held_out_case_ids': [],
            'native_run': {'root': str(self.run)}}
        self.manifest_path = self.root / 'manifest.json'
        self.diagnostic = (f'Traceback (most recent call last):\n  File "{self.source}/lib.py", line 5, in f\n'
                           '    raise ValueError("Input must be nonnegative.")\n'
                           'ValueError: Input must be nonnegative.\n')
        self.add_attempt('python:lib.g')
        self.save()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), '-c', 'user.name=Fixture',
            '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
            '-c', 'core.hooksPath=/dev/null', *args], text=True, stderr=subprocess.DEVNULL).strip()

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value, indent=2)+'\n')

    def add_attempt(self, api, number=1, *, rc=1, provider='returned', diagnostic=None, round=0):
        directory = self.run / 'execution' / ('run_'+api[-1]) / f'attempt_{number:04d}'
        directory.mkdir(parents=True)
        row = next(row for row in self.rows if row['api_id'] == api)
        target = {key: row[key] for key in ('api_id', 'qualified_name', 'owner', 'signature')}
        target['target_fingerprint'] = digest(target)
        self.write(directory / 'request.json', {'api': api, 'round': round, 'run_id': 'fixture-r0',
            'system': 'Exact audience system.', 'user': 'Exact original task for '+api+'.',
            'requested_target_declaration': target})
        self.write(directory / 'provider.json', {'status': provider, 'usage': {'input_tokens': 12, 'output_tokens': 7}})
        if provider == 'returned':
            (directory / 'response.txt').write_text('```python\ng(-1)\n```')
            (directory / 'Generated.py').write_text('from lib import g\ng(-1)\n')
            self.write(directory / 'execution.json', {'exit_code': rc, 'command': 'python Generated.py',
                'cwd': str(self.run / 'execution'), 'timeout_s': 10})
            (directory / 'stdout.txt').write_text('DONE\n__CHECK__ result\n' if rc == 0 else '')
            (directory / 'stderr.txt').write_text(self.diagnostic if diagnostic is None else diagnostic)
        metric = self.result['metrics'].setdefault(api, {'status': 'fail', 'attempt_evidence': [],
                                                       'private_expected': 'NEVER_SEND_PRIVATE'})
        metric['attempt_evidence'].append(str(directory))
        return directory

    def save(self):
        cfg = load_config(self.config)
        components = {'doc_source': 'original', 'manifest_sha256': self.result['run']['manifest_sha256'],
            'execute_config': cfg.comprehension['execute'],
            'original_document_files': _sha256_files([self.source/'README.md'], cfg.root)}
        self.result['run'].update(fingerprint_components=components, experiment_fingerprint=digest(components))
        checkpoint=[]
        for api, metric in self.result['metrics'].items():
            hashes=[]
            for directory in metric['attempt_evidence']:
                path=Path(directory)/'request.json'
                if path.exists():
                    request=load(path)
                    hashes.append(hashlib.sha256(json.dumps([request['system'],request['user']]).encode()).hexdigest())
            checkpoint.append({'name':api,'experiment_fingerprint':digest(components),
                               'attempt_evidence':metric['attempt_evidence'],'rendered_prompt_sha256':hashes or ['missing']})
        (self.run/'execution/comprehension_progress.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in checkpoint))
        self.write(self.run / 'result.json', self.result)
        self.manifest['native_run'].update({key: bind(self.run / path) for key, path in (
            ('result', 'result.json'), ('launch', 'launch.json'), ('config', 'configs/aideal.yaml'),
            ('api_manifest', 'inputs/api_manifest.json'))})
        self.write(self.manifest_path, self.manifest)

    def preview(self, name='preview', **kwargs):
        result = build_development_preview(self.manifest_path, self.root/name, **kwargs)
        return result, load(result['preview'])

    def test_actual_api_list_must_match_recorded_denominator_hash(self):
        self.write(self.run/'inputs/api_manifest.json',list(reversed(self.names)))
        self.save()
        with self.assertRaisesRegex(ValueError,'matching Original/source/config'):
            self.preview()

    def test_structured_manifest_preserves_full_binding_and_exact_ids(self):
        path = self.run / 'inputs/api_manifest.json'
        self.write(path, {'schema': 2, 'identity_mode': 'qualified',
                          'apis': self.names, 'api_names': self.names})
        self.save()
        result, preview = self.preview()
        self.assertEqual(1, result['cases'])
        self.assertIn(bind(path), preview['artifacts'])
        self.assertEqual(set(self.names), {row['api_id'] for row in preview['intake']})

    def test_structured_manifest_order_must_match_recorded_denominator(self):
        self.write(self.run / 'inputs/api_manifest.json',
                   {'schema': 2, 'identity_mode': 'qualified',
                    'apis': list(reversed(self.names)), 'api_names': self.names})
        self.save()
        with self.assertRaisesRegex(ValueError, 'matching Original/source/config'):
            self.preview()

    def test_structured_manifest_rejects_malformed_or_duplicate_ids(self):
        for names in [None, 'python:lib.f', [''], [5], [['python:lib.f']],
                      ['python:lib.f', 'python:lib.f']]:
            with self.subTest(names=names):
                self.write(self.run / 'inputs/api_manifest.json', {'apis': names})
                self.save()
                with self.assertRaisesRegex(ValueError, 'distinct exact IDs'):
                    self.preview()

    def test_structured_manifest_unknown_id_fails_even_with_matching_name_hash(self):
        names = [*self.names, 'python:lib.unknown']
        self.write(self.run / 'inputs/api_manifest.json', {'apis': names})
        self.result['run']['manifest_sha256'] = hashlib.sha256('\n'.join(names).encode()).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, 'outside the frozen bank'):
            self.preview()

    def test_structured_manifest_metadata_change_breaks_artifact_binding(self):
        path = self.run / 'inputs/api_manifest.json'
        data = {'schema': 2, 'identity_mode': 'qualified',
                'apis': self.names, 'api_names': self.names}
        self.write(path, data)
        self.save()
        # Metadata is not a second API selection source, but its exact bytes
        # remain part of the frozen evidence and cannot be changed in place.
        data['api_names'] = list(reversed(self.names))
        self.write(path, data)
        with self.assertRaisesRegex(ValueError, 'changed native R0 evidence'):
            self.preview()

    def test_uninstalled_cli_resolves_its_vendored_engine(self):
        import sys
        root=Path(__file__).resolve().parents[1]
        program=("import sys; sys.path.insert(0,"+repr(str(root))+"); "
                 "from workflow.native_r0_evidence import _inputs\n"
                 "try: _inputs({})\n"
                 "except (KeyError, ValueError): print('engine resolved before manifest validation')\n")
        result=subprocess.run([sys.executable,'-I','-c',program],capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertIn('engine resolved',result.stdout)

    def test_installed_source_requires_declared_root_and_identical_pinned_bytes(self):
        installed=self.root/'site-packages/demo';installed.mkdir(parents=True)
        (installed/'lib.py').write_text(self.text)
        attempt=Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        (attempt/'stderr.txt').write_text(self.diagnostic.replace(str(self.source),str(installed)))
        self.save();result,_=self.preview('no-runtime-mapping')
        self.assertEqual(0,result['cases'])
        self.manifest['runtime_source_roots']=[{'runtime_root':str(installed),'source_root':'.'}]
        self.save();result,preview=self.preview('mapped-runtime')
        self.assertEqual(1,result['cases'])
        self.assertEqual(bind(installed/'lib.py'),preview['cases'][0]['attribution']['runtime_source'])
        self.assertIn(bind(installed/'lib.py'),preview['artifacts'])
        (installed/'lib.py').write_text(self.text+'# changed runtime\n')
        self.save();result,_=self.preview('changed-runtime')
        self.assertEqual(0,result['cases'])

    def test_exact_native_evidence_and_distinct_requested_failing_api(self):
        result, preview = self.preview()
        self.assertEqual('ready_for_diagnosis', result['status'])
        case = preview['cases'][0]
        self.assertEqual('python:lib.g', case['requested_api_id'])
        self.assertEqual('python:lib.f', case['failing_api_id'])
        self.assertEqual('lib.py:3:lib.f', case['function_id'])
        self.assertEqual(self.diagnostic, case['diagnostic'].lstrip('\n'))
        self.assertEqual('from lib import g\ng(-1)\n', case['code'])
        self.assertEqual('Exact original task for python:lib.g.', case['audience_request']['prompt'])
        self.assertEqual('```python\ng(-1)\n```', case['native_evidence']['model_response'])
        self.assertEqual('returned', case['native_evidence']['provider_status'])
        self.assertEqual('python:lib.g',case['native_evidence']['requested_target_declaration']['api_id'])
        self.assertEqual('not_independently_recorded', case['native_evidence']['oracle_status'])
        self.assertNotIn('oracle_pass', json.dumps(case))
        self.assertEqual('not_recorded_in_checkpoint', preview['intake'][0]['disposition'])
        self.assertEqual(self.text, (self.source/'lib.py').read_text())

    def test_request_target_and_source_text_alone_never_prove_runtime_failure(self):
        attempt = Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        (attempt/'stderr.txt').write_text('ValueError: Input must be nonnegative.\n')
        self.save(); result, preview = self.preview()
        self.assertEqual('no_supported_native_failures', result['status'])
        self.assertEqual('no_supported_source_exception_frame', preview['skipped'][0]['reason'])

    def test_success_provider_error_compile_timeout_and_retry_are_all_recorded(self):
        self.add_attempt('python:lib.f', 1, rc=0)
        self.add_attempt('python:lib.f', 2, provider='error')
        self.add_attempt('python:lib.f', 3, diagnostic='error: expected identifier')
        self.add_attempt('python:lib.f', 4, rc=124)
        self.add_attempt('python:lib.f', 5, round=1)
        self.save(); _, preview = self.preview()
        self.assertEqual(1, len(preview['cases']))
        self.assertEqual(6, len(preview['intake']))
        self.assertEqual({'recorded_marker_pass','provider_failure','no_supported_source_exception_frame','timeout','not_r0'},
                         {row['reason'] for row in preview['skipped']})

    def test_success_marker_failure_is_not_promoted_to_an_exception(self):
        attempt = Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        process = load(attempt/'execution.json'); process['exit_code'] = 0
        self.write(attempt/'execution.json',process); self.save()
        _, preview = self.preview()
        self.assertEqual('marker_or_oracle_failure_without_exception',preview['skipped'][0]['reason'])

    def test_heldout_requested_or_failing_api_never_enters_author_context(self):
        for index, api in enumerate(self.names):
            self.manifest['held_out_api_ids'] = [api]; self.save()
            _, preview = self.preview('held-'+str(index))
            self.assertEqual([], preview['cases'])
            self.assertTrue(preview['skipped'][0]['reason'].startswith('held_out'))

    def test_target_identity_change_and_escaped_attempt_are_rejected(self):
        attempt = Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        request = load(attempt/'request.json'); request['requested_target_declaration']['api_id'] = 'python:lib.f'
        self.write(attempt/'request.json',request)
        with self.assertRaisesRegex(ValueError,'target differs'): self.preview()
        self.result['metrics']['python:lib.g']['attempt_evidence'] = [str(self.source)];self.save()
        with self.assertRaisesRegex(ValueError,'escaped execution'): self.preview()

    def test_original_documentation_and_manifest_binding_drift_block_intake(self):
        (self.source/'README.md').write_text('changed')
        with self.assertRaises(ValueError): self.preview()
        (self.source/'README.md').write_text('f and g accept a nonnegative integer.')
        (self.run/'result.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'changed native'): self.preview()

    def test_batch_limit_and_explicit_next_batch_do_not_drop_intake(self):
        self.add_attempt('python:lib.f'); self.save()
        _, first = self.preview(max_cases=1)
        omitted = next(row['case_id'] for row in first['skipped'] if row['reason']=='batch_limit')
        self.manifest['native_case_ids'] = [omitted]; self.save()
        _, second = self.preview('second',max_cases=1)
        self.assertEqual(2,len(second['intake']))
        self.assertEqual(omitted,second['cases'][0]['evidence_id'])

    def test_empty_intake_never_calls_author(self):
        attempt = Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        (attempt/'stderr.txt').write_text('compile failed'); self.save()
        result,_ = self.preview()
        with patch('workflow.native_hints.invoke',side_effect=AssertionError('No author for empty intake')) as call:
            outcome=propose_native_hints(result['preview'],self.root/'absent-model-config.json',self.root/'proposal')
        self.assertEqual(0,call.call_count);self.assertEqual(0,outcome['llm_calls'])

    def test_resumed_checkpoint_keeps_prior_provider_failure_and_prior_run_id(self):
        old = self.add_attempt('python:lib.f',provider='error'); self.save()
        checkpoint=self.run/'execution/comprehension_progress.jsonl'
        old_lines=checkpoint.read_text()
        # Native resume may replace the result metric while preserving the old
        # fingerprint-bound checkpoint row and its separate attempt artifacts.
        self.result['metrics'].pop('python:lib.f')
        self.result['run']['run_id']='new-invocation'
        self.write(self.run/'result.json',self.result)
        self.manifest['native_run']['result']=bind(self.run/'result.json')
        self.write(self.manifest_path,self.manifest)
        _,preview=self.preview()
        self.assertEqual(1,len(preview['cases']))
        self.assertIn('provider_failure',{row.get('disposition') for row in preview['intake']})
        accepted=next(row for row in preview['intake'] if row.get('disposition')=='accepted_for_diagnosis')
        self.assertEqual('fixture-r0',accepted['recorded_run_id'])
        self.assertEqual(old_lines,checkpoint.read_text())

    def test_changed_prompt_without_checkpoint_update_is_rejected(self):
        attempt=Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        request=load(attempt/'request.json');request['user']='A different task'
        self.write(attempt/'request.json',request)
        with self.assertRaisesRegex(ValueError,'rendered prompt differs'):self.preview()

    def test_crash_artifacts_without_checkpoint_are_retained_but_not_promoted(self):
        directory=self.add_attempt('python:lib.f')
        self.result['metrics'].pop('python:lib.f');self.save()
        _,preview=self.preview()
        orphan=next(row for row in preview['intake'] if row.get('disposition')=='unbound_attempt_not_promoted')
        self.assertEqual(str(directory),orphan['attempt_directory'])
        self.assertEqual(bind(directory/'stderr.txt'),orphan['evidence']['stderr.txt'])
        self.assertEqual(1,len(preview['cases']))

    def test_wrong_frame_line_or_source_exception_message_is_not_promoted(self):
        attempt=Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        for index,text in enumerate([self.diagnostic.replace('line 5','line 9'),
                                    self.diagnostic.replace('ValueError: Input must be nonnegative.', 'ValueError: Different error.')]):
            (attempt/'stderr.txt').write_text(text)
            _,preview=self.preview('wrong-'+str(index))
            self.assertEqual([],preview['cases'])

    def test_registered_sql_keeps_failure_evidence_without_guessing_implementation(self):
        self.write(self.inventory,{'kind':'registered_sql','source_commit':self.revision})
        self.raw['codebase']['api_inventory_sha256']=bind(self.inventory)['sha256']
        self.config.write_text(yaml.safe_dump(self.raw));self.save()
        _,preview=self.preview()
        self.assertEqual({},preview['api_function_ids'])
        self.assertEqual([],preview['cases'])
        self.assertTrue(preview['intake'][-1]['evidence'])

    def test_cython_failure_is_retained_but_not_given_a_python_message_patch(self):
        (self.source/'native.pyx').write_text('cpdef f(int x):\n    raise ValueError("Input must be nonnegative.")\n')
        self.git('add','native.pyx');self.git('commit','-qm','Cython fixture')
        self.revision=self.git('rev-parse','HEAD');self.manifest['baseline_revision']=self.revision
        self.write(self.inventory,{'kind':'qualified_source_api_inventory','source_commit':self.revision})
        self.raw['codebase']['api_inventory_sha256']=bind(self.inventory)['sha256']
        self.config.write_text(yaml.safe_dump(self.raw))
        self.rows[0].update(file=str(self.source/'native.pyx'),line=1,
                           source_sha256=bind(self.source/'native.pyx')['sha256'])
        attempt=Path(self.result['metrics']['python:lib.g']['attempt_evidence'][0])
        (attempt/'stderr.txt').write_text(f'  File "{self.source}/native.pyx", line 2, in f\nValueError: Input must be nonnegative.\n')
        self.save();_,preview=self.preview()
        self.assertEqual([],preview['cases'])
        self.assertEqual('no_supported_source_exception_frame',preview['skipped'][0]['reason'])

    def test_same_pipeline_author_receives_exact_evidence_without_private_fields(self):
        result, preview = self.preview(); case = preview['cases'][0]
        hint = {'function_id':case['function_id'],'evidence_id':case['evidence_id'],
            'requirement_id':'nonnegative','error_line':5,'original_message':'Input must be nonnegative.',
            'action':'Pass an integer at least zero.','source_quote':'raise ValueError("Input must be nonnegative.")',
            'corrected_code':'from lib import g\ng(2)\n'}
        model = self.root/'model.json';self.write(model,{'model':{}})
        captured=[]
        def author(command, request, directory, timeout):
            captured.append(request);directory.mkdir(parents=True)
            process={'status':'ok','payload':{'code':json.dumps({'hints':[hint],'unsupported_evidence_ids':[]}),
                      'response_status':'completed'}}
            self.write(directory/'request.json',request);self.write(directory/'process.json',process)
            return process
        settings={'command':['SYNTHETIC_NEVER_EXECUTED'],'name':'offline','temperature':0,'max_output_tokens':1000,'timeout_s':1}
        with patch('workflow.improvement_suggestions._model_settings',return_value=settings),patch('workflow.native_hints.invoke',side_effect=author):
            outcome=propose_native_hints(result['preview'],model,self.root/'proposal')
        request=captured[0]['prompt'];self.assertNotIn('NEVER_SEND_PRIVATE',request)
        sent=json.loads(request)['cases'][0]
        self.assertEqual(case['audience_request'],sent['audience_request'])
        self.assertEqual(case['code'],sent['code']);self.assertEqual(case['diagnostic'],sent['diagnostic'])
        proposal=load(outcome['proposal']);self.assertEqual('unvalidated',proposal['status'])
        changed=Path(proposal['sources'][0]['candidate']['path']).read_text()
        self.assertIn('[AIDEAL fix:nonnegative]',changed)
        self.assertEqual(self.text,(self.source/'lib.py').read_text())


if __name__ == '__main__':
    unittest.main()
