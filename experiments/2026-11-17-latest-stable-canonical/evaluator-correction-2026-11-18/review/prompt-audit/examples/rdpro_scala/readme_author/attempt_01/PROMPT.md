# Recorded author system prompt

You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

Role: An expert Scala developer using public RDPro/Raptor raster APIs.
Project: RDPro (Scala) - Pinned official Beast0.10.1 production source
Domain: Geospatial computing
Target users: Scala geospatial developers
Use cases: Raster processing and raster metadata; Raster/vector joins and zonal statistics; Local Spark transformations supporting raster workflows
Constraints: Use original APIs only.; Use provided local raster, shapefile, and HDF4 fixtures or tiny in-memory values.; Write temporary outputs only under the run output directory.; Do not contact services or change repository files.

# Recorded author user prompt

Document the Scala function `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` of RDPro.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{
  "name": "scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable",
  "signature": "[]:Boolean",
  "params": [],
  "returns": "Boolean",
  "source_doc": null,
  "overloads": [],
  "api_id": "scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable",
  "display_name": "isImmutable",
  "identity_version": "language_qualified_api_v1",
  "parameter_count": 0,
  "parameter_count_status": "compiler_declared",
  "exposure_ids": [
    "scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable"
  ],
  "preferred_public_path": "edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable",
  "qualified_name": "edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable",
  "owner": "edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer",
  "owner_kind": "class",
  "source": {
    "file": "source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala",
    "line": 53,
    "site_id": "Scala:cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:1841:method:isImmutable"
  },
  "definition_sites": [
    {
      "signature": "[]:Boolean",
      "qualified_name": "edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable",
      "owner": "edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer",
      "owner_kind": "class",
      "source": {
        "file": "source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala",
        "line": 53,
        "site_id": "Scala:cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:1841:method:isImmutable"
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
===== Original documentation part 1/1 =====
This distillation provides the factual foundation for generating documentation for the Beast (v0.10.1) geospatial framework.

### 1. Project purpose
Beast is a Spark-based system for Big Exploratory Analytics on Spatio-Temporal data. It provides a unified framework for processing vector and raster data, supporting multidimensional indexing, scalable visualization, and concurrent raster-vector processing (Raptor).

### 2. Main workflows
*   **Spatial Indexing:** Building distributed spatial indexes (e.g., R*-Grove) for efficient querying and join operations.
*   **Spatial Joins:** Performing joins between vector-vector or raster-vector datasets using distributed algorithms (BNLJ, PBSM, DJ, REPJ).
*   **Raster Processing (RDPro):** Pixel-level transformations, filtering, and reshaping (reprojection, rescaling) of raster data.
*   **Visualization:** Generating single-image plots or multilevel pyramid tiles (MVT/PNG) for interactive web exploration.
*   **Data Generation:** Creating synthetic spatial datasets (points, boxes, polygons) for benchmarking.

### 3. Important APIs and usage patterns
*   **Entry Points:** `SparkContext` (Scala) or `JavaSpatialSparkContext` (Java) are extended with spatial methods.
*   **RDD Types:** `RDD[IFeature]` for vector data; `RasterRDD[T]` or `RDD[ITile[T]]` for raster data.
*   **Spatial Partitioning:** `features.spatialPartition(classOf[RSGrovePartitioner])` is the recommended approach for load balancing.
*   **Raptor Join:** `raster.raptorJoin[T](vector)` combines raster pixels with vector geometries.
*   **Web Integration:** `AbstractWebHandler` allows custom web operations via `@WebMethod` annotations.

### 4. Inputs and file formats
*   **Vector:** Shapefile (ZIP or directory), GeoJSON, JSON+WKT, GPX, CSV (delimited points/WKT/envelopes).
*   **Raster:** GeoTIFF, HDF4.
*   **Auto-detection:** Beast attempts to detect formats based on file extensions or content analysis.

### 5. Outputs and generated artifacts
*   **Spatial Files:** Saved via `saveAsShapefile`, `saveAsGeoJSON`, `saveAsKML`, `saveAsWKTFile`, or `writeSpatialFile`.
*   **Visualization:** PNG images (`splot`), multilevel pyramid tiles (`mplot`, `vmplot`), and MVT vector tiles.
*   **Summaries:** `Summary` objects (MBR, count, size, geometry type) and histograms (count/size, simple/Euler).

### 6. Configuration and environment assumptions
*   **Dependencies:** JDK 1.8+, Apache Maven/SBT, Spark 3.x (implied).
*   **CLI:** Requires `beast` binary in `PATH`.
*   **Development:** Add `beast-spark` dependency to `pom.xml`.
*   **Server:** `beast server` starts a Jetty-based web UI on port 8890.

### 7. Commands and examples
**Spatial Indexing:**
```shell
beast index tl_2018_us_primaryroads.zip iformat:shapefile tl_2018_us_primaryroads_index gindex:rsgrove oformat:rtree
```

**Multilevel Plotting:**
```shell
beast mplot tl_2018_us_primaryroads_index iformat:rtree tl_2018_us_primaryroads_plot.zip levels:20 plotter:gplot -mercator
```

**Raptor Join (Scala):**
```scala
val join: RDD[RaptorJoinFeature[Float]] = treecover.raptorJoin(countries)
  .filter(v => v.m >= 0 && v.m <= 100.0)
```

**Raster Processing (Scala):**
```scala
val temperatureF: RasterRDD[Float] = temperatureK.mapPixels(k => (k-273.15f) * 9 / 5 + 32)
temperatureF.saveAsGeoTiff("temperature_f")
```

**Spatial Data Generation (Scala):**
```scala
val randomPoints: RDD[IFeature] = sc.generateSpatialData.uniform(1000000000)
```

### 8. Constraints, preconditions, compatibility rules
*   **Output Directories:** Operations fail if the output directory exists; use `-overwrite` to force deletion.
*   **Raster Compatibility:** `overlay` operations require identical metadata (resolution, CRS, tile size). Use `reshape` to align rasters first.
*   **Partitioning:** `spatialJoin` performance is optimized when both datasets are spatially partitioned.
*   **Type Selection:** `sc.geoTiff[T]` must match the pixel type (IntegerType, FloatType, Array[Int], Array[Float]).

### 9. Facts to preserve in the final README
*   Beast is a Spark add-on; it does not replace Spark but extends it with spatial RDDs.
*   The `RSGrovePartitioner` is the recommended partitioner for most spatial workloads.
*   The `beast-shell` provides an interactive Scala environment with Beast classes pre-linked.
*   The `Data Explorer` module exposes local files via REST API; use with caution in public environments.

### 10. Missing or weak documentation
*   Specific Spark version compatibility (e.g., Spark 3.2 vs 3.5) is not explicitly stated.
*   Detailed API documentation for `RaptorJoinFeature` fields (e.g., `v.m`, `v.feature`) is sparse.
*   The distinction between `mplot` (raster-based) and `vmplot` (vector-tile-based) could be clearer for users choosing a visualization strategy.
*   HDF4 support details are limited compared to GeoTIFF.

Real usage from the project's existing test suite (these compile and pass — base
the Valid Call Patterns and realistic Common Failure Modes on them; may be empty):
```Scala
(no existing test found for this API)
```

Verbatim code example(s) from the ORIGINAL project README that call `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable`
(the project's real, documented usage — may be empty):
```Scala
===== Shared original document: README.md =====
# ![Beast](doc/images/beast-logo.svg)
Beast is a system for Big Exploratory Analytics on Spatio-Temporal data. It supports both vector and raster data with
multidimensional data types and index structures. Here is a short list of the most important components of Beast.

![Beast Splash Screen](doc/images/splash.svg)

- **Multidimensional data**: Beast can work with arbitrarily multidimensional data.
- **Input/Output formats**: Beast supports many standard formats including Esri Shapefile, CSV, JSON+WKT, GeoJSON, KML, KMZ, and GPX.
- **Scalable visualization**: Visualize terabytes of data on an interactive map. Beast powers [UCR-Star](https://star.cs.ucr.edu) the home of terabytes of public geospatial data.
- **Raptor = Raster + Vector**: Beast hosts a novel component for processing raster and vector data concurrently. It is orders of magnitude faster than competitive systems.
- **Data Generator**: [Spider](https://spider.cs.ucr.edu) is an award-winning scalable data generator for benchmarking and testing.

## Documentation
- [Getting Started](doc/Home.md)
- [Installation](doc/installation.md)
- [Development Setup](doc/dev-setup.md)
- [Input/Output Formats](doc/input-output.md)
- [UCR-Star](https://star.cs.ucr.edu) powered by Beast
- [Spider Web](https://spider.cs.ucr.edu)
- [SatEx Satellite Data Extractor](satex/README.md)

## Questions

If you have any questions about any of the packages or modules of beast,
please ask your question on [StackOverflow](https://stackoverflow.com/)
and tag your questions with `#ucrbeast` and `#beast`. Beast team members
follow these tags and will respond to those questions as soon as possible.

## Issues

If you found any bugs or have any recommended features to add, please
[open a ticket](https://bitbucket.org/bdlabucr/beast/issues/new)
on the project homepage.

No documented original API excerpt for `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` in the reviewed corpus. Disposition: undocumented. No reviewed defining-interface or verified consolidated-operation match was found in the pinned original corpus. This disposition is a retrieval-coverage result, not a claim that the source lacks comments or that no related prose exists.
```

GROUND THE CALL FORM by combining the sources above, in this priority order — and
NEVER invent a call shape that appears in none of them:
1. If a test-suite example is shown, its call form is authoritative (it compiles
   and passes) — reproduce that exact receiver and argument order.
2. Otherwise use the original-README example's call form.
3. If BOTH are shown, reproduce a real form verbatim (either compiles); when they
   differ, the instance/implicit form `value.scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable(...)` is the most portable.
4. If NEITHER is shown, derive the call from the Signature/API facts and say in the
   entry that the example is inferred from the signature (not verified).
Preserve the receiver/qualifier EXACTLY as written — if it is
`value.scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable(...)` or `Object.scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable(...)`, keep it; do NOT collapse it to
a bare `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable(...)`, which usually will not compile.

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

## API Test: `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable`

### Signature
```scala
[]:Boolean
```
_Source: source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:53_

### Goal
TODO: one sentence describing what `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` does, in the project's domain terms.

### Parameters
_None._

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `Boolean` — TODO: what the value represents and its format.

### Valid Call Patterns
```scala
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable`.

### Prompt Snippet
```text
TODO
```

### Common Failure Modes
- TODO

### Fix Code Hint
```scala
TODO
```

