from pathlib import Path
import datetime,fcntl,json,os,subprocess
root=Path(__file__).resolve().parent
plan=json.loads((root/'PLAN.json').read_text())
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(data):
 temp=root/'STATE.tmp';temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(root/'STATE.json')
with (root/'launch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 previous=[int(p.name[8:]) for p in root.glob('attempt_*') if p.is_dir() and p.name[8:].isdigit()]
 attempt=root/f'attempt_{max(previous,default=0)+1:04d}';attempt.mkdir()
 state={'status':'running','pid':os.getpid(),'started_at':stamp(),'new_model_calls':0,'selected':plan['selected'],'attempt':attempt.name,'console':str(attempt/'console.log')}
 save(state)
 env=dict(os.environ)
 for key in list(env):
  if key.endswith(('_API_KEY','_API_TOKEN','_ACCESS_TOKEN','_SECRET_ACCESS_KEY')):env.pop(key)
 env['PYTHONDONTWRITEBYTECODE']='1'
 try:
  with (attempt/'console.log').open('w') as output:
   result=subprocess.run(plan['command'],cwd=plan['cwd'],env=env,stdout=output,stderr=subprocess.STDOUT)
  state.update(status='complete' if result.returncode==0 and (Path(plan['output'])/'completion.json').exists() else 'failed',exit_code=result.returncode,finished_at=stamp())
 except BaseException as error:state.update(status='failed',error=type(error).__name__+': '+str(error),finished_at=stamp())
 save(state)
