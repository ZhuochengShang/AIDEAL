"""Start here: one schedule, repair loop and replay path for both study protocols.

The explicit policies in evaluation_readme.py and evaluation_conditions.py supply the
public context and library-specific checks. This module owns lifecycle rules;
it does not import either policy or choose behavior from a protocol name.
"""
from pathlib import Path
import random

from .ablation import bind, digest, load
from .evaluation_setup import assert_review_released
from .execution import ownership
from .evaluation_program_generation import (STOPPED_STATUSES, mark_generation, selected_response,
                                            verify_generation, verify_checkpoint_extension)
from .response_status import strip_code_fence


def run_study(study, output, open_policy, condition=None, max_units=None, retry_provider=False):
    """Validate all checkpoints, then resume a deterministic complete schedule."""
    # Open the saved study and take ownership of its output directory.
    # Schedule a unit for each condition, task, and trial, then return the report.
    assert_review_released(Path(study).resolve().parent)
    if max_units is not None and (type(max_units) is not int or max_units < 1):
        raise ValueError('max_units must be a positive integer')
    policy = open_policy(study)
    frozen, api = policy.frozen, policy.api
    if condition is not None and condition not in policy.arms:
        raise ValueError(policy.unknown_condition)
    output = Path(output).resolve()
    assert_review_released(output)
    with ownership(output):
        identity = output / 'identity.json'
        if identity.exists() and load(identity).get('study_sha256') != frozen['study_sha256']:
            raise ValueError('This run directory belongs to another frozen study')
        api.atomic_json(identity, policy.identity)
        rows = api._load_completed_rows(output)
        # Validate checkpoint rows and replay saved attempts before making new calls.
        summary = policy.report(frozen, list(rows.values()))
        for (arm, case_id, trial), row in rows.items():
            verify_row(policy, row, output / arm / f'{case_id}--{trial}')
        # Build the schedule in a reproducible order using the configured seed.
        common = frozen['config']['common']
        schedule = [(arm, case, trial) for arm in policy.arms
                    for case in frozen['bank']['cases'] for trial in common['trial_ids']]
        random.Random(common.get('ordering_seed', 42)).shuffle(schedule)
        processed = 0
        for arm, case, trial in schedule:
            key = (arm, case['id'], trial)
            # Skip unselected conditions and units with a terminal result.
            if (condition and arm != condition) or rows.get(key, {}).get('status') in STOPPED_STATUSES:
                continue
            if max_units is not None and processed >= max_units:
                break
            policy.verify_inputs(frozen)
            directory = output / arm / f"{case['id']}--{trial}"
            directory.mkdir(parents=True, exist_ok=True)
            context = policy.prepare(arm, case, directory, replay=False)
            row = run_unit(policy, arm, case, trial, directory, context, retry_provider)
            policy.verify_inputs(frozen)
            verify_row(policy, row, directory)
            api.atomic_json(directory / 'result.json', row)
            rows[key] = row
            # Publish the report only after the verified unit checkpoint is on disk.
            summary = policy.report(frozen, list(rows.values()))
            policy.write_report(output, summary)
            if policy.log_progress:
                print(f"{arm} | {case['id']} | {trial}: {row['status']}", flush=True)
            processed += 1
            # Pause the schedule when the model or checker cannot finish this unit.
            if row['status'] in ('provider_pending', 'unverified'):
                break
        if not processed:
            # A resume with no new units can still regenerate the report.
            policy.write_report(output, summary)
        return summary


