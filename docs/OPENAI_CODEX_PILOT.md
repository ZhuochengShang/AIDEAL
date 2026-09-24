# Codex adapter and shared study budgets

This separate adapter uses `gpt-5.3-codex` through the OpenAI Responses API.
Install both new modules, `workflow/openai_codex_adapter.py` and
`workflow/provider_budget.py`, beside the existing controller. Existing Google
adapters and frozen controllers stay unchanged. Install the optional provider
dependency with `pip install -r requirements-openai.txt` (`openai==2.28.0`).

Use one ledger for every development and evaluation call in the same pilot:

```json
["/path/to/python", "/path/to/AIDEAL_workflow/workflow/openai_codex_adapter.py", "--budget-ledger=/path/to/study/development/codex_budget_v1.json", "--max-cost-usd=5"]
```

Keep the ledger flag and its path in **one equals-form argument**. A separate
absolute path argument would cause existing controllers to hash the mutable
ledger as a command artifact. Bind the adapter and budget-module files, the
complete command arguments, and the model configuration. Do not hash the mutable
ledger into a frozen command identity. Set the outer provider timeout above 120
seconds. Credentials come only from `OPENAI_API_KEY`.

## Request and result

Stdin remains JSON with `system`, `prompt`, `model`, `max_output_tokens`, and
`temperature`. Only text prompts and the exact model `gpt-5.3-codex` are accepted.
The output cap is passed unchanged and must be between 1 and 128000.

The endpoint is fixed to `https://api.openai.com/v1`. Each call uses low reasoning,
120-second SDK timeout, zero SDK retries, standard service tier, `store=false`,
no tools, no streaming, no background work, and disabled input truncation.
Requested temperature is recorded but **not sent**; the effective temperature is
the provider default, not a claimed deterministic zero. The adapter performs no
extra generation, token-count request, repair, or provider fallback.

Stdout retains `code`, `model_version`, and `usage.input_tokens/output_tokens`.
Output tokens already include reasoning and are never added twice. Separate
`reasoning_tokens`, `non_reasoning_output_tokens`, cached input, and total counts
are recorded. Non-reasoning output can include formatting tokens; it is not an
exact count of visible text. Effective parameters, requested temperature, SDK
version, prompt hashes, and a canonical settings hash accompany each result.

The adapter selects `final_answer` messages when present; otherwise it selects
unphased assistant text. Commentary alone is not executable code. Returned
message phases/text, refusal text, response ID/model/status, and incomplete reason
remain available for review; hidden reasoning content is not exposed. Completed
empty/refused answers remain empty solutions. Incomplete output preserves partial
text and usage without retry. Failed/cancelled/pending statuses are provider
failures, after accounting for any known usage.

## Budget behavior

The default `legacy-v1` policy retains schema 1 and a maximum of **$5 shared across calls using its ledger**. A smaller cap is allowed initially; changing it on resume is rejected. The historical pilot used this policy.

A new explicit `study-v2` policy permits a configured ceiling up to **$100**, requires a stable `study_id`, and uses schema 2. Use a new ledger path; an existing ledger cannot change its schema, cap, model or study identity. For command adapters, add `--budget-policy=study-v2 --study-id=YOUR_NEW_STUDY --max-cost-usd=100` to the equals-form ledger command. These flags authorize accounting policy only; they do not generate or evaluate a study. The native bridge requires this explicit policy; see [audited README sessions](README_SESSIONS.md).

Monetary
arithmetic uses integer nanodollars. Fixed standard prices are $1.75 per million
uncached input tokens, $0.175 cached input, and $14 output, verified against the
[model specification](https://developers.openai.com/api/docs/models/gpt-5.3-codex).
The guard covers token charges at these rates before tax, not account-wide spend.

Before HTTP, a request reserves `(UTF-8 bytes of system + prompt + 4096 framing
tokens) × uncached input price + maximum output tokens × output price`. This
deliberately overestimates ordinary text inputs and assumes no tools or additional
conversation state. Pending reservations count against the cap. A POSIX `flock`
on a persistent sibling `.lock` file serializes changes; ledger writes use atomic
replacement and filesystem synchronization. Concurrent development/evaluation
processes cannot reserve the same remaining capacity.

Final, valid input/cached/output usage replaces the reservation with its actual
token cost. Missing or malformed usage, nonfinal responses, transport errors,
5xx responses, and process interruption retain the full reservation. There is no
automatic reset or release command. Never delete/edit the ledger or its lock file
to regain capacity. Their identity marker rejects missing files, and resume checks
the schema, model, cap, prices, and record arithmetic. If observed usage exceeds
its reserved bound, actual cost is recorded and future calls are blocked for
review; the ledger cannot retroactively undo a provider charge.

The ledger stores hashes, IDs, token/cost counts and sanitized status metadata,
without prompt bodies or credentials. SDK errors expose only sanitized type,
status, error code and request ID; raw error bodies and chained SDK tracebacks are
suppressed. Other clients, different ledger paths, provider pricing changes, or
manual ledger alteration fall outside this local guard.

## Audited native text route

[Native `invoke_text`](../vendor/aideal_engine/src/aideal/llm.py) routes only an explicit `aideal-codex-audited` model registry entry through [native_provider_bridge.py](../workflow/native_provider_bridge.py). The bridge verifies source/policy hashes, writes exact request/settings/reservation evidence before HTTP, then saves response/result/outcome records. It requires completed nonempty output with accounted usage; incomplete, refused, uncertain or changed-contract results fail closed with evidence retained. There is no direct-provider fallback.

The same route serves prepared author, reviewer and fixer phases with separate stage directories and one immutable budget identity. [readme_receipts.py](../workflow/readme_receipts.py) verifies complete saved phase evidence against the settled ledger row on resume. This capability is implemented and tested offline; it does not claim that a newly prepared study has executed.

## Offline verification

```bash
python -m unittest discover -s tests -v
python -S -m unittest discover -s tests -p 'test_provider_budget.py' -v
```

The full suite requires base dependencies. The second command checks only the standard-library budget suite without site packages. Tests mock the provider client. Budget tests use only the standard library and
include competing processes. Without the optional SDK, adapter tests skip while
budget tests still run. No provider request is needed for either test command.
The installed SDK's Responses types are used when available.

See also the [Codex model guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.3-codex)
for reasoning and message-phase behavior. This adapter and its tests make no claim
about model task performance.

## Review the implementation

Follow the [provider stage](CODE_MAP.html#stage-codex_provider) and [budget stage](CODE_MAP.html#stage-codex_budget) in the downloaded interactive map. Review [request construction and phase-aware extraction](../workflow/openai_codex_adapter.py#L15), [reservation before HTTP](../workflow/provider_budget.py#L116), and [accounting after the response](../workflow/provider_budget.py#L148). The [function index](FUNCTION_INDEX.md) includes their static helpers.

A source/API preview is preparation: it makes no inference call and is not an evaluated model result. Actual study status comes from that study's saved request, provider, checker and report evidence.
