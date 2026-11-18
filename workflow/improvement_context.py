"""Explicit, bounded development inputs; never import or execute library code."""
from dataclasses import replace
import glob
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

from .ablation import bind, digest, load, verify_artifact
from .execution import atomic_json
from .preparation import _engine_config_module
from .treatment_versions import _run as _git, _check_worktree


def alias_target(value):
    # Return a normalized relative path for a supported source file, or None if
    # aliases were not requested.
    if value is None:
        return None
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('Alias destination must be a relative source filename')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')) or any(p.startswith('.') for p in path.parts):
        raise ValueError('Alias destination cannot escape the source tree or use hidden paths')
    if path.suffix not in ('.py', '.scala', '.java', '.rs'):
        raise ValueError('Alias destination needs a supported source extension')
    return path.as_posix()


def original_checkout(study):
    # Resolve the recorded Original checkout, then check that its path, branch,
    # commit, and on-disk files match the baseline.
    study = Path(study).resolve()
    attachment = load(study / 'attachment.json')
    item = attachment['worktrees']['original']
    root = Path(item['path']).resolve()
    expected = study / 'Original' / 'source'
    if root != expected.resolve() or not root.is_relative_to(study):
        raise ValueError('Original worktree is outside the attached study')
    if _git(root, 'rev-parse', 'HEAD') != attachment['revision']:
        raise ValueError('Original worktree no longer matches the pinned baseline')
    if _git(root, 'branch', '--show-current') != 'aideal/original':
        raise ValueError('Original worktree branch changed')
    # Raw index/file comparisons avoid invoking repository clean filters or
    # filesystem-monitor hooks while inspecting source for a model preview.
    _check_worktree(root, attachment['revision'], {})
    return study, root, attachment


def development_destination(study, output):
    """Keep preview/proposal outputs outside all library source checkouts."""
    # Resolve the requested output and compare it with the original repository and
    # every attached worktree.
    output = Path(output).resolve()
    attachment = load(Path(study) / 'attachment.json')
    roots = [Path(attachment['repository']).resolve()]
    roots.extend(Path(item['path']).resolve() for item in attachment['worktrees'].values())
    if any(output == root or output.is_relative_to(root) for root in roots):
        raise ValueError('Development outputs must be outside source checkouts')
    return output


def _development_errors(path, definitions, max_characters=12000):
    """Only explicit development logs; never read a held-out bank or its oracles."""
    # Return selected log rows, a hash binding for the log file, and a count of
    # skipped rows. An absent log contributes no evidence.
    if path is None:
        return [], None, 0
    path = Path(path).resolve()
    rows, omitted, used = [], 0, 0
    by_name = {}
    for definition in definitions:
        labels = [definition['name'], definition['qualified_name'], definition['id']]
        labels += [definition.get('source_function_id'), *definition.get('exposure_ids', []),
                   *definition.get('public_access_paths', [])]
        for name in filter(None, labels):
            by_name.setdefault(name, set()).add(definition['id'])
    # Match each failure to one API and keep only bounded text from the development
    # log.
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f'Development log line {number} must be an object')
        metadata = record.get('metadata') or {}
        if not isinstance(metadata, dict):
            raise ValueError('Development log metadata must be an object')
        if any(str(obj.get(key, '')).lower() in ('held_out', 'held-out', 'evaluation', 'test')
               for obj in (record, metadata) for key in ('split', 'phase', 'scope')):
            raise ValueError('Held-out/evaluation failures cannot train development hints')
        if record.get('status') not in ('fail', 'fixed'):
            omitted += 1
            continue
        if not isinstance(record.get('function'), str):
            raise ValueError('Development log function must be text')
        candidates = by_name.get(record['function'], set())
        if len(candidates) != 1:
            omitted += 1  # Ambiguous overloads need a qualified location ID.
            continue
        item = {'id': f'error-{number}', 'function_id': next(iter(candidates)),
                'status': record['status']}
        for key in ('error', 'root_cause', 'code', 'suggested_fix_code'):
            value = record.get(key, '')
            if not isinstance(value, str):
                raise ValueError(f'Development log {key} must be text')
            item[key] = value[:2500]
        size = len(json.dumps(item, ensure_ascii=False))
        if used + size > max_characters:
            omitted += 1
            continue
        used += size
        rows.append(item)
    return rows, bind(path), omitted


