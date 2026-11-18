"""Read compact Generated R0 summaries and live process metadata; no writes on lab."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

STUDY = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
OPERATOR = STUDY / 'operator/ablation/2026-11-18'


def load(path):
    return json.loads(path.read_text()) if path.exists() else {}


def binding(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def scalars(value):
    return {k: v for k, v in value.items() if v is None or isinstance(v, (str, int, float, bool))}


def main():
    plan, controller = load(OPERATOR / 'QUEUE.json'), load(OPERATOR / 'STATE.json')
    rows = []
    for job in plan['jobs']:
        out = Path(job['output'])
        checkpoint = out / 'execution/comprehension_progress.jsonl'
        state = load(Path(plan['root']) / 'supervisor' / job['id'] / 'state.json')
        launch = load(out / 'GENERATED_LAUNCH.json')
        completion, result = load(out / 'completion.json'), load(out / 'result.json')
        latest, partial = {}, 0
        if checkpoint.exists():
            for line in checkpoint.read_text().splitlines():
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    partial += 1
                    continue
                if value.get('name'): latest[value['name']] = value
        metrics = result.get('metrics', latest) if completion else latest
        counts = Counter(v.get('status', 'unknown') for v in metrics.values())
        categories = Counter(v.get('error_category', 'unclassified') for v in metrics.values() if v.get('status') != 'pass')
        by_model = defaultdict(lambda: {'calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'missing_usage_calls': 0})
        usage = {'input_tokens': 0, 'output_tokens': 0, 'llm_calls': 0, 'metric_rows_without_usage': 0}
        for metric in metrics.values():
            for key in ['input_tokens', 'output_tokens', 'llm_calls']:
                usage[key] += metric.get(key) or 0
            usage['metric_rows_without_usage'] += not all(isinstance(metric.get(k), (int, float)) for k in ['input_tokens', 'output_tokens'])
            for model, values in metric.get('by_model', {}).items():
                for key in by_model[model]: by_model[model][key] += values.get(key) or 0
        blocked = sum(v.get('error_category') == 'llm-error' or str(v.get('error_category', '')).startswith('provider-') for v in metrics.values())
        artifacts = {name: binding(out / name) for name in ['completion.json', 'result.json', 'REPORT.md', 'GENERATED_LAUNCH.json'] if (out / name).is_file()}
        result_matches_completion = None
        if completion and isinstance(completion.get('result'), dict):
            result_matches_completion = artifacts['result.json']['sha256'] == completion['result']['sha256']
        row = {'bank': job['library'], 'status': state.get('status', 'pending'),
               'selected': launch.get('selected'), 'recorded': len(metrics), 'statuses': dict(counts),
               'provider_blocked': blocked, 'partial_checkpoint_lines': partial,
               'usage_scope': 'completed result metrics' if completion else 'latest recorded checkpoint rows; in-flight calls excluded',
               'usage': usage, 'actual_models': dict(by_model), 'error_categories': dict(categories),
               'output': str(out), 'completion': completion, 'state': state,
               'result_summary': {**scalars(result), 'run': scalars(result.get('run', {}))} if result else None,
               'result_matches_completion': result_matches_completion, 'artifacts': artifacts}
        report = out / 'REPORT.md'
        if completion and report.exists():
            text = report.read_text()
            row['report_text'] = text if len(text) <= 30000 else '\n'.join(text.splitlines()[:60])
            row['report_copy_complete'] = len(text) <= 30000
        rows.append(row)
    processes = []
    hz = os.sysconf('SC_CLK_TCK')
    boot = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try:
            args = [v.decode(errors='replace') for v in (proc / 'cmdline').read_bytes().split(b'\0') if v]
            names = [Path(v).name for v in args]
            if not any(name in {'generated_readme_r0.py', 'start_generated.py'} for name in names): continue
            stat = (proc / 'stat').read_text().split()
            processes.append({'pid': int(proc.name), 'state': stat[2],
                              'scripts': [x for x in names if x in {'generated_readme_r0.py', 'start_generated.py'}],
                              'spec_basenames': [Path(a).name for a in args if a.endswith('.json')],
                              'started_at': datetime.fromtimestamp(boot + int(stat[21]) / hz, timezone.utc).isoformat()})
        except (PermissionError, FileNotFoundError, ProcessLookupError): pass
    print(json.dumps({'observed_at': datetime.now(timezone.utc).isoformat(),
                      'condition': 'generated_readme', 'repair_rounds': 0,
                      'controller': controller, 'controller_pid_live': any(p['pid'] == controller.get('pid') and p['state'] != 'Z' for p in processes),
                      'processes': processes, 'banks': rows,
                      'note': 'Read-only snapshot. No active calls are included in partial token totals; no jobs or frozen inputs changed.'}, indent=2))


if __name__ == '__main__':
    main()
