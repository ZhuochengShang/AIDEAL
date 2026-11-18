#!/usr/bin/env python3
"""Read only this launch's job states and per-API checkpoints; never call a model."""
from pathlib import Path
import argparse,datetime,json

def read(path):
 try:return json.loads(Path(path).read_text())
 except FileNotFoundError:return {}

def collect(directory):
 plan=read(directory/'QUEUE.json');root=Path(plan['root']);supervisor=read(root/'supervisor/summary.json');rows=[]
 counts={r['bank']:r['selected'] for r in read(directory/'PRELAUNCH_CHECKS.json').get('selection',[])}
 for job in plan['jobs']:
  target=Path(job['output'])/job['library'];state=supervisor.get('jobs',{}).get(job['id'],{});row={'job':job['id'],'status':state.get('status','prepared_not_started'),'selected':counts.get(job['library']),'output':str(target),'completed':0,'passes':None,'failures':None}
  if job['stage']=='r0':
   path=target/'execution/comprehension_progress.jsonl';seen={};partial=0
   if path.exists():
    for line in path.read_text().splitlines():
     try:r=json.loads(line)
     except json.JSONDecodeError:partial+=1;continue
     if r.get('name'):seen[r['name']]=r
   provider=[r for r in seen.values() if r.get('error_category')=='llm-error' or str(r.get('error_category','')).startswith('provider-')]
   done=[r for r in seen.values() if r not in provider];row.update(completed=len(done),passes=sum(r.get('status')=='pass' for r in done),failures=sum(r.get('status')=='fail' for r in done),provider_blocked_targets=len(provider),unfinished_checkpoint_lines=partial)
  else:
   saved=read(target/'.aideal_exec/readme_generation_state.json');row.update(completed=saved.get('completed_count',0),generation_complete=saved.get('complete',False),completion_receipt_exists=(target/'completion.json').is_file())
  rows.append(row)
 return {'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'launch':read(directory/'LAUNCH_STATE.json'),'jobs':rows,'note':'Prepared and running jobs are not completed results. R0 failures are separate from provider-blocked targets. README completion is not execution validation.'}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--json',action='store_true');parser.add_argument('--output-json',type=Path);args=parser.parse_args();d=collect(Path(__file__).resolve().parent)
 if args.output_json:args.output_json.write_text(json.dumps(d,indent=2)+'\n')
 if args.json:print(json.dumps(d,indent=2));return
 print(d['observed_at']);print(f"{'Job':26} {'State':24} {'Done / selected':18} {'Pass':6} {'Fail':6}")
 for r in d['jobs']:print(f"{r['job']:26} {r['status']:24} {str(r['completed'])+' / '+str(r['selected']):18} {str(r['passes']):6} {str(r['failures']):6}")
 print(d['note'])
if __name__=='__main__':main()
