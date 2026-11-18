# Fix-loop report — result

_Generated 2026-11-18 09:59 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-174705Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **5/69** raw (7.2%)  ·  scored **5/69** (7.2%) after excluding 0 infra
- wall 0.2 h  ·  tokens in 133,382 / out 14,820 ·  llm calls 69  ·  max_fix_rounds 0
- pass-by-round: r0:5  ·  **0 rescued by the fix loop** (pass@0 = 5)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **9x** [compile] <path>:<n>: error: cannot find symbol
  - `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata`, `java:edu.ucr.cs.bdlab.raptor.Intersections.getY`, `java:edu.ucr.cs.bdlab.raptor.PixelScale.getScaleX`, `java:edu.ucr.cs.bdlab.raptor.PixelScale.getScaleY`, `java:edu.ucr.cs.bdlab.raptor.PixelScale.getValues`, `java:edu.ucr.cs.bdlab.raptor.Statistics.accumulate`, `java:edu.ucr.cs.bdlab.raptor.Statistics.setNumBands`, `java:edu.ucr.cs.bdlab.raptor.TiePoint`, `java:edu.ucr.cs.bdlab.raptor.TiePoint.set`
- **3x** [compile] <path>:<n>: error: illegal start of ex
  - `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getValueOffset`, `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata2CRSAdapter`, `java:edu.ucr.cs.bdlab.raptor.Intersections.getFeatureID`
- **3x** [compile] <path>:<n>: error: constructor GeoKeyEntry i
  - `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.hashCode`, `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.setCount`, `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.setKeyID`
- **3x** [compile] <path>:<n>: error: no suitable constructor fo
  - `java:edu.ucr.cs.bdlab.raptor.PixelScale.hashCode`, `java:edu.ucr.cs.bdlab.raptor.PixelScale.toString`, `java:edu.ucr.cs.bdlab.raptor.TiePoint.getValueAt`
- **2x** [compile] <path>:<n>: error: constructor GeoKeyEntry
  - `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.compareTo`, `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getValues`
- **2x** [compile] <path>:<n>: error: illegal start of expressi
  - `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getKeyID`, `java:edu.ucr.cs.bdlab.raptor.PixelScale.getScaleZ`
- **2x** [compile] <path>:<n>: error: constructor Geo
  - `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.setTiffTagLocation`, `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.hasPixelScales`
- **2x** [compile] <path>:<n>: error: constru
  - `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getGeoKeyMinorRevision`, `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getModelTransformation`
- **2x** [compile] <path>:<n>: error: constructor
  - `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getGeoKeyRevision`, `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getModelTiePoints`
- **2x** [compile] <path>:<n>: error: no suitable constructor foun
  - `java:edu.ucr.cs.bdlab.raptor.PixelScale.equals`, `java:edu.ucr.cs.bdlab.raptor.TiePoint.toString`
- **2x** [compile] <path>:<n>: error: no suitable constructor found
  - `java:edu.ucr.cs.bdlab.raptor.PixelScale.isSet`, `java:edu.ucr.cs.bdlab.raptor.TiePoint.equals`
- **1x** [compile] <path>:<n>: error: keyID has private access in GeoKey
  - `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry`

