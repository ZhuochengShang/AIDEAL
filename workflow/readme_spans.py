"""Fence-aware, byte-preserving catalog composition; no provider dependencies."""
import re


API = re.compile(rb'^## API Test: `([^`\r\n]+)`[ \t]*(?:\r?\n)?$')
HEADING = re.compile(rb'^#{1,2}[ \t]+')
FENCE = re.compile(rb'^ {0,3}(`{3,}|~{3,})(.*?)(?:\r?\n)?$')


def headings(data):
    """Return real top-level heading byte offsets, ignoring fenced examples."""
    if not isinstance(data, bytes):
        raise ValueError('Catalog must be UTF-8 bytes')
    data.decode('utf-8')
    found, fence, offset = [], None, 0
    for line in data.splitlines(keepends=True):
        match = FENCE.match(line)
        if fence:
            if match and match[1][:1] == fence[:1] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
        elif match:
            fence = match[1]
        elif HEADING.match(line):
            api = API.match(line)
            found.append({'start_byte': offset, 'heading': api[1].decode() if api else None})
        offset += len(line)
    if fence:
        raise ValueError('Unclosed Markdown code fence')
    return found


def inspect_sections(data):
    """Suggested spans stop at any level-one/two heading, preserving a footer.

    A plain-text footer without a heading needs an explicit shorter end_byte
    selected by the caller. No heuristic guesses whether prose is a footer.
    """
    marks = headings(data)
    rows = []
    names = set()
    for i, mark in enumerate(marks):
        name = mark['heading']
        if name is None:
            continue
        if name in names:
            raise ValueError('Duplicate API heading: ' + name)
        names.add(name)
        rows.append({**mark, 'end_byte': marks[i + 1]['start_byte'] if i + 1 < len(marks) else len(data)})
    return rows


def validate_spans(data, entries):
    actual = {row['heading']: row for row in inspect_sections(data)}
    names = [e['heading'] for e in entries]
    ids = [e['id'] for e in entries]
    if len(set(names)) != len(names) or len(set(ids)) != len(ids):
        raise ValueError('Duplicate heading or target identity')
    if set(names) != set(actual):
        raise ValueError('Manifest must map every base API heading exactly once; reconcile the scope first')
    for entry in entries:
        span, section = entry['span'], actual[entry['heading']]
        start, end = span['start_byte'], span['end_byte']
        if type(start) is not int or type(end) is not int or start != section['start_byte'] or not start < end <= section['end_byte']:
            raise ValueError('Invalid or overlapping entry span: ' + entry['id'])
        if end != len(data) and data[end - 1:end] != b'\n':
            raise ValueError('Entry span must end on a line boundary')
        if len(headings(data[start:end])) != 1:
            raise ValueError('Entry span contains another top-level section')
    return sorted(entries, key=lambda e: e['span']['start_byte'])


def candidate_bytes(text, heading):
    if not isinstance(text, str) or not text.strip() or 'TODO' in text:
        raise ValueError('Incomplete generated entry')
    data = text.strip().encode('utf-8') + b'\n\n'
    marks = headings(data)
    if marks != [{'start_byte': 0, 'heading': heading}]:
        raise ValueError('Candidate must contain exactly the intended API entry and no other top-level section')
    return data


def compose(data, entries, candidates):
    ordered = validate_spans(data, entries)
    if set(candidates) - {e['id'] for e in entries}:
        raise ValueError('Unknown candidate identity')
    chunks, cursor = [], 0
    for entry in ordered:
        start, end = entry['span']['start_byte'], entry['span']['end_byte']
        chunks.append(data[cursor:start])
        value = candidates.get(entry['id'])
        chunks.append(candidate_bytes(value, entry['heading']) if value is not None else data[start:end])
        cursor = end
    chunks.append(data[cursor:])
    return b''.join(chunks)
