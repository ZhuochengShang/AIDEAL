# Recorded author system prompt

You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

Role: A Python developer using SedonaDB SQL for geospatial computation.
Project: SedonaDB 0.5.0 registered SQL operations (Python and SQL) - Official SedonaDB 0.5.0 SQL scalar and aggregate operations called through its Python SQL connection. Targets are public SQL names and their documented call patterns; runtime user-defined signatures are not assigned a finite maximum arity.
Domain: Geospatial vector and raster analysis
Target users: Python developers using SedonaDB SQL
Use cases: Run small SQL queries and verify materialized geometry, raster, scalar, and aggregate results.
Constraints: Use the original SQL API and original documentation only.; Write Python statements using sd.sql(query).to_arrow_table(); assert known documented results and print the __CHECK__ witness.; Use tiny literal inputs or the supplied local raster files. No remote datasets or services.

# Recorded author user prompt

Document the Python and SQL function `sql:ST_Point` of SedonaDB 0.5.0 registered SQL operations.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{
  "name": "sql:ST_Point",
  "signature": "ST_Point(x: double, y: double, srid: crs) -> geometry",
  "params": [
    {
      "name": "x",
      "type": "double"
    },
    {
      "name": "y",
      "type": "double"
    },
    {
      "name": "srid",
      "type": "crs"
    }
  ],
  "returns": "geometry",
  "source_doc": "---\n# Licensed to the Apache Software Foundation (ASF) under one\n# or more contributor license agreements.  See the NOTICE file\n# distributed with this work for additional information\n# regarding copyright ownership.  The ASF licenses this file\n# to you under the Apache License, Version 2.0 (the\n# \"License\"); you may not use this file except in compliance\n# with the License.  You may obtain a copy of the License at\n#\n#   http://www.apache.org/licenses/LICENSE-2.0\n#\n# Unless required by applicable law or agreed to in writing,\n# software distributed under the License is distributed on an\n# \"AS IS\" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY\n# KIND, either express or implied.  See the License for the\n# specific language governing permissions and limitations\n# under the License.\n\ntitle: ST_Point\ndescription: Constructs a Point Geometry from X and Y.\nkernels:\n  - returns: geometry\n    args:\n    - name: x\n      type: double\n    - name: \"y\"\n      type: double\n    - name: srid\n      type: crs\n---\n\n## Description\n\nConstructs a Point geometry from X and Y coordinates. An optional SRID or CRS can be provided as a third argument.\n\n## Examples\n\n```sql\nSELECT ST_AsText(ST_Point(-74.0060, 40.7128));\n```\n\nWith an SRID:\n\n```sql\nSELECT ST_Point(-74.0060, 40.7128, 4326);\n```\n\nWith a CRS:\n\n```sql\nSELECT ST_Point(-74.0060, 40.7128, 'EPSG:3857');\n```\n",
  "overloads": [],
  "api_id": "sql:ST_Point",
  "display_name": "ST_Point",
  "identity_version": "language_qualified_api_v1",
  "parameter_count": null,
  "parameter_count_status": "user_defined_runtime_signature",
  "qualified_name": "ST_Point",
  "source": {
    "file": "source/docs/reference/sql/st_point.qmd",
    "line": 19,
    "site_id": "SQL:st_point",
    "file_sha256": "e8a3d4cd6a29e00351566deb0bd0baa92c92673525de6267e7559f5eb1ede054"
  },
  "definition_sites": [
    {
      "signature": "ST_Point(x: double, y: double, srid: crs) -> geometry",
      "qualified_name": "ST_Point",
      "source": {
        "file": "source/docs/reference/sql/st_point.qmd",
        "line": 19,
        "site_id": "SQL:st_point",
        "file_sha256": "e8a3d4cd6a29e00351566deb0bd0baa92c92673525de6267e7559f5eb1ede054"
      }
    }
  ],
  "definition_site_count": 1,
  "definition_sites_truncated": false,
  "overloads_total": 0,
  "overloads_truncated": false
}
```

Project context distilled from the original README (grounding — may say none exists):
===== Original documentation part 1/3 =====
### 1. Project purpose
SedonaDB 0.5.0 provides a suite of SQL-based geospatial operations for vector and raster data. It enables users to perform raster-to-vector conversions, raster metadata inspection, grid-based resampling, and spatial analysis (zonal statistics, intersection, containment) within a SQL environment. The project is designed for high-performance geospatial computation, supporting both in-database and out-of-database raster workflows.

### 2. Main workflows
*   **Raster Creation & Loading:** Creating empty grids (`RS_MakeEmptyRaster`), loading from file paths (`RS_FromPath`), or decoding binary content (`RS_FromGDALRaster`).
*   **Raster-Geometry Interaction:** Rasterizing geometries (`RS_AsRaster`), clipping rasters to geometries (`RS_Clip`), and computing zonal statistics (`RS_ZonalStats`).
*   **Raster Transformation:** Resampling grids (`RS_Resample`), reprojecting to match a reference (`RS_ReprojectMatch`), and stacking bands (`RS_Stack`).
*   **Metadata & Inspection:** Querying CRS, geotransforms, dimensions, and band statistics (`RS_MetaData`, `RS_SummaryStats`, `RS_DimSize`).
*   **Vectorization:** Converting raster bands to polygons (`RS_Polygonize`) or extracting pixel values at specific points (`RS_Value`).

### 3. Important APIs and usage patterns
*   **Raster Accessors:** `RS_Width`, `RS_Height`, `RS_NumBands`, `RS_CRS`, `RS_SRID`, `RS_GeoReference`.
*   **Band Operations:** `RS_BandIsNoData`, `RS_BandNoDataValue`, `RS_BandPixelType`, `RS_SetBandNoDataValue`.
*   **Dimension Management:** `RS_BandToDim`, `RS_DimToBand`, `RS_Slice`, `RS_SliceRange`.
*   **Spatial Predicates:** `RS_Intersects`, `RS_Contains`, `RS_Within`.
*   **Coordinate Conversion:** `RS_RasterToWorldCoord`, `RS_WorldToRasterCoord`.

### 4. Inputs and file formats
*   **Raster Inputs:** Supports GDAL-readable formats (GeoTIFF, PNG, etc.).
*   **Geometry Inputs:** Standard OGC WKT/WKB geometries.
*   **Data Types:** Pixel types include `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64`, `float32`, `float64`.
*   **Configuration:** CRS is represented as strings (e.g., 'EPSG:4326').

### 5. Outputs and generated artifacts
*   **Raster:** In-database raster objects.
*   **Geometry:** Points, Polygons, or Envelopes.
*   **Scalar/Aggregate:** `double`, `bigint`, `boolean`, or `struct` (for metadata/stats).
*   **Binary:** GeoTIFF byte streams via `RS_AsGeoTiff`.

### 6. Configuration and environment assumptions
*   **Experimental Status:** Many raster functions (e.g., `RS_Clip`, `RS_Resample`, `RS_ReprojectMatch`) are marked as experimental and subject to change.
*   **CRS Consistency:** Operations like `RS_ReprojectMatch` and `RS_Clip` require consistent CRS handling; errors occur if exactly one input has a CRS.
*   **Memory:** Functions like `RS_ReprojectMatch` and `RS_Resample` (with extent-growing) load the entire raster into memory.

### 7. Commands and examples
**Rasterization:**
```sql
SELECT RS_Width(
  RS_AsRaster(
    RS_ConvexHull(raster),
    raster,
    'float64',
    false,
    1.0,
    0.0,
    false
  )
)
FROM (SELECT RS_FromPath('https://download.osgeo.org/geotiff/samples/gdal_eg/cea.tif') AS raster) r;
```

**Clipping:**
```sql
SELECT RS_Width(
  RS_Clip(
    RS_Example(),
    1,
    ST_GeomFromText('POLYGON ((60 90, 160 90, 160 190, 60 190, 60 90))', 'OGC:CRS84')
  )
);
```

**Resampling:**
```sql
SELECT RS_Width(RS_Resample(RS_Example(), 32, 16, false, 'NearestNeighbor'));
```

**Zonal Statistics:**
```sql
SELECT RS_ZonalStats(
  RS_Example(),
  ST_GeomFromText('POLYGON ((60 90, 160 90, 160 190, 60 190, 60 90))', 'OGC:CRS84'),
  1,
  'mean'
);
```

### 8. Constraints, preconditions, compatibility rules, and type-selection rules
*   **Integer Constraints:** `Int64` and `UInt64` rasters are not supported by `RS_ReprojectMatch` (must cast to `Int32` or `Float64` first).
*   **Band Indexing:** Band indices are 1-based.
*   **Coordinate Systems:** If CRS differs, geometries are reprojected to the raster's CRS. If only one side has a CRS, the operation fails.
*   **Tile Dimensions:** TIFF tile dimensions must be multiples of 16.
*   **Dimension Names:** New dimension names in `RS_BandToDim` must not already exist.

### 9. Facts to preserve in the final README
*   `RS_AsGeoTiff` returns binary bytes.
*   `RS_MakeEmptyRaster` supports 0 bands for template grids.
*   `RS_Tile` materializes a full copy of the raster in memory.
*   `RS_SummaryStats` and `RS_ZonalStats` support `count`, `sum`, `mean`, `stddev`, `min`, `max`.
*   `RS_Value` and `RS_Values` perform no resampling (nearest-pixel sampling).

### 10. Missing or weak documentation
*   Specific memory limits for "in-database" rasters are not explicitly defined beyond the 4 GiB per-band limit.
*   The exact behavior of "preferred transformation" fallback to WGS 84 in `RS_Intersects` is not detailed.
*   The "session's geography bounder" mentioned in `RS_MakeEmptyRaster` is not documented in the provided snippets.

===== Original documentation part 2/3 =====
### 1. Project purpose
SedonaDB 0.5.0 provides a suite of SQL-based geospatial operations for vector and raster analysis. It enables users to perform geometric computations, spatial predicates, and aggregations on `geometry` and `geography` types within a SQL environment, accessible via Python using `sedonadb.connect()`.

### 2. Main workflows
*   **Data Construction:** Creating geometries/geographies from WKT, WKB, or coordinate primitives (e.g., `ST_Point`, `ST_GeomFromWKT`).
*   **Spatial Analysis:** Computing relationships (e.g., `ST_Contains`, `ST_Intersects`, `ST_DWithin`) and measurements (e.g., `ST_Area`, `ST_Length`, `ST_Distance`).
*   **Geometry Processing:** Modifying or deriving new geometries (e.g., `ST_Buffer`, `ST_Intersection`, `ST_ConvexHull`, `ST_MakeValid`).
*   **Aggregation:** Performing group-wise spatial operations (e.g., `ST_Collect_Agg`, `ST_ConvexHull_Agg`, `ST_Envelope_Agg`).
*   **Coordinate/Dimension Management:** Handling Z/M dimensions (`ST_Force3D`, `ST_Force4D`) and CRS metadata (`ST_CRS`).

### 3. Important APIs and usage patterns
*   **Connection:** `sd = sedonadb.connect()`
*   **Execution:** `sd.sql(query).to_arrow_table()` or `.to_pandas()`.
*   **Views:** Use `.to_view("name")` to register intermediate results for subsequent SQL joins or complex queries.
*   **Naming Conventions:** Most functions follow the OGC standard (e.g., `ST_Area`, `ST_Buffer`). Aliases exist for common functions (e.g., `ST_AsWKT` for `ST_AsText`, `ST_NumInteriorRing` for `ST_NumInteriorRings`).
*   **Aggregate Functions:** Suffix `_Agg` denotes aggregate operations (e.g., `ST_ConvexHull_Agg`).

### 4. Inputs and file formats
*   **Formats:** Well-Known Text (WKT), Well-Known Binary (WKB), Extended WKT (EWKT), and Extended WKB (EWKB).
*   **Types:** `geometry` (planar) and `geography` (spherical).
*   **Primitives:** `double` (coordinates, distances, fractions), `integer` (indices, precision, SRIDs), `string` (WKT, parameters), `binary` (WKB).

### 5. Outputs and generated artifacts
*   **Scalars:** `double`, `integer`, `boolean`, `string`, `binary`.
*   **Geospatial:** `geometry` or `geography` objects.
*   **Structures:** `ST_Dump` returns a `struct` containing expanded geometry parts.

### 6. Configuration and environment assumptions
*   **CRS:** GeoHash operations require WGS84 (`EPSG:4326` / `OGC:CRS84`) or no CRS.
*   **Geography:** Geography operations require the `s2geography` bounder to be registered on the session.
*   **Storage:** `ST_AsBinary` may preserve Arrow `BinaryView` storage; use `sd_simplifystorage()` if standard `Binary` is required.

### 7. Commands and examples
**Basic Geometry Creation:**
```sql
SELECT ST_Point(-74.0060, 40.7128, 4326);
```

**Spatial Predicate:**
```sql
SELECT ST_Contains(
    ST_GeomFromText('POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))'),
    ST_Point(0.25, 0.25)
) AS val;
```

**Buffer with Parameters:**
```sql
SELECT ST_Buffer(
  ST_GeomFromText('POLYGON ((10 10, 11 10, 10 11, 10 10))'),
  1.0,
  'quad_segs=2'
) AS geom;
```

**Aggregate Operation:**
```sql
SELECT ST_ConvexHull_Agg(geom) FROM (
    VALUES
        (ST_Point(0, 0)),
        (ST_Point(0, 1)),
        (ST_Point(1, 0)),
        (ST_Point(1, 1))
) AS t(geom);
```

**Python Integration:**
```python
import sedonadb
sd = sedonadb.connect()
sd.sql("SELECT ST_Point(1.0, 2.0) as geom").to_view("input")
df = sd.sql("SELECT ST_AsText(geom) as wkt FROM input").to_pandas()
```

### 8. Constraints, preconditions, compatibility rules, and type-selection rules
*   **Geography vs. Geometry:** `ST_Area` for geometry returns units of the CRS; for geography, it returns square meters.
*   **Dimension Handling:** `ST_Force3D` and `ST_Force4D` preserve existing Z/M values if present; otherwise, they default to 0.
*   **Validation:** `ST_IsValid` checks OGC compliance; `ST_MakeValid` repairs invalid geometries.
*   **GeoHash:** Precision is capped at 20 characters. Non-positive precision returns an empty string.
*   **Index:** `ST_GeometryN` and `ST_InteriorRingN` use 1-based indexing.

### 9. Facts to preserve in the final README
*   SedonaDB 0.5.0 supports both planar `geometry` and spherical `geography` types.
*   Aggregate functions are explicitly marked with `_Agg`.
*   The library supports PostGIS-compatible EWKT/EWKB formats.
*   Python interaction is primarily through `sd.sql(...).to_arrow_table()`.

### 10. Missing or weak documentation
*   The documentation for `ST_ReducePrecision` is truncated in the provided source.
*   Specific details on the `sd_simplifystorage()` function are limited to a mention in `ST_AsBinary`.
*   The exact list of supported `params` strings for `ST_Buffer` is referenced as "identical to PostGIS" but not explicitly enumerated.

===== Original documentation part 3/3 =====
### 1. Project purpose
SedonaDB is an open-source, single-node analytical database engine designed for high-performance geospatial computation. It treats spatial data as a first-class citizen, providing comprehensive support for vector and (forthcoming) raster analysis. It is built on Rust, leveraging Apache Arrow and Apache DataFusion for in-memory columnar processing, spatial indexing, and efficient query optimization.

### 2. Main workflows
* **Connection:** Initialize a session using `sedona.db.connect()`.
* **Data Loading:** Load datasets (e.g., Parquet) into a `DataFrame` and register them as SQL views using `df.to_view("name")`.
* **Query Execution:** Execute spatial SQL queries via `sd.sql("...").to_arrow_table()`.
* **Spatial Analysis:** Perform range queries, KNN, spatial joins, and coordinate transformations using the provided `ST_*` SQL function library.

### 3. Important APIs and usage patterns
* **Connection:** `sd = sedona.db.connect()`
* **Execution:** `sd.sql(query).to_arrow_table()`
* **Metadata/CRS:** Functions like `ST_SetCRS`, `ST_SetSRID`, and `ST_Transform` manage spatial reference systems.
* **Geometry Manipulation:** Operations include `ST_ReducePrecision`, `ST_Reverse`, `ST_Rotate`, `ST_Scale`, `ST_Segmentize`, `ST_Simplify`, `ST_Snap`, `ST_Translate`, and `ST_UnaryUnion`.
* **Predicates:** `ST_Relate`, `ST_Touches`, `ST_Within`.
* **Accessors:** `ST_X`, `ST_Y`, `ST_Z`, `ST_XMin`, `ST_XMax`, `ST_YMin`, `ST_YMax`, `ST_ZMin`, `ST_ZMax`, `ST_SRID`, `ST_Zmflag`, `ST_StartPoint`.

### 4. Inputs and file formats
* **Vector:** GeoParquet, WKT, WKB, and formats supported by GeoPandas.
* **Raster:** Support is planned (compatible with SedonaSpark).
* **CRS:** Accepts authority codes (e.g., `'EPSG:4326'`), PROJJSON, or WKT.

### 5. Outputs and generated artifacts
* Results are returned as PyArrow tables.
* Spatial operations return `geometry` or `geography` types, or scalar values (double, integer, boolean, string) depending on the function.

### 6. Configuration and environment assumptions
* Designed for single-node local or cloud instances.
* Assumes availability of PyArrow-compatible environments.
* Metadata-only operations (e.g., `ST_SetCRS`, `ST_ToGeography`) do not modify underlying coordinate data.

### 7. Commands and examples
**Reduce Precision:**
```sql
SELECT ST_ReducePrecision(
    ST_GeogFromWKT('POINT (1.123456 2.654321)'),
    0.01
);
```

**Relate (DE-9IM):**
```sql
SELECT ST_Relate(
    ST_GeomFromText('POINT (0.5 0.5)'),
    ST_GeomFromText('POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))'),
    '0FFFFF212'
);
```

**Simplify:**
```sql
SELECT ST_Simplify(
    ST_GeomFromWKT('LINESTRING (0 0, 0.5 0.1, 1 0, 1.5 0.1, 2 0)'),
    0.2
);
```

**Transform:**
```sql
SELECT ST_Transform(ST_SetCRS(ST_Point(-122.35, 47.65), 'EPSG:4326'), 'EPSG:26910');
```

**Union Aggregate:**
```sql
SELECT ST_Union_Agg(geom) FROM (
  VALUES
    (ST_GeomFromText('POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))')),
    (ST_GeomFromText('POLYGON ((1 1, 1 3, 3 3, 3 1, 1 1))'))
) AS t(geom);
```

### 8. Constraints, preconditions, compatibility rules, and type-selection rules
* **Geography vs. Geometry:** Many functions have separate kernels for `geometry` (planar) and `geography` (spherical).
* **Transformation:** `ST_Transform` requires target CRS to be geographic if the input is `geography`.
* **Validity:** `ST_Simplify` may produce invalid geometries; use `ST_SimplifyPreserveTopology` for validity guarantees.
* **Metadata:** `ST_SetCRS` and `ST_SetSRID` are metadata-only; they do not reproject coordinates.
* **Antimeridian:** `ST_TessellateGeom` handles antimeridian crossing by wrapping coordinates, but fails for polygons spanning the full longitude range (e.g., Antarctica).

### 9. Facts to preserve in the final README
* SedonaDB is a single-node engine built in Rust.
* It provides dual Python and SQL APIs.
* It maintains CRS propagation throughout operations.
* It is interoperable with the broader PyArrow ecosystem (DuckDB, Polars, GeoPandas).

### 10. Missing or weak documentation
* Specifics on the "Raster" function API are currently missing (marked as "coming soon").
* The exact list of supported EPSG codes or PROJ string validation rules is not explicitly detailed beyond general references to CRS concepts.
* Documentation for `ST_Zmflag` return codes is clear, but the behavior for mixed-dimension collections is not explicitly defined.

Real usage from the project's existing test suite (these compile and pass — base
the Valid Call Patterns and realistic Common Failure Modes on them; may be empty):
```Python and SQL
(no existing test found for this API)
```

Verbatim code example(s) from the ORIGINAL project README that call `sql:ST_Point`
(the project's real, documented usage — may be empty):
```Python and SQL
===== Shared original document: README.md =====
<!---
  Licensed to the Apache Software Foundation (ASF) under one
  or more contributor license agreements.  See the NOTICE file
  distributed with this work for additional information
  regarding copyright ownership.  The ASF licenses this file
  to you under the Apache License, Version 2.0 (the
  "License"); you may not use this file except in compliance
  with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing,
  software distributed under the License is distributed on an
  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
  KIND, either express or implied.  See the License for the
  specific language governing permissions and limitations
  under the License.
