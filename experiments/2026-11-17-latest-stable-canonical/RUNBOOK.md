# Current hold — do not launch the prior plan

API and documentation correction is required. The old 1,695-target bank and costs are superseded preparation evidence. No new runs have started; the approved replacement count is pending. The cluster PRELAUNCH_CHECKS status is `requires_api_surface_revision`. The commands below are preserved preparation history and are not authorized replacement launch commands. See [the current guide](EXPERIMENT_GUIDE.md).

---

# Review and run commands

**Current state: held for your review.** The commands in sections 1–3 only inspect or prepare previews. Sections 4–6 are instructions for a later explicitly approved run; they have not been executed.

## 1. Where to work

| Location | Best use | Current readiness |
|---|---|---|
| Mac browser or VS Code | Read code, prompts, fixtures, charts and saved outcomes | Exact 225-file evaluator and portable review snapshot |
| VS Code Remote SSH → `lab` | Debug a real library with breakpoints while using the cluster key/runtime | Recommended for the six pilots |
| Cluster terminal or tmux | Run a reviewed batch without depending on your laptop session | Six Linux library runtimes checked |
| Native Mac Python execution | Separate local reproduction | Requires matching package/JVM/fixture setup and relocated configs; not yet validated |

A Git clone provides code and recorded settings. It does not install the Linux runtime on a Mac. For immediate execution from your Mac, connect to the cluster through its terminal or VS Code Remote SSH.

On your Mac:

```bash
cd "/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical"
open review/REVIEW_HOME.html
open review/CURRENT_BANK.html
open review/PILOT_REVIEW.html
```

Read [STUDY_LOCK.json](STUDY_LOCK.json) to identify the current code, six sources, branch names and all three review locations. [SYNC_MANIFEST.json](SYNC_MANIFEST.json) lists the exact review-file hashes. Historical results are in [HISTORY.md](HISTORY.md), with their own models and denominators.

## 2. Connect and inspect

From a Mac terminal:

```bash
ssh -o ClearAllForwardings=yes lab
```

In that cluster terminal:

```bash
STUDY=/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical
RELEASE=/home/zshan011/apps/aideal/releases/2026-11-17-canonical-api-a6e8bb84fe32
PYTHON=/home/zshan011/apps/aideal/venv/bin/python
HELPER="$STUDY/review_snapshot/review/tools/scripts/trace_original_micro.py"
cat "$STUDY/REVIEW_STATUS.json"
cat "$STUDY/PRELAUNCH_CHECKS.json"
cat "$STUDY/PILOT_CATALOG.yaml"
```

The controller uses Python 3.10. Library programs use the interpreter or JVM configured for that library, including the isolated Python 3.12 scientific environment. The key stays on the cluster. These inspection commands do not read it.

## 3. Preview one pilot without a model or program execution

The six proposed targets are selected definitions from the current bank.

| Catalog key | Exact API name | What the earlier positive infrastructure control checks |
|---|---|---|
| `rdpro_scala` | `numTiles` | Raster tile metadata and matching raster/vector/HDF fixtures |
| `mdanalysis` | `rmsd` | Self RMSD and a known coordinate shift |
| `tslearn` | `dtw` | Identical and different short time series |
| `mir_eval` | `f_measure` | Aligned and shifted beat timestamps |
| `thumbnailator` | `resize` | Output dimensions and fixture colors |
| `sedonadb` | `ST_Area` | A materialized SQL area result and a correctness assertion |

The operator controls are examples of valid runtime use. They are not hidden expected-answer programs supplied to the audience. A live pilot receives its recorded task/resource context and writes its own program.

```bash
PREVIEW_ID=review-preview-$(date +%Y%m%d-%H%M%S)
"$PYTHON" "$HELPER" \
  --toolkit "$RELEASE" --catalog "$STUDY/PILOT_CATALOG.yaml" \
  --library rdpro_scala --api numTiles --repairs 2 \
  --preview --output "$STUDY/pilots/$PREVIEW_ID/rdpro_scala"
```

Preview records the actual native R0 prompt, selected documentation, configuration and source locations, then stops before the model boundary. It produces `TRACE.html`, `request.json` and `preview.json`; it does not create a model answer or a verdict. R1/R2 prompts require real earlier failures and remain absent.

For another library, change both `--library` and `--api` according to the table. Each invocation needs a fresh output directory. Sedona's repair-pilot configuration explicitly replaces an R0-only prohibition on repairs; its baseline configuration and the 1,695 R0 previews remain unchanged. The policy diff is recorded with the pilot inputs.

## 4. After approval: run the six Original pilots interactively

This section spends Gemini credits and executes generated programs. Use it only after reviewing the six pilot cards and approving their inputs and repair policy. It performs at most 18 logical audience/fixer requests: R0 plus up to two repairs for each of six APIs. A pass ends that API's loop immediately; provider retries are additional attempts, not repair rounds.

```bash
PILOT_ID=reviewed-pilot-$(date +%Y%m%d-%H%M%S)
PILOT_CASES=(
  rdpro_scala:numTiles
  mdanalysis:rmsd
  tslearn:dtw
  mir_eval:f_measure
  thumbnailator:resize
  sedonadb:ST_Area
)
for case_spec in "${PILOT_CASES[@]}"; do
  library="${case_spec%%:*}"
  api="${case_spec#*:}"
  "$PYTHON" "$HELPER" \
    --toolkit "$RELEASE" --catalog "$STUDY/PILOT_CATALOG.yaml" \
    --library "$library" --api "$api" --repairs 2 \
    --model gemini-3.1-flash-lite \
    --key-file /home/zshan011/gemini-apikey-aideal.txt \
    --live --pause --output "$STUDY/pilots/$PILOT_ID/original/$library" || break
done
```

