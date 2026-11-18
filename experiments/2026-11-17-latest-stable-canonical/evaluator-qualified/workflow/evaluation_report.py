"""Read-only reports for README and matched-condition evaluation.

Both public report contracts keep their original fields and formatting. They
share pairing/resource aggregation and use the unchanged score() calculation.
No function in this module calls a model or executes a library.
"""
from itertools import combinations
from pathlib import Path

from .ablation import ARMS, file_hash, load, score
from .evaluation_setup import CONDITIONS
from .execution import atomic_json
from .evaluation_program_generation import generation_counts


FORMULAS = {
    'selected': 'N_k = number of selected cases of kind k × number of trials, per condition',
    'first_attempt_lower_bound_pct': '100 × first-attempt correct / N_k',
    'within_budget_lower_bound_pct': '100 × correct within the common repair budget / N_k',
    'unresolved': 'N_k − (verified passes + verified failures)',
    'paired_delta_percentage_points': '100 × (fail→pass recoveries − pass→fail regressions) / completed matched pairs',
    'final_lift_percentage_points': '100 × (recoveries − regressions) / N_k, only when all N_k pairs complete',
}


def verify(root):
    """Check artifact identity and archived reporting independently of live jobs."""
    # Compare the archive’s bound file hashes with the current files
    # and return a list of mismatches together with the active-arm status.
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


def _paired_comparisons(frozen, rows, arms, metrics, count_fields=('paired_completed', 'selected')):
    """Compare matched completed units; count_fields preserves each JSON field order."""
    # Pair results from the same task and trial across two conditions.
    # Calculate changes only for pairs with a checked result on both sides.
    indexed = {(row['arm'], row['case_id'], row['trial_id']): row for row in rows}
    pairs = []
    for baseline, treatment in combinations(arms, 2):
        for kind in ('micro', 'puzzle'):
            matched = [(indexed.get((baseline, case['id'], trial), {}).get('status'),
                        indexed.get((treatment, case['id'], trial), {}).get('status'))
                       for case in frozen['bank']['cases'] if case['kind'] == kind
                       for trial in frozen['config']['common']['trial_ids']]
            # A missing or unresolved side does not count as a completed pair.
            done = [(a, b) for a, b in matched if a in ('pass', 'fail') and b in ('pass', 'fail')]
            recovered = sum(a == 'fail' and b == 'pass' for a, b in done)
            regressed = sum(a == 'pass' and b == 'fail' for a, b in done)
            n = metrics[baseline][kind]['selected']
            counts = {'paired_completed': len(done), 'selected': n}
            pair = {'baseline': baseline, 'treatment': treatment, 'kind': kind}
            pair.update((key, counts[key]) for key in count_fields)
            # Report the completed-pair delta now. Final lift requires every
            # selected pair to have a checked result.
            pair.update(recoveries=recovered, regressions=regressed,
                        paired_delta_percentage_points=100 * (recovered - regressed) / len(done) if done else None,
                        final_lift_percentage_points=100 * (recovered - regressed) / n if n and len(done) == n else None)
            pairs.append(pair)
    return pairs


def _resource_totals(rows, arms):
    # Sum the resource counters from the saved rows by condition.
    # A missing counter contributes zero to the sum.
    keys = ('provider_calls', 'provider_seconds', 'execution_seconds', 'reported_input_tokens',
            'reported_output_tokens', 'calls_without_usage')
    return {arm: {key: sum(row.get('resources', {}).get(key, 0) for row in rows if row['arm'] == arm)
                  for key in keys} for arm in arms}


def report(frozen, rows):
    # Score the three README arms against the frozen tasks and trials.
    # Return the metrics, paired results, generation outcomes, and resources.
    common = frozen['config']['common']
    metrics = score(frozen['bank'], common['trial_ids'], rows,
                    study_sha256=frozen['study_sha256'], max_snippet_fixes=common['max_snippet_fixes'],
                    arms=CONDITIONS, baseline=CONDITIONS[0])
    pairs = _paired_comparisons(frozen, rows, CONDITIONS, metrics)
    resources = _resource_totals(rows, CONDITIONS)
    return {'study_sha256': frozen['study_sha256'], 'metrics': metrics, 'paired_comparisons': pairs,
            'generation_classifications': generation_counts(rows, CONDITIONS), 'resources': resources, 'all_complete': all(metrics[a][k]['unresolved'] == 0 for a in CONDITIONS for k in ('micro', 'puzzle')),
            'scope': frozen['bank'].get('scope_note', ''), 'holdout_review': frozen['config']['holdout_review']}


