# AIDEAL: start here

**Current study, November 18, 2026:** Original R0 and README authoring completed for **2,850 targets across six libraries**. Generated README R0 is now running on the lab cluster; aliases, source-embedded hints, and the matched repair protocol are in development and validation.

[Current experiment guide](AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/EXPERIMENT_GUIDE.md) · [Ablation plan and commands](AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/operator/ablation/2026-11-18/PLAN.md) · [Original completion evidence](AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/operator/resume/2026-11-18/COMPLETION.md) · [RDPro's 330-target bank](AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/review/raptor-scope/README.md).

RDPro covers Raptor and supporting raster types, with 69 Java and 261 Scala targets. Older full-Beast counts and launch snapshots are historical. Use the timestamped current progress record rather than an old launch page.

**Earlier run readiness checked November 12, 2026:** [what runs automatically, what API access enables, and how to review the code](AIDEAL_workflow/docs/AUTOMATION_READINESS.md).

**Shared evaluation and code guide, November 12, 2026:** [clickable workflow](AIDEAL_workflow/docs/EVALUATION_CODE_GUIDE.html), [three-file reading route](AIDEAL_workflow/docs/EVALUATION_CODE_GUIDE.md) and [current treatment workflow](AIDEAL_workflow/docs/TREATMENT_WORKFLOW.md). Canonical evaluation files share the `evaluation_` prefix. File/line links follow the current source. September study/status links below retain their historical meaning.

The navigation below was recorded September 22, 2026; use the current study links above for the latest prepared scope.
The four older `AIDEAL_*_LATEST.md` names now lead here.

**Supporting folders are now grouped in [AIDEAL_WORKSPACE](AIDEAL_WORKSPACE/README.md).**
The normal Finder view keeps these project entries visible:

```text
geoAI/
├── GRAIL/                 NL/Python → RDPro demo
├── GRAIL_WORKSPACE/       GRAIL-only support navigation
├── AIDEAL_workflow/       Current code, evidence and paper
├── AIDEAL_WORKSPACE/      Grouped supporting folders
├── AIDEAL_ARCHIVE/        Historical material and cleanup records
├── AIDEAL_START_HERE.md   This page
└── GS-QA-main/            Separate benchmark project
```

Unrelated projects in geoAI are unchanged. Older project paths are hidden from
normal Finder view and remain usable by jobs and saved references. If Finder is
showing hidden items, Command–Shift–period toggles them off. Terminal listings
can still show the original names.

| What you want | Open this | Status |
|---|---|---|
| All six libraries and new setups | [Study index](AIDEAL_WORKSPACE/03_Experiments/README.md) | Seven repositories public; RDPro pilot completed; five baseline preparations |
| Current implementation and study status | [Current status](AIDEAL_workflow/docs/CURRENT_STATUS.md) | GPT-5.3-Codex five-condition pilot; exact progress and results are recorded |
| Review the new RDPro versions | [RDPro treatment study](AIDEAL_WORKSPACE/03_Experiments/rdpro/treatment_comparison_v1/README.md) | Five installed treatment versions and a separate refactor; exact states shown |
| Project separation and Git branches | [Two-project guide](AIDEAL_workflow/docs/PROJECTS_AND_GIT.md) | Local folders, study arms, source branches and GitHub explained |
| Current code and treatment workflow | [AIDEAL_workflow](AIDEAL_workflow/README.md) | Library batches, five/six-condition and original/refactor runners |
| How to read the implementation | [End-to-end guide](AIDEAL_workflow/docs/END_TO_END.md) | Implemented and pending stages distinguished |
| Prompts, harnesses and skills | [Model-input guide](AIDEAL_workflow/docs/PROMPTS_HARNESS_SKILL.md) | Templates plus actual execution boundaries |
| Rust / SedonaDB | [Rust report](AIDEAL_workflow/studies/sedonadb/RUST_RUNNER.md) | 320/322 documented SQL examples execute; zero experimental LLM calls |
| Results and their denominators | [Results memo](AIDEAL_workflow/evidence/historical/RESULTS_MEMO.md) | Dated historical evidence; not a live progress report |
| Paper | [Changes and evidence](AIDEAL_workflow/paper/CHANGELOG.md) | Updated source and compiled PDF in that folder |
| Historical completed-work handoff | [September 14 evening handoff](AIDEAL_WORKFLOW_HANDOFF_20260914_1930/RESUME.md) | Dated snapshot; recheck processes before resuming |
| Historical MDAnalysis job handoff | [Operational handoff](AIDEAL_RESUME_20260914_1505/RESUME.md) | Dated supervisor records; check current process state before resuming |
| VLDB demo | [GRAIL](GRAIL/) | Protected; current checkout and local edits preserved |
| VLDB alias-demo worktree | [GRAIL_vldb_rdpro_alias](GRAIL_vldb_rdpro_alias/) | Protected separately |
| Current small cleanup | [Audited cleanup](AIDEAL_workflow/docs/HISTORICAL_CLEANUP.md) | Two reports archived; 37 generated files removed; saved evidence preserved |
| Earlier cleanup | [Cleanup report](AIDEAL_ARCHIVE/20260914_cleanup/audit/REPORT.md) | Reversible moves, exact-copy consolidation, restoration instructions |

## Supporting folders

- [Runtime](AIDEAL_WORKSPACE/01_Runtime/): MDAnalysis A1/A2/B2, supervisors,
  resume tools, runtime engine and live reports.
- [Development](AIDEAL_WORKSPACE/02_Development/): SedonaDB Rust, alias tooling,
  RDPro source, documentation audit and portable puzzle work.
- [Experiments](AIDEAL_WORKSPACE/03_Experiments/): current attached studies and earlier worktrees grouped by
  repository, with separate A1/A2/B2 cohorts preserved.
GRAIL demo support now belongs to the separate
[GRAIL_WORKSPACE](GRAIL_WORKSPACE/README.md), outside AIDEAL navigation.

These links open the existing directories. Runtime paths remain stable; a dated
folder name does not mean its scripts are inactive. Recheck live processes before
resuming; do not start another supervisor solely because a saved status is old.

## History and compatibility

`AIDEAL_ARCHIVE/20260914_cleanup/` groups handoffs, historical evidence, backups
and the retired Git-history copy. Old paths remain compatibility links where
saved reports or scripts may still refer to them. These links are not extra
copies of the folders.

Other `GRAIL_*` experiment directories are distinct Git worktrees with separate
results and sometimes local edits. They are retained as evidence/dependencies.
The worktrees already share Git objects through `GRAIL/.git`; they are not
independent full Git-history copies. `GS-QA-main/` is a separate benchmark project.

The five historical `AIDEAL_workflow` ablation branches contain toolkit flag configurations.
They are not the source versions of the new RDPro study. Current library treatment commits live
in the attached study’s isolated Git store and worktrees; see the [version guide](AIDEAL_workflow/docs/VERSION_NAVIGATION.md).


[RDPro 171 versus the Raptor-only bank](AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/review/raptor-scope/COUNT_EXPLANATION.md) · [Current experiment guide](AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/EXPERIMENT_GUIDE.md). The active scope is 330 Raptor/raster targets and 2,850 targets across six libraries; full-Beast setup files remain historical.
