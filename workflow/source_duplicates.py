"""Read-only duplicate candidates in attached libraries; never imports target code."""
import ast
from collections import defaultdict
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


LANGUAGES = {'.py': 'python', '.scala': 'scala', '.java': 'java', '.rs': 'rust'}
EXCLUDED = {'.git', '.aideal', '.hg', '.svn', '.venv', 'venv', '__pycache__',
            'vendor', 'vendors', 'node_modules', 'target', 'build', 'dist', '.tox',
            '.mypy_cache', '.pytest_cache', '.gradle', '.idea'}
METHODS = {'python': 'exact_ast_signature_and_body',
           'scala': 'braced_signature_and_body_tokens',
           'java': 'braced_signature_and_body_tokens',
           'rust': 'braced_signature_and_body_tokens'}
_WORD = re.compile(r'[A-Za-z_$][\w$]*|\d[\w.]*|==|!=|=>|->|::|&&|\|\||<=|>=|\+\+|--')
_RUST_RAW = re.compile(r'(?:br|r)(#{0,255})"')
_CHAR = re.compile(r"'(?:\\u\{[0-9a-fA-F_]+\}|\\x[0-9a-fA-F]{2}|\\.|[^'\\\n])'")
LIMITATIONS = [
    'Matches are structural candidates, not proof of semantic equivalence or permission to delete APIs.',
    'Names and literals are preserved; parameter/local alpha-renaming and near-duplicate detection are disabled.',
    'Python scans direct module/class declarations, excluding nested/conditional declarations and trivial/abstract bodies.',
    'Scala/Java/Rust use conservative lexical extraction, not compilers or type/name resolution; coverage is partial.',
    'Lexical extraction requires named, braced functions; constructors, annotations/attributes, Scala indentation/expression bodies, macros and generated functions may be missed.',
    'Comments/formatting are ignored in lexical groups (Scala newlines retained); bindings, ownership, annotations, effects and dispatch require review.',
    'Git scans tracked working-tree contents, including edits, not untracked files; excluded directories and symlinks are never followed.',
    'Counts describe this scan scope, not all duplication in the library. No target code, tests or model is executed.',
    'Hashes bind the bytes read; scanning does not freeze an atomic repository snapshot.',
]


def _digest(value):
    payload = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _matches(path, patterns):
    def match(parts, pattern):
        if not pattern:
            return not parts
        if pattern[0] == '**':
            return match(parts, pattern[1:]) or bool(parts) and match(parts[1:], pattern)
        return bool(parts) and fnmatch.fnmatchcase(parts[0], pattern[0]) and match(parts[1:], pattern[1:])
    return not patterns or any(match(path.split('/'), p.split('/')) for p in patterns)


def _files(root, patterns):
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
    skipped = []
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                              timeout=15, env=env)
    try:
        found = git('rev-parse', '--show-toplevel')
    except FileNotFoundError:
        if (root / '.git').exists():
            raise ValueError('Git is required to scan tracked repository sources')
        found = None
    if found is not None and found.returncode == 0:
        if Path(os.fsdecode(found.stdout).strip()).resolve() != root:
            raise ValueError('Pass the Git repository root, not a subdirectory')
        listing = git('ls-files', '--cached', '-z')
        if listing.returncode:
            raise ValueError('Unable to enumerate tracked Git sources')
        paths = [os.fsdecode(p) for p in listing.stdout.split(b'\0') if p]
        head = git('rev-parse', '--verify', 'HEAD')
        revision = head.stdout.decode().strip() if head.returncode == 0 else None
        mode = 'git_tracked_worktree'
    else:
        if (root / '.git').exists():
            raise ValueError('Cannot read the Git repository; refusing a filesystem fallback')
        paths = []
        def fail_discovery(error):
            raise ValueError('Unable to enumerate source scope: ' + str(error))
        for base, dirs, files in os.walk(root, followlinks=False, onerror=fail_discovery):
            skipped.extend({'path': (Path(base) / d).relative_to(root).as_posix(),
                            'reason': 'excluded_directory'} for d in dirs if d.lower() in EXCLUDED)
            dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDED)
            paths.extend((Path(base) / f).relative_to(root).as_posix() for f in files)
            paths.extend((Path(base) / d).relative_to(root).as_posix() for d in dirs
                         if (Path(base) / d).is_symlink())
            dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
        revision, mode = None, 'filesystem'
    selected = []
    for name in sorted(set(paths)):
        path = Path(name)
        if any(part.lower() in EXCLUDED for part in path.parts[:-1]):
            skipped.append({'path': name, 'reason': 'excluded_directory'})
        elif _matches(name, patterns) and (patterns or path.suffix.lower() in LANGUAGES
                                          or (root / path).is_symlink()):
            selected.append(name)
    return selected, skipped, mode, revision


