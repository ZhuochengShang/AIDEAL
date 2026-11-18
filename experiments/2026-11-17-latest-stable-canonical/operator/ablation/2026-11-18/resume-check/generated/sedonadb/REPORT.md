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
sedonadb._lib.SedonaError: reference raster has a CRS but the geometry does not
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] me.to_arrow_table(*args, **kwargs)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", li

### `sql:RS_BandIsNoData` — unknown

- canonical source: `source/docs/reference/sql/rs_bandisnodata.qmd:19`
- last error: elf,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Error during planning: Invalid function 'rs_addbandfromarray'.
Did you mean 'rs_bandisnodata'?
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] elf,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFram

### `sql:RS_BandPath` — unknown

- canonical source: `source/docs/reference/sql/rs_bandpath.qmd:19`
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

### `sql:RS_BandPixelType` — runtime

- canonical source: `source/docs/reference/sql/rs_bandpixeltype.qmd:19`
- last error: AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'

### `sql:RS_BandToDim` — unknown

- canonical source: `source/docs/reference/sql/rs_bandtodim.qmd:19`
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

### `sql:RS_Clip` — unknown

- canonical source: `source/docs/reference/sql/rs_clip.qmd:19`
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

### `sql:RS_Contains` — unknown

- canonical source: `source/docs/reference/sql/rs_contains.qmd:19`
- last error: s)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 1496, in to_arrow_table
    batches = self._impl.to_batches(schema)
sedonadb._lib.SedonaError: Cannot evaluate spatial predicate: left geometry has CRS but right geometry does not
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] s)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 1496, in to_arrow_table
    b

### `sql:RS_ConvexHull` — runtime

- canonical source: `source/docs/reference/sql/rs_convexhull.qmd:19`
- last error: AttributeError: 'dict' object has no attribute 'startswith'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'dict' object has no attribute 'startswith'

### `sql:RS_DimToBand` — unknown

- canonical source: `source/docs/reference/sql/rs_dimtoband.qmd:19`
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

### `sql:RS_Envelope` — runtime

- canonical source: `source/docs/reference/sql/rs_envelope.qmd:19`
- last error: AttributeError: 'dict' object has no attribute 'startswith'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'dict' object has no attribute 'startswith'

### `sql:RS_Example` — runtime

- canonical source: `source/docs/reference/sql/rs_example.qmd:19`
- last error: AssertionError: Expected width 5, got 64
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected width 5, got 64

### `sql:RS_FromGDALRaster` — unknown

- canonical source: `source/docs/reference/sql/rs_fromgdalraster.qmd:19`
- last error: **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Error during planning: Invalid function 'rs_asbinary'.
Did you mean 'st_asbinary'?
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    d

### `sql:RS_GeoReference` — unknown

- canonical source: `source/docs/reference/sql/rs_georeference.qmd:19`
- last error: sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Error during planning: table 'datafusion.public.raster_table' not found
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, i

### `sql:RS_Intersects` — unknown

- canonical source: `source/docs/reference/sql/rs_intersects.qmd:19`
- last error: s)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 1496, in to_arrow_table
    batches = self._impl.to_batches(schema)
sedonadb._lib.SedonaError: Cannot evaluate spatial predicate: left geometry has CRS but right geometry does not
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] s)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 1496, in to_arrow_table
    b

### `sql:RS_IsEmpty` — unknown

- canonical source: `source/docs/reference/sql/rs_isempty.qmd:19`
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

### `sql:RS_MinConvexHull` — unknown

- canonical source: `source/docs/reference/sql/rs_minconvexhull.qmd:19`
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

### `sql:RS_PixelAsCentroid` — runtime

- canonical source: `source/docs/reference/sql/rs_pixelascentroid.qmd:19`
- last error: AttributeError: 'dict' object has no attribute 'startswith'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'dict' object has no attribute 'startswith'

### `sql:RS_PixelAsPoint` — runtime

- canonical source: `source/docs/reference/sql/rs_pixelaspoint.qmd:19`
- last error: AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'

### `sql:RS_PixelAsPolygon` — unknown

