"""Qualified alias/source-hint preview relocation; synthetic Git fixtures only."""
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
from workflow.ablation import bind,load
from workflow.improvement_context import preview_improvements,_library_inputs,_qualified_library_definitions
from workflow.improvement_context import _source_windows
from workflow.improvement_batches import preview_library_improvements
from workflow.improvement_suggestions import validate_suggestions
from workflow.failure_diagnosis import diagnose_failure
from workflow.native_hints import patch_message
from workflow.worktrees import attach


class QualifiedDevelopmentTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='aideal-qualified-development-');self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.repo=self.root/'repository'
        self.path=self.repo/'src/package/api.py';self.path.parent.mkdir(parents=True)
        self.path.write_text('raise RuntimeError("TARGET MUST NEVER BE IMPORTED")\n\n'
            'class A:\n    def run(self, x):\n        if x < 0:\n            raise ValueError("Input must be nonnegative.")\n        return x\n\n'
            'class B:\n    def run(self, x):\n        return x+1\n\n'
            'def _adjust(x):\n    return x+2\n\nincrement = _adjust\n')
        (self.repo/'README.md').write_text('Use package.api.A.run or package.api.B.run with a number.')
        self.git(self.repo,'init','-q');self.git(self.repo,'config','user.name','Fixture');self.git(self.repo,'config','user.email','fixture@example.invalid')
        self.git(self.repo,'add','.');self.git(self.repo,'commit','-qm','Source baseline')
        self.source_commit=self.git(self.repo,'rev-parse','HEAD')
        (self.root/'configs').mkdir();(self.root/'inputs').mkdir()
        (self.root/'inputs/ledger.json').write_text('{}');(self.root/'inputs/selection.json').write_text('{}')
        manifest={'kind':'qualified_source_api_inventory','source_root':'repository','source_inventory':'inputs/ledger.json',
                  'canonical_selection':'inputs/selection.json','source_commit':self.source_commit}
        (self.root/'inputs/inventory.json').write_text(json.dumps(manifest))
        config={'project':{'name':'fixture','language':'Python'},'codebase':{'identity_mode':'qualified','surface_filter':'all',
                    'source_globs':['repository/src/**/*.py'],'api_inventory':'inputs/inventory.json',
                    'api_inventory_sha256':hashlib.sha256((self.root/'inputs/inventory.json').read_bytes()).hexdigest()},
                'files':{'original_readme':'repository/README.md'}}
        self.config=self.root/'configs/aideal.yaml';self.config.write_text(yaml.safe_dump(config))
        self.study=self.root/'study';attach(self.repo,self.config,self.study)
        attached=self.study/'Original/source'
        # An instrumentation commit is allowed to differ from the pristine source
        # commit. The source-file bytes must still match, and the attachment pins it.
        (attached/'instrumentation.txt').write_text('Study instrumentation')
        self.git(attached,'add','instrumentation.txt');self.git(attached,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','Instrumentation')
        attachment=load(self.study/'attachment.json');attachment['revision']=self.git(attached,'rev-parse','HEAD')
        (self.study/'attachment.json').write_text(json.dumps(attachment))
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.rows=[]
        for qname,name,line in [('package.api.A.run','run',4),('package.api.B.run','run',10),('package.api._adjust','_adjust',13)]:
            private=name.startswith('_');api='python:'+qname
            self.rows.append({'name':name,'api_id':api,'qualified_name':qname,'owner':qname.rsplit('.',1)[0],
                'file':'repository/src/package/api.py','defining_file':'repository/src/package/api.py','line':line,
                'source_sha256':digest,'signature':f'def {name}(x)','visibility':'non-public' if private else 'public',
                'declared_visibility':'non-public' if private else 'public','public_exposure_established':True,
                'exposure_ids':['python:package.api.increment' if private else api],
                'public_access_paths':['package.api.increment' if private else qname],
                'params':[{'name':'x','type':''}],'returns':'','description':'','module':'package.api'})
        self.discovery_calls=[]
        def discover(cfg):
            self.discovery_calls.append(cfg.root)
            self.assertEqual(self.root,cfg.root,'Discovery must keep the original external config root')
            self.assertTrue((cfg.root/cfg.raw['codebase']['api_inventory']).is_file())
            return deepcopy(self.rows)
        discovery=patch('aideal.api_discovery.public_api_details',side_effect=discover)
        discovery.start();self.addCleanup(discovery.stop)

    def git(self,root,*args):
        return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL).strip()

    def test_external_provenance_and_instrumented_checkout_map_by_verified_bytes(self):
        result=preview_improvements(self.study,self.root/'preview',alias_path='src/package/aliases.py')
        preview=load(result['preview']);apis=preview['context']['apis']
        self.assertEqual(3,len(apis));self.assertEqual(0,result['llm_calls'])
        self.assertTrue(all(row['id']==row['api_id'] for row in apis))
        self.assertTrue(all(row['file']=='src/package/api.py' for row in apis))
        self.assertIn('TARGET MUST NEVER BE IMPORTED',apis[0]['source_window']['text'])
        self.assertNotEqual(self.source_commit,preview['baseline_revision'])
        self.assertEqual('src/package/api.py:4:package.api.A.run',preview['context']['api_function_ids']['python:package.api.A.run'])
        self.assertEqual(['package.api.increment'],preview['context']['api_public_paths']['python:package.api._adjust'])
        artifacts={ref['path'] for ref in preview['artifacts']}
        self.assertIn(str(self.root/'inputs/inventory.json'),artifacts)
        self.assertIn(str(self.path),artifacts)
        self.assertIn(str(self.study/'Original/source/src/package/api.py'),artifacts)

    def test_bare_same_name_fails_and_exact_owner_id_selects_one(self):
        with self.assertRaisesRegex(ValueError,'Ambiguous API'):_library_inputs(self.study,['run'])
        definitions=_library_inputs(self.study,['python:package.api.B.run'])[4]
        self.assertEqual(['python:package.api.B.run'],[row['id'] for row in definitions])
        public=_library_inputs(self.study,['package.api.increment'])[4]
        self.assertEqual(['python:package.api._adjust'],[row['id'] for row in public])

    def test_batched_preview_keeps_owner_ids_and_source_patch_mapping(self):
        result=preview_library_improvements(self.study,self.root/'batches',batch_size=1,max_catalog_characters=1000)
        manifest=load(result['manifest']);ids=[api for batch in manifest['batches'] for api in batch['api_ids']]
        self.assertEqual(3,len(ids));self.assertEqual(3,len(set(ids)))
        self.assertEqual(set(ids),set(manifest['api_function_ids']))
        with self.assertRaisesRegex(ValueError,'Ambiguous API'):
            preview_library_improvements(self.study,self.root/'ambiguous',apis=['run'])

    def test_changed_attached_source_and_untracked_source_are_rejected(self):
        cfg=load_config(self.config);root=self.study/'Original/source'
        with self.assertRaisesRegex(ValueError,'tracked'):_qualified_library_definitions(cfg,root,set())
        file=root/'src/package/api.py';file.write_text(file.read_text()+'\n# changed\n')
        with self.assertRaisesRegex(ValueError,'differs from the pinned'):
            _qualified_library_definitions(cfg,root,{'src/package/api.py'})

    def test_registered_sql_docs_are_never_read_as_implementation_windows(self):
        manifest=self.root/'inputs/inventory.json';data=load(manifest);data['kind']='registered_sql';manifest.write_text(json.dumps(data))
        raw=yaml.safe_load(self.config.read_text());raw['codebase']['api_inventory_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.config.write_text(yaml.safe_dump(raw))
        with self.assertRaisesRegex(ValueError,'not implementation source'):
            _qualified_library_definitions(load_config(self.config),self.study/'Original/source',{'src/package/api.py'})

    def test_alias_and_native_hint_consumers_use_separate_explicit_identities(self):
        preview=load(preview_improvements(self.study,self.root/'preview',alias_path='src/package/aliases.py',apis=['python:package.api.A.run'])['preview'])
        context=preview['context'];api=context['apis'][0]
        response={'aliases':[{'name':'run_a','target_function':api['id'],'rationale':'Explicit owner'}],
                  'alias_code':'def run_a(instance, x):\n    return instance.run(x)\n','alias_interface':'run_a forwards to A.run.',
                  'hints':[],'notes':'Synthetic only'}
        self.assertEqual(api['id'],validate_suggestions(response,context)['aliases'][0]['target_function'])
        hint={'function_id':api['source_function_id'],'requirement_id':'nonnegative','error_line':6,
              'original_message':'Input must be nonnegative.','action':'Pass an input at least zero.'}
        changed,message=patch_message(self.path.read_text(),api['file'],hint)
        self.assertIn('[AIDEAL fix:nonnegative]',message);self.assertIn(message,changed)
        self.assertEqual(self.path.read_text(),(self.study/'Original/source'/api['file']).read_text())

    def test_development_logs_match_exact_api_and_reject_ambiguous_name(self):
        log=self.root/'development.jsonl'
        log.write_text('\n'.join(json.dumps({'function':name,'status':'fail','split':'development','error':'bad input'}) for name in ['run','python:package.api.B.run']))
        preview=load(preview_improvements(self.study,self.root/'preview',development_errors=log)['preview'])
        self.assertEqual(1,preview['context']['coverage']['omitted_error_rows'])
        self.assertEqual('python:package.api.B.run',preview['context']['development_errors'][0]['function_id'])

    def test_failure_localization_understands_api_prefix_and_public_exposure(self):
        index={'api_function_ids':{'python:package.api.A.run':'api.py:4:run','python:package.api.B.run':'api.py:10:run',
                                  'python:package.api._adjust':'api.py:13:_adjust'},
               'api_public_paths':{'python:package.api._adjust':['package.api.increment']}}
        previous={'code':'package.api.A.run(-1)','feedback':'at package.api.A.run(Api.java:4)'}
        self.assertEqual('api.py:4:run',diagnose_failure(index,previous)['function_id'])
        previous={'code':'from package.api import increment\nincrement(-1)',
                  'feedback':'Candidate.py:2: error: bad input\nincrement(-1)\n^'}
        self.assertEqual('api.py:13:_adjust',diagnose_failure(index,previous)['function_id'])

    def test_companion_kind_collision_is_not_guessed_from_textual_owner(self):
        index={'api_function_ids':{'scala:class:own.Tile.rescale':'Tile.scala:3:rescale',
                                  'scala:object:own.Tile.rescale':'Tile.scala:20:rescale'}}
        result=diagnose_failure(index,{'code':'own.Tile.rescale(2)','feedback':'at own.Tile.rescale(Tile.scala:3)'})
        self.assertEqual('ambiguous_function',result['status'])

    def test_companion_preview_preserves_two_source_sites_in_same_file(self):
        path=self.repo/'src/Tile.scala'
        path.write_text('package own\nclass Tile {\n  def rescale(n: Int): Int = n\n}\n'
                        'object Tile {\n  def rescale(n: Int): Int = n+1\n}\n')
        self.git(self.repo,'add','src/Tile.scala');self.git(self.repo,'commit','-qm','Companion fixture')
        raw=yaml.safe_load(self.config.read_text());raw['project']['language']='Scala'
        raw['codebase']['source_globs']=['repository/src/*.scala']
        config=self.root/'configs/scala.yaml';config.write_text(yaml.safe_dump(raw))
        study=self.root/'companion-study';attach(self.repo,config,study)
        rows=[]
        for kind,line in [('class',3),('object',6)]:
            rows.append({**self.rows[0],'api_id':f'scala:{kind}:own.Tile.rescale','name':'rescale',
                'qualified_name':'own.Tile.rescale','owner':'own.Tile','defining_owner_kind':kind,
                'file':'repository/src/Tile.scala','defining_file':'repository/src/Tile.scala','line':line,
                'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'signature':'def rescale(n: Int): Int',
                'exposure_ids':[],'public_access_paths':[]})
        self.rows=rows
        with self.assertRaisesRegex(ValueError,'Ambiguous API'):_library_inputs(study,['own.Tile.rescale'])
        definitions=_library_inputs(study)[4]
        self.assertEqual({r['api_id'] for r in rows},{r['id'] for r in definitions})
        self.assertEqual({'src/Tile.scala:3:rescale','src/Tile.scala:6:rescale'},
                         {r['source_function_id'] for r in definitions})

    def test_changed_source_between_mapping_and_window_capture_is_rejected(self):
        _,root,_,_,definitions,_=_library_inputs(self.study)
        path=root/definitions[0]['file'];path.write_text(path.read_text()+'\n# changed after mapping\n')
        with self.assertRaisesRegex(ValueError,'source changed before source-window'):
            _source_windows(root,definitions)


if __name__=='__main__':unittest.main()
