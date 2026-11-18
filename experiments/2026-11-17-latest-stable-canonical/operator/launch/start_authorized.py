#!/usr/bin/env python3
"""Start the authorized queue after immutable-input and provider checks.

A key is read only from the explicit --key-file argument. It is never logged or
copied into a plan. The existing supervisor owns the actual two-worker queue.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,subprocess,sys,time

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
 path=Path(path);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def require(condition, message):
 if not condition:raise ValueError(message)

def verified_inputs(root):
 plan=json.loads((root/'QUEUE.json').read_text());auth=json.loads((root/'USER_AUTHORIZATION.json').read_text());checks=json.loads((root/'PRELAUNCH_CHECKS.json').read_text())
 require(auth['authorized'] is True and checks['status']=='PASS','User authorization or prelaunch checks are missing')
 require(sha(root/'QUEUE.json')==auth['plan_sha256']==checks['plan_sha256'],'Authorized queue bytes changed')
 study=root.parents[1];review=study/'review_snapshot';manifest=json.loads((review/'SYNC_MANIFEST.json').read_text())
 # Verify the actual file map, not just a copied bundle label. Keep these checks
 # active even if an operator starts Python with optimization enabled.
 bundle=hashlib.sha256(json.dumps(manifest['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 require(bundle==manifest['bundle_sha256']==auth['base_review_bundle_sha256']==checks['base_bundle_sha256'],'Review bundle identity changed')
 require(all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in manifest['files']),'Unsafe review manifest path')
 require(all((review/p).is_file() and sha(review/p)==h for p,h in manifest['files'].items()),'Frozen review files changed')
 release=Path(plan['release']);binding=json.loads((review/'EVALUATOR_RELEASE.json').read_text())
 require(release.name==binding['release'] and binding['content_sha256']==checks['release_sha256'],'Evaluator release identity changed')
 require(all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in binding['files']),'Unsafe release manifest path')
 require(all((release/p).is_file() and sha(release/p)==h for p,h in binding['files'].items()),'Frozen evaluator files changed')
 require(Path(plan['root']).resolve().is_relative_to(study.resolve()) and Path(plan['root']).resolve()!=study.resolve(),'Queue outputs must stay within this study')
 for lib in checks['source_bindings']:
  source=study/'sources'/lib['library']
  def git(*args):return subprocess.check_output(['git','-C',str(source),*args],stderr=subprocess.PIPE,text=True).strip()
  require(git('rev-parse','HEAD')==lib['commit'] and git('rev-parse','HEAD^{tree}')==lib['tree'],'Pinned source identity changed: '+lib['library'])
  require(not git('status','--porcelain','--untracked-files=no'),'Pinned source has tracked edits: '+lib['library'])
 return plan,release,study

def provider_check(root,model,key):
 from aideal.config import ModelSpec
 from aideal.llm import invoke_text,reset_usage,usage_snapshot
 parent=root/'provider_checks';parent.mkdir(exist_ok=True);path=parent/f'check_{time.time_ns()}';path.mkdir()
 request={'purpose':'provider access check, not a benchmark','provider':'google','model':model,'max_output_tokens':8192,'system':'Return the requested readiness marker only.','user':'Reply exactly AIDEAL_READY.'}
 save(path/'request.json',request);t=time.monotonic();reset_usage();result={'status':'started','started_at':stamp()};save(path/'result.json',result)
 try:
  text=invoke_text(ModelSpec(provider='google',model=model,max_output_tokens=8192),request['system'],request['user'])
  safe_text=text.replace(key,'[REDACTED]') if key else text
  (path/'response.txt').write_text(safe_text)
  if safe_text!=text:result['response_redacted']=True
  if text.strip()!='AIDEAL_READY':raise ValueError('Provider did not return the requested readiness marker')
  result.update(status='PASS',response_sha256=sha(path/'response.txt'))
 except BaseException as exc:
  result.update(status='FAIL',error_type=type(exc).__name__,error=str(exc).replace(key,'[REDACTED]'))
 finally:
  result.update(finished_at=stamp(),seconds=round(time.monotonic()-t,3),usage=usage_snapshot());save(path/'result.json',result)
 return path,result

def worker(root,key_file):
 env=json.loads((root/'RUNTIME_ENV.json').read_text());os.environ.update(env)
 with (root/'launch.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  state={'status':'CHECKING','pid':os.getpid(),'started_at':stamp(),'plan_sha256':sha(root/'QUEUE.json')};save(root/'LAUNCH_STATE.json',state)
  key=''
  try:
   plan,release,study=verified_inputs(root)
   # Stop before reading a credential if a queue already owns these outputs.
   supervisor=Path(plan['root'])/'supervisor';supervisor.mkdir(exist_ok=True)
   with (supervisor/'queue.lock').open('a') as queue_lock:
    fcntl.flock(queue_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   key=Path(key_file).read_text().strip()
   if not key or '\n' in key or '\r' in key:raise ValueError('Credential file must contain one nonempty key')
   os.environ.pop('GEMINI_API_KEY',None);os.environ['GOOGLE_API_KEY']=key
   sys.path[:0]=[str(release),str(release/'vendor/aideal_engine/src')]
   model=plan['jobs'][0]['command'][plan['jobs'][0]['command'].index('--model')+1]
   probe,result=provider_check(root,model,key);state['provider_check']=str(probe)
   if result['status']!='PASS':
    state.update(status='PROVIDER_BLOCKED',finished_at=stamp());save(root/'LAUNCH_STATE.json',state);return 2
   # Current user authorization supersedes review-only holds for this study.
   # Preserve their original bytes as history. Do not release any parent hold.
   holds=[]
   for directory in [study,Path(plan['root'])]:
    hold=directory/'REVIEW_HOLD.json'
    if hold.exists():
     archived=root/('study-' if directory==study else 'qualified-')/'REVIEW_HOLD.released.json'
     if archived.exists():raise ValueError('Hold release receipt already exists; inspect before resuming')
     holds.append((hold,archived))
   released=[]
   try:
    for hold,archived in holds:
     archived.parent.mkdir(exist_ok=True);hold.rename(archived);released.append((hold,archived))
   except BaseException:
    for hold,archived in reversed(released):archived.rename(hold)
    raise
   spec=importlib.util.spec_from_file_location('aideal_frozen_queue',release/'scripts/run_cluster_experiment.py');queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)
   state.update(status='RUNNING',queue_started_at=stamp(),workers=2,release=str(release));save(root/'LAUNCH_STATE.json',state)
   result=queue.supervise(plan,key_file,workers=2)
   state.update(status='COMPLETE' if result['complete'] else 'STOPPED_WITH_INCOMPLETE_JOBS',finished_at=stamp(),jobs={k:v['status'] for k,v in result['jobs'].items()});save(root/'LAUNCH_STATE.json',state)
   return 0 if result['complete'] else 2
  except BaseException as exc:
   state.update(status='BLOCKED',finished_at=stamp(),error_type=type(exc).__name__,error=str(exc).replace(key,'[REDACTED]') if key else str(exc));save(root/'LAUNCH_STATE.json',state);return 2

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--key-file',type=Path,required=True);parser.add_argument('--worker',action='store_true');args=parser.parse_args();root=Path(__file__).resolve().parent
 if args.worker:return worker(root,args.key_file)
 # Validate first; background stdout contains only controlled messages/tracebacks.
 verified_inputs(root)
 with (root/'launcher_console.log').open('a') as log:
  child=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker','--key-file',str(args.key_file.resolve())],cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 save(root/'LAUNCH_PROCESS.json',{'pid':child.pid,'started_at':stamp(),'log':str(root/'launcher_console.log'),'state':str(root/'LAUNCH_STATE.json')});print(json.dumps({'pid':child.pid,'state':str(root/'LAUNCH_STATE.json')}));return 0
if __name__=='__main__':raise SystemExit(main())