def run_unit(policy, arm, case, trial, directory, context=None, retry_provider=False):
    """Generate, check and repair one unit without changing its library resources."""
    # The policy supplies the prompt and checker for this study.
    frozen, api = policy.frozen, policy.api
    # cfg holds the frozen study settings, including the model and repair budget.
    cfg = frozen['config']
    # One row records one condition (arm), task (case), and repetition (trial).
    # The study hash ties it to this freeze. ** inserts extra condition fields,
    # such as backend_sha256 for the library build under test.
    row = {'arm': arm, 'case_id': case['id'], 'trial_id': trial,
           'study_sha256': frozen['study_sha256'], **policy.row_fields[arm],
           'status': 'not_run', 'first_attempt_pass': False}
    # The initial prompt has no failed program or feedback to include.
    previous = None
    # Round 0 is the initial attempt. A budget of 2 repairs allows rounds 0, 1, 2.
    for number in range(cfg['common']['max_snippet_fixes'] + 1):
        # Give each round its own folder. :02d pads 0 to 00, 1 to 01, and so on.
        root = directory / f'round_{number:02d}'
        # 1. Build the public prompt and record the context used to build it.
        # A repair prompt can include the last failed program and its feedback.
        request, receipts = policy.request(arm, case, previous, number, context)
        # Save each receipt under its policy-defined name, if any were returned.
        for key, receipt in receipts.items():
            api.atomic_json(root / policy.receipt_files[key], receipt)
        # 2. Reuse or request a candidate program for this task. Transport retries
        # stay within this round. Recheck the pinned inputs afterward.
        response = api._request_solution(cfg, request, root, retry_provider)
        policy.verify_inputs(frozen)
        if response is None:
            # No usable response arrived within the allowed provider attempts.
            row['status'] = 'provider_pending'
            break
        # 3. Record the generation status. Stop before the checker if the answer
        # is incomplete, refused, empty, or otherwise unusable.
        if not mark_generation(row, response, number):
            break
        # Unwrap an answer enclosed in a Markdown code block.
        code = strip_code_fence(response['code'])
        # 4. Run the checker against the selected library. It returns an attempt
        # folder and a process record, which the policy turns into a verdict.
        destination, process = policy.execute(arm, case, code, root)
        policy.verify_inputs(frozen)
        passed = policy.outcome(process, arm)
        if passed is None:
            # The checker could not establish a verdict. Save an unresolved row.
            row['status'] = 'unverified'
            break
        # Bind the exact checker request and result by path, hash, and size.
        # Record the checked round. Only a pass in round 0 is a first-attempt pass.
        records = {name: bind(destination / name) for name in ('process.json', 'request.json')}
        _checked_result(row, number, code, passed, process, records)
        if passed:
            break
        # 5. A checked failure supplies the failed program and public feedback
        # for the next prompt, if a repair round remains.
        previous = api.previous_result(code, process['payload'], policy.failure_feedback)
    # 6. Use the same saved attempts for resource totals and replay. The caller
    # verifies the returned row before saving it as result.json.
    evidence = policy.evidence(directory)
    row['resources'] = api._collect_resources(evidence)
    row['round_evidence'] = evidence
    row.update({key: [item[field] for item in row['round_evidence']]
                for key, field in policy.row_receipts.items()})
    return row


def _checked_result(row, number, code, passed, process, records):
    """Use the same verdict projection during execution and evidence replay."""
    # Update row in place with the checker flags, candidate hash, and
    # files that support the verdict. Only a round 0 pass is a first-attempt pass.
    row.update({key: process['payload'][key] for key in ('execution_pass', 'oracle_pass', 'target_reached')})
    row.update(status='pass' if passed else 'fail', last_checked_round=number,
               code_sha256=digest(code), adjudication={'process': records['process.json'],
                                                     'request': records['request.json']})
    if passed:
        row.update(first_attempt_pass=number == 0, first_pass_round=number)


def verify_row(policy, row, directory):
    """Reject changed history; validate append-only recovery before any new call."""
    # Compare the row with the files in its unit directory. Rebuild its
    # verdict and resource totals before trusting it on resume.
    api = policy.api
    evidence = row.get('round_evidence')
    current = policy.evidence(directory)
    # An unresolved unit may gain later attempts. Verify that the
    # previous evidence still matches before accepting that extension.
    extended = evidence != current
    if extended:
        if row.get('status') not in ('provider_pending', 'unverified') or not isinstance(evidence, list):
            raise ValueError('Saved condition attempt evidence changed')
        verify_checkpoint_extension(evidence, current)
    if row.get('resources') != api._collect_resources(evidence):
        raise ValueError('Saved condition resource totals differ from attempt evidence')
    for key, field in policy.row_receipts.items():
        expected = [item[field] for item in evidence]
        if row.get(key) != expected:
            raise ValueError('Saved public-context exposure changed')
    expected = replay(policy, row, directory, evidence)
    api.verify_result_fields(row, expected)
    if extended:
        replay(policy, row, directory, current, allow_partial=True)