def _python_functions(raw, path):
    tree = ast.parse(raw, filename=path, type_comments=True)
    result, excluded = [], 0
    def visit(body, prefix=''):
        nonlocal excluded
        for node in body:
            if isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + '.')
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                executable = node.body
                if executable and isinstance(executable[0], ast.Expr) and isinstance(
                        executable[0].value, ast.Constant) and isinstance(executable[0].value.value, str):
                    executable = executable[1:]
                abstract = any(ast.unparse(d).split('.')[-1] == 'abstractmethod' for d in node.decorator_list)
                if abstract or len(executable) < 2 or sum(1 for n in executable for _ in ast.walk(n)) < 12:
                    excluded += 1
                    continue
                # Only the declared function name is omitted; all bindings/literals remain.
                structure = {field: ast.dump(value, include_attributes=False) if isinstance(value, ast.AST)
                             else [ast.dump(v, include_attributes=False) for v in value] if isinstance(value, list)
                             else value for field, value in ast.iter_fields(node) if field != 'name'}
                signature = ('async ' if isinstance(node, ast.AsyncFunctionDef) else '') + node.name + '(' + ast.unparse(node.args) + ')'
                if node.returns:
                    signature += ' -> ' + ast.unparse(node.returns)
                result.append({'name': prefix + node.name, 'line': node.lineno,
                    'end_line': node.end_lineno, 'kind': 'method' if prefix else 'function',
                    'decorators': [ast.unparse(d) for d in node.decorator_list], 'type_comment': node.type_comment,
                    'signature': signature, '_key': _digest([type(node).__name__, structure])})
    visit(tree.body)
    return result, excluded


