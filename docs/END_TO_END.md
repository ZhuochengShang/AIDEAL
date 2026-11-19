# Portable AIDEAL process

Start with [README.md](../README.md) and the target's YAML, not a predefined library
folder. The machine-readable shared stage map is [stages.json](stages.json).

For the current cluster run, use the [current experiment guide](../experiments/2026-11-17-latest-stable-canonical/EXPERIMENT_GUIDE.md) and [end-to-end audit](../experiments/2026-11-17-latest-stable-canonical/review/audits/2026-11-19/README.md). It runs Original and existing D1 at native R0; it does not run the full paper design.

The independent three-README comparison is described in [Evaluating your own library](EVALUATING_YOUR_LIBRARY.md). The broader condition runner currently supports five-arm, six-arm and refactor-pair designs. The paper's eight-factorial design and its complete treatment validation remain pending. The sequence below explains the intended boundaries; it is not a claim that all stages launch automatically.

1. **Attach.** Resolve the existing YAML configuration, pin a clean source commit
   and create five real branches in an isolated clone.
2. **Discover.** Use the language adapter and configured source/test globs to propose
   API identities. Audit visibility, exports, overloads and features before freezing
   the denominator. A declaration count is not automatically an API count.
3. **Develop.** Generate grounded documentation and small development tasks. Diagnose
   failures using source and full errors. Prepare README, alias and hint artifacts
   without exposing held-out answers to the development models.
4. **Validate the evaluation bank.** Use microtests for individual APIs and puzzles
   for multi-API tasks. Independently validate fixtures, reference outputs and tests
   that reject wrong answers. Freeze one bank for every condition.
5. **Review and freeze.** Present exact alias changes and compatibility evidence for
   the requested human decision. Freeze treatments, prompt exposure, model settings,
   runtime identities and repair limits. Combined reuses the individual artifacts.
6. **Evaluate.** Generate fresh audience solutions in each isolated condition. Build,
   execute and independently check them. Allow the same bounded repair procedure.
   Only the designated conditions receive improved README/alias/hint exposure.
7. **Report and resume.** Record full attempts, delivered prompts and errors, provider
   failures and unresolved cases. Score initial and within-budget success, puzzle
   success, paired recoveries/regressions and resources. Reuse only checkpoints with
   matching identities; create a new study identity when the protocol changes.

For the three-README comparison, the working commands are `freeze-evaluation`
and `run-evaluation`; see [the execution guide](README_EVALUATION_RUNNER.md).

The attachment, preparation and treatment proposal/install commands work now.
See [treatment support](STUDY_TREATMENTS.md) for exact branch routing, model inputs
and duplicate-refactor comparison. Installation is labelled unvalidated. The existing engine implements
many generation and repair operations, and the controller supplies preflight and
scoring helpers. The validated adapter orchestration that connects every stage
into one automatic measured run remains unfinished. Once inputs are prepared,
`freeze-conditions` and `run-conditions` validate and execute the matched study.

The archived engine's `all` command is its older document/check sequence. It is not
a shortcut around the new five-condition protocol or its independent checks.
For historical examples, see [the study index](../studies/README.md).
