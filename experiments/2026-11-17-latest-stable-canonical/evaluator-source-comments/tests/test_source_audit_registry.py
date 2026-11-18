"""Frozen callable-surface contracts using synthetic, temporary Git sources."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.api_canonical_selection import POLICY_VERSION, select_canonical_implementations
from aideal.api_registry import configured_api_details
from aideal.api_discovery import api_coverage


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def param(name, default=None):
    return {'name': name, 'kind': 'positional_or_keyword', 'annotation': '',
            'default': default, 'required': default is None}


class SourceAuditRegistryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-source-registry-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source_root = self.root / 'source'; self.source_root.mkdir()
        self.text = ('def add(x, y=1):\n    """Add values."""\n    return x + y\n\n'
                     'class Box:\n    def __init__(self, value):\n        self.value = value\n'
                     '    def get(self):\n        return self.value + 1\n\n'
                     'class Inherited(Base):\n    pass\n')
        self.source_path = self.source_root / 'api.py'; self.source_path.write_text(self.text)
        self.git('init', '-q')
        self.git('add', 'api.py')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        add = self.row('add', 'function', 'def add', self.text.index('\n\n'), 'def add(x, y=1)', [param('x'), param('y', '1')])
        box_end = self.text.index('\n\n', self.text.index('class Box'))
        box = self.row('Box', 'class_constructor', 'class Box', box_end, 'class Box', [param('value')])
        ctor = {'name': '__init__', 'line': 6, 'end_line': 7, 'signature': 'def __init__(self, value)',
                'params': [param('value')], 'declared_params': [param('self'), param('value')],
                'implicit_receiver': param('self'), 'parameter_count': 1}
        box.update(declared_constructors=[ctor], parameter_count_status='declared_constructor_only',
                   declared_params=ctor['declared_params'], implicit_receiver=param('self'), returns='api.Box')
        get = self.row('get', 'method', 'def get', box_end, 'def get(self)', [], owner='Box')
        get.update(declared_params=[param('self')], implicit_receiver=param('self'))
        inherited = self.row('Inherited', 'class_constructor', 'class Inherited', len(self.text.rstrip('\n')),
                             'class Inherited(Base)', [], category='unresolved')
        inherited.update(declared_constructors=[], parameter_count_status='unknown_inherited_or_generated', returns='api.Inherited')
        self.rows = [add, box, get, inherited]
        self.make_manifest('Python', 'api.py')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source_root), *args], text=True).strip()

    def row(self, name, kind, needle, end, signature, params, owner='', category='implementation'):
        start = self.text.index(needle)
        return {'site_id': name, 'language': 'Python', 'name': name, 'owner': owner,
                'qualified_name': '.'.join(value for value in ('api', owner, name) if value), 'module': 'api',
                'path': 'api.py', 'line': self.text[:start].count('\n') + 1,
                'end_line': self.text[:end].count('\n') + 1, 'start': start, 'end': end,
                'offset_unit': 'Unicode code points in decoded source', 'kind': kind, 'scope': 'production',
                'declared_visibility': 'public', 'public_owner_chain': True, 'synthetic': False,
                'source_sha256': sha(self.source_path), 'source_span_sha256': hashlib.sha256(self.text[start:end].encode()).hexdigest(),
                'signature': signature, 'returns': '', 'params': params, 'declared_params': params,
                'implicit_receiver': None, 'parameter_count': len(params),
                'body_classification': {'category': category, 'reviewed': True, 'evidence': {'auditor': 'fixture'}}}

    def make_manifest(self, language, pattern):
        binding = {'path': self.source_path.name, 'sha256': sha(self.source_path), 'bytes': self.source_path.stat().st_size}
        if language == 'Python': binding['encoding'] = 'utf-8'
        self.ledger = {'schema': 1, 'language': language, 'records': self.rows, 'source_files': [binding],
            'source_snapshot': {'commit': self.git('rev-parse', 'HEAD'), 'tree': self.git('rev-parse', 'HEAD^{tree}'), 'tracked_worktree_clean': True},
            'discovery_policy': {'source_globs': [pattern], 'exclude_names': [], 'surface_filter': 'all'},
            'receipt': {'passed': True, 'source_file_binding_sha256': digest([binding])}}
        self.inventory = self.root / 'ledger.json'; self.selection = self.root / 'selection.json'
        self.manifest = self.root / 'api_inventory.json'
        self.definition = {'schema': 1, 'kind': 'source_audited_callables', 'language': language,
            'source_root': 'source', 'source_inventory': str(self.inventory),
            'source_commit': self.ledger['source_snapshot']['commit'], 'source_tree': self.ledger['source_snapshot']['tree'],
            'source_file_binding_sha256': digest([binding]), 'declaration_ids': [row['site_id'] for row in self.rows],
            'canonical_selection': str(self.selection), 'canonical_selection_policy_version': POLICY_VERSION}
        self.cfg = SimpleNamespace(root=self.root, language=language, surface_filter='all', exclude_names=[],
                                   source_globs=['source/' + pattern], raw={'codebase': {}})
        self.freeze()

    def freeze(self):
        self.inventory.write_text(json.dumps(self.ledger))
        self.definition['source_inventory_sha256'] = sha(self.inventory)
        receipt = select_canonical_implementations(self.ledger['records'])
        self.bound = {'schema': 1, 'kind': 'source_audit_global_canonical_selection', 'policy_version': POLICY_VERSION,
                      'source_inventory_sha256': sha(self.inventory), 'selection': receipt}
        self.selection.write_text(json.dumps(self.bound))
        self.definition['canonical_selection_sha256'] = sha(self.selection)
        self.definition['canonical_declaration_ids'] = receipt['winner_site_ids']
        self.freeze_manifest()

    def freeze_manifest(self):
        self.manifest.write_text(json.dumps(self.definition))
        self.cfg.raw['codebase'].update(api_inventory=str(self.manifest), api_inventory_sha256=sha(self.manifest))

    def test_python_functions_methods_and_explicit_class_constructor_use_exact_public_facts(self):
        by_name = {row['name']: row for row in configured_api_details(self.cfg)}
        self.assertEqual({'add', 'Box', 'get'}, set(by_name))
        self.assertEqual('api.Box', by_name['Box']['qualified_name'])
        self.assertEqual('class Box; def __init__(self, value)', by_name['Box']['signature'])
        self.assertEqual(['value'], [p['name'] for p in by_name['Box']['params']])
        self.assertEqual('1', by_name['add']['params'][1]['default'])
        self.assertEqual([], by_name['get']['params'])
        self.assertEqual('Add values.', by_name['add']['description'])
        self.assertTrue(all('body_classification' not in row for row in by_name.values()))

    def test_unknown_inherited_constructor_is_retained_in_inventory_but_never_selected(self):
        self.assertIn('Inherited', self.definition['declaration_ids'])
        self.assertNotIn('Inherited', self.definition['canonical_declaration_ids'])

    def test_selected_constructor_metadata_reaches_existing_canonical_prompt_binding(self):
        from aideal.doc_check_execution import _canonical_prompt_targets
        targets = _canonical_prompt_targets(self.cfg)
        self.assertEqual('Box', targets['Box']['selected_site_id'])
        self.assertEqual('api.Box', targets['Box']['qualified_name'])
        self.assertEqual('class Box; def __init__(self, value)', targets['Box']['signature'])
        self.assertEqual(1, targets['Box']['parameter_count'])
        self.assertNotIn('description', targets['add'])
        self.assertNotIn('Add values', json.dumps(targets))

    def test_unknown_constructor_cannot_be_promoted_by_relabeling_body_category(self):
        self.ledger['records'][-1]['body_classification']['category'] = 'implementation'
        self.freeze()
        with self.assertRaisesRegex(ValueError, 'Unresolved source binding'):
            configured_api_details(self.cfg)

    def test_rehashed_owner_signature_params_and_arity_tampering_are_rejected_by_source_ast(self):
        original = deepcopy(self.ledger)
        for field, value in [('owner', 'Fake'), ('signature', 'def add(z)'), ('qualified_name', 'fake.add'),
                             ('params', [param('wrong'), param('y', '1')]), ('declared_params', []), ('line', 999)]:
            self.ledger = deepcopy(original); self.ledger['records'][0][field] = value; self.freeze()
            with self.subTest(field=field), self.assertRaises(ValueError): configured_api_details(self.cfg)

    def test_rehashed_constructor_metadata_changes_are_rejected(self):
        self.ledger['records'][1]['declared_constructors'][0]['signature'] = 'def __init__(self, invented)'
        self.freeze()
        with self.assertRaisesRegex(ValueError, 'constructor evidence'): configured_api_details(self.cfg)

    def test_no_public_declarations_can_be_dropped_from_rehashed_audit(self):
        self.ledger['records'].pop(0)
        self.definition['declaration_ids'].remove('add'); self.freeze()
        with self.assertRaisesRegex(ValueError, 'omits or duplicates'): configured_api_details(self.cfg)

    def test_source_root_file_hash_scope_and_manifest_identity_remain_frozen(self):
        self.definition['source_tree'] = '0' * 40; self.freeze_manifest()
        with self.assertRaisesRegex(ValueError, 'commit/tree'): configured_api_details(self.cfg)
        self.definition['source_tree'] = self.ledger['source_snapshot']['tree']; self.freeze_manifest()
        self.source_path.write_text(self.text + '\n# changed\n')
        with self.assertRaisesRegex(ValueError, 'commit/tree'): configured_api_details(self.cfg)
        self.source_path.write_text(self.text)
        self.cfg.source_globs = ['source/*.py']
        with self.assertRaisesRegex(ValueError, 'discovery scope'): configured_api_details(self.cfg)

    def test_wrong_winner_ids_and_selection_evidence_are_rejected(self):
        self.definition['canonical_declaration_ids'] = ['Inherited']; self.freeze_manifest()
        with self.assertRaisesRegex(ValueError, 'Canonical IDs'): configured_api_details(self.cfg)
        self.freeze()
        self.bound['selection']['winner_site_ids'] = ['Inherited']
        self.selection.write_text(json.dumps(self.bound)); self.definition['canonical_selection_sha256'] = sha(self.selection); self.freeze_manifest()
        with self.assertRaisesRegex(ValueError, 'does not replay'): configured_api_details(self.cfg)

    def test_external_original_documents_are_preserved_and_fully_scanned(self):
        first, second = self.root / 'README.md', self.root / 'other.md'
        first.write_text('Call `add(1)`.'); second.write_text('Construct `Box(1)`. Call `get()`.')
        self.cfg.original_readme_files = [first, second]
        self.cfg.original_readme_text = lambda **kwargs: first.read_text() + '\n' + second.read_text()
        self.cfg.llm_readme = self.root / 'not-generated.md'
        coverage = api_coverage(self.cfg)
        self.assertEqual(['README.md', 'other.md'], coverage['original_doc_files'])
        self.assertEqual(['Box', 'add', 'get'], coverage['original_documented_O'])

    def test_java_explicit_constructor_uses_its_public_name_signature_and_arity(self):
        self.source_path.unlink()
        self.text = 'package sample;\npublic class Tools {\n public Tools(int x) { this.x = x; }\n private int x;\n}\n'
        self.source_path = self.source_root / 'Tools.java'; self.source_path.write_text(self.text)
        self.git('add', '-A'); self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'java fixture')
        start = self.text.index('public Tools('); end = self.text.index('\n private int')
        row = {'site_id': 'ctor', 'language': 'Java', 'name': 'Tools', 'owner': 'sample.Tools',
               'qualified_name': 'sample.Tools', 'path': 'Tools.java', 'line': 3, 'start': start, 'end': end,
               'offset_unit': 'UTF-16 code units in decoded UTF-8 source', 'source_span_sha256': hashlib.sha256(self.text[start:end].encode()).hexdigest(),
               'kind': 'class_constructor', 'scope': 'production', 'declared_visibility': 'public',
               'public_owner_chain': True, 'synthetic': False, 'source_sha256': sha(self.source_path),
               'signature': '(int x):null', 'parameter_count': 1,
               'body_classification': {'category': 'implementation', 'reviewed': True, 'evidence': 'fixture'}}
        self.rows = [row]; self.make_manifest('Java', 'Tools.java')
        details = configured_api_details(self.cfg)
        self.assertEqual('Tools', details[0]['name'])
        self.assertEqual('public Tools(int x)', details[0]['signature'])
        self.assertEqual('sample.Tools', details[0]['returns'])
        self.assertEqual('x', details[0]['params'][0]['name'])
        self.ledger['records'][0]['signature'] = '(String x):null'; self.freeze()
        with self.assertRaisesRegex(ValueError, 'parameters differ'):
            configured_api_details(self.cfg)


if __name__ == '__main__': unittest.main()
