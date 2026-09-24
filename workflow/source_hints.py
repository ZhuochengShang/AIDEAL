"""Readable, function-local source guidance; no executable annotation payloads.

AIDEAL-HINT-BEGIN / END blocks contain only whole-line ``#`` or ``//``
comments immediately before a declaration. This deliberately bounded format is
not a language AST or an automatic claim that the guidance fixes the program.
"""
import hashlib
from pathlib import Path
import re

BEGIN, END = 'AIDEAL-HINT-BEGIN', 'AIDEAL-HINT-END'
REQUIRED = ('function_id', 'requirement_id', 'requirement', 'diagnostic', 'action', 'validation')
MAX_SOURCE_BYTES, MAX_BLOCK_CHARACTERS = 2_000_000, 12_000


def _reject_unicode_escapes(values):
    """Java expands Unicode escapes before recognizing line comments.

    Reject all such spellings conservatively in slash-comment guidance, including
    repeated ``u`` characters and doubled backslashes. The raw-text stripper must
    never certify an annotation that a compiler can reinterpret as executable code.
    """
    if any(re.search(r'\\u+[0-9a-fA-F]{4}', value) for value in values):
        raise ValueError('Unicode escape sequences are not allowed in // source hints')


def _comment_lines(text):
    """Identify genuine whole-line comments, excluding strings/block comments.

    Handles Python triple strings and C/Scala/Java strings, plus Rust raw strings.
    Unknown/unterminated quoting fails conservatively by hiding later markers.
    """
    comments, quote, block, raw_end = {}, None, 0, None
    for number, line in enumerate(text.splitlines(keepends=True)):
        i = 0
        while i < len(line):
            if raw_end:
                end = line.find(raw_end, i)
                if end < 0:
                    break
                i, raw_end = end + len(raw_end), None
                continue
            if quote:
                if line.startswith(quote, i):
                    i, quote = i + len(quote), None
                elif line[i] == '\\':
                    i += 2
                else:
                    i += 1
                continue
            if block:
                if line.startswith('*/', i):
                    block -= 1
                    i += 2
                elif line.startswith('/*', i):
                    block += 1
                    i += 2
                else:
                    i += 1
                continue
            if line.startswith('//', i) or line[i] == '#':
                if not line[:i].strip():
                    prefix = '//' if line.startswith('//', i) else '#'
                    comments[number] = (prefix, line[i + len(prefix):].strip())
                break
            if line.startswith('/*', i):
                block, i = 1, i + 2
                continue
            raw = re.match(r'(?:br|r)(#+)?"', line[i:])
            if raw:
                raw_end = '"' + (raw[1] or '')
                i += raw.end()
                continue
            if line.startswith('"""', i) or line.startswith("'''", i):
                quote, i = line[i:i + 3], i + 3
                continue
            if line[i] in '\"\'':
                # Rust lifetimes are not string literals.
                if line[i] == "'" and re.match(r"'[A-Za-z_]\w*(?!')", line[i:]) and "'" not in line[i + 1:]:
                    i += 1
                    continue
                quote, i = line[i], i + 1
                continue
            i += 1
    return comments


def _blocks(text):
    lines, comments = text.splitlines(keepends=True), _comment_lines(text)
    active, blocks = None, []
    for number, (_, content) in comments.items():
        if content == BEGIN:
            if active is not None:
                raise ValueError('Nested source hint markers')
            active = number
        elif content == END:
            if active is None:
                raise ValueError('Unpaired source hint END')
            if any(i not in comments for i in range(active, number + 1)):
                raise ValueError('Source hints must contain only whole-line comments')
            prefixes = {comments[i][0] for i in range(active, number + 1)}
            if len(prefixes) != 1:
                raise ValueError('Source hint comment prefixes differ')
            if prefixes == {'//'}:
                _reject_unicode_escapes(lines[active:number + 1])
            if sum(len(lines[i]) for i in range(active, number + 1)) > MAX_BLOCK_CHARACTERS:
                raise ValueError('Source hint exceeds bounded annotation size')
            blocks.append((active, number, [comments[i][1] for i in range(active + 1, number)]))
            active = None
    if active is not None:
        raise ValueError('Unpaired source hint BEGIN')
    return blocks


def strip_source_hints(text):
    """Remove only recognized comment blocks, retaining every other exact byte."""
    lines = text.splitlines(keepends=True)
    for start, end, _ in reversed(_blocks(text)):
        del lines[start:end + 1]
    return ''.join(lines)


