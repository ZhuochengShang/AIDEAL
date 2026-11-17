"""Validate authored entries without treating verbatim source notes as placeholders."""
from __future__ import annotations

import re

POLICY = 'source-note-todo-v2'


def validate_entry(text, api=None, source_docs=()):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Author returned empty text')
    if api is None:
        return
    if re.findall(r'^## API Test: `([^`]+)`\s*$', text, re.M) != [api]:
        raise ValueError('Author returned an incomplete or wrong-API entry')
    # Only the exact source-doc field supplied by discovery is exempt, within
    # Signature. Quotes, code fences, or invented source labels elsewhere must
    # not conceal unfinished author content. The source text itself is retained.
    checked = text
    signature = re.search(r'^### Signature\s*\n(.*?)(?=^### |\Z)', text, re.M | re.S)
    if signature:
        body = signature.group(1)
        for doc in sorted({d for d in source_docs if d}, key=len, reverse=True):
            body = re.sub(r'^_Source doc:_ ' + re.escape(doc) + r'[ \t]*$',
                          '_Source doc:_ [verbatim source note]', body, flags=re.M)
        checked = text[:signature.start(1)] + body + text[signature.end(1):]
    if re.search(r'\bTODO\b', checked, re.I):
        raise ValueError('Author returned an unfinished TODO placeholder')


def is_complete_entry(text, api, source_docs=()):
    try:
        validate_entry(text, api, source_docs)
        return True
    except ValueError:
        return False
