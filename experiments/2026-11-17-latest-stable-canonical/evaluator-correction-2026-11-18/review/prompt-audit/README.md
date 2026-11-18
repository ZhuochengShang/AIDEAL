# Full prompt and evidence review

This review covers all **2,850 API targets across seven execution banks and six libraries**. Original and D1 artifacts here are historical records from the November 17–18 R0 runs. They are not new corrected scores. R0 means the initial generated program with no snippet repair. No model calls were made to prepare this review. **D1 still contains the earlier generated README. Fixing the author prompt did not regenerate or repair D1. A new D1 audience evaluation therefore tests that same saved document under the corrected execution setup.**

## What the audience actually receives

1. A shared execution setup describes the language, available inputs, and output rules.
2. The request names the selected API and gives its canonical signature, defining owner, and available public access paths. Both conditions receive these source-inventory interface facts.
3. Original receives the selected original-document excerpt. D1 receives that API’s generated README entry.
4. The audience writes one program body and its own assertion. The executor compiles/runs it and records stdout, stderr, markers, and exit status. Native success does not establish an independent expected-output check.

All 2,850 paired system prompts and target declarations match. User text outside the documentation matches in 2,633 pairs; the remaining 217 SedonaDB pairs differ only in their condition-specific output directory. After replacing that directory with a common placeholder, those 217 pairs match too.

The structural scan found no implementation-body fields or direct source-window markers outside the supplied audience documentation. This is a bounded exposure check, not proof that every possible answer is absent. Original documentation can contain examples and expected values. Fixture dimensions and types are public setup facts, not hidden answers. Because some microbenchmarks inspect those same properties, their assertions must not simply echo a supplied dimension or accept any value.

## Findings and changes

| Finding | Evidence | New behavior |
|---|---|---|
| Stale scope wording | mir_eval125 vs178, Thumbnailator94 vs225, tslearn116 vs362, MDAnalysis435 vs1538 | New profile snapshots remove hardcoded counts; the manifest remains authoritative. |
| Conflicting condition wording | SedonaDB says original documentation only even in D1 | New profile says documentation supplied in this request. |
| Baseline already supplies repair advice | RDPro Scala explains coalesce(1), Wrong FS, and path-scheme remedies | New shared execution context retains input/environment facts but removes failure-specific fixes. |
| Audience tells itself how to classify setup failures | MD profile and tslearn execution hints label missing packages as infrastructure | New prompts leave classification to recorded diagnostics and evidence review. |
| Invalid author call syntax | All2,850 author entry prompts interpolate language-qualified IDs into value.ID(...) | Future default author prompt separates the registry label from callable public access; old records remain untouched. |
| Unverified test-example claim | All2,850 current qualified author entry requests say no existing test found | Future prompt calls retrieved snippets source evidence, never claims they compiled/passed without execution evidence. This does not mean the repositories lack tests. |
| Incomplete historical runtime identity | All364 RDPro runtime JARs match archived build hashes; JDK has version/path but no historical binary SHA | Preserve this partial evidence; do not certify historical byte identity or silently reuse scores under a strict unchanged-runtime rule. |

These prompt defects are measured configuration limitations, not proof that each caused a score regression. Concrete source-contradicting D1 content still requires API-level diagnosis. For example, Statistics.isValid describes a fresh Statistics instance as invalid although the implementation initializes it as valid.

## Authoring evidence

The D1 author receives structured API facts, retrieved documentation and its distilled summary, project context, and available source comments. It does not generally receive implementation bodies. All555 Java/Scala entries have an empty source_doc field. Python entries vary. For SedonaDB, source_doc contains upstream SQL reference text rather than implementation code. All2,850 selected author requests lack an extracted test example. D1 authoring records label this stage static grounding without execution. Therefore signatures alone cannot establish initialization, defaults, state transitions, or parameterless access behavior.

| Bank | APIs | Author entries with nonempty source_doc | Complete example |
|---|---:|---:|---|
| mir_eval | 178 | 178 | [Open full pair](examples/mir_eval/original/PROMPT.md) |
| thumbnailator | 225 | 0 | [Open full pair](examples/thumbnailator/original/PROMPT.md) |
| sedonadb | 217 | 217 | [Open full pair](examples/sedonadb/original/PROMPT.md) |
| rdpro_java | 69 | 0 | [Open full pair](examples/rdpro_java/original/PROMPT.md) |
| rdpro_scala | 261 | 0 | [Open full pair](examples/rdpro_scala/original/PROMPT.md) |
| tslearn | 362 | 277 | [Open full pair](examples/tslearn/original/PROMPT.md) |
| mdanalysis | 1538 | 1101 | [Open full pair](examples/mdanalysis/original/PROMPT.md) |

MDAnalysis has 1,348 replayed author requests. Each reused request was resolved through its saved receipt and its hash checked. All1,538 MDAnalysis API identities have an author request; 1,538 entries plus13 distillation requests are indexed.

## Open a complete example

For each bank, open `examples/<bank>/`:

- `original/PROMPT.md` and `generated_d1/PROMPT.md` contain the **entire** recorded system and user prompts.
- `request.json` preserves the exact provider/model, round, output allowance, declaration, and prompt fields.
- `response.txt` is the full model answer; `ApiTest.java`, `ApiTest.scala`, or `api_test.py`/`ApiTest.py` is the executed scaffold and snippet.
- `execution.json`, `stdout.txt`, and `stderr.txt` preserve the exact command and full execution output.
- `RESULT.json` preserves the historical verdict and per-API metrics. A historical pass is not a corrected score.
- `CONFIG.yaml`, `EXECUTION_INPUTS.json`, and `FIXTURE_BINDINGS.json` show all configured inputs, preamble/scaffold, file paths, sizes, and hashes. Fixture bytes remain in their recorded cluster locations.
- `readme_author/attempt_*/` contains the full recorded D1 author request, response and provider record for the same API.
- `PROVENANCE.json` binds copied files to their source artifacts and links the separate, manually reviewed corrected-executor controls.

[ALL_API_INDEX.tsv](ALL_API_INDEX.tsv) lists every API and its Original/D1 request, executed program, execution record, author request, and saved verdict. Per-bank JSON indexes additionally include response and stdout/stderr paths. These are cluster source paths; the seven paired examples are copied locally in full.

## How corrected D2 differs

Corrected replay first reexecutes saved programs with repaired execution rules. D2 selects failing entries from that completed replay, supplies the exact historical program/request/diagnostic plus selected source windows to the author, and validates a proposed example in an isolated output. A candidate can replace D1 only if it keeps the requested API heading/signature and passes execution with the exact target witness. Other entries remain byte-preserved. This is development on R0 failures, not the planned post-R2 deep dive or held-out validation. New paid work is blocked for unresolved relevant setup prerequisites.

New neutral profiles live in [corrected-profiles](../corrected-profiles/MANIFEST.json); shared execution overrides live in [corrected-contexts](../corrected-contexts/MANIFEST.json). Both record exact prior/new bindings and readable diffs. Apply each new context identically to Original, D1 and D2. Changing context requires new requests; do not relabel old responses as fresh matched trials.

## Software checks

45 focused tests passed, including12 subtests, covering qualified README identities, the author prompt, D2 immutable inputs, blocked paid launch, exact heading checks, example acceptance, and safe resume. Existing historical author records and D1 documents were preserved.