def _select_library_apis(definitions, apis):
    """Select explicit identities; qualified-mode shorthand must be unambiguous."""
    if not apis:
        return definitions
    if not any(row.get('api_id') for row in definitions):
        selected = [row for row in definitions if {row['id'], row['name'], row['qualified_name']}.intersection(apis)]
        known = {row[key] for row in selected for key in ('id', 'name', 'qualified_name')}
        if set(apis) - known:
            raise ValueError('Requested API not found: ' + ', '.join(sorted(set(apis) - known)))
        return selected
    exact = {row['id']: row for row in definitions}
    selected = set()
    for requested in apis:
        if requested in exact:
            selected.add(requested)
            continue
        matches = [row for row in definitions if requested in {
            row['name'], row['qualified_name'], row.get('source_function_id'),
            *row.get('public_access_paths', []), *row.get('exposure_ids', [])}]
        if not matches:
            raise ValueError('Requested API not found: ' + requested)
        if len(matches) != 1:
            raise ValueError('Ambiguous API shorthand; use one exact API ID: ' + ', '.join(row['id'] for row in matches))
        selected.add(matches[0]['id'])
    return [row for row in definitions if row['id'] in selected]


def _qualified_library_definitions(cfg, root, tracked):
    """Discover on pinned provenance, then byte-check the attached source copy.

    The attached checkout has an instrumentation commit. It is not the pristine
    inventory root, so changing cfg.root would invalidate both inventory and
    documentation bindings. Only verified defining files are relocated here.
    """
    from aideal.api_discovery import public_api_details
    from aideal.api_registry import target_key
    from aideal.original_documentation import original_document_paths
    codebase = cfg.raw.get('codebase', {})
    locator = codebase.get('api_inventory')
    if not locator:
        raise ValueError('Qualified development requires a hash-bound source inventory')
    inventory_path = (cfg.root / locator).resolve(strict=True)
    inventory_ref = bind(inventory_path)
    if inventory_ref['sha256'] != codebase.get('api_inventory_sha256'):
        raise ValueError('Qualified development inventory checksum differs from configuration')
    inventory = load(inventory_path)
    # Registry discovery validates manifests, receipts and pristine source first.
    discovered = public_api_details(cfg)
    if inventory.get('kind') == 'registered_sql':
        raise ValueError('Registered SQL documentation is not implementation source; a reviewed native registration adapter is required for alias/hint development')
    source_root = inventory.get('source_root')
    if not source_root:
        raise ValueError('Qualified development inventory needs its pinned source_root')
    pinned = (cfg.root / source_root).resolve(strict=True)
    refs = [inventory_ref, *[bind(path) for path in original_document_paths(cfg)]]
    for field in ('source_inventory', 'canonical_selection', 'parser_contract'):
        if inventory.get(field):
            refs.append(bind((cfg.root / inventory[field]).resolve(strict=True)))
    definitions = []
    for row in discovered:
        if row['visibility'] != 'public' and row.get('public_exposure_established') is not True:
            continue
        original_path = (cfg.root / (row.get('defining_file') or row['file'])).resolve(strict=True)
        if not original_path.is_relative_to(pinned):
            raise ValueError('API defining source escapes the pinned inventory root')
        relative = original_path.relative_to(pinned).as_posix()
        candidate = root / relative
        if (relative not in tracked or '.aideal' in Path(relative).parts or candidate.is_symlink()
                or not candidate.is_file() or not candidate.resolve().is_relative_to(root)):
            raise ValueError('API defining source is not an ordinary tracked attached file: ' + relative)
        original_bytes, attached_bytes = original_path.read_bytes(), candidate.read_bytes()
        source_hash = hashlib.sha256(original_bytes).hexdigest()
        if (source_hash != (row.get('source_sha256') or row.get('file_sha256'))
                or attached_bytes != original_bytes):
            raise ValueError('Attached defining source differs from the pinned inventory: ' + relative)
        # Source patchers use path:line:name, independently of the public API ID.
        # Python's parser also validates its lexical module/class ownership.
        source_name = row['qualified_name'] if candidate.suffix == '.py' else row['name']
        identity = target_key(row)
        definitions.append({**row, 'id': identity, 'file': relative,
            'source_function_id': f"{relative}:{row['line']}:{source_name}",
            'source_discovery': {'api_id': identity, 'pinned_file': str(original_path),
                                 'attached_file': relative, 'file_sha256': source_hash,
                                 'mapping': 'identical_bytes_in_tracked_attached_source'}})
        refs.append(bind(original_path))
    if not all(verify_artifact(ref) for ref in refs):
        raise ValueError('Pinned development provenance changed during discovery')
    return definitions, list({ref['path']: ref for ref in refs}.values())


