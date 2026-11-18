"""Compatibility import. Start reviewing evaluation_conditions.py instead."""
import sys
from . import evaluation_conditions as _implementation
from .evaluation_conditions import (
    _ConditionPolicy,
    run_conditions,
    freeze_conditions,
    open_conditions,
)

# Keep imports and monkeypatches on the same implementation object.
sys.modules[__name__] = _implementation
