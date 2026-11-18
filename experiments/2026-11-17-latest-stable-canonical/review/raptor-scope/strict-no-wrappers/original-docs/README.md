# Original documentation for the strict raster bank

The strict bank contains **330 source targets**. Its Original-document mapping resolves all 330 and supplies reviewed API-specific original context to **16 implementation identities**. The other 314 receive the unchanged shared original README and an explicit no-reviewed-mapping disposition. This does not establish that no related prose exists elsewhere.

The published documentation still describes **18 raster operation families through 21 callable interface paths**. Those documentation counts do not change when wrapper entry points cease to be independent benchmark targets.

| Original calling form | Retained implementation receiving its unchanged original excerpt | Evidence boundary |
|---|---|---|
| `sc.geoTiff` and `sc.hdfFile` | `RasterFileRDD` constructor | Source configures options and invokes this constructor. The examples document those configured factory uses, not every constructor option. |
| `raster.overlay` | `RasterOperationsLocal.overlay` | Source prepends the receiver to the supplied rasters and passes the resulting ordered varargs. |
| `raster.retile` | `RasterOperationsFocal.reshapeNN` | Source uses nearest-neighbor reshaping with an existing metadata-retile callback. The general reshape operation already has an original example. |

The generic `ITile` type is no longer an independent executable target. Its original documentation remains in the preserved corpus. The mapping does not relabel that type documentation as another operation.

All 16 Markdown pages from the linked GitHub folder are byte-identical to pinned Beast 0.10.1. The manifest also preserves five existing module/top-level documents, for 21 original documents total. Relevant excerpts are exact contiguous original text. Source signatures, argument mappings, and source code exist only in audit evidence and are not added to audience prompts. Any errors in the original examples remain unchanged.

Validation exercises the actual `original_target_texts` and `_relevant_doc_inventory` functions. Both resolve all 330 targets. The largest documentation context is 14,416 characters, below the configured 22,119-character ceiling. Hash mismatches are rejected. These checks make no model calls and do not certify execution of the library examples.

- [Manifest](manifest.json)
- [Validation](VALIDATION.json)
- [Source-bound exposure proofs](../ORIGINAL_DOC_EXPOSURES.json)
- [Actual Original input for RasterFileRDD](EXAMPLE_ORIGINAL_CONTEXT_RasterFileRDD.txt)
- [Actual Original input for overlay](EXAMPLE_ORIGINAL_CONTEXT_overlay.txt)