def _library_inputs(study, apis=None):
    """Discover the full pinned public surface without importing target code."""
    # Verify the saved configuration, then map its source patterns into the pinned
    # Original worktree before discovering APIs.
    study, root, attachment = original_checkout(study)
    source = load(study / 'source.json')
    refs = source['configuration_layers']
    if not all(verify_artifact(ref) for ref in refs):
        raise ValueError('Configuration changed since attachment')
    cfg = _engine_config_module().load_config(source['configuration']['path'])
    engine_path = str(Path(__file__).resolve().parents[1] / 'vendor/aideal_engine/src')
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    tracked = set(_git(root, 'ls-files', '-z').split('\x00'))
    if cfg.raw.get('codebase', {}).get('identity_mode') == 'qualified':
        definitions, provenance_refs = _qualified_library_definitions(cfg, root, tracked)
        definitions = _select_library_apis(definitions, apis)
        definitions.sort(key=lambda row: (row['file'], row['line'], row['id']))
        if not definitions or len({row['id'] for row in definitions}) != len(definitions):
            raise ValueError('Qualified discovery returned no APIs or duplicate defining identities')
        return study, root, attachment, cfg, definitions, refs + provenance_refs
    repository = Path(attachment['repository']).resolve()
    patterns = []
    for pattern in cfg.source_globs:
        absolute = (cfg.root / pattern).resolve()
        if not absolute.is_relative_to(repository):
            raise ValueError('Configured source pattern escapes the pinned repository')
        patterns.append(str(root / absolute.relative_to(repository)))
    files = sorted({Path(p) for pattern in patterns for p in glob.glob(pattern, recursive=True)
                    if Path(p).is_file()})
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Source symlinks are not allowed in development context')
    files = [p for p in files if p.relative_to(root).as_posix() in tracked
             and '.aideal' not in p.relative_to(root).parts]
    if not files:
        raise ValueError('No tracked source files match the configured patterns')
    from aideal.api_discovery import public_api_details
    # Resolve discovery inside the pinned checkout, not the caller's mutable repo.
    local = replace(cfg, root=root, source_globs=[glob.escape(str(p)) for p in files], test_globs=[])
    definitions = []
    for row in public_api_details(local):
        if row['visibility'] != 'public':
            continue
        row = {**row, 'id': f"{row['file']}:{row['line']}:{row['qualified_name']}"}
        if apis and not {row['id'], row['qualified_name'], row['name']}.intersection(apis):
            continue
        definitions.append(row)
    definitions.sort(key=lambda r: (r['file'], r['line'], r['id']))
    if apis:
        known = {r[k] for r in definitions for k in ('id', 'qualified_name', 'name')}
        if set(apis) - known:
            raise ValueError('Requested API not found: ' + ', '.join(sorted(set(apis) - known)))
    if not definitions:
        raise ValueError('No public APIs discovered; configure a language adapter/definition pattern')
    if len({row['id'] for row in definitions}) != len(definitions):
        raise ValueError('Discovery returned duplicate function IDs')
    return study, root, attachment, cfg, definitions, refs


