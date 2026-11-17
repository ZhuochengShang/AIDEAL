"""Compatibility entry point for the AIDEAL documentation-check pipeline.

Implementations live in focused doc_check_* modules. Public check functions and
shared private helpers retain their names and call signatures.
Native execution semantics and prompts remain separate from workflow/evaluation.py.
"""
from __future__ import annotations

from .doc_check_provenance import (
    _sha256_files,
    _comprehension_fingerprint_components,
    _checkpoint_row_reusable,
)
from .doc_check_sources import (
    form_check,
    _load_manifest,
    _shared_doc_text,
    _markdown_chunks,
    _relevant_original_texts,
    _relevant_doc_inventory,
    _comprehension_inventory,
    _build_catalogue_context,
    _resolve_class_context,
    _normalize,
    completeness_check,
)
from .doc_check_inputs import (
    _fill_scaffold,
    _strip_fences,
    _kind_of,
    _validate_sample_data,
    _discover_fixtures,
    _base_type,
    _consumed_type_counts,
    _useful_readers,
    _drop_unconsumed_lines,
    _resolve_preamble,
    _resolve_io_hints,
    _execute_sample_data,
    _owner_map,
    _receiver_hint,
    _FIXTURE_TYPES,
    _SUFFIXES_FOR_TYPE,
)
from .doc_check_errors import (
    _classify_error_py,
    _classify_error_java,
    _classify_error,
    _codebase_frames,
    _FRAME_RE,
)
from .doc_check_comprehension import (
    comprehension_check,
)
from .doc_check_execution import (
    _comprehension_execute,
)
from .doc_check_puzzles import (
    puzzle_check,
)
