"""Offline identity/document contracts; all author boundaries are stubbed."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import unittest

from test_readme_modules import ReadmeFixtures


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


class QualifiedReadmeTests(ReadmeFixtures):
    def setUp(self):
        super().setUp()
        from aideal import readme_generation, doc_check_sources, original_documentation, readme_format
        self.generation = readme_generation
        self.sources = doc_check_sources
        self.documents = original_documentation
        self.format = readme_format
        self.keys = ['scala:demo.Reader.run', 'scala:demo.Writer.run']
        self.cfg.raw['codebase']['identity_mode'] = 'qualified'
        self.rows = [dict(name='run', api_id=key, identity_version='language_qualified_api_v1',
                         qualified_name=key.split(':', 1)[1], owner='demo.' + owner,
                         owner_kind='object', visibility='public', file='src/Ops.scala', line=i+2,
                         signature=f'def run(value: {typ}): {typ}',
                         params=[dict(name='value', type=typ, default=None)], returns=typ,
                         description='', parameter_count=1, parameter_count_status='known')
                     for i, (key, owner, typ) in enumerate(zip(self.keys, ['Reader', 'Writer'], ['Int', 'String']))]
        self.doc_dir = self.root / 'reviewed'
        self.doc_dir.mkdir()
        (self.doc_dir / 'corpus.md').write_text('Reader precise docs.\nWriter precise docs.\n')
        (self.doc_dir / 'reader.md').write_text('Reader.run receives an integer. Reader-only sentinel.')
        (self.doc_dir / 'writer.md').write_text('Writer.run receives text. Writer-only sentinel.')
        self.manifest = dict(schema='aideal.original-documents/v1', library='Offline',
                             source_version='1.0', source_commit='a'*40, source_tree='b'*40,
                             scope='Exact API-reference pages, not the entire website',
                             documents=[dict(id='api-page', path='corpus.md', kind='rendered_api',
                                             sha256=sha((self.doc_dir/'corpus.md').read_bytes()))],
                             targets={key: dict(status='documented', excerpts=[dict(
                                 path=name+'.md', sha256=sha((self.doc_dir/(name+'.md')).read_bytes()),
                                 document_id='api-page', origin_url='https://example.invalid/api', anchor=key)])
                                      for key, name in zip(self.keys, ['reader', 'writer'])})
        self.write_manifest()

    def write_manifest(self):
        path = self.doc_dir/'manifest.json'
        content = json.dumps(self.manifest, sort_keys=True).encode()
        path.write_bytes(content)
        self.cfg.raw['files'] = dict(original_doc_manifest=str(path), original_doc_manifest_sha256=sha(content))

    def discovery(self):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch.object(self.generation, 'public_api_details', return_value=self.rows))
        stack.enter_context(patch.object(self.generation, 'public_api_surface', return_value=set(self.keys)))
        stack.enter_context(patch.object(self.sources, 'public_api_surface', return_value=set(self.keys)))
        return stack

    def generate(self):
        with self.discovery(), self.fake_models() as calls:
            result = self.generation.find_or_create(self.cfg, generate=True, max_generated=0)
        return result, calls

    def test_two_owners_generate_and_retrieve_separately(self):
        result, calls = self.generate()
        self.assertEqual(self.keys, json.loads(Path(result['generation_state']).read_text())['completed_apis'])
        entries = self.format.parse_readme(self.cfg.llm_readme)
        self.assertEqual(self.keys, [e.name for e in entries])
        requests = [json.loads(c[3]) for c in calls if c[2] == 'aideal/readme_entry']
        for index, request in enumerate(requests):
            facts = json.loads(request['api_facts'])
            self.assertEqual(self.keys[index], facts['api_id'])
            self.assertEqual(self.rows[index]['signature'], facts['signature'])
            self.assertNotIn('SIBLING', request['test_examples'])
        self.assertIn('Reader-only', requests[0]['original_examples'])
        self.assertNotIn('Writer-only', requests[0]['original_examples'])
        selected = self.sources._relevant_doc_inventory(self.cfg, 'aideal', [self.keys[1]])
        self.assertEqual(entries[1].body, selected[0].body)
        self.assertNotEqual(entries[0].body, selected[0].body)

    def test_resume_and_completion_remain_exact_ids(self):
        self.generate()
        with self.discovery(), self.fake_models() as calls:
            result = self.generation.find_or_create(self.cfg, generate=True, resume=True, max_generated=0)
        self.assertEqual(2, result['api_entries'])
        self.assertEqual([], [c for c in calls if c[2] == 'aideal/readme_entry'])
        self.assertEqual(self.keys, json.loads(Path(result['generation_state']).read_text())['completed_apis'])

    def test_missing_or_unresolved_mapping_blocks_before_model(self):
        for replacement in (None, dict(status='unresolved', reason='Dynamic alias unresolved')):
            with self.subTest(replacement=replacement):
                if replacement is None:
                    self.manifest['targets'].pop(self.keys[1], None)
                else:
                    self.manifest['targets'][self.keys[1]] = replacement
                self.write_manifest()
                with self.discovery(), self.fake_models() as calls:
                    with self.assertRaisesRegex(ValueError, 'mapping unresolved'):
                        self.generation.find_or_create(self.cfg, generate=True, force=True)
                self.assertEqual([], calls)

    def test_explicit_undocumented_is_not_bare_name_credit(self):
        self.manifest['targets'][self.keys[1]] = dict(status='undocumented', reason='No verified anchor')
        self.write_manifest()
        texts = self.documents.original_target_texts(self.cfg, self.keys)
        self.assertIn('undocumented', texts[self.keys[1]])
        self.assertNotIn('Reader-only', texts[self.keys[1]])
        with self.assertRaises(ValueError):
            self.documents.original_target_texts(self.cfg, ['run'])

    def test_exact_excerpts_never_silently_truncate(self):
        with self.assertRaisesRegex(ValueError, 'exceeds explicit budget'):
            self.sources._relevant_original_texts(self.cfg, self.keys, 5)
        with self.assertRaisesRegex(ValueError, 'exceeds budget'):
            self.cfg.original_readme_text(limit=5)
        self.generate()
        self.cfg.comprehension['relevant_doc_chars'] = 5
        with self.assertRaisesRegex(ValueError, 'no text was truncated'):
            self.sources._relevant_doc_inventory(self.cfg, 'aideal', self.keys)

    def test_distillation_covers_every_character_and_records_ranges(self):
        corpus = 'begin-' + 'x'*150100 + '-TAIL-SENTINEL'
        (self.doc_dir/'corpus.md').write_text(corpus)
        self.manifest['documents'][0]['sha256'] = sha(corpus)
        self.write_manifest()
        with self.fake_models() as calls:
            note = self.generation.distilled_readme_context(self.cfg)
        requests = [json.loads(c[3])['original_readme'] for c in calls]
        full = self.cfg.original_readme_text()
        self.assertEqual(full, ''.join(requests))
        self.assertEqual(2, len(requests))
        self.assertIn('TAIL-SENTINEL', requests[-1])
        receipt = json.loads((self.cfg.llm_readme.parent/'original_readme_notes.json').read_text())
        self.assertEqual(len(full), receipt['chunks'][-1]['end'])
        self.assertFalse(receipt['truncated'])
        self.assertEqual(sha(note), receipt['note_sha256'])
        with self.fake_models() as calls:
            self.assertEqual(note, self.generation.distilled_readme_context(self.cfg))
        self.assertEqual([], calls)

    def test_manifest_and_every_payload_hash_checked(self):
        for file in ['corpus.md', 'reader.md']:
            path = self.doc_dir/file
            before = path.read_bytes()
            path.write_bytes(before+b'changed')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                self.documents.original_document_paths(self.cfg)
            path.write_bytes(before)
        self.cfg.raw['files']['original_doc_manifest_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'manifest checksum mismatch'):
            self.documents.original_document_paths(self.cfg)

    def test_missing_payload_fails_instead_of_skipping(self):
        (self.doc_dir/'reader.md').unlink()
        with self.assertRaises(FileNotFoundError):
            self.documents.original_documents(self.cfg)

    def test_only_reviewed_text_kinds_are_accepted(self):
        for kind in ['dataset', 'source_stub', None]:
            self.manifest['documents'][0]['kind'] = kind
            self.write_manifest()
            with self.assertRaisesRegex(ValueError, 'Unreviewed'):
                self.documents.original_documents(self.cfg)

    def test_manifest_relative_payloads_survive_config_relocation(self):
        before = self.documents.original_target_texts(self.cfg, self.keys)
        self.cfg.root = self.root/'relocated'
        self.assertEqual(before, self.documents.original_target_texts(self.cfg, self.keys))
        paths = self.documents.original_document_paths(self.cfg)
        self.assertEqual(4, len(paths))
        self.assertIn(self.doc_dir/'reader.md', paths)

    def test_duplicate_ids_rejected_at_both_document_and_task_boundary(self):
        self.cfg.llm_readme.write_text('## API Test: `'+self.keys[0]+'`\n'*1)
        self.cfg.llm_readme.write_text(('## API Test: `'+self.keys[0]+'`\n')*2)
        with self.assertRaisesRegex(ValueError, 'duplicate API identities'):
            self.format.parse_readme(self.cfg.llm_readme)
        path = self.root/'apis.json'
        path.write_text(json.dumps(self.keys+self.keys[:1]))
        with self.discovery(), self.assertRaisesRegex(ValueError, 'duplicate identities'):
            self.sources._load_manifest(self.cfg, str(path))

    def test_legacy_entry_cannot_fill_qualified_owner(self):
        self.cfg.llm_readme.write_text('## API Test: `run`\n### Goal\nRuns.\n')
        with self.assertRaisesRegex(ValueError, 'missing exact API identity'):
            self.sources._relevant_doc_inventory(self.cfg, 'aideal', self.keys)

    def test_storage_keys_are_safe_unique_and_legacy_compatible(self):
        self.assertEqual('run', self.format.api_storage_key('run'))
        values = self.keys + ['python:pkg.Class.a/b', 'python:pkg.Class.a_b', '../escape']
        mapped = [self.format.api_storage_key(key) for key in values]
        self.assertEqual(len(values), len(set(mapped)))
        self.assertTrue(all('/' not in name and ':' not in name and len(name) < 255 for name in mapped))

    def test_unknown_constructor_signature_is_not_zero_arity(self):
        row = dict(self.rows[0], parameter_count=None, parameter_count_status='unknown', params=[])
        body = self.format._entry_skeleton(row['api_id'], 'scala', [row])
        self.assertIn('not a verified zero-argument', body)
        from aideal.doc_check_execution import _requested_target_context
        target = dict(qualified_name=row['qualified_name'], owner=row['owner'], signature='constructor unknown',
                      parameters=[], parameter_count=None)
        text = _requested_target_context('', target)
        self.assertIn('arity unresolved', text)
        self.assertNotIn('(0)', text)

    def test_catalogue_keeps_two_owners_in_one_scala_file(self):
        self.generate()
        from aideal.readme_catalogue import _catalogue_model
        entries = self.format.parse_readme(self.cfg.llm_readme)
        model = _catalogue_model(entries, {}, {}, dict(zip(self.keys, ['demo.Reader', 'demo.Writer'])), {},
                                 file_of={key:'src/Ops.scala' for key in self.keys})
        self.assertEqual({'demo.Reader', 'demo.Writer'}, set(model))

    def test_scala_receiver_uses_exact_owner_and_callable_name(self):
        from aideal.doc_check_inputs import _owner_map, _receiver_hint
        with patch.object(self.readme, 'public_api_details', return_value=self.rows):
            owners = _owner_map(self.cfg)
        self.assertEqual(('demo.Reader', 'static'), owners[self.keys[0]])
        text = _receiver_hint(self.keys[0], owners)
        self.assertIn('demo.Reader.run(...)', text)
        self.assertNotIn('demo.Reader.scala:', text)

    def test_source_window_uses_qualified_owner_only(self):
        from aideal.docfix import _source_window
        with patch.object(self.readme, 'public_api_details', return_value=self.rows):
            body, others = _source_window(self.cfg, self.keys[1])
        self.assertIn('src/Ops.scala:3', body)
        self.assertEqual('(none)', others)

    def test_replay_request_identity_does_not_erase_owner(self):
        from aideal.readme_replay import normalized
        first = dict(api=self.keys[0], phase='entry', system='s', user='same', binding='a')
        second = dict(first, api=self.keys[1], binding='b')
        self.assertNotEqual(normalized(first), normalized(second))

    def test_docs_source_version_must_match_the_frozen_api_inventory(self):
        inventory = {key: self.manifest[key] for key in ('source_commit', 'source_tree', 'source_version')}
        path = self.root/'inventory.json'
        path.write_text(json.dumps(inventory))
        self.cfg.raw['codebase'].update(api_inventory=str(path), api_inventory_sha256=sha(path.read_bytes()))
        self.assertIsNotNone(self.documents.original_documents(self.cfg))
        inventory['source_version'] = 'other-version'
        path.write_text(json.dumps(inventory))
        self.cfg.raw['codebase']['api_inventory_sha256'] = sha(path.read_bytes())
        with self.assertRaisesRegex(ValueError, 'mismatch: source_version'):
            self.documents.original_documents(self.cfg)

    def test_reviewed_config_resolves_documents_not_the_old_glob(self):
        import yaml
        config = self.root/'config.yaml'
        config.write_text(yaml.safe_dump(dict(project=dict(name='Offline', language='Scala'),
            files={**self.cfg.raw['files'], 'original_readme': 'README.md'})))
        loaded = self.config_module.load_config(config)
        self.assertEqual([self.doc_dir/'corpus.md'], loaded.original_readme_files)
        self.assertNotIn('Ops.scale', loaded.original_readme_text())

    def test_qualified_prompt_binding_supports_new_inventory_kind(self):
        from aideal.doc_check_execution import _canonical_prompt_targets
        inventory = dict(kind='qualified_source_api_inventory', source_inventory_sha256='c'*64,
                         canonical_selection='selection.json', canonical_selection_sha256='d'*64,
                         canonical_selection_policy_version='owner_qualified_max_arity_v2',
                         **{key: self.manifest[key] for key in ('source_commit', 'source_tree', 'source_version')})
        path = self.root/'inventory.json'
        path.write_text(json.dumps(inventory))
        self.cfg.raw['codebase'].update(api_inventory=str(path), api_inventory_sha256=sha(path.read_bytes()))
        rows = [dict(row, site_id=str(i)) for i, row in enumerate(self.rows)]
        with patch('aideal.api_registry.configured_api_details', return_value=rows):
            targets = _canonical_prompt_targets(self.cfg)
        self.assertEqual(set(self.keys), set(targets))
        self.assertEqual('run', targets[self.keys[0]]['display_name'])
        self.assertEqual('owner_qualified_max_arity_v2', targets[self.keys[0]]['selection_policy_version'])
        self.assertEqual('c'*64, targets[self.keys[1]]['source_inventory_sha256'])

    def test_qualified_execution_without_inventory_fails_closed(self):
        from aideal.doc_check_execution import _canonical_prompt_targets
        with self.assertRaisesRegex(ValueError, 'requires a frozen'):
            _canonical_prompt_targets(self.cfg)

    def test_native_requests_and_adapter_metadata_keep_both_owners(self):
        from contextlib import ExitStack
        import subprocess
        import test_canonical_prompt_targets as native_fixture
        from aideal import doc_check_execution as execution
        from aideal.experiment_identity import digest_native
        case = native_fixture.CanonicalPromptTargetTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        targets = {}
        for row in self.rows:
            target = dict(api_id=row['api_id'], display_name='run', qualified_name=row['qualified_name'],
                          owner=row['owner'], signature=row['signature'], parameters=row['params'], parameter_count=1)
            target['target_fingerprint'] = digest_native(target)
            targets[row['api_id']] = target
        with ExitStack() as stack:
            provider = stack.enter_context(patch('aideal.llm.invoke_text', return_value='print("DONE")'))
            stack.enter_context(patch('aideal.execution.run_command', return_value=subprocess.CompletedProcess('synthetic', 0, 'DONE', '')))
            stack.enter_context(patch('subprocess.run', side_effect=AssertionError('Unexpected external process')))
            stack.enter_context(patch.object(execution, '_canonical_prompt_targets', return_value=targets))
            stack.enter_context(patch.object(execution, 'public_api_details', return_value=[]))
            stack.enter_context(patch.object(execution, 'public_api_surface', return_value=set(self.keys)))
            stack.enter_context(patch.object(self.readme, 'public_api_details', return_value=[]))
            entries = [self.format.ApiEntry(key, '', '', 'Reviewed document') for key in self.keys]
            result = execution._comprehension_execute(case.cfg, entries, 0, 42, 'aideal', max_fix_rounds=0)
        self.assertEqual(2, provider.call_count)
        for key in self.keys:
            evidence = Path(result['metrics'][key]['attempt_evidence'][0])
            request = json.loads((evidence/'request.json').read_text())
            adapter = json.loads((evidence.parent/'requested_target.json').read_text())
            self.assertEqual(key, request['api'])
            self.assertEqual(key, adapter['api_id'])
            self.assertEqual('run', adapter['display_name'])
            self.assertEqual('run_'+self.format.api_storage_key(key), evidence.parent.name)

    def test_deepdive_preserves_exact_identity_and_safe_storage(self):
        from aideal import deepdive
        from types import ModuleType
        import sys
        self.cfg.roles['fixer'] = 'offline'
        fake = ModuleType('aideal.llm')
        fake.invoke_text = lambda *args: 'Offline diagnosis.'
        fake.usage_snapshot = lambda: {}
        fake.usage_delta = lambda before: dict(input_tokens=0, output_tokens=0)
        with self.fake_models(), patch.dict(sys.modules, {'aideal.llm': fake}), \
                patch.object(self.readme, 'public_api_details', return_value=self.rows):
            result = deepdive.deep_dive_run(self.cfg, self.keys[0])
        self.assertEqual(self.keys[0], result['api'])
        self.assertEqual(self.format.api_storage_key(self.keys[0])+'.md', Path(result['report']).name)
        self.assertIn(self.keys[0], Path(result['report']).read_text())
        self.assertIn('not attributed', deepdive._call_sites(self.cfg, self.keys[0]))

    def test_private_definition_with_verified_public_exposure_is_retained(self):
        self.rows[0].update(visibility='nonpublic', public_exposure_established=True,
                            preferred_public_path='demo.Reader.run', public_access_paths=['demo.Reader.run'],
                            exposure_ids=['scala:demo.Reader.run'])
        result, calls = self.generate()
        self.assertEqual(2, result['generated_ok'])
        request = next(json.loads(c[3]) for c in calls if c[2]=='aideal/readme_entry')
        self.assertEqual('demo.Reader.run', json.loads(request['api_facts'])['preferred_public_path'])
        from aideal.doc_check_execution import _requested_target_context
        text = _requested_target_context('', dict(qualified_name='demo._Hidden.run', owner='demo._Hidden',
            signature='run()', parameters=[], parameter_count=0, preferred_public_path='demo.Reader.run'))
        self.assertIn('Verified public access paths', text)
        self.assertIn('demo.Reader.run', text)

    def test_existing_legacy_catalog_is_not_reported_as_completed_qualified_generation(self):
        self.cfg.llm_readme.write_text('## API Test: `run`\n### Goal\nRun.\n')
        with self.discovery(), self.fake_models() as calls:
            with self.assertRaisesRegex(ValueError, 'qualified README requires force or resume'):
                self.generation.find_or_create(self.cfg, generate=True)
        self.assertEqual([], calls)

    def test_existing_complete_qualified_catalog_still_requires_fingerprint_resume(self):
        self.generate()
        with self.discovery(), self.fake_models() as calls:
            with self.assertRaisesRegex(ValueError, 'current source/document fingerprint'):
                self.generation.find_or_create(self.cfg, generate=True)
        self.assertEqual([], calls)
        # Inspection alone remains available, including historical readmes.
        self.assertEqual('found', self.generation.find_or_create(self.cfg, generate=False)['action'])

    def test_shared_original_document_precedes_exact_excerpts_without_coverage_credit(self):
        self.manifest['shared_document_ids'] = ['api-page']
        self.manifest['targets'][self.keys[1]] = dict(status='undocumented', reason='No exact anchor')
        self.write_manifest()
        texts = self.documents.original_target_texts(self.cfg, self.keys)
        original = (self.doc_dir/'corpus.md').read_text()
        for text in texts.values():
            self.assertIn(original, text)
            self.assertTrue(text.startswith('===== Shared original document: api-page ====='))
        self.assertIn('Reader-only sentinel', texts[self.keys[0]])
        self.assertIn('Disposition: undocumented', texts[self.keys[1]])
        self.assertEqual('undocumented', self.documents.original_documents(self.cfg)['manifest']['targets'][self.keys[1]]['status'])

    def test_shared_document_ids_reject_unknown_duplicate_and_wrong_type(self):
        for value in [['missing'], ['api-page','api-page'], 'api-page', [None]]:
            with self.subTest(value=value):
                self.manifest['shared_document_ids'] = value
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, 'shared_document_ids'):
                    self.documents.original_documents(self.cfg)

    def test_shared_exact_whole_document_is_not_repeated_as_excerpt(self):
        self.manifest['shared_document_ids'] = ['api-page']
        self.manifest['targets'][self.keys[0]]['excerpts'][0].update(
            path='corpus.md', sha256=sha((self.doc_dir/'corpus.md').read_bytes()))
        self.write_manifest()
        text = self.documents.original_target_texts(self.cfg,[self.keys[0]])[self.keys[0]]
        self.assertEqual(1,text.count('Reader precise docs.'))
        self.assertEqual('documented', self.documents.original_documents(self.cfg)['manifest']['targets'][self.keys[0]]['status'])

    def test_shared_context_budget_counts_all_verbatim_content(self):
        before = self.documents.original_target_texts(self.cfg,[self.keys[0]])[self.keys[0]]
        self.manifest['shared_document_ids'] = ['api-page']
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'exceeds explicit budget'):
            self.documents.original_target_texts(self.cfg,[self.keys[0]],len(before))

    def test_missing_shared_document_payload_fails_before_model_call(self):
        self.manifest['shared_document_ids'] = ['api-page']
        self.write_manifest()
        (self.doc_dir/'corpus.md').unlink()
        with self.discovery(),self.fake_models() as calls:
            with self.assertRaises(FileNotFoundError):
                self.generation.find_or_create(self.cfg,generate=True)
        self.assertEqual([],calls)

    def test_reviewed_rst_readme_keeps_exact_text_and_its_actual_format(self):
        self.manifest['documents'][0]['kind'] = 'original_rst'
        self.manifest['shared_document_ids'] = ['api-page']
        self.write_manifest()
        self.assertIn((self.doc_dir/'corpus.md').read_text(),
                      self.documents.original_target_texts(self.cfg,[self.keys[0]])[self.keys[0]])


if __name__ == '__main__':
    unittest.main()