def _fields(lines):
    result = {}
    for line in lines:
        key, separator, value = line.partition(':')
        if not separator or key not in REQUIRED + ('status',):
            raise ValueError('Unknown or malformed source hint field')
        if key in result:
            raise ValueError('Duplicate source hint field: ' + key)
        result[key] = value.strip()
    if any(not result.get(key) for key in REQUIRED):
        raise ValueError('Source hint is missing a required field')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+', result['requirement_id']):
        raise ValueError('Unsafe requirement identifier')
    # Broad compiler phrases are symptoms, not violated API requirements.
    diagnostic = result['diagnostic'].casefold().strip(' .:;')
    if len(diagnostic) < 8 or diagnostic in {
            'type mismatch', 'typeerror', 'valueerror', 'error', 'exception',
            'compilation failed', 'runtime error', 'assertion failed'}:
        raise ValueError('Source hint needs a specific requirement diagnostic')
    result.setdefault('status', 'unvalidated')
    return result


def _identity(function_id):
    match = re.fullmatch(r'(.+):(\d+):([^:/]+)', function_id)
    if not match or int(match[2]) < 1:
        raise ValueError('Canonical function ID must be path:line:name')
    path = Path(match[1])
    if path.is_absolute() or '..' in path.parts or '\\' in match[1]:
        raise ValueError('Canonical function path must stay inside worktree')
    return match[1], int(match[2]), match[3]


def _declaration(lines, start, name):
    while start < len(lines) and not lines[start].strip():
        start += 1
    prefix = ''.join(lines[start:start + 12])
    # Only declaration syntax, never an arbitrary reference or call expression.
    patterns = (r'\b(?:async\s+)?def\s+' + re.escape(name) + r'\b',
                r'\bfn\s+' + re.escape(name) + r'\b',
                r'\b(?:public|protected|private|static|final|synchronized|abstract|native|default)\s+[^;={}]*?\b' + re.escape(name) + r'\s*\(')
    found = next((re.search(p, prefix) for p in patterns if re.search(p, prefix)), None)
    if found is None or prefix[:found.start()].count('\n') > 2:
        raise ValueError('Source hint must immediately precede its real function declaration')
    declaration_start = start + prefix[:found.start()].count('\n')
    if any(line.strip() and not line.lstrip().startswith(('@', 'pub ', 'public ', 'private ', 'protected ', 'static ', 'final '))
           for line in lines[start:declaration_start]):
        raise ValueError('Unexpected code between source hint and declaration')
    signature = ''
    depth = 0
    for line in lines[declaration_start:declaration_start + 12]:
        for i, char in enumerate(line):
            if char in '([':
                depth += 1
            elif char in ')]':
                depth -= 1
            if depth == 0 and (char == '{' or (char == '=' and line[i:i + 2] != '=>')
                               or (char == ':' and re.search(r'\bdef\s+', signature + line[:i]) and line[i + 1:].strip() == '')):
                signature += line[:i].rstrip()
                if len(signature) > 4000:
                    raise ValueError('Signature exceeds bound')
                return declaration_start, signature
        signature += line
        if len(signature) > 4000:
            break
    raise ValueError('Cannot identify bounded function signature')


