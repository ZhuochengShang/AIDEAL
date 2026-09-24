"""Conservative public failure localization for source guidance selection.

This is a bounded diagnostic reader, not whole-program type inference. Unknown
receivers, overloaded owners and conflicting evidence produce no automatic hint.
Task target IDs never count as evidence that a function actually failed.
"""
import re


def _result(status, **fields):
    return {'status': status, **fields}



def _code_only(code):
    """Mask comments and literals while preserving exact line/column offsets."""
    pattern = re.compile(
        r'(?P<raw>(?:br|r)(?P<hashes>#+)?".*?"(?P=hashes))'
        r'|""".*?"""|\'\'\'.*?\'\'\''
        r'|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\\n])*\''
        r'|/\*.*?\*/|//[^\n]*|\#[^\n]*', re.DOTALL)
    return pattern.sub(lambda match: ''.join('\n' if c == '\n' else ' ' for c in match[0]), code)


def _owners(index, receiver, method):
    """Require an exact qualified owner, or an unambiguous short owner."""
    mapping = index['api_function_ids']
    full = receiver.replace('::', '.').replace('$', '') + '.' + method
    if full in mapping:
        return {mapping[full]}
    if '.' in receiver or '::' in receiver:
        return set()
    return {identity for api, identity in mapping.items()
            if api == full or api.endswith('.' + full)}


def _receiver_ids(index, code, receiver, method):
    # A literal owner call is acceptable only if its owner is unique.
    direct = _owners(index, receiver, method)
    if direct:
        return direct
    escaped = re.escape(receiver)
    types = set()
    # Scala/Python/Rust explicit type annotations and Java declarations.
    for pattern in (rf'\b{escaped}\s*:\s*([\w.]+)',
                    rf'\b([\w.]+)\s+{escaped}\s*=',
                    rf'\b{escaped}\s*=\s*(?:new\s+)?([\w.]+)\s*\('):
        types.update(re.findall(pattern, code))
    types.difference_update({'val', 'var', 'let', 'return'})
    # Multiple writes may shadow a prior declaration even when the second
    # value's type cannot be inferred. Fail closed rather than borrow its type.
    writes = re.findall(rf'\b{escaped}\s*(?::[^=\n]+)?=(?!=)', code)
    if len(types) != 1 or len(writes) > 1:
        return set()
    return _owners(index, types.pop(), method)


def _calls_at(index, code, line_number, column):
    code = _code_only(code)
    lines = code.splitlines()
    if line_number < 1 or line_number > len(lines):
        return set()
    line = lines[line_number - 1]
    # Do not interpret error locations inside comments as executable calls.
    if line.lstrip().startswith(('#', '//')):
        return set()
    calls = []
    for match in re.finditer(r'\b([A-Za-z_]\w*(?:(?:\.|::)[A-Za-z_]\w*)*)\s*\(', line):
        open_paren = match.end() - 1
        depth, closing = 0, None
        for at in range(open_paren, len(line)):
            if line[at] == '(':
                depth += 1
            elif line[at] == ')':
                depth -= 1
                if depth == 0:
                    closing = at
                    break
        if closing is None:
            continue  # Multiline call inference is deliberately unsupported.
        if column is not None and not match.start() <= column <= closing:
            continue
        name = match[1].replace('::', '.')
        if '.' in name:
            receiver, method = name.rsplit('.', 1)
            ids = _receiver_ids(index, code, receiver, method)
        else:
            # A short function call needs an explicit import, not a task target.
            aliases = re.findall(r'\bfrom\s+([\w.]+)\s+import\s+' + re.escape(name) + r'\b', code)
            ids = {index['api_function_ids'][module + '.' + name] for module in aliases
                   if module + '.' + name in index['api_function_ids']}
        if ids:
            calls.append((closing - match.start(), ids))
    if not calls:
        return set()
    # A caret inside a nested call identifies the innermost known API call.
    if column is not None:
        shortest = min(size for size, _ in calls)
        calls = [item for item in calls if item[0] == shortest]
    return set().union(*(ids for _, ids in calls))


