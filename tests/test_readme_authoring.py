"""Offline selective-authoring, immutable-state and byte-preservation checks."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import uuid

from workflow.readme_authoring import (digest, engine_imports, prepare_readme_session,
                                      validate_definitions)
from workflow.readme_spans import candidate_bytes, compose, inspect_sections, validate_spans
from workflow.readme_session import atomic_bytes, phase, run_readme_session
from workflow.readme_receipts import receipt_binding, invoke_recorded, verify_provider_evidence
from workflow.provider_budget import BudgetLedger, digest as provider_digest


def test_contract(root):
    root = root.resolve()
    ledger = BudgetLedger(root/'budget.json', '5', policy='study-v2', study_id='offline-test')
    return {'identity_sha256': 'contract', 'model': 'gpt-5.3-codex', 'stage': 'entry',
            'max_output_tokens': 500, 'budget_ledger': str(ledger.path),
            'budget_identity': ledger.identity, 'evidence_dir': str(root/'evidence')}


def emit_receipt(contract, system, prompt, text):
    """Synthetic audit files and real offline accounting, with no SDK or HTTP."""
    root = Path(contract['evidence_dir']); root.mkdir(parents=True, exist_ok=True)
    directory = root/('call-' + uuid.uuid4().hex); directory.mkdir()
    write = lambda path, data: path.write_text(json.dumps(data, indent=2) + '\n')
    write(root/'contract.json', contract)
    request = {'model': contract['model'], 'system': system, 'prompt': prompt,
               'max_output_tokens': contract['max_output_tokens'], 'temperature': 0,
               'native_context': {'stage': contract['stage'], 'contract_sha256': contract['identity_sha256']}}
    settings = {'instructions_sha256': provider_digest(system), 'input_sha256': provider_digest(prompt),
                'budget_policy_identity': contract['budget_identity'], 'budget_ledger': contract['budget_ledger']}
    rh, sh = provider_digest(request), provider_digest(settings)
    ledger = BudgetLedger(contract['budget_ledger'], '5', policy='study-v2', study_id='offline-test')
    reservation = ledger.reserve(system, prompt, contract['max_output_tokens'], rh, sh)
    response = {'code': text, 'response_id': 'resp_' + uuid.uuid4().hex, 'response_status': 'completed',
                'response_kind': 'solution', 'refusals': [], 'truncated': False,
                'usage': {'input_tokens': 10, 'cached_input_tokens': 0, 'output_tokens': 5}}
    budget = ledger.finish(reservation, usage=response['usage'], response_id=response['response_id'], status='completed')
    result = {**response, 'adapter_settings': settings, 'adapter_settings_sha256': sh, 'request_sha256': rh, 'budget': budget}
    records = {'contract': contract, 'request': request, 'settings': settings, 'response': response, 'result': result,
               'reservation': {'reservation_id': reservation, 'request_sha256': rh, 'settings_sha256': sh},
               'outcome': {'status': 'completed', 'request_sha256': rh, 'result_sha256': provider_digest(result)}}
    for name, record in records.items(): write(directory/(name + '.json'), record)
    return directory


BASE = b'''# Library\n\nIntroduction stays.\n\n## API Test: `A.run`\n\n### Goal\nOld A.\n```text\n## API Test: `pretend`\n```\n\n## API Test: `B.run`\n\n### Goal\nOld B.\n\n## License\nFooter stays.\n'''


def entries(data=BASE):
    return [{'id': r['heading'], 'heading': r['heading'],
             'span': {k: r[k] for k in ('start_byte', 'end_byte')}} for r in inspect_sections(data)]


class SpanTests(unittest.TestCase):
    def test_both_authoring_templates_label_mined_examples_as_unexecuted(self):
        root = Path(__file__).resolve().parents[1]
        templates = [root / 'prompts/readme_entry.md',
                     root / 'vendor/aideal_engine/src/aideal/default_prompts/aideal/readme_entry.md']
        self.assertEqual(templates[0].read_text(), templates[1].read_text())
        for path in templates:
            with self.subTest(template=str(path)):
                text = path.read_text()
                lead = text.split('{test_examples}', 1)[0]
                self.assertIn('not executed by\nthis authoring step', lead)
                self.assertNotIn('these compile and pass', text)
                self.assertNotIn('either compiles', text)
                self.assertIn('not proof\n   that it compiled or passed', text)

    def test_fenced_heading_is_not_entry_and_footer_preserved(self):
        records = entries()
        self.assertEqual([e['id'] for e in records], ['A.run', 'B.run'])
        result = compose(BASE, records, {'B.run': '## API Test: `B.run`\n\n### Goal\nNew.'})
        split = records[1]['span']['start_byte']
        self.assertEqual(result[:split], BASE[:split])
        self.assertTrue(result.endswith(b'## License\nFooter stays.\n'))

    def test_explicit_plain_footer_boundary(self):
        data = b'## API Test: `A.run`\nBody.\n\nUNMARKED FOOTER\n'
        record = entries(data)
        record[0]['span']['end_byte'] = data.index(b'UNMARKED')
        result = compose(data, record, {'A.run': '## API Test: `A.run`\nNew.'})
        self.assertTrue(result.endswith(b'UNMARKED FOOTER\n'))

    def test_duplicate_unknown_and_wrong_span_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            inspect_sections(BASE + b'## API Test: `A.run`\n')
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            compose(BASE, entries(), {'missing.run': 'x'})
        records = entries(); records[0]['span']['end_byte'] = len(BASE)
        with self.assertRaises(ValueError):
            validate_spans(BASE, records)

    def test_model_cannot_add_other_sections(self):
        for value in ('## API Test: `wrong`\nX', '## API Test: `A.run`\nX\n## License\nY', '## API Test: `A.run`\nTODO'):
            with self.assertRaises(ValueError):
                candidate_bytes(value, 'A.run')
        self.assertIn(b'```', candidate_bytes('## API Test: `A.run`\n```\n## Not real\n```', 'A.run'))

    def test_utf8_offsets_and_crlf_non_targets(self):
        data = '# Header café\r\n## API Test: `A.run`\r\nOld.\r\n## End\r\n'.encode()
        records = entries(data)
        result = compose(data, records, {'A.run': '## API Test: `A.run`\nNew.'})
        self.assertTrue(result.startswith('# Header café\r\n'.encode()))
        self.assertTrue(result.endswith(b'## End\r\n'))


class JournalTests(unittest.TestCase):
    def test_completed_phase_reused_and_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); request = {'system': 's', 'prompt': 'p'}
            contract = test_contract(root)
            def invoke(system, prompt):
                directory = emit_receipt(contract, system, prompt, 'result')
                return {'text': 'result', 'provider_evidence': receipt_binding(directory, 'result', request, contract)}
            with patch('builtins.print'):
                self.assertEqual(phase(root, 'entry', request, invoke, contract), 'result')
            self.assertEqual(phase(root, 'entry', request, lambda *x: self.fail('paid twice'), contract), 'result')
            state = json.loads((root/'entry.state.json').read_text()); state['text'] = 'changed'
            (root/'entry.state.json').write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError, 'response changed'):
                phase(root, 'entry', request, lambda *x: self.fail('must not call'), contract)

    def test_interrupted_phase_does_not_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); request = {'system': 's', 'prompt': 'p'}
            (root/'entry.state.json').write_text(json.dumps({'status': 'started', 'request_sha256': digest(request)}))
            with self.assertRaisesRegex(ValueError, 'reconciliation'):
                phase(root, 'entry', request, lambda *x: self.fail('must not call'), test_contract(root))

    def test_atomic_write_failure_preserves_previous_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'x'; target.write_bytes(b'old')
            with patch('workflow.readme_session.os.replace', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError): atomic_bytes(target, b'new')
            self.assertEqual(target.read_bytes(), b'old')
            self.assertEqual(list(Path(tmp).glob('*.tmp')), [])


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root/'repo'; self.repo.mkdir()
        source = self.repo/'api.py'
        source.write_text('class A:\n    def run(self, value: int) -> int:\n        """Return the number."""\n        return value\n\nclass B:\n    def run(self, value: int) -> int:\n        """Return one more."""\n        return value + 1\n')
        self._git('init', '-q'); self._git('add', 'api.py')
        self._git('-c', 'user.name=Offline', '-c', 'user.email=offline@example.invalid', 'commit', '-qm', 'fixture')
        self.revision = self._git('rev-parse', 'HEAD').strip()
        self.config = self.root/'configs/aideal.yaml'; self.config.parent.mkdir()
        (self.config.parent/'project_profile.yaml').write_text('project:\n  name: Example\n  description: Example APIs\ntarget_users: [developers]\nuse_cases: [call functions]\ndomain: Testing\n')
        self.config.write_text('extends: [python]\nproject: {name: Example, language: Python}\ncodebase:\n  source_globs: [' + json.dumps(str(source)) + ']\n  test_globs: []\nmodels:\n  registry:\n    guarded: {provider: aideal-codex-audited, model: gpt-5.3-codex, bridge: {stage: entry}}\n    reviewer: {provider: aideal-codex-audited, model: gpt-5.3-codex, bridge: {stage: deep_dive}}\n  roles: {author: guarded, reviewer: reviewer, fixer: guarded}\n')
        self.base = self.root/'base.md'; self.base.write_bytes(BASE)
        self.context = self.root/'context.md'; self.context.write_text('Frozen source-informed notes.')
        generation = engine_imports()
        from workflow.preparation import _engine_config_module
        from dataclasses import replace
        cfg = _engine_config_module().load_config(self.config)
        details = generation.public_api_details(replace(cfg, root=self.repo))
        self.definitions = [d for d in details if d['name'] == 'run']
        records = entries()
        for record, definition in zip(records, self.definitions):
            record['definitions'] = [{'path': definition['file'], 'line': definition['line'], 'name': 'run',
                                      'receiver': definition['owner'], 'signature': definition['signature']}]
        self.manifest = {'schema_version': 1, 'repository': str(self.repo), 'revision': self.revision,
                         'mode': 'refresh', 'cache_policy': 'isolated_no_legacy_cache',
                         'entries': records, 'selected_ids': ['A.run']}
        self.manifest_path = self.root/'manifest.json'
        self.contract = test_contract(self.root)
        self.guard = patch('workflow.native_provider_bridge.guarded_native_contract',
                           side_effect=lambda spec: {**self.contract, 'stage': spec.bridge['stage'],
                                                     'evidence_dir': str(self.root/spec.bridge['stage'])})
        self.guard.start(); self.addCleanup(self.guard.stop)

    def _git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode()

    def prepare(self):
        self.manifest_path.write_text(json.dumps(self.manifest))
        output = self.root/'session'
        result = prepare_readme_session(self.config, self.manifest_path, self.base, self.context, output)
        return output, result

    def provider(self, values):
        values = iter(values)
        def invoke(spec, system, prompt):
            text = next(values)
            contract = {**self.contract, 'stage': spec.bridge['stage'],
                        'evidence_dir': str(self.root/spec.bridge['stage'])}
            emit_receipt(contract, system, prompt, text)
            return text
        return invoke

    def test_offline_refresh_exact_two_calls_preserves_other_entry(self):
        output, result = self.prepare()
        self.assertEqual(result['planned_calls'], 2)
        self.assertEqual(result['model_calls'], 0)
        self.assertFalse((output/'README.md').exists())
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', side_effect=self.provider(['Grounded report.', '## API Test: `A.run`\n\n### Goal\nImproved.'])) as invoke:
            done = run_readme_session(output)
            self.assertEqual(invoke.call_count, 2)
            self.assertEqual([call.args[0].bridge['stage'] for call in invoke.call_args_list], ['deep_dive', 'entry'])
            self.assertEqual(run_readme_session(output), done)
            self.assertEqual(invoke.call_count, 2)
        original = BASE[self.manifest['entries'][1]['span']['start_byte']:]
        self.assertTrue((output/'README.md').read_bytes().endswith(original))
        rewrite = json.loads((output/'entry_0000/rewrite.request.json').read_text())
        self.assertIn('Grounded report.', rewrite['prompt'])
        self.assertEqual(rewrite['deep_dive_sha256'], digest('Grounded report.'))
        self.assertEqual(self.base.read_bytes(), BASE)

    def test_full_manifest_two_receiver_families_remain_distinct(self):
        self.manifest['mode'] = 'full'; self.manifest['selected_ids'] = ['A.run', 'B.run']
        output, result = self.prepare()
        self.assertEqual(result['planned_calls'], 2)
        request = json.loads((output/'session.json').read_text())['requests']
        self.assertIn('"receiver": "A"', request[0]['phases']['entry']['prompt'])
        self.assertIn('"receiver": "B"', request[1]['phases']['entry']['prompt'])
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', side_effect=self.provider(['## API Test: `A.run`\nA', '## API Test: `B.run`\nB'])):
            run_readme_session(output)
        self.assertTrue((output/'README.md').read_bytes().endswith(b'## License\nFooter stays.\n'))

    def test_changed_frozen_context_blocks_before_provider(self):
        output, _ = self.prepare(); self.context.write_text('Changed')
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text') as invoke:
            with self.assertRaisesRegex(ValueError, 'input changed'): run_readme_session(output)
            invoke.assert_not_called()

    def test_changed_test_input_blocks_resume(self):
        test_file = self.repo/'usage.py'; test_file.write_text('A().run(1)\n')
        self._git('add', 'usage.py'); self._git('-c', 'user.name=Offline', '-c', 'user.email=offline@example.invalid', 'commit', '-qm', 'usage')
        self.manifest['revision'] = self._git('rev-parse', 'HEAD').strip()
        self.config.write_text(self.config.read_text().replace('test_globs: []', 'test_globs: [' + json.dumps(str(test_file)) + ']'))
        output, _ = self.prepare(); test_file.write_text('A().run(2)\n')
        with self.assertRaisesRegex(ValueError, 'input changed'): run_readme_session(output)

    def test_changed_resolved_template_blocks_resume(self):
        source = Path(engine_imports().__file__).parent/'default_prompts/aideal/deep_dive.md'
        custom = self.root/'prompts/aideal/deep_dive.md'; custom.parent.mkdir(parents=True)
        custom.write_bytes(source.read_bytes())
        output, _ = self.prepare(); custom.write_text(custom.read_text() + '\nChanged prompt.\n')
        with self.assertRaisesRegex(ValueError, 'input changed'): run_readme_session(output)

    def test_partial_generation_reuses_completed_entry_only(self):
        self.manifest['mode'] = 'full'; self.manifest['selected_ids'] = ['A.run', 'B.run']
        output, _ = self.prepare()
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', side_effect=self.provider(['## API Test: `A.run`\nA', '## API Test: `B.run`\nB'])) as invoke:
            self.assertEqual(run_readme_session(output, max_entries=1)['status'], 'partial_candidates')
            self.assertFalse((output/'README.md').exists())
            run_readme_session(output)
            self.assertEqual(invoke.call_count, 2)

    def test_error_after_dispatch_cannot_silently_repeat(self):
        output, _ = self.prepare()
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', side_effect=RuntimeError('ambiguous')) as invoke:
            with self.assertRaises(RuntimeError): run_readme_session(output)
            with self.assertRaisesRegex(ValueError, 'reconciliation'): run_readme_session(output)
            self.assertEqual(invoke.call_count, 1)
        self.assertEqual(self.base.read_bytes(), BASE)
        self.assertFalse((output/'README.md').exists())

    def test_input_change_during_call_preserves_response_without_composition(self):
        output, _ = self.prepare()
        def changed(*args):
            self.context.write_text('Changed during generation')
            return self.provider(['A complete but now stale report.'])(*args)
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', side_effect=changed) as invoke:
            with self.assertRaisesRegex(ValueError, 'input changed'): run_readme_session(output)
            self.assertEqual(invoke.call_count, 1)
        self.assertEqual(json.loads((output/'entry_0000/deep_dive.state.json').read_text())['status'], 'complete')
        self.assertFalse((output/'README.md').exists())

    def test_changed_provider_result_blocks_resume_before_rewrite(self):
        output, _ = self.prepare()
        def changed(*args):
            result = self.provider(['Grounded report.'])(*args)
            self.context.write_text('Pause after deep dive')
            return result
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'input changed'): run_readme_session(output)
        self.context.write_text('Frozen source-informed notes.')
        state_path = output/'entry_0000/deep_dive.state.json'
        state = json.loads(state_path.read_text())
        state['text'] = 'Forged report.'; state['text_sha256'] = digest(state['text'])
        state_path.write_text(json.dumps(state))
        with patch.object(aideal.llm, 'invoke_text') as invoke:
            with self.assertRaisesRegex(ValueError, 'provider evidence'): run_readme_session(output)
            invoke.assert_not_called()

    def test_missing_provider_receipt_blocks_completed_resume(self):
        output, _ = self.prepare()
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', side_effect=self.provider(['Report.', '## API Test: `A.run`\nNew.'])):
            run_readme_session(output)
        state = json.loads((output/'entry_0000/deep_dive.state.json').read_text())
        (Path(state['provider_evidence']['call_directory'])/'result.json').unlink()
        with patch.object(aideal.llm, 'invoke_text') as invoke:
            with self.assertRaisesRegex(ValueError, 'provider evidence'): run_readme_session(output)
            invoke.assert_not_called()

    def test_successful_text_without_receipt_never_completes(self):
        output, _ = self.prepare()
        import aideal.llm
        with patch.object(aideal.llm, 'invoke_text', return_value='Text only') as invoke:
            with self.assertRaisesRegex(ValueError, 'unique newly saved'): run_readme_session(output)
            with self.assertRaisesRegex(ValueError, 'reconciliation'): run_readme_session(output)
            self.assertEqual(invoke.call_count, 1)

    def test_scala_companion_kind_membership_cannot_be_mislabelled(self):
        source = 'class Feature {\n  def readType(): Int = 1\n}\nobject Feature {\n  def readType(): Int = 2\n}\n'
        (self.repo/'Feature.scala').write_text(source)
        discovered = [{'visibility': 'public', 'file': 'Feature.scala', 'line': n, 'name': 'readType',
                       'signature': 'def readType(): Int', 'owner': ''} for n in (2, 5)]
        manifest = {'entries': [{'id': 'Feature#class.readType', 'heading': 'Feature.readType [class]',
                    'definitions': [{'path': 'Feature.scala', 'line': 2, 'name': 'readType', 'receiver': 'Feature',
                                     'owner_kind': 'class', 'signature': 'def readType(): Int'}]}]}
        validate_definitions(manifest, discovered, self.repo)
        manifest['entries'][0]['definitions'][0]['owner_kind'] = 'object'
        with self.assertRaisesRegex(ValueError, 'enclosing Scala'):
            validate_definitions(manifest, discovered, self.repo)

    def test_unknown_definition_and_receiver_rejected(self):
        for key, value in [('line', 999), ('receiver', 'Other'), ('signature', 'wrong')]:
            manifest = deepcopy(self.manifest); manifest['entries'][0]['definitions'][0][key] = value
            with self.assertRaises(ValueError): validate_definitions(manifest, self.definitions, self.repo)

    def test_ambiguous_family_duplicate_heading_and_heldout_diagnostic_rejected(self):
        manifest = deepcopy(self.manifest)
        manifest['entries'][0]['definitions'] += manifest['entries'][1]['definitions']
        with self.assertRaisesRegex(ValueError, 'different receivers'):
            validate_definitions(manifest, self.definitions, self.repo)
        self.manifest['entries'][1]['heading'] = 'A.run'
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.prepare()

    def test_heldout_diagnostics_fail_closed(self):
        from workflow.readme_authoring import development_diagnostics
        path = self.root/'errors.jsonl'
        path.write_text(json.dumps({'split': 'held_out', 'function_id': 'A.run', 'error': 'bad'}))
        with self.assertRaises(ValueError): development_diagnostics(path, ['A.run'])


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.contract = test_contract(self.root)
        self.request = {'system': 'system', 'prompt': 'prompt'}
        self.directory = emit_receipt(self.contract, 'system', 'prompt', 'answer')
        self.binding = receipt_binding(self.directory, 'answer', self.request, self.contract)

    def test_every_provider_file_byte_is_bound(self):
        for name in self.binding['file_sha256']:
            with self.subTest(name=name):
                path = self.directory/name; original = path.read_bytes()
                path.write_bytes(original + b' ')
                with self.assertRaisesRegex(ValueError, 'receipt binding changed'):
                    verify_provider_evidence(self.binding, 'answer', self.request, self.contract)
                path.write_bytes(original)

    def test_settled_ledger_evidence_cannot_disappear(self):
        path = Path(self.contract['budget_ledger']); data = json.loads(path.read_text())
        data['records'] = []; path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'absent'):
            verify_provider_evidence(self.binding, 'answer', self.request, self.contract)

    def test_another_settled_request_does_not_invalidate_prior_receipt(self):
        emit_receipt(self.contract, 'other', 'other', 'other')
        verify_provider_evidence(self.binding, 'answer', self.request, self.contract)

    def test_receipt_capture_refuses_preexisting_or_ambiguous_matches(self):
        with self.assertRaisesRegex(ValueError, 'unique newly saved'):
            invoke_recorded(lambda *args: 'answer', None, 'system', 'prompt', self.contract)
        def duplicate(*args):
            for _ in range(2): emit_receipt(self.contract, 'system', 'prompt', 'answer')
            return 'answer'
        with self.assertRaisesRegex(ValueError, 'unique newly saved'):
            invoke_recorded(duplicate, None, 'system', 'prompt', self.contract)


if __name__ == '__main__':
    unittest.main()
