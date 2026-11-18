#!/usr/bin/env python3
"""Combine original and corrected-bank status without modifying either run."""
from pathlib import Path
import argparse,datetime,importlib.util,json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
    checks=json.loads((root/'RECOVERY_CHECKS.json').read_text());old=Path(checks['original_launch']);spec=importlib.util.spec_from_file_location('recorded_progress',old/'progress.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    data=mod.collect(old);replacement=mod.collect(root);state=mod.read(root/'STATE.json');data['recovery']=state;replaced={r['job']:r for r in replacement['jobs']}
    for i,previous in enumerate(data['jobs']):
        if previous['job'] not in replaced:continue
        new=replaced[previous['job']];new['selected']=checks['selected'].get(previous['job'].removesuffix('-r0').removesuffix('-readme'),previous['selected']);new['previous_status']=previous['status'];new['previous_output']=previous['output'];new['evaluator']=json.loads((root/'EVALUATOR_RELEASE.json').read_text())['release']
        if new['status']=='prepared_not_started':new['status']='waiting_for_original_queue' if state.get('status')=='WAITING_FOR_ORIGINAL_QUEUE' else state.get('status','prepared_not_started').lower()
        data['jobs'][i]=new
    data['observed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();data['note']+=' RDPro uses the Raptor/raster-only bank with verified forwarding consolidation and reviewed original-document mappings. Full-Beast jobs are superseded; previous results remain recorded.'
    if a.json:print(json.dumps(data,indent=2));return
    print(data['observed_at']);print('Corrected queue: '+state.get('status','not_started'));print(f"{'Job':26} {'State':28} {'Done / targets':18} {'Pass':6} {'Fail':6}")
    for r in data['jobs']:print(f"{r['job']:26} {r['status']:28} {str(r['completed'])+' / '+str(r['selected']):18} {str(r['passes']):6} {str(r['failures']):6}")
    print(data['note'])
if __name__=='__main__':main()