def _tokens(text, language):
    """Keep literal bytes/identifiers; discard comments without treating their braces as code."""
    tokens, i, line = [], 0, 1
    while i < len(text):
        start, start_line, char = i, line, text[i]
        if char.isspace():
            if char == '\n':
                line += 1
                if language == 'scala':
                    tokens.append(('\n', start_line, i))
            i += 1
            continue
        if text.startswith('//', i):
            end = text.find('\n', i)
            i = len(text) if end < 0 else end
            continue
        if text.startswith('/*', i):
            depth, i = 1, i + 2
            while depth and i < len(text):
                if text.startswith('/*', i) and language in {'scala', 'rust'}:
                    depth, i = depth + 1, i + 2
                elif text.startswith('*/', i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            if depth:
                raise ValueError('Unterminated block comment')
            line += text[start:i].count('\n')
            if language == 'scala' and '\n' in text[start:i]:
                tokens.append(('\n', start_line, start))
            continue
        raw = _RUST_RAW.match(text, i) if language == 'rust' else None
        if raw:
            close = '"' + raw.group(1)
            end = text.find(close, raw.end())
            if end < 0:
                raise ValueError('Unterminated Rust raw string')
            i = end + len(close)
        elif text.startswith('"""', i) and language in {'scala', 'java'}:
            end = text.find('"""', i + 3)
            if language == 'java':
                while end >= 0 and (len(text[:end]) - len(text[:end].rstrip('\\'))) % 2:
                    end = text.find('"""', end + 3)
            if end < 0:
                raise ValueError('Unterminated multiline string')
            i = end + 3
        elif char == '"' or (char == "'" and _CHAR.match(text, i)):
            quote, i = char, i + 1
            while i < len(text) and text[i] != quote:
                i += 2 if text[i] == '\\' else 1
            if i >= len(text):
                raise ValueError('Unterminated string')
            i += 1
        else:
            if char == "'" and language == 'java':
                raise ValueError('Invalid or unsupported Java character literal')
            word = _WORD.match(text, i)
            i = word.end() if word else i + 1
        value = text[start:i]
        line += value.count('\n')
        tokens.append((value, start_line, start))
    return tokens


def _lexical_functions(raw, path, language):
    text = raw.decode('utf-8')
    if language == 'java' and re.search(r'\\u+[0-9a-fA-F]{4}', text):
        raise ValueError('Java Unicode preprocessing requires a compiler parser')
    tokens = _tokens(text, language)
    values = [t[0] for t in tokens]
    pairs, stack = {}, []
    for i, value in enumerate(values):
        if value in ('(', '[', '{'):
            stack.append((value, i))
        elif value in (')', ']', '}'):
            if not stack or stack[-1][0] != {')': '(', ']': '[', '}': '{'}[value]:
                raise ValueError('Unbalanced delimiters; lexical extraction incomplete')
            _, start = stack.pop()
            pairs[start] = i
    if stack:
        raise ValueError('Unbalanced delimiters; lexical extraction incomplete')
    result, excluded, i = [], 0, 0
    while i < len(values):
        name_at = i + 1 if values[i] == {'scala': 'def', 'rust': 'fn'}.get(language) else i
        if language != 'java' and name_at == i:
            i += 1
            continue
        name = values[name_at] if name_at < len(values) else ''
        if not re.fullmatch(r'[A-Za-z_$][\w$]*', name):
            i += 1
            continue
        cursor = name_at + 1
        if language == 'java' and (cursor >= len(values) or values[cursor] != '('):
            i += 1
            continue
        seen_params = False
        while cursor < len(values) and values[cursor] not in ('{', '}', ';', '='):
            if values[cursor] in ('(', '['):
                seen_params |= values[cursor] == '('
                cursor = pairs[cursor] + 1
            else:
                cursor += 1
        if language == 'scala' and cursor < len(values) and values[cursor] == '=':
            cursor += 1
            while cursor < len(values) and values[cursor] == '\n':
                cursor += 1
        if not seen_params or cursor >= len(values) or values[cursor] != '{':
            i += 1
            continue
        start = i
        while start and values[start - 1] not in (';', '{', '}', '\n'):
            start -= 1
        prefix = values[start:i]
        if language == 'java':
            modifiers = {'public', 'private', 'protected', 'static', 'final', 'abstract', 'synchronized', 'native', 'strictfp', 'default'}
            if (name in {'if', 'for', 'while', 'switch', 'catch', 'synchronized', 'try'}
                    or not any(v not in modifiers for v in prefix)
                    or any(v in prefix for v in ('=', 'new', 'class', 'record', 'interface', '@', '.', 'return'))):
                i += 1
                continue
            close_params = pairs[name_at + 1]
            if close_params + 1 != cursor and values[close_params + 1] != 'throws':
                i += 1
                continue
        end = pairs[cursor]
        body = values[cursor + 1:end]
        meaningful = [v for v in body if v not in ('\n', '{', '}')]
        separators = body.count(';') + (body.count('\n') if language == 'scala' else 0)
        if len(meaningful) < 14 or separators < (2 if language == 'java' else 1):
            excluded += 1
        else:
            header = values[start:cursor]
            header[name_at - start] = '<function-name>'
            result.append({'name': name, 'line': tokens[i][1], 'end_line': tokens[end][1],
                'kind': 'method' if language == 'java' else 'function_or_method',
                'signature': text[tokens[start][2]:tokens[cursor][2]].strip(),
                '_key': _digest([header, body])})
        i = end + 1
    return result, excluded


def scan_duplicates(repository, *, source_globs=None):
    """Return JSON-compatible evidence and suggestions; never change library files."""
    root = Path(repository).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Repository must be a directory')
    if source_globs is not None and (not isinstance(source_globs, (list, tuple))
            or not source_globs or any(not isinstance(p, str) or not p.strip()
            or Path(p).is_absolute() or '..' in Path(p).parts for p in source_globs)):
        raise ValueError('source_globs must be nonempty repository-relative patterns')
    patterns = sorted({Path(p).as_posix() for p in source_globs or []})
    paths, skipped, mode, revision = _files(root, patterns)
    settings = {'source_globs': patterns, 'excluded_directories': sorted(EXCLUDED),
                'max_file_bytes': 5_000_000, 'python_min_statements': 2,
                'python_min_ast_nodes': 12, 'lexical_min_tokens': 14,
                'alpha_renaming': False, 'near_duplicates': False}
    inputs, functions, errors, languages, groups_by_key = [], [], [], {}, defaultdict(list)
    for name in paths:
        path, language = root / name, LANGUAGES.get(Path(name).suffix.lower())
        record = {'path': name, 'language': language, 'sha256': None, 'status': 'error'}
        inputs.append(record)
        try:
            if path.is_absolute() and root not in path.parents:
                raise ValueError('Source path escapes the repository')
            if any((root / Path(*Path(name).parts[:j])).is_symlink() for j in range(1, len(Path(name).parts) + 1)):
                raise ValueError('Symlink source is not scanned')
            if root not in path.resolve().parents:
                raise ValueError('Source path escapes the repository')
            if not language:
                raise ValueError('Unsupported source language')
            if not path.is_file():
                raise ValueError('Source is not a regular file')
            if path.stat().st_size > settings['max_file_bytes']:
                raise ValueError('Source exceeds configured scan size limit')
            with path.open('rb') as source:
                raw = source.read(settings['max_file_bytes'] + 1)
            if len(raw) > settings['max_file_bytes']:
                raise ValueError('Source exceeds configured scan size limit')
            record['sha256'] = _digest(raw)
            found, excluded = _python_functions(raw, name) if language == 'python' else _lexical_functions(raw, name, language)
            coverage = languages.setdefault(language, {'files': 0, 'eligible_functions': 0, 'trivial_or_abstract_functions_skipped': 0, 'method': METHODS[language], 'coverage': 'module_class_definitions' if language == 'python' else 'partial_braced_extraction'})
            coverage['files'] += 1
            coverage['eligible_functions'] += len(found)
            coverage['trivial_or_abstract_functions_skipped'] += excluded
            record['status'] = 'scanned'
            for entry in found:
                key = entry.pop('_key')
                entry.update(path=name, language=language, method=METHODS[language], id=f'{name}:{entry["line"]}:{entry["name"]}')
                functions.append(entry)
                groups_by_key[(language, key)].append(entry)
        except (OSError, SyntaxError, UnicodeError, ValueError, RecursionError) as exc:
            errors.append({'path': name, 'language': language, 'type': type(exc).__name__, 'message': str(exc)})
    groups = []
    for (language, key), members in sorted(groups_by_key.items()):
        if len(members) < 2:
            continue
        groups.append({'id': key, 'language': language, 'method': METHODS[language],
            'requires_semantic_review': True, 'members': members,
            'suggestion': {'action': 'Extract a shared implementation or delegate to a reviewed canonical implementation; preserve each original public API/signature.',
                'canonical_candidate': members[0]['id'], 'alias_policy': 'Use thin delegation, never copy the implementation into each alias.',
                'required_checks': ['Resolve globals, receivers, decorators/annotations, ownership and side effects before choosing a shared implementation.',
                    'Run existing tests and contract checks through every original entrypoint, including return values, errors and mutation/order behavior.',
                    'Check defaults, keyword/overload dispatch, visibility and compatibility; then rescan the same source scope.']}})
    counts = {'eligible_functions': len(functions), 'duplicate_groups': len(groups),
              'functions_in_groups': sum(len(g['members']) for g in groups),
              'redundant_instances': sum(len(g['members']) - 1 for g in groups)}
    return {'schema_version': 1, 'analyzer': {'name': 'aideal_source_duplicates', 'version': 1, 'sha256': _digest(Path(__file__).read_bytes())},
        'repository': {'root': str(root), 'git_revision': revision},
        'scope': {'selection': mode, 'extensions': sorted(LANGUAGES)}, 'settings': settings,
        'coverage': {'selected_files': len(inputs), 'scanned_files': sum(r['status'] == 'scanned' for r in inputs),
                     'failed_files': len(errors), 'by_language': languages, 'excluded_paths': skipped},
        'inputs': inputs, 'input_sha256': _digest(inputs), 'functions': functions, 'groups': groups,
        'counts': counts, 'errors': errors, 'limitations': LIMITATIONS[:]}


def compare_duplicate_reports(before, after):
    """Compare observed candidates, refusing to claim reduction after coverage failures."""
    reasons = []
    for field in ('schema_version', 'analyzer', 'settings', 'scope'):
        if field not in before or field not in after or before[field] != after[field]:
            reasons.append(f'Incompatible or missing {field}')
    for label, report in (('before', before), ('after', after)):
        if report.get('schema_version') != 1:
            reasons.append(f'{label} has an unsupported report schema')
        if report.get('errors') or report.get('coverage', {}).get('failed_files', 1):
            reasons.append(f'{label} has incomplete/error coverage')
        if not report.get('coverage', {}).get('scanned_files'):
            reasons.append(f'{label} has no scanned source files')
        counts = report.get('counts')
        required = ('eligible_functions', 'duplicate_groups', 'functions_in_groups', 'redundant_instances')
        if not isinstance(counts, dict) or any(type(counts.get(k)) is not int or counts[k] < 0 for k in required):
            reasons.append(f'{label} has an invalid count record')
    before_paths = {r['path'] for r in before.get('inputs', [])}
    after_paths = {r['path'] for r in after.get('inputs', [])}
    comparable = not reasons
    reduction = ({key: before['counts'][key] - after['counts'][key]
                  for key in ('duplicate_groups', 'functions_in_groups', 'redundant_instances')}
                 if comparable else None)
    return {'schema_version': 1, 'comparable': comparable, 'reasons': reasons,
            'before': before.get('counts'), 'after': after.get('counts'), 'reduction': reduction,
            'added_files': sorted(after_paths - before_paths), 'removed_files': sorted(before_paths - after_paths),
            'before_input_sha256': before.get('input_sha256'), 'after_input_sha256': after.get('input_sha256'),
            'semantic_equivalence': 'not_checked', 'api_compatibility': 'not_checked',
            'interpretation': 'Counts concern structural candidates only. A reduction does not prove equivalent behavior, successful refactoring, or preserved API coverage. Partial lexical extraction may miss changed syntax. Different roots are allowed; repository lineage is not established.'}
