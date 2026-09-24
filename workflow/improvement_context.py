"""Explicit, bounded development inputs; never import or execute library code."""
from dataclasses import replace
from functools import lru_cache
import glob
import json
from pathlib import Path, PurePosixPath
import re
import sys

from .ablation import bind, digest, load, verify_artifact
from .execution import atomic_json
from .preparation import _engine_config_module
from .treatment_versions import _run as _git, _check_worktree
from .scala_owners import _tokens as _scala_tokens, owner_at_line


def alias_target(value):
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
    output = Path(output).resolve()
    attachment = load(Path(study) / 'attachment.json')
    roots = [Path(attachment['repository']).resolve()]
    roots.extend(Path(item['path']).resolve() for item in attachment['worktrees'].values())
    if any(output == root or output.is_relative_to(root) for root in roots):
        raise ValueError('Development outputs must be outside source checkouts')
    return output


def _development_errors(path, definitions, max_characters=12000):
    """Only explicit development logs; never read a held-out bank or its oracles."""
    if path is None:
        return [], None, 0
    path = Path(path).resolve()
    rows, omitted, used = [], 0, 0
    by_name = {}
    for definition in definitions:
        for name in (definition['name'], definition['qualified_name'], definition['id']):
            by_name.setdefault(name, set()).add(definition['id'])
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


@lru_cache(maxsize=128)
def _scala_package(source):
    """Accept leading, unbraced package declarations; ignore comments/literals."""
    tokens = _scala_tokens(source)
    cursor, packages = 0, []
    while cursor < len(tokens) and tokens[cursor].value == 'package':
        line = tokens[cursor].line
        cursor += 1
        parts = []
        while cursor < len(tokens) and tokens[cursor].line == line and tokens[cursor].value != ';':
            parts.append(tokens[cursor].value)
            cursor += 1
        if (not parts or any(not re.fullmatch(r'[A-Za-z_$][\w$]*', part)
                             for part in parts[::2])
                or len(parts) % 2 != 1 or any(part != '.' for part in parts[1::2])):
            raise ValueError('Unsupported Scala package declaration')
        packages.append(''.join(parts))
        if cursor < len(tokens) and tokens[cursor].value == ';':
            cursor += 1
    if any(token.value == 'package' for token in tokens[cursor:]):
        raise ValueError('Non-leading Scala package declarations require explicit resolution')
    return '.'.join(packages)


def _scala_receiver_facts(source, line, name):
    """Add lexical facts without redefining discovery identity or public scope."""
    facts = dict.fromkeys(('receiver', 'owner_kind', 'owner_path', 'qualified_receiver',
                           'source_qualified_name', 'owner_declaration'))
    try:
        owner = owner_at_line(source, line, name)
        package = _scala_package(source)
    except ValueError as exc:
        return {**facts, 'qualification_status': 'unresolved', 'qualification_reason': str(exc)}
    qualified = '.'.join(filter(None, (package, owner['owner_path'])))
    declaration_line = owner['declaration_line']
    return {**owner, 'qualified_receiver': qualified,
            'source_qualified_name': qualified + '.' + name,
            'owner_declaration': {'line': declaration_line,
                                  'text': source.splitlines()[declaration_line - 1]},
            'qualification_status': 'resolved_lexical',
            'qualification_reason': 'Direct named-owner member; not a type, visibility or dispatch proof.'}


def _library_inputs(study, apis=None):
    """Discover the full pinned public surface without importing target code."""
    study, root, attachment = original_checkout(study)
    source = load(study / 'source.json')
    refs = source['configuration_layers']
    if not all(verify_artifact(ref) for ref in refs):
        raise ValueError('Configuration changed since attachment')
    cfg = _engine_config_module().load_config(source['configuration']['path'])
    repository = Path(attachment['repository']).resolve()
    patterns = []
    for pattern in cfg.source_globs:
        absolute = (cfg.root / pattern).resolve()
        if not absolute.is_relative_to(repository):
            raise ValueError('Configured source pattern escapes the pinned repository')
        patterns.append(str(root / absolute.relative_to(repository)))
    tracked = set(_git(root, 'ls-files', '-z').split('\x00'))
    files = sorted({Path(p) for pattern in patterns for p in glob.glob(pattern, recursive=True)
                    if Path(p).is_file()})
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Source symlinks are not allowed in development context')
    files = [p for p in files if p.relative_to(root).as_posix() in tracked
             and '.aideal' not in p.relative_to(root).parts]
    if not files:
        raise ValueError('No tracked source files match the configured patterns')
    engine_path = str(Path(__file__).resolve().parents[1] / 'vendor/aideal_engine/src')
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    from aideal.api_discovery import public_api_details
    # Resolve discovery inside the pinned checkout, not the caller's mutable repo.
    local = replace(cfg, root=root, source_globs=[glob.escape(str(p)) for p in files], test_globs=[])
    definitions, scala_sources = [], {}
    for row in public_api_details(local):
        if row['visibility'] != 'public':
            continue
        row = {**row, 'id': f"{row['file']}:{row['line']}:{row['qualified_name']}"}
        if apis and not {row['id'], row['qualified_name'], row['name']}.intersection(apis):
            continue
        if Path(row['file']).suffix == '.scala':
            if row['file'] not in scala_sources:
                scala_sources[row['file']] = (root / row['file']).read_text()
            # Keep the original id/qualified_name and selection semantics. These
            # additional facts disambiguate receivers for the model only.
            row.update(_scala_receiver_facts(scala_sources[row['file']], row['line'], row['name']))
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
    refs, file_lines = {}, {}
    for row in definitions:
        path = root / row['file']
        if row['file'] not in file_lines:
            file_lines[row['file']] = path.read_text().splitlines()
            refs[row['file']] = bind(path)
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


def preview_improvements(study, output, *, alias_path=None, apis=None, development_errors=None,
                         max_apis=12, max_context_characters=60000):
    """Save the exact development context before any model command is permitted."""
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
    context = {'project': cfg.project_name, 'language': cfg.language,
               'baseline_revision': attachment['revision'], 'alias_destination': target,
               'apis': selected, 'development_errors': errors, **semantics,
               'coverage': {'matching_definitions': available, 'selected_definitions': len(selected),
                            'omitted_definitions': available - len(selected), 'omitted_error_rows': omitted,
                            'source_window_policy': 'Three preceding lines and up to sixty following lines; not the full codebase.'}}
    if len(json.dumps(context, ensure_ascii=False)) > max_context_characters:
        raise ValueError('Context exceeds budget; select fewer APIs or raise max_context_characters')
    preview = {'schema_version': 1, 'study': str(study), 'source_root': str(root),
               'baseline_revision': attachment['revision'], 'context': context,
               'artifacts': selected_refs + refs + profile_refs + ([error_ref] if error_ref else []),
               'error_scope': 'operator-designated development logs only',
               'llm_calls': 0}
    preview['preview_sha256'] = digest(preview)
    output = development_destination(study, output)
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'preview.json', preview)
    return {'preview': str(output / 'preview.json'), 'llm_calls': 0, 'coverage': context['coverage']}
