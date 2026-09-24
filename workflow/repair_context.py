"""Deterministic repair context extraction; no LLM summary or private checker data."""
from pathlib import Path
import re

from .ablation import digest


def public_failure(payload):
    """Accept only an adapter's explicitly public, diagnostic-backed attribution."""
    value = payload.get('public_failure')
    fields = ('function_id', 'requirement_id', 'diagnostic')
    if not isinstance(value, dict) or set(value) != set(fields):
        return None
    if not all(isinstance(value[k], str) and value[k].strip() for k in fields):
        return None
    feedback = payload.get('public_feedback', '')
    if not isinstance(feedback, str) or value['diagnostic'] not in feedback:
        return None
    return {key: value[key] for key in fields}


def compact_previous(previous):
    """Keep the complete latest candidate and exact unique diagnostic paragraphs.

    Remove repeated *whole* paragraphs, not individual lines: a repeated caret,
    source line or stack frame inside another diagnostic can change its meaning.
    History and private fields never enter the model prompt.
    """
    feedback = previous['feedback']
    chunks = re.split(r'\n[ \t]*\n', feedback)
    seen, kept, repeated = set(), [], 0
    for chunk in chunks:
        if chunk and chunk in seen:
            repeated += 1
            continue
        seen.add(chunk)
        kept.append(chunk)
    compact = '\n\n'.join(kept) if repeated else feedback
    result = {'code': previous['code'], 'feedback': compact}
    receipt = {'method': 'exact_paragraph_deduplication', 'llm_calls': 0,
               'code_sha256': digest(previous['code']), 'code_characters': len(previous['code']),
               'code_truncated': False, 'diagnostic_sha256': digest(feedback),
               'delivered_diagnostic_sha256': digest(compact),
               'diagnostic_source_characters': len(feedback),
               'diagnostic_delivered_characters': len(compact),
               'repeated_paragraphs_removed': repeated,
               'history_policy': 'latest_complete_candidate_and_latest_public_feedback'}
    return result, receipt


def _blocks(text):
    """Markdown paragraphs, preserving each fenced code block as an atomic unit."""
    blocks, current, fence = [], [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif (marker[1][0] == fence[0] and len(marker[1]) >= len(fence)
                  and not line[marker.end():].strip()):
                fence = None
        if not line.strip() and fence is None:
            if current:
                blocks.append(''.join(current))
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(''.join(current))
    return blocks


def distill_documentation(paths, targets, max_characters):
    """Rank complete public-document blocks; never clip signatures or code fences.

    The same policy applies to every arm. Source implementations and test answers
    are not inputs. Oversized blocks are omitted explicitly, never sliced.
    """
    text = '\n\n'.join(Path(p).read_text() for p in paths)
    blocks = _blocks(text)
    if len(text) <= max_characters:
        return text, {'method': 'whole_public_document', 'source_characters': len(text),
                      'delivered_characters': len(text), 'selected_block_indices': list(range(len(blocks))),
                      'omitted_block_indices': [], 'truncated': False, 'delivered_sha256': digest(text)}
    patterns = [re.compile(r'(?<!\w)' + re.escape(t) + r'(?!\w)') for t in targets]
    relevance = [sum(len(p.findall(block)) for p in patterns) for block in blocks]
    order = sorted(range(len(blocks)), key=lambda i: (-relevance[i], i))
    selected, size = [], 0
    for i in order:
        addition = len(blocks[i]) + (2 if selected else 0)
        if size + addition <= max_characters:
            selected.append(i)
            size += addition
    # Preserve source order so a heading continues to precede its example.
    selected.sort()
    delivered = '\n\n'.join(blocks[i] for i in selected)
    return delivered, {'method': 'whole_block_public_document_retrieval', 'source_characters': len(text),
                       'delivered_characters': len(delivered), 'selected_block_indices': selected,
                       'omitted_block_indices': [i for i in range(len(blocks)) if i not in selected],
                       'truncated': False, 'omitted': len(selected) < len(blocks),
                       'delivered_sha256': digest(delivered)}


def render_guidance(selection, max_characters):
    """Deliver complete source annotations or report an explicit allowance omission."""
    selected = selection['matched']
    delivered, omitted, texts = [], [], []
    for hint in selected:
        text = ('Function: ' + hint['function_id'] + '\nExact signature:\n' + hint['signature']
                + '\nViolated requirement: ' + hint['requirement']
                + '\nCorrective action: ' + hint['action']
                + '\nValidation: ' + hint['validation']
                + '\nStatus: source guidance; repair still requires execution validation')
        size = len('\n\n'.join(texts + [text]))
        if size > max_characters:
            omitted.append({'function_id': hint['function_id'], 'requirement_id': hint['requirement_id'],
                            'reason': 'complete_guidance_exceeds_character_allowance'})
            continue
        texts.append(text)
        delivered.append(hint)
    text = '\n\n'.join(texts)
    return text, {'eligible': True, 'diagnosis': selection['diagnosis'], 'reason': selection['reason'],
                  'matched': selected, 'delivered': delivered, 'omitted': omitted,
                  'text': text, 'delivered_characters': len(text), 'delivered_sha256': digest(text),
                  'truncated': False}
