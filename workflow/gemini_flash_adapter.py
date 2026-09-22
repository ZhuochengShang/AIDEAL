"""One Gemini 3 Flash request, with explicit low/minimal thinking and no retries."""
import argparse
import hashlib
import json
import os
import sys

if __package__:
    from .model_adapter import response_record as base_response_record
else:
    from model_adapter import response_record as base_response_record


def response_record(response):
    """Retain evaluator-compatible totals and distinguish visible/reasoning usage."""
    record = base_response_record(response)
    usage = response.usage_metadata
    if usage is not None:
        record['usage'].update({
            'visible_output_tokens': usage.candidates_token_count,
            'thinking_tokens': usage.thoughts_token_count,
            'cached_input_tokens': usage.cached_content_token_count,
            'tool_use_prompt_tokens': usage.tool_use_prompt_token_count,
            'total_tokens': usage.total_token_count,
        })
    candidate = (response.candidates or [None])[0]
    reason = getattr(candidate, 'finish_reason', None)
    record['finish_reason'] = getattr(reason, 'value', reason)
    record['finish_message'] = getattr(candidate, 'finish_message', None)
    record['truncated'] = record['finish_reason'] == 'MAX_TOKENS'
    block = getattr(response.prompt_feedback, 'block_reason', None)
    record['prompt_block_reason'] = getattr(block, 'value', block)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--thinking-level', choices=('low', 'minimal'), default='low')
    parser.add_argument('--timeout-ms', type=int, default=120000,
                        help='SDK HTTP timeout in milliseconds (default: 120000)')
    args = parser.parse_args(argv)
    if args.timeout_ms <= 0:
        parser.error('--timeout-ms must be positive')
    request = json.load(sys.stdin)
    if request['model'] != 'gemini-3-flash-preview':
        raise ValueError('This adapter requires model gemini-3-flash-preview')
    cap = request['max_output_tokens']
    if type(cap) is not int or cap <= 0:
        raise ValueError('max_output_tokens must be a positive integer')
    key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('Set GOOGLE_API_KEY or GEMINI_API_KEY in the launching environment')

    # Lazy imports keep --help and configuration inspection offline.
    from google import genai
    from google.genai import types

    settings = {
        'model': request['model'], 'thinking_level': args.thinking_level,
        'include_thoughts': False, 'temperature': request['temperature'],
        'max_output_tokens': cap, 'candidate_count': 1,
        'timeout_ms': args.timeout_ms, 'http_attempts': 1,
        'api_version': 'v1beta', 'base_url': 'https://generativelanguage.googleapis.com',
        'vertexai': False, 'sdk_version': genai.__version__,
    }
    with genai.Client(api_key=key, vertexai=False, http_options=types.HttpOptions(
            api_version=settings['api_version'], base_url=settings['base_url'], timeout=args.timeout_ms,
            retry_options=types.HttpRetryOptions(attempts=1))) as client:
        response = client.models.generate_content(
            model=request['model'], contents=request['prompt'],
            config=types.GenerateContentConfig(
                system_instruction=request['system'], temperature=request['temperature'],
                max_output_tokens=cap, candidate_count=1,
                thinking_config=types.ThinkingConfig(
                    thinking_level=args.thinking_level, include_thoughts=False)))
    record = response_record(response)
    record['adapter_settings'] = settings
    record['adapter_settings_sha256'] = hashlib.sha256(json.dumps(
        settings, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    print(json.dumps(record))


if __name__ == '__main__':
    main()