At each pause, inspect the printed prompt or output and the refreshed `TRACE.html`. Enter continues. Ctrl+C stops the helper; a request already sent may still incur usage. It pauses before sending the prompt and before executing the completed program. Do not treat an incomplete/provider-failed trace as a scored task.

| Artifact | What you can inspect |
|---|---|
| `configs/aideal.yaml`, `launch.json` | Exact configuration, source, model and repair scope |
| `inputs/selected_documentation.txt` | Original documentation selected for this API |
| `trace_sources.json`, `TRACE.html` | Function names, source lines, prompt/response/output panels |
| `execution/run_<API>/attempt_*/request.json` | Exact system/user messages and round number |
| `response.txt`, `ApiTest.*` or `api_test.py` | Raw reply and complete runnable program |
| `execution.json`, `stdout.txt`, `stderr.txt` | Actual command, return code and diagnostic |
| `provider.json`, `trace_provider.json` | Recorded model accounting and call time |
| `result.json`, `summary.json`, `logs/` | Native verdict, first passing round and failure history |

`attempt_0001` is the first persisted attempt, not R1. Read the `round` field: 0=initial program,1=first repair,2=second repair.

## 5. After approval: author one README entry per pilot

README authoring is a separate operation. It sends original-document text for distillation, then selected API facts, source comments, examples and the resulting summary to the author. It does not run the API example merely because an entry was authored.

First prepare without model calls:

```bash
"$PYTHON" "$RELEASE/scripts/run_readme_generation.py" \
  --catalog "$STUDY/PILOT_CATALOG.yaml" \
  --output "$STUDY/pilots/$PILOT_ID/readme" \
  --scope manifest --model gemini-3.1-flash-lite --prepare
```

After approving those authoring inputs, run the same command with `--run` instead of `--prepare`. The author launcher uses an environment key; the following reads the existing file without displaying it:

```bash
IFS= read -r GOOGLE_API_KEY < /home/zshan011/gemini-apikey-aideal.txt
export GOOGLE_API_KEY
"$PYTHON" "$RELEASE/scripts/run_readme_generation.py" \
  --catalog "$STUDY/PILOT_CATALOG.yaml" \
  --output "$STUDY/pilots/$PILOT_ID/readme" \
  --scope manifest --model gemini-3.1-flash-lite --run
unset GOOGLE_API_KEY
```

The six one-target manifests give six entries, not the entire 1,695-entry bank. Distillation may add one call per library. Read each library's saved `request.json`/`response.txt`/`provider.json`, generated `docs/LLM_readme.md`, and `completion.json`. The full distillation result and final entry prompt do not exist before this stage runs.

This command does not install pilot documents on the full-study branches. Installation must use the intended pilot condition refs and matching completion hashes. Alias proposals, embedded hints, generated-README reevaluation and Combined are separate reviewed stages shown in the tracker, not side effects of this command.

## 6. Full R0 plus README queue, only after separate approval

The prepared full plan has 14 jobs: seven language/library banks × Original R0 or README authoring. It uses 1,695 API targets, one baseline trial, zero program repairs and two workers. Its launch script refuses to start without a `USER_REVIEW_APPROVAL.json` whose plan hash matches `plan.json`. No approval file has been created.

After the pilots and full plan are reviewed, the operator can record that approval and start the existing pinned `launch.sh` in tmux. Approval applies to that exact plan, not every later treatment or repair experiment. Use the final approved plan's commands; never restart the stopped 1,348-target RDPro plan.

Once approved and started, these commands inspect progress:

```bash
cat "$STUDY/supervisor/summary.json"
cat "$STUDY/supervisor.pid"
tail -f "$STUDY/supervisor_console.log"
```

Ctrl+C stops `tail`, not the experiment. To stop a running queue, first verify that the saved PID belongs to this exact study's `run_cluster_experiment.py`; then send TERM only to that PID. The supervisor stops its own child process groups. Preserve checkpoints and provider receipts. Resume only an unchanged approved plan; changed inputs require a new study identity.

## 7. Debug in VS Code Remote SSH

1. Connect to `lab` using Remote SSH and open `$STUDY/review_snapshot`.
2. Select `/home/zshan011/apps/aideal/venv/bin/python` as the controller interpreter.
3. Open `review/tools/scripts/trace_original_micro.py`; use the preview mode first.
4. Put breakpoints in `trace_model` and `trace_execution`. Enable stepping into external code to enter the pinned engine's `_comprehension_execute` loop.
5. For a later approved live debug, use the same arguments as section 4, including `--toolkit`, `--key-file` and `--pause`.
6. Use F10 to step over, F11 to enter a function, Shift+F11 to return, and F5 to continue. At an `input()` pause, press Enter in the integrated terminal.

The source line links in [the guide](EXPERIMENT_GUIDE.md#10-exact-evaluator-code-to-review) identify the pinned code. The review helper observes that native loop; it does not implement a second repair algorithm. Local Mac review and Remote SSH execution therefore examine the same evaluator files while using the already checked Linux runtime.

## 8. Keep the three locations aligned

`SYNC_MANIFEST.json` covers the snapshot at its recorded review stage. Verify it after copying. The exact evaluator content hash is `a6e8bb84fe32644837603ee4c73a1100f5f51519dfdecbdc36c4ffc992ba98c1`.

GitHub and local HTML are snapshots, not live databases. A new approved run first writes cluster evidence. Refresh and republish a new reviewed snapshot to expose later results in all three locations; preserve the earlier manifest. Do not edit measured artifacts to make a score or hash match. The current snapshot contains zero new model results by design.
