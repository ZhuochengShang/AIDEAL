# Fix-loop report — result

_Generated 2026-11-18 11:04 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-180004Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **19/261** raw (7.3%)  ·  scored **19/261** (7.3%) after excluding 0 infra
- wall 1.06 h  ·  tokens in 602,177 / out 58,250 ·  llm calls 261  ·  max_fix_rounds 0
- pass-by-round: r0:19  ·  **0 rescued by the fix loop** (pass@0 = 19)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **57x** [compile] <path>:<n>: error: value <name> is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
  - `scala:class:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.reproject`, `scala:class:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.rescale`, `scala:edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile.copy`, `scala:edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile.getPixelValue`, `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.rasterMetadataToRow`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.envelope`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.equals`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.extents`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getPixelScaleX`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileIDAtPixel`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileIDAtPoint`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileX1`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileX2`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileY1` …
- **27x** [compile] <path>:<n>: error: type mismatch;
  - `scala:edu.ucr.cs.bdlab.beast.geolite.RasterFeatureSerializer.read`, `scala:edu.ucr.cs.bdlab.beast.geolite.RasterFeatureSerializer.write`, `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsIterator`, `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsTileBreaker.moveToNextIntersections`, `scala:edu.ucr.cs.bdlab.raptor.ExplodedTile`, `scala:edu.ucr.cs.bdlab.raptor.FilterTile`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.TempIFDEntry.count`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.TempIFDEntry.getValueOrOffsetBig`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.TempIFDEntry.toString`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.TempIFDEntry.valueLength`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.closeTileDataOnly`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.makeIFDEntry`, `scala:edu.ucr.cs.bdlab.raptor.IntersectionsIterator.hasNext`, `scala:edu.ucr.cs.bdlab.raptor.IntersectionsIterator1.hasNext` …
- **24x** [compile] <path>:<n>: error: value <name> is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
  - `scala:edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile.isEmpty`, `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.get`, `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.getPointValue`, `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.isDefined`, `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.isEmptyAt`, `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.isPixelInRange`, `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.setAttribute`, `scala:edu.ucr.cs.bdlab.raptor.AbstractGeoTiffTile.isEmpty`, `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileMultiBand`, `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileMultiBand.getPixelValue`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileFloatArray.componentType`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileSerializer.write`, `scala:edu.ucr.cs.bdlab.raptor.MaskTile.isEmpty`, `scala:edu.ucr.cs.bdlab.raptor.MemoryTile` …
- **10x** [compile] <path>:<n>: error: object RasterMetadata is not a member of package edu.ucr.cs.bdlab.raptor
  - `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileSingleBand`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileDouble`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileFloat`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileFloatArray`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileInt`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.prependGeoTiffHeader`, `scala:edu.ucr.cs.bdlab.raptor.HDFTile`, `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsGlobal.rasterizePixels`, `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsGlobal.rasterizePoints`, `scala:edu.ucr.cs.bdlab.raptor.SlidingWindowTile`
