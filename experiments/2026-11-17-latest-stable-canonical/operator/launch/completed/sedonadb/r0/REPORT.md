# Fix-loop report — result

_Generated 2026-11-17 17:28 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-011545Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **78/217** raw (35.9%)  ·  scored **78/217** (35.9%) after excluding 0 infra
- wall 0.21 h  ·  tokens in 1,230,325 / out 56,067 ·  llm calls 217  ·  max_fix_rounds 0
- pass-by-round: r0:78  ·  **0 rescued by the fix loop** (pass@0 = 78)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **56x** [unknown] args), self, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: Error during planning: Inv
  - `sql:RS_AsGeoTiff`, `sql:RS_BandNoDataValue`, `sql:RS_BandPixelType`, `sql:RS_BandToDim`, `sql:RS_CRS`, `sql:RS_Clip`, `sql:RS_Contains`, `sql:RS_ConvexHull`, `sql:RS_DimNames`, `sql:RS_DimSize`, `sql:RS_DimToBand`, `sql:RS_Envelope`, `sql:RS_GeoReference`, `sql:RS_GeoTransform` …
- **43x** [runtime] AssertionError
  - `sql:S2_CellIdFromPoint`, `sql:ST_Affine`, `sql:ST_AsEWKB`, `sql:ST_AsText`, `sql:ST_BuildArea`, `sql:ST_Centroid`, `sql:ST_ConvexHull`, `sql:ST_DelaunayTriangles`, `sql:ST_EndPoint`, `sql:ST_Envelope`, `sql:ST_Force2D`, `sql:ST_Force3D`, `sql:ST_Force3DM`, `sql:ST_GeogFromWKT` …
- **4x** [runtime] TypeError: a bytes-like object is required, not <name>
  - `sql:ST_Collect_Agg`, `sql:ST_Envelope_Agg`, `sql:ST_GeomCollFromText`, `sql:ST_TessellateGeom`
- **4x** [runtime] AssertionError: Expected POINT (1 2), got POINT(1 2)
  - `sql:ST_GeomFromEWKB`, `sql:ST_PointFromWKB`, `sql:ST_PointN`, `sql:st_geomfromwkbunchecked`
- **1x** [runtime] AttributeError: <name> object has no attribute <name>
  - `sql:RS_BandIsNoData`
- **1x** [unknown] self, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: Error during planning: Invalid fu
  - `sql:RS_BandPath`
- **1x** [unknown] f._context.sql(query, **kwargs), self, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError:
  - `sql:rs_ensureloaded`
- **1x** [runtime] AssertionError: Expected width 4, got 10
  - `sql:RS_FromGDALRaster`
- **1x** [runtime] AssertionError: Expected gridHeight <num>, got <num>
  - `sql:RS_MetaData`
- **1x** [unknown] **kwargs), self, File "<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: Error during planning:
  - `sql:RS_NumDimensions`
- **1x** [unknown] e<path>", line <n>, in sql df = DataFrame(self, self._impl.sql(sql)) sedonadb._lib.SedonaError: rs_makeemptyraster(int64, int64, int64, int6
  - `sql:RS_SetValue`
- **1x** [runtime] AssertionError: Expected 2 bands after slicing, but got 1
  - `sql:RS_SliceRange`

## Why each API fails (139 failing)

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

### `sql:RS_BandIsNoData` — runtime

- canonical source: `source/docs/reference/sql/rs_bandisnodata.qmd:19`
- last error: AttributeError: 'TrackedContext' object has no attribute 'read_raster'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TrackedContext' object has no attribute 'read_raster'

### `sql:RS_BandNoDataValue` — unknown

- canonical source: `source/docs/reference/sql/rs_bandnodatavalue.qmd:19`
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

### `sql:RS_BandPath` — unknown

- canonical source: `source/docs/reference/sql/rs_bandpath.qmd:19`
- last error: self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Error during planning: Invalid function 'st_fromgeoraster'.
Did you mean 'rs_fromgdalraster'?
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFra

