"""Opt-in qualified README selection; the default legacy selector is unchanged.

Heading identities are reviewed public configuration, not inferred from private
oracles. Validation proves complete API-key coverage and matching API spelling;
it does not independently establish class/object ownership from source code.
"""
from pathlib import Path
import re

from .ablation import digest

POLICY = 'qualified_sections'


def validate_documentation_selection(value, api_names=None):
    """Reject malformed/misdirected maps before controls or provider execution."""
    if not isinstance(value, dict) or set(value) != {'policy', 'api_headings'}:
        raise ValueError('documentation_selection needs policy and api_headings only')
    if value['policy'] != POLICY:
        raise ValueError('Unknown documentation_selection policy')
    mapping = value['api_headings']
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError('api_headings must be a nonempty mapping')
    for api, heading in mapping.items():
        if (not isinstance(api, str) or not api.strip() or '\n' in api or '\r' in api
                or not isinstance(heading, str)
                or re.fullmatch(re.escape(api) + r' \[(?:class|object)\]', heading) is None):
            raise ValueError('api_headings values must match the canonical API plus [class] or [object]')
    if len(set(mapping.values())) != len(mapping):
        raise ValueError('api_headings must be distinct')
    if api_names is not None and set(mapping) != set(api_names):
        raise ValueError('api_headings must map every bank API exactly once, with no extra APIs')
    return value


def markdown_sections(text):
    """Split real Markdown H2 sections, ignoring headings inside fenced blocks.

    Character ranges refer to decoded text, not raw byte offsets. Backtick
    and tilde fences follow the same-character/at-least-opening-length rule.
    """
    starts, offset, fence = [(0, None)], 0, None
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip('\r\n')
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', stripped)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
        elif marker:
            # A backtick fence's info string cannot itself contain a backtick.
            if marker[1][0] != '`' or '`' not in marker[2]:
                fence = (marker[1][0], len(marker[1]))
        else:
            heading = re.match(r'^ {0,3}##[ \t]+(.+?)[ \t]*$', stripped)
            if heading:
                title = re.sub(r'[ \t]+#+[ \t]*$', '', heading[1]).strip()
                if offset == 0:
                    starts[0] = (0, title)
                else:
                    starts.append((offset, title))
        offset += len(line)
    sections = []
    for index, (start, heading) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        if start != end:
            sections.append({'start': start, 'end': end, 'heading': heading, 'text': text[start:end]})
    return sections


def _identity(heading):
    if heading is None:
        return None
    value = re.sub(r'^API Test:\s*', '', heading).strip()
    if value.startswith('`') and value.endswith('`'):
        value = value[1:-1]
    return value


def _structured(section):
    return re.fullmatch(r'.+ \[(class|object)\]', _identity(section['heading']) or '') is not None


def _mentions(text, term):
    return len(re.findall(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text))


def _fallback_score(section, api):
    # Specific spelling wins over any number of incidental bare-name mentions.
    terms = (api, '.'.join(api.split('.')[-2:]), api.split('.')[-1])
    return tuple(_mentions(section['text'], term) for term in terms)


def _fair_lengths(lengths, budget):
    """Water-fill equally; redistribute unused short-section quota deterministically."""
    allocated = [0] * len(lengths)
    active = list(range(len(lengths)))
    while budget > 0 and active:
        share, extra = divmod(budget, len(active))
        used = 0
        for place, index in enumerate(active):
            amount = min(lengths[index] - allocated[index], share + (place < extra))
            allocated[index] += amount
            used += amount
        budget -= used
        active = [i for i in active if allocated[i] < lengths[i]]
        if used == 0:
            break
    return allocated


def select_qualified_sections(paths, targets, max_characters, selection):
    """Select one exact section per target, then receiver/name fallback if absent.

    Other explicitly qualified API sections never substitute for a missing exact
    identity. Unstructured Original documentation may fall back lexically; if no
    target has a match, its original ordered prefix is delivered. Relevant
    sections that fit are not padded with unrelated API entries. Quotas are fair
    across distinct required sections. A clipped section may end mid-code; the
    receipt records the exact range and does not claim full-section coverage.
    """
    validate_documentation_selection(selection)
    if type(max_characters) is not int or max_characters < 1:
        raise ValueError('documentation_max_characters must be a positive integer')
    if not targets or len(set(targets)) != len(targets) or set(targets) - set(selection['api_headings']):
        raise ValueError('Every requested API must have one reviewed heading')
    texts, sections = [], []
    for file_index, path in enumerate(paths):
        text = Path(path).read_text()
        texts.append(text)
        for section in markdown_sections(text):
            sections.append({**section, 'index': len(sections), 'file_index': file_index, 'path': str(path),
                             'joined_start': sum(len(t) for t in texts[:-1]) + 2 * file_index + section['start']})
    source = '\n\n'.join(texts)
    choices, primary = {}, []
    for api in sorted(targets):
        expected = selection['api_headings'][api]
        matches = [s for s in sections if _identity(s['heading']) == expected]
        if len(matches) > 1:
            raise ValueError('Duplicate exact qualified heading: ' + expected)
        section, mode = (matches[0], 'exact_heading') if matches else (None, 'absent')
        if section is None:
            candidates = [s for s in sections if not _structured(s)]
            candidates.sort(key=lambda s: tuple(-n for n in _fallback_score(s, api)) + (s['index'],))
            if candidates and any(_fallback_score(candidates[0], api)):
                section, mode = candidates[0], 'lexical_fallback'
        choices[api] = (section, mode)
        if section is not None and section['index'] not in primary:
            primary.append(section['index'])
    records = []
    if primary:
        chosen = [sections[i] for i in primary]
        budget = max(0, max_characters - 2 * (len(chosen) - 1))
        lengths = _fair_lengths([len(s['text']) for s in chosen], budget)
        pieces = []
        for section, length in zip(chosen, lengths):
            if length:
                if pieces:
                    pieces.append('\n\n')
                pieces.append(section['text'][:length])
                records.append(_section_receipt(section, length))
        delivered = ''.join(pieces)
        mode = 'target_sections'
    else:
        delivered = source[:max_characters]
        mode = 'ordered_prefix_no_match'
        for section in sections:
            length = max(0, min(len(section['text']), len(delivered) - section['joined_start']))
            if length:
                records.append(_section_receipt(section, length))
    selected = {r['index']: r for r in records}
    coverage = {}
    for api, (section, match) in choices.items():
        record = selected.get(section['index']) if section is not None else None
        coverage[api] = {'expected_heading': selection['api_headings'][api], 'match': match,
                         'selected_heading': section['heading'] if section else None,
                         'section_index': section['index'] if section else None,
                         'coverage': ('full' if record and record['full_section'] else 'clipped' if record else 'absent'),
                         'delivered_characters': record['delivered_characters'] if record else 0}
    return delivered, {'policy': POLICY, 'mode': mode, 'source_characters': len(source),
                       'delivered_characters': len(delivered), 'selected_section_indices': [r['index'] for r in records],
                       'selected_sections': records, 'targets': coverage,
                       'truncated': len(delivered) < len(source), 'delivered_sha256': digest(delivered)}


def _section_receipt(section, length):
    return {'index': section['index'], 'file_index': section['file_index'], 'path': section['path'],
            'heading': section['heading'], 'source_start_character': section['start'],
            'source_end_character': section['end'], 'delivered_end_character': section['start'] + length,
            'source_characters': len(section['text']), 'delivered_characters': length,
            'full_section': length == len(section['text']), 'clipped': length < len(section['text']),
            'delivered_sha256': digest(section['text'][:length])}
