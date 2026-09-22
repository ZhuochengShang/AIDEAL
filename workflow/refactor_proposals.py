"""Source-grounded review candidates, kept separate from executable aliases."""


def validate_refactors(rows, functions):
    """Check literal source citations, not equivalence or implementation safety."""
    if not isinstance(rows, list) or len(rows) > 20:
        raise ValueError('refactors must be a bounded list')
    required = {'title', 'function_ids', 'source_evidence', 'rationale',
                'proposed_change', 'preservation_plan', 'regression_checks', 'risks'}
    for row in rows:
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError('Invalid refactor record')
        for field in ('title', 'rationale', 'proposed_change', 'preservation_plan', 'risks'):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError('refactor.' + field + ' must be nonempty text')
        ids = row['function_ids']
        if (not isinstance(ids, list) or not ids or len(ids) > 100
                or any(not isinstance(i, str) or i not in functions for i in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError('Refactor functions must be distinct supplied API IDs')
        checks = row['regression_checks']
        if (not isinstance(checks, list) or not checks
                or any(not isinstance(x, str) or not x.strip() for x in checks)):
            raise ValueError('Refactor needs concrete regression checks')
        citations = row['source_evidence']
        if not isinstance(citations, list) or not citations or len(citations) > 100:
            raise ValueError('Refactor needs bounded source evidence')
        supported = set()
        for cite in citations:
            if not isinstance(cite, dict) or set(cite) != {'function_id', 'start_line', 'end_line', 'quote'}:
                raise ValueError('Invalid refactor source citation')
            identifier = cite['function_id']
            if not isinstance(identifier, str) or identifier not in ids:
                raise ValueError('Refactor citation must belong to a proposed function')
            window = functions[identifier].get('source_window', {})
            first, last, quote = cite['start_line'], cite['end_line'], cite['quote']
            if (type(first) is not int or type(last) is not int
                    or not window.get('start_line', 1) <= first <= last <= window.get('end_line', 0)
                    or not isinstance(quote, str) or not quote.strip()):
                raise ValueError('Refactor source citation is outside the supplied window')
            excerpt = '\n'.join(window['text'].splitlines()[first-window['start_line']:last-window['start_line']+1])
            if quote not in excerpt:
                raise ValueError('Refactor quote does not occur at the cited source lines')
            supported.add(identifier)
        if supported != set(ids):
            raise ValueError('Every refactored function needs supplied source evidence')
    return rows
