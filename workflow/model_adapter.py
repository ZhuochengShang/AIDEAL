"""One audience request through the installed Google SDK; no hidden retries.

Run using the environment already provisioned for AIDEAL. Credentials are read
from GOOGLE_API_KEY or GEMINI_API_KEY and are never written to evidence.
"""
import json
import os
import sys

if __package__:
    from .response_status import classify_record
else:
    from response_status import classify_record


def response_record(response):
    """Keep partial output and usage, and expose provider completion evidence."""
    code = response.text or ''
    record = {'code': code, 'model_version': response.model_version}
    candidates = getattr(response, 'candidates', None)
    candidate = (candidates or [None])[0]
    reason = getattr(candidate, 'finish_reason', None)
    block = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', None)
    record.update(finish_reason=getattr(reason, 'value', reason),
                  finish_message=getattr(candidate, 'finish_message', None),
                  prompt_block_reason=getattr(block, 'value', block),
                  completion_metadata_expected=hasattr(response, 'candidates'))
    record['truncated'] = record['finish_reason'] == 'MAX_TOKENS'
    usage = response.usage_metadata
    if usage is not None:
        record['usage'] = {
            'input_tokens': usage.prompt_token_count,
            'output_tokens': (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0),
        }
    return classify_record(record)


def main():
    # Lazy SDK imports keep configuration inspection and software tests offline.
    from google import genai
    from google.genai import types
    request = json.load(sys.stdin)
    cap = request['max_output_tokens']
    if type(cap) is not int or cap <= 0:
        raise ValueError('max_output_tokens must be a positive integer')
    key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('Set GOOGLE_API_KEY or GEMINI_API_KEY in the launching environment')
    client = genai.Client(api_key=key, http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=1)))
    response = client.models.generate_content(model=request['model'], contents=request['prompt'],
        config=types.GenerateContentConfig(system_instruction=request['system'],
            temperature=request['temperature'], max_output_tokens=cap))
    print(json.dumps(response_record(response)))


if __name__ == '__main__':
    main()