def _compiler_evidence(index, code, feedback):
    lines = feedback.splitlines()
    # Scala/Java/Python adapter public diagnostic format: file:line[:column].
    header = re.compile(r'^\s*(.+?\.(?:scala|java|py|rs)):(\d+)(?::(\d+))?:\s*(?:error:?)?')
    starts = [(i, header.match(line)) for i, line in enumerate(lines) if header.match(line)]
    found = []
    for position, (start, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        chunk = lines[start:end]
        column = int(match[3]) - 1 if match[3] else None
        if column is None:
            carets = [line.index('^') for line in chunk if '^' in line and not line.strip(' ^~\t')]
            column = carets[0] if len(carets) == 1 else None
        candidate_lines = code.splitlines()
        declared_line = int(match[2])
        # Adapters may wrap snippets and shift diagnostic line numbers. Match
        # the exact displayed candidate line uniquely instead of guessing the
        # wrapper offset or borrowing an unrelated library source location.
        displayed = {line.strip() for line in chunk[1:] if line.strip()}
        locations = [i + 1 for i, line in enumerate(candidate_lines)
                     if line.strip() and line.strip() in displayed]
        if len(locations) != 1:
            continue
        line_number = locations[0]
        identities = _calls_at(index, code, line_number, column)
        if identities:
            found.append((identities, '\n'.join(chunk),
                          {'kind': 'compiler_location', 'file': match[1],
                           'line': line_number, 'diagnostic_line': declared_line, 'column': None if column is None else column + 1}))
    return found



def _import_call_ids(index, masked, class_name, canonical_owner):
    """Require actual calls through the imported owner or an explicit new receiver."""
    receivers = set()
    cls = re.escape(class_name)
    if re.search(r'\b(?:class|object|trait|interface|enum)\s+' + cls + r'\b', masked):
        return set()
    declaration = re.compile(r'\b(?:val|var|' + cls + r')\s+(\w+)\s*(?::[^=\n]+)?=\s*new\s+' + cls + r'\s*\(')
    for match in declaration.finditer(masked):
        receiver = match[1]
        assignments = re.findall(r'\b' + re.escape(receiver) + r'\s*(?::[^=\n]+)?=(?!=)', masked)
        if len(assignments) == 1:
            receivers.add(receiver)
    # A shadowed owner name is not a static/object receiver.
    if not re.search(r'\b(?:class|object|val|var)\s+' + cls + r'\b', masked):
        receivers.add(class_name)
    ids = set()
    for receiver in receivers:
        calls = re.finditer(r'\b' + re.escape(receiver) + r'\.([A-Za-z_]\w*)\s*\(', masked)
        for call in calls:
            api = canonical_owner + '.' + call[1]
            if api in index['api_function_ids']:
                ids.add(index['api_function_ids'][api])
    return ids


def _import_evidence(index, code, feedback):
    """Localize a missing class import only with an exact compiler source echo.

    Supports plain Scala/Java imports. No wildcard/renamed imports, inferred
    factory types or task-target substitution. Homonymous class owners abstain.
    """
    masked, lines = _code_only(code), feedback.splitlines()
    imports = list(re.finditer(r'^\s*import\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\s*;?\s*$', masked, re.M))
    headers = [(i, re.match(r'^\s*(.+?\.(?:scala|java)):(\d+)(?::\d+)?:\s*(?:error:?)?\s*(.*)', line))
               for i, line in enumerate(lines)]
    headers = [(i, match) for i, match in headers if match]
    owners = {api.rsplit('.', 1)[0] for api in index['api_function_ids'] if '.' in api}
    evidence = []
    for position, (start, header) in enumerate(headers):
        end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
        chunk, message = lines[start:end], header[3]
        for imported in imports:
            wrong_owner = imported[1]
            wrong_package, name = wrong_owner.rsplit('.', 1)
            source_line = code[imported.start():imported.end()].strip()
            # The raw echo must actually be the import declaration, not a
            # quoted/commented imitation removed by masking.
            if source_line not in [line.strip() for line in chunk[1:]]:
                continue
            patterns = (rf'\b(?:object|type|class)\s+{re.escape(name)}\s+is not a member of package\s+{re.escape(wrong_package)}\b',
                        rf'\bpackage\s+(?:{re.escape(wrong_owner)}|{re.escape(wrong_package)})\s+does not exist\b')
            if not any(re.search(pattern, message) for pattern in patterns):
                continue
            same_name = {owner for owner in owners if owner.rsplit('.', 1)[-1] == name}
            same_import = [item for item in imports if item[1].rsplit('.', 1)[-1] == name]
            if len(same_name) != 1 or len(same_import) != 1:
                continue
            canonical_owner = next(iter(same_name))
            if wrong_owner == canonical_owner:
                continue  # Correct import may instead expose a missing dependency.
            ids = _import_call_ids(index, masked, name, canonical_owner)
            if ids:
                evidence.append((ids, '\n'.join(chunk),
                    {'kind': 'compiler_import_and_explicit_call', 'file': header[1],
                     'diagnostic_line': int(header[2]), 'imported_owner': wrong_owner,
                     'canonical_owner': canonical_owner, 'import_source': source_line}))
    return evidence


def _stack_evidence(index, feedback):
    found = []
    for line in feedback.splitlines():
        match = re.search(r'\bat\s+([\w.$]+)\.([\w$]+)\([^()]+:\d+\)', line)
        if match:
            identities = _owners(index, match[1], match[2])
            if identities:
                # Only the innermost recognized frame is the failure location;
                # later callers are not independently failing functions.
                found.append((identities, feedback, {'kind': 'qualified_stack_frame', 'frame': line.strip()}))
                break
    return found


def diagnose_failure(index, previous):
    """Return one identified function or a public, auditable no-match reason.

    An adapter can supply ``public_failure`` with function_id, requirement_id
    and diagnostic. Its diagnostic must also occur in public_feedback. No
    private checker fields, expected outputs or oracle data enter this API.
    """
    if not previous:
        return _result('no_previous_failure')
    if (previous.get('incomplete') is True
            or previous.get('response_status') == 'incomplete'
            or previous.get('output_status') == 'incomplete'
            or (isinstance(previous.get('response_state'), dict)
                and previous['response_state'].get('complete') is False)):
        return _result('incomplete_model_output')
    code, feedback = previous.get('code', ''), previous.get('feedback', '')
    if not isinstance(code, str) or not isinstance(feedback, str):
        return _result('invalid_public_failure')
    if not code.strip():
        return _result('empty_candidate')
    public = previous.get('public_failure')
    explicit = None
    if public is not None:
        if (not isinstance(public, dict)
                or public.get('function_id') not in set(index['api_function_ids'].values())
                or not isinstance(public.get('requirement_id'), str)
                or not re.fullmatch(r'[A-Za-z0-9_.:-]+', public['requirement_id'])
                or not isinstance(public.get('diagnostic'), str)
                or not public['diagnostic'] or public['diagnostic'] not in feedback):
            return _result('invalid_public_failure')
        explicit = ({public['function_id']}, public['diagnostic'], {'kind': 'public_adapter_failure'})
    evidence = (_compiler_evidence(index, code, feedback) + _import_evidence(index, code, feedback)
                + _stack_evidence(index, feedback))
    if explicit:
        evidence.append(explicit)
    if not evidence:
        return _result('unresolved_function')
    identities = set().union(*(entry[0] for entry in evidence))
    if len(identities) != 1:
        return _result('ambiguous_function', candidate_function_ids=sorted(identities))
    function_id = identities.pop()
    diagnostic = '\n'.join(dict.fromkeys(entry[1] for entry in evidence))
    result = _result('identified', function_id=function_id, diagnostic=diagnostic,
                     evidence=[entry[2] for entry in evidence])
    if explicit:
        result['requirement_id'] = public['requirement_id']
    return result
