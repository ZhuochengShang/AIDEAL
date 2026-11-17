# Current review commands — execution remains blocked

The approved replacement count and run plan do not exist yet. The prior 1,695-target plan and six pilot input bundles are superseded. No model, subject-program or treatment run is authorized by this runbook.

## Review locally

```bash
cd "/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical"
python3 verify_snapshot.py
open review/REVIEW_HOME.html
open review/api-audit/API_AUDIT.html
open review/EXPERIMENT_TRACKER.html
```

The [guide](EXPERIMENT_GUIDE.md), [version lock](STUDY_LOCK.json), [source/document audit](review/api-audit/API_AUDIT.md) and [tracker](review/EXPERIMENT_TRACKER.json) define current scope and blockers. The saved [task previews](review/CURRENT_BANK.html) and [pilot previews](review/PILOT_REVIEW.html) are historical preparation evidence; opening them does not send a request or run a program.

## Inspect the cluster without launching

```bash
ssh -o ClearAllForwardings=yes lab
STUDY=/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical
cat "$STUDY/REVIEW_STATUS.json"
cat "$STUDY/PRELAUNCH_CHECKS.json"
cd "$STUDY/review_snapshot"
python3 verify_snapshot.py
```

The expected hold is `requires_api_surface_revision`, with generation and evaluation disallowed. Do not create an approval file for the old plan or restart its supervisor. VS Code Remote SSH can inspect the same pinned files and recorded controls; native Mac scientific execution remains unvalidated.

## Required before any replacement run

1. Complete the public source/exposure ledger and resolve defining ownership, uncertain candidates and wrapper-to-retained-target mappings.
2. Carry qualified target IDs through selection, README entries, task IDs, verification and installation. Distinct owners stay separate; overload reduction stays within one qualified API.
3. Bind version-matched original documents to those targets and review retrieval/context policy. Recalculate coverage and costs.
4. Freeze a new shared bank, pilot inputs, output namespace and run plan. Revalidate the changed integration paths without paid calls first.
5. Present that concrete replacement for the requested pre-run review. Publish new executable instructions only after the reviewed inputs and protocol are ready.

The [tracker](review/EXPERIMENT_TRACKER.html) separates these prerequisites from R0, R1/R2, README revision, fresh evaluation and the unscheduled puzzle/protocol studies. The 25 retained runtime-control outcomes are setup evidence, not six completed end-to-end model pilots.

## Code and historical reference

The portable [frozen evaluator](evaluator/README.md) is the prior release, not the new origin-filter working revision. Inspect the [origin-filter documentation](review/api-audit/code_updates/docs/API_ORIGIN.md) for that separate staged/working change. It does not complete the public inventory or migrate qualified README identities by itself.

[Historical operator commands](review/api-audit/PRIOR_RUNBOOK.md) preserve the old preview/live/README examples for provenance. They are not replacement launch commands. No key needs to be opened to review these files.

Local, cluster and GitHub pages are snapshots. After a reviewed change or later approved run, synchronize a newly hashed snapshot; do not alter measured evidence to match a claim.
