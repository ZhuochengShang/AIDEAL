# Ablation execution status

This is a timestamped snapshot, not a live monitor. Run `progress.py` on the cluster for current evaluation counts.

## Generated README R0

Observed **2026-11-18T17:50:51.157415+00:00**. Model `gemini-3.1-flash-lite`, one trial, zero program repairs, same selected API bank and native execution checks as Original R0.

| Bank | Original R0 | Generated README R0 |
|---|---:|---|
| mir_eval | 128/178 (71.9%) | 119/178 (66.9%) |
| thumbnailator | 104/225 (46.2%) | 83/225 (36.9%) |
| sedonadb | 78/217 (35.9%) | 100/217 (46.1%) |
| tslearn | 219/362 (60.5%) | running; 88/362 processed |
| rdpro_java | 13/69 (18.8%) | running; 37/69 processed |
| rdpro_scala | 24/261 (9.2%) | pending; 0/261 processed |
| mdanalysis | 612/1538 (39.8%) | pending; 0/1538 processed |

No provider-blocked targets were present at this snapshot. These are native execution/check outcomes; they are not independently adjudicated puzzle scores. The preliminary results vary by library. They do not support assuming that generated documentation always improves performance.

## Remaining condition gates

| Stage | Evidence / current state | Next required step |
|---|---|---|
| README branches | Exact authored files installed in all six public repositories | Continue matched R0 evaluation |
| Alias development | Fresh alias-only, compact-context queue launched; full API evidence retained | Complete proposals, build and validate forwarding behavior before installation |
| mir_eval native hint | Transcription hint passed four paired controls, eight executions; installed in Error Hints only | Verify condition runtime and run audience repair experiment |
| MDAnalysis native hint | `check_box` hint passed paired controls and geometry checks; source and dependent-module runtime smoke installed | Run the separately frozen audience repair experiment |
| Other native hints | All Original failures retained; RDPro/tslearn/Thumbnailator have no eligible sites under the current literal-message patcher | Extend supported edits or report no accepted treatment; never substitute a JSON prompt hint |
| SedonaDB source treatments | The current alias/hint adapter does not support the registered SQL bank | Implement and validate a SQL-native treatment adapter before these conditions |
| Combined | Generated README installed; mir_eval and MDAnalysis native hints also installed | Require the same accepted aliases/hints as individual conditions before labelling the treatment complete |
| Matched R0–R2 | New protocol under software checks | Use previous program and bounded native diagnostics consistently across conditions |
| Deep-dive README repair | Planned after R2 | Revise failed entries, freeze revised README, then fresh evaluation |

Hint validation establishes the source edit's tested behavior. It is not an audience repair result. Both current validated corrected callers use new synthetic examples rather than preserving the original benchmark fixture. Native hints reach the model through execution feedback during repairs, not the initial prompt.

## Review commands

```bash
ssh lab
cd /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical
/home/zshan011/apps/aideal/venv/bin/python operator/ablation/2026-11-18/progress.py
```

Current Generated README outputs are in `ablation-2026-11-18/generated-readme-r0/<bank>/`. Review `GENERATED_LAUNCH.json`, `configs/generated_readme.yaml`, `docs/LLM_readme.md`, and each `execution/run_*/attempt_*` directory for the exact request, response, program and diagnostic. `result.json`, `REPORT.md` and `completion.json` are final only for completed jobs.

Alias previews and model outputs are in `ablation-2026-11-18/development/aliases-only-proposals/<bank>/`. Native-hint authoring and controls are in `native-hint-authoring-2026-11-18/`. Operator records are in `operator/ablation/2026-11-18/`.

## Code changes checked today

The development runtime accepts an explicit aliases-only scope, removes repeated API exposure data from model requests while retaining full hash-bound evidence, and reads both list and structured API manifests plus the default Scala program filename. Forty focused regression checks passed on the final 275-file forwarding-authoring release. Ten repair-protocol tests and two actual native R0/R1/R2 scripted chains also passed without provider calls. Running evaluations keep their earlier frozen engines.