def index_source_hints(worktree, artifacts, api_function_ids):
    """Index explicit source files and report missing API coverage before a run."""
    root = Path(worktree).resolve(strict=True)
    reverse = {identity: api for api, identity in api_function_ids.items()}
    if len(reverse) != len(api_function_ids):
        raise ValueError('Canonical function IDs must be unique')
    records, bindings, seen_paths, seen_requirements, unmapped = [], [], set(), set(), []
    for artifact in artifacts:
        path = Path(artifact)
        path = (root / path if not path.is_absolute() else path).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Source hint artifact escapes worktree')
        relative = path.relative_to(root).as_posix()
        if relative in seen_paths:
            raise ValueError('Duplicate source hint artifact')
        seen_paths.add(relative)
        if path.suffix not in ('.py', '.scala', '.java', '.rs'):
            raise ValueError('Source hints support Python, Scala, Java and Rust source files')
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError('Source hint artifact exceeds source size bound')
        data = path.read_bytes()
        text, lines = data.decode('utf-8'), data.decode('utf-8').splitlines(keepends=True)
        bindings.append({'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
        blocks = _blocks(text)
        removed = {i for start, end, _ in blocks for i in range(start, end + 1)}
        for start, end, content in blocks:
            fields = _fields(content)
            source_path, baseline_line, name = _identity(fields['function_id'])
            if source_path != relative:
                raise ValueError('Source hint canonical path does not match its source file')
            after = end + 1
            while after < len(lines) and (after in removed or not lines[after].strip()):
                after += 1
            declaration_line, signature = _declaration(lines, after, name)
            original_line = declaration_line + 1 - sum(i < declaration_line for i in removed)
            if baseline_line != original_line:
                raise ValueError('Canonical baseline line does not identify the annotated declaration')
            key = fields['function_id'], fields['requirement_id']
            if key in seen_requirements:
                raise ValueError('Duplicate source requirement identity')
            seen_requirements.add(key)
            if fields['function_id'] not in reverse:
                unmapped.append(fields['function_id'])
                continue
            record = {**fields, 'api': reverse[fields['function_id']], 'path': relative,
                      'annotation_start_line': start + 1, 'annotation_end_line': end + 1,
                      'declaration_line': declaration_line + 1, 'signature': signature,
                      'source_window': ''.join(lines[declaration_line:declaration_line + 12])[:6000],
                      'source_sha256': bindings[-1]['sha256']}
            record['hint_sha256'] = hashlib.sha256(repr(sorted(record.items())).encode()).hexdigest()
            records.append(record)
    covered = {r['function_id'] for r in records}
    return {'schema_version': 1, 'records': records, 'artifacts': bindings,
            'api_function_ids': dict(api_function_ids),
            'coverage': {'total_functions': len(reverse), 'covered_functions': len(covered),
                         'hint_count': len(records), 'uncovered_function_ids': sorted(set(reverse) - covered),
                         'unmapped_function_ids': sorted(set(unmapped))}}


def render_source_hint(fields, comment_prefix='//'):
    """Render a reviewed proposal as ordinary source comments, never code."""
    if comment_prefix not in ('//', '#'):
        raise ValueError('Use a supported whole-line comment prefix')
    if any(not isinstance(value, str) or '\n' in value or '\r' in value
           for value in fields.values()):
        raise ValueError('Source hint values must be single-line text')
    if comment_prefix == '//':
        _reject_unicode_escapes(fields.values())
    checked = _fields([key + ': ' + value for key, value in fields.items()])
    return '\n'.join(comment_prefix + ' ' + line for line in
                     [BEGIN, *(key + ': ' + checked[key] for key in REQUIRED + ('status',)), END]) + '\n'


def insert_source_hint(source, function_id, fields, *, source_path=None):
    """Return annotation-only edited source; caller owns saving and committing."""
    path, baseline_line, name = _identity(function_id)
    if source_path is not None and Path(source_path).as_posix() != path:
        raise ValueError('Source insertion path differs from canonical identity')
    if any((_fields(content)['function_id'], _fields(content)['requirement_id'])
           == (function_id, fields.get('requirement_id')) for _, _, content in _blocks(source)):
        raise ValueError('Function already contains guidance for this requirement')
    lines = source.splitlines(keepends=True)
    # Canonical line identifies the original declaration. Existing annotations
    # shift its physical position; map through their removed original lines.
    deleted = {i for start, end, _ in _blocks(source) for i in range(start, end + 1)}
    positions = [i for i in range(len(lines)) if i not in deleted]
    if baseline_line > len(positions):
        raise ValueError('Canonical declaration line is outside source')
    at = positions[baseline_line - 1]
    actual, _ = _declaration(lines, at, name)
    if actual != at:
        raise ValueError('Canonical line does not identify exact declaration')
    values = {**fields, 'function_id': function_id}
    prefix = '#' if Path(path).suffix == '.py' else '//'
    block = render_source_hint(values, prefix)
    indentation = re.match(r'\s*', lines[at])[0]
    block = ''.join(indentation + line for line in block.splitlines(keepends=True))
    result = ''.join(lines[:at]) + block + ''.join(lines[at:])
    if strip_source_hints(result) != strip_source_hints(source):
        raise ValueError('Source hint insertion changed non-annotation text')
    return result


def select_source_hints(index, previous):
    """Select guidance only after function and requirement evidence agree."""
    from .failure_diagnosis import diagnose_failure
    diagnosis = diagnose_failure(index, previous)
    if diagnosis['status'] != 'identified':
        return {'diagnosis': diagnosis, 'matched': [], 'reason': diagnosis['status']}
    candidates = [r for r in index['records'] if r['function_id'] == diagnosis['function_id']]
    matched = [r for r in candidates if r['diagnostic'] in diagnosis['diagnostic']
               and (not diagnosis.get('requirement_id') or r['requirement_id'] == diagnosis['requirement_id'])]
    reason = 'matched' if matched else 'requirement_not_covered' if candidates else 'function_not_covered'
    return {'diagnosis': diagnosis, 'matched': matched, 'reason': reason}