- **6x** [compile] <path>:<n>: error: not enough arguments for constructor HDFTile: (tileID: Int, data: Array[Byte], valueSize: Int, fillValue: Int, scaleFacto
  - `scala:edu.ucr.cs.bdlab.raptor.HDFTile.componentType`, `scala:edu.ucr.cs.bdlab.raptor.HDFTile.getInt`, `scala:edu.ucr.cs.bdlab.raptor.HDFTile.getPixelValue`, `scala:edu.ucr.cs.bdlab.raptor.HDFTile.getShort`, `scala:edu.ucr.cs.bdlab.raptor.HDFTile.isEmpty`, `scala:edu.ucr.cs.bdlab.raptor.HDFTile.numComponents`
- **5x** [compile] <path>:<n>: error: value <name> is not a member of edu.ucr.cs.bdlab.beast.geolite.RasterMetadata
  - `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.allMetadata`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffReader`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffReader.getRasterMetadata`, `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsFocal.reshapeAverage`, `scala:edu.ucr.cs.bdlab.raptor.RasterOperationsFocal.reshapeBilinear`
- **4x** [compile] <path>:<n>: error: value <name> is not a member of edu.ucr.cs.bdlab.raptor.GeoTiffReader[Nothing]
  - `scala:edu.ucr.cs.bdlab.raptor.GeoTiffReader.close`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffReader.initialize`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffReader.isValidTile`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffReader.readTile`
- **4x** [compile] <path>:<n>: error: no arguments allowed for nullary constructor HDF4Reader: ()edu.ucr.cs.bdlab.raptor.HDF4Reader
  - `scala:edu.ucr.cs.bdlab.raptor.HDF4Reader.getTileOffset`, `scala:edu.ucr.cs.bdlab.raptor.HDF4Reader.loadRasterMetadata`, `scala:edu.ucr.cs.bdlab.raptor.HDF4Reader.metadata`, `scala:edu.ucr.cs.bdlab.raptor.HDF4Reader.readTile`
- **3x** [compile] <path>:<n>: error: not enough arguments for constructor EmptyTile: (tileID: Int, rasterMetadata: edu.ucr.cs.bdlab.beast.geolite.RasterMetada
  - `scala:edu.ucr.cs.bdlab.raptor.EmptyTile.componentType`, `scala:edu.ucr.cs.bdlab.raptor.EmptyTile.getPixelValue`, `scala:edu.ucr.cs.bdlab.raptor.EmptyTile.isEmpty`
- **3x** [compile] <path>:<n>: error: object DataType is not a member of package edu.ucr.cs.bdlab.beast.geolite
  - `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileFloat.componentType`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffTileIntArray.componentType`, `scala:edu.ucr.cs.bdlab.raptor.MemoryTile2.componentType`
- **3x** [compile] <path>:<n>: error: not enough arguments for constructor GeoTiffWriter: (outPath: org.apache.hadoop.fs.Path, rasterMetadata: edu.ucr.cs.bdlab
  - `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.close`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.setFillValue`, `scala:edu.ucr.cs.bdlab.raptor.GeoTiffWriter.write`
- **3x** [compile] <path>:<n>: error: trait IRasterReader takes type parameters
  - `scala:edu.ucr.cs.bdlab.raptor.IRasterReader.getFilePath`, `scala:edu.ucr.cs.bdlab.raptor.IRasterReader.getLayerName`, `scala:edu.ucr.cs.bdlab.raptor.IRasterReader.isValidTile`

## Why each API fails (242 failing)

### `scala:class:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.reproject` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:237`
- last error: ApiTest.scala:355: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_class_ed

### `scala:class:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.rescale` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:219`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_class_ed

### `scala:edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/DefaultReadOnlyTile.scala:38`
- last error: ApiTest.scala:353: error: object DataType is not a member of package edu.ucr.cs.bdlab.beast.common
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile.copy` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/DefaultReadOnlyTile.scala:108`
- last error: ApiTest.scala:355: error: value toTileRDD is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile.getPixelValue` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/DefaultReadOnlyTile.scala:54`
- last error: ApiTest.scala:352: error: value toTileRDD is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile.isEmpty` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/DefaultReadOnlyTile.scala:47`
- last error: ApiTest.scala:356: error: value tile is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.extents` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:152`
- last error: ApiTest.scala:353: error: overloaded method value apply with alternatives:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.get` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:181`
- last error: ApiTest.scala:353: error: value data is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.getPointValue` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:93`
- last error: ApiTest.scala:353: error: value getMBR is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.isDefined` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:126`
- last error: ApiTest.scala:353: error: value getWidth is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.isEmptyAt` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:114`
- last error: ApiTest.scala:353: error: value getEnvelope is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.isPixelInRange` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:188`
- last error: ApiTest.scala:353: error: value width is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.pixelLocations` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:81`
- last error: ApiTest.scala:353: error: Iterator[(Int, Int)] does not take parameters
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.pixels` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:84`
- last error: ApiTest.scala:353: error: Iterator[(Int, Int, Array[Float])] does not take parameters
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.rasterMetadataToRow` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:220`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.schema` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:40`
- last error: ApiTest.scala:356: error: class ITile takes type parameters
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.setAttribute` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:196`
- last error: ApiTest.scala:357: error: value getAttribute is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITile.toString` — runtime

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:145`
- last error: java.lang.AssertionError: assertion failed: ITile.toString output 'Tile #0 (0,0) - (255,255)' did not contain expected metadata markers
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] java.lang.AssertionError: assertion failed: ITile.toString output 'Tile #0 (0,0) - (255,255)' did not contain expected metadata markers

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITileSerializer` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITileSerializer.scala:30`
- last error: ApiTest.scala:354: error: value serialize is not a member of edu.ucr.cs.bdlab.beast.geolite.ITileSerializer[Nothing]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.ITileSerializer.read` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITileSerializer.scala:74`
- last error: ApiTest.scala:359: error: type RasterTile is not a member of package edu.ucr.cs.bdlab.beast.geolite
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterFeature.append` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterFeature.scala:59`
- last error: ApiTest.scala:356: error: not enough arguments for constructor RasterFeature: (values: Array[Any], schema: org.apache.spark.sql.types.StructType)edu.ucr.cs.bdlab.beast.geolite.RasterFeature.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterFeature.setOrAppend` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterFeature.scala:35`
- last error: ApiTest.scala:357: error: not enough arguments for constructor RasterFeature: (values: Array[Any], schema: org.apache.spark.sql.types.StructType)edu.ucr.cs.bdlab.beast.geolite.RasterFeature.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterFeatureSerializer` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterFeatureSerializer.scala:25`
- last error: ApiTest.scala:362: error: value serialize is not a member of edu.ucr.cs.bdlab.beast.geolite.RasterFeatureSerializer
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterFeatureSerializer.read` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterFeatureSerializer.scala:31`
- last error: ApiTest.scala:362: error: type mismatch;
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterFeatureSerializer.write` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterFeatureSerializer.scala:26`
- last error: ApiTest.scala:367: error: type mismatch;
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.allMetadata` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:337`
- last error: ApiTest.scala:356: error: value numBands is not a member of edu.ucr.cs.bdlab.beast.geolite.RasterMetadata
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.create` — runtime

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:324`
- last error: java.lang.AssertionError: assertion failed: Metadata properties did not match input parameters
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] java.lang.AssertionError: assertion failed: Metadata properties did not match input parameters

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.envelope` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:170`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.equals` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:196`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.extents` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:181`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.forOneTile` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:300`
- last error: ApiTest.scala:353: error: value forOneTile is not a member of object edu.ucr.cs.bdlab.beast.geolite.RasterMetadata
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getPixelScaleX` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:93`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileIDAtPixel` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:69`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileIDAtPoint` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:81`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileX1` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:107`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileX2` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:118`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileY1` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:128`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.getTileY2` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:139`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.gridToGridTransform` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:425`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.gridToModel` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:150`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.hashCode` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:204`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.isPixelInRange` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:194`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.modelToGrid` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:161`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.numTiles` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:61`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.numTilesX` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:55`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.numTilesY` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:58`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.rasterHeight` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:52`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.rasterWidth` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:49`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.tileIDs` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:91`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.toString` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:209`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:26`
- last error: ApiTest.scala:353: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` — runtime

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:53`
- last error: java.lang.AssertionError: assertion failed: Expected isImmutable to be false, but got true
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] java.lang.AssertionError: assertion failed: Expected isImmutable to be false, but got true

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.read` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:40`
- last error: ApiTest.scala:358: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.write` — compile

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:27`
- last error: ApiTest.scala:358: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterSchemaHelper.readExternalObj` — runtime

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterSchemaHelper.scala:46` · reached: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterSchemaHelper.scala:48`
- last error: java.io.EOFException: null
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] java.io.EOFException: null