def _semantic_context(cfg, root, attachment):
    """Expose discovery semantics and explicit profile, never model credentials."""
    # Resolve the configured profile path and record the supplied profile plus
    # discovery settings for use in the prompt.
    configured = Path(cfg.raw.get('files', {}).get('project_profile', 'configs/project_profile.yaml'))
    path = (cfg.root / configured).resolve()
    repository = Path(attachment['repository']).resolve()
    if path.is_relative_to(repository):
        path = root / path.relative_to(repository)
    profile, refs = {}, []
    if path.exists():
        if path.is_symlink() or (path.is_relative_to(root) and not path.resolve().is_relative_to(root)):
            raise ValueError('Profile symlinks cannot escape the pinned source tree')
        profile = _engine_config_module().yaml.safe_load(path.read_text()) or {}
        if not isinstance(profile, dict):
            raise ValueError('Project profile must be a mapping')
        refs.append(bind(path))
    config = {'source_globs': cfg.source_globs, 'test_globs': cfg.test_globs,
              'public_def_regex': cfg.public_def_regex, 'exclude_names': cfg.exclude_names,
              'visibility': cfg.visibility, 'surface_filter': cfg.surface_filter,
              'exclude_path_patterns': cfg.raw.get('codebase', {}).get('exclude_path_patterns', []),
              'discovery_scope': 'All discovered public definitions in tracked configured sources; no LLM intent filter.'}
    return {'configuration': config, 'project_profile': profile,
            'profile_status': 'supplied' if profile else 'not_supplied'}, refs


def _source_windows(root, definitions):
    """Capture bounded literal source evidence, keyed by original function ID."""
    # Attach a short literal excerpt and its line numbers to each definition. Read and
    # bind each source file once.
    refs, file_lines = {}, {}
    for row in definitions:
        path = root / row['file']
        if row['file'] not in file_lines:
            if row.get('source_discovery'):
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != row['source_discovery']['file_sha256']:
                    raise ValueError('Attached source changed before source-window capture')
                file_lines[row['file']] = data.decode('utf-8').splitlines()
            else:
                file_lines[row['file']] = path.read_text().splitlines()
            refs[row['file']] = bind(path)
            if row.get('source_discovery') and refs[row['file']]['sha256'] != row['source_discovery']['file_sha256']:
                raise ValueError('Attached source changed during source-window capture')
        lines = file_lines[row['file']]
        first, last = max(0, row['line'] - 4), min(len(lines), row['line'] + 60)
        row['source_window'] = {'start_line': first + 1, 'end_line': last,
                                'text': '\n'.join(lines[first:last]),
                                'complete_file': first == 0 and last == len(lines)}
        # Preserve package/import/container declarations needed to place a new
        # module correctly. These are observed lines, not an inferred receiver.
        candidates = [(i + 1, line) for i, line in enumerate(lines[:row['line']])
                      if re.match(r'^\s*(?:(?:public|final|abstract|sealed|case)\s+)*'
                                  r'(?:package|import|from|class|object|trait|impl|mod)\b', line)]
        candidates.sort(key=lambda item: (bool(re.match(r'^\s*(?:import|from)\b', item[1])), item[0]))
        declaration_text = '\n'.join(f'{i}: {line}' for i, line in candidates)
        row['declaration_context'] = {
            'text': declaration_text[:2000], 'source_characters': len(declaration_text),
            'truncated': len(declaration_text) > 2000,
            'meaning': 'Preceding declaration lines; lexical observations, not proof of nesting or receiver identity.'}
    return list(refs.values())



