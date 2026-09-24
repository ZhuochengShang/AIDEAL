"""Offline gate regressions: tiny files and mocked processes, no provider/library."""
import json
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

for script_dir in (Path(__file__).resolve().parent, Path(__file__).resolve().parents[1]/'scripts'):
    if (script_dir/'main_pipeline.py').is_file():
        sys.path.insert(0,str(script_dir))

from pipeline_gates import (bind, write_once, refresh_manifest, inspect_bundle, hint_delivery,
                            require_review, require_alias_probes)
from main_pipeline import Pipeline
from workflow.readme_spans import inspect_sections
from workflow.condition_context import public_context


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def put(self,name,value):
        return write_once(self.root/name,value)

    def bundle(self):
        text=self.root/'alias.scala';text.write_text('object Nice { def safeCall(x: Int): Int = x }\n')
        interface=self.root/'ALIASES.md';interface.write_text('Nice.safeCall(x: Int): Int\n')
        readme=self.root/'README.md';readme.write_text('Public documentation\n')
        hints=self.put('hints.json',{'hints':[]})
        p=self.put('proposal.json',{'artifacts':{'alias_0001':{**bind(text),'target':'src/Nice.scala'},
                 'alias_interface':bind(interface),'readme':bind(readme),'error_hints':bind(hints)},
                 'aliases':[{'name':'safeCall','target_function':'file.scala:1:call','rationale':'test'}]})
        return p,{'pkg.Target.call':'file.scala:1:call'}

    def test_exact_new_spans_and_unselected_definitions(self):
        data=b'Intro\n'+b''.join(('## API Test: `Owner.m%d [class]`\n\n' % i).encode()+('Longer é body\n'*i).encode() for i in range(4))
        full={'mode':'full','entries':[{'id':str(i),'heading':'Owner.m%d [class]'%i,'span':{'start_byte':0,'end_byte':1},'definitions':[{'line':i+1}]} for i in range(4)],'selected_ids':list('0123')}
        result=refresh_manifest(full,data,list('0123'),inspect_sections)
        self.assertEqual(result['mode'],'refresh');self.assertEqual(result['entries'][3]['span']['end_byte'],len(data))
        self.assertEqual(full['entries'][3]['span']['end_byte'],1)
        self.assertEqual(result['entries'][3]['definitions'],[{'line':4}])

    def test_refresh_scope_drift_rejected(self):
        with self.assertRaises(ValueError):refresh_manifest({'entries':[]},b'## API Test: `extra`\n',[],inspect_sections)

    def test_write_once_cannot_replace_record(self):
        p=self.put('receipt.json',{'status':'a'})
        with self.assertRaises(ValueError):write_once(p,{'status':'b'})
        self.assertEqual(json.loads(p.read_text())['status'],'a')

    def test_alias_structural_check_does_not_claim_behavior(self):
        p,mapping=self.bundle();r=inspect_bundle(p,mapping)
        self.assertTrue(r['interface_full_fit']);self.assertFalse(r['behavior_validated'])
        self.assertEqual(r['aliases'][0]['api'],'pkg.Target.call')

    def test_full_alias_interface_over_cap_rejected(self):
        p,mapping=self.bundle()
        with self.assertRaisesRegex(ValueError,'fit'):inspect_bundle(p,mapping,cap=2)

    def test_unmapped_alias_rejected(self):
        p,_=self.bundle()
        with self.assertRaisesRegex(ValueError,'unknown'):inspect_bundle(p,{'Other.call':'other.scala:2:call'})

    def test_tampered_alias_rejected(self):
        p,mapping=self.bundle();(self.root/'alias.scala').write_text('changed')
        with self.assertRaisesRegex(ValueError,'Changed'):inspect_bundle(p,mapping)

    def test_install_review_bound_to_actual_manifest(self):
        manifest=self.put('manifest.json',{'x':1})
        review=self.put('review.json',{'status':'approved_for_installation','artifact_manifest':bind(manifest),
                                     'reviewer':'root review','held_out_bank_used_for_development':False})
        require_review(review,manifest)
        manifest.write_text('{"x":2}')
        with self.assertRaises(ValueError):require_review(review,manifest)

    def test_automatic_source_review_requires_actual_passing_certificates(self):
        proposal,mapping=self.bundle();manifest=self.put('manifest.json',inspect_bundle(proposal,mapping))
        original=self.root/'original.scala';original.write_text('pinned source')
        source=bind(self.root/'alias.scala');certificate={'status':'supported_thin_forwarding_syntax',
            'source':source,'canonical_source':bind(original)}
        source_check=self.put('sourcecheck.json',{'status':'verified_forwarding_source','proposal':bind(proposal),
            'certificates':[certificate],'behavior_validated':False,'hint_correctness_validated':False})
        bundle=self.put('bundle.json',{'source_proposals':[bind(proposal)]})
        review=self.put('review.json',{'status':'validated_proposal_sources','proposal_bindings':[bind(proposal)],
            'source_checks':[bind(source_check)],'held_out_bank_used_for_development':False})
        result=require_review(review,manifest,bundle)
        self.assertEqual(result['final_artifact_manifest'],bind(manifest))
        value=json.loads(source_check.read_text());value['status']='not_checked';source_check.write_text(json.dumps(value))
        value=json.loads(review.read_text());value['source_checks']=[bind(source_check)];review.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'passing'):require_review(review,manifest,bundle)

    def test_actual_context_hint_positive_and_three_negative_routes(self):
        mapping={'pkg.Target.call'+str(i):'File.scala:%d:call'%i for i in range(4)}
        diagnostics=[];hints=[]
        for i,(api,function) in enumerate(mapping.items()):
            error='Compiler error distinctive'+str(i)
            diagnostics.append({'split':'development','function':function,'code':'invalid','error':error})
            hints.append({'function_id':function,'error_contains':error,'likely_cause':'Cause','fix_steps':['Step'],
                          'suggested_fix_code':'snippet','validation':'Check locally'})
        h=self.put('hintbundle.json',{'hints':hints});d=self.root/'diagnostics.jsonl'
        d.write_text(''.join(json.dumps(x)+'\n' for x in diagnostics))
        doc=self.root/'original.md';doc.write_text('Original public docs')
        result=hint_delivery({'artifacts':{'error_hints':bind(h)}},d,mapping,[str(doc)],
            {'policy':'qualified_sections','api_headings':{api:api+' [class]' for api in mapping}},public_context)
        self.assertEqual(result['positive_coverage'],4)
        self.assertTrue(all(r['negative_checks_pass'] for r in result['rows']))
        self.assertFalse(result['audience_error_coverage_proven'])

    def probe_fixture(self):
        p,mapping=self.bundle();check=inspect_bundle(p,mapping);backends={};receipts={};rows=[]
        plan=self.put('plan.json',{'development_only':True});event='pkg.Target$.call(I)I'
        for arm in ['alias_only','combined']:
            overlay=self.root/(arm+'.jar');overlay.write_bytes(b'fake test overlay')
            build=self.put(arm+'build.json',{'alias_classes':['Nice$'],'sha256':arm+'build','overlay':bind(overlay)})
            runtime=self.put(arm+'runtime.json',{'build_identity':bind(build)})
            backends[arm]={'runtime':str(runtime),'build_sha256':arm+'build'}
            receipt={'sha256':arm+'-hash'};receipts[arm]=receipt
            program=self.root/(arm+'.scala');program.write_text('synthetic offline fixture')
            cert=self.put(arm+'certificate.json',{'syntax_checked':True})
            policy=self.root/(arm+'.tsv');policy.write_text('synthetic')
            req=self.put(arm+'request.json',{'protocol':'independent_development_alias_probe_v1',
                'backend':receipt,'target_apis':['pkg.Target.call'],'program':bind(program),
                'certificate':bind(cert),'trace_policy':bind(policy),'plan':bind(plan)})
            runs={};evidence=[]
            for mode in ['canonical','alias']:
                directory=self.root/arm/mode;directory.mkdir(parents=True)
                proc=write_once(directory/'process.json',{'returncode':0})
                stdout=directory/'stdout.txt';stdout.write_text('AIDEAL_DEVELOPMENT_PROBE='+json.dumps({'mode':mode,'observations':['value:7']})+'\n')
                stderr=directory/'stderr.txt';stderr.write_text('')
                trace=directory/'trace.txt';trace.write_text(event+'\n'+('Nice$.safeCall(I)I\n' if mode=='alias' else ''))
                log=directory/'classload.log';log.write_text('[0.1][info][class,load] pkg.Target$ source: '+overlay.as_uri()+'\n[0.1][info][class,load] Nice$ source: '+overlay.as_uri()+'\n')
                runs[mode+'_run']={k:bind(x) for k,x in [('process',proc),('stdout',stdout),('stderr',stderr),('trace',trace),('classload',log)]}
                evidence.extend(runs[mode+'_run'].values())
            comparison=self.put(arm+'comparison.json',{**runs,'canonical_observations':['value:7'],'alias_observations':['value:7'],'observations_equal':True})
            process=self.put(arm+'process.json',{'status':'ok','payload':{'backend_sha256':receipt['sha256'],
                'build_sha256':arm+'build','execution_pass':True,'paired_observations_pass':True,
                'canonical_target_reached':True,'alias_target_reached':True,
                'observed_alias_events':['Nice$.safeCall(I)I'],'adjudication_artifacts':evidence}})
            rows.append({'arm':arm,'api':'pkg.Target.call','alias_name':'safeCall','alias_event':'Nice$.safeCall(I)I',
                         'canonical_event':event,'request':bind(req),'process':bind(process),'comparison':bind(comparison)})
        b=self.put('backends.json',backends);r=self.put('backend_receipts.json',receipts)
        receipt=self.put('probes.json',{'status':'verified_alias_behavior','proposal':check['proposal'],'backends':bind(b),
            'backend_receipts':bind(r),'plan':bind(plan),'held_out_bank_used_for_development':False,'probes':rows})
        return receipt,check,b,receipts,{'pkg.Target.call':event}

    def test_alias_gate_checks_both_arms_and_actual_events(self):
        result=require_alias_probes(*self.probe_fixture())
        self.assertEqual(result['probe_count'],2)

    def test_alias_gate_rejects_missing_arm(self):
        args=self.probe_fixture();p=args[0];v=json.loads(p.read_text());v['probes'].pop();p.write_text(json.dumps(v))
        with self.assertRaisesRegex(ValueError,'every'):require_alias_probes(*args)

    def test_alias_gate_rejects_changed_raw_trace(self):
        args=self.probe_fixture();(self.root/'alias_only/alias/trace.txt').write_text('different')
        with self.assertRaisesRegex(ValueError,'Changed'):require_alias_probes(*args)

    def test_alias_gate_rejects_claim_without_observed_alias(self):
        args=self.probe_fixture();p=args[0];v=json.loads(p.read_text());row=v['probes'][0];process=Path(row['process']['path'])
        payload=json.loads(process.read_text());payload['payload']['observed_alias_events']=[];process.write_text(json.dumps(payload))
        row['process']=bind(process);p.write_text(json.dumps(v))
        with self.assertRaisesRegex(ValueError,'Actual alias'):require_alias_probes(*args)

    def test_alias_target_coverage_can_be_a_strict_subset(self):
        p,mapping=self.bundle();mapping['pkg.Other.call']='Elsewhere.scala:2:call'
        result=inspect_bundle(p,mapping)
        self.assertEqual(result['untreated_targets'],['pkg.Other.call'])
        self.assertEqual(result['alias_target_coverage'],['pkg.Target.call'])

    def test_incomplete_report_never_creates_stage_completion(self):
        pipeline=Pipeline.__new__(Pipeline);pipeline.root=self.root;pipeline.engine=self.root
        report=self.put('report.json',{'all_complete':False})
        with patch('main_pipeline.subprocess.run',return_value=SimpleNamespace(returncode=0)), patch.object(pipeline,'telemetry',return_value=[]):
            with self.assertRaisesRegex(ValueError,'unresolved'):pipeline.command('audience',['offline-mock'],[report])
        self.assertFalse((self.root/'stages/audience/complete.json').exists())
        self.assertTrue((self.root/'stages/audience/attempt-001/process.json').exists())


if __name__=='__main__':unittest.main()
