# Why the previous RDPro study used 171 targets

The earlier denominator counted selected **bare API names/README entries**, not every public function in Raptor or Beast, and not 171 originally documented APIs.

| Historical evidence | Count | Meaning |
|---|---:|---|
| Static intent-selected surface |161| Names selected from all Beast Scala source using threshold 5; Java only supplied type context |
| Original documentation matches within that surface |88| Name matches in code-context documentation, not a complete semantic API catalog |
| Selected names without an original documentation match |73|161−88|
| Generated README evaluation entries |171|161 selected names plus 10 additional generated entry names |
| Frozen shared/complement manifests |88+83|Disjoint sets exactly reproduce all 171 evaluated names |

## Exact denominator mechanism

`doc_checks.py:198–202` selects the filled `## API Test: ...` entries from the generated README for a generated-document run with `doc_scope=relevant` and no manifest. The July 14 result records exactly that mode (`manifest=null`, `api_count=171`). It does not intersect those README names with the 161-name source surface. The surviving generated README has the same 171-name set, although its current bytes are not claimed to be identical to the historical A2 input.

The additional names are `area`, `build`, `call`, `compute`, `end`, `extents`, `geometryType`, `initialized`, `normal`, and `numNonEmptyGeometries`. Their presence explains 171 versus 161. It does not prove that these entries were invented; the earlier source reconciliation found all 171 names in the broader source. The complemented manifest explicitly allows `generated_document_entries` outside the selected surface.

## Why this differs from a qualified Raptor inventory

1. The old study scanned only Scala declarations. It did not include Java declarations as target APIs.
2. It used an intent filter based on documentation, tests, mentions, visibility, and penalties. It did not select every public declaration.
3. It grouped by bare name (`readme_agent.py:1443`, `recs.setdefault(name, ...)`). Separate classes with the same method name collapsed into one target.
4. It scanned all Beast modules, so it included vector and visualization operations such as `spatialJoin`, `saveAsShapefile`, and `plotImage`. It was not a clean Raptor-only inventory.
5. The current inventory distinguishes owners and source sites and includes both implementation languages. A restricted Raptor count must be labeled with its own rules and scope.

A concrete collision is `readTile`: the historical list has one `readTile` entry, while `GeoTiffReader.scala:167` and `HDF4Reader.scala:163` define separate implementations. Likewise, `reproject` appears in raster code (`RaptorMixin.scala:146`, `RasterOperationsFocal.scala:517`) and vector code (`CGOperationsMixin.scala:139`). A single old name cannot identify all these operations fairly.

The saved source receipt reports the same official Beast 0.10.1 source tree for the historical run and the newer original publication snapshot (tree `757142fe21ba53b1388880d6abc7423aff844295`). The count difference is therefore explained by selection and API identity, not a source expansion between those pinned snapshots. This does not assert all later release inventories are identical.

## Results caution

The inspected A2 artifact records 73/171 raw passes, not the separately quoted 92/171. The saved reconciliation derives Original 46/171 from 37 dedicated R0 shared passes plus nine first-attempt complement passes from a run allowing five repairs. Do not present that reconstruction as one dedicated 171-target R0 run, or silently match different A2 runs. These result issues do not change the verified 171-name denominator.

`AUDIT.json` contains source paths, hashes, rules, counts, and the exact 171 names. `historical171_manifest.json` is the extracted name list.
