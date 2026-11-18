# Recorded author system prompt

You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

Role: An expert Java developer using public RDPro/Raptor raster APIs.
Project: RDPro Java (Java) - Pinned official Beast0.10.1 production source
Domain: Geospatial computing
Target users: Java geospatial developers
Use cases: Raster processing and raster metadata; Raster/vector joins and zonal statistics; Local Spark transformations supporting raster workflows
Constraints: Use original APIs only.; Use provided local raster, shapefile, and HDF4 fixtures or tiny in-memory values.; Write temporary outputs only under the run output directory.; Do not contact services or change repository files.

# Recorded author user prompt

Document the Java function `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` of RDPro Java.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{
  "name": "java:edu.ucr.cs.bdlab.raptor.Statistics.isValid",
  "signature": "():boolean",
  "params": [],
  "returns": "boolean",
  "source_doc": null,
  "overloads": [],
  "api_id": "java:edu.ucr.cs.bdlab.raptor.Statistics.isValid",
  "display_name": "isValid",
  "identity_version": "language_qualified_api_v1",
  "parameter_count": 0,
  "parameter_count_status": "compiler_declared",
  "exposure_ids": [
    "java:edu.ucr.cs.bdlab.raptor.Statistics.isValid"
  ],
  "preferred_public_path": "edu.ucr.cs.bdlab.raptor.Statistics.isValid",
  "qualified_name": "edu.ucr.cs.bdlab.raptor.Statistics.isValid",
  "owner": "edu.ucr.cs.bdlab.raptor.Statistics",
  "source": {
    "file": "source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java",
    "line": 131,
    "site_id": "Java:raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:3648:method:isValid"
  },
  "definition_sites": [
    {
      "signature": "():boolean",
      "qualified_name": "edu.ucr.cs.bdlab.raptor.Statistics.isValid",
      "owner": "edu.ucr.cs.bdlab.raptor.Statistics",
      "source": {
        "file": "source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java",
        "line": 131,
        "site_id": "Java:raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:3648:method:isValid"
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
### 1. Project purpose
Beast is a Spark-based system for Big Exploratory Analytics on Spatio-Temporal data. It provides a unified framework for processing and visualizing both vector (Shapefile, GeoJSON, etc.) and raster (GeoTIFF, HDF) data. Its core component, **Raptor** (Raster-Plus-Vector), enables high-performance concurrent processing of raster and vector datasets.

### 2. Main workflows
*   **Spatial Indexing:** Building distributed spatial indexes (e.g., R*-Grove) for efficient querying and visualization.
*   **Spatial Joins:** Performing distributed joins between vector-vector or raster-vector datasets using predicates like `Intersects`, `Contains`, and `MBRIntersects`.
*   **Raster Processing (RDPro):** Performing pixel-level operations (map, filter, overlay, reshape) on satellite data.
*   **Visualization:** Generating single-image plots or multilevel interactive pyramid tiles (MVT/PNG) for web exploration.
*   **Data Generation:** Creating synthetic spatial datasets (points, boxes, polygons) for benchmarking.

### 3. Important APIs and usage patterns
*   **Contexts:** Use `JavaSpatialSparkContext` (Java) or `import edu.ucr.cs.bdlab.beast._` (Scala) to access spatial RDD extensions.
*   **Raster/Vector Join:** `raptorJoin` combines raster tiles with vector features.
*   **Spatial Partitioning:** `spatialPartition(classOf[RSGrovePartitioner])` is the recommended method for load balancing.
*   **Web Integration:** Extend `AbstractWebHandler` and annotate methods with `@WebMethod` to add custom REST endpoints to the Beast server.

### 4. Inputs and file formats
*   **Vector:** Esri Shapefile, GeoJSON, JSON+WKT, GPX, CSV (delimited text).
*   **Raster:** GeoTIFF, HDF4.
*   **Auto-detection:** Beast can auto-detect formats based on file extensions or content analysis (for CSV).

### 5. Outputs and generated artifacts
*   **Spatial Files:** Saved via `saveAsShapefile`, `saveAsGeoJSON`, `saveAsKML`, or `writeSpatialFile`.
*   **Visualization:** PNG images, MVT (Mapbox Vector Tiles) pyramids, and interactive HTML/JS interfaces.
*   **Summaries:** JSON-formatted metadata including MBR, feature counts, and geometry types.

### 6. Configuration and environment assumptions
*   **Environment:** Requires JDK 1.8+, Apache Maven/SBT, and a configured Spark cluster.
*   **CLI:** The `beast` command-line tool is the primary entry point for prepackaged operations.
*   **Server:** The `beast server` command starts a Jetty-based visualization and API server on port 8890.

### 7. Commands and examples
**Indexing:**
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

**Spatial Join (Java):**
```java
JavaPairRDD<IFeature, IFeature> sjResults = JavaSpatialRDDHelper.spatialJoin(matchedPolygons, matchedPoints,
    SpatialJoinAlgorithms.ESJPredicate.Contains, SpatialJoinAlgorithms.ESJDistributedAlgorithm.PBSM);
```

### 8. Constraints, preconditions, compatibility rules
*   **Output Directories:** Operations fail if the output directory exists; use `-overwrite` to force deletion.
*   **Raptor Join:** Raster and vector data must be compatible (e.g., same CRS). Use `reproject` or `reshape` to align them first.
*   **Partitioning:** `spatialJoin` performs best when both datasets are spatially partitioned.
*   **Type Selection:** When loading GeoTIFFs, the type parameter (e.g., `[Int]`, `[Float]`) must match the file's pixel type.

### 9. Facts to preserve in the final README
*   Beast is a Spark add-on; it does not replace Spark but extends it with spatial RDDs.
*   The `R*-Grove` partitioner is the recommended choice for balanced spatial partitioning.
*   The `beast server` provides a REST API for dataset management and visualization.
*   The project uses `beast-spark` as the primary Maven dependency.

### 10. Missing or weak documentation
*   Specific API documentation for `RaptorJoinFeature` methods is sparse.
*   The distinction between `reshapeNN` and `reshapeAverage` is documented, but performance benchmarks for different interpolation methods are not provided.
*   The `beast.xml` configuration schema for custom web handlers is not fully detailed.
*   Not clearly documented: The exact behavior of `raptorJoin` when the raster and vector data have different coordinate systems without explicit reprojection.

Real usage from the project's existing test suite (these compile and pass — base
the Valid Call Patterns and realistic Common Failure Modes on them; may be empty):
```Java
(no existing test found for this API)
```

Verbatim code example(s) from the ORIGINAL project README that call `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid`
(the project's real, documented usage — may be empty):
```Java
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

No documented original API excerpt for `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` in the reviewed corpus. Disposition: undocumented. No reviewed defining-interface or verified consolidated-operation match was found in the pinned original corpus. This disposition is a retrieval-coverage result, not a claim that the source lacks comments or that no related prose exists.
```

GROUND THE CALL FORM by combining the sources above, in this priority order — and
NEVER invent a call shape that appears in none of them:
1. If a test-suite example is shown, its call form is authoritative (it compiles
   and passes) — reproduce that exact receiver and argument order.
2. Otherwise use the original-README example's call form.
3. If BOTH are shown, reproduce a real form verbatim (either compiles); when they
   differ, the instance/implicit form `value.java:edu.ucr.cs.bdlab.raptor.Statistics.isValid(...)` is the most portable.
4. If NEITHER is shown, derive the call from the Signature/API facts and say in the
   entry that the example is inferred from the signature (not verified).
Preserve the receiver/qualifier EXACTLY as written — if it is
`value.java:edu.ucr.cs.bdlab.raptor.Statistics.isValid(...)` or `Object.java:edu.ucr.cs.bdlab.raptor.Statistics.isValid(...)`, keep it; do NOT collapse it to
a bare `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid(...)`, which usually will not compile.

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

## API Test: `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid`

### Signature
```java
():boolean
```
_Source: source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:131_

### Goal
TODO: one sentence describing what `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` does, in the project's domain terms.

### Parameters
_None._

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `boolean` — TODO: what the value represents and its format.

### Valid Call Patterns
```java
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid`.

### Prompt Snippet
```text
TODO
```

### Common Failure Modes
- TODO

### Fix Code Hint
```java
TODO
```

