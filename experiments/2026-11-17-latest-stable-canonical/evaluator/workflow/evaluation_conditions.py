"""Matched-condition context and checker policy for the shared evaluation runner."""
from functools import partial
import sys

from .evaluation_readme import (_collect_resources, _load_completed_rows,
                                previous_result, verify_result_fields)
from .evaluation_program_generation import _request_solution, model_request, rounds
from .execution import atomic_json
from .evaluation_context import public_context
from .evaluation_runner import run_study
from .evaluation_report import report_conditions, write_condition_report
from .evaluation_freeze import (checked_outcome, checker_request, execute_condition,
                               freeze_conditions, open_conditions, verify_inputs)


class _ConditionPolicy:
    """Treatment context and pinned backend checks for an explicit condition bank."""
    receipt_files = {'exposure': 'context_exposure.json'}
    row_receipts = {'context_exposures': 'exposure'}
    failure_feedback = 'Independent checks failed.'
    unknown_condition = 'Unknown study condition'
    log_progress = False

    def __init__(self, frozen):
        # Connect the shared runner to this study’s conditions, checker, and report.
        # Each result row will carry the hash of the library backend it used.
        self.frozen, self.api = frozen, sys.modules[__name__]
        self.arms = tuple(frozen['config']['conditions'])
        self.identity = {'study_sha256': frozen['study_sha256'], 'protocol': frozen['protocol']}
        self.row_fields = {arm: {'backend_sha256': frozen['backends'][arm]['sha256']} for arm in self.arms}
        self.report, self.write_report = report_conditions, write_condition_report
        self.verify_inputs = verify_inputs
        self.evidence = partial(rounds, exposure=True)

    def prepare(self, arm, case, directory, replay):
        # Treatment context is assembled per round because it can include feedback.
        # Return None because this mode rebuilds its context for each attempt.
        return None

    def request(self, arm, case, previous, number, context):
        # Turn the task and optional failure feedback into a model request.
        # Return the prompt exposure record so the runner can save it with the attempt.
        prompt, exposure = self.api.public_context(self.frozen, arm, case, previous)
        return model_request(self.frozen, prompt, number), {'exposure': exposure}

    def execute(self, arm, case, code, root):
        # Give the generated code to the checker for this condition.
        # Return its attempt directory and the saved process record.
        return self.api.execute_condition(self.frozen, arm, case, code, root)

    def checker_request(self, arm, case, code):
        # Rebuild the expected checker request for replaying a saved attempt.
        return self.api.checker_request(self.frozen, arm, case, code)

    def outcome(self, process, arm):
        # Use the expected backend hash to decide whether the checker result
        # can establish a pass or failure for this condition.
        return self.api.checked_outcome(process, self.frozen['backends'][arm]['sha256'])


def run_conditions(study, output, condition=None, max_units=None, retry_provider=False):
    """Run the shared schedule with this study's explicit treatment policies."""
    # Open the validated treatment freeze, select its policy, and let
    # the shared runner schedule tasks and return the condition summary.
    return run_study(study, output, lambda path: _ConditionPolicy(open_conditions(path)),
                     condition, max_units, retry_provider)
