# Recorded system prompt

You write Python and SQL code that will be spliced into a runnable test harness.
Write Python statements only. A SedonaDB connection named sd is already provided. The target is a SQL function, not a Python method: call it inside sd.sql("SELECT ..."). Materialize with .to_arrow_table(), which returns a real pyarrow.Table. Read a scalar with table.column("name")[0].as_py() or rows with table.to_pylist(). Setup SQL may use sd.sql(...).execute(). The adapter requires the target SQL function to be called and materialized. Do not import another database or replace sd. Use Python assert with a falsifiable documented expectation and then print the exact target __CHECK__ witness.

Requested registered SQL operation:
SQL name: ST_Point
Documented call patterns: ST_Point(x: double, y: double, srid: crs) -> geometry
Arity status: user_defined_runtime_signature
Call this registered SQL operation using a documented call pattern; no finite maximum arity is asserted.

Pick the input variable(s) whose type matches the API's parameters. Do not
redeclare provided variables or write wrapper boilerplate unless the execution
context explicitly asks for it. Output ONLY the body statements that exercise the
API. Use ONLY the documentation provided. Output only code, no markdown fences.

Role: A Python developer using SedonaDB SQL for geospatial computation.
Project: SedonaDB 0.5.0 registered SQL operations (Python and SQL) - Official SedonaDB 0.5.0 SQL scalar and aggregate operations called through its Python SQL connection. Targets are public SQL names and their documented call patterns; runtime user-defined signatures are not assigned a finite maximum arity.
Domain: Geospatial vector and raster analysis
Target users: Python developers using SedonaDB SQL
Use cases: Run small SQL queries and verify materialized geometry, raster, scalar, and aggregate results.
Constraints: Use the original SQL API and original documentation only.; Write Python statements using sd.sql(query).to_arrow_table(); assert known documented results and print the __CHECK__ witness.; Use tiny literal inputs or the supplied local raster files. No remote datasets or services.

# Recorded user prompt

Documentation:
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


Available input path variables already in scope (choose the matching one(s) by type):
- raster_cea_tif = /home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/cea.tif
- raster_test4_tif = /home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/test4.tiff
- output_dir = /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/qualified/runs/original/sedonadb/sedonadb/execution/output

RECEIVER — call `sql:ST_Point` on the RIGHT type (calling it on the wrong receiver is
the #1 failure; if it is an instance method, first obtain a value of the owner type,
do NOT call it on an unrelated preloaded input):
(receiver type not resolved)

(none yet)

Write minimal body statements that use `sql:ST_Point` correctly per the docs,
reading from the appropriate input variable(s) above.

The snippet MUST EXECUTE the operation AND VERIFY the result is correct — not just
that it ran (some frameworks defer/lazily evaluate, and incorrectly interpreted
data can produce plausible output without throwing). End with a CORRECTNESS CHECK
written in valid Python and SQL syntax:
- force the result to materialize and compute a small witness of it — a count, a
  size, or a sampled element;
- use the language's normal assertion mechanism with a FALSIFIABLE condition tied
  to the documented contract or to values chosen earlier in the snippet;
- print a STRUCTURED line whose literal prefix is exactly
  `__CHECK__ sql:ST_Point ` followed by the witness, using the language's normal
  output function and formatting syntax.

The assertion must be capable of rejecting a plausible but incorrect result.
The following are TAUTOLOGIES and MUST NOT be the only correctness check:
- a Boolean value is either true or false;
- a count, size, offset, or index is merely non-negative;
- a value has the type already guaranteed by the language;
- an object is non-null when construction itself guarantees that;
- the operation completed without throwing.

Choose the strongest lightweight oracle supported by the documentation and the
available inputs:
- for setters/configuration APIs, read the value back and compare it with the exact
  value set;
- for generators, filters, joins, aggregations, and collections, compare a count,
  key, membership relation, or aggregate with a known expectation derived from a
  deliberately small input or an independently computed input property;
- for readers, validate representative content plus relevant size/shape/schema or
  metadata, rather than checking only that some output exists;
- for transformations, check deterministic sampled output values or a documented
  input/output invariant;
- for writers, read the output back and compare representative content or a known
  aggregate with the input.

If the documentation does not support any non-tautological oracle, still call and
materialize `sql:ST_Point`, but deliberately fail the assertion with a short message
stating that the documented contract is insufficient to verify the result. This is
a documentation-comprehension test: an unverifiable contract must not earn a pass.
If `sql:ST_Point` is itself a writer/output API, use an output binding only when one
is listed among the available inputs or execution context; then read back a small
part of the output, assert a known content/aggregate relation when the documented
contract permits it, and print the same structured line.
Do not call other heavyweight operations unless `sql:ST_Point` is the writer; keep the
body focused on `sql:ST_Point` so the run isolates that one call.
Use individual SQL statements. Paths raster_cea_tif and raster_test4_tif are available local fixture files; output_dir is available for tiny outputs. Use only these paths when a documented operation needs a file. Tiny SQL VALUES and documented constructors are available for in-memory inputs. Do not use remote URLs. No repairs are permitted in this R0 run.
