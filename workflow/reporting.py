"""Read-only score aggregation and report writing; never call a model or library."""
from itertools import combinations
from pathlib import Path

from .ablation import ARMS, file_hash, load, score
from .evaluation_setup import CONDITIONS, conditions_for
from .execution import atomic_json


def verify(root):
    """Check artifact identity and archived reporting independently of live jobs."""
    root = Path(root)
    manifest = load(root / "evidence/manifest.json")
    changed = [r["path"] for r in manifest["files"]
               if not (root / r["path"]).is_file() or file_hash(root / r["path"]) != r["sha256"]]
    arm = load(root / "configs/active_arm.json")
    flags = tuple(arm[k] for k in ("readme", "aliases", "error_hints"))
    if arm["arm"] not in ARMS or flags != ARMS[arm["arm"]]:
        changed.append("invalid active-arm treatment matrix")
    return {"verified": not changed, "bound_files": len(manifest["files"]), "changed": changed,
            "arm": arm["arm"], "new_ablation_results_available": False}


def report(frozen, rows):
    common = frozen['config']['common']
    conditions = conditions_for(frozen['config'])
    metrics = score(frozen['bank'], common['trial_ids'], rows,
                    study_sha256=frozen['study_sha256'], max_snippet_fixes=common['max_snippet_fixes'],
                    arms=conditions, baseline=conditions[0])
    pairs = []
    by_key = {(r['arm'], r['case_id'], r['trial_id']): r for r in rows}
    for baseline, treatment in combinations(conditions, 2):
        for kind in ('micro', 'puzzle'):
            paired = []
            for c in frozen['bank']['cases']:
                if c['kind'] != kind:
                    continue
                for trial in common['trial_ids']:
                    a, b = [by_key.get((arm, c['id'], trial), {}) for arm in (baseline, treatment)]
                    if a.get('status') in ('pass', 'fail') and b.get('status') in ('pass', 'fail'):
                        paired.append((a['status'], b['status']))
            recovered = sum(a == 'fail' and b == 'pass' for a, b in paired)
            regressed = sum(a == 'pass' and b == 'fail' for a, b in paired)
            n = metrics[baseline][kind]['selected']
            pairs.append({'baseline': baseline, 'treatment': treatment, 'kind': kind,
                          'paired_completed': len(paired), 'selected': n,
                          'recoveries': recovered, 'regressions': regressed,
                          'paired_delta_percentage_points': 100 * (recovered - regressed) / len(paired) if paired else None,
                          'final_lift_percentage_points': 100 * (recovered - regressed) / n if n and len(paired) == n else None})
    resources = {}
    for condition in conditions:
        values = [r.get('resources', {}) for r in rows if r['arm'] == condition]
        resources[condition] = {key: sum(v.get(key, 0) for v in values) for key in
                               ('provider_calls', 'provider_seconds', 'execution_seconds', 'reported_input_tokens', 'reported_output_tokens')}
        resources[condition]['calls_without_usage'] = sum(v.get('calls_without_usage', 0) for v in values)
    return {'study_sha256': frozen['study_sha256'], 'conditions': list(conditions),
            'metrics': metrics, 'paired_comparisons': pairs,
            'resources': resources, 'all_complete': all(metrics[a][k]['unresolved'] == 0 for a in conditions for k in ('micro', 'puzzle')),
            'scope': frozen['bank'].get('scope_note', ''), 'holdout_review': frozen['config']['holdout_review']}


def write_report(output, summary):
    atomic_json(output / 'report.json', summary)
    lines = ['# Three-README evaluation', '', summary['scope'], '',
             '| Condition | Task type | First correct | Correct within budget | Completed | Unresolved |',
             '|---|---|---|---|---|---|']
    # Reports written before explicit designs used only the legacy conditions.
    for condition in summary.get('conditions', CONDITIONS):
        for kind in ('micro', 'puzzle'):
            m = summary['metrics'][condition][kind]
            n = m['selected']
            initial = f"{m['first_attempt_correct']}/{n}"
            correct = f"{m['correct_within_budget']}/{n}"
            if n:
                initial += f" ({m['first_attempt_lower_bound_pct']:.1f}%)"
                correct += f" ({m['within_budget_lower_bound_pct']:.1f}%)"
            lines.append(f"| {condition} | {kind} | {initial} | {correct} | {m['completed']}/{n} | {m['unresolved']} |")
    lines += ['', 'Percentages retain all selected tasks. With unresolved cases, these are observed lower bounds, not final scores or confidence bounds.',
              '', '## Paired comparisons', '', '| Baseline → Treatment | Type | Recoveries | Regressions | Completed pairs | Final lift |',
              '|---|---|---|---|---|---|']
    for p in summary['paired_comparisons']:
        lift = p['final_lift_percentage_points']
        lift_text = f'{lift:+.1f} percentage points' if lift is not None else 'pending'
        lines.append(f"| {p['baseline']} → {p['treatment']} | {p['kind']} | {p['recoveries']} | {p['regressions']} | {p['paired_completed']}/{p['selected']} | {lift_text} |")
    lines += ['', '## Scope and independence', '', summary['holdout_review'], '',
              'Resource accounting and exact input identity: `report.json`. Full model requests, responses, compiler/runtime logs and oracle checks are under each condition folder.', '']
    (output / 'REPORT.md').write_text('\n'.join(lines))

