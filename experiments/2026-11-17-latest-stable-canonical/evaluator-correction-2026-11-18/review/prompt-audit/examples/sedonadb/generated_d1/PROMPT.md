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
Constructs a new `geometry` object of type Point from provided X and Y coordinate values, with optional spatial reference system metadata.

### Parameters
- `x` (`double`): The X-coordinate (longitude or easting) of the point.
- `y` (`double`): The Y-coordinate (latitude or northing) of the point.
- `srid` (`crs`): Optional coordinate reference system identifier, provided as an integer (SRID) or a string (e.g., 'EPSG:4326').

### Input
Requires two `double` values for coordinates. An optional third argument can be an integer SRID or a string representing the CRS. No specific file format is required as this is a constructor for in-memory geometry objects.

### Output
Returns a `geometry` object representing a single point in the specified or default coordinate system.

### Valid Call Patterns
```python
# Basic construction
sd.sql("SELECT ST_Point(-74.0060, 40.7128) as geom").to_arrow_table()

# Construction with SRID
sd.sql("SELECT ST_Point(-74.0060, 40.7128, 4326) as geom").to_arrow_table()

# Construction with CRS string
sd.sql("SELECT ST_Point(-74.0060, 40.7128, 'EPSG:3857') as geom").to_arrow_table()
```

### LLM Instruction Prompt
- Always use `sd.sql(query).to_arrow_table()` for executing queries.
- When constructing points for spatial predicates, ensure the `srid` matches the reference geometry's CRS to avoid implicit conversion errors.
- Use `ST_AsText()` if you need to verify the geometry output in a human-readable format.

### Prompt Snippet
```text
sd.sql("SELECT ST_Point(x_val, y_val, srid_val)").to_arrow_table()
```

### Common Failure Modes
- Providing non-numeric values for `x` or `y` coordinates.
- Mismatched CRS: If performing spatial operations (e.g., `ST_Intersects`) between a point and another geometry, ensure both share the same CRS or are explicitly transformed.
- Invalid CRS strings: Providing a string that does not conform to standard EPSG or OGC formats.

### Fix Code Hint
```python
# Ensure coordinates are floats and CRS is a valid string or integer
x, y = -74.0060, 40.7128
srid = 4326
query = f"SELECT ST_Point({x}, {y}, {srid}) as geom"
result = sd.sql(query).to_arrow_table()
print("__CHECK__")
```

Available input path variables already in scope (choose the matching one(s) by type):
- raster_cea_tif = /home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/cea.tif
- raster_test4_tif = /home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/test4.tiff
- output_dir = /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/sedonadb/execution/output

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
