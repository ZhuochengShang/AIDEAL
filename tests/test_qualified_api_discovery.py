"""Qualified discovery/coverage contracts; no model, network or subject calls."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.api_discovery import api_coverage, public_api_details, public_api_surface, surface_audit
from aideal.api_registry import configured_api_details, target_key, with_api_identity


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class QualifiedDiscoveryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cfg = SimpleNamespace(root=self.root, language='Python', surface_filter='all',
            llm_readme=self.root/'generated.md', original_readme_files=[],
            raw={'codebase': {'identity_mode':'qualified'}})
        self.rows = [{'name':'run', 'qualified_name':'ownlib.A.run', 'visibility':'public'},
                     {'name':'run', 'qualified_name':'ownlib.B.run', 'visibility':'public'}]

    def test_helper_preserves_bare_name_and_derives_stable_defining_key(self):
        rows = with_api_identity(self.cfg, self.rows)
        self.assertEqual(['run','run'], [row['name'] for row in rows])
        self.assertEqual(['python:ownlib.A.run','python:ownlib.B.run'], [target_key(row) for row in rows])
        self.assertNotIn('api_id', self.rows[0])

    def test_legacy_identity_returns_exact_original_object(self):
        self.cfg.raw = {'codebase':{}}
        self.assertIs(self.rows, with_api_identity(self.cfg, self.rows))
        self.assertEqual('run', target_key(self.rows[0]))

    def test_conflicting_or_missing_identity_fails_without_guessing(self):
        for row in ({'name':'run'}, {'name':'run','qualified_name':'run'},
                    {**self.rows[0], 'api_id':'python:ownlib.B.run'}):
            with self.subTest(row=row), self.assertRaises(ValueError):
                with_api_identity(self.cfg, [row])
        self.cfg.raw['codebase']['identity_mode']='guess'
        with self.assertRaises(ValueError): with_api_identity(self.cfg, self.rows)

    def test_sql_keys_use_sql_namespace(self):
        rows=with_api_identity(self.cfg,[{'name':'ST_Area','definition_kind':'registered_sql'}])
        self.assertEqual('sql:ST_Area', target_key(rows[0]))

    def test_registered_surface_never_collapses_distinct_owners(self):
        rows=with_api_identity(self.cfg,self.rows)
        with patch('aideal.api_discovery.configured_api_details', return_value=rows):
            self.assertEqual({'python:ownlib.A.run','python:ownlib.B.run'}, public_api_surface(self.cfg))
            self.assertEqual(rows, public_api_details(self.cfg))

    def test_raw_qualified_surface_uses_exact_key_and_public_exposure(self):
        rows=self.rows+[{'name':'_run','qualified_name':'ownlib._private._run','visibility':'non-public',
                        'public_exposure_established':True},
                       {'name':'hidden','qualified_name':'ownlib.hidden','visibility':'non-public'}]
        with patch('aideal.api_discovery.configured_api_details', return_value=None), \
             patch('aideal.api_discovery._unfiltered_api_details', return_value=rows):
            self.assertEqual({'python:ownlib.A.run','python:ownlib.B.run','python:ownlib._private._run'}, public_api_surface(self.cfg))

    def test_qualified_raw_name_only_intent_filter_is_rejected(self):
        self.cfg.surface_filter='intent_score'
        with patch('aideal.api_discovery.configured_api_details', return_value=None), self.assertRaisesRegex(ValueError,'surface_filter'):
            public_api_surface(self.cfg)

    def test_catalogue_audit_distinguishes_owners(self):
        rows=with_api_identity(self.cfg,self.rows)
        entries=[SimpleNamespace(name='python:ownlib.A.run'),SimpleNamespace(name='python:ownlib.C.run')]
        with patch('aideal.api_discovery.public_api_details',return_value=rows), \
             patch('aideal.api_discovery.public_api_surface',return_value={target_key(r) for r in rows}), \
             patch('aideal.api_discovery.parse_readme',return_value=entries), \
             patch('aideal.api_discovery._iter_defs',return_value=[]):
            result=surface_audit(self.cfg)
        self.assertEqual(2,result['public_names_on_surface'])
        self.assertEqual(['python:ownlib.C.run'],result['prune_candidates'])

    def documents(self):
        doc=self.root/'reference.md';doc.write_text('ownlib.A.run(x) runs A. The bare name run also occurs here.')
        excerpt=self.root/'A.run.md';excerpt.write_text('ownlib.A.run(x) runs A.')
        manifest={'schema':'aideal.original-documents/v1','library':'fixture','source_version':'v1',
                  'source_commit':'fixture-commit','source_tree':'fixture-tree','scope':'owned public definitions',
                  'documents':[{'id':'api','path':doc.name,'sha256':sha(doc.read_bytes()),'kind':'api_reference','origin_url':'https://example.invalid/api'}],
                  'targets':{'python:ownlib.A.run':{'status':'documented','excerpts':[{'path':excerpt.name,'sha256':sha(excerpt.read_bytes()),'document_id':'api','anchor':'ownlib.A.run'}]},
                             'python:ownlib.B.run':{'status':'undocumented','reason':'No owner-specific reference in reviewed corpus'},
                             'python:ownlib.C.run':{'status':'unresolved','reason':'Reference fragment does not establish defining owner'}}}
        path=self.root/'original.json';path.write_text(json.dumps(manifest))
        self.cfg.raw['files']={'original_doc_manifest':path.name,'original_doc_manifest_sha256':sha(path.read_bytes())}
        return path,doc,excerpt

    def test_coverage_uses_exact_bound_target_not_bare_name(self):
        self.documents()
        surface={f'python:ownlib.{x}.run' for x in 'ABCD'}
        self.cfg.llm_readme.write_text('generated')
        with patch('aideal.api_discovery.public_api_surface',return_value=surface), \
             patch('aideal.api_discovery.parse_readme',return_value=[SimpleNamespace(name='python:ownlib.B.run')]):
            result=api_coverage(self.cfg)
        self.assertEqual(['python:ownlib.A.run'],result['original_documented_O'])
        self.assertEqual(['python:ownlib.B.run'],result['undocumented_in_original'])
        self.assertEqual(['python:ownlib.C.run','python:ownlib.D.run'],result['original_documentation_unresolved'])
        self.assertEqual(25.0,result['coverage']['original_pct_of_S'])
        self.assertFalse(result['original_coverage_resolved'])
        self.assertEqual([],result['shared_T'])

    def test_changed_original_excerpt_is_rejected(self):
        _,_,excerpt=self.documents();excerpt.write_text('changed')
        with patch('aideal.api_discovery.public_api_surface',return_value={'python:ownlib.A.run'}), \
             self.assertRaisesRegex(ValueError,'checksum mismatch'):
            api_coverage(self.cfg)

    def test_missing_original_manifest_is_not_guessed_from_names(self):
        with patch('aideal.api_discovery.public_api_surface',return_value={'python:ownlib.A.run'}), \
             self.assertRaisesRegex(ValueError,'original_doc_manifest'):
            api_coverage(self.cfg)

    def test_new_inventory_dispatch_checks_manifest_hash(self):
        path=self.root/'inventory.json';path.write_text(json.dumps({'kind':'qualified_source_api_inventory','schema':2}))
        self.cfg.raw['codebase'].update(api_inventory=path.name,api_inventory_sha256=sha(path.read_bytes()))
        with patch('aideal.api_public_inventory.qualified_inventory_details',return_value=self.rows) as reader:
            self.assertEqual(with_api_identity(self.cfg,self.rows),configured_api_details(self.cfg))
            reader.assert_called_once()
        self.cfg.raw['codebase']['identity_mode']='legacy'
        with self.assertRaisesRegex(ValueError,'identity_mode=qualified'):
            configured_api_details(self.cfg)
        self.cfg.raw['codebase']['identity_mode']='qualified'
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'checksum'):
            configured_api_details(self.cfg)


if __name__=='__main__':
    unittest.main()
