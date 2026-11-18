"""Prepare real canonical inventories under a different root without model calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml
from aideal.api_registry import configured_api_details, relocated_inventory_binding
from aideal.doc_check_execution import _canonical_prompt_targets
import test_source_audit_registry as source_fixture
import test_sql_canonical_aliases as sql_fixture

STAGE = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


original = module('relocation_original_launcher', STAGE / 'scripts/run_original_micro.py')
readme = module('relocation_readme_launcher', STAGE / 'scripts/run_readme_generation.py')


class CanonicalLaunchRelocationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = source_fixture.SourceAuditRegistryTests('test_python_functions_methods_and_explicit_class_constructor_use_exact_public_facts')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        f.definition['source_inventory'] = 'ledger.json'
        f.definition['canonical_selection'] = 'selection.json'
        (f.root / 'contract.json').write_text('{"parser": "fixture"}\n')
        f.definition['parser_contract'] = 'contract.json'
        f.definition['parser_contract_sha256'] = hashlib.sha256((f.root / 'contract.json').read_bytes()).hexdigest()
        f.freeze_manifest()
        (f.root / 'configs').mkdir()
        (f.root / 'README.md').write_text('Original contracts: add(x, y=1), Box(value), get().\n')
        (f.root / 'scaffold.py').write_text('# AIDEAL_DATA_BINDINGS\n# START\n# END\nprint("DONE")\n')
        (f.root / 'configs/project_profile.yaml').write_text(yaml.safe_dump({
            'project': {'name': 'fixture', 'language': 'Python', 'description': 'Arithmetic fixtures'},
            'domain': 'arithmetic', 'target_users': ['developers'], 'use_cases': ['Add values']}))
        raw = {'project': {'name': 'fixture', 'language': 'Python'},
            'codebase': {'source_globs': ['source/api.py'], 'test_globs': [], 'surface_filter': 'all',
                'api_inventory': 'api_inventory.json', 'api_inventory_sha256': hashlib.sha256(f.manifest.read_bytes()).hexdigest()},
            'files': {'original_readme': ['README.md'], 'project_profile': 'configs/project_profile.yaml'},
            'comprehension': {'execute': {'scaffold': 'scaffold.py', 'command': 'python {test_file}',
                'region': ['# START', '# END'], 'preamble': '', 'io_hints': '', 'max_fix_rounds': 0}}}
        config = f.root / 'configs/aideal.yaml'; config.write_text(yaml.safe_dump(raw))
        manifest = f.root / 'names.json'; manifest.write_text('["Box", "add", "get"]\n')
        self.spec = {'base_config': str(config), 'manifest': str(manifest),
                     'source_link': {'name': 'source', 'target': str(f.source_root)}}
        self.before = {p: p.read_bytes() for p in f.root.iterdir() if p.is_file()}

    def assert_relocated(self, cfg):
        f = self.fixture
        relocated = cfg.root / cfg.raw['codebase']['api_inventory']
        self.assertEqual(cfg.root / 'inputs/api_inventory.json', relocated)
        data = json.loads(relocated.read_text())
        for field, filename in [('source_inventory', 'ledger.json'), ('canonical_selection', 'selection.json'), ('parser_contract', 'contract.json')]:
            self.assertEqual(str((f.root / filename).resolve()), data[field])
            self.assertEqual(f.definition[field + '_sha256'], data[field + '_sha256'])
        self.assertEqual('source', data['source_root'])
        self.assertEqual(hashlib.sha256(relocated.read_bytes()).hexdigest(), cfg.raw['codebase']['api_inventory_sha256'])
        rows = configured_api_details(cfg)
        self.assertEqual({'Box', 'add', 'get'}, {r['name'] for r in rows})
        self.assertEqual('Box', _canonical_prompt_targets(cfg)['Box']['selected_site_id'])
        self.assertEqual([(f.root / 'README.md').resolve()], cfg.original_readme_files)
        for p, value in self.before.items():
            self.assertEqual(value, p.read_bytes())

    def test_original_r0_prepares_and_replays_relative_canonical_bindings(self):
        destination = self.fixture.root / 'r0-new'
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('No model calls')):
            cfg, names = original.prepare(self.spec, destination, 'offline', None)
            self.assertEqual({'Box', 'add', 'get'}, set(names))
            self.assert_relocated(cfg)
            again, _ = original.prepare(self.spec, destination, 'offline', None)
            self.assertEqual(cfg.raw, again.raw)

    def test_readme_prepares_exact_selected_definitions_with_relative_bindings(self):
        destination = self.fixture.root / 'readme-new'
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('No model calls')):
            cfg, manifest, _ = readme.prepare(self.spec, destination, 'offline')
            self.assert_relocated(cfg)
            self.assertEqual(3, manifest['selected_count'])
            self.assertEqual('canonical_selected_target', manifest['identity_kind'])
            self.assertIn('frozen by the canonical-selection receipt', manifest['note'])
            self.assertNotIn('remain grouped', manifest['note'])
            self.assertTrue(all(len(rows) == 1 for rows in manifest['definitions'].values()))
            again, _, _ = readme.prepare(self.spec, destination, 'offline')
            self.assertEqual(cfg.raw, again.raw)

    def test_legacy_readme_manifest_wording_is_unchanged(self):
        config = Path(self.spec['base_config'])
        raw = yaml.safe_load(config.read_text())
        del raw['codebase']['api_inventory']
        del raw['codebase']['api_inventory_sha256']
        legacy = config.with_name('legacy.yaml'); legacy.write_text(yaml.safe_dump(raw))
        spec = dict(self.spec, base_config=str(legacy))
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('No model calls')):
            _, manifest, _ = readme.prepare(spec, self.fixture.root / 'legacy-readme', 'offline')
        self.assertEqual('bare_name_family', manifest['identity_kind'])
        self.assertEqual('One entry per bare API name; same-name declarations remain grouped. Source definitions are explicit; no overload-complete claim.', manifest['note'])

    def test_relative_evidence_must_keep_its_checksum(self):
        cfg = original.load_config(self.spec['base_config'])
        (self.fixture.root / 'selection.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'checksum changed'):
            relocated_inventory_binding(cfg)

    def test_sql_alias_binding_relocates_for_both_launchers_without_rewriting_sources(self):
        fixture = sql_fixture.SqlCanonicalAliasTests('test_complete_registry_validated_then_only_proven_alias_removed')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        root = fixture.root
        (root / 'configs').mkdir()
        for relative in ('configs/project_profile.yaml', 'README.md', 'scaffold.py'):
            (root / relative).write_bytes((self.fixture.root / relative).read_bytes())
        raw = yaml.safe_load(Path(self.spec['base_config']).read_text())
        raw['codebase'].update(source_globs=['source/*.rs'], api_inventory='inventory.json',
                              api_inventory_sha256=hashlib.sha256((root / 'inventory.json').read_bytes()).hexdigest())
        config = root / 'configs/aideal.yaml'; config.write_text(yaml.safe_dump(raw))
        names = root / 'names.json'; names.write_text('["base", "many"]\n')
        spec = {'base_config': str(config), 'manifest': str(names),
                'source_link': {'name': 'source', 'target': str(fixture.source)}}
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('No model calls')):
            configs = [original.prepare(spec, root / 'r0', 'offline', None)[0],
                       readme.prepare(spec, root / 'readme', 'offline')[0]]
        for cfg in configs:
            data = json.loads((cfg.root / cfg.raw['codebase']['api_inventory']).read_text())
            self.assertEqual('source/registry.rs', data['definitions'][0]['file'])
            self.assertEqual(['base', 'many'], [r['name'] for r in configured_api_details(cfg)])
            self.assertEqual('SQL:many', _canonical_prompt_targets(cfg)['many']['selected_site_id'])
            self.assertEqual(fixture.receipt, json.loads((root / 'selection.json').read_text()))

    def test_no_binding_legacy_and_absolute_bindings_return_no_rewrite(self):
        cfg = original.load_config(self.spec['base_config'])
        for data in ({'schema': 1, 'kind': 'registered_sql'}, {'canonical_selection': '/abs/selection.json'}):
            self.fixture.manifest.write_text(json.dumps(data, separators=(',', ':')))
            self.assertIsNone(relocated_inventory_binding(cfg))
        empty = SimpleNamespace(root=self.fixture.root, raw={})
        self.assertIsNone(relocated_inventory_binding(empty))


if __name__ == '__main__':
    unittest.main()
