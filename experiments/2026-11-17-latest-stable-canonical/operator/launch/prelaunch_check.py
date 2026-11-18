"""Verify and prepare the authorized queue without loading credentials or calling models."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess,sys,time
root=Path(__file__).resolve().parent;study=root.parents[1];review=study/'review_snapshot';plan=json.loads((root/'QUEUE.json').read_text());release=Path(plan['release']);approval=json.loads((root/'USER_AUTHORIZATION.json').read_text());env_settings=json.loads((root/'RUNTIME_ENV.json').read_text());os.environ.update(env_settings)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert approval['authorized'] and approval['plan_sha256']==sha(root/'QUEUE.json')
m=json.loads((review/'SYNC_MANIFEST.json').read_text());assert hashlib.sha256(json.dumps(m['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==m['bundle_sha256'];assert m['bundle_sha256']==approval['base_review_bundle_sha256'];assert all((review/r).is_file() and sha(review/r)==h for r,h in m['files'].items())
r=json.loads((review/'EVALUATOR_RELEASE.json').read_text());assert release.name==r['release'] and all((release/p).is_file() and sha(release/p)==h for p,h in r['files'].items())
lock=json.loads((review/'STUDY_LOCK.json').read_text());source_rows=[]
for lib in lock['libraries']:
 source=Path(lib['cluster_source'])
 def git(*args):return subprocess.check_output(['git','-C',str(source),*args],stderr=subprocess.PIPE,text=True).strip()
 assert git('rev-parse','HEAD')==lib['official_commit'];assert git('rev-parse','HEAD^{tree}')==lib['source_tree']
 assert not git('status','--porcelain','--untracked-files=no'),lib['library']
 source_rows.append({'library':lib['library'],'commit':lib['official_commit'],'tree':lib['source_tree'],'tracked_source_clean':True})
sys.path[:0]=[str(release),str(release/'vendor/aideal_engine/src')]
import yaml
from aideal import llm
# These guarded calls must never occur during preparation.
def forbidden(*args,**kwargs):raise RuntimeError('PREPARATION_MUST_NOT_CALL_A_MODEL')
llm.invoke_text=forbidden;llm.get_chat_model=forbidden
spec=importlib.util.spec_from_file_location('qualified_author_launcher',release/'scripts/run_readme_generation.py');author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
cat_path=Path(plan['jobs'][0]['command'][plan['jobs'][0]['command'].index('--catalog')+1]);catalog=yaml.safe_load(cat_path.read_text());selection=[]
for name,spec in catalog.items():
 cfg,manifest,_,_=author.inspect(spec,'manifest');_,surface,_,_=author.inspect(spec,'surface');assert set(manifest)==set(surface),name
 selection.append({'bank':name,'selected':len(manifest),'manifest_surface_equal':True,'names_sha256':hashlib.sha256('\n'.join(manifest).encode()).hexdigest()})
assert sum(x['selected'] for x in selection)==5307
checks=root/'checks';checks.mkdir(exist_ok=True);jobs=[];started=time.monotonic()
for job in plan['jobs']:
 cmd=list(job['command']);cmd[cmd.index('--run')]='--prepare';log=checks/(job['id']+'.prepare.log');t=time.monotonic()
 with log.open('w') as f:process=subprocess.run(cmd,cwd=release,env=dict(os.environ),stdout=f,stderr=subprocess.STDOUT)
 row={'job':job['id'],'exit_code':process.returncode,'seconds':round(time.monotonic()-t,3),'log':str(log),'prepared_output':job['output']};jobs.append(row)
 print(json.dumps(row),flush=True)
 if process.returncode:break
summary={'status':'PASS' if len(jobs)==14 and all(j['exit_code']==0 for j in jobs) else 'FAIL','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':round(time.monotonic()-started,3),'source_bindings':source_rows,'selection':selection,'jobs':jobs,'model_calls':0,'subject_executions':0,'credential_files_read':0,'review_hold_unchanged':(study/'qualified/REVIEW_HOLD.json').is_file(),'plan_sha256':sha(root/'QUEUE.json'),'release_sha256':r['content_sha256'],'base_bundle_sha256':m['bundle_sha256']}
(root/'PRELAUNCH_CHECKS.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['source_bindings','selection','jobs']}));raise SystemExit(summary['status']!='PASS')
