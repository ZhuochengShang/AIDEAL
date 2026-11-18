# Documented RDPro/Raptor API count

The linked branch contains 16 Markdown tutorial pages, not a complete API catalog. This audit inspects the folder for raster calls and resolves the receiver names against the pinned Beast 0.10.1 source.

| Scope | Raster interfaces | Raster operation families | Other helper interfaces |
|---|---:|---:|---:|
| `doc/rdpro.md` | 18 | 18 | 1 (`shapefile`) |
| `doc/raptor-join.md` | 4 | 2 | 2 (Scala/Java `shapefile`) |
| Union, repeats removed | **21** | **18** | **2** |

The union has 19 distinct raster method names. It has 21 owner-specific source interfaces because Java/Scala access paths can expose the same operation. The 18 families group GeoTIFF-loading adapters and raster-vector join adapters with their underlying operations. Such grouping is not a claim that JavaRDD and Scala RDD wrappers have identical types.

**For a concise paper count: 18 documented raster operation families, with 21 callable interface paths.** Seventeen families have code examples in `rdpro.md`; `reshapeAverage` is described in prose. The other 14 Markdown pages do not add a raster operation family under these rules. `Home.md` lists raster-related CLI commands, which are not counted as API methods.

## Auditable list

| Family | Documented call path | Evidence | Source definition | Forwarding target |
|---|---|---|---|---|
| geoTiff | `sc.geoTiff` | [rdpro.md:23](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L23) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:40` | — |
| hdfFile | `sc.hdfFile` | [rdpro.md:27](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L27) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:46` | — |
| pixelType | `tile.pixelType` | [rdpro.md:38](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L38) | `cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:138` | — |
| create | `RasterMetadata.create` | [rdpro.md:57](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L57) | `cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:324` | — |
| rasterizePixels | `sc.rasterizePixels` | [rdpro.md:64](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L64) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:58` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsGlobal.rasterizePixels` |
| rasterizePoints | `sc.rasterizePoints` | [rdpro.md:86](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L86) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:68` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsGlobal.rasterizePoints` |
| mapPixels | `raster.mapPixels` | [rdpro.md:99](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L99) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:119` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsLocal.mapPixels` |
| saveAsGeoTiff | `raster.saveAsGeoTiff` | [rdpro.md:100](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L100) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:104` | `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.saveAsGeoTiff` |
| filterPixels | `raster.filterPixels` | [rdpro.md:112](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L112) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:128` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsLocal.filterPixels` |
| flatten | `raster.flatten` | [rdpro.md:121](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L121) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:175` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsGlobal.flatten` |
| overlay | `raster.overlay` | [rdpro.md:138](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L138) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:96` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsLocal.overlay` |
| retile | `raster.retile` | [rdpro.md:151](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L151) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:137` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsFocal.retile` |
| explode | `raster.explode` | [rdpro.md:162](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L162) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:181` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsLocal.explode` |
| reproject | `raster.reproject` | [rdpro.md:176](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L176) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:155` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsFocal.reproject` |
| rescale | `raster.rescale` | [rdpro.md:186](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L186) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:166` | `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsFocal.rescale` |
| reshapeNN | `RasterOperationsFocal.reshapeNN` | [rdpro.md:200](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L200) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:408` | — |
| reshapeAverage | `RasterOperationsFocal.reshapeAverage` | [rdpro.md:212](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L212) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:58` | — |
| shapefile | `sc.shapefile` | [rdpro.md:237](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L237) | `io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:76` | — |
| raster_vector_join | `RaptorJoin.raptorJoinFeature` | [rdpro.md:238](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/rdpro.md#L238) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorJoin.scala:73` | — |
| raster_vector_join | `raster.raptorJoin` | [raptor-join.md:16](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/raptor-join.md#L16) | `raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:87` | `scala:edu.ucr.cs.bdlab.raptor.RaptorJoin.raptorJoinFeature` |
| geoTiff | `sparkContext.geoTiff [Java]` | [raptor-join.md:200](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/raptor-join.md#L200) | `beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialSparkContext.scala:119` | `scala:edu.ucr.cs.bdlab.raptor.RaptorMixin.RasterReadMixinFunctions.geoTiff` |
| shapefile | `sparkContext.shapefile [Java]` | [raptor-join.md:201](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/raptor-join.md#L201) | `beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialSparkContext.scala:68` | `scala:edu.ucr.cs.bdlab.beast.io.ReadWriteMixin.ReadWriteMixinFunctions.shapefile` |
| raster_vector_join | `JavaSpatialRDDHelper.raptorJoin` | [raptor-join.md:205](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8/doc/raptor-join.md#L205) | `beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:269` | `scala:edu.ucr.cs.bdlab.raptor.RaptorJoin.raptorJoinFeatureJ` |

## What the source count means

The initial raster source subset contained 422 selected callable identities: 347 in `raptor/` and 75 in eight supporting raster-type files. A subsequent source review consolidated 16 proven forwarding wrappers, leaving **406 source targets (328 Scala, 78 Java)**. This still includes low-level methods, constructors and distinct adapters; it is not a count of user-facing operation families or a claim that every adapter is redundant. The exact 16 mappings and retained cases are in `../consolidated/CONSOLIDATION.json`.

Nineteen of the 21 documented raster interface identities fall in the 422-source subset. The remaining two are Java-facing adapters in `beast-spark`: `JavaSpatialSparkContext.geoTiff` and `JavaSpatialRDDHelper.raptorJoin`. Their underlying raster operations are in scope. Vector `shapefile` helpers, generic Spark transformations, constructors, output fields, constants and CLI commands are excluded from the raster API count.

All 16 Markdown files from the linked branch are byte-identical to their counterparts in pinned Beast 0.10.1; the exact blob/hash comparison is saved in `../github-docs/VERSION_COMPARISON.json`. Mapping a name to source still does not prove its original example is executable. In particular, source `rasterizePixels`/`rasterizePoints` require a `RasterFeature` parameter that the published tutorial calls omit. This is an issue in the preserved original documentation, not evidence of mismatched document versions.

[Machine-readable count and every source/doc identity](COUNTS.json).

## Corrected Original-context mapping

The new scoped manifest resolves the 19 documented in-scope interface paths to **18 retained operations** after forwarding consolidation, and preserves the existing original documentation match for the `ITile` type identity. Thus **19/406 target identities** have reviewed API-specific Original context, comprising 18 operations and one type. The remaining 387 receive the unchanged original README plus an explicit no-reviewed-mapping disposition; this is not proof that no related prose exists. The previous 1/422 exact-name match missed implicit receiver forms such as `raster.mapPixels`.

The mapping changes retrieval metadata only. Original snippets remain byte-for-byte excerpts, including any mistakes in the original examples. Source signatures and forwarding proofs remain in review metadata and are not inserted into audience context. The real `original_target_texts` reader resolves all406 targets; the largest context is14,416 characters, below the configured22,119 ceiling. No model call or library execution was used for this mapping validation.

[Scoped original manifest](../original-docs/manifest.json) · [Validation](../original-docs/VALIDATION.json) · [Actual mapPixels Original context](../original-docs/EXAMPLE_ORIGINAL_CONTEXT_mapPixels.txt)
