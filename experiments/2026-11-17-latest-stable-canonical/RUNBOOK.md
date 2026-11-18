# Review-only runbook

**Current state: ready for input review is not a completed scientific study.** The live review hold remains active. The commands below inspect or prepare inputs; they contain no live-run option and do not authorize model calls.

[Experiment guide](EXPERIMENT_GUIDE.html) · [All selected API/task inputs](review/qualified-bank/INDEX.html) · [Readiness fixes](READINESS_FIXES.html) · [History](HISTORY.md)

## Current package and scope

| Item | Current path / state |
|---|---|
| Qualified evaluator snapshot | `evaluator-qualified/` |
| Final evaluator release | `2026-11-17-qualified-api-f3c6fd6fe802` |
| Final evaluator content SHA256 | `f3c6fd6fe802716592df2d1342fc1b5bc9de5ca372aac880c196a240b2cb1838` |
| Integrated test receipt | [Final checks](review/qualified-checks/FINAL_VALIDATION.json) — 684 tests and 365 subtests passed on both Mac and lab cluster |
| Cluster preflight receipt | `review/qualified-checks/preflight/PREFLIGHT.json` |
| Seven-bank catalog | [RUN_CATALOG.cluster.yaml](review/qualified-plan/RUN_CATALOG.cluster.yaml) |
| Selected targets | 5,307 total; [source/doc count evidence](review/figures/qualified_count_data.json) |
| New output namespace | Cluster study `qualified/`; prior measured output trees remain unchanged |
| Initial full queue | 14 proposed jobs: seven Original R0 banks + seven README-authoring banks; held |

| Bank | Selected APIs |
|---|---:|
| `rdpro_scala` | 1,394 |
| `rdpro_java` | 1,393 |
| `mdanalysis` | 1,538 |
| `tslearn` | 362 |
| `mir_eval` | 178 |
| `thumbnailator` | 225 |
| `sedonadb` | 217 |

Source ledgers, manifests, exact target excerpts and pinned shared READMEs live under `review/qualified-api/<library>/`. Each bank's proposed scaffold, profile and configuration live under `review/qualified-plan/libraries/<bank>/`. A CSV plus row-level links are available in the [bank browser](review/qualified-bank/INDEX.html).

## Local review

Use the Mac or VS Code for reviewing the portable artifacts. A native Mac scientific execution environment is not certified. These commands verify local bytes and open the current input browser:

```bash
cd "/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical"
python3 verify_snapshot.py
open EXPERIMENT_GUIDE.html
open review/qualified-bank/INDEX.html
open review/qualified-pilots/INDEX.html
```

The standalone HTML loads local static scripts. It does not call a model, fetch remote data in the background or launch an experiment. If browser file policies block it, the CSV and Markdown are the direct review alternatives; no browser workaround is required.

## Cluster inspection and preparation

Use VS Code **Remote SSH** for the validated cluster environment. First connect and identify the reviewed snapshot:

```bash
ssh -o ClearAllForwardings=yes lab
STUDY=/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical
REVIEW="$STUDY/review_snapshot"
TOOLKIT="$REVIEW/evaluator-qualified"
CONTROL_PY=/home/zshan011/apps/aideal/venv/bin/python
CATALOG="$REVIEW/review/qualified-plan/RUN_CATALOG.cluster.yaml"
cd "$REVIEW"
python3 verify_snapshot.py
test -f "$TOOLKIT/scripts/run_original_micro.py"
test -f "$TOOLKIT/scripts/run_readme_generation.py"
test -f "$CATALOG"
```

Run preparation only after the final snapshot verification and preflight receipt identify the qualified evaluator. Preparation writes isolated input configurations, manifests and fingerprint receipts. It makes no model calls and runs no subject programs.

Prepare the complete Original R0 inputs into a review-specific output directory:

```bash
"$CONTROL_PY" "$TOOLKIT/scripts/run_original_micro.py" \
  --prepare \
  --catalog "$CATALOG" \
  --output "$STUDY/qualified/review_prepare/original_r0" \
  --model gemini-3.1-flash-lite \
  --libraries rdpro_scala rdpro_java mdanalysis tslearn mir_eval thumbnailator sedonadb
```

Prepare complete README-authoring inputs, using the exact selected manifest:

```bash
"$CONTROL_PY" "$TOOLKIT/scripts/run_readme_generation.py" \
  --prepare \
  --scope manifest \
  --catalog "$CATALOG" \
  --output "$STUDY/qualified/review_prepare/readme_authoring" \
  --model gemini-3.1-flash-lite \
  --libraries rdpro_scala rdpro_java mdanalysis tslearn mir_eval thumbnailator sedonadb
```

Keep the two output directories separate. A changed source, document, configuration, model or evaluator invalidates reuse; retain the old receipts and choose a newly identified output namespace. Do not reuse the superseded 1,695-target plan.

## What must be reviewed before live work

Review the selected IDs and unresolved boundaries, all six pilot target choices, actual prompt/data exposure, shared README plus exact excerpts, fixture/scaffold behavior, assertion/witness contract, independent-oracle limits, repair policy, request budget and output namespace. The first full queue proposes at least 10,614 per-API calls plus whole-corpus distillation chunks and any authorized provider retries; fourteen jobs does not mean fourteen model calls. The new [cost scenarios](review/qualified-plan/COST_SCOPE.md) cover 10,639 minimum requests, including 25 distillation chunks. They replace the reduced-bank forecast and remain estimates.

No runnable live command is supplied here. After approval, the operator should bind the approved plan hash and exact scope before launching. Six new end-to-end pilots, complete authoring/R0, later R1/R2, aliases/hints/Combined installation, and matched puzzle evaluation remain separate stages. A passing preflight or a prepared catalog does not count as their completion.

## Branches and immutable history

Five library branches remain under `study/2026-11-17-latest-stable-canonical/{original,readme-only,alias-only,error-hints-only,combined}`. Treatment installation is pending; the branch names do not establish that any treatment was applied. The original source commit and public snapshot commit can differ while sharing an identical tree.

The prior `evaluator/` and historical guide/results remain preserved. New operational code belongs to `evaluator-qualified/`; current native source/doc inputs belong to the qualified catalog. [HISTORY.md](HISTORY.md) is the place for previous measured cohorts and superseded commands.
