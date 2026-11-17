"""Public treatment context with audited source guidance for the new protocol."""
from pathlib import Path

from .ablation import bind, digest
from .evaluation_readme import audience_prompt, select_documentation
from .repair_context import compact_previous, distill_documentation
from .native_hints import native_feedback_receipt


def public_context(frozen, arm, case, previous=None):
    # Build the audience prompt for one condition/task and optional failed attempt.
    # Select permitted documentation and alias/hint context, then return both the
    # prompt and a receipt of what was exposed. No LLM call happens here.
    # For native hints, guidance comes from execution feedback, not a hint lookup.
    cfg, condition = frozen['config'], frozen['config']['conditions'][arm]
    common = cfg['common']
    native = cfg.get('schema_version') == 3
    if native and any(k in condition for k in ('source_hints', 'error_hints')):
        raise ValueError('Native diagnostics cannot also retrieve external or comment hints')
    # Public canonical IDs include packages, while README headings often name
    # only the receiver or method. Keep retrieval useful under either spelling.
    retrieval_terms = sorted({term for api in case['target_apis']
                              for term in (api, '.'.join(api.split('.')[-2:]), api.split('.')[-1])})
    # Switch to compact documentation only for repair prompts when the
    # study has enabled distilled context.
    distilled = previous is not None and common.get('repair_context') == 'distilled'
    select = distill_documentation if distilled else select_documentation
    docs, exposure = select(condition['documents'], retrieval_terms,
                                           common.get('documentation_max_characters', 32000))
    exposure['retrieval_terms'] = retrieval_terms
    repair_previous, repair_receipt = compact_previous(previous) if distilled else (previous, None)
    prompt = audience_prompt(case, docs, repair_previous)
    receipt = {'documentation': exposure, 'alias': None,
               'hints': {'eligible': previous is not None, 'matched': [], 'delivered': [], 'text': '',
                         'source_characters': 0, 'delivered_characters': 0},
               'documentation_characters': len(docs), 'alias_characters': 0, 'hint_characters': 0}
    if native:
        # Native messages have already been emitted by the library and are part
        # of ordinary execution feedback. Never read a hint bank or source here.
        receipt['native_diagnostics'] = native_feedback_receipt(previous['feedback'] if previous else '')
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
    if not native and previous is not None:
        # Older studies explicitly opt into a separate compatibility path.
        from .evaluation_legacy_hints import append_legacy_guidance
        prompt = append_legacy_guidance(frozen, arm, case, previous, prompt, receipt)
    receipt['total_treatment_characters'] = sum(receipt[k] for k in
                                               ('documentation_characters', 'alias_characters', 'hint_characters'))
    receipt['public_prompt_characters'] = len(prompt)
    receipt['public_prompt_sha256'] = digest(prompt)
    return prompt, receipt
