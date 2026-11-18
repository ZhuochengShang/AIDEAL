#!/usr/bin/env python3
"""Continue Original/D1 with corrected saved passes and new no-feedback attempts.

This is a cumulative continuation, not a fresh R0 comparison or R1 repair.
--prepare makes no model calls. --run evaluates only the nonreusable API subset
in a separate native checkpoint, then reports the entire original denominator.
Set force_fresh=true to request every target without consuming replay evidence.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'vendor').exists():
    ROOT = Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow')
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'vendor/aideal_engine/src')]
import yaml
import run_corrected_readme_comparison as common
import rescore_native_programs as replay
from aideal.doc_check_sources import _comprehension_inventory, _load_manifest
from aideal.doc_check_inputs import _execute_sample_data
from aideal.doc_check_provenance import _comprehension_fingerprint_components
from aideal.doc_check_execution import _canonical_prompt_targets
from aideal.experiment_identity import digest_native, prompt_contract
from aideal.native_execution_contract import execution_contract
from aideal.readme_format import parse_readme
from workflow.runtime_profile import (load_runtime_profile, runtime_profile_receipts,
                                      verify_runtime_profile, require_runtime_ready)

ARMS = ('original', 'generated_d1')
read, binding, verify = common.read, common.binding, common.verify


def json_once(path, value):
    common.baseline.write_once(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def current_inputs(cfg, old, manifest):
    """Recompute model-visible library/document inputs from the historical config."""
    names = _load_manifest(cfg, str(manifest))
    inventory, shared, error = _comprehension_inventory(cfg, old['doc_source'], manifest=names,
                                                      full_doc=False, doc_scope='relevant')
    if error:
        raise ValueError('Unable to reconstruct saved documentation context: ' + str(error))
    data, _, _ = _execute_sample_data(cfg, cfg.comprehension['execute'])
    ex = cfg.comprehension['execute']
    payload = shared if shared is not None else '\n\0\n'.join(f'{e.name}\n{e.body}' for e in inventory)
    fp = _comprehension_fingerprint_components(cfg, ex=ex, doc_source=old['doc_source'],
        doc_scope='relevant', max_fix_rounds=0,
        manifest_sha256=hashlib.sha256('\n'.join(e.name for e in inventory).encode()).hexdigest(),
        document_sha256=hashlib.sha256(payload.encode()).hexdigest(),
        scaffold_file=cfg.root / ex['scaffold'], sample_data=data, class_context=False,
        timeout=int(ex.get('timeout_seconds', 600) or 600))
    targets = _canonical_prompt_targets(cfg)
    if targets is not None:
        fp['canonical_requested_targets'] = {'protocol_version': 1,
            'targets_sha256': digest_native(targets), 'targets_count': len(targets)}
    return fp


def verify_base_materials(old, current):
    """Fresh requests do not authorize changing the historical library or bank.

    Check the saved base before applying an explicitly reviewed input bundle,
    profile or execution-context override to the new condition configuration.
    """
    historical = old.get('run', {}).get('fingerprint_components', {})
    for key in ('source', 'fixtures', 'api_inventory', 'scaffold',
                'canonical_requested_targets', 'manifest_sha256',
                'document_sha256', 'original_document_files'):
        if key not in historical or historical[key] != current.get(key):
            raise ValueError('Historical base material changed before preparation: ' + key)


def reuse_reasons(old, current, intended_prompt, model, runtime_receipts, runtime_verified=False):
    """Fail closed when historical task/context identity cannot support reuse."""
    historical = old.get('run', {}).get('fingerprint_components', {})
    keys = ('project', 'language', 'doc_source', 'doc_scope', 'class_context',
            'manifest_sha256', 'document_sha256', 'original_document_files',
            'source', 'fixtures', 'api_inventory', 'scaffold', 'canonical_requested_targets',
            'prompt_contract', 'owner_overrides', 'execute_config', 'interpreter')
    reasons = ['changed_or_missing_' + key for key in keys
               if key not in historical or historical[key] != current.get(key)]
    if not runtime_verified:
        reasons.append('historical_runtime_not_verified_unchanged')
    if historical.get('prompt_contract') != intended_prompt:
        reasons.append('changed_intended_prompt_or_profile')
    if historical.get('models', {}).get('audience') != model:
        reasons.append('changed_audience_model')
    if historical.get('runtime_profile', []) != runtime_receipts:
        reasons.append('changed_runtime_profile')
    # Fixer settings are irrelevant at R0, but audience output allowance is not.
    if historical.get('models', {}).get('audience_max_output_tokens') != current.get('models', {}).get('audience_max_output_tokens'):
        reasons.append('changed_audience_output_limit')
    return sorted(set(reasons))


def validate_replay(old_path, corrected_path, runtime):
    """Require complete, immutable saved-program reexecution with this executor."""
    old, corrected = read(old_path), read(corrected_path)
    old_binding = binding(old_path)
    if (corrected.get('mode') != 'rescored_saved_programs' or not corrected.get('run', {}).get('complete')
            or corrected.get('source_result') != old_binding
            or set(corrected.get('details', {})) != set(old.get('details', {}))):
        raise ValueError('A complete matched corrected replay is required')
    if corrected.get('runtime_profile', []) != runtime:
        raise ValueError('Replay and continuation runtime profiles differ')
    contract = corrected['run'].get('contract')
    language = old['run']['fingerprint_components']['language']
    if contract != execution_contract(language):
        raise ValueError('Replay execution contract is not current')
    records = [old_binding, binding(corrected_path), binding(corrected_path.parent / 'launch.json')]
    complete = read(corrected_path.parent / 'completion.json')
    if complete.get('result') != binding(corrected_path) or complete.get('launch') != binding(corrected_path.parent / 'launch.json'):
        raise ValueError('Replay completion result hash changed')
    records.append(binding(corrected_path.parent / 'completion.json'))
    for api, row in corrected['details'].items():
        if row.get('mode') != 'saved_program_replay' or row.get('source_result') != old_binding:
            raise ValueError('Only unchanged saved programs may be reused: ' + api)
        evidence = row.get('evidence_bindings', [])
        identity_record = next((p for p in evidence if Path(p['path']).name == 'replay_identity.json'), None)
        if identity_record is None:
            raise ValueError('Replay lacks per-program provenance: ' + api)
        identity = read(identity_record['path'])
        if identity.get('override_sha256') is not None or identity.get('contract') != contract:
            raise ValueError('Replay code or contract differs: ' + api)
        if set(identity.get('execution_helpers', {})) != {'evaluation_scope.py', 'native_execution_contract.py', 'execution.py'}:
            raise ValueError('Replay execution helper bindings are incomplete: ' + api)
        for name, expected in identity['execution_helpers'].items():
            if replay.digest(ROOT / 'vendor/aideal_engine/src/aideal' / name) != expected:
                raise ValueError('Replay helper changed: ' + name)
        for name in ('source_result', 'source_config', 'source_program', 'source_execution', 'source_request'):
            records.append(identity[name])
        records.extend(evidence)
    records = list({r['path']: r for r in records}.values())
    verify(records)
    return old, corrected, records


def choose_rows(old, corrected, reasons):
    """Only proven current passes suppress a new request; failures never do."""
    reused, pending = {}, []
    for api in old['details']:
        row = corrected['details'][api]
        if not reasons and row.get('status') == 'pass':
            reused[api] = {**row, 'provenance': 'reused_verified',
                           'prior_generation_attempts': old.get('metrics', {}).get(api, {}).get('llm_calls', 1),
                           'new_generation_attempts': 0}
        else:
            pending.append(api)
    return reused, pending


def runtime_reuse_proof(path, sources):
    """A partial runtime audit cannot authorize reuse of historical successes."""
    if not path:
        return False, []
    path = Path(path).resolve(strict=True)
    proof = read(path)
    records = [binding(path)]
    if proof.get('status') != 'verified_unchanged':
        return False, records
    expected = sorted((binding(p) for p in sources), key=lambda r: r['path'])
    if sorted(proof.get('historical_results', []), key=lambda r: r['path']) != expected:
        raise ValueError('Runtime reuse proof does not bind both historical conditions')
    if not proof.get('artifact_bindings') or not proof.get('historical_receipts'):
        raise ValueError('Runtime reuse proof requires historical and current artifact evidence')
    records.extend(proof['artifact_bindings'] + proof['historical_receipts'] + expected)
    verify(records)
    return True, records


def input_bundle(path):
    """A reviewed optional fixture/scaffold replacement, identical in both arms."""
    if not path:
        return None, []
    path = Path(path).resolve(strict=True)
    bundle = read(path)
    records = [binding(path), bundle['scaffold'], bundle['setup_report']]
    for role, record in bundle.get('sample_data', {}).items():
        if role.lower() in {'output', 'output_path', 'output_file', 'output_dir'}:
            raise ValueError('Input bundle may not override writable output bindings')
        records.append(record)
    records.extend(bundle.get('support_files', []))
    verify(records)
    return bundle, records


def require_bundle_ready(bundle):
    if bundle is None:
        return
    report = read(bundle['setup_report']['path'])
    if report.get('status') != 'ready' or report.get('unresolved_setup', ['not declared']):
        raise ValueError('Input bundle has unresolved setup; model requests are blocked')


def selection_revision(path, historical_names, force_fresh):
    """Accept only an audited strict subset; selection never follows fresh failures."""
    if not path:
        return list(historical_names), {}, []
    if not force_fresh:
        raise ValueError('A selection revision requires force_fresh=true')
    path = Path(path).resolve(strict=True)
    revision = read(path)
    records = [binding(path), revision['manifest'], revision['audit']]
    verify(records)
    selected = read(revision['manifest']['path'])
    if (not isinstance(selected, list) or not selected or
            any(not isinstance(api, str) for api in selected) or len(selected) != len(set(selected)) or
            not set(selected) < set(historical_names)):
        raise ValueError('Revised manifest must be a nonempty strict subset of historical API identities')
    audit = read(revision['audit']['path'])
    if audit.get('policy') != 'public_owned_nonwrapper':
        raise ValueError('Selection revision must state the public-owned nonwrapper policy')
    exclusions = {}
    for row in audit.get('excluded', []):
        api = row.get('api')
        if not isinstance(api, str) or api in exclusions or not str(row.get('reason', '')).strip():
            raise ValueError('Every excluded API needs one explicit selection reason')
        evidence = row.get('source_evidence', [])
        if not evidence:
            raise ValueError('Every excluded API needs source evidence: ' + api)
        for source in evidence:
            if not isinstance(source.get('line'), int) or source['line'] < 1:
                raise ValueError('Source evidence requires a positive source line: ' + api)
            record = {key: source[key] for key in ('path', 'sha256')}
            verify([record])
            if source['line'] > len(Path(record['path']).read_text().splitlines()):
                raise ValueError('Source evidence line is outside the file: ' + api)
            records.append(record)
        exclusions[api] = {**row, 'status': 'excluded_by_selection'}
    if set(exclusions) != set(historical_names) - set(selected):
        raise ValueError('Selection audit must explain exactly every excluded API')
    return selected, exclusions, records


def verify_required_selection(spec, runtime, bundle):
    """A runtime validated for a reduced bank must not launch the old full bank."""
    for owner in (runtime, bundle):
        if owner is None:
            continue
        report = read(owner['setup_report']['path'])
        required = report.get('required_selection_revision')
        if required is not None and (not spec.get('selection_revision') or
                binding(spec['selection_revision']) != required):
            raise ValueError('Setup readiness requires the exact reviewed selection revision')


def prepare(spec):
    """Freeze Original and D1 in new namespaces; D2 is intentionally absent."""
    output = Path(spec['output']).resolve()
    force_fresh = spec.get('force_fresh', False)
    if not isinstance(force_fresh, bool):
        raise ValueError('force_fresh must be a boolean')
    runtime = load_runtime_profile(spec['runtime_profile']) if spec.get('runtime_profile') else None
    runtime_records = runtime_profile_receipts(runtime)
    bundle, bundle_records = input_bundle(spec.get('input_bundle'))
    verify_required_selection(spec, runtime, bundle)
    paths = {arm: Path(spec[key]).resolve(strict=True) for arm, key in
             zip(ARMS, ('original_result', 'generated_result'))}
    runtime_verified, runtime_proof_records = ((False, []) if force_fresh else
        runtime_reuse_proof(spec.get('runtime_reuse_evidence'), paths.values()))
    overrides = {}
    override_records = []
    if spec.get('execution_overrides'):
        overrides = read(spec['execution_overrides'])
        if set(overrides) - {'execution_context', 'exec_hints'} or any(not isinstance(v, str) for v in overrides.values()):
            raise ValueError('Execution overrides may contain only execution_context and exec_hints text')
        override_records = [binding(spec['execution_overrides'])]
    replay_paths = ({} if force_fresh else
        {arm: Path(spec[key]).resolve(strict=True) for arm, key in
         zip(ARMS, ('corrected_original_result', 'corrected_generated_result'))})
    for prior in [*paths.values(), *replay_paths.values()]:
        replay.assert_separate(prior.parent, output)
    original = read(paths['original'])
    original_cfg_path = paths['original'].parent / 'configs/aideal.yaml'
    original_cfg = common.load_config(original_cfg_path)
    manifest = paths['original'].parent / 'inputs/api_manifest.json'
    source = Path(read(paths['original'].parent / 'launch.json')['source']).resolve(strict=True)
    link = next((p.name for p in paths['original'].parent.iterdir()
                 if p.is_symlink() and p.resolve() == source), None)
    if not link:
        raise ValueError('Saved Original source link is missing')
    model = spec.get('model') or original_cfg.model_for_role('audience').model
    base = {'base_config': str(original_cfg_path), 'manifest': str(manifest),
            'source_link': {'name': link, 'target': str(source)}}
    records = runtime_records + runtime_proof_records + bundle_records + override_records + [binding(original_cfg_path), binding(manifest)]
    conditions = {}
    historical_names = set(original['details'])
    selected_names, exclusions, selection_records = selection_revision(
        spec.get('selection_revision'), list(original['details']), force_fresh)
    names = set(selected_names)
    records.extend(selection_records)
    common_contract = None
    for arm in ARMS:
        if force_fresh:
            old, corrected, proof = read(paths[arm]), None, [binding(paths[arm])]
        else:
            old, corrected, proof = validate_replay(paths[arm], replay_paths[arm], runtime_records)
        if (set(old['details']) != historical_names or not old['run'].get('complete')
                or old['run'].get('max_fix_rounds') != 0):
            raise ValueError('Original and D1 must have the same completed zero-repair bank')
        old_cfg_path = paths[arm].parent / 'configs' / ('aideal.yaml' if arm == 'original' else 'generated_readme.yaml')
        old_cfg = common.load_config(old_cfg_path)
        old_inputs = current_inputs(old_cfg, old, manifest)
        verify_base_materials(old, old_inputs)
        destination = output / arm
        cfg, selected = common.baseline.prepare(base, destination, model, None)
        if set(selected) != historical_names:
            raise ValueError('Prepared bank differs from the saved denominator')
        document = old_cfg.llm_readme if arm == 'generated_d1' else None
        if document is not None and set(e.name for e in parse_readme(document)) != historical_names:
            raise ValueError('D1 entries differ from the saved bank')
        raw = common.condition_raw(cfg.raw, destination, document, runtime)
        raw['comprehension']['execute'].update(overrides)
        if bundle is not None:
            scaffold = Path(bundle['scaffold']['path'])
            target = destination / 'inputs' / ('reviewed_' + scaffold.name)
            common.baseline.write_once(target, scaffold.read_bytes())
            raw['comprehension']['execute']['scaffold'] = str(target.relative_to(destination))
            raw['comprehension']['execute'].setdefault('sample_data', {}).update(
                {role: record['path'] for role, record in bundle.get('sample_data', {}).items()})
            records.append(binding(target))
            context = bundle.get('execution_context', '')
            if not isinstance(context, str):
                raise ValueError('Reviewed execution context must be text')
            if context:
                execution = raw['comprehension']['execute']
                execution['execution_context'] = execution.get('execution_context', '') + '\n' + context
        if spec.get('project_profile'):
            profile = Path(spec['project_profile']).resolve(strict=True)
            common.baseline.write_once(destination / 'configs/continuation_profile.yaml', profile.read_bytes())
            raw['files']['project_profile'] = 'configs/continuation_profile.yaml'
            records.append(binding(profile))
        config = destination / 'configs/continuation.yaml'
        common.baseline.write_once(config, yaml.safe_dump(raw, sort_keys=False).encode())
        final = common.load_config(config)
        audience = final.model_for_role('audience')
        intended_prompt = prompt_contract(final)
        contract = {'prompt': intended_prompt, 'model': f'{audience.provider}:{audience.model}',
                    'max_output_tokens': audience.max_output_tokens, 'runtime': runtime_records,
                    'engine': read(destination / 'launch.json')['engine'], 'input_bundle': bundle_records, 'execution_overrides': overrides}
        if common_contract is not None and contract != common_contract:
            raise ValueError('Original and D1 do not share the same current settings')
        common_contract = contract
        reasons = reuse_reasons(old, old_inputs, intended_prompt, contract['model'], runtime_records, runtime_verified)
        if audience.max_output_tokens != old_inputs['models'].get('audience_max_output_tokens'):
            reasons.append('changed_intended_output_limit')
        if overrides:
            reasons.append('changed_reviewed_execution_context')
        if bundle is not None:
            reasons.append('changed_reviewed_input_bundle')
        if force_fresh:
            reasons.append('explicit_force_fresh_no_replay_consumed')
            reused, pending = {}, selected_names
        else:
            reused, pending = choose_rows(old, corrected, reasons)
        json_once(destination / 'inputs/pending_manifest.json', pending)
        records.extend(proof + [binding(old_cfg_path), binding(config), binding(destination / 'launch.json'),
            binding(destination / 'inputs/pending_manifest.json')])
        if document is not None:
            records.extend([binding(document), binding(destination / 'docs/README.md')])
        conditions[arm] = {'config': str(config), 'source_result': str(paths[arm]),
            'corrected_result': str(replay_paths[arm]) if arm in replay_paths else None,
            'replay_consumed': not force_fresh, 'selected_apis': selected_names,
            'historical_count': len(historical_names), 'excluded_apis': exclusions,
            'reused_apis': list(reused), 'pending_apis': pending, 'reuse_blockers': sorted(set(reasons)),
            'old_input_fingerprint': old_inputs,
            'runtime_reuse_verified': runtime_verified,
            'output_relocation': 'Writable paths relocate per attempt; input fixture contents remain bound.'}
    identity = {'schema': 'aideal.verified-readme-continuation/v1', 'conditions': conditions,
        'library': spec.get('library'), 'selected': len(names), 'historical_count': len(historical_names),
        'excluded_count': len(exclusions), 'selection_bindings': selection_records,
        'model': model, 'force_fresh': force_fresh,
        'mode': ('fresh_corrected_protocol_R0' if all(not c['reused_apis'] for c in conditions.values())
                 else 'cumulative_no_feedback_resampling'), 'max_fix_rounds': 0,
        'paper_fresh_R0_eligible': all(not c['reused_apis'] for c in conditions.values()), 'common_contract': common_contract,
        'bindings': sorted({r['path']: r for r in records}.values(), key=lambda r: r['path']),
        'operator': binding(__file__), 'scope': 'Native execution and configured self-checks; no independent output oracle.'}
    json_once(output / 'continuation.json', identity)
    return identity


def totals(rows):
    return {key: sum((row.get(key) or 0) for row in rows.values())
            for key in ('llm_calls', 'input_tokens', 'output_tokens', 'wall_s')}


def aggregate(old, corrected, fresh, condition):
    """Keep old costs, replay costs and new generation costs explicitly separate."""
    details = {}
    for api in condition['reused_apis']:
        details[api] = {**corrected['details'][api], 'provenance': 'reused_verified',
                       'prior_generation_attempts': old.get('metrics', {}).get(api, {}).get('llm_calls', 1),
                       'new_generation_attempts': 0}
    fresh_metrics = fresh.get('metrics', {})
    for api in condition['pending_apis']:
        if api in fresh_metrics:
            saved = fresh.get('details', {}).get(api)
            details[api] = {**(saved if isinstance(saved, dict) else {}), **fresh_metrics[api],
                           'provenance': 'fresh_generated',
                           'prior_generation_attempts': old.get('metrics', {}).get(api, {}).get('llm_calls', 1),
                           'new_generation_attempts': fresh_metrics[api].get('llm_calls', 0)}
        else:
            details[api] = {'status': 'not_run', 'provenance': 'pending_new_generation'}
    pending = condition['pending_apis']
    complete = (not pending or (fresh.get('run', {}).get('complete') is True
                and fresh['run'].get('remaining_api_count') == 0
                and set(fresh_metrics) == set(pending)
                and not any(str(r.get('error_category', '')).startswith(('provider-', 'llm-error'))
                            for r in fresh_metrics.values())))
    passes = sum(row.get('status') == 'pass' for row in details.values())
    return {'mode': 'cumulative_no_feedback_resampling' if condition['reused_apis'] else 'fresh_corrected_protocol_R0',
        'paper_fresh_R0_eligible': not condition['reused_apis'],
        'run': {'complete': complete, 'selected_api_count': len(condition['selected_apis']),
                'max_fix_rounds': 0, 'reused_verified': len(condition['reused_apis']),
                'new_requested_targets': len(pending), 'new_recorded_targets': len(fresh_metrics)},
        'passes': passes, 'score_with_infra': passes / len(condition['selected_apis']),
        'details': details, 'exclusions': condition.get('excluded_apis', {}),
        'selection': {'historical_count': condition.get('historical_count', len(old['details'])),
                      'selected_count': len(condition['selected_apis']),
                      'excluded_count': len(condition.get('excluded_apis', {}))},
        'prior_generation_cost_scope': 'full_historical_bank', 'costs': {'prior_generation': totals(old.get('metrics', {})),
            'corrected_saved_program_replay': (totals(corrected.get('metrics', {})) if corrected is not None else
                {'status': 'not_consumed', 'calls': 0, 'llm_calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'wall_s': 0}),
            'new_generation': totals(fresh_metrics)},
        'interpretation': ('Verified saved successes plus new attempts on remaining targets; cumulative continuation, '
            'not fresh R0 or R1 repair.' if condition['reused_apis'] else
            'All targets receive fresh initial programs under the new protocol. No prior failure feedback is sent.')}


def run_condition(spec, arm):
    identity = prepare(spec)
    condition = identity['conditions'][arm]
    destination = Path(spec['output']).resolve() / arm
    runtime = load_runtime_profile(spec['runtime_profile']) if spec.get('runtime_profile') else None
    with common.ownership(destination):
        verify(identity['bindings'] + [identity['operator']])
        verify_runtime_profile(runtime)
        complete_path = destination / 'completion.json'
        if complete_path.exists():
            summary = read(complete_path)
            verify([summary['result']])
            return summary
        fresh = {}
        if condition['pending_apis']:
            common.assert_review_released(destination)
            require_runtime_ready(runtime, library=spec.get('library'))
            bundle, _ = input_bundle(spec.get('input_bundle'))
            require_bundle_ready(bundle)
            cfg = common.load_config(condition['config'])
            os.environ['MPLCONFIGDIR'] = str(destination / 'cache/matplotlib')
            common.reset_usage()
            with (destination / 'console.log').open('a', buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
                fresh = common.comprehension_check(cfg, doc_source='original' if arm == 'original' else 'aideal',
                    execute=True, show_code=True, class_context=False, max_fix_rounds=0,
                    resume=True, doc_scope='relevant', sample=None,
                    manifest=str(destination / 'inputs/pending_manifest.json'))
                common.atomic_json(destination / 'fresh_result.json', fresh)
        verify(identity['bindings'] + [identity['operator']])
        verify_runtime_profile(runtime)
        corrected = read(condition['corrected_result']) if condition['corrected_result'] else None
        result = aggregate(read(condition['source_result']), corrected, fresh, condition)
        result.update(condition=arm, source_result=binding(condition['source_result']),
                      corrected_result=binding(condition['corrected_result']) if condition['corrected_result'] else None,
                      fresh_result=binding(destination / 'fresh_result.json') if condition['pending_apis'] else None,
                      scope=identity['scope'])
        common.atomic_json(destination / 'result.json', result)
        summary = {'condition': arm, 'status': 'complete' if result['run']['complete'] else 'incomplete',
                   **result['run'], 'passes': result['passes'], 'costs': result['costs'],
                   'paper_fresh_R0_eligible': result['paper_fresh_R0_eligible'], 'result': binding(destination / 'result.json')}
        common.atomic_json(destination / 'status.json', summary)
        if result['run']['complete']:
            common.atomic_json(complete_path, summary)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--bank')
    parser.add_argument('--condition', choices=ARMS)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare', action='store_true')
    modes.add_argument('--run', action='store_true')
    modes.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    data = read(args.spec)
    banks = data.get('banks') or {None: data}
    if args.bank is not None:
        banks = {args.bank: banks[args.bank]}
    if args.worker:
        if len(banks) != 1 or not args.condition:
            parser.error('Worker requires one bank and one condition')
        summary = run_condition(next(iter(banks.values())), args.condition)
        print(json.dumps(summary), flush=True)
        return 0 if summary['status'] == 'complete' else 2
    for bank, spec in banks.items():
        with common.ownership(Path(spec['output']).resolve()):
            identity = prepare(spec)
        print(json.dumps({'bank': bank, 'selected': identity['selected'], 'conditions': {
            arm: {'reuse': len(c['reused_apis']), 'new': len(c['pending_apis']), 'blockers': c['reuse_blockers']}
            for arm, c in identity['conditions'].items()}}), flush=True)
    if args.run:
        for bank, spec in banks.items():
            for arm in ARMS:
                command = [sys.executable, str(Path(__file__).resolve()), '--spec', str(args.spec.resolve()),
                           '--worker', '--condition', arm]
                if bank is not None:
                    command.extend(['--bank', bank])
                completed = subprocess.run(command, check=False)
                if completed.returncode:
                    return completed.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
