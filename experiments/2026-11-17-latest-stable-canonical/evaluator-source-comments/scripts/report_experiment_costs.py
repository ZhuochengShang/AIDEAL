#!/usr/bin/env python3
"""Summarize saved Gemini receipts and label projections without reading secrets."""
import argparse
import hashlib
import json
import math
from pathlib import Path

MODEL = 'gemini-3.1-flash-lite'
RATES = {'input_usd_per_million': 0.25, 'output_usd_per_million': 1.50,
         'model': MODEL, 'basis': 'Gemini Developer API standard text; output includes thinking; no cached discount',
         'source': 'https://ai.google.dev/gemini-api/docs/pricing', 'checked': '2026-11-16'}
SCENARIO = {'r0': {'input_tokens': 4000, 'output_tokens': 1000},
            'readme_entry': {'input_tokens': 8000, 'output_tokens': 2000},
            'readme_distill': {'input_tokens': 20000, 'output_tokens': 1500}}


def price(inputs, outputs):
    return (inputs * RATES['input_usd_per_million'] + outputs * RATES['output_usd_per_million']) / 1e6


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def read(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def scan(r0_root=None, readme_root=None):
    rows, seen = [], set()
    for root, kind in ((r0_root, 'r0'), (readme_root, 'readme')):
        if root is None:
            continue
        root = Path(root).resolve()
        if not root.is_dir():
            raise ValueError('Receipt root is not a directory: ' + str(root))
        for path in sorted(root.rglob('provider.json')):
            if path.resolve() in seen:
                continue
            seen.add(path.resolve())
            provider, request = read(path), read(path.with_name('request.json'))
            library = path.relative_to(root).parts[0]
            stage = ('r0' if request.get('round', 0) == 0 else 'unexpected_repair') if kind == 'r0' else {
                'entry': 'readme_entry', 'distill': 'readme_distill'}.get(request.get('phase'), 'readme_unknown')
            usage = provider.get('usage') or {}
            if not isinstance(usage, dict):
                usage = {}
            ins, outs = usage.get('input_tokens'), usage.get('output_tokens')
            calls = usage.get('calls', 1)
            known = number(ins) and number(outs) and number(calls) and calls > 0
            success = provider.get('status') in ('returned', 'complete')
            unit = 'distillation' if stage == 'readme_distill' else request.get('api')
            rows.append({'library': library, 'stage': stage, 'success': success, 'unit': unit,
                         'known': known, 'priced': known and request.get('model') == MODEL,
                         'input_tokens': ins if known else 0, 'output_tokens': outs if known else 0})
    return rows


def summarize(rows):
    priced = [r for r in rows if r['priced']]
    return {'requests': len(rows), 'successful_requests': sum(r['success'] for r in rows),
            'failed_or_unfinished_requests': sum(not r['success'] for r in rows),
            'unique_completed_units': len({r['unit'] for r in rows if r['success'] and r['unit']}),
            'input_tokens': sum(r['input_tokens'] for r in rows), 'output_tokens': sum(r['output_tokens'] for r in rows),
            'unknown_usage_requests': sum(not r['known'] for r in rows),
            'failed_unknown_usage_requests': sum(not r['known'] and not r['success'] for r in rows),
            'unpriced_known_usage_requests': sum(r['known'] and not r['priced'] for r in rows),
            'known_cost_usd': round(sum(price(r['input_tokens'], r['output_tokens']) for r in priced), 8)}



def replayed_units(readme_root):
    """Count validated reused entries as progress, never as another paid request."""
    units = set()
    if readme_root is None:
        return units
    root = Path(readme_root).resolve()
    for path in root.rglob('replay_receipt.json'):
        receipt = read(path)
        if receipt.get('action') not in ('replayed_complete', 'revalidated_returned_response'):
            raise ValueError('Unsupported README replay receipt: ' + str(path))
        documents = {}
        for source, expected in receipt.get('files', {}).items():
            data = Path(source).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('README replay evidence changed: ' + source)
            documents[Path(source).name] = data
        if not {'request.json', 'response.txt', 'provider.json'} <= documents.keys():
            raise ValueError('Incomplete README replay receipt: ' + str(path))
        request = json.loads(documents['request.json'])
        stage = {'entry': 'readme_entry', 'distill': 'readme_distill'}.get(request.get('phase'))
        unit = 'distillation' if stage == 'readme_distill' else request.get('api')
        if stage and unit:
            units.add((path.relative_to(root).parts[0], stage, unit))
    return units


def build_report(r0_root=None, readme_root=None, plan=None, scenario=None):
    rows, scenario = scan(r0_root, readme_root), scenario or SCENARIO
    replays = replayed_units(readme_root)
    plan = (plan or {}).get('libraries', {})
    pools = {stage: [r for r in rows if r['stage'] == stage and r['success'] and r['priced']] for stage in SCENARIO}
    libraries, total_remaining = {}, 0.0
    remaining_tokens = {'input_tokens': 0.0, 'output_tokens': 0.0}
    for name in sorted(set(plan) | {r['library'] for r in rows} | {r[0] for r in replays}):
        stages, spec = {}, plan.get(name, {})
        planned = {'r0': spec.get('r0_apis'), 'readme_entry': spec.get('readme_entries'),
                   'readme_distill': (spec.get('readme_distill_calls', 1 if spec.get('readme_entries', 0) else 0)
                                      if name in plan else None)}
        for stage in sorted(set(SCENARIO) | {r['stage'] for r in rows if r['library'] == name}):
            current = [r for r in rows if r['library'] == name and r['stage'] == stage]
            record = summarize(current)
            reused = {unit for library, phase, unit in replays if library == name and phase == stage}
            completed = {r['unit'] for r in current if r['success'] and r['unit']}
            record['replayed_units'] = len(reused)
            record['unique_completed_units'] = len(completed | reused)
            expected = planned.get(stage)
            if expected is not None and (type(expected) is not int or expected < 0):
                raise ValueError('Plan counts must be nonnegative integers')
            record['planned_units'] = expected
            record['remaining_units'] = max(0, expected - record['unique_completed_units']) if expected is not None else None
            if stage in SCENARIO and expected is not None:
                pool = pools[stage]
                means = ({key: sum(r[key] for r in pool) / len(pool) for key in ('input_tokens', 'output_tokens')}
                         if pool else scenario.get(stage, {}))
                if not all(number(means.get(key)) for key in ('input_tokens', 'output_tokens')):
                    raise ValueError('Scenario requires nonnegative input_tokens and output_tokens for each stage')
                record['projection_basis'] = 'observed successful request mean across libraries' if pool else 'explicit scenario; not measured'
                record['mean_input_tokens'], record['mean_output_tokens'] = means['input_tokens'], means['output_tokens']
                record['mean_sample_requests'] = len(pool)
                remaining = record['remaining_units'] * price(means['input_tokens'], means['output_tokens'])
                record['estimated_remaining_cost_usd'] = round(remaining, 8)
                for key in remaining_tokens:
                    record['estimated_remaining_' + key] = record['remaining_units'] * means[key]
                    remaining_tokens[key] += record['estimated_remaining_' + key]
                total_remaining += remaining
            stages[stage] = record
        libraries[name] = stages
    totals = summarize(rows)
    totals['replayed_units'] = len(replays)
    totals.pop('unique_completed_units')  # Cross-library names are not global API identities.
    for key, value in remaining_tokens.items():
        totals['estimated_remaining_' + key] = value if plan else None
        totals['known_plus_projected_' + key] = totals[key] + value if plan else None
    totals['estimated_remaining_cost_usd'] = round(total_remaining, 8) if plan else None
    totals['known_plus_projected_cost_usd'] = round(totals['known_cost_usd'] + total_remaining, 8) if plan else None
    return {'rates': RATES, 'totals': totals, 'libraries': libraries,
            'limitations': ['Costs are estimates at standard listed rates, not an invoice.',
             'Unknown-usage and other-model costs are excluded, never assumed zero.',
             'Projections exclude future retries and SDK attempts without separate usage receipts.',
             'Provider completion counts generation outcomes, not successful API execution.',
             'Validated replay contributes completed units but no new requests, tokens, or charges.',
             'README distillation defaults to one call per planned library; override readme_distill_calls when no original docs exist.']}


def markdown(report):
    total = report['totals']
    lines = ['# Experiment token and cost report', '',
             f"Recorded requests: **{total['requests']}**. Known tokens: **{total['input_tokens']:,} input / {total['output_tokens']:,} output**.",
             f"Known priced usage: **${total['known_cost_usd']:.6f}**. Unknown usage: **{total['unknown_usage_requests']} requests**; other-model/unpriced receipts: **{total['unpriced_known_usage_requests']}**.", '',
             '| Library | Stage | Completed / planned | Requests | Input / output tokens | Known USD | Remaining estimate USD | Basis |',
             '|---|---|---:|---:|---:|---:|---:|---|']
    for library, stages in report['libraries'].items():
        for stage, row in stages.items():
            planned = row['planned_units'] if row['planned_units'] is not None else 'unspecified'
            estimate = f"${row['estimated_remaining_cost_usd']:.6f}" if 'estimated_remaining_cost_usd' in row else '—'
            basis = row.get('projection_basis', 'No projection')
            if 'mean_input_tokens' in row:
                basis += f" ({row['mean_input_tokens']:.0f} in / {row['mean_output_tokens']:.0f} out; n={row['mean_sample_requests']})"
            lines.append(f"| {library} | {stage} | {row['unique_completed_units']} / {planned} | {row['requests']} | {row['input_tokens']:,} / {row['output_tokens']:,} | ${row['known_cost_usd']:.6f} | {estimate} | {basis} |")
    if total['known_plus_projected_cost_usd'] is not None:
        lines += ['', f"Known spend plus estimated remaining work: **${total['known_plus_projected_cost_usd']:.6f}** (excludes unknown costs).",
                  f"Known plus projected tokens: **{total['known_plus_projected_input_tokens']:,.0f} input / {total['known_plus_projected_output_tokens']:,.0f} output**."]
    lines += ['', f"Rates: $0.25/M input and $1.50/M output including thinking, with no cached discount. [Google pricing]({RATES['source']}) checked {RATES['checked']}.", '']
    lines.extend('- ' + item for item in report['limitations'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('r0-root', 'readme-root', 'plan', 'scenario'):
        parser.add_argument('--' + arg, type=Path)
    parser.add_argument('--output-json', type=Path, required=True)
    parser.add_argument('--output-md', type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.r0_root, args.readme_root,
                          json.loads(args.plan.read_text()) if args.plan else None,
                          json.loads(args.scenario.read_text()) if args.scenario else None)
    for path, content in ((args.output_json, json.dumps(report, indent=2) + '\n'), (args.output_md, markdown(report))):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_text(content)
        temporary.replace(path)
    print(json.dumps(report['totals']))


if __name__ == '__main__':
    main()
