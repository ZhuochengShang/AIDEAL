"""Evaluate prepared README versions and share result/checkpoint helpers.

The schedule, repair loop and replay live in evaluation_runner.py.
Candidate program requests live in evaluation_program_generation.py.
"""
from pathlib import Path
import sys
import re

from .ablation import digest, load, verify_artifact
from .execution import atomic_json
from .evaluation_setup import (
    CONDITIONS, SYSTEM, adapter_request, verified_outcome,
    read_config, validate_bank, freeze_evaluation, open_frozen,
    _checked_execution,
)
from .evaluation_report import report, write_report
from .evaluation_program_generation import _request_solution, model_request, rounds
from .repair_context import compact_previous, public_failure
from .evaluation_runner import run_study

# Setup functions remain importable here for existing study launchers. They are
# imports, not second implementations; new callers may import evaluation_setup.

def audience_prompt(case, documentation, previous=None):
    # Input: a public task contract, selected documentation and optional repair
    # feedback. Return the text body that the provider adapter will send.
    # Only explicit public fields are selected; private oracle paths are excluded.
    """Build public model context; exclude oracle paths and reference answers."""
    # Put the task, shared contract, and selected documentation into
    # separate sections. When repairing, append the last program and feedback.
    sections = ['TASK\n' + case['prompt'], 'SHARED CONTRACT\n' + case.get('public_context', ''),
                'DOCUMENTATION\n' + documentation]
    if previous:
        sections += ['COMPLETE PREVIOUS SOLUTION\n' + previous['code'],
                     'EXECUTION FEEDBACK\n' + previous['feedback']]
    return '\n\n'.join(sections)


def select_documentation(paths, targets, max_characters):
    """Same deterministic heading retrieval for every condition; log actual exposure.

    Short documents are delivered in full. Long documents rank level-two sections
    by exact API-name mentions, with stable file order breaking ties. No LLM
    selects text, and no test answer enters retrieval.
    """
    # Return both the text the model sees and a receipt containing
    # selected section indexes, character counts, and the delivered text hash.
    text = '\n\n'.join(Path(p).read_text() for p in paths)
    chunks = re.split(r'(?m)(?=^## )', text)
    selected = []
    if len(text) <= max_characters:
        delivered = text
        selected = list(range(len(chunks)))
    else:
        def relevance(index):
            # Count whole target names in this section. The outer sort prefers
            # higher counts and breaks ties by the original section order.
            return sum(len(re.findall(r'(?<!\w)' + re.escape(t) + r'(?!\w)', chunks[index])) for t in targets)
        order = sorted(range(len(chunks)), key=lambda i: (-relevance(i), i))
        delivered = ''
        for i in order:
            remaining = max_characters - len(delivered)
            if remaining <= 2:
                break
            delivered += ('\n\n' if delivered else '') + chunks[i][:remaining - 2]
            selected.append(i)
    return delivered, {'source_characters': len(text), 'delivered_characters': len(delivered),
                       'selected_section_indices': selected, 'truncated': len(delivered) < len(text),
                       'delivered_sha256': digest(delivered)}


class _ReadmePolicy:
    """Documentation selection and checks for Original/Generated/Repaired README."""
    receipt_files = {'repair_context': 'repair_context.json'}
    row_receipts = {}
    failure_feedback = 'Independent checks did not pass.'
    unknown_condition = 'Unknown documentation condition'
    log_progress = True

    def __init__(self, frozen):
        # Use the three README versions as arms. They share a checker, so
        # there is no separate backend hash to add to each arm’s result row.
        self.frozen, self.api = frozen, sys.modules[__name__]
        self.arms = CONDITIONS
        self.identity = {'study_sha256': frozen['study_sha256']}
        self.row_fields = {arm: {} for arm in self.arms}
        self.report, self.write_report = report, write_report
        self.verify_inputs, self.evidence = _verify_readme_inputs, rounds

    def prepare(self, arm, case, directory, replay):
        # Select documentation for this condition, task, and trial. Save its
        # exposure on a live run, or compare it with the receipt during replay.
        cfg = self.frozen['config']
        docs, exposure = self.api.select_documentation(cfg['documents'][arm], case['target_apis'],
                                                       cfg['common'].get('documentation_max_characters', 32000))
        path = directory / 'documentation_exposure.json'
        if replay:
            if load(path) != exposure:
                raise ValueError('Saved documentation exposure differs from the frozen prompt')
        else:
            self.api.atomic_json(path, exposure)
        return docs

    def request(self, arm, case, previous, number, documentation):
        # Build the provider request from the selected README and any
        # previous failed attempt. Save a receipt when feedback is distilled.
        receipts = {}
        common = self.frozen['config']['common']
        if previous and common.get('repair_context') == 'distilled':
            previous, receipts['repair_context'] = compact_previous(previous)
        prompt = self.api.audience_prompt(case, documentation, previous)
        return model_request(self.frozen, prompt, number), receipts

    def execute(self, arm, case, code, root):
        # Check the generated program with the study’s shared adapter and
        # return the attempt directory and process record.
        return self.api._checked_execution(self.frozen['config'], case, code, root, prefix='execution_')

    def checker_request(self, arm, case, code):
        # Rebuild the expected private checker request from the task and code.
        # All README arms use the same request format and checker.
        return self.api.adapter_request(case, code)

    def outcome(self, process, arm):
        # Translate the checker flags into True, False, or None. This mode
        # uses a shared backend, so the arm does not affect that interpretation.
        return self.api.verified_outcome(process)