-->

# SedonaDB

[![PyPI Version](https://img.shields.io/pypi/v/sedonadb)](https://pypi.org/project/sedonadb/) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/sedonadb?period=monthly&units=NONE&left_color=BLACK&right_color=GREEN&left_text=downloads%2Fmonth)](https://pepy.tech/projects/sedonadb) [![Downloads](https://static.pepy.tech/personalized-badge/sedonadb?period=total&units=international_system&left_color=black&right_color=brightgreen&left_text=total%20downloads)](https://pepy.tech/project/sedonadb)
[![Anaconda Version](
https://anaconda.org/conda-forge/sedonadb/badges/version.svg)](https://anaconda.org/conda-forge/sedonadb) [![Conda Downloads](https://anaconda.org/conda-forge/sedonadb/badges/downloads.svg)](https://anaconda.org/channels/conda-forge/packages/sedonadb/overview)
[![R-multiverse
status](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fcommunity.r-multiverse.org%2Fapi%2Fpackages%2Fsedonadb&query=%24.Version&label=r-multiverse)](https://community.r-multiverse.org/sedonadb)

SedonaDB is an open-source single-node analytical database engine with **geospatial as a first-class citizen**. It aims to deliver the fastest spatial analytics query speed and the most comprehensive function coverage available.

SedonaDB is perfect for processing smaller to medium datasets on local machines or cloud instances. For distributed workloads, you can leverage the power of SedonaSpark, SedonaFlink, or SedonaSnow.

## Architecture

![SedonaDB Architecture](https://raw.githubusercontent.com/apache/sedona-db/refs/heads/main/docs/image/sedonadb-architecture.svg)

* **Columnar in-memory datasets**
    * Spatial indexing
    * Spatial statistics
    * CRS tracking
    * Arrow format and zero serialization overhead

* **Spatial query optimization**
    * Spatial-aware heuristic based optimization
    * Spatial-aware cost based optimization
    * Automatic disk spilling for large-scale spatial joins

* **Spatial query processing**
    * Spatial range query, KNN query, spatial join query, KNN join query
    * Map algebra, NDVI, mask, zonal statistics

Raster functions are coming soon. We expect SedonaDB Raster will match all raster functions provided in [SedonaSpark](https://sedona.apache.org/latest/api/sql/Raster-operators/).

## Features of SedonaDB

SedonaDB has several advantages:

* **High Performance:** Built in Rust for exceptional speed and memory efficiency
* **Comprehensive Spatial Toolkit:** Supports both vector and raster functions in a single library
* **CRS Propagation:** Always maintains coordinate reference system information
* **Format Flexibility:** Supports legacy and modern file formats including GeoParquet, Shapefile, GeoJSON
* **Dual APIs:** Python and SQL interfaces for seamless workflow integration
* **Extensible:** Easily customizable and extensible architecture
* **Ecosystem Integration:** Interoperable with PyArrow-compatible libraries like GeoPandas, DuckDB, and Polars
* **Active Community:** Great maintainers and contributors who encourage external contributions

## Performance Benchmarks

This is a performance benchmark comparing SedonaDB 0.1.0, DuckDB 1.4.0, and GeoPandas 1.1.1 using SpatialBench Queries 1-12 at Scale Factors 1 and 10. Details can be found at [Apache Sedona SpatialBench](https://sedona.apache.org/spatialbench/single-node-benchmarks/).

<div align="center">
  <img src="https://raw.githubusercontent.com/apache/sedona-db/refs/heads/main/docs/image/sf1-09242025.png" alt="SF1 Benchmark Results" width="45%" />
  <img src="https://raw.githubusercontent.com/apache/sedona-db/refs/heads/main/docs/image/sf10-09242025.png" alt="SF10 Benchmark Results" width="45%" />
</div>

## Install

You can install Python SedonaDB with [PyPI](https://packaging.python.org/en/latest/tutorials/installing-packages/):

```sh
pip install "apache-sedona[db]"
```

Or with [conda](https://www.anaconda.com/docs/getting-started/main):

```sh
conda install sedonadb
```

## Quick Start

Get started with SedonaDB in just a few lines:

```python
import sedona.db

# Connect to SedonaDB
sd = sedona.db.connect()

# Run a simple spatial query
result = sd.sql("SELECT ST_Point(0, 1) as geom")
result.show()
```

### Supported File Formats

SedonaDB supports a wide range of geospatial file formats:

- **Vector:** GeoParquet, WKT, WKB, all formats supported by GeoPandas
- **Raster:** Coming soon with full SedonaSpark compatibility

## Overture buildings example

This section shows how to query the Overture buildings data.

Start by establishing a connection:

```python
import sedona.db

sd = sedona.db.connect()
```

Read the dataset into a Python SedonaDB `DataFrame`. This is lazy: even though the Overture buildings table contains millions of rows, SedonaDB will only fetch the data required for the query.

```python
df = sd.read_parquet(
    "s3://overturemaps-us-west-2/release/2026-02-18.0/theme=buildings/type=building/",
    options={"aws.skip_signature": True, "aws.region": "us-west-2"},
)
df.to_view("buildings")
```

Now run a query to compute the centroids of tall buildings (above 20 meters) in New York City:

```python
nyc_bbox_wkt = (
    "POLYGON((-74.2591 40.4774, -74.2591 40.9176, -73.7004 40.9176, -73.7004 40.4774, -74.2591 40.4774))"
)

sd.sql(f"""
SELECT
    id,
    height,
    num_floors,
    roof_shape,
    ST_Centroid(geometry) as centroid
FROM
    buildings
WHERE
    is_underground = FALSE
    AND height IS NOT NULL
    AND height > 20
    AND ST_Intersects(geometry, ST_GeomFromText('{nyc_bbox_wkt}', 4326))
LIMIT 5;
""").show()
```

Here's the query output:

```
┌─────────────────────────┬────────────────────┬────────────┬────────────┬─────────────────────────┐
│            id           ┆       height       ┆ num_floors ┆ roof_shape ┆         centroid        │
│           utf8          ┆       float64      ┆    int32   ┆    utf8    ┆         geometry        │
╞═════════════════════════╪════════════════════╪════════════╪════════════╪═════════════════════════╡
│ 1b9040c2-2e79-4f56-aba… ┆               22.4 ┆            ┆            ┆ POINT(-74.230407502993… │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ 1b5e1cd2-d697-489e-892… ┆               21.5 ┆            ┆            ┆ POINT(-74.231451103592… │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ c1afdf78-bf84-4b8f-ae1… ┆               20.9 ┆            ┆            ┆ POINT(-74.232593032240… │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ 88f36399-b09f-491b-bb6… ┆               24.5 ┆            ┆            ┆ POINT(-74.231878209597… │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ df37a283-f5bd-4822-a05… ┆ 24.154542922973633 ┆            ┆            ┆ POINT(-74.241910239840… │
└─────────────────────────┴────────────────────┴────────────┴────────────┴─────────────────────────┘
```

## Community & Support

### Get Help

- **Discord:** Join our [Discord community](https://discord.com/invite/9A3k5dEBsY) for real-time chat and support
- **GitHub Discussions:** Start a [GitHub Discussion](https://github.com/apache/sedona/discussions) with questions or ideas
- **Documentation:** Check out our [comprehensive docs](https://sedona.apache.org/sedonadb)

### Contributing

We welcome contributions! Here's how you can get involved:

* **Report Issues:** Found a bug? Open an issue on GitHub
* **Suggest Features:** Have an idea? Start a GitHub Discussion
* **Fix Issues:** Comment "take" on any open issue to claim it
* **Submit PRs:** Brainstorm features with contributors and submit pull requests
* **Join Meetings:** Monthly contributor meetings - we'd love to have you!

### About SedonaDB

SedonaDB is a subproject of **Apache Sedona**, an Apache Software Foundation project. The project is governed by the Apache Software Foundation and subject to all the rules and oversight requirements. SedonaDB is built on top of **Apache Arrow** and **Apache DataFusion** for fast query processing.

### Related Projects

- **[Apache Sedona](https://sedona.apache.org/)** - The main Apache Sedona project for distributed spatial analytics
- **[Sedona SpatialBench](https://sedona.apache.org/spatialbench)** - Comprehensive benchmarking suite for spatial analytics performance testing


===== https://github.com/apache/sedona-db/blob/751453f04cd6e09842adf3073b2b3dac7d1777bc/docs/reference/sql/st_point.qmd =====
---
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

title: ST_Point
description: Constructs a Point Geometry from X and Y.
kernels:
  - returns: geometry
    args:
    - name: x
      type: double
    - name: "y"
      type: double
    - name: srid
      type: crs
---

## Description

Constructs a Point geometry from X and Y coordinates. An optional SRID or CRS can be provided as a third argument.

## Examples

```sql
SELECT ST_AsText(ST_Point(-74.0060, 40.7128));
```

With an SRID:

```sql
SELECT ST_Point(-74.0060, 40.7128, 4326);
```

With a CRS:

```sql
SELECT ST_Point(-74.0060, 40.7128, 'EPSG:3857');
```

```

GROUND THE CALL FORM by combining the sources above, in this priority order — and
NEVER invent a call shape that appears in none of them:
1. If a test-suite example is shown, its call form is authoritative (it compiles
   and passes) — reproduce that exact receiver and argument order.
2. Otherwise use the original-README example's call form.
3. If BOTH are shown, reproduce a real form verbatim (either compiles); when they
   differ, the instance/implicit form `value.sql:ST_Point(...)` is the most portable.
4. If NEITHER is shown, derive the call from the Signature/API facts and say in the
   entry that the example is inferred from the signature (not verified).
Preserve the receiver/qualifier EXACTLY as written — if it is
`value.sql:ST_Point(...)` or `Object.sql:ST_Point(...)`, keep it; do NOT collapse it to
a bare `sql:ST_Point(...)`, which usually will not compile.

Fill in the template below. Replace every TODO. Keep the Signature block and the
pre-filled Parameters types and Output type exactly as given; add the meaning of
each parameter, the Input (data/formats/preconditions), and what the Output
represents. Tailor Goal, examples, and Common Failure Modes to the target users
and use cases above, honoring the project constraints.

If the context states PRECONDITIONS or compatibility rules (conditions under which
the call is valid, or inputs that must be made compatible or converted/prepared
first with another operation) or TYPE-PARAMETER selection rules (which generic /
type argument to use for a given input type), you MUST state them explicitly under
Input and Common Failure Modes. These rules are what make generated code correct —
do not drop them. Output ONLY the filled template, nothing else.

## API Test: `sql:ST_Point`

### Signature
```python
ST_Point(x: double, y: double, srid: crs) -> geometry
```
_Source: source/docs/reference/sql/st_point.qmd:19_

_Source doc:_ ---
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

title: ST_Point
description: Constructs a Point Geometry from X and Y.
kernels:
  - returns: geometry
    args:
    - name: x
      type: double
    - name: "y"
      type: double
    - name: srid
      type: crs
---

## Description

Constructs a Point geometry from X and Y coordinates. An optional SRID or CRS can be provided as a third argument.

## Examples

```sql
SELECT ST_AsText(ST_Point(-74.0060, 40.7128));
```

With an SRID:

```sql
SELECT ST_Point(-74.0060, 40.7128, 4326);
```

With a CRS:

```sql
SELECT ST_Point(-74.0060, 40.7128, 'EPSG:3857');
```


### Goal
TODO: one sentence describing what `sql:ST_Point` does, in the project's domain terms.

### Parameters
- `x` (`double`): TODO — what this argument means / expected values.
- `y` (`double`): TODO — what this argument means / expected values.
- `srid` (`crs`): TODO — what this argument means / expected values.

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `geometry` — TODO: what the value represents and its format.

### Valid Call Patterns
```python
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `sql:ST_Point`.

### Prompt Snippet
```text
TODO
```

### Common Failure Modes
- TODO

### Fix Code Hint
```python
TODO
```

