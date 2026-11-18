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
summary={'status':'PASS' if len(rows)==6 and all(r['exit_code']==0 for r in rows) else 'FAIL','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':sha(root/'QUEUE.json'),'release_sha256':binding['content_sha256'],'original_launch':str(old),'replaces_jobs':[j['id'] for j in plan['jobs']],'jobs':rows,'model_calls':0,'credential_files_read':0,'reason':'Java/Scala optional source-comment normalization; original attempts and input inventories are preserved.'}
(root/'RECOVERY_CHECKS.json').write_text(json.dumps(summary,indent=2)+'\n');raise SystemExit(summary['status']!='PASS')
