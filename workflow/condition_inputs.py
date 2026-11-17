"""Compatibility import for saved preparation scripts. Review evaluation_inputs.py."""
import sys
from . import evaluation_inputs as _implementation

# Old imports and the current evaluator share the same implementation object.
sys.modules[__name__] = _implementation