- canonical source: `source/docs/reference/sql/rs_pixelaspolygon.qmd:19`
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

### `sql:RS_RasterToWorldCoord` — runtime

- canonical source: `source/docs/reference/sql/rs_rastertoworldcoord.qmd:19`
- last error: AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'

### `sql:RS_RasterToWorldCoordX` — runtime

- canonical source: `source/docs/reference/sql/rs_rastertoworldcoordx.qmd:19`
- last error: AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'

### `sql:RS_RasterToWorldCoordY` — runtime

- canonical source: `source/docs/reference/sql/rs_rastertoworldcoordy.qmd:19`
- last error: AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'

### `sql:RS_ReplaceBandNoDataValue` — unknown

- canonical source: `source/docs/reference/sql/rs_replacebandnodatavalue.qmd:19`
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

### `sql:RS_ReprojectMatch` — unknown

- canonical source: `source/docs/reference/sql/rs_reprojectmatch.qmd:19`
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

### `sql:RS_Resample` — unknown

- canonical source: `source/docs/reference/sql/rs_resample.qmd:19`
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

### `sql:RS_SRID` — unknown

- canonical source: `source/docs/reference/sql/rs_srid.qmd:19`
- last error: subtype": "Cartesian",
    "axis": [
      {
        "name": "Easting",
        "abbreviation": "",
        "direction": "east",
        "unit": "metre"
      },
      {
        "name": "Northing",
        "abbreviation": "",
        "direction": "north",
        "unit": "metre"
      }
    ]
  }
}'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] subtype": "Cartesian",
    "axis": [
      {
        "name": "Easting",
        "abbreviation": "",
        "direction": "east",
        "unit": "metr

### `sql:RS_SetCRS` — unknown

- canonical source: `source/docs/reference/sql/rs_setcrs.qmd:19`
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

### `sql:RS_SetGeoReference` — unknown

- canonical source: `source/docs/reference/sql/rs_setgeoreference.qmd:19`
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

### `sql:RS_SetValue` — unknown

- canonical source: `source/docs/reference/sql/rs_setvalue.qmd:19`
- last error: _arrow_table(*args, **kwargs)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 1496, in to_arrow_table
    batches = self._impl.to_batches(schema)
sedonadb._lib.SedonaError: RS_Value: Band 5 is out of range: this raster has 1 bands
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] _arrow_table(*args, **kwargs)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 14

### `sql:RS_Shape` — runtime

- canonical source: `source/docs/reference/sql/rs_shape.qmd:19`
- last error: AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TrackedFrame' object has no attribute 'createOrReplaceTempView'

### `sql:RS_Slice` — unknown

- canonical source: `source/docs/reference/sql/rs_slice.qmd:19`
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

### `sql:RS_SliceRange` — unknown

- canonical source: `source/docs/reference/sql/rs_slicerange.qmd:19`
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

### `sql:RS_Stack` — unknown

- canonical source: `source/docs/reference/sql/rs_stack.qmd:19`
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

### `sql:RS_SummaryStats` — unknown

- canonical source: `source/docs/reference/sql/rs_summarystats.qmd:19`
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

### `sql:RS_SummaryStatsAll` — unknown

- canonical source: `source/docs/reference/sql/rs_summarystatsall.qmd:19`
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

### `sql:RS_Tile` — unknown

- canonical source: `source/docs/reference/sql/rs_tile.qmd:19`
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

### `sql:RS_UpperLeftY` — runtime

- canonical source: `source/docs/reference/sql/rs_upperlefty.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:RS_Value` — unknown

- canonical source: `source/docs/reference/sql/rs_value.qmd:19`
- last error: me.to_arrow_table(*args, **kwargs)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", line 1496, in to_arrow_table
    batches = self._impl.to_batches(schema)
sedonadb._lib.SedonaError: RS_Value: raster has a CRS but the geometry does not
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] me.to_arrow_table(*args, **kwargs)
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/dataframe.py", li

### `sql:RS_Values` — unknown

- canonical source: `source/docs/reference/sql/rs_values.qmd:19`
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