def replay(policy, row, directory, evidence, allow_partial=False):
    """Reconstruct requests and verdicts from immutable attempt records."""
    # Rebuild the expected verdict from existing attempt records without
    # calling the model or checker. Return the fields the saved row must match.
    if not evidence or [item['round'] for item in evidence] != list(range(len(evidence))):
        raise ValueError('Saved evidence has missing or unexpected rounds')
    frozen, api = policy.frozen, policy.api
    budget = frozen['config']['common']['max_snippet_fixes'] + 1
    if len(evidence) > budget:
        raise ValueError('Saved result exceeds the common repair budget')
    arm = row['arm']
    case = next(case for case in frozen['bank']['cases'] if case['id'] == row['case_id'])
    # Recreate the context used for this task and compare its saved receipts
    # with what the policy would produce for the same input.
    context = policy.prepare(arm, case, directory, replay=True)
    expected = {'status': 'not_run', 'first_attempt_pass': False}
    previous = None
    for item in evidence:
        number = item['round']
        request, receipts = policy.request(arm, case, previous, number, context)
        for key in policy.receipt_files:
            label = key.replace('_', ' ')
            if key in receipts:
                if key not in item or load(item[key]['path']) != receipts[key]:
                    raise ValueError(f'Saved {label} differs from the frozen prompt')
            elif key in item:
                raise ValueError(f'Unexpected saved {label}')
        selected = selected_response(item['providers'], request)
        if selected is None:
            if item['executions'] or item.get('generation'):
                raise ValueError('Execution/generation evidence lacks a provider response')
            expected['status'] = 'provider_pending'
        else:
            response, files = selected
            executable = mark_generation(expected, response, number)
            # A crash can leave the last round with a response but no generation
            # receipt yet. Any execution evidence at that point is inconsistent.
            if allow_partial and not item.get('generation'):
                if item['executions'] or number != len(evidence) - 1:
                    raise ValueError('Saved execution/repair lacks generation evidence')
                break
            if not executable:
                if item['executions']:
                    raise ValueError('Nonexecutable generation has execution evidence')
            else:
                code = strip_code_fence(response['code'])
                # Check that the recorded execution request used this exact candidate.
                checker = policy.checker_request(arm, case, code)
                checked = None
                for attempt in item['executions']:
                    if checked is not None:
                        raise ValueError('Saved execution follows an already checked outcome')
                    records = attempt['files']
                    if 'request.json' in records and load(records['request.json']['path']) != checker:
                        raise ValueError('Saved checker candidate differs from the provider response')
                    if 'process.json' in records:
                        if 'request.json' not in records:
                            raise ValueError('Saved checker process lacks its request')
                        process = load(records['process.json']['path'])
                        outcome = policy.outcome(process, arm)
                        if outcome is not None:
                            checked = (outcome, process, records)
                if checked is None:
                    expected['status'] = 'unverified'
                else:
                    outcome, process, records = checked
                    _checked_result(expected, number, code, outcome, process, records)
                    previous = api.previous_result(code, process['payload'], policy.failure_feedback)
            # Check the receipt after matching the recorded requests to this round.
            verify_generation(item, response, files)
        # A later repair is valid only after a checked failure in this round.
        if number < len(evidence) - 1 and expected['status'] != 'fail':
            raise ValueError('Saved repair follows a stopped or already passing round')
    if not allow_partial and expected['status'] == 'fail' and len(evidence) != budget:
        raise ValueError('Saved failure has not exhausted the common repair budget')
    return expected
