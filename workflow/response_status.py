"""Classify model completion separately from compilation and program correctness.

This module uses provider metadata, never guesses completeness from program text.
Adapters retain partial output for audit; callers must check ``executable`` before
passing it to an execution adapter. No classification retries or changes a cap.
"""


def _value(value):
    """Accept enum values from SDK records as well as their JSON representation."""
    return getattr(value, 'value', value)


def _selected_messages(record):
    messages = record.get('messages') or []
    final = [item for item in messages if item.get('phase') == 'final_answer']
    return final or [item for item in messages if item.get('phase') is None]


def solution_state(record):
    """Return an auditable completion decision for an adapter response dictionary.

    ``status`` is complete, incomplete, refusal, empty, or provider_failure.
    Only complete nonempty answers are executable. A legacy response without
    completeness metadata remains supported, but its unverified status is stated
    explicitly in ``reason``. The input dictionary and its code are not modified.
    """
    code = record.get('code')
    status = _value(record.get('response_status'))
    details = record.get('incomplete_details') or {}
    incomplete = record.get('incomplete_reason') or details.get('reason')
    finish = _value(record.get('finish_reason'))
    block = _value(record.get('prompt_block_reason'))
    selected = _selected_messages(record)
    message_statuses = [_value(item.get('status')) for item in selected]
    evidence = {'provider_status': status, 'incomplete_reason': incomplete,
                'finish_reason': finish, 'prompt_block_reason': block,
                'selected_message_statuses': message_statuses,
                'code_characters': len(code) if isinstance(code, str) else 0}

    def result(state, reason):
        return {'status': state, 'reason': reason, 'executable': state == 'complete',
                'evidence': evidence}

    if not isinstance(code, str):
        return result('provider_failure', 'invalid_code_field')
    if status in ('failed', 'cancelled') or record.get('error_code'):
        return result('provider_failure', 'provider_' + (status or 'error'))
    if record.get('refusals'):
        return result('refusal', 'provider_refusal')
    if block not in (None, '', 'BLOCKED_REASON_UNSPECIFIED'):
        return result('refusal', 'prompt_blocked_' + str(block).lower())
    blocked_finishes = {'SAFETY', 'RECITATION', 'BLOCKLIST', 'PROHIBITED_CONTENT',
                        'SPII', 'IMAGE_SAFETY', 'IMAGE_PROHIBITED_CONTENT'}
    if finish in blocked_finishes or incomplete == 'content_filter':
        return result('refusal', 'content_filter' if incomplete == 'content_filter'
                      else 'finish_' + str(finish).lower())
    if incomplete == 'max_output_tokens' or finish == 'MAX_TOKENS' or record.get('truncated') is True:
        return result('incomplete', 'max_output_tokens')
    if incomplete:
        return result('incomplete', str(incomplete))
    if status and status != 'completed':
        return result('incomplete', 'provider_' + str(status))
    if finish and finish != 'STOP':
        return result('incomplete', 'finish_' + str(finish).lower())
    for message_status in message_statuses:
        if message_status != 'completed':
            return result('incomplete', 'message_' + str(message_status or 'status_missing'))
    # Some custom adapters only report a kind. Use it as a fallback, preserving
    # more precise raw-provider reasons when both representations are present.
    for kind, state in (('provider_failure', 'provider_failure'),
                        ('refusal', 'refusal'), ('incomplete_model_output', 'incomplete')):
        if record.get('response_kind') == kind:
            return result(state, kind)
    if record.get('completion_metadata_expected') and not (status or finish or block):
        return result('incomplete', 'missing_completion_metadata')
    if not code.strip():
        return result('empty', 'no_model_code')
    if status == 'completed' or finish == 'STOP' or selected:
        return result('complete', 'provider_completed')
    return result('complete', 'legacy_nonempty_unverified')


def classify_record(record):
    """Attach the normalized state while retaining code, usage, and raw metadata."""
    state = solution_state(record)
    record['solution_state'] = state
    record['response_kind'] = {
        'complete': 'solution', 'incomplete': 'incomplete_model_output',
        'refusal': 'refusal', 'empty': 'empty_model_output',
        'provider_failure': 'provider_failure',
    }[state['status']]
    return record
