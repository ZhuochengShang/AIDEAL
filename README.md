# AIDEAL — RDPro Codex evaluation

This is **`evaluation/rdpro-codex-v1`**, the dedicated review branch for the completed RDPro pilot. It starts from toolkit commit `8083e3b27c05b899b8a4941377ab0abc5c81dcbb`; GitHub `main` remains the toolkit release.

- [RDPro evaluation: setup, five conditions and results](studies/rdpro/codex_v1/README.md)
- [Actual checker, JVM harness and offline tests](studies/rdpro/codex_v1/harness/README.md)
- [Audited result summary](studies/rdpro/codex_v1/RESULTS.md)
- [Exact RDPro treatment branch names and commits](studies/rdpro/codex_v1/source_versions.json)

The five RDPro source branches belong to the separate local library repository. This AIDEAL branch records their identities, the evaluation code, treatment artifacts and a reviewed result export. It does not contain the private fixture bank, expected answers, runtime binaries or complete machine-bound evidence. Repeating the original experiment requires those local inputs; the included synthetic harness tests run independently.

The pilot resolved 40 model tasks after 120 trusted controls validated. No generated error hint was delivered, so the hints-only arm's extra pass cannot establish a hint benefit. The study README explains this and the other limitations.

The toolkit guide follows below. `python scripts/aideal verify` checks this branch's complete integrity inventory. The source-only `scripts/build_publication_manifest.py` intentionally rejects study exports; do not use it to overwrite this branch's inventory.

[Codex pilot and shared budget](docs/OPENAI_CODEX_PILOT.md) · [Gemini Flash settings](docs/GEMINI_FLASH.md) · [Legacy-code review](docs/LEGACY_CODE_REVIEW.md)

AIDEAL prepares and evaluates changes that may help language models use a software library: clearer documentation, forwarding aliases, function-specific error hints, and source refactors that preserve the public API.

The toolkit records source versions, model inputs, checker controls, execution attempts, and scores needed to review a comparison. It supports five treatment conditions, an original/refactor pair, or all six conditions. A separate three-README evaluator remains available.

**The framework and this small pilot do not establish a general effectiveness claim.** Offline tests check controller behavior. Local library controls and regression probes check selected implementations and harness behavior. This branch includes the reviewed RDPro pilot summary and selected generated treatments; private study inputs, complete request/response transcripts, runtime JARs and machine-bound experiment evidence remain local.

## Read first

- [Workflow summary](docs/SUMMARY.md): design, prompts, data boundaries and harness responsibilities.
- [Configuration](docs/CONFIGURATION.md): library, model, task bank and adapter inputs.
- [Output locations](docs/OUTPUTS.md): especially generated API tests, controls and audience results.
- [Conditions and versions](docs/VERSIONS.md): which changes belong in each condition.
- [Scoring](docs/SCORING.md): fixed denominators, repair budgets and incomplete runs.
- [Code review route](docs/CODE_REVIEW.md): implementation entry points and generated function map.

## Start with an explicit library

Use Python 3.10 or later. Source inspection and study preparation require the base dependencies:

```sh
python -m pip install -r requirements.txt
python scripts/aideal --help
python scripts/aideal status
```

Copy [configs/aideal.example.yaml](configs/aideal.example.yaml) to a study workspace's `configs/aideal.yaml`, then set source/test patterns and original documentation paths. Replace every placeholder. The example is a schema guide, not a runnable library configuration.

```sh
python scripts/aideal attach \
  --repo /absolute/path/to/clean-library \
  --config /absolute/path/to/workspace/configs/aideal.yaml \
  --output /absolute/path/to/study

python scripts/aideal preview-library \
  --study /absolute/path/to/study \
  --output /absolute/path/to/study/development/preview_v1 \
  --batch-size 12
```

Attachment pins the baseline in an isolated Git store and creates five preparation worktrees. Preview records bounded source/API context and coverage without calling a model. Add `--api` for explicit APIs and `--alias-path-template` for a language-appropriate new alias module path.

Model proposals require an explicit [development-model configuration](configs/improvements.example.yaml). The included Google adapter uses [requirements-evaluation.txt](requirements-evaluation.txt). The optional [Codex adapter](docs/OPENAI_CODEX_PILOT.md) uses [requirements-openai.txt](requirements-openai.txt) and a shared budget ledger. Each provider reads its credentials from the launching environment.

Native README authoring is a separate engine interface. Install its model-provider dependencies when using that path:

```sh
python -m pip install -e './vendor/aideal_engine[providers]'
python -m aideal.cli --help
```

The retained distribution name is `grail-agent`; its native console command is `aideal`. Use `python scripts/aideal ...` for the portable controller and `python -m aideal.cli ...` for native documentation development to avoid ambiguity. [Third-party notices](THIRD_PARTY_NOTICES.md) explain the retained naming and provenance.

## Develop, then measure

1. Generate or select the README; review bounded alias/hint/refactor proposals from development evidence.
2. Build and regression-test proposed changes. Bundle selected README/alias/hint artifacts and install their exact versions; install a source refactor separately.
3. Supply an independent held-out microtask/puzzle bank, trusted reference and negative controls, and a library-specific execution adapter.
4. Configure [condition_evaluation.example.yaml](configs/condition_evaluation.example.yaml), validate every backend, and freeze.
5. Run fresh audience solutions and inspect matched results.

```sh
python scripts/aideal freeze-conditions \
  --config /absolute/path/to/study/conditions.yaml \
  --output /absolute/path/to/study/frozen_v1

python scripts/aideal run-conditions \
  --study /absolute/path/to/study/frozen_v1/frozen.json \
  --output /absolute/path/to/study/runs/first
```

Freezing executes configured controls; running calls the configured model and checker. Repeating a compatible run output resumes saved work. Changed source, prompts, tasks, model settings or checker artifacts require a new validated identity. Preparation folders and installed commits alone are not evaluated treatments.

## Review the implementation

The portable controller is in [workflow/](workflow/); native documentation development is in [vendor/aideal_engine/src/aideal/](vendor/aideal_engine/src/aideal/). See the [API test guide](docs/OUTPUTS.md#development-readme-api-checks) for native execution outputs.

The [function index](docs/FUNCTION_INDEX.md) provides static caller/callee links. To use the interactive [CODE_MAP.html](docs/CODE_MAP.html), open the downloaded file in a browser; GitHub's file view does not execute its JavaScript. Static calls are review aids, not runtime traces or unused-code proof.

```sh
# Offline controller/regression fixtures; no real provider call is required.
python -m unittest discover -s tests
```

Library-specific build tools, fixture data, oracle design, runtime isolation, and source-to-binary checks remain explicit study responsibilities. Generic subprocess execution is not an operating-system sandbox.
