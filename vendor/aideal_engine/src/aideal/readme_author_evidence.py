"""Bound source comments and conservative owner-qualified repository examples.

No subject is imported or executed. These are development source excerpts, not
held-out tasks or proof that tests pass. Unsupported/dynamic call forms are
omitted rather than matched by a bare method name or a sibling API.
"""
from __future__ import annotations

import ast
import glob
import hashlib
import json
import re
from pathlib import Path

from .api_examples import _test_blocks_for
from .api_registry import target_key


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _span(path, raw, text, start, end):
    return {'path': str(path.resolve()), 'file_sha256': _sha(raw),
            'start': start, 'end': end, 'offset_unit': 'Unicode code points',
            'start_line': text.count('\n', 0, start) + 1,
            'end_line': text.count('\n', 0, max(start, end - 1)) + 1,
            'text': text[start:end], 'text_sha256': _sha(text[start:end].encode())}


def source_comment(cfg, row, max_chars=12000):
    """Read only the comment attached to a hash-bound selected source location."""
    result = {'status': 'not_supplied', 'text': '', 'evidence': None}
    expected = row.get('source_sha256') or row.get('file_sha256')
    if not expected or not row.get('file') or not row.get('line'):
        return {**result, 'reason': 'selected_definition_has_no_source_binding'}
    path = (cfg.root / row.get('defining_file', row['file'])).resolve(strict=True)
    raw = path.read_bytes()
    if _sha(raw) != expected:
        raise ValueError('README author source changed: ' + str(path))
    text = raw.decode('utf-8')
    line = int(row['line'])
    if line < 1 or line > len(text.splitlines()):
        raise ValueError('README source location is outside its bound file')
    start = end = None
    if path.suffix == '.py':
        nodes = [n for n in ast.walk(ast.parse(text))
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                 and n.lineno == line and n.name == row['name']]
        if len(nodes) == 1 and ast.get_docstring(nodes[0], clean=False) is not None:
            doc = nodes[0].body[0]
            lines = text.splitlines(keepends=True)
            start = sum(map(len, lines[:doc.lineno - 1])) + len(lines[doc.lineno - 1].encode()[:doc.col_offset].decode())
            end = sum(map(len, lines[:doc.end_lineno - 1])) + len(lines[doc.end_lineno - 1].encode()[:doc.end_col_offset].decode())
            content = ast.get_docstring(nodes[0], clean=False)
    elif path.suffix in ('.java', '.scala'):
        # An adjacent Javadoc/Scaladoc block may precede plain annotation lines.
        # Do not borrow comments from a prior overload or another declaration.
        boundary = sum(map(len, text.splitlines(keepends=True)[:line - 1]))
        prefix = text[:boundary]
        match = re.search(r'/\*\*(?:(?!/\*|\*/)[\s\S])*\*/\s*(?:@[\w.]+(?:\([^()\n]*\))?\s*)*\Z', prefix)
        if match:
            start = match.start(); end = text.index('*/', start) + 2
            content = re.sub(r'^\s*\* ?', '', text[start + 3:end - 2], flags=re.M).strip()
    if start is None:
        return {**result, 'reason': 'no_supported_attached_comment',
                'source': {'path': str(path), 'file_sha256': expected}}
    if end - start > max_chars:
        return {**result, 'reason': 'attached_comment_exceeds_budget',
                'source': {'path': str(path), 'file_sha256': expected}, 'source_characters': end - start}
    return {'status': 'source_bound', 'text': content,
            'evidence': _span(path, raw, text, start, end),
            'meaning': 'Comment text from the selected source site; not execution validation.'}


def _code_mask(text):
    """Mask JVM comments/strings without moving source offsets or line breaks."""
    pattern = r'//[^\n]*|/\*[\s\S]*?\*/|"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern, lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text)


