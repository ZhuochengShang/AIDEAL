#!/usr/bin/env python3
"""Run the corrected JVM banks after the original two-worker queue releases its lock.

The original queue, completed measurements and failed evidence remain immutable.
This operator starts the existing supervisor in a separate output namespace.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,subprocess,sys

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value):
    p=Path(p); temporary=p.with_suffix('.tmp'); temporary.write_text(json.dumps(value,indent=2)+'\n'); temporary.replace(p)
def require(value,message):
    if not value: raise ValueError(message)
def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def verify(root):
    checks=json.loads((root/'RECOVERY_CHECKS.json').read_text()); plan=json.loads((root/'QUEUE.json').read_text())
    require(checks['status']=='PASS' and sha(root/'QUEUE.json')==checks['plan_sha256'],'Recovery checks or queue identity changed')
    release=Path(plan['release']); binding=json.loads((root/'EVALUATOR_RELEASE.json').read_text())
    require(release.name==binding['release'],'Recovery release differs from recorded release')
    require(all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in binding['files']),'Unsafe release manifest path')
    require(all((release/p).is_file() and sha(release/p)==h for p,h in binding['files'].items()),'Recovery evaluator bytes changed')
    content=hashlib.sha256(json.dumps(binding['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(checks['release_sha256']==binding['content_sha256']==content,'Recovery release identity changed')
    require(all(Path(p).is_file() and sha(p)==h for p,h in checks.get('scope_files',{}).items()),'Raptor scope or original-document inputs changed')
    old=Path(checks['original_launch']); previous=load_module(old/'start_authorized.py','original_authorized_operator')
    previous.verified_inputs(old)
    require({j['id'] for j in plan['jobs']}==set(checks['replaces_jobs']),'Recovery scope changed')
    require(Path(plan['root']).resolve()==root.parent.resolve(),'Recovery output ownership changed')
    return plan, release, old, checks

def worker(root,key_file,lock_fd=None):
    # Acquire ownership before writing any shared status. A duplicate launch
    # must not replace the running owner's progress with a failure receipt.
    own=os.fdopen(lock_fd,'a') if lock_fd is not None else (root/'worker.lock').open('a')
    with own:
        try:
            fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            return 2
        state={'status':'CHECKING','pid':os.getpid(),'started_at':stamp()};save(root/'STATE.json',state)
        try:
            plan,release,old,checks=verify(root)
            os.environ.update(json.loads((old/'RUNTIME_ENV.json').read_text()))
            original_plan=json.loads((old/'QUEUE.json').read_text())
            original_root=Path(original_plan['root'])
            with (original_root/'supervisor/queue.lock').open('a') as upstream:
                state.update(status='WAITING_FOR_ORIGINAL_QUEUE',plan_sha256=sha(root/'QUEUE.json'));save(root/'STATE.json',state)
                # Lock ownership, rather than a stale PID/status, proves the prior
                # supervisor and its inherited worker locks have all closed.
                fcntl.flock(upstream,fcntl.LOCK_EX)
                verify(root)
                terminal=json.loads((original_root/'supervisor/summary.json').read_text())
                expected={job['id'] for job in original_plan['jobs']}
                require(set(terminal['jobs'])==expected,'Original terminal job coverage is incomplete')
                require(all(j['status'] in ('complete','failed') for j in terminal['jobs'].values()),'Original queue ended with unfinished jobs; inspect before recovery')
                require(all(terminal['jobs'][name]['status']=='failed' for name in checks['replaces_jobs']),'A recovery bank already completed or lacks its failed receipt')
                save(root/'ORIGINAL_TERMINAL_STATE.json',terminal)
                sys.path[:0]=[str(release),str(release/'vendor/aideal_engine/src')]
                supervisor=load_module(release/'scripts/run_cluster_experiment.py','corrected_queue')
                state.update(status='RUNNING',queue_started_at=stamp(),workers=2);save(root/'STATE.json',state)
                result=supervisor.supervise(plan,key_file,workers=2)
                state.update(status='COMPLETE' if result['complete'] else 'STOPPED_WITH_INCOMPLETE_JOBS',finished_at=stamp(),jobs={k:v['status'] for k,v in result['jobs'].items()});save(root/'STATE.json',state)
                return 0 if result['complete'] else 2
        except BaseException as exc:
            # Do not copy exception strings that might contain provider credentials.
            state.update(status='BLOCKED',finished_at=stamp(),error_type=type(exc).__name__);save(root/'STATE.json',state);return 2

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--key-file',type=Path,required=True);p.add_argument('--worker',action='store_true');p.add_argument('--lock-fd',type=int,help=argparse.SUPPRESS);a=p.parse_args();root=Path(__file__).resolve().parent
    if a.worker:return worker(root,a.key_file,a.lock_fd)
    with (root/'worker.lock').open('a') as own:
        try:
            fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'status':'ALREADY_RUNNING','state':str(root/'STATE.json')}));return 2
        verify(root)
        with (root/'console.log').open('a') as log:
            # Pass the held lock into the child before publishing its PID. The
            # parent closes its descriptor only after the child has inherited it.
            child=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker','--lock-fd',str(own.fileno()),'--key-file',str(a.key_file.resolve())],cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(own.fileno(),),env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        save(root/'PROCESS.json',{'pid':child.pid,'started_at':stamp()});print(json.dumps({'pid':child.pid,'state':str(root/'STATE.json')}));return 0
if __name__=='__main__':raise SystemExit(main())
