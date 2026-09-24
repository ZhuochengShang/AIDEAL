"""Matched condition scores with fixed denominators and explicit treatment costs."""
from itertools import combinations

from .ablation import score
from .execution import atomic_json
from .generation import generation_counts
from .condition_inputs import measured_conditions, source_api_function_ids


FORMULAS = {
    'selected': 'N_k = number of selected cases of kind k × number of trials, per condition',
    'first_attempt_lower_bound_pct': '100 × first-attempt correct / N_k',
    'within_budget_lower_bound_pct': '100 × correct within the common repair budget / N_k',
    'unresolved': 'N_k − (verified passes + verified failures)',
    'paired_delta_percentage_points': '100 × (fail→pass recoveries − pass→fail regressions) / completed matched pairs',
    'final_lift_percentage_points': '100 × (recoveries − regressions) / N_k, only when all N_k pairs complete',
}


def report_conditions(frozen, rows):
    cfg = frozen['config']
    arms, common = measured_conditions(cfg), cfg['common']
    metric_baseline = 'original' if 'original' in arms else arms[0]
    for row in rows:
        if row.get('arm') not in arms:
            raise ValueError('Result is outside the frozen measured_conditions scope')
        if row.get('backend_sha256') != frozen['backends'].get(row.get('arm'), {}).get('sha256'):
            raise ValueError('Result belongs to another condition backend')
    metrics = score(frozen['bank'], common['trial_ids'], rows,
                    study_sha256=frozen['study_sha256'], max_snippet_fixes=common['max_snippet_fixes'],
                    arms=arms, baseline=metric_baseline)
    if metric_baseline != 'original':
        # The shared scorer retains legacy field names; never label H as Original.
        for kinds in metrics.values():
            for values in kinds.values():
                for key in ('recoveries', 'regressions'):
                    values[key + '_vs_measured_baseline'] = values.pop(key + '_vs_original')
    indexed = {(r['arm'], r['case_id'], r['trial_id']): r for r in rows}
    pairs = []
    for baseline, treatment in combinations(arms, 2):
        for kind in ('micro', 'puzzle'):
            matched = [(indexed.get((baseline, c['id'], trial), {}).get('status'),
                        indexed.get((treatment, c['id'], trial), {}).get('status'))
                       for c in frozen['bank']['cases'] if c['kind'] == kind
                       for trial in common['trial_ids']]
            done = [(a, b) for a, b in matched if a in ('pass', 'fail') and b in ('pass', 'fail')]
            recovered = sum(a == 'fail' and b == 'pass' for a, b in done)
            regressed = sum(a == 'pass' and b == 'fail' for a, b in done)
            n = len(matched)
            pairs.append({'baseline': baseline, 'treatment': treatment, 'kind': kind,
                          'selected': n, 'paired_completed': len(done), 'recoveries': recovered,
                          'regressions': regressed,
                          'paired_delta_percentage_points': 100 * (recovered - regressed) / len(done) if done else None,
                          'final_lift_percentage_points': 100 * (recovered - regressed) / n if n and len(done) == n else None})
    keys = ('provider_calls', 'provider_seconds', 'execution_seconds', 'reported_input_tokens',
            'reported_output_tokens', 'calls_without_usage')
    resources = {arm: {k: sum(r.get('resources', {}).get(k, 0) for r in rows if r['arm'] == arm)
                       for k in keys} for arm in arms}
    targets = set(cfg['api_function_ids'].values())
    coverage = {}
    for arm, index in frozen.get('source_hint_indexes', {}).items():
        covered = {r['function_id'] for r in index['records']}
        coverage[arm] = {**index['coverage'], 'task_bank_api_count': len(targets),
                         'covered_task_bank_api_count': len(targets & covered),
                         'uncovered_task_bank_function_ids': sorted(targets - covered),
                         'supplementary_api_count': len(source_api_function_ids(cfg)) - len(targets)}
    return {'protocol': frozen['protocol'], 'study_sha256': frozen['study_sha256'],
            'design': cfg['design'], 'conditions': list(arms), 'metrics': metrics, 'paired_comparisons': pairs,
            'frozen_conditions': list(cfg['conditions']),
            'unmeasured_conditions': [a for a in cfg['conditions'] if a not in arms],
            'metrics_baseline': metric_baseline,
            'measurement_scope': {'condition_count': len(arms), 'case_count': len(frozen['bank']['cases']),
                                  'trials_per_case': len(common['trial_ids']),
                                  'planned_units': len(arms) * len(frozen['bank']['cases']) * len(common['trial_ids']),
                                  'task_bank_api_count': len(targets),
                                  'source_attribution_api_count': len(source_api_function_ids(cfg)),
                                  'maximum_repair_round': common['max_snippet_fixes']},
            'generation_classifications': generation_counts(rows, arms), 'resources': resources, 'formulas': FORMULAS, 'scope': frozen['bank'].get('scope_note', ''),
            'holdout_review': cfg['holdout_review'],
            'source_hint_coverage': coverage,
            'all_complete': all(m['unresolved'] == 0 for by_kind in metrics.values() for m in by_kind.values()),
            'limitations': ['Percentages with unresolved units are observed lower bounds, not confidence bounds.',
                           'Backend receipts are adapter attestations; controls test concrete behavior, not hostile-adapter security.',
                           'Treatment character exposures are recorded per round; token totals are provider-reported.',
                           'Completion and scores cover only the frozen measured conditions; other backends are validation controls.',
                           'A comparison without Original does not estimate improvement over Original.']}


def write_condition_report(output, summary):
    atomic_json(output / 'report.json', summary)
    scope = summary['measurement_scope']
    lines = ['# Matched condition evaluation', '', summary['scope'], '',
             'Measured conditions: ' + ', '.join(summary['conditions']) + '.',
             'Frozen and control-validated backends: ' + ', '.join(summary['frozen_conditions']) + '.',
             f"Planned audience units: {scope['planned_units']} = {scope['condition_count']} conditions × "
             f"{scope['case_count']} cases × {scope['trials_per_case']} trials. "
             f"Each unit allows initial R0 and repairs through R{scope['maximum_repair_round']}.",
             'Metric comparison baseline: ' + summary['metrics_baseline'] + '.', '',
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
    lines += ['', '## Generation stops (unresolved)', '',
              '| Condition | Incomplete | Refusal | Empty | Provider failure |',
              '|---|---|---|---|---|']
    for arm, counts in summary['generation_classifications'].items():
        values = [counts['generation_' + name] for name in ('incomplete', 'refusal', 'empty', 'provider_failure')]
        lines.append('| ' + arm + ' | ' + ' | '.join(str(value) for value in values) + ' |')
    lines += ['', 'These stopped generations were not compiled or executed. They retain the fixed denominator and are not verified API failures.']
    if summary.get('source_hint_coverage'):
        lines += ['', '## Source-hint coverage', '',
                  'total_functions describes the source attribution catalog. task_bank_api_count describes the scored API scope; supplemental helpers never enlarge its denominator.', '']
        for arm, coverage in summary['source_hint_coverage'].items():
            lines.append(f'- {arm}: {coverage}')
    (output / 'REPORT.md').write_text('\n'.join(lines) + '\n')
