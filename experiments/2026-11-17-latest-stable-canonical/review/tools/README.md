# Review-only native trace helper

These staged helper files extend the existing trace observer and read-only viewer.
They do not replace or modify the pinned `a6e8bb84fe32` production evaluator.
Keep `trace_original_micro.py`, `trace_view.py`, and `trace_view.html` together in
the review package's tools/scripts directory. Point `--toolkit` or `AIDEAL_TOOLKIT` to the
verified evaluator root containing `scripts`, `workflow`, and `vendor/aideal_engine`.

Preview one exact catalog target in a fresh output directory:

```sh
python review/tools/scripts/trace_original_micro.py --toolkit /path/to/pinned/evaluator \
  --catalog /path/to/study/PILOT_CATALOG.yaml --library sedonadb --api ST_Area \
  --preview --repairs 2 --output /path/to/fresh/review-preview
```

Preview uses the real native prompt construction and stops immediately after its
R0 `request.json` is written, before the provider boundary. It makes zero model
calls and executes no generated program. No response, provider failure, verdict,
or repair result is fabricated. `TRACE.html`, the source snapshot, selected
documentation, exact request, and `preview.json` are available for review.
An isolated preview relocates its output directory; comparisons must disclose
that exact path difference when the task bank was rendered for another namespace.

R1/R2 prompts depend on actual earlier code and failures. They do not yet exist
in a preview. After the user approves a live pilot, replacing `--preview` with
`--live --pause` invokes the existing native loop with at most two repairs.
It pauses for the prompt, response, complete rendered program and command, and
execution output. An R0 pass ends the loop; later rounds are never forced.
For an approved live run, `--key-file /path/to/private/single-line-key.txt` reads
the private file only in `--live` mode and sets the controller's `GOOGLE_API_KEY`
without printing it. Empty or multiline keys are rejected. Preview ignores this
argument entirely, so it does not require the file to exist. An existing key in
the environment also remains supported when no key file is supplied.
Generic catalog libraries have no invented scripted responses. Existing demo
and RDPro scripted modes remain separate and perform real execution, so they
must not be used during a preview-only hold.

The six pilot inputs live at the study root: `PILOT_CATALOG.yaml` references one
API per library in `pilots/inputs/<bank>/api_manifest.json`. All source links are
unchanged. Sedona alone uses a separate `libraries/sedonadb/configs/aideal.review-repairs.yaml`:
it replaces the baseline's "No repairs are permitted in this R0 run." sentence
with an explicit initial-attempt-plus-two-repairs policy. Every other config byte
is preserved. The helper's `--repairs 2` sets the effective round limit. Baseline
catalogs, configs, full-bank prompts and v2 previews remain unchanged.

`pilot_inputs/PILOT_INPUT_RECEIPT.json` and `sedonadb-review-repairs.diff` record
that declared change. The new Sedona v3 preview differs from baseline R0 only in
that sentence and the isolated output directory. Its comparison receipt records
both differences; it is not a claim of exact baseline prompt identity. The
portable `pilot_inputs` copies are review evidence containing the exact cluster
paths. They do not relocate or replace the primary bound study inputs.

The native engine remains the sole repair loop. Full requests, responses,
programs, stdout, stderr, execution metadata, provider accounting and verdicts
are retained for every actual attempt. Source-informed review notes are not
inserted into audience prompts. The viewer supports Scala, Java and Python
program files, and labels preview artifacts separately from live evidence.

Run the synthetic contract tests with an explicit shared toolkit:

```sh
AIDEAL_TOOLKIT=/path/to/pinned/evaluator PYTHONDONTWRITEBYTECODE=1 \
  python -m unittest discover -s review/tools/tests -p test_generic_trace_preview.py -v
```

The seven contracts cover all six catalog keys in preview mode, the native
R0/R1/R2 observer path with fake provider/process boundaries, the native default
program filename, and Java evidence display. They make no model calls or
scientific-library program executions. Authentication checks use temporary fake
keys only; they never read an actual private key file or call a provider.
