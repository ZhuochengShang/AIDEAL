# Source and documentation recheck — 2026-11-17

All six cluster source checkouts match their pinned stable commit and tree and have clean tracked status. The main problems are the meaning of the reported counts and the documentation inputs. No model calls, subject imports/executions, source edits, release edits or configuration changes occurred.

Source root prefix: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/`. Full commits, trees and each configured document’s URL/hash are in [SOURCE_DOC_RECHECK.json](SOURCE_DOC_RECHECK.json) and [CONFIGURED_DOCUMENT_ORIGINS.csv](CONFIGURED_DOCUMENT_ORIGINS.csv).

| Library / pinned version | Source folder and upstream | Configured original docs | Saved sites / names → selected targets | Code-context hits |
|---|---|---|---:|---:|
| rdpro 0.10.1 | `rdpro/` · [beast-0.10.1](https://bitbucket.org/bdlabucr/beast/commits/547f7f912131a8032f6b5d26991415a5faf05cef) | `README.md` + `doc/`; 17 files | 2973 / 1268 → 708 | 55 |
| mdanalysis 2.11.0 | `mdanalysis/` · [package-2.11.0](https://github.com/MDAnalysis/mdanalysis/commit/ace84dde1363e32aa94cd3f29a42c2f590bd0575) | `README.rst` + `package/doc/sphinx/source/`; 186 files | 1435 / 1053 → 435 | 38 |
| tslearn 0.10.0 | `tslearn/` · [v0.10.0](https://github.com/tslearn-team/tslearn/commit/f6072f237313d610413359ecc899cdb9038f4b7e) | `README.md` + `docs/`; 121 files | 348 / 237 → 116 | 56 |
| mir_eval 0.8.2 | `mir_eval/` · [0.8.2](https://github.com/mir-evaluation/mir_eval/commit/8db0b3812e2032544c1fc00d02d4256cab043f3d) | `README.rst` + `docs/`; 23 files | 177 / 147 → 125 | 22 |
| thumbnailator 0.4.21 | `thumbnailator/` · [0.4.21](https://github.com/coobird/thumbnailator/commit/c9d99613878bbbf1f4d9369585b4cb5352c3b474) | `README.md` + `../../extras/thumbnailator/original_docs/ (official Javadoc artifact)`; 117 files | 319 / 145 → 94 | 94 |
| sedonadb 0.5.0 | `sedonadb/` · [apache-sedona-db-0.5.0](https://github.com/apache/sedona-db/commit/751453f04cd6e09842adf3073b2b3dac7d1777bc) | `README.md` + `docs/reference/sql/*.qmd`; 214 files | 226 / 226 → 217 | 212 |

The RDPro row is **Entire Beast**, as requested: 297 selected Scala names plus 411 Java names. It is a benchmark subset after structural exclusions and global simple-name election. It is not a claim that the whole repository has only 708 APIs. SedonaDB’s row counts registered SQL names, with 9 explicit aliases removed; it is not a Rust-source API count. MDAnalysis’s saved source inventory excludes Cython declarations.

**The 477 figure must be labeled “selected simple names with code-context mentions in the configured text bundle.”** It is not the number of APIs documented by the original projects.

| Official rendered documentation inventory | Functions | Methods | Classes / exceptions | Properties | Attributes / data | Callable qualified objects / simple names |
|---|---:|---:|---:|---:|---:|
| [mdanalysis](https://docs.mdanalysis.org/2.11.0/) | 227 | 1557 | 314 / 10 | 278 | 429 / 37 | 2108 / 888 |
| [tslearn](https://tslearn.readthedocs.io/en/stable/) | 69 | 339 | 60 / 0 | 1 | 0 / 0 | 468 / 151 |
| [mir_eval](https://mir-eval.readthedocs.io/stable/) | 175 | 0 | 1 / 1 | 0 | 0 / 0 | 177 / 147 |

These are documentation objects, including public aliases and inherited/private members, not independently established public API totals. Full typed names and target URLs are in each `*-official-inventory.csv`.

- **mir_eval:** all 177 saved source sites have exact qualified documentation targets, including all 125 selected targets. 103 of those 125 are falsely absent if 22 code-context hits are presented as “documented APIs.” Its raw `beat.rst` is an `automodule` directive, so rendered docstrings were missing from the configured audience bundle.
- **MDAnalysis:** 341 of 435 selected targets match official qualified documentation identities; 359 have a simple-name match. 305 exactly documented selected targets lack the old code-context signal. 13 tracked `.pyx` files are outside the Python-only inventory; 81 official objects belong to 9 Cython-backed modules (6 functions, 38 methods, 6 classes, 22 attributes, 9 modules). This is module-linked evidence, not a newly parsed Cython API count.
- **tslearn:** public re-export names differ from source-file module paths. Static `__init__.py` imports resolve 77 of 116 selected identities, up from 5 direct source-path matches. Four further bare-name cases (`to_hdf5`, `from_hdf5`, `from_json`, `kneighbors`) need inheritance/owner resolution. A bare name alone does not establish a correct match.
- **tslearn input defect:** 33 dataset files contribute 6,836,895 bytes to the 7,109,823-character text bundle. The actual 150,000-character README-distillation cap ends inside `docs/datasets/Beef/Beef_TEST.txt`, before 111 later files, including examples/reference material. Dataset/configuration files must not be described as documentation pages.
- **Retrieval defect:** the released relevant-context helper applies the same code-mention detector. Unresolved `automodule`/`autosummary` sources therefore cause many API requests to receive “No code-context section…” despite authoritative rendered API documentation. Thumbnailator’s rendered Javadoc has a different representation advantage.
- **Authoring cap:** the same 150k cap cuts off 110 later Thumbnailator files, 146 Sedona files and 14 MDAnalysis files. These are authoring-input omissions; original R0 relevant retrieval has a separate 12k per-target cap.
- **Access correction:** MDAnalysis 2.11.0 official docs are accessible now. The previous 403 must remain historical rather than a current exclusion rationale.

Replacement material is staged only: **265 official HTML pages**, every page’s version checked; **2,867/2,867 exact anchors found**. Script/style/navigation-free main text totals approximately 2.42 million characters. 2,867 API-target records point to 1,679 content-deduplicated excerpts; 271 class/exception targets contain nested member documentation, explicitly recorded. No implementation-source page was fetched or appended.

| Library | Version-checked pages | API-target excerpts |
|---|---:|---:|
| mdanalysis | 148 | 2222 |
| tslearn | 99 | 468 |
| mir_eval | 18 | 177 |

Use [NORMALIZED_DOC_BUNDLE.json](NORMALIZED_DOC_BUNDLE.json) for page provenance and [RENDERED_DOC_API_EXCERPTS.csv](RENDERED_DOC_API_EXCERPTS.csv) for exact target → URL → anchor → raw/derived hash → local excerpt. Raw official HTML remains under `raw-docs/`; derived text is under `derived-docs/`. All download dates, URLs and byte hashes are retained. The stable tslearn/mir_eval URLs are mutable, so these downloaded snapshots—not a future fetch—identify this audit. Exact hosted documentation build commits are not independently known.

The staged replacements do not yet change any measured input. A reviewed source identity/owner policy and a per-API documentation policy are still required before generation resumes. The prepared API-page bundles are not claimed to include every standalone user-guide page.
