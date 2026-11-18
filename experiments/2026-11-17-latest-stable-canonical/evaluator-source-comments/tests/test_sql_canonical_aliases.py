from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from aideal.api_registry import configured_api_details
from aideal.api_sql_canonical import POLICY_VERSION
from aideal.doc_check_execution import _canonical_prompt_targets, _requested_target_context


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


class SqlCanonicalAliasTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name); self.source = self.root / 'source'; self.source.mkdir()
        text = 'pub fn registration() { let udf = make("base"); udf.with_aliases(vec!["alias".to_string()]) }\n'
        path = self.source / 'registry.rs'; path.write_text(text)
        def git(*args): return subprocess.check_output(['git', '-C', str(self.source), *args], text=True).strip()
        git('init', '-q'); git('add', 'registry.rs'); git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        names = ['alias', 'base', 'many']
        self.data = {'schema': 1, 'kind': 'registered_sql', 'source_revision': git('rev-parse', 'HEAD'),
            'registered_names': names, 'definitions': [{'name': name, 'signature': name + '(value)',
                'params': [{'name': 'value', 'type': 'geometry'}], 'returns': 'geometry', 'description': 'Source body stays out of task metadata',
                'file': 'source/registry.rs', 'line': 1, 'file_sha256': sha(path)} for name in names],
            'canonical_selection': 'selection.json', 'canonical_selection_policy_version': POLICY_VERSION,
            'canonical_registered_names': ['base', 'many']}
        self.receipt = {'schema': 1, 'kind': 'registered_sql_canonical_selection', 'policy_version': POLICY_VERSION,
            'source_root': 'source', 'source_revision': self.data['source_revision'], 'source_tree': git('rev-parse', 'HEAD^{tree}'),
            'registered_names': names, 'registered_names_sha256': hashlib.sha256(json.dumps(names, separators=(',', ':')).encode()).hexdigest(),
            'source_evidence': [{'path': 'registry.rs', 'sha256': sha(path)}], 'unbounded_names': ['many'],
            'selected_names': ['base', 'many'], 'aliases': [{'alias': 'alias', 'canonical': 'base',
                'relationship': 'explicit_udf_with_aliases', 'path': 'registry.rs', 'file_sha256': sha(path),
                'start': 0, 'end': len(text.rstrip()), 'source_span_sha256': hashlib.sha256(text.rstrip().encode()).hexdigest()}]}
        self.cfg = SimpleNamespace(root=self.root, language='Python', surface_filter='all', exclude_names=[], raw={'codebase': {}})
        self.freeze()

    def freeze(self):
        receipt = self.root / 'selection.json'; receipt.write_text(json.dumps(self.receipt))
        if 'canonical_selection' in self.data: self.data['canonical_selection_sha256'] = sha(receipt)
        manifest = self.root / 'inventory.json'; manifest.write_text(json.dumps(self.data))
        self.cfg.raw['codebase'].update(api_inventory=str(manifest), api_inventory_sha256=sha(manifest))

    def test_complete_registry_validated_then_only_proven_alias_removed(self):
        details = configured_api_details(self.cfg)
        self.assertEqual(['base', 'many'], [row['name'] for row in details])
        self.assertEqual(['SQL:base', 'SQL:many'], [row['site_id'] for row in details])
        self.assertEqual(3, len(self.data['definitions']))
        self.data['definitions'][0]['file_sha256'] = '0' * 64; self.freeze()
        with self.assertRaisesRegex(ValueError, 'source evidence changed'): configured_api_details(self.cfg)

    def test_legacy_registered_surface_keeps_all_names_and_original_shape(self):
        for field in list(self.data):
            if field.startswith('canonical_'): del self.data[field]
        self.freeze()
        details = configured_api_details(self.cfg)
        self.assertEqual(['alias', 'base', 'many'], [row['name'] for row in details])
        self.assertNotIn('site_id', details[0])
        self.assertIsNone(_canonical_prompt_targets(self.cfg))

    def test_requested_sql_metadata_does_not_fabricate_finite_arity_or_expose_body(self):
        targets = _canonical_prompt_targets(self.cfg)
        self.assertEqual({'base', 'many'}, set(targets))
        self.assertIsNone(targets['many']['parameter_count'])
        self.assertEqual('unbounded_variadic', targets['many']['parameter_count_status'])
        self.assertEqual([], targets['many']['parameters'])
        context = _requested_target_context('Shared context', targets['many'])
        self.assertIn('Documented call patterns: many(value)', context)
        self.assertIn('no finite maximum arity is asserted', context)
        self.assertNotIn('Source body', json.dumps(targets))

    def test_unproven_or_retargeted_alias_and_bad_selection_fail_closed(self):
        original = deepcopy(self.receipt)
        for change in ['target', 'proof', 'selected']:
            self.receipt = deepcopy(original)
            if change == 'target': self.receipt['aliases'][0]['canonical'] = 'many'
            if change == 'proof': self.receipt['aliases'][0]['source_span_sha256'] = '0' * 64
            if change == 'selected': self.receipt['selected_names'] = ['base']
            self.freeze()
            with self.subTest(change=change), self.assertRaises(ValueError): configured_api_details(self.cfg)

    def test_registry_and_source_revision_mismatch_are_rejected(self):
        original = deepcopy(self.receipt)
        for field, value in [('source_revision', '0' * 40), ('source_tree', '0' * 40), ('registered_names_sha256', '0' * 64)]:
            self.receipt = deepcopy(original); self.receipt[field] = value; self.freeze()
            with self.subTest(field=field), self.assertRaises(ValueError): configured_api_details(self.cfg)


if __name__ == '__main__': unittest.main()