def _generation_stop_lines(summary):
    # Turn each condition’s generation stop counts into the table lines
    # shared by both Markdown reports.
    lines = ['', '## Generation stops (unresolved)', '',
              '| Condition | Incomplete | Refusal | Empty | Provider failure |',
              '|---|---|---|---|---|']
    for arm, counts in summary['generation_classifications'].items():
        values = [counts['generation_' + name] for name in ('incomplete', 'refusal', 'empty', 'provider_failure')]
        lines.append('| ' + arm + ' | ' + ' | '.join(str(value) for value in values) + ' |')
    lines += ['', 'These stopped generations were not compiled or executed. They retain the fixed denominator and are not verified API failures.']
    return lines


def write_report(output, summary):
    # Save the full README summary as JSON and write a Markdown report
    # with scores, paired comparisons, and generation outcomes.
    atomic_json(output / 'report.json', summary)
    lines = ['# Three-README evaluation', '', summary['scope'], '',
             '| Condition | Task type | First correct | Correct within budget | Completed | Unresolved |',
             '|---|---|---|---|---|---|']
    for condition in CONDITIONS:
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
    lines += _generation_stop_lines(summary)
    (output / 'REPORT.md').write_text('\n'.join(lines))


def report_conditions(frozen, rows):
    # Input: the frozen study and one current result row per evaluated unit.
    # Check backend identity, call score, and add paired comparisons and resource
    # totals. Return a summary; write_condition_report writes its JSON/Markdown.
    # Use the original condition as the scoring baseline. Each supplied
    # row must identify the backend frozen for its condition.
    cfg = frozen['config']
    arms, common = tuple(cfg['conditions']), cfg['common']
    for row in rows:
        if row.get('backend_sha256') != frozen['backends'].get(row.get('arm'), {}).get('sha256'):
            raise ValueError('Result belongs to another condition backend')
    metrics = score(frozen['bank'], common['trial_ids'], rows,
                    study_sha256=frozen['study_sha256'], max_snippet_fixes=common['max_snippet_fixes'],
                    arms=arms, baseline='original')
    pairs = _paired_comparisons(frozen, rows, arms, metrics, ('selected', 'paired_completed'))
    resources = _resource_totals(rows, arms)
    return {'protocol': frozen['protocol'], 'study_sha256': frozen['study_sha256'],
            'design': cfg['design'], 'conditions': list(arms), 'metrics': metrics, 'paired_comparisons': pairs,
            'generation_classifications': generation_counts(rows, arms), 'resources': resources, 'formulas': FORMULAS, 'scope': frozen['bank'].get('scope_note', ''),
            'holdout_review': cfg['holdout_review'],
            'source_hint_coverage': {arm: index['coverage'] for arm, index in
                                     frozen.get('source_hint_indexes', {}).items()},
            'all_complete': all(m['unresolved'] == 0 for by_kind in metrics.values() for m in by_kind.values()),
            'limitations': ['Percentages with unresolved units are observed lower bounds, not confidence bounds.',
                           'Backend receipts are adapter attestations; controls test concrete behavior, not hostile-adapter security.',
                           'Treatment character exposures are recorded per round; token totals are provider-reported.']}


def write_condition_report(output, summary):
    # Write the treatment summary to report.json, then format the same
    # counts, formulas, and available hint coverage in REPORT.md.
    atomic_json(output / 'report.json', summary)
    lines = ['# Matched condition evaluation', '', summary['scope'], '',
             '| Condition | Kind | First correct | Within budget | Completed | Unresolved |',
             '|---|---|---|---|---|---|']
    for arm, kinds in summary['metrics'].items():
        for kind, m in kinds.items():
            n = m['selected']
            lines.append(f"| {arm} | {kind} | {m['first_attempt_correct']}/{n} | "
                         f"{m['correct_within_budget']}/{n} | {m['completed']}/{n} | {m['unresolved']} |")
    lines += ['', '## Exact formulas', ''] + [f'- {key}: {value}' for key, value in FORMULAS.items()]
    lines += ['', '## Matched comparisons', '',
              '| Baseline → Treatment | Kind | Recoveries | Regressions | Complete pairs | Final lift (pp) |',
              '|---|---|---|---|---|---|']
    for p in summary['paired_comparisons']:
        lift = p['final_lift_percentage_points']
        lines.append(f"| {p['baseline']} → {p['treatment']} | {p['kind']} | {p['recoveries']} | "
                     f"{p['regressions']} | {p['paired_completed']}/{p['selected']} | "
                     + ('pending' if lift is None else f'{lift:+.1f}') + ' |')
    lines += ['', '## Interpretation', '', summary['holdout_review'], ''] + summary['limitations']
    lines += _generation_stop_lines(summary)
    if summary.get('source_hint_coverage'):
        lines += ['', '## Source-hint coverage', '',
                  'Coverage records list selected APIs with source guidance and APIs without it.', '']
        for arm, coverage in summary['source_hint_coverage'].items():
            lines.append(f'- {arm}: {coverage}')
    (output / 'REPORT.md').write_text('\n'.join(lines) + '\n')
