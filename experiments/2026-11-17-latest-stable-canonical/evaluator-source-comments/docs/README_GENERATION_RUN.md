# Isolated, recorded README generation

Use `scripts/run_readme_generation.py` for new Gemini authoring. It invokes the
current native engine directly and keeps authoring separate from Original R0
measurements. Do not reuse a preserved Codex audited session or old output path.

The default selection is every API name discovered by the configured static
surface. This is not a claim to cover all public APIs in an entire upstream
repository. Current configured scopes are RDPro 50, MDAnalysis 1,032, tslearn
235, mir_eval 148 and Thumbnailator 149: **1,614 entries**. RDPro's Original R0
manifest has 16 selected names; use `--scope manifest` only when deliberately
matching that subset. The manifest records every selected definition and
signature. Names are grouped by bare method name, including same-name declarations
on different receivers. A receiver-qualified protocol would require a new scope.

From the toolkit checkout, with its native Python environment:

```sh
python scripts/run_readme_generation.py --catalog /absolute/linux-catalog.yaml \
  --output /absolute/readme-full-run --prepare

python scripts/run_readme_generation.py --catalog /absolute/linux-catalog.yaml \
  --output /absolute/readme-pilot-run --sample 1 --run

python scripts/run_readme_generation.py --catalog /absolute/linux-catalog.yaml \
  --output /absolute/readme-full-run --run
```

Omit both `--prepare` and `--run` to print a read-only schedule. `--libraries`
selects explicit catalog libraries. The model defaults to
`gemini-3.1-flash-lite`. The key comes from the process environment and is never
written by this launcher. Paths must be correct for the machine running the
experiment; the Mac catalog is not a Linux runtime catalog.

The pilot uses the first sorted API name. Original R0 `--sample 1` uses its own
seeded sampling, so those two pilots need not select the same API. The full
command processes every selected API. Changing the scope, sample count, model,
source, effective prompts, profile, configuration, engine, provider timeout/retry
settings or installed provider versions requires a new output path.

Each library owns its own `configs/`, `inputs/api_manifest.json`, `launch.json`,
`author_calls/`, `.aideal_exec/readme_generation_state.json`, `console.log`,
`docs/LLM_readme.md`, `result.json` and `completion.json`. The batch owns one lock
and `summary.json`. Original source trees and documentation are reused by their
bound paths; measured Original R0 results are never edited or consumed as author
failure hints. API probes and automatic preamble/I/O-hint calls are disabled.

Every distillation and entry request stores its exact system/user text, model,
response, elapsed time, and native provider-reported usage. A failed or
interrupted call has a separate retained attempt, with unknown usage recorded as
null when no usage was received. SDK retries may still happen inside one logical
call and are distinct from README entry retries. Native provider defaults have
no explicit output-token cap; this launcher does not claim a hard cost bound.

A provider failure, empty response or malformed entry stops the current run.
Repeat the identical command to resume: verified successful requests replay from
receipts without another provider call; failed/interrupted requests get a new
numbered attempt. A previously uncertain request may have consumed provider
credits, so its missing usage is never represented as a known zero charge.

The prior README remains intact until a complete replacement is ready. Partial
work lives in receipts and a `.pending` preview. The final completion gate checks
all selected names, no duplicate/placeholder entries, the native completion
state and output hashes. Resume also verifies completed call evidence. A
completion receipt means `authored_not_execution_validated`; authoring alone
does not establish that generated examples compile, execute or pass independent
correctness checks. Evaluation is a separate frozen step.

Author requests may contain source facts, source documentation and mined test
examples. Audience R0 requests remain restricted to their configured Original
documents, public fixture descriptions and receiver/execution guidance; never
add `author_calls`, generated entries, source windows, private checker output or
source-informed review to those prompts.