## Why each API fails (64 failing)

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:56`
- last error: ApiTest.java:50: error: keyID has private access in GeoKey
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.compareTo` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:109`
- last error: ApiTest.java:41: error: constructor GeoKeyEntry 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.equals` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:27`
- last error: ApiTest.java:41: error: constructor GeoKeyEntry in 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getCount` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:77`
- last error: ApiTest.java:41: error: incompatible types: int[]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getKeyID` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:69`
- last error: ApiTest.java:41: error: illegal start of expressi
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getTiffTagLocation` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:73`
- last error: ApiTest.java:41: error: illegal start o
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getValueOffset` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:81`
- last error: ApiTest.java:41: error: illegal start of ex
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.getValues` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:105`
- last error: ApiTest.java:41: error: constructor GeoKeyEntry 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.hashCode` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:38`
- last error: ApiTest.java:41: error: constructor GeoKeyEntry i
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.setCount` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:85`
- last error: ApiTest.java:41: error: constructor GeoKeyEntry i
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.setKeyID` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:90`
- last error: ApiTest.java:41: error: constructor GeoKeyEntry i
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.setTiffTagLocation` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:95`
- last error: ApiTest.java:41: error: constructor Geo
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoKeyEntry.setValueOffset` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoKeyEntry.java:100`
- last error: ApiTest.java:41: error: constructor GeoKeyE
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffException` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffException.java:43`
- last error: ApiTest.java:41: error: illegal start of expression
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffException.getMessage` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffException.java:70`
- last error: ApiTest.java:42: error: constructor GeoTif
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:46`
- last error: ApiTest.java:41: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getGeoKey` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:227`
- last error: ApiTest.java:41: error: constructor GeoTiffM
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getGeoKeyDirectoryVersion` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:195`
- last error: ApiTest.java:41: error: cons
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getGeoKeyMinorRevision` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:213`
- last error: ApiTest.java:41: error: constru
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getGeoKeyRevision` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:204`
- last error: ApiTest.java:41: error: constructor 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getModelPixelScales` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:332`
- last error: ApiTest.java:41: error: constructo
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getModelTiePoints` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:341`
- last error: ApiTest.java:41: error: constructor 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.getModelTransformation` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:316`
- last error: ApiTest.java:41: error: constru
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.hasModelTrasformation` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:360`
- last error: ApiTest.java:41: error: construc
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.hasPixelScales` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:369`
- last error: ApiTest.java:41: error: constructor Geo
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata.hasTiePoints` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata.java:350`
- last error: ApiTest.java:41: error: constructor GeoTi
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata2CRSAdapter` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata2CRSAdapter.java:140`
- last error: ApiTest.java:41: error: illegal start of ex
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata2CRSAdapter.createCoordinateSystem` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata2CRSAdapter.java:169`
- last error: ApiTest.java:41: err
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata2CRSAdapter.getRasterToModel` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata2CRSAdapter.java:428`
- last error: ApiTest.java:41: error: il
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.GeoTiffMetadata2CRSAdapter.getRasterType` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/GeoTiffMetadata2CRSAdapter.java:550`
- last error: ApiTest.java:41: error: illeg
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.compute` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:155`
- last error: ApiTest.java:43: error: non-static method comput
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.getFeatureID` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:121`
- last error: ApiTest.java:41: error: illegal start of ex
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.getNumIntersections` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:81`
- last error: ApiTest.java:41: error: illegal star
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.getPolygonIndex` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:117`
- last error: ApiTest.java:47: error: non-static metho
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.getTileID` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:125`
- last error: ApiTest.java:42: error: non-static method getT
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.getX1` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:90`
- last error: ApiTest.java:41: error: illegal start of expressio
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.getX2` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:99`
- last error: ApiTest.java:42: error: non-static method getX2(in
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Intersections.getY` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:108`
- last error: ApiTest.java:42: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:52`
- last error: ApiTest.java:48: error: scaleX has private access in PixelS
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.equals` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:25`
- last error: ApiTest.java:41: error: no suitable constructor foun
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.getScaleX` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:64`
- last error: ApiTest.java:41: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.getScaleY` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:72`
- last error: ApiTest.java:41: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.getScaleZ` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:80`
- last error: ApiTest.java:41: error: illegal start of expressi
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.getValues` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:88`
- last error: ApiTest.java:41: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.hashCode` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:36`
- last error: ApiTest.java:41: error: no suitable constructor fo
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.isSet` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:92`
- last error: ApiTest.java:41: error: no suitable constructor found
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.PixelScale.toString` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/PixelScale.java:43`
- last error: ApiTest.java:41: error: no suitable constructor fo
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.RaptorSplit` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/RaptorSplit.java:43`
- last error: ApiTest.java:46: error: no suitable method found for compu
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.RaptorSplit.getLength` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/RaptorSplit.java:51`
- last error: ApiTest.java:41: error: illegal start of express
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.RaptorSplit.getLocations` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/RaptorSplit.java:56`
- last error: ApiTest.java:41: error: incompatible types: S
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.RasterHelper.createRasterReader` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/RasterHelper.java:10`
- last error: ApiTest.java:43: error: cannot find sy
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Statistics.accumulate` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:106`
- last error: ApiTest.java:41: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Statistics.collect` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:90`
- last error: ApiTest.java:44: error: non-static method collect(i
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Statistics.getNumBands` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:121`
- last error: ApiTest.java:41: error: constructor Statistics 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Statistics.invalidate` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:126`
- last error: ApiTest.java:41: error: non-static method invali
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` — runtime

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:131`
- last error: AssertionError: Statistics object should be invalid before computation.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Statistics object should be invalid before computation.

### `java:edu.ucr.cs.bdlab.raptor.Statistics.setNumBands` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:52`
- last error: ApiTest.java:42: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.Statistics.toString` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:45`
- last error: ApiTest.java:42: error: incompatible types: int ca
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.TiePoint` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/TiePoint.java:26`
- last error: ApiTest.java:52: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.TiePoint.equals` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/TiePoint.java:65`
- last error: ApiTest.java:41: error: no suitable constructor found 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.TiePoint.getValueAt` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/TiePoint.java:39`
- last error: ApiTest.java:41: error: no suitable constructor fo
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.TiePoint.isSet` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/TiePoint.java:51`
- last error: ApiTest.java:46: error: method set in class TiePoint ca
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.TiePoint.set` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/TiePoint.java:30`
- last error: ApiTest.java:49: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs

### `java:edu.ucr.cs.bdlab.raptor.TiePoint.toString` — compile

- canonical source: `source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/TiePoint.java:80`
- last error: ApiTest.java:41: error: no suitable constructor foun
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java/execution/run_java_edu.ucr.cs
