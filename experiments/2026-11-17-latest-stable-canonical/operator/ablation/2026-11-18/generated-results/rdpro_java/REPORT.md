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