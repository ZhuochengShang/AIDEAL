"""Compatibility import. Start reviewing evaluation_readme.py instead."""
import sys
from . import evaluation_readme as _implementation
from .evaluation_readme import (
    audience_prompt,
    select_documentation,
    _ReadmePolicy,
    run_evaluation,
    _verify_readme_inputs,
    _load_completed_rows,
    _request_solution,
    previous_result,
    verify_result_fields,
    _collect_resources,
    CONDITIONS,
    SYSTEM,
    read_config,
    validate_bank,
    freeze_evaluation,
    open_frozen,
)

# Keep imports and monkeypatches on the same implementation object.
sys.modules[__name__] = _implementation