### `sql:RS_WorldToRasterCoord` — unknown

- canonical source: `source/docs/reference/sql/rs_worldtorastercoord.qmd:19`
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

### `sql:RS_WorldToRasterCoordY` — unknown

- canonical source: `source/docs/reference/sql/rs_worldtorastercoordy.qmd:19`
- last error: sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Error during planning: table 'datafusion.public.raster_table' not found
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, i

### `sql:RS_ZonalStats` — unknown

- canonical source: `source/docs/reference/sql/rs_zonalstats.qmd:19`
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

### `sql:RS_ZonalStatsAll` — unknown

- canonical source: `source/docs/reference/sql/rs_zonalstatsall.qmd:19`
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

### `sql:SD_Format` — runtime

- canonical source: `source/docs/reference/sql/sd_format.qmd:19`
- last error: AssertionError: Formatted output POINT(1 2) does not contain expected coordinates
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Formatted output POINT(1 2) does not contain expected coordinates

### `sql:ST_Affine` — runtime

- canonical source: `source/docs/reference/sql/st_affine.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_AsText` — runtime

- canonical source: `source/docs/reference/sql/st_astext.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_Boundary` — runtime

- canonical source: `source/docs/reference/sql/st_boundary.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_BuildArea` — runtime

- canonical source: `source/docs/reference/sql/st_buildarea.qmd:19`
- last error: AssertionError: Expected POLYGON for open linestring, got GEOMETRYCOLLECTION EMPTY
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POLYGON for open linestring, got GEOMETRYCOLLECTION EMPTY

### `sql:ST_CRS` — runtime

- canonical source: `source/docs/reference/sql/st_crs.qmd:19`
- last error: AssertionError: Expected CRS to contain 4326, but got OGC:CRS84
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected CRS to contain 4326, but got OGC:CRS84

### `sql:ST_Centroid` — runtime

- canonical source: `source/docs/reference/sql/st_centroid.qmd:19`
- last error: AssertionError: Expected POINT (-6 26.5), got POINT(-6 26.5)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POINT (-6 26.5), got POINT(-6 26.5)

### `sql:ST_ClosestPoint` — unknown

- canonical source: `source/docs/reference/sql/st_closestpoint.qmd:19`
- last error: ntext.sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: st_closestpoint(geometry, geometry): No kernel matching arguments
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] ntext.sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 

### `sql:ST_Contains` — runtime

- canonical source: `source/docs/reference/sql/st_contains.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_DelaunayTriangles` — runtime

- canonical source: `source/docs/reference/sql/st_delaunaytriangles.qmd:19`
- last error: TypeError: a bytes-like object is required, not 'str'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: a bytes-like object is required, not 'str'

### `sql:ST_Difference` — runtime

- canonical source: `source/docs/reference/sql/st_difference.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_Dump` — runtime

- canonical source: `source/docs/reference/sql/st_dump.qmd:19`
- last error: AssertionError: Expected 3 rows, got 1
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected 3 rows, got 1

### `sql:ST_EndPoint` — runtime

- canonical source: `source/docs/reference/sql/st_endpoint.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_Envelope` — runtime

- canonical source: `source/docs/reference/sql/st_envelope.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_Envelope_Agg` — runtime

- canonical source: `source/docs/reference/sql/st_envelope_agg.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_ExteriorRing` — runtime

- canonical source: `source/docs/reference/sql/st_exteriorring.qmd:19`
- last error: AssertionError: Expected LINESTRING (0 0, 4 0, 4 4, 0 4, 0 0), got LINESTRING(0 0,4 0,4 4,0 4,0 0)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected LINESTRING (0 0, 4 0, 4 4, 0 4, 0 0), got LINESTRING(0 0,4 0,4 4,0 4,0 0)

### `sql:ST_FlipCoordinates` — runtime

- canonical source: `source/docs/reference/sql/st_flipcoordinates.qmd:19`
- last error: AssertionError: Expected POINT (20 10), got POINT(20 10)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POINT (20 10), got POINT(20 10)

