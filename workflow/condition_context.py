"""Public treatment context with audited source guidance for the new protocol."""
from pathlib import Path

from .ablation import bind, digest, load
from .evaluation import audience_prompt, select_documentation
from .repair_context import compact_previous, distill_documentation, render_guidance
from .source_hints import select_source_hints


def public_context(frozen, arm, case, previous=None):
    cfg, condition = frozen['config'], frozen['config']['conditions'][arm]
    if cfg.get('schema_version') == 2 and 'error_hints' in condition:
        raise ValueError('Source-guided protocol forbids legacy JSON hint lookup')
    common = cfg['common']
    # Public canonical IDs include packages, while README headings often name
    # only the receiver or method. Keep retrieval useful under either spelling.
    retrieval_terms = sorted({term for api in case['target_apis']
                              for term in (api, '.'.join(api.split('.')[-2:]), api.split('.')[-1])})
    distilled = previous is not None and common.get('repair_context') == 'distilled'
    selection = common.get('documentation_selection')
    targets = case['target_apis'] if selection is not None else retrieval_terms
    if selection is not None:
        # An explicit frozen section policy takes precedence over block ranking.
        docs, exposure = select_documentation(condition['documents'], targets,
                                               common.get('documentation_max_characters', 32000), selection)
    else:
        select = distill_documentation if distilled else select_documentation
        docs, exposure = select(condition['documents'], targets,
                                common.get('documentation_max_characters', 32000))
    exposure['retrieval_terms'] = retrieval_terms
    repair_previous, repair_receipt = compact_previous(previous) if distilled else (previous, None)
    prompt = audience_prompt(case, docs, repair_previous)
    receipt = {'documentation': exposure, 'alias': None,
               'hints': {'eligible': previous is not None, 'matched': [], 'delivered': [], 'text': '',
                         'source_characters': 0, 'delivered_characters': 0},
               'documentation_characters': len(docs), 'alias_characters': 0, 'hint_characters': 0}
    if repair_receipt is not None:
        receipt['repair_context'] = repair_receipt
    if 'alias_interface' in condition:
        source = Path(condition['alias_interface']).read_text()
        delivered = source[:common['alias_max_characters']]
        prompt += '\n\nADDITIONAL ALIAS INTERFACE\n' + delivered
        receipt['alias'] = {'artifact': bind(condition['alias_interface']), 'source_characters': len(source),
                            'delivered_characters': len(delivered), 'delivered_sha256': digest(delivered),
                            'truncated': len(source) > len(delivered)}
        receipt['alias_characters'] = len(delivered)
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
    receipt['total_treatment_characters'] = sum(receipt[k] for k in
                                               ('documentation_characters', 'alias_characters', 'hint_characters'))
    receipt['public_prompt_characters'] = len(prompt)
    receipt['public_prompt_sha256'] = digest(prompt)
    return prompt, receipt
