"""Offline compiler-inventory contracts; no model or repository dependency."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.api_registry import configured_api_details, _parameters, _source_header
from aideal.api_discovery import public_api_details, public_api_surface, api_coverage
from aideal.doc_check_sources import _load_manifest
from aideal.readme_format import parse_readme


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CompilerInventoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name); (self.root / 'source').mkdir()
        self.source = self.root / 'source/Tools.java'
        methods = ['public static int add(int x) { return x; }',
                   'public static int add(int x, int y) { return x+y; }',
                   'private int hidden() { return 0; }']
        text = 'package sample;\npublic class Tools {\n' + '\n'.join(methods) + '\n}\n'
        self.source.write_text(text)
        records = []
        for index, method in enumerate(methods):
            start = text.index(method)
            records.append({'site_id': str(index), 'language': 'Java', 'kind': 'method',
                'scope': 'production', 'declared_visibility': 'public' if index < 2 else 'private',
                'public_owner_chain': index < 2, 'synthetic': False, 'path': 'Tools.java',
                'source_sha256': sha(self.source), 'name': 'add' if index < 2 else 'hidden',
                'owner': 'sample.Tools', 'qualified_name': 'sample.Tools.' + ('add' if index < 2 else 'hidden'),
                'line': text[:start].count('\n') + 1, 'start': start, 'end': start + len(method),
                'signature': ['(int x):int', '(int x,int y):int', '():int'][index]})
        self.inventory = self.root / 'compiler.json'
        self.provenance = {'schema_version': 1, 'records': records}
        self.inventory.write_text(json.dumps(self.provenance))
        self.contract = self.root / 'parser_contract.json'; self.contract.write_text('{"status":"passed"}')
        self.definition = {'schema': 1, 'kind': 'compiler_declared_methods', 'language': 'Java',
            'source_root': 'source', 'source_inventory': str(self.inventory), 'source_inventory_sha256': sha(self.inventory),
            'parser_contract': str(self.contract), 'parser_contract_sha256': sha(self.contract), 'declaration_ids': ['0', '1']}
        self.path = self.root / 'api_inventory.json'
        self.cfg = SimpleNamespace(root=self.root, language='Java', surface_filter='all', exclude_names=[], raw={'codebase': {}})
        self.freeze()

    def freeze(self):
        self.path.write_text(json.dumps(self.definition))
        self.cfg.raw['codebase'].update(api_inventory=str(self.path), api_inventory_sha256=sha(self.path))

    def revise_provenance(self):
        self.inventory.write_text(json.dumps(self.provenance))
        self.definition['source_inventory_sha256'] = sha(self.inventory)
        self.freeze()

    def test_public_owner_overloads_are_retained_and_private_sites_absent(self):
        details = public_api_details(self.cfg)
        self.assertEqual({'add'}, public_api_surface(self.cfg))
        self.assertEqual([1, 2], [len(row['params']) for row in details])
        self.assertEqual(['sample.Tools.add'] * 2, [row['qualified_name'] for row in details])
        self.assertTrue(all(row['visibility'] == 'public' for row in details))
        self.assertNotIn('hidden', json.dumps(details))

    def test_source_inventory_and_contract_changes_are_rejected(self):
        for path in [self.source, self.inventory, self.contract, self.path]:
            saved = path.read_bytes(); path.write_bytes(saved + b'\n')
            with self.subTest(path=path), self.assertRaises(ValueError):
                configured_api_details(self.cfg)
            path.write_bytes(saved)

    def test_private_missing_and_duplicate_ids_cannot_change_frozen_scope(self):
        for ids in [['0', '1', '2'], ['0'], ['0', '1', '1']]:
            self.definition['declaration_ids'] = ids; self.freeze()
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                configured_api_details(self.cfg)

    def test_bad_line_name_and_empty_signature_fail_before_returning_facts(self):
        original = deepcopy(self.provenance)
        for field, value in [('line', 999), ('name', 'fabricated'), ('signature', '')]:
            self.provenance = deepcopy(original)
            self.provenance['records'][0][field] = value; self.revise_provenance()
            with self.subTest(field=field), self.assertRaises(ValueError):
                configured_api_details(self.cfg)

    def test_unknown_kind_filter_and_exclusions_are_rejected(self):
        self.definition['kind'] = 'unknown'; self.freeze()
        with self.assertRaises(ValueError): configured_api_details(self.cfg)
        self.definition['kind'] = 'compiler_declared_methods'; self.freeze()
        self.cfg.surface_filter = 'documented'
        with self.assertRaises(ValueError): configured_api_details(self.cfg)
        self.cfg.surface_filter = 'all'; self.cfg.exclude_names = ['add']
        with self.assertRaises(ValueError): configured_api_details(self.cfg)
        self.cfg.exclude_names = []
        with self.assertRaises(ValueError): public_api_surface(self.cfg, 'documented')

    def test_scala_operators_and_underscores_reach_native_manifest_and_readme(self):
        self.cfg.language = self.definition['language'] = 'Scala'
        self.source.unlink(); self.source = self.root / 'source/Ops.scala'
        text = 'class Ops {\n def +=(x: Int): Int = x\n def _value: Int = 1\n}\n'
        self.source.write_text(text); records = []
        for index, (name, declaration, signature) in enumerate([
                ('+=', 'def +=(x: Int): Int = x', '[](x:Int):Int'),
                ('_value', 'def _value: Int = 1', '[]:Int')]):
            start = text.index(declaration)
            records.append({**self.provenance['records'][0], 'site_id': str(index), 'language': 'Scala',
                'path': 'Ops.scala', 'source_sha256': sha(self.source), 'name': name,
                'owner': 'Ops', 'owner_kind': 'class', 'qualified_name': 'Ops.' + name,
                'line': text[:start].count('\n') + 1, 'start': start, 'end': start + len(declaration), 'signature': signature})
        self.provenance['records'] = records; self.revise_provenance()
        self.assertEqual({'+=', '_value'}, public_api_surface(self.cfg))
        manifest = self.root / 'manifest.json'; manifest.write_text(json.dumps(['+=', '_value']))
        self.assertEqual(['+=', '_value'], _load_manifest(self.cfg, str(manifest)))
        readme = self.root / 'README.md'; readme.write_text('## API Test: `+=`\n### Goal\nAdd.\n## API Test: `_value`\n### Goal\nValue.')
        self.assertEqual(['+=', '_value'], [e.name for e in parse_readme(readme)])

    def test_function_types_curried_parameters_and_unknown_returns_are_honest(self):
        params, returns = _parameters('[](f:(Int,Int)=>Int,x:Int)(y:List[Int]):<type ?>', 'Scala')
        self.assertEqual(['f', 'x', 'y'], [p['name'] for p in params])
        self.assertEqual('(Int,Int)=>Int', params[0]['type'])
        self.assertEqual('', returns)
        params, returns = _parameters('T extends TreeNode(Class<T> value):T', 'Java')
        self.assertEqual('Class<T>', params[0]['type']); self.assertEqual('T', returns)

    def test_annotation_with_same_name_does_not_select_wrong_source_position(self):
        source = '@example.add(1)\npublic int add(int x) { return x; }'
        header, offset = _source_header(source, 'add', 'Java')
        self.assertEqual(source.index('add(int'), offset)
        self.assertIn('public int add(int x)', header)

    def test_coverage_reports_external_original_document_without_relocating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / 'README.md'
            document.write_text('Call `add(1)`.')
            self.cfg.original_readme_files = [document]
            self.cfg.original_readme_text = lambda **kwargs: document.read_text()
            self.cfg.llm_readme = self.root / 'not-generated.md'
            result = api_coverage(self.cfg)
            self.assertEqual([str(document)], result['original_doc_files'])
            self.assertEqual(['add'], result['surface_S'])
            self.assertEqual(['add'], result['original_documented_O'])


if __name__ == '__main__': unittest.main()