def compact_api_context(definitions):
    """Keep calling facts and literal source; leave audit graphs in bound evidence.

    Exact signatures and source windows are never shortened. A preferred public
    access path plus at most seven alternatives is enough to orient a wrapper;
    the full exposure graph remains recoverable from api_evidence.json.
    """
    fields = (
        'id', 'api_id', 'name', 'qualified_name', 'source_function_id', 'file', 'line', 'end_line',
        'signature', 'kind', 'definition_kind', 'language', 'source_language', 'module',
        'scope', 'owner', 'defining_owner', 'defining_owner_kind', 'params', 'parameters',
        'parameter_count', 'parameter_count_status', 'returns', 'decorators',
        'implicit_receiver', 'public_owner_chain', 'conditional_context', 'is_abstract',
        'public_exposure_established', 'source_window', 'declaration_context', 'preferred_public_path')
    result = []
    for row in definitions:
        value = {key: row[key] for key in fields if key in row}
        paths = row.get('public_access_paths') or [p.rsplit(':', 1)[-1] for p in row.get('exposure_ids', [])]
        preferred = row.get('preferred_public_path')
        paths = list(dict.fromkeys(([preferred] if preferred else []) + list(paths)))
        value['public_access_paths'] = paths[:8]
        value['omitted_public_access_paths'] = max(0, len(paths) - 8)
        description = row.get('description')
        if isinstance(description, str):
            value['description'] = description[:2000]
            value['description_characters'] = len(description)
            value['description_truncated'] = len(description) > 2000
        result.append(value)
    return result


def _hint_identity_fields(definitions):
    """Bridge qualified evaluation targets to exact source-edit locations."""
    if not any(row.get('api_id') for row in definitions):
        return {}
    return {'api_function_ids': {row['id']: row['source_function_id'] for row in definitions},
            'api_public_paths': {row['id']: row.get('public_access_paths') or
                                 [path.rsplit(':', 1)[-1] for path in row.get('exposure_ids', [])]
                                 for row in definitions}}


def preview_improvements(study, output, *, alias_path=None, apis=None, development_errors=None,
                         max_apis=12, max_context_characters=60000):
    """Save the exact development context before any model command is permitted."""
    # Prepare one preview for a small API selection. Save the prompt data and input
    # hashes for the later proposal command.
    if type(max_apis) is not int or not 1 <= max_apis <= 100:
        raise ValueError('max_apis must be between 1 and 100')
    if type(max_context_characters) is not int or not 1000 <= max_context_characters <= 250000:
        raise ValueError('max_context_characters must be between 1000 and 250000')
    study, root, attachment, cfg, definitions, refs = _library_inputs(study, apis)
    target = alias_target(alias_path)
    if target and (root / target).exists():
        raise ValueError('Aliases must be a new source module, not replace baseline code')
    available = len(definitions)
    selected = definitions[:max_apis]
    if not selected:
        raise ValueError('No public APIs discovered; configure a language adapter/definition pattern')
    selected_refs = _source_windows(root, selected)
    semantics, profile_refs = _semantic_context(cfg, root, attachment)
    errors, error_ref, omitted = _development_errors(development_errors, selected)
    model_apis = compact_api_context(selected)
    context = {'project': cfg.project_name, 'language': cfg.language,
               'baseline_revision': attachment['revision'], 'alias_destination': target,
               'apis': model_apis, 'development_errors': errors, **semantics, **_hint_identity_fields(model_apis),
               'coverage': {'matching_definitions': available, 'selected_definitions': len(selected),
                            'omitted_definitions': available - len(selected), 'omitted_error_rows': omitted,
                            'source_window_policy': 'Three preceding lines and up to sixty following lines; not the full codebase.'}}
    if len(json.dumps(context, ensure_ascii=False, indent=2)) > max_context_characters:
        raise ValueError('Context exceeds budget; select fewer APIs or raise max_context_characters')
    output = development_destination(study, output)
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'api_evidence.json', {'schema_version': 1, 'apis': selected})
    evidence = bind(output / 'api_evidence.json')
    preview = {'schema_version': 1, 'study': str(study), 'source_root': str(root),
               'baseline_revision': attachment['revision'], 'context': context,
               'api_evidence': evidence, 'context_policy': 'calling-facts-and-source-v1',
               'artifacts': selected_refs + refs + profile_refs + [evidence] + ([error_ref] if error_ref else []),
               'error_scope': 'operator-designated development logs only',
               'llm_calls': 0}
    preview['preview_sha256'] = digest(preview)
    atomic_json(output / 'preview.json', preview)
    return {'preview': str(output / 'preview.json'), 'llm_calls': 0, 'coverage': context['coverage']}