### `sql:RS_BandPixelType` — unknown

- canonical source: `source/docs/reference/sql/rs_bandpixeltype.qmd:19`
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

### `sql:RS_CRS` — unknown

- canonical source: `source/docs/reference/sql/rs_crs.qmd:19`
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

### `sql:RS_ConvexHull` — unknown

- canonical source: `source/docs/reference/sql/rs_convexhull.qmd:19`
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

### `sql:RS_DimNames` — unknown

- canonical source: `source/docs/reference/sql/rs_dimnames.qmd:19`
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

### `sql:RS_DimSize` — unknown

- canonical source: `source/docs/reference/sql/rs_dimsize.qmd:19`
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

### `sql:RS_Envelope` — unknown

- canonical source: `source/docs/reference/sql/rs_envelope.qmd:19`
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

### `sql:RS_FromGDALRaster` — runtime

- canonical source: `source/docs/reference/sql/rs_fromgdalraster.qmd:19`
- last error: AssertionError: Expected width 4, got 10
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected width 4, got 10

### `sql:RS_GeoReference` — unknown

- canonical source: `source/docs/reference/sql/rs_georeference.qmd:19`
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

### `sql:RS_GeoTransform` — unknown

- canonical source: `source/docs/reference/sql/rs_geotransform.qmd:19`
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

### `sql:RS_Height` — unknown

- canonical source: `source/docs/reference/sql/rs_height.qmd:19`
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

### `sql:RS_Intersects` — unknown

- canonical source: `source/docs/reference/sql/rs_intersects.qmd:19`
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

### `sql:RS_MetaData` — runtime

- canonical source: `source/docs/reference/sql/rs_metadata.qmd:19`
- last error: AssertionError: Expected gridHeight 514, got 515
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected gridHeight 514, got 515

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

### `sql:RS_NumBands` — unknown

- canonical source: `source/docs/reference/sql/rs_numbands.qmd:19`
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

### `sql:RS_NumDimensions` — unknown

- canonical source: `source/docs/reference/sql/rs_numdimensions.qmd:19`
- last error: **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Error during planning: Invalid function 'read_binary'.
Did you mean 'st_asbinary'?
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] **kwargs), self,
  File "/home/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    d

### `sql:RS_PixelAsCentroid` — unknown

- canonical source: `source/docs/reference/sql/rs_pixelascentroid.qmd:19`
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

### `sql:RS_PixelAsPoint` — unknown

- canonical source: `source/docs/reference/sql/rs_pixelaspoint.qmd:19`
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

### `sql:RS_Polygonize` — unknown

- canonical source: `source/docs/reference/sql/rs_polygonize.qmd:19`
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

### `sql:RS_RasterToWorldCoord` — unknown

- canonical source: `source/docs/reference/sql/rs_rastertoworldcoord.qmd:19`
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

### `sql:RS_RasterToWorldCoordX` — unknown

- canonical source: `source/docs/reference/sql/rs_rastertoworldcoordx.qmd:19`
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

### `sql:RS_RasterToWorldCoordY` — unknown

- canonical source: `source/docs/reference/sql/rs_rastertoworldcoordy.qmd:19`
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

### `sql:RS_Rotation` — unknown

- canonical source: `source/docs/reference/sql/rs_rotation.qmd:19`
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

### `sql:RS_ScaleX` — unknown

- canonical source: `source/docs/reference/sql/rs_scalex.qmd:19`
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

### `sql:RS_ScaleY` — unknown

- canonical source: `source/docs/reference/sql/rs_scaley.qmd:19`
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

### `sql:RS_SetBandNoDataValue` — unknown

- canonical source: `source/docs/reference/sql/rs_setbandnodatavalue.qmd:19`
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

### `sql:RS_SetSRID` — unknown

- canonical source: `source/docs/reference/sql/rs_setsrid.qmd:19`
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
- last error: e/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: rs_makeemptyraster(int64, int64, int64, int64, int64, int64, int64, int64, int64): No kernel matching arguments
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] e/zshan011/apps/aideal/envs/2026-11-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._imp