### `sql:ST_Force2D` — runtime

- canonical source: `source/docs/reference/sql/st_force2d.qmd:19`
- last error: AssertionError: Expected POINT (10 20), got POINT(10 20)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POINT (10 20), got POINT(10 20)

### `sql:ST_Force3D` — runtime

- canonical source: `source/docs/reference/sql/st_force3d.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_Force3DM` — runtime

- canonical source: `source/docs/reference/sql/st_force3dm.qmd:19`
- last error: AssertionError: Expected POINT ZM (1 2 0 10), got POINT M(1 2 10)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POINT ZM (1 2 0 10), got POINT M(1 2 10)

### `sql:ST_Force4D` — runtime

- canonical source: `source/docs/reference/sql/st_force4d.qmd:19`
- last error: AssertionError: Expected POINT ZM (1 2 3 4), got POINT ZM(1 2 3 4)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POINT ZM (1 2 3 4), got POINT ZM(1 2 3 4)

### `sql:ST_GeogFromWKT` — unknown

- canonical source: `source/docs/reference/sql/st_geogfromwkt.qmd:19`
- last error: kedFrame(self._context.sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Config value "global" not found on SedonaOptions
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] kedFrame(self._context.sql(query, **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/c

### `sql:ST_GeomCollFromText` — runtime

- canonical source: `source/docs/reference/sql/st_geomcollfromtext.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_GeomFromEWKB` — runtime

- canonical source: `source/docs/reference/sql/st_geomfromewkb.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_GeomFromEWKT` — runtime

- canonical source: `source/docs/reference/sql/st_geomfromewkt.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_GeometryN` — runtime

- canonical source: `source/docs/reference/sql/st_geometryn.qmd:19`
- last error: AssertionError: Expected POINT (3 4), got POINT(3 4)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POINT (3 4), got POINT(3 4)

### `sql:ST_InteriorRingN` — runtime

- canonical source: `source/docs/reference/sql/st_interiorringn.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_Intersection_Agg` — runtime

- canonical source: `source/docs/reference/sql/st_intersection_agg.qmd:19`
- last error: AssertionError: Expected POLYGON ((2 2, 2 4, 4 4, 4 2, 2 2)), got MULTIPOLYGON(((2 4,2 2,4 2,4 4,2 4)))
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POLYGON ((2 2, 2 4, 4 4, 4 2, 2 2)), got MULTIPOLYGON(((2 4,2 2,4 2,4 4,2 4)))

### `sql:ST_IsValidReason` — runtime

- canonical source: `source/docs/reference/sql/st_isvalidreason.qmd:19`
- last error: AssertionError: Expected self-intersection error, got: Valid Geometry
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected self-intersection error, got: Valid Geometry

### `sql:ST_LineFromText` — runtime

- canonical source: `source/docs/reference/sql/st_linefromtext.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_LineInterpolatePoint` — runtime

- canonical source: `source/docs/reference/sql/st_lineinterpolatepoint.qmd:19`
- last error: AssertionError: Expected POINT (5 5), got POINT(5 5)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected POINT (5 5), got POINT(5 5)

### `sql:ST_LineMerge` — runtime

- canonical source: `source/docs/reference/sql/st_linemerge.qmd:19`
- last error: AssertionError: Expected merged LineString, got LINESTRING(0 0,1 0,1 1)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected merged LineString, got LINESTRING(0 0,1 0,1 1)

### `sql:ST_LineStringFromWKB` — runtime

- canonical source: `source/docs/reference/sql/st_linestringfromwkb.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_LineSubstring` — runtime

- canonical source: `source/docs/reference/sql/st_linesubstring.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_MLineFromText` — runtime

- canonical source: `source/docs/reference/sql/st_mlinefromtext.qmd:19`
- last error: TypeError: a bytes-like object is required, not 'str'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: a bytes-like object is required, not 'str'

### `sql:ST_MPointFromText` — runtime

- canonical source: `source/docs/reference/sql/st_mpointfromtext.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

_… 37 more failing APIs omitted (--max-api-detail to raise)._