def _jvm_calls(text, start, end, known_paths):
    """Only literal qualified/static/constructor paths; no receiver inference."""
    mask = _code_mask(text)
    block = mask[start:end]
    if not block.startswith('{') or not block.endswith('}') or block.count('{') != block.count('}'):
        return []
    aliases = {}
    for match in re.finditer(r'\bimport\s+(?:static\s+)?([\w.]+)(?:\s*;|\s*(?=\n|\Z))', mask):
        value = match[1]
        aliases.setdefault(value.rsplit('.', 1)[-1], set()).add(value)
    package = re.search(r'\bpackage\s+([\w.]+)', mask)
    if package:
        # Only exact known declarations in the test's package are eligible.
        for value in known_paths:
            tail = value.removeprefix(package[1] + '.')
            if tail != value:
                first = tail.split('.')[0]
                aliases.setdefault(first, set()).add(package[1] + '.' + first)
    # A local declaration/assignment can shadow an imported owner. Reject that
    # spelling throughout the file rather than guessing a lexical binding.
    shadowed = set(re.findall(r'\b(?:class|object|trait|def|val|var)\s+(\w+)', mask))
    shadowed.update(re.findall(r'\b(\w+)\s*=(?!=|>)', mask))
    calls = []
    for m in re.finditer(r'\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*(?:\[[^\]\n]*\]\s*)?\(', mask[start:end]):
        spelling = m[1]; head, dot, tail = spelling.partition('.')
        if head in shadowed:
            continue
        resolved = {spelling} if spelling in known_paths and '.' in spelling else set()
        if len(aliases.get(head, ())) == 1:
            resolved.add(next(iter(aliases[head])) + (dot + tail if dot else ''))
        for value in resolved & known_paths:
            calls.append({'public_path': value, 'spelling': spelling,
                          'call_offset': start + m.start(1),
                          'resolution': 'explicit_qualified_or_unambiguous_imported_owner',
                          'overload_resolution': 'not_inferred'})
    return calls


