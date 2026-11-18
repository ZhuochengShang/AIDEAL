from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess,sys
root=Path(__file__).resolve().parent;plan=json.loads((root/'QUEUE.json').read_text());release=Path(plan['release']);study=root.parents[1];old=study/'qualified/launch';binding=json.loads((root/'EVALUATOR_RELEASE.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert all(sha(release/p)==h for p,h in binding['files'].items())
spec=importlib.util.spec_from_file_location('original_launch',old/'start_authorized.py');launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch);launch.verified_inputs(old)
os.environ.update(json.loads((old/'RUNTIME_ENV.json').read_text()));os.environ.pop('GOOGLE_API_KEY',None);os.environ.pop('GEMINI_API_KEY',None)
logs=root/'checks';logs.mkdir(exist_ok=True);rows=[]
for job in plan['jobs']:
 cmd=list(job['command']);cmd[cmd.index('--run')]='--prepare';p=logs/(job['id']+'.log')
 with p.open('w') as f:r=subprocess.run(cmd,cwd=release,stdout=f,stderr=subprocess.STDOUT)
 rows.append({'job':job['id'],'exit_code':r.returncode,'log':str(p)});print(json.dumps(rows[-1]),flush=True)
 if r.returncode:break
summary={'status':'PASS' if len(rows)==6 and all(r['exit_code']==0 for r in rows) else 'FAIL','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':sha(root/'QUEUE.json'),'release_sha256':binding['content_sha256'],'original_launch':str(old),'replaces_jobs':[j['id'] for j in plan['jobs']],'jobs':rows,'model_calls':0,'credential_files_read':0,'reason':'Strict Raptor scope and source-reviewed selection; class/type receiver guidance corrected; historical attempts and frozen inputs preserved.'}
scope_root=study/'review_snapshot/review/raptor-scope'
summary['scope_files']={str(p):sha(p) for prefix in ['plan','original-docs','strict-no-wrappers'] for p in sorted((scope_root/prefix).rglob('*')) if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts}
summary['scope_files'].update({str(root/name):sha(root/name) for name in ['start_after_queue.py','preflight.py','progress_all.py']})
# Launchers preserve either a bare API list or an identity manifest object.
summary['selected']={}
for job in plan['jobs']:
    if job['stage']!='r0':continue
    manifest=json.loads((Path(job['output'])/job['library']/'inputs/api_manifest.json').read_text())
    apis=manifest['apis'] if isinstance(manifest,dict) else manifest
    assert isinstance(apis,list) and apis and all(isinstance(api,str) and api for api in apis)
    summary['selected'][job['library']]=len(apis)
summary['study_total']=2520+sum(summary['selected'][name] for name in ('rdpro_java','rdpro_scala'))
(root/'RECOVERY_CHECKS.json').write_text(json.dumps(summary,indent=2)+'\n');raise SystemExit(summary['status']!='PASS')
