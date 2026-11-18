# Lab cluster and step-by-step walkthrough

The current standalone AIDEAL pipeline is deployed through the `lab` SSH alias
on `ec-hn.cs.ucr.edu`. Open `/home/zshan011/apps/aideal/current` for code and
`/home/zshan011/apps/aideal/runs` for new output. The `current` link selects a
verified release. Release directories contain a SHA-256 file manifest identifying
the exact local working-tree code, including current files not yet committed to Git.

The older deployment at `/home/zshan011/apps/grail-vldb/repo` serves the live
GRAIL demonstration. The standalone AIDEAL update leaves that service and its
credentials, data and saved experiments unchanged.

## One script to print or debug R0, R1 and R2

Open the AIDEAL repository folder in Terminal, VS Code, or your coding-agent
terminal. Use Python 3.10 or later with PyYAML. This script traces the **native
microbenchmark loop used by `run_original_micro.py`**. It executes real Python
programs and uses clearly labelled mocked model responses, with no key or paid
calls. The full-library launcher remains configured for Original R0 only.

On your Mac:

```zsh
cd /Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow
/Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python scripts/trace_original_micro.py
```

On the lab server:

```bash
ssh lab
cd /home/zshan011/apps/aideal/current
/home/zshan011/apps/aideal/venv/bin/python scripts/trace_original_micro.py
```

In another Linux environment or a VS Code/Devin terminal:

```bash
python3 scripts/trace_original_micro.py
```

The default demonstration deliberately produces these three actual executions:

| Round | Model role | Mocked assertion | Observed result |
|---|---|---|---|
| R0 | Audience | `double(3) == 5` | Assertion failure; record feedback |
| R1 | Fixer | `double(3) == 7` | Assertion failure; retain both failures |
| R2 | Fixer | `double(3) == 6` | Pass; stop the loop |

The function always returns 6. Deterministic replies make the repair loop easy
to inspect; they are not evidence of an LLM learning or solving this example.
The real loop is `for attempt in range(1 + max_fix_rounds)`. With two repairs,
R0 is the initial program and R1/R2 are the two subsequent attempts.

Use the same script in these modes:

```bash
# Pause for Enter at main steps and around every round's execution.
python3 scripts/trace_original_micro.py --pause

# End after R0 or R1, to inspect stopping at a smaller repair limit.
python3 scripts/trace_original_micro.py --repairs 0
python3 scripts/trace_original_micro.py --repairs 1

# Keep R2 incorrect and stop after the configured two repairs.
python3 scripts/trace_original_micro.py --fail

# Step through Python with the standard debugger.
python3 -m pdb scripts/trace_original_micro.py
```

For VS Code, open this script, select the configured Python interpreter, set a
breakpoint in `trace_model` or `trace_execution` (older cluster snapshots call the model observer `mock_model`), and use **Run and Debug → Python
File**. The console also prints verified source file/line locations for the
actual native runner, prompt renderer, execution function, error classifier and
error-memory methods. Set a breakpoint on the displayed repair-loop line to
follow the engine itself. `--pause` provides a simpler Enter-to-continue view.

The terminal and saved `trace.log` show seven numbered stages:

1. The tiny example library and supplied original README.
2. Configuration, selected API, actual function/file/line map and prompt template.
3. Each round's exact system/user input, prior failure feedback and mocked response.
4. Each complete program before execution, followed immediately by its real command,
   exit code, standard output and standard error.
5. Per-round verdicts, total attempts, pass/limit stopping reason and accounting.
6. Checkpoint reuse with zero new model calls, for a completed pass or failure.
7. Paths to every saved artifact. Each `attempt_0001`, `attempt_0002`, or
   `attempt_0003` directory retains its own prompt, response, program and output.

The default creates a fresh temporary folder and prints its location. Add
`--output /path/to/a/new/folder` to save elsewhere; an existing nonempty folder
is rejected. The script demonstrates resume internally without overwriting
prior attempts. Mock token counts are unavailable. Reported walkthrough time
includes printing and any pauses, so it is not experiment timing. The README
is supplied as evaluation input; this example does not generate or revise it.
It exercises the native API microbenchmark path. The independent-oracle task
runner in `workflow/evaluation_runner.py`, puzzle tasks and treatment development
remain separate workflows.

## Full library experiments still need cluster inputs

Updating the toolkit does not transfer the six source checkouts, fixtures,
prebuilt Java/Scala runtime dependencies, or Linux builds of Python extensions.
The Mac catalog contains absolute Mac paths and Darwin extensions, so it is
excluded from the cluster deployment. Use an explicit Linux catalog with
`scripts/run_original_micro.py --catalog PATH --output PATH --prepare` before
starting paid work. No full library experiment is launched by this update.

The lab host has `tmux` and `screen`; the inspected shell has no Slurm/PBS/LSF
commands. Use the lab-approved execution node for long jobs. A detached `tmux`
session survives disconnects. Provider access and quota failures still require
attention; the R0 launcher checkpoints the affected API and stops.

## Environment and version checks

The standalone environment is `/home/zshan011/apps/aideal/venv`. Its direct
provider dependencies are listed in `requirements-native.txt`. It is separate
from the live GRAIL environment. Existing secrets are not copied into the release.
A model key must be made available to the shell or job that runs paid evaluation.

Read `DEPLOYMENT_MANIFEST.json` in the selected release to inspect hashes. The
cluster update receipt under `checks/` records validation, and `/home/zshan011/apps/aideal/runs/` holds
new execution evidence. Replacing `current` affects new invocations; already
running jobs should retain their own release and output directory.
