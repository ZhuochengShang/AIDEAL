# Source, documentation and API reduction audit

Updated November 17, 2026. **The previous 1,695-target selection is under correction and must not be launched. No new model call or subject execution occurred.**

## Agreed scope and counting unit

RDPro means the entire pinned Beast repository, reported by module. Distinct owners remain distinct APIs. Maximum-parameter reduction applies only within the same qualified API, not across unrelated classes. Dependency imports/inherited members are excluded using their defining owner and source, never just a common function name.

Every row in [the full source candidate ledger](ALL_SOURCE_CANDIDATES.csv) stays visible. It includes excluded/unresolved candidates from the old policy. It is not a claim that the existing scanner captured every runtime exposure: MDAnalysis Cython, public re-exports and inherited exposures require reconciliation with the original API documentation.

## 1. Exact source locations

[Full source paths, commits and URLs](SOURCE_LOCATIONS.csv). Cluster source root is `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/`.

| Library | Version | Source commit | Upstream |
|---|---|---|---|
| RDPro / whole Beast | 0.10.1 | `547f7f912131` | [Source](https://bitbucket.org/bdlabucr/beast.git) |
| MDAnalysis | 2.11.0 | `ace84dde1363` | [Source](https://github.com/MDAnalysis/mdanalysis.git) |
| tslearn | 0.10.0 | `f6072f237313` | [Source](https://github.com/tslearn-team/tslearn.git) |
| mir_eval | 0.8.2 | `8db0b3812e20` | [Source](https://github.com/mir-evaluation/mir_eval.git) |
| Thumbnailator | 0.4.21 | `c9d99613878b` | [Source](https://github.com/coobird/thumbnailator.git) |
| SedonaDB | 0.5.0 | `751453f04cd6` | [Source](https://github.com/apache/sedona-db.git) |

All six cluster HEAD/tree pairs were re-read and matched the pinned versions, with clean tracked files. Local Git-store locations are in the CSV; an arbitrary working checkout is not assumed to be at the pinned commit.

## 2. Why previous counts fell

These are the old reduction steps, reconstructed exactly from recorded decisions. **Unresolved means the classifier could not establish its category; it does not mean duplicate.**

| Library | Source sites | Unique simple names | Unresolved sites removed | Other sites excluded | Same-name/alias omissions | Old selected |
|---|---:|---:|---:|---:|---:|---:|
|RDPro / whole Beast|2973|1268|714|905|646|708|
|MDAnalysis|1435|1053|752|143|105|435|
|tslearn|348|237|139|38|55|116|
|mir_eval|177|147|17|6|29|125|
|Thumbnailator|319|145|88|74|63|94|
|SedonaDB|226|226|0|0|9|217|

MDAnalysis previously used 1,032 simple names. The new-version source scan found 1,053 names at 1,435 sites. It removed 752 unresolved sites, 127 wrapper/forwarder-classified sites and 16 abstract/bodyless sites, leaving 540; global bare-name selection then removed 105 more, producing 435. Thus 435 is a filtered subset, not the library API total.

The original source audit also omitted MDAnalysis `.pyx` extension modules. Its Python-only scope cannot establish a complete public API catalog. Official documentation exposes Cython-backed APIs such as `Timestep`, `make_whole` and `FastNS`.

## 3. Whole Beast, by module

The old 708 comprises functions from all these modules. It is not a count of the narrow raster module. Module simple-name counts overlap and must not be summed. The final corrected count remains unset while external ownership, forwarding and overload identities are reviewed.

| Module | Source sites | Simple names in module | Qualified groups before new filters | Old winners located here |
|---|---:|---:|---:|---:|
|beast-spark|77|44|57|9|
|cg|575|282|501|153|
|common|361|211|311|123|
|dataExplorer|40|37|38|21|
|distribution|1|1|1|1|
|dynoviz|54|29|54|20|
|io|818|342|762|134|
|raptor|311|153|299|67|
|satex|10|10|10|3|
|spatialtest|4|4|4|0|
|visualization|722|352|619|177|

The old arithmetic is `2,973 source sites − 1,619 excluded sites − 646 global-name omissions = 708`. Of the excluded sites, 714 were unresolved. Under the agreed owner rule, 2,656 qualified-name groups exist before the new filters; this is a candidate count, not an approved evaluation denominator. Whole-repository counts can legitimately exceed 700. We do not force a number to match an expectation.

A concrete false exclusion is RDPro `RasterOperationsLocal.mapPixels`, which implements a raster transformation using `inputRaster.map(inputTile => new MapPixelsTile(inputTile, f))`. Calling Spark `map` does not make this operation Spark’s own API. The old rule labelled both its convenience wrapper and implementation as wrappers, removing the operation entirely.

## 4. Original documentation counts

The previous 477/1,695 metric counted simple names in selected code-context text. It was not a count of documented APIs. The [official documentation inventories](documentation/OFFICIAL_INVENTORY_AUDIT.json), [all configured document paths/URLs/hashes](documentation/CONFIGURED_DOCUMENT_ORIGINS.csv), and [version-checked rendered bundle](documentation/RENDERED_DOC_BUNDLE.json) are now available.

| Library / original documentation | Functions | Methods | Classes + exceptions | Interpretation |
|---|---:|---:|---:|---|
|[MDAnalysis 2.11.0](https://docs.mdanalysis.org/2.11.0/)|227|1557|324|Sphinx documented qualified entries, before re-export/inheritance/external-owner deduplication|
|[tslearn 0.10.0](https://tslearn.readthedocs.io/en/stable/)|69|339|60|Sphinx documented qualified entries, before re-export/inheritance/external-owner deduplication|
|[mir_eval 0.8.2](https://mir-eval.readthedocs.io/stable/)|175|0|2|Sphinx documented qualified entries, before re-export/inheritance/external-owner deduplication|

Thumbnailator’s official 0.4.21 Javadoc contains 349 parsed public declared member signatures (152 simple member names). The parser records visibility in the CSV; inherited navigation links are not counted as new declarations. This count includes constructors and is not the benchmark denominator.

SedonaDB’s 0.5.0 source has 212 original SQL reference function pages matching 212 of 226 registered names by filename. Alias-to-target documentation mappings remain separate. The 217 prior selection removed nine explicit registered aliases.

Beast’s 17-file old documentation bundle mentions 119 distinct source names in code context. Four additional production-module READMEs bring the inspected file set to 21 and the mention count remains 119. These short-name mentions do not establish qualified API coverage. The RDPro evidence JSON records document paths, sampled plain-word match lines and candidate-site counts. Those sampled lines are not necessarily code-context matches. Definition owners and source locations are available in ALL_SOURCE_CANDIDATES.csv.

Important corrections:

- MDAnalysis: 177 raw `automodule` stubs do not contain the rendered API descriptions. Official 2.11.0 rendered pages are now available and version checked.
- mir_eval: all 177 saved source sites match official qualified documentation targets; the prior 22/125 code-mention count understated documentation availability.
- tslearn: 33 dataset files contributed approximately 96% of the old 7.1-million-character bundle. Its 150,000-character distillation window ended inside a dataset, before most API reference material. Replacement inputs contain documentation text rather than dataset/config/template payloads.
- Sphinx inventory counts include public aliases, inherited methods and sometimes private objects. They must be reconciled with defining source ownership, not substituted directly for a benchmark API count.

265 official pages have been fetched with matching version headers. Exact-anchor API excerpts preserve their original documentation URL and page hash. They contain no invented LLM README text. These replacements are staged, not silently substituted into earlier runs.

## 5. Required reduction order

```text
Pinned source + matching original documentation
  -> enumerate public definitions AND documented public exposures
  -> resolve each exposure to its defining library/dependency source
  -> exclude external-only imports/inherited members (record evidence)
  -> map proven forwarding wrappers to retained library targets
  -> group overloads within the same qualified API
  -> keep largest explicit-parameter version; retain every variant in ledger
  -> review unresolved origins, signatures and body classifications
  -> approve and freeze the final IDs and original-doc coverage
  -> generate README entries for exactly those approved IDs
  -> verify no selected ID is missing, duplicated or replaced by another owner
```

A wrapper cannot disappear without a retained target mapping. A call to an external helper is not an external API definition. An unresolved candidate remains in the review ledger; it is not silently relabelled as a duplicate. Name collisions between owners do not justify removal.

## 6. Execution state

The earlier study is held for source/documentation correction. Current API tasks, costs and selected counts are superseded preparation evidence. Original R0 and README generation require a new inventory/disposition/selection review and fresh input fingerprints. No provider calls, audience programs or new treatment evaluations ran during this audit.


### Verified custom Spark namespace

Beast defines four production files under org.apache.spark.beast, including its custom SQL data types. The most specific configured namespace rule preserves these custom definitions while excluding ordinary Spark APIs. The origin filter retained all 31 recorded declarations from those four files in a read-only source check; this is not a final benchmark count. See [the origin rules](code_updates/docs/API_ORIGIN.md) and [the real source check](code_updates/BEAST_REAL_SOURCE_ORIGIN_CHECK.json).