### `scala:edu.ucr.cs.bdlab.beast.geolite.RasterSchemaHelper.readType` — runtime

- canonical source: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterSchemaHelper.scala:68` · reached: `source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterSchemaHelper.scala:69`
- last error: java.io.EOFException: null
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] java.io.EOFException: null

### `scala:edu.ucr.cs.bdlab.raptor.AbstractConvolutionTile.componentType` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:113`
- last error: ApiTest.scala:352: error: object ConvolutionTile is not a member of package edu.ucr.cs.bdlab.raptor
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.AbstractConvolutionTile.isEmpty` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:44`
- last error: ApiTest.scala:360: error: type ConvolutionTile is not a member of package edu.ucr.cs.bdlab.raptor
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.AbstractConvolutionTile.merge` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:77`
- last error: ApiTest.scala:352: error: object FloatArrayTile is not a member of package edu.ucr.cs.bdlab.raptor
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.AbstractGeoTiffTile.isEmpty` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/AbstractGeoTiffTile.scala:35`
- last error: ApiTest.scala:352: error: value _2 is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsIterator` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsIterator.scala:7`
- last error: ApiTest.scala:354: error: type mismatch;
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsIterator.hasNext` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsIterator.scala:40`
- last error: ApiTest.scala:352: error: object RasterFeatureJoin is not a member of package edu.ucr.cs.bdlab.raptor
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsIterator.moveToNextIntersections` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsIterator.scala:25`
- last error: ApiTest.scala:357: error: value join is not a member of object edu.ucr.cs.bdlab.raptor.RaptorJoin
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsIterator.next` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsIterator.scala:42`
- last error: ApiTest.scala:353: error: object ReadWriteMixin is not a member of package org.apache.spark.beast.sql
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsTileBreaker` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsTileBreaker.scala:14`
- last error: ApiTest.scala:358: error: value rdd is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsTileBreaker.hasNext` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsTileBreaker.scala:40`
- last error: ApiTest.scala:358: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsTileBreaker.moveToNextIntersections` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsTileBreaker.scala:26`
- last error: ApiTest.scala:360: error: type mismatch;
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.CompactIntersectionsTileBreaker.next` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/CompactIntersectionsTileBreaker.scala:42`
- last error: ApiTest.scala:352: error: too many arguments (2) for constructor CompactIntersectionsTileBreaker: (intersections: Iterator[(Int, edu.ucr.cs.bdlab.raptor.Intersections)])edu.ucr.cs.bdlab.raptor.CompactIntersectionsTileBreaker
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileMultiBand` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:143`
- last error: ApiTest.scala:354: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileMultiBand.getPixelValue` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:163`
- last error: ApiTest.scala:356: error: value _2 is not a member of edu.ucr.cs.bdlab.beast.geolite.ITile[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileSerializer` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTileSerializer.scala:30`
- last error: ApiTest.scala:354: error: value serialize is not a member of edu.ucr.cs.bdlab.raptor.ConvolutionTileSerializer
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileSerializer.read` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTileSerializer.scala:50`
- last error: ApiTest.scala:354: error: object RasterTile is not a member of package edu.ucr.cs.bdlab.raptor
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileSerializer.write` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTileSerializer.scala:32`
- last error: ApiTest.scala:361: error: not enough arguments for constructor AbstractConvolutionTile: (tileID: Int, metadata: edu.ucr.cs.bdlab.beast.geolite.RasterMetadata, rasterFeature: edu.ucr.cs.bdlab.beast.geolite.RasterFeature, w: Int, weights: Array[Float], sourceTileID: Int, pixelValues: Array[Float], pix
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileSingleBand` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:117`
- last error: ApiTest.scala:352: error: object RasterMetadata is not a member of package edu.ucr.cs.bdlab.raptor
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileSingleBand.getPixelValue` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:135`
- last error: ApiTest.scala:358: error: not enough arguments for constructor ConvolutionTileSingleBand: (tileID: Int, metadata: edu.ucr.cs.bdlab.beast.geolite.RasterMetadata, rasterFeature: edu.ucr.cs.bdlab.beast.geolite.RasterFeature, w: Int, weights: Array[Float], stid: Int, values: Array[Float], exists: edu.uc
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.ConvolutionTileSingleBand.numComponents` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ConvolutionTile.scala:137`
- last error: ApiTest.scala:360: error: not enough arguments for constructor ConvolutionTileSingleBand: (tileID: Int, metadata: edu.ucr.cs.bdlab.beast.geolite.RasterMetadata, rasterFeature: edu.ucr.cs.bdlab.beast.geolite.RasterFeature, w: Int, weights: Array[Float], stid: Int, values: Array[Float], exists: edu.uc
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.EmptyTile` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/EmptyTile.scala:15`
- last error: ApiTest.scala:352: error: value metadata is not a member of edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD[Array[Float]]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.EmptyTile.componentType` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/EmptyTile.scala:23`
- last error: ApiTest.scala:357: error: not enough arguments for constructor EmptyTile: (tileID: Int, rasterMetadata: edu.ucr.cs.bdlab.beast.geolite.RasterMetadata, numComponents: Int, rasterFeature: edu.ucr.cs.bdlab.beast.geolite.RasterFeature)edu.ucr.cs.bdlab.raptor.EmptyTile[T].
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.EmptyTile.getPixelValue` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/EmptyTile.scala:21`
- last error: ApiTest.scala:355: error: not enough arguments for constructor EmptyTile: (tileID: Int, rasterMetadata: edu.ucr.cs.bdlab.beast.geolite.RasterMetadata, numComponents: Int, rasterFeature: edu.ucr.cs.bdlab.beast.geolite.RasterFeature)edu.ucr.cs.bdlab.raptor.EmptyTile[Float].
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

### `scala:edu.ucr.cs.bdlab.raptor.EmptyTile.isEmpty` — compile

- canonical source: `source/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/EmptyTile.scala:18`
- last error: ApiTest.scala:354: error: not enough arguments for constructor EmptyTile: (tileID: Int, rasterMetadata: edu.ucr.cs.bdlab.beast.geolite.RasterMetadata, numComponents: Int, rasterFeature: edu.ucr.cs.bdlab.beast.geolite.RasterFeature)edu.ucr.cs.bdlab.raptor.EmptyTile[T].
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala/execution/run_scala_edu.ucr.

_… 162 more failing APIs omitted (--max-api-detail to raise)._