def _python_calls(text, start, end, known_paths):
    """Resolve import-backed call paths; omit local receivers and shadowing."""
    tree = ast.parse(text)
    imports = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.setdefault(a.asname or a.name.split('.')[0], set()).add(a.name if a.asname else a.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for a in node.names:
                if a.name != '*':imports.setdefault(a.asname or a.name, set()).add(node.module + '.' + a.name)
    lines = text.splitlines(keepends=True)
    offset = lambda n: sum(map(len, lines[:n.lineno - 1])) + len(lines[n.lineno - 1].encode()[:n.col_offset].decode())
    candidates = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_') and start <= offset(n) < end]
    if len(candidates) != 1:return []
    test = candidates[0]
    shadowed = {n.id for n in ast.walk(test) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    shadowed.update(n.arg for n in ast.walk(test) if isinstance(n, ast.arg))
    shadowed.update(n.name for n in ast.walk(test) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    shadowed.update(n.asname or n.name.split('.')[0] for n in ast.walk(test) if isinstance(n, ast.alias))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            shadowed.update(n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store))
    calls = []
    for node in ast.walk(test):
        if not isinstance(node, ast.Call):continue
        spelling = ast.unparse(node.func)
        if not re.fullmatch(r'\w+(?:\.\w+)*', spelling):continue
        head, dot, tail = spelling.partition('.')
        if head in shadowed or len(imports.get(head, ())) != 1:continue
        value = next(iter(imports[head])) + (dot + tail if dot else '')
        if value in known_paths:
            calls.append({'public_path': value, 'spelling': spelling,
                          'call_offset': offset(node), 'resolution': 'explicit_module_import',
                          'overload_resolution': 'not_inferred'})
    return calls


def qualified_author_evidence(cfg, definitions, max_examples=2, max_chars=6000):
    """Return auditable evidence for exact selected APIs, never bare-name hits."""
    rows = {target_key(row): row for row in definitions}
    evidence = {key: {'schema': 'aideal.qualified-author-evidence/v1', 'api_id': key,
                     'source_comment': source_comment(cfg, row), 'test_examples': [],
                     'test_selection': {'status': 'no_supported_exact_owner_example',
                                        'meaning': 'Only explicit source call bindings are used; absence is not absence of repository tests.'}}
                for key, row in rows.items()}
    by_path = {}
    for key, row in rows.items():
        for value in [row.get('qualified_name'), *(row.get('public_access_paths') or [])]:
            if value:by_path.setdefault(value, set()).add(key)
    # A public spelling shared by distinct defining APIs is not usable evidence.
    by_path = {key: next(iter(values)) for key, values in by_path.items() if len(values) == 1}
    if cfg.language.lower() not in {'python', 'java', 'scala'}:
        for record in evidence.values():
            record['test_selection']['status'] = 'language_not_supported_by_exact_owner_miner'
        return evidence
    # Mine only the attached repository, never evaluation work directories or
    # private task/oracle banks accidentally included in a broad test glob.
    source_root = Path(cfg.root).resolve()
    codebase = (getattr(cfg, 'raw', {}) or {}).get('codebase', {})
    if codebase.get('api_inventory'):
        inventory = (cfg.root / codebase['api_inventory']).read_bytes()
        if _sha(inventory) != codebase.get('api_inventory_sha256'):
            raise ValueError('README author API inventory changed')
        declared = json.loads(inventory).get('source_root')
        if not declared:
            raise ValueError('Exact-owner test mining requires a pinned repository source root')
        source_root = (cfg.root / declared).resolve(strict=True)
    files = sorted({Path(p).resolve() for g in cfg.test_globs
                    for p in glob.glob(str(cfg.root / g), recursive=True) if Path(p).is_file()})
    if any(not path.is_relative_to(source_root) for path in files):
        raise ValueError('README test evidence must stay inside the pinned source repository')
    scan = {'files_considered': len(files), 'oversized_files': 0,
            'omitted_oversized_or_ambiguous_blocks': 0, 'unparseable_python_blocks': 0,
            'omitted_oversized_import_contexts': 0,
            'resolution_scope': 'Explicit qualified/import-backed calls only; instance receivers, wildcard imports and dynamic aliases are not inferred.'}
    for path in files:
        raw = path.read_bytes()
        if len(raw) > 1_000_000:
            scan['oversized_files'] += 1
            continue  # bounded source mining; never cut a test
        text = raw.decode('utf-8')
        for name, block in _test_blocks_for(cfg, text):
            if not block or len(block) > max_chars or text.count(block) != 1:
                scan['omitted_oversized_or_ambiguous_blocks'] += 1
                continue
            start = text.index(block); end = start + len(block)
            try:
                calls = (_python_calls if cfg.language.lower() == 'python' else _jvm_calls)(text, start, end, set(by_path))
            except SyntaxError:
                scan['unparseable_python_blocks'] += 1
                continue  # no regex fallback for unparseable Python
            grouped = {}
            for call in calls:grouped.setdefault(by_path[call['public_path']], []).append(call)
            for key, matches in grouped.items():
                examples = evidence[key]['test_examples']
                if len(examples) >= max_examples:continue
                context = [line for line in text[:start].splitlines()
                           if re.match(r'^\s*(?:package|import|from)\b', line)]
                if len('\n'.join(context)) > 2000:
                    scan['omitted_oversized_import_contexts'] += 1
                    continue
                examples.append({'file': str(path), 'test': name, 'code': block,
                                 'imports_context': '\n'.join(context),
                                 'span': _span(path, raw, text, start, end),
                                 'matched_calls': matches, 'execution_status': 'not_run',
                                 'self_contained': False})
                evidence[key]['test_selection']['status'] = 'source_bound_examples'
    for record in evidence.values():
        record['test_selection']['scan'] = scan
    return evidence


def verify_author_evidence(record):
    """Fail if supplied source/test evidence changes before or during a call."""
    comment = record['source_comment']
    refs = [comment.get('evidence') or comment.get('source')]
    refs += [example['span'] for example in record['test_examples']]
    for binding in filter(None, refs):
        raw = Path(binding['path']).read_bytes()
        if _sha(raw) != binding['file_sha256']:
            raise ValueError('README author evidence changed: ' + binding['path'])
        if 'start' in binding:
            text = raw.decode('utf-8')[binding['start']:binding['end']]
            if text != binding['text'] or _sha(text.encode()) != binding['text_sha256']:
                raise ValueError('README author evidence span changed')
