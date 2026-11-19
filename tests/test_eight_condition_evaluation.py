"""Execute the full factorial through the existing runner; no external model calls."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import yaml

from workflow.ablation import bind, digest, load
from workflow.evaluation_inputs import EIGHT_ARMS, ALIAS_ARMS, HINT_ARMS, README_ARMS
from workflow.evaluation_freeze import freeze_conditions, open_conditions, read_condition_config
from workflow.condition_evaluation import run_conditions
import test_condition_evaluation as condition_fixtures
import test_native_hints as hint_fixtures

ADAPTER = r'''
import hashlib, json, pathlib, subprocess, sys, types
r=json.load(sys.stdin)
root=pathlib.Path(sys.argv[1])
head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
assert head==r['backend']['revision'] and str(root)==r['backend']['worktree']
lib=types.ModuleType('lib');exec(compile((root/'lib.py').read_text(),str(root/'lib.py'),'exec'),lib.__dict__)
reached=[]; aliases=[]; original=lib.resize
 def_placeholder
namespace={'resize':tracked}
if (root/'aliases.py').exists():
    sys.modules['lib']=lib
    module=types.ModuleType('aliases');exec(compile((root/'aliases.py').read_text(),str(root/'aliases.py'),'exec'),module.__dict__)
    forward=module.fit_box
    def traced_alias(*args,**kwargs):
        aliases.append('fit_box');return forward(*args,**kwargs)
    namespace['fit_box']=traced_alias
try:
    exec(compile(r['code'],'<candidate>','exec'),namespace)
    observation={'kind':'return','value':namespace['result']};feedback=''
except Exception as exc:
    observation={'kind':'raise','type':type(exc).__name__,'message':str(exc)}
    feedback=type(exc).__name__+': '+str(exc)
expected=json.loads(pathlib.Path(r['oracle_path']).read_text())
# Error controls intentionally check the actual exception type and message.
# Held-out evaluation expects successful return values, so exceptions fail it.
correct=observation==expected
executed=observation['kind']=='return' or expected.get('kind')=='raise'
print(json.dumps({'execution_pass':executed,'oracle_pass':correct,'target_reached':bool(reached),
 'backend_sha256':r['backend']['sha256'],'public_feedback':feedback,
 'aliases_reached':aliases,'observed_kind':observation['kind'],
 'observation_sha256':hashlib.sha256(json.dumps(observation,sort_keys=True).encode()).hexdigest()}))
'''.replace(' def_placeholder', '''def tracked(*args,**kwargs):
    reached.append(True);return original(*args,**kwargs)
lib.resize=tracked''')

MODEL = r'''
import json,sys
r=json.load(sys.stdin);p=r['prompt']
assert 'PRIVATE_ORACLE_ONLY' not in str(r) and 'oracle_path' not in str(r) and 'alias_control' not in r
assert not ('TASK_MICRO' in p and 'TASK_PUZZLE' in p)
correct='BETTER_DOCS' in p or 'USE_ALIAS' in p or '[AIDEAL fix:positive_width]' in p
call='fit_box' if 'USE_ALIAS' in p else 'resize'
code='result = '+call+('(10, 5)' if correct else '(0, 5)')
print(json.dumps({'code':code,'usage':{'input_tokens':7,'output_tokens':3}}))
'''


class EightConditionTests(unittest.TestCase):
    git=staticmethod(condition_fixtures.ConditionEvaluationTests.git)

    def setUp(self):
        self.fixture=hint_fixtures.NativeHintTests()
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root
        self.base=self.fixture.baseline
        self.validation=self.fixture.validate()
        proposal=load(load(self.validation)['proposal']['path'])
        self.hinted=Path(proposal['sources'][0]['candidate']['path']).read_bytes()
        (self.base/'README.md').write_text('ORIGINAL_DOC')
        self.git(self.base,'init','-q');self.git(self.base,'add','.');self.git(self.base,'commit','-qm','baseline')
        self.adapter=self.root/'checker.py';self.adapter.write_text(ADAPTER)
        self.model=self.root/'model.py';self.model.write_text(MODEL)
        self.alias_source='from lib import resize\ndef fit_box(width, height=5):\n    return resize(width, height)\n'
        self.conditions={}
        for arm in EIGHT_ARMS:
            work=self.root/arm
            self.git(self.root,'clone','-q','--no-hardlinks',str(self.base),str(work))
            self.git(work,'checkout','-qb','aideal/'+arm)
            treatments=work/'.aideal/treatments';treatments.mkdir(parents=True)
            if arm in ALIAS_ARMS:
                (work/'aliases.py').write_text(self.alias_source)
                (treatments/'ALIASES.md').write_text('USE_ALIAS fit_box(width, height=5) forwards to resize.')
            if arm in HINT_ARMS:
                (work/'lib.py').write_bytes(self.hinted)
            if arm in README_ARMS:
                (treatments/'README.md').write_text('BETTER_DOCS resize requires positive dimensions.')
            self.git(work,'add','.')
            self.git(work,'commit','--allow-empty','-qm',arm)
            condition={'documents':[str(treatments/'README.md' if arm in README_ARMS else work/'README.md')],
                'source':{'worktree':str(work),'revision':self.git(work,'rev-parse','HEAD'),
                    'artifacts':[str(work/'lib.py')]+([str(work/'aliases.py')] if arm in ALIAS_ARMS else [])},
                'adapter':{'command':[sys.executable,str(self.adapter),str(work)],'artifacts':[str(self.adapter)]}}
            if arm in ALIAS_ARMS:condition['alias_interface']=str(treatments/'ALIASES.md')
            if arm in HINT_ARMS:condition['native_hints_validation']=str(self.validation)
            self.conditions[arm]=condition
        bundle=self.root/'alias_bundle';bundle.mkdir()
        (bundle/'aliases.py').write_text(self.alias_source)
        (bundle/'ALIASES.md').write_text(Path(self.conditions['alias_only']['alias_interface']).read_text())
        self.bundle=bundle/'proposal.json'
        self.write_json(self.bundle,{'schema_version':2,'baseline_revision':self.conditions['original']['source']['revision'],
            'aliases':[{'name':'fit_box','target_function':'lib.py:1:resize','rationale':'Explicit forwarding example'}],
            'artifacts':{'alias_0001':{**bind(bundle/'aliases.py'),'target':'aliases.py'},
                         'alias_interface':bind(bundle/'ALIASES.md')}})
        for name,text in {'reference.py':'result = resize(10,5)','wrong.py':'result = resize(9,5)',
                          'no_target.py':'result = [10,5]'}.items():(self.root/name).write_text(text)
        self.write_json(self.root/'bank_oracle.json',{'kind':'return','value':[10,5]})
        cases=[{'id':kind,'kind':kind,'split':'held_out','target_apis':['resize'],
            'prompt':'TASK_'+kind.upper()+': produce dimensions 10 by 5.',
            'public_context':'Use the provided dimension library.',
            'reference':'reference.py','negative_controls':['wrong.py'],
            'target_negative_controls':['no_target.py'],'oracle':'bank_oracle.json'} for kind in ('micro','puzzle')]
        self.write_json(self.root/'bank.json',{'api_names':['resize'],'cases':cases,'scope_note':'Offline software validation only; not library measurements.'})
        alias_cases=[]
        for case_id,kind,canonical,alias,observation in [
            ('dev_default','valid','resize(10,5)','fit_box(10)',{'kind':'return','value':[10,5]}),
            ('dev_keyword','valid','resize(10,7)','fit_box(10,height=7)',{'kind':'return','value':[10,7]}),
            ('dev_error','error','resize(0,5)','fit_box(0)',{'kind':'raise','type':'ValueError','message':'Width must be positive.'}),
        ]:
            folder=self.root/case_id;folder.mkdir()
            for name,code in [('canonical.py','result = '+canonical),('alias.py','result = '+alias),
                ('wrong.py','result = fit_box(3, 4)'),('bypass.py','result = '+canonical)]:
                (folder/name).write_text(code)
            self.write_json(folder/'oracle.json',observation)
            alias_cases.append({'id':case_id,'split':'development','kind':kind,'alias':'fit_box','target_api':'resize',
                'canonical_reference':str(folder/'canonical.py'),'alias_reference':str(folder/'alias.py'),
                'oracle':str(folder/'oracle.json'),'negative_controls':[str(folder/'wrong.py')],
                'alias_negative_controls':[str(folder/'bypass.py')]})
        self.cfg={'condition_evaluation':{'schema_version':3,'design':'eight_arm','bank':'bank.json',
            'conditions':self.conditions,'api_function_ids':{'resize':'lib.py:1:resize'},
            'alias_validation':{'proposal':str(self.bundle),'cases':alias_cases},
            'development_case_ids':[row['id'] for row in alias_cases],
            'model':{'name':'synthetic-no-model','command':[sys.executable,str(self.model)],'artifacts':[str(self.model)]},
            'common':{'temperature':0,'max_output_tokens':100,'provider_attempt_limit':1,'execution_timeout_s':5,
                'provider_timeout_s':5,'max_snippet_fixes':2,'trial_ids':['trial_01'],
                'documentation_max_characters':500,'alias_max_characters':500,'hint_max_characters':500},
            'holdout_review':'Synthetic disjoint development and held-out controls; no model calls.'}}
        self.config=self.root/'study.yaml';self.write_config()

    @staticmethod
    def write_json(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
    def write_config(self):self.config.write_text(yaml.safe_dump(self.cfg,sort_keys=False))
    def freeze(self):return Path(freeze_conditions(self.config,self.root/'freeze')['frozen'])

    def test_eight_arms_execute_independent_controls_repair_and_resume(self):
        study=self.freeze();frozen=open_conditions(study)
        self.assertEqual(48,len(frozen['validation']['controls']))
        self.assertEqual(12,len(frozen['validation']['alias_validation']['controls']))
        self.assertEqual('episode_only',frozen['config']['common']['memory_policy'])
        out=self.root/'run';summary=run_conditions(study,out)
        self.assertTrue(summary['all_complete'])
        self.assertEqual(56,len(summary['paired_comparisons']))
        for arm in EIGHT_ARMS:
            for kind in ('micro','puzzle'):
                metric=summary['metrics'][arm][kind]
                self.assertEqual(int(arm!='original'),metric['correct_within_budget'])
                self.assertEqual(int(arm in README_ARMS or arm in ALIAS_ARMS),metric['first_attempt_correct'])
        before={p:p.read_bytes() for p in out.glob('*/**/provider_*/request.json')}
        self.assertEqual(summary,run_conditions(study,out))
        self.assertEqual(before,{p:p.read_bytes() for p in out.glob('*/**/provider_*/request.json')})
        for path in before:
            text=path.read_text()
            self.assertNotIn('oracle_path',text);self.assertNotIn('alias_control',text)
            if 'round_00' in str(path):self.assertNotIn('[AIDEAL fix:',text)
        hints=load(out/'error_hints_only/micro--trial_01/round_01/context_exposure.json')
        self.assertEqual('',hints['hints']['text'])
        self.assertTrue(hints['native_diagnostics']['observed_requirement_ids'])
        self.assertFalse((out/'readme_error_hints/micro--trial_01/round_01').exists())

    def test_new_design_rejects_legacy_hints_missing_alias_proof_and_memory_carryover(self):
        original=deepcopy(self.cfg)
        mutations=[lambda c:c.update(schema_version=1),lambda c:c.pop('alias_validation'),
                   lambda c:c['common'].update(memory_policy='cross_trial')]
        for mutate in mutations:
            self.cfg=deepcopy(original);mutate(self.cfg['condition_evaluation']);self.write_config()
            with patch('workflow.evaluation_freeze.invoke') as invoke:
                with self.assertRaises(ValueError):read_condition_config(self.config)
                invoke.assert_not_called()

    def test_partial_alias_control_coverage_and_holdout_overlap_rejected(self):
        c=self.cfg['condition_evaluation'];c['alias_validation']['cases']=c['alias_validation']['cases'][:2]
        self.write_config()
        with self.assertRaisesRegex(ValueError,'valid and error'):read_condition_config(self.config)
        c['alias_validation']['cases'][0]['id']='micro';self.write_config()
        with self.assertRaisesRegex(ValueError,'development IDs'):read_condition_config(self.config)

    def test_pairwise_document_or_backend_contamination_rejected(self):
        original=deepcopy(self.cfg)
        for arm,field,value in [('readme_alias','documents',self.conditions['original']['documents']),
             ('alias_error_hints','alias_interface',str(self.root/'wrong.py'))]:
            self.cfg=deepcopy(original);self.cfg['condition_evaluation']['conditions'][arm][field]=value;self.write_config()
            with self.assertRaises(ValueError):read_condition_config(self.config)
        self.cfg=original
        root=self.root/'readme_alias';(root/'aliases.py').write_text(self.alias_source.replace('resize(width, height)','resize(width, 9)'))
        self.git(root,'add','.');self.git(root,'commit','-qm','wrong wrapper')
        self.cfg['condition_evaluation']['conditions']['readme_alias']['source']['revision']=self.git(root,'rev-parse','HEAD');self.write_config()
        with self.assertRaisesRegex(ValueError,'backend code tree'):read_condition_config(self.config)

    def _replace_alias(self, source):
        for arm in ALIAS_ARMS:
            root=self.root/arm;(root/'aliases.py').write_text(source)
            self.git(root,'add','.');self.git(root,'commit','-qm','changed wrapper')
            self.conditions[arm]['source']['revision']=self.git(root,'rev-parse','HEAD')
        bundle=load(self.bundle);path=self.bundle.parent/'aliases.py';path.write_text(source)
        bundle['artifacts']['alias_0001']={**bind(path),'target':'aliases.py'};self.write_json(self.bundle,bundle);self.write_config()

    def test_dropped_keyword_argument_cannot_pass_alias_gate(self):
        self._replace_alias(self.alias_source.replace('resize(width, height)','resize(width, 5)'))
        with self.assertRaisesRegex(ValueError,'Condition controls failed'):self.freeze()
        record=load(self.root/'freeze/validation/aliases/validation.json')
        self.assertFalse(record['validated']);self.assertEqual('dev_keyword',record['controls'][-1]['case_id'])

    def test_changed_exception_cannot_pass_alias_gate(self):
        self._replace_alias('from lib import resize\ndef fit_box(width, height=5):\n    try:\n        return resize(width,height)\n    except ValueError:\n        raise TypeError("Changed error")\n')
        with self.assertRaisesRegex(ValueError,'Condition controls failed'):self.freeze()
        self.assertFalse((self.root/'freeze/frozen.json').exists())

    def test_missing_alias_control_evidence_refuses_resume(self):
        study=self.freeze();frozen=load(study);frozen['validation']['alias_validation']['controls'].pop()
        frozen['study_sha256']=digest({k:v for k,v in frozen.items() if k!='study_sha256'})
        self.write_json(study,frozen)
        with self.assertRaisesRegex(ValueError,'Missing per-alias'):open_conditions(study)