def run_evaluation(study, output, condition=None, max_units=None, retry_provider=False):
    """Run the shared schedule with the three-README context and checker policy."""
    # Open the README freeze, create its policy, and run the common
    # condition-by-task-by-trial schedule. Return the report summary.
    return run_study(study, output, lambda path: _ReadmePolicy(open_frozen(path)),
                     condition, max_units, retry_provider)


def _verify_readme_inputs(frozen):
    """Do not publish a verdict or execute against inputs changed during a call."""
    # Check the file bindings recorded in the freeze again. A mismatch
    # stops the runner before it can use the external call’s output.
    if not all(verify_artifact(ref) for ref in frozen.get('artifacts', [])):
        raise ValueError('Study inputs changed while running')


def _load_completed_rows(output):
    """Read only unit checkpoints and reject duplicates before another model call."""
    # Index saved result rows by condition, task, and trial. The path
    # must agree with the row’s identifiers so resume finds the correct task.
    rows = {}
    for path in output.glob('*/*/result.json'):
        row = load(path)
        key = (row['arm'], row['case_id'], row['trial_id'])
        if key in rows:
            raise ValueError(f'Duplicate saved result: {key}')
        expected = output / key[0] / f'{key[1]}--{key[2]}' / 'result.json'
        if path != expected:
            raise ValueError(f'Saved result does not match its directory: {path}')
        rows[key] = row
    return rows


def previous_result(code, payload, fallback='Independent checks failed.'):
    # Return the candidate and the checker’s public feedback for repair.
    # Attach a failure attribution only if public_failure accepts it.
    previous = {'code': code, 'feedback': payload.get('public_feedback', fallback)}
    failure = public_failure(payload)
    if failure is not None:
        previous['public_failure'] = failure
    return previous


_RESULT_FIELDS = ('status', 'first_attempt_pass', 'first_pass_round', 'last_checked_round',
                  'code_sha256', 'adjudication', 'execution_pass', 'oracle_pass', 'target_reached',
                  'generation_status', 'generation_reason', 'last_generation_round')


def verify_result_fields(row, expected):
    # Compare both the presence and value of each verdict field.
    # A missing field differs from a field explicitly saved with value None.
    for key in _RESULT_FIELDS:
        if (key in row) != (key in expected) or row.get(key) != expected.get(key):
            raise ValueError('Saved result differs from the replayed generation/checker verdict: ' + key)


def _collect_resources(evidence):
    """Count the saved attempts, including interrupted calls with unknown usage."""
    # Walk the captured attempt records for time and reported token usage.
    # Count every provider attempt even if its process record is missing.
    resources = {'provider_calls': 0, 'provider_seconds': 0, 'execution_seconds': 0,
                 'reported_input_tokens': 0, 'reported_output_tokens': 0, 'calls_without_usage': 0}
    providers = [attempt['files'].get('process.json', {}).get('path')
                 for item in evidence for attempt in item['providers']]
    executions = [attempt['files']['process.json']['path']
                  for item in evidence for attempt in item['executions']
                  if 'process.json' in attempt['files']]
    for p in providers:
        resources['provider_calls'] += 1
        proc = load(p) if p is not None else {}
        resources['provider_seconds'] += proc.get('seconds', 0)
        payload = proc.get('payload')
        usage = payload.get('usage') if isinstance(payload, dict) else None
        usage = usage if isinstance(usage, dict) else {}
        if not all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('input_tokens', 'output_tokens')):
            resources['calls_without_usage'] += 1
        else:
            resources['reported_input_tokens'] += usage['input_tokens']
            resources['reported_output_tokens'] += usage['output_tokens']
    for p in executions:
        resources['execution_seconds'] += load(p)['seconds']
    return resources
