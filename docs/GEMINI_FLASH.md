# Lower-token Gemini Flash runs

The toolkit includes a separate adapter for explicit Flash settings. Existing frozen model commands are unchanged.

Configure the controller's model command as an argument list:

```json
["/path/to/python", "/path/to/AIDEAL_workflow/workflow/gemini_flash_adapter.py", "--thinking-level", "low", "--timeout-ms", "120000"]
```

Use the environment with `google-genai==1.67.0`. Credentials come from
`GOOGLE_API_KEY`, falling back to `GEMINI_API_KEY`; neither is saved in the response.
The destination is explicitly the Gemini Developer API at
`https://generativelanguage.googleapis.com`, API version `v1beta`.

The stdin JSON contract is unchanged: `model`, `system`, `prompt`, `temperature`,
and a positive integer `max_output_tokens`. The model must be
`gemini-3-flash-preview`. `--thinking-level` supports `low` (default) and `minimal`;
`--timeout-ms` defaults to 120000 milliseconds. The SDK receives one candidate,
no thought summaries, and exactly one HTTP attempt. No adapter retry, fallback,
token-count request, or follow-up generation is performed. Set the controller's
outer timeout above the SDK timeout so it can save provider failures normally.

The response retains `code`, `model_version`, `response_kind`, and the existing
usage totals. `usage.output_tokens` retains the existing sum of visible candidate
tokens and thinking tokens. New `visible_output_tokens`, `thinking_tokens`,
`cached_input_tokens`, `tool_use_prompt_tokens`, and `total_tokens` fields preserve
the SDK values; an unreported breakdown remains JSON `null`.

`finish_reason`, `finish_message`, `truncated`, and `prompt_block_reason` distinguish
normal completion, token-limit truncation, and prompt blocking. `truncated` means
the SDK reported `MAX_TOKENS`; other incomplete/blocked responses are not silently
reclassified. Empty output is still an empty solution with usage, while a transport
exception propagates to the existing controller. Truncated text is preserved for
evaluation and never automatically regenerated.

Each successful response saves effective `adapter_settings` and their canonical
JSON SHA-256. The controller must bind its complete command argument list, model
configuration, this adapter file, and the imported `model_adapter.py` file before
running. Keep explicit CLI flags in that configuration: request/command bindings
then preserve settings even when a provider error yields no response JSON.

Install `requirements-evaluation.txt` to exercise the Flash adapter tests. Base-only installations skip these 14 SDK-dependent tests when `google-genai` is absent.

Offline tests use actual SDK configuration/response classes and a mocked client:

```bash
python -m unittest discover -s tests -p 'test_gemini_flash_adapter.py' -v
```

No provider request was made to implement or test this adapter. Low/minimal thinking
does not guarantee a specific reasoning-token count or answer quality. A small
output limit can still yield an empty or truncated answer.

References: [model specification](https://ai.google.dev/gemini-api/docs/models/gemini-3-flash-preview)
and [supported thinking levels](https://ai.google.dev/gemini-api/docs/thinking).
