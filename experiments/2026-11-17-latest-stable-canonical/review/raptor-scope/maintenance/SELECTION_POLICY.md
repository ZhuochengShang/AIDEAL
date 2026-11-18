# API selection policy across the six libraries

The banks share source-ownership and stable-identity principles, but **only the current RDPro raster bank has completed the new strict wrapper, unimplemented-body and abstract-constructor review**. The other banks must not be described as identically filtered.

This is a read-only audit of the recorded inputs. Existing runs, results and frozen banks remain unchanged. Counts below describe current banks, not proposed counts after another cleanup.

| Library | Targets | Current identity and selection rule | Strict-review status |
|---|---:|---|---|
| RDPro / Raptor | **330** | Library-owned qualified identities; reviewed exclusions before maximum-parameter selection within each owner/API | **Completed for the strict raster bank**; 271 methods and 59 concrete constructors |
| MDAnalysis | 1,538 | Qualified Python/Cython definitions; same-owner selection; five explicit abstract/bodyless declarations excluded | No strict exclusion receipt; 15 selected methods have a sole `raise NotImplementedError` body |
| tslearn | 362 | Qualified Python definitions; distinct owners retained | No completed strict wrapper/stub review |
| mir_eval | 178 | Qualified Python definitions; distinct owners retained | No completed strict wrapper/stub review |
| Thumbnailator | 225 | Qualified Java definitions; 23 abstract/bodyless sites excluded and 71 overload sites omitted | No strict exclusion receipt; winners still include 23 `direct_forwarder` and three `wrapper` classifications |
| SedonaDB | 217 | Public registered SQL names; 226 names minus nine explicit aliases | SQL-specific policy; host-method arity and constructor rules do not directly apply |

## Shared rules and their limits

MDAnalysis, tslearn, mir_eval and Thumbnailator use `owner_qualified_max_arity_v2`. It preserves different owners, selects within one defining language and qualified API, and does not infer equivalence from a shared short name. Imported external definitions are excluded through ownership rules. Library-owned implementations of framework interfaces can remain eligible.

The configs bind their inventories and canonical selections by hash. This audit verified those bindings and **2,303 selected source spans** across the four libraries. Every selected definition has a `library_defined` origin record, and API identifiers are unique within each bank.

Their policy permits forwarder consolidation only with source-bound argument mapping to an exact retained library definition. That mechanism is not evidence that every wrapper has been found. None of these four current inventories has the additional hash-bound strict exclusions used by RDPro. Python's recorded `implementation` label primarily establishes body presence, not useful behavior or absence of forwarding.

## Concrete gaps

- **MDAnalysis:** selected examples `BackendBase.apply` and `TopologyReaderBase.parse` contain only `raise NotImplementedError` after their docstrings. The audit lists all 15 such methods. They require eligibility review; no upstream source was deleted or rewritten.
- **Thumbnailator:** selected `ThumbnailParameter.getResizer` returns `resizerFactory.getResizer()`, and `Thumbnails.Builder.toFiles(File, Rename)` calls `asFiles(destinationDir, rename)`. Constructor adapters also remain. Review candidate overloads before choosing a replacement implementation.
- **Python banks:** a narrow scan found 123, 31 and six single-return-call candidates in MDAnalysis, tslearn and mir_eval, respectively. **These are not confirmed wrapper or removal counts.** Argument computation, decorators, defaults and target bindings require review. The 113 selected MDAnalysis Cython declarations were hash-verified but were outside this Python-AST scan.
- **Constructor eligibility:** one selected class in MDAnalysis and one in tslearn declares a locally decorated abstract method. These are review candidates; runtime abstractness also depends on metaclasses and inheritance.
- **SedonaDB:** its registry policy appropriately excludes DataFusion builtins and Rust methods from the SQL bank. Nine source-proven aliases, such as `st_aswkb → st_asbinary`, count once. It retains documented SQL call patterns and variadic `rs_stack`, without borrowing arity from Rust UDF factories. One selected operation, `S2_CellIdFromPoint`, still has unresolved dynamic source registration.

A library-owned wrapper around NumPy, Java or Spark is different from an imported external definition. Source ownership alone does not remove that wrapper. Conversely, matching method names or short bodies do not justify merging distinct owner contracts.

## How to make the next revision consistent

1. Preserve current and completed runs under their existing bank identities.
2. Apply one explicit wrapper, stub and constructor eligibility policy to a new revision of each source-method bank, preserving distinct owners.
3. Review exclusions before overload election, retain the supporting source evidence, and keep native calling forms as documentation exposures.
4. Retain SedonaDB's SQL-specific identity policy; resolve the outstanding registration and verify any further aliases against registration evidence.
5. Rebuild manifests, original-document mappings and denominator reports, then validate the new inputs before a replacement run.

No revised counts are claimed for the other libraries until that review is complete. Consistent study principles do not require identical extraction mechanics for source methods and registered SQL operations.

## Evidence and navigation

- [Machine-readable policy audit](policy-audit.json) — exact config, inventory and source hashes; candidate identities and limitations.
- [Current strict RDPro bank](../strict-no-wrappers/README.md) and [selection exclusions](../strict-no-wrappers/selection_exclusions.json).
- Current canonical receipts: [MDAnalysis](../../qualified-api/mdanalysis/canonical-selection.json), [tslearn](../../qualified-api/tslearn/canonical-selection.json), [mir_eval](../../qualified-api/mir_eval/canonical-selection.json), [Thumbnailator](../../qualified-api/thumbnailator/canonical-selection.json), [SedonaDB](../../qualified-api/sedonadb/canonical-selection.json).
- [SedonaDB registration-origin audit](../../qualified-api/sedonadb/registration-origin.json).

No measured input, library source, queue, branch or credential was changed for this audit. No model calls or library executions were made.
