# Fix-loop report — result

_Generated 2026-11-18 09:46 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-173346Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **100/217** raw (46.1%)  ·  scored **100/217** (46.1%) after excluding 0 infra
- wall 0.21 h  ·  tokens in 511,581 / out 56,231 ·  llm calls 217  ·  max_fix_rounds 0
- pass-by-round: r0:100  ·  **0 rescued by the fix loop** (pass@0 = 100)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **40x** [runtime] AssertionError
  - `sql:RS_UpperLeftY`, `sql:ST_Affine`, `sql:ST_AsText`, `sql:ST_Boundary`, `sql:ST_Contains`, `sql:ST_Difference`, `sql:ST_EndPoint`, `sql:ST_Envelope`, `sql:ST_Envelope_Agg`, `sql:ST_Force3D`, `sql:ST_GeomCollFromText`, `sql:ST_GeomFromEWKB`, `sql:ST_GeomFromEWKT`, `sql:ST_InteriorRingN` …
- **23x** [unknown] args), self, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: Error during planning: Inv
  - `sql:RS_AsGeoTiff`, `sql:RS_BandPath`, `sql:RS_BandToDim`, `sql:RS_Clip`, `sql:RS_DimToBand`, `sql:RS_IsEmpty`, `sql:RS_MinConvexHull`, `sql:RS_PixelAsPolygon`, `sql:RS_ReplaceBandNoDataValue`, `sql:RS_ReprojectMatch`, `sql:RS_Resample`, `sql:RS_SetCRS`, `sql:RS_SetGeoReference`, `sql:RS_Slice` …
- **11x** [runtime] AttributeError: <name> object has no attribute <name>
  - `sql:RS_BandPixelType`, `sql:RS_ConvexHull`, `sql:RS_Envelope`, `sql:RS_PixelAsCentroid`, `sql:RS_PixelAsPoint`, `sql:RS_RasterToWorldCoord`, `sql:RS_RasterToWorldCoordX`, `sql:RS_RasterToWorldCoordY`, `sql:RS_Shape`, `sql:ST_SimplifyPreserveTopology`, `sql:rs_ensureloaded`
- **2x** [unknown] me.to_arrow_table(*args, **kwargs) File "<path>", line <n>, in to_arrow_table batches = self._impl.to_batches(schema) sedonadb._lib.SedonaEr
  - `sql:RS_AsRaster`, `sql:RS_Value`
- **2x** [unknown] s) File "<path>", line <n>, in to_arrow_table batches = self._impl.to_batches(schema) sedonadb._lib.SedonaError: Cannot evaluate spatial pre
  - `sql:RS_Contains`, `sql:RS_Intersects`
- **2x** [unknown] sql(query, **kwargs), self, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: Error durin
  - `sql:RS_GeoReference`, `sql:RS_WorldToRasterCoordY`
- **2x** [runtime] TypeError: a bytes-like object is required, not <name>
  - `sql:ST_DelaunayTriangles`, `sql:ST_MLineFromText`
- **2x** [unknown] to_arrow_table result = self._frame.to_arrow_table(*args, **kwargs) File "<path>", line <n>, in to_arrow_table batches = self._impl.to_batch
  - `sql:ST_X`, `sql:ST_Y`
- **1x** [unknown] elf, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: Error during planning: Invalid fun
  - `sql:RS_BandIsNoData`
- **1x** [runtime] AssertionError: Expected width 5, got 64
  - `sql:RS_Example`
- **1x** [unknown] **kwargs), self, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: Error during planning:
  - `sql:RS_FromGDALRaster`
- **1x** [unknown] _arrow_table(*args, **kwargs) File "<path>", line <n>, in to_arrow_table batches = self._impl.to_batches(schema) sedonadb._lib.SedonaError:
  - `sql:RS_SetValue`

## Why each API fails (117 failing)

### `sql:RS_AsGeoTiff` — unknown

- canonical source: `source/docs/reference/sql/rs_asgeotiff.qmd:19`
- last error: args), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Error during planning: Invalid function 'rs_fromgeotiff'.
Did you mean 'rs_asgeotiff'?
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] args), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = 

### `sql:RS_AsRaster` — unknown

- canonical source: `source/docs/reference/sql/rs_asraster.qmd:19`
- last error: me.to_arrow_table(*args, **kwargs)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 1496, in to_arrow_table
    batches = self._impl.to_batches(schema)