### `sql:RS_Shape` — unknown

- canonical source: `source/docs/reference/sql/rs_shape.qmd:19`
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

### `sql:RS_SkewX` — unknown

- canonical source: `source/docs/reference/sql/rs_skewx.qmd:19`
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

### `sql:RS_SkewY` — unknown

- canonical source: `source/docs/reference/sql/rs_skewy.qmd:19`
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

### `sql:RS_SliceRange` — runtime

- canonical source: `source/docs/reference/sql/rs_slicerange.qmd:19`
- last error: AssertionError: Expected 2 bands after slicing, but got 1
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected 2 bands after slicing, but got 1

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

### `sql:RS_UpperLeftX` — unknown

- canonical source: `source/docs/reference/sql/rs_upperleftx.qmd:19`
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

### `sql:RS_UpperLeftY` — unknown

- canonical source: `source/docs/reference/sql/rs_upperlefty.qmd:19`
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

### `sql:RS_Value` — unknown

- canonical source: `source/docs/reference/sql/rs_value.qmd:19`
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

### `sql:RS_Width` — unknown

- canonical source: `source/docs/reference/sql/rs_width.qmd:19`
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

### `sql:RS_Within` — unknown

- canonical source: `source/docs/reference/sql/rs_within.qmd:19`
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

### `sql:RS_WorldToRasterCoordX` — unknown

- canonical source: `source/docs/reference/sql/rs_worldtorastercoordx.qmd:19`
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

### `sql:S2_CellIdFromPoint` — runtime

- canonical source: `source/docs/reference/sql/s2_cellidfrompoint.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:S2_CoveringCellIds` — runtime

- canonical source: `source/docs/reference/sql/s2_coveringcellids.qmd:19`
- last error: AssertionError: Expected at most 16 cells, got 30
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected at most 16 cells, got 30

### `sql:SD_Format` — runtime

- canonical source: `source/docs/reference/sql/sd_format.qmd:19`
- last error: AssertionError: Expected coordinates in formatted string, got: POINT(1 2)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected coordinates in formatted string, got: POINT(1 2)

### `sql:ST_Affine` — runtime

- canonical source: `source/docs/reference/sql/st_affine.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_AsEWKB` — runtime

- canonical source: `source/docs/reference/sql/st_asewkb.qmd:19`
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

### `sql:ST_BuildArea` — runtime

- canonical source: `source/docs/reference/sql/st_buildarea.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_CRS` — runtime

- canonical source: `source/docs/reference/sql/st_crs.qmd:19`
- last error: AssertionError: Expected EPSG:4326, got OGC:CRS84
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected EPSG:4326, got OGC:CRS84

### `sql:ST_Centroid` — runtime

- canonical source: `source/docs/reference/sql/st_centroid.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

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

### `sql:ST_Collect_Agg` — runtime

- canonical source: `source/docs/reference/sql/st_collect_agg.qmd:19`
- last error: TypeError: a bytes-like object is required, not 'str'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: a bytes-like object is required, not 'str'

### `sql:ST_ConvexHull` — runtime

- canonical source: `source/docs/reference/sql/st_convexhull.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_DelaunayTriangles` — runtime

- canonical source: `source/docs/reference/sql/st_delaunaytriangles.qmd:19`
- last error: AssertionError
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError

### `sql:ST_Dump` — unknown

- canonical source: `source/docs/reference/sql/st_dump.qmd:19`
- last error: 1-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaError: Dot access not supported for non-string expr: Identifier(Ident { value: "geom", quote_style: None, span: Span(Location(3,97)..Location(3,101)) })
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [unknown] 1-16-sedonadb/lib/python3.10/site-packages/sedonadb/context.py", line 424, in sql
    df = DataFrame(self, self._impl.sql(sql))
sedonadb._lib.SedonaEr

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
- last error: TypeError: a bytes-like object is required, not 'str'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: a bytes-like object is required, not 'str'

_… 59 more failing APIs omitted (--max-api-detail to raise)._
