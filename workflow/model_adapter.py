"""One audience request through the installed Google SDK; no hidden retries.

Run using the environment already provisioned for AIDEAL. Credentials are read
from GOOGLE_API_KEY or GEMINI_API_KEY and are never written to evidence.
"""
import json
import os
import sys


def response_record(response):
    """Preserve usage even when the model returns no code.

    An empty model answer is evaluated as an empty solution. It is different
    from a transport exception, which the caller records as provider_pending.
    """
    code = response.text or ''
    record = {'code': code, 'model_version': response.model_version,
              'response_kind': 'solution' if code else 'empty_model_output'}
    usage = response.usage_metadata
    if usage is not None:
        record['usage'] = {
            'input_tokens': usage.prompt_token_count,
            'output_tokens': (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0),
        }
    return record


def main():
    # Lazy SDK imports keep configuration inspection and software tests offline.
    from google import genai
    from google.genai import types
    request = json.load(sys.stdin)
    key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('Set GOOGLE_API_KEY or GEMINI_API_KEY in the launching environment')
    client = genai.Client(api_key=key, http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=1)))
    response = client.models.generate_content(model=request['model'], contents=request['prompt'],
        config=types.GenerateContentConfig(system_instruction=request['system'],
            temperature=request['temperature'], max_output_tokens=request['max_output_tokens']))
    print(json.dumps(response_record(response)))


if __name__ == '__main__':
    main()
