"""Historical JSON/comment hint delivery; native exception hints never call this.

Preserve the exact schema 1/2 prompt bytes and exposure receipts for explicit
compatibility studies. New studies use native runtime feedback instead.
"""
from .ablation import bind, digest, load
from .repair_context import render_guidance
from .source_hints import select_source_hints


def append_legacy_guidance(frozen, arm, case, previous, prompt, receipt):
    """Append the historical repair supplement and update its exposure receipt."""
    # Use the condition settings and prior failure to select legacy guidance.
    # Return the supplemented prompt and update the receipt with what fits its character budget.
    cfg = frozen['config']
    common, condition = cfg['common'], cfg['conditions'][arm]
    if previous is not None and 'source_hints' in condition:
        selection = select_source_hints(frozen['source_hint_indexes'][arm], previous)
        text, hint_receipt = render_guidance(selection, common['hint_max_characters'])
        receipt['hints'] = hint_receipt
        receipt['hint_characters'] = len(text)
        if text:
            prompt += '\n\nSOURCE-EMBEDDED REPAIR GUIDANCE\n' + text
    if previous is not None and 'error_hints' in condition:
        identities = {cfg['api_function_ids'][api] for api in case['target_apis']}
        matched = []
        for index, h in enumerate(load(condition['error_hints'])['hints']):
            if h['function_id'] in identities and h['error_contains'] in previous['feedback']:
                text = ('Function: ' + h['function_id'] + '\nUnverified development hint\nLikely cause: '
                        + h['likely_cause'] + '\nFix steps:\n' + '\n'.join('- ' + s for s in h['fix_steps'])
                        + '\nSuggested code:\n' + h.get('suggested_fix_code', '')
                        + '\nCheck the result: ' + h['validation'])
                matched.append((index, digest(h), text))
        source = '\n\n'.join(x[2] for x in matched)
        delivered = source[:common['hint_max_characters']]
        # Measure how many characters from each matched hint survive the shared budget.
        start = 0
        shown = []
        for index, hint_id, text in matched:
            available = max(0, min(len(text), len(delivered) - start))
            if available:
                shown.append({'index': index, 'hint_sha256': hint_id, 'delivered_characters': available})
            start += len(text) + 2
        receipt['hints'] = {'eligible': True, 'artifact': bind(condition['error_hints']),
                            'matched': [{'index': i, 'hint_sha256': h} for i, h, _ in matched],
                            'delivered': shown, 'text': delivered, 'source_characters': len(source),
                            'delivered_characters': len(delivered), 'delivered_sha256': digest(delivered),
                            'truncated': len(delivered) < len(source)}
        receipt['hint_characters'] = len(delivered)
        if delivered:
            prompt += '\n\nPOST-FAILURE DEVELOPMENT HINTS\n' + delivered
    return prompt
