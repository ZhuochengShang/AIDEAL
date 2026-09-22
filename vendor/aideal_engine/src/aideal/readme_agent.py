"""Compatibility imports for AIDEAL README development.

Implementation responsibilities now live in focused modules. Existing callers may
continue importing every original function, helper, constant, and ApiEntry here.
For changes and test patches, import the owning implementation module directly.
No discovery, generation, model request, or filesystem write runs at import time.
"""
from .readme_format import (
    API_HEADER_RE,
    ApiEntry,
    _section_between,
    parse_readme,
    _replace_section,
    _section_has_code,
    _params_block,
    _entry_skeleton,
)

from .readme_evidence import (
    _recency_key,
    _is_stale,
    _fresh,
    _augment_block,
    _grounding_tiers,
    _exec_status_map,
    grounding_report,
    organize_report,
    augment_from_log,
)

from .readme_catalogue import (
    _TIER_BADGE,
    _TIER_RANK,
    _EXEC_RANK,
    _safe_filenames,
    _catalogue_model,
    _class_context_body,
    _receiver_line,
    write_catalogue,
)

from .api_visibility import (
    _VISIBILITY_DEFAULTS,
    visibility_model,
    _is_public,
    _CONTAINER_DECL_RE,
    _NONPUBLIC_MOD_RE,
    _container_context,
    _exclude_path_patterns,
    _iter_defs,
)

from .api_examples import (
    _TEST_BLOCK_RE,
    _PY_TEST_DEF_RE,
    _iter_test_blocks_py,
    _JAVA_TEST_RE,
    _iter_test_blocks_java,
    _TEST_MINERS,
    _test_blocks_for,
    _iter_test_blocks,
    api_test_examples,
)

from .scaffold_generation import (
    _SCAFFOLD_FRAME,
    _SCAFFOLD_BASE_IMPORTS,
    _available_packages,
    _import_package,
    _on_classpath,
    _TEST_FRAMEWORK_IMPORT,
    _imports_from_tests,
    _pkgobject_reexported_wildcards,
    _source_symbol_index,
    _defining_object_imports,
    generate_scaffold,
)

from .api_intent import (
    _BOILERPLATE_NAMES,
    _INTERNAL_PATH_SEGMENTS,
    _DEFAULT_INTENT_WEIGHTS,
    llm_common_apis,
    intended_api_llm,
    _names_called_in,
    _doc_code_mentions,
    intent_scores,
    intent_compare,
)

from .api_overloads import (
    _subsume_overloads,
    _dedup_deprioritize,
    dedup_report,
)

from .api_signatures import (
    _split_top_level,
    _param_record,
    _java_param_record,
    _JAVA_MEMBER_MODIFIERS,
    _java_return_type,
    _signature_at,
    _doc_below_py,
    _DOC_POSITION,
    _doc_at,
    _doc_above,
    _python_module_name,
    _python_qualified_identities,
)

from .api_discovery import (
    public_api_surface,
    public_api_details,
    render_api_surface,
    surface_audit,
    api_coverage,
)

from .readme_generation import (
    distilled_readme_context,
    _original_readme_snippets,
    find_or_create,
)
