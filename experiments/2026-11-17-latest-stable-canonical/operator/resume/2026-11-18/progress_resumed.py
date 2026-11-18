#!/usr/bin/env python3
"""Combine current banks with checkpoint and validation-only recovery status."""
from pathlib import Path
import argparse, importlib.util, json, subprocess, sys

STUDY = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    data = json.loads(subprocess.check_output([sys.executable, str(STUDY / 'qualified-raptor/launch/progress_all.py'), '--json']))
    def read(path):
        return json.loads(path.read_text()) if path.exists() else {}
    summary = read(STUDY / 'supervisor/summary.json')
    for row in data['jobs']:
        latest = summary.get('jobs', {}).get(row['job'])
        if latest:
            row['previous_controller_status'] = row['status']
            row['status'] = latest['status']
    recovery = STUDY / 'qualified-readme-source-note'
    if (recovery / 'QUEUE.json').exists():
        spec = importlib.util.spec_from_file_location('recorded_progress', STUDY / 'qualified/launch/progress.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        replacement = {row['job']: row for row in mod.collect(recovery)['jobs']}
        for i, row in enumerate(data['jobs']):
            if row['job'] in replacement:
                new = replacement[row['job']]
                new.update(selected=row['selected'], previous_output=row['output'], previous_completed=row['completed'])
                output = Path(new['output'])
                new['replayed_responses'] = len(list((output / 'author_replay').glob('*/replay_receipt.json')))
                new['validation_policy'] = 'source-note-todo-v3'
                data['jobs'][i] = new
    data['provider_resume'] = read(STUDY / 'operator/resume/2026-11-18/STATE.json')
    data['author_recovery'] = read(recovery / 'STATE.json')
    data['note'] += ' tslearn reuses its R0 checkpoint. MDAnalysis README recovery revalidates recorded responses in a separate namespace; replayed calls are not new token usage.'
    if args.json:
        print(json.dumps(data, indent=2))
        return
    print(data['observed_at'])
    print(f"{'Job':26} {'State':24} {'Done / selected':18} {'Pass':6} {'Fail':6}")
    for row in data['jobs']:
        print(f"{row['job']:26} {row['status']:24} {str(row['completed'])+' / '+str(row['selected']):18} {str(row['passes']):6} {str(row['failures']):6}")
    print(data['note'])

if __name__ == '__main__':
    main()
