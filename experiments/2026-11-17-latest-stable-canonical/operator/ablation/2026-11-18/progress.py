#!/usr/bin/env python3
"""Read this continuation's recorded progress without contacting a model."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def collect(directory):
    plan = read(directory / 'QUEUE.json')
    root = Path(plan['root'])
    controller = read(directory / 'STATE.json')
    summary = read(root / 'supervisor/summary.json')
    rows = []
    for job in plan['jobs']:
        output = Path(job['output'])
        launch = read(output / 'GENERATED_LAUNCH.json')
        state = read(root / 'supervisor' / job['id'] / 'state.json')
        seen, partial = {}, 0
        checkpoint = output / 'execution/comprehension_progress.jsonl'
        if checkpoint.exists():
            for line in checkpoint.read_text().splitlines():
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    partial += 1
                    continue
                if value.get('name'):
                    seen[value['name']] = value
        blocked = [v for v in seen.values() if v.get('error_category') == 'llm-error'
                   or str(v.get('error_category', '')).startswith('provider-')]
        done = [v for v in seen.values() if v not in blocked]
        rows.append({'job': job['id'], 'library': job['library'],
                     'status': state.get('status', summary.get('jobs', {}).get(job['id'], {}).get('status', 'prepared')),
                     'selected': launch.get('selected'), 'completed': len(done),
                     'passes': sum(v.get('status') == 'pass' for v in done),
                     'failures': sum(v.get('status') == 'fail' for v in done),
                     'provider_blocked': len(blocked), 'partial_checkpoint_lines': partial,
                     'output': str(output), 'completion_receipt': (output / 'completion.json').is_file()})
    return {'observed_at': datetime.now(timezone.utc).isoformat(),
            'condition': 'generated_readme', 'repair_rounds': 0, 'model': 'gemini-3.1-flash-lite',
            'controller': controller, 'jobs': rows,
            'note': 'Running and prepared jobs are not completed results. Later treatment conditions require validation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = collect(Path(__file__).resolve().parent)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result['observed_at'])
        print(f"{'Bank':18} {'Status':12} {'Done / selected':18} {'Pass':6} {'Fail':6} {'Provider blocked':16}")
        for row in result['jobs']:
            completed = str(row['completed']) + ' / ' + str(row['selected'])
            print(f"{row['library']:18} {row['status']:12} {completed:18} {row['passes']:<6} {row['failures']:<6} {row['provider_blocked']:<16}")
        print(result['note'])
