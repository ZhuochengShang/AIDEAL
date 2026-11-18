"""Synthetic end-to-end qualified README/R0 launcher tests.

The source parser boundary is replaced with fixed, source-hash-checked records.
Selection, preparation, documentation binding, rendered model prompts, recording,
scaffold execution, checkpoints and result maps use their actual implementation.
Only tiny arithmetic fixture code executes; no subject library or real API call.
"""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'vendor/aideal_engine/src'))
from aideal.api_canonical_selection import QUALIFIED_POLICY_VERSION, select_canonical_implementations
from aideal.api_origin import audit_api_origins
from aideal.config import load_config
from aideal.readme_format import api_storage_key


def load_launcher(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class QualifiedLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme=load_launcher('qualified_readme_launcher','run_readme_generation.py')
        cls.micro=load_launcher('qualified_micro_launcher','run_original_micro.py')

    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='aideal-qualified-launch-')
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()
        self.original=self.root/'original';self.source=self.original/'source'
        self.source.mkdir(parents=True)
        (self.original/'configs').mkdir();(self.original/'inputs').mkdir()
        self.source_file=self.source/'demo.py'
        self.source_file.write_text('class A:\n    def run(self, x):\n        return x+1\n\nclass B:\n    def run(self, x):\n        return x+2\n\ndef _adjust(x):\n    return x+3\n\nincrement = _adjust\n')
        self.source_hash=sha(self.source_file.read_bytes())
        (self.original/'scaffold.py').write_text('import sys\n'+f'sys.path.insert(0, {str(self.source)!r})\n'+'from demo import A, B, increment\n# AIDEAL_DATA_BINDINGS\n# START\n# END\nprint("DONE")\n')
        (self.original/'runtime').mkdir();(self.original/'runtime/mock.jar').write_bytes(b'Only a fixture path; never used by Python.')
        profile={'project':{'name':'qualified-fixture','language':'Python','description':'Arithmetic fixture.'},
                 'domain':'arithmetic','target_users':['Python developers'],'use_cases':['Compute small integer adjustments']}
        (self.original/'configs/project_profile.yaml').write_text(yaml.safe_dump(profile))
        raw={'project':{'name':'qualified-fixture','language':'Python'},
             'codebase':{'source_globs':['source/*.py'],'identity_mode':'qualified','surface_filter':'all',
                         'api_origin':{'source_roots':['source'],'library_namespaces':['demo'],'external_namespaces':['builtins']}},
             'files':{'project_profile':'configs/project_profile.yaml','original_readme':'inputs/original.md'},
             'comprehension':{'class_context':False,'execute':{'scaffold':'scaffold.py','region':['# START','# END'],
                    'command':shlex.quote(sys.executable)+' {test_file}','test_filename':'Generated.py',
                    'success_marker':'DONE','correctness_marker':'__CHECK__','require_correctness_check':True,
                    'work_dir':'execution','output_dir':'execution/output','max_fix_rounds':0,
                    'preamble':'','io_hints':'','spark_jars':'runtime/*.jar','probe_on_missing':False,'local_uris':False}},
             'models':{'registry':{'mock':{'provider':'synthetic','model':'offline'}},'roles':{'author':'mock','audience':'mock','fixer':'mock'}}}
        self.config=self.original/'configs/aideal.yaml';self.config.write_text(yaml.safe_dump(raw))
        cfg=load_config(self.config)
        candidates=[]
        for owner,name,line in [('demo.A','run',2),('demo.B','run',6),('demo','_adjust',9)]:
            private=name.startswith('_');qn=owner+'.'+name
            row={'site_id':'source:'+qn,'language':'Python','name':name,'owner':owner,'module':'demo',
                 'qualified_name':qn,'path':'source/demo.py','file':str(self.source_file),'line':line,
                 'source_sha256':self.source_hash,'file_sha256':self.source_hash,'source_span_sha256':sha(qn.encode()),
                 'params':[{'name':'x','type':'int','default':None,'required':True}], 'parameter_count':1,
                 'parameter_count_status':'declared','signature':f'def {name}(x: int) -> int','returns':'int','description':'',
                 'scope':'production','synthetic':False,'callable':True,'public_owner_chain':True,
                 'visibility':'non-public' if private else 'public','declared_visibility':'non-public' if private else 'public',
                 'definition_kind':'function' if private else 'method','defining_owner_kind':'module' if private else 'class',
                 'public_exposure_established':True,'preferred_public_path':'demo.increment' if private else qn,
                 'exposure_ids':['python:demo.increment' if private else 'python:'+qn],
                 'public_access_paths':['demo.increment' if private else qn],
                 'body_classification':{'category':'implementation'}}
            row['api_origin']=audit_api_origins(cfg,[row])['decisions'][0];candidates.append(row)
        receipt=select_canonical_implementations(candidates,policy_version=QUALIFIED_POLICY_VERSION)
        self.rows=receipt['winners'];self.names=receipt['winner_api_ids']
        selection=self.original/'inputs/selection.json';selection.write_text(json.dumps(receipt))
        # The compiler boundary is patched below, not the public registry,
        # selection, launcher or source/docs fingerprinting logic.
        inventory={'kind':'compiler_declared_methods','canonical_selection':'inputs/selection.json',
                   'source_commit':'synthetic-source','source_tree':'synthetic-tree','source_version':'fixture-v1',
                   'canonical_selection_sha256':sha(selection.read_bytes()),'canonical_selection_policy_version':QUALIFIED_POLICY_VERSION}
        inventory_path=self.original/'inputs/inventory.json';inventory_path.write_text(json.dumps(inventory))
        raw['codebase'].update(api_inventory='inputs/inventory.json',api_inventory_sha256=sha(inventory_path.read_bytes()))
        documents=[];targets={}
        original_doc=self.original/'inputs/original.md'
        original_doc.write_text('A.run(x) adds one. B.run(x) adds two. increment(x) adds three.\n')
        documents.append({'id':'manual','path':original_doc.name,'sha256':sha(original_doc.read_bytes()),'kind':'api_reference','origin_url':'https://example.invalid/manual'})
        for i,row in enumerate(self.rows):
            path=self.original/'inputs'/f'entry-{i}.md'
            path.write_text(row['preferred_public_path']+'(x) returns x + '+str(i+1)+'.\n')
            targets[row['api_id']]={'status':'documented','excerpts':[{'path':path.name,'sha256':sha(path.read_bytes()),'document_id':'manual','anchor':row['preferred_public_path']}]}
        manifest={'schema':'aideal.original-documents/v1','library':'fixture','source_version':'fixture-v1',
                  'source_commit':'synthetic-source','source_tree':'synthetic-tree','scope':'three source-defined fixture callables',
                  'documents':documents,'targets':targets}
        self.doc_manifest=self.original/'inputs/original_manifest.json';self.doc_manifest.write_text(json.dumps(manifest))
        raw['files'].update(original_doc_manifest='inputs/original_manifest.json',original_doc_manifest_sha256=sha(self.doc_manifest.read_bytes()))
        self.config.write_text(yaml.safe_dump(raw))
        self.manifest=self.original/'inputs/targets.json';self.manifest.write_text(json.dumps(self.names))
        self.library={'base_config':str(self.config),'manifest':str(self.manifest),'source_link':{'name':'source','target':str(self.source)}}
        def source_bound_rows(cfg,data):
            if sha(self.source_file.read_bytes())!=self.source_hash:raise ValueError('Synthetic source hash changed')
            return deepcopy(self.rows)
        self.registry_patch=patch('aideal.api_registry._compiler_details',side_effect=source_bound_rows)
        self.registry_patch.start();self.addCleanup(self.registry_patch.stop)
        environment=patch.dict(os.environ,{'PYTHONDONTWRITEBYTECODE':'1'})
        environment.start();self.addCleanup(environment.stop)

    def entry(self, name):
        row=next(r for r in self.rows if r['api_id']==name)
        return f'## API Test: `{name}`\n\n### Goal\nCompute a small integer adjustment.\n\n### Prompt Snippet\n```python\n{row["preferred_public_path"]}(1)\n```\n'

    def test_readme_preserves_two_owners_and_public_reexport_through_saved_prompts(self):
        destination=self.root/'readme'
        cfg,manifest,identity=self.readme.prepare(self.library,destination,'offline-no-api')
        self.assertEqual(self.names,manifest['names'])
        self.assertEqual('language_qualified_api_v1',manifest['identity_kind'])
        with patch('aideal.llm.invoke_text',side_effect=['summary']+[self.entry(n) for n in self.names]) as provider:
            result=self.readme.run_library(cfg,destination,manifest,identity)
        self.assertEqual(4,provider.call_count)
        self.assertEqual(3,result['selected'])
        self.assertEqual(self.names,[entry.name for entry in self.readme.parse_readme(cfg.llm_readme)])
        saved=[json.loads(path.read_text()) for path in (destination/'author_calls').rglob('request.json')]
        for name in self.names:
            self.assertTrue(any(name in row['user'] for row in saved),name)
        self.assertTrue(any('demo.increment' in row['user'] for row in saved))
        self.assertEqual('non-public',manifest['definitions']['python:demo._adjust'][0]['declared_visibility'])

    def test_original_runs_two_same_name_owners_in_distinct_folders_and_result_keys(self):
        destination=self.root/'micro'
        cfg,names=self.micro.prepare(self.library,destination,'offline-no-api',None)
        programs=['assert A().run(2) == 3\nprint("__CHECK__ python:demo.A.run 3")',
                  'assert B().run(2) == 4\nprint("__CHECK__ python:demo.B.run 4")',
                  'assert increment(2) == 5\nprint("__CHECK__ python:demo._adjust 5")']
        with redirect_stdout(io.StringIO()),patch('aideal.llm.invoke_text',side_effect=programs) as provider:
            summary=self.micro.run_library(cfg,destination,None)
        self.assertEqual(3,provider.call_count)
        self.assertEqual(3,summary['passes'])
        result=json.loads((destination/'result.json').read_text())
        self.assertEqual(set(names),set(result['metrics']))
        folders=[]
        for name in names:
            row=result['metrics'][name];self.assertEqual('pass',row['status'])
            evidence=Path(row['attempt_evidence'][0]);folders.append(evidence.parent)
            self.assertEqual('run_'+api_storage_key(name),evidence.parent.name)
            request=json.loads((evidence/'request.json').read_text())
            self.assertEqual(name,request['requested_target_declaration']['api_id'])
            self.assertIn(name,request['system']+request['user'])
            self.assertIn('__CHECK__ '+name,(evidence/'stdout.txt').read_text())
            self.assertEqual(0,json.loads((evidence/'execution.json').read_text())['exit_code'])
        self.assertEqual(3,len(set(folders)))
        with redirect_stdout(io.StringIO()),patch('aideal.llm.invoke_text',side_effect=AssertionError('Must reuse completed fixture')) as provider:
            self.micro.run_library(cfg,destination,None)
        self.assertEqual(0,provider.call_count)

    def test_absolute_inventory_binding_is_copied_into_original_output(self):
        inventory_path=self.original/'inputs/inventory.json'
        inventory=json.loads(inventory_path.read_text())
        inventory['canonical_selection']=str((self.original/'inputs/selection.json').resolve())
        inventory_path.write_text(json.dumps(inventory))
        raw=yaml.safe_load(self.config.read_text())
        raw['codebase']['api_inventory_sha256']=sha(inventory_path.read_bytes())
        self.config.write_text(yaml.safe_dump(raw))
        destination=self.root/'absolute-micro'
        cfg,names=self.micro.prepare(self.library,destination,'offline-no-api',None)
        self.assertEqual(self.names,names)
        self.assertEqual(inventory_path.read_bytes(),(destination/'inputs/api_inventory.json').read_bytes())
        self.assertEqual(self.names,self.micro._load_manifest(cfg,self.manifest))
        # Existing prepared inputs remain resumable without copying new bytes.
        self.micro.prepare(self.library,destination,'offline-no-api',None)

    def test_document_manifest_drift_rejects_prepared_readme_and_r0_before_provider(self):
        readme_destination=self.root/'readme';micro_destination=self.root/'micro'
        self.readme.prepare(self.library,readme_destination,'offline-no-api')
        self.micro.prepare(self.library,micro_destination,'offline-no-api',None)
        # Even if the caller updates the top-level checksum, prepared snapshots
        # cannot resume using different original-document evidence.
        manifest=json.loads(self.doc_manifest.read_text());manifest['scope']+=' changed'
        self.doc_manifest.write_text(json.dumps(manifest))
        raw=yaml.safe_load(self.config.read_text())
        raw['files']['original_doc_manifest_sha256']=sha(self.doc_manifest.read_bytes())
        self.config.write_text(yaml.safe_dump(raw))
        with patch('aideal.llm.invoke_text',side_effect=AssertionError('No provider before drift check')) as provider:
            with self.assertRaisesRegex(ValueError,'changed'):
                self.readme.prepare(self.library,readme_destination,'offline-no-api')
            with self.assertRaisesRegex(ValueError,'changed'):
                self.micro.prepare(self.library,micro_destination,'offline-no-api',None)
        self.assertEqual(0,provider.call_count)


if __name__=='__main__':
    unittest.main()
