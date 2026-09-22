# RDPro — LLM_readme

LLM-facing API documentation. Generated from the API surface, project profile, and distilled docs.

## API Test: `addFeature`

### Signature
```scala
def addFeature(feature: IFeature): IntermediateVectorTile
def addFeature(feature: IFeature): Unit
def addFeature(feature: Row, geometry: LiteGeometry): Unit
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/VectorLayerBuilder.scala:92  (+2 more definition site/overload)_

### Goal
Adds a spatial feature (with its geometry and attributes) to an intermediate vector tile or layer builder, either appending it as-is or rasterizing and aggregating it based on the tile's current state.

### Parameters
- `feature` (`Row`): The attribute data of the feature represented as a Spark SQL `Row` (when using the separated overload), or an `IFeature` containing both geometry and attributes (in the primary signatures).
- `geometry` (`LiteGeometry`): The lightweight spatial geometry (e.g., point, line, polygon) corresponding to the `Row` attributes.

### Input
Requires an instantiated tile builder (e.g., `VectorLayerBuilder`). The feature must have a valid geometry (e.g., created via JTS `GeometryFactory`) and attributes. If constructing an `IFeature` manually via `Feature.create`, the attribute names array and values array must be of equal length. Null attribute values are permitted and will be safely skipped during tile construction.

### Output
Returns `Unit` — (or `IntermediateVectorTile` in the primary signature to allow method chaining). It represents the mutated state of the underlying tile builder, which now contains the appended or aggregated feature data ready for MVT (Mapbox Vector Tile) generation.

### Valid Call Patterns
```scala
val factory = FeatureReader.DefaultGeometryFactory
val builder = new VectorLayerBuilder(100, "test")

// Adding an IFeature with geometry and attributes
builder.addFeature(Feature.create(
  factory.createPoint(new CoordinateXY(50, 50)), 
  Array("id", "name"), // Attribute names
  null, 
  Array(10, "pt")      // Attribute values
))

// Adding a feature with a null attribute (safely skipped)
builder.addFeature(Feature.create(
  factory.createPoint(new CoordinateXY(50, 50)), 
  Array("id", "name"), 
  null, 
  Array(10, null)
))

val layer = builder.build()
```

### LLM Instruction Prompt
- When generating MVT (Mapbox Vector Tiles) or custom vector layers in Beast's visualization API, use `builder.addFeature(...)` to incrementally populate the layer. 
- If constructing an `IFeature` manually to pass to this method, ensure the schema array (attribute names) and the value array have the exact same length.
- Do not worry about filtering out null attribute values before calling this method; the builder safely skips null attributes automatically.

### Prompt Snippet
```text
Populate the `VectorLayerBuilder` by iterating over the local features and calling `addFeature`. Ensure the `IFeature` attribute names and values arrays match in length.
```

### Common Failure Modes
- **Array Length Mismatch:** Passing an `IFeature` where the attribute names array (e.g., `Array("id", "name")`) does not match the length of the values array (e.g., `Array(10)`). This will cause runtime indexing exceptions when the builder attempts to read the tags.
- **Uninitialized Builder:** Attempting to call `addFeature` without first properly initializing the `VectorLayerBuilder` with an extent and layer name.

### Fix Code Hint
```scala
// BAD: Mismatched attribute names and values arrays
// builder.addFeature(Feature.create(geom, Array("id", "name"), null, Array(10)))

// GOOD: Arrays match in length. Nulls are acceptable for missing values.
builder.addFeature(Feature.create(
  geom, 
  Array("id", "name"), 
  null, 
  Array(10, null)
))
```

## API Test: `addGeometry`

### Signature
```scala
def addGeometry(geometry: Geometry, title: String): Boolean
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/VectorCanvas.scala:169_

_Source doc:_ Adds the given geometry to the canvas. This method might simplify, drop, or combine geometries to accommodate the given geometry without getting too big. @param geometry the geometry to add @param title an optional title to attach to the geometry in the SVG file @return `true` if the state of the canvas was modified.

### Goal
Adds a spatial geometry to a `VectorCanvas` for visualization, automatically simplifying, dropping, or combining geometries to prevent the canvas from exceeding memory or size limits.

### Parameters
- `geometry` (`Geometry`): The spatial geometry (e.g., Point, Polygon, LineString) to be drawn on the canvas.
- `title` (`String`): An optional title to attach to the geometry in the resulting SVG file. Can be `null`.

### Input
Requires an initialized `VectorCanvas` instance. The `geometry` must be a valid JTS `Geometry` object (typically created via a `GeometryFactory` such as `GeometryReader.DefaultGeometryFactory`). 

### Output
Returns `Boolean` — `true` if the state of the canvas was modified by the addition of the geometry, otherwise `false`.

### Valid Call Patterns
```scala
// Example 1: Adding individual points to a VectorCanvas
val canvas = new VectorCanvas(new Envelope(0, 256, 0, 256), 256, 256, 0, 1)
val factory = GeometryReader.DefaultGeometryFactory

canvas.addGeometry(factory.createPoint(new CoordinateXY(5, 5)), null)
canvas.addGeometry(factory.createPoint(new CoordinateXY(10.5, 10.5)), "Point A")

// Example 2: Adding many geometries in a loop (may trigger rasterization/dropping)
for (x <- 0 to 255; y <- 0 to 255) {
  canvas.addGeometry(factory.createPoint(new CoordinateXY(x, y)), null)
}
```

### LLM Instruction Prompt
- Call `addGeometry` on an instantiated `VectorCanvas` object.
- Pass a valid JTS `Geometry` as the first argument and a `String` (or `null`) as the second argument for the SVG title.
- Do not assume that every geometry added will be preserved exactly as provided; the canvas is designed to simplify, combine, or drop geometries (or rasterize them entirely) if the visual density becomes too high.

### Prompt Snippet
```text
To draw a geometry on a VectorCanvas in Beast, use `canvas.addGeometry(geometry, title)`. The `title` parameter is used for SVG outputs and can be `null`. Note that the canvas automatically manages its size and may simplify or drop geometries if too many are added.
```

### Common Failure Modes
- **Assuming exact preservation of geometries:** Callers might expect `canvas.geometries.length` to equal the exact number of times `addGeometry` was called. If too many geometries (e.g., dense points) are added, the canvas will simplify or rasterize them, potentially resulting in an empty geometry list despite a modified canvas state.
- **Null Pointer Exceptions:** Passing an uninitialized `Geometry` object instead of a properly constructed JTS geometry.

### Fix Code Hint
```scala
// Ensure the geometry is properly instantiated using a factory before adding
val factory = GeometryReader.DefaultGeometryFactory
val geom = factory.createPoint(new CoordinateXY(100, 100))

// Title can safely be null if SVG metadata is not required
val wasModified = canvas.addGeometry(geom, null)
```

## API Test: `affineTransform`

### Signature
```scala
def affineTransform(matrix: AffineTransform): SpatialGeneratorBuilder
def affineTransform(geometry: Geometry): Geometry
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/SpatialGeneratorBuilder.scala:85  (+1 more definition site/overload)_

_Source doc:_ Sets the affine transformation for the generated data. @param matrix the affine transformation matrix @return

### Goal
Applies an affine transformation (such as scaling, translation, or rotation) either to a spatial data generator builder to transform all subsequently generated synthetic geometries, or directly to a single geometry.

### Parameters
- `matrix` (`AffineTransform`): The affine transformation matrix defining the spatial adjustments (e.g., `.scale()`, `.translate()`) to apply to the generated dataset.
- `geometry` (`Geometry`): The individual JTS geometry object to transform using the generator's configured affine transformation.

### Input
- For the `SpatialGeneratorBuilder` overload, the caller must provide an initialized `AffineTransform` matrix and chain the call onto `sparkContext.generateSpatialData` prior to specifying the distribution (e.g., `.uniform()`).
- For the `Geometry` overload, the caller must provide a valid JTS `Geometry` object.
- Requires an initialized `SparkContext` (or `JavaSpatialSparkContext`) to access the generator builder.

### Output
Returns `SpatialGeneratorBuilder` (when configuring a generator, allowing method chaining for data generation) or `Geometry` (when transforming a single geometry object).

### Valid Call Patterns
```scala
val transform = new AffineTransform()
transform.scale(2.0, 1.0)
transform.translate(0.0, 3.0)

// Apply to a spatial data generator
println(sparkContext.generateSpatialData
  .affineTransform(transform)
  .uniform(1000)
  .summary)
```

### LLM Instruction Prompt
- When generating synthetic spatial data in Beast (e.g., for benchmarking or testing), configure an `AffineTransform` matrix and pass it to `sparkContext.generateSpatialData.affineTransform(matrix)` **before** calling the distribution method (like `.uniform(size)`).
- Do not attempt to call `affineTransform` on the resulting `RDD`; it is a builder method on `SpatialGeneratorBuilder`.

### Prompt Snippet
```text
To apply scaling or translation to generated spatial data in Beast, create an `AffineTransform`, configure its parameters, and pass it to the generator builder: `sc.generateSpatialData.affineTransform(matrix).uniform(1000)`.
```

### Common Failure Modes
- **Calling on the wrong object:** Attempting to call `.affineTransform()` on the resulting `SpatialRDD` or `RDD[IFeature]` instead of the `SpatialGeneratorBuilder`. The transformation must be applied during the builder phase.
- **Incorrect chaining order:** Calling `.affineTransform()` after `.uniform()`. The distribution method (like `.uniform()`) terminates the builder and returns an RDD.

### Fix Code Hint
```scala
// WRONG: Calling affineTransform after uniform()
// val data = sparkContext.generateSpatialData.uniform(1000).affineTransform(transform)

// CORRECT: Apply the transform to the builder before generating the data
val data = sparkContext.generateSpatialData
  .affineTransform(transform)
  .uniform(1000)
```

## API Test: `append`

### Signature
```scala
def append(feature: IFeature, value: Any, name: String = null, dataType: DataType = null): IFeature
def append(rasterFeature: RasterFeature, name: String, value: Any): RasterFeature
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/Feature.scala:405  (+1 more definition site/overload)_

_Source doc:_ Appends an additional attribute to the given feature and returns a new feature @param feature the feature to append to. This feature is not modified. @param value the value to append. @param name (Optional) the name of the new attribute @param dataType (Optional) the type of the additional attribute. @return a new feature that contains the geometry and all attributes of the input feature + the new attribute.

### Goal
Creates a new spatial feature by appending an additional attribute (such as a unique ID or a joined property) to an existing feature without modifying the original.

### Parameters
- `feature` (`IFeature`): The input spatial feature (vector or raster feature) to which the attribute will be added. This feature is not modified.
- `value` (`Any`): The attribute value to append (e.g., a `Long` ID, a `String` name, or a computed statistic).
- `name` (`String`), default `null`: The optional column/attribute name for the newly appended value.
- `dataType` (`DataType`), default `null`: The optional Spark SQL `DataType` of the new attribute.

### Input
An existing `IFeature` (typically from a spatial RDD, such as points or polygons loaded from a Shapefile, GeoJSON, or CSV) and a scalar value to attach to it. This is commonly used inside a `.map()` operation after a spatial join (to merge attributes from two matched features) or after `zipWithUniqueId()` (to attach generated IDs).

### Output
Returns `IFeature` — A newly instantiated feature containing the original geometry, all prior attributes of the input feature, and the newly appended attribute.

### Valid Call Patterns
```scala
// Example 1: Appending a unique ID (from test suite)
val addRecordID: ((IFeature, Long)) => IFeature = fid => Feature.append(fid._1, fid._2, "ID")

// Example 2: Appending an attribute from a spatial join result (from README)
val finalResults: RDD[IFeature] = sjResults.map(pip => {
  val polygon: IFeature = pip._1
  val point: IFeature = pip._2
  Feature.append(point, polygon.getAs[String]("NAME"), "state")
})
```

### LLM Instruction Prompt
- Always call `append` on the `Feature` object (`Feature.append(feature, value, name)`), not as an instance method on the feature itself.
- Remember that `append` returns a *new* feature; it does not mutate the input feature in place. You must capture or return the result.
- When enriching features after a spatial join, extract the desired attribute from one feature using `.getAs[T]("colName")` and append it to the other feature using `Feature.append`.

### Prompt Snippet
```text
To add an attribute to an IFeature in Beast, use the static method `Feature.append(feature, value, "columnName")`. Do not call `feature.append(...)`. The operation is immutable and returns a new IFeature, so you must capture the return value.
```

### Common Failure Modes
- **Calling as an instance method:** Attempting to call `myFeature.append(value)` will fail compilation because `append` is a method on the `Feature` companion object, not the `IFeature` trait.
- **Ignoring the return value:** Because `IFeature` is immutable, calling `Feature.append(...)` without assigning or returning the result will leave the original feature unchanged and the new attribute will be lost.

### Fix Code Hint
```scala
// WRONG: Instance method call and ignoring return value
point.append(polygonName, "state")

// CORRECT: Static method call capturing the new feature
val enrichedPoint = Feature.append(point, polygonName, "state")
```

## API Test: `area`

### Signature
```scala
def area: Double
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/LiteGeometry.scala:115_

### Goal
Computes the 2D area of a lightweight geometry (`LiteGeometry`) used internally during vector tile generation and visualization.

### Parameters
_None._

### Input
A `LiteGeometry` instance (such as a `LiteList` representing a simplified polygon or linear ring). These geometries are typically generated during Mapbox Vector Tile (MVT) processing, visualization tasks, or when simplifying standard JTS geometries via `IntermediateVectorTile.simplifyGeometry`.

### Output
Returns `Double` — the computed area of the geometry in its current coordinate space (e.g., tile pixel coordinates for MVT generation).

### Valid Call Patterns
```scala
// Inferred from the signature and test suite context (LiteGeometry usage)
val simplifiedRing = interTile.simplifyGeometry(ring) // Returns a LiteGeometry (e.g., LiteList)
val geomArea: Double = simplifiedRing.area
```

### LLM Instruction Prompt
- Call `area` on a `LiteGeometry` instance to retrieve its area as a `Double`.
- Do not use parentheses when calling this method, as it is defined without them (`def area: Double`).
- Use this primarily when working with the `davinci` visualization package or evaluating the size of simplified geometries during vector tile generation.

### Prompt Snippet
```text
Calculate the area of the simplified LiteGeometry without using parentheses.
```

### Common Failure Modes
- **Compilation Error (Parentheses):** Calling `liteGeom.area()` will fail to compile in Scala because the method is defined without parentheses.
- **Zero Area for Lines/Points:** Calling `area` on a `LiteGeometry` that represents a point, a non-closed linestring, or a degenerate polygon will return `0.0`.

### Fix Code Hint
```scala
// WRONG:
val a = liteGeom.area()

// CORRECT:
val a = liteGeom.area
```

## API Test: `bit`

### Signature
```scala
def bit(cardinality: Long, digits: Int = 10, probability: Double = 0.2): JavaSpatialRDD
def bit(cardinality: Long, digits: Int = 10, probability: Double = 0.2): SpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:139  (+1 more definition site/overload)_

_Source doc:_ Generate data from the bit distribution @param cardinality the number of records to generate @param digits the number of digits to set per coordinate @param probability the probability of setting each bit @return the RDD that contains the generated data

### Goal
Generate a synthetic distributed spatial dataset (SpatialRDD) using a bit distribution, typically used for benchmarking spatial algorithms, partitioning, and queries in Beast.

### Parameters
- `cardinality` (`Long`): The total number of spatial records (geometries) to generate across the cluster.
- `digits` (`Int`), default `10`: The number of digits to set per coordinate, controlling the granularity/resolution of the generated spatial points.
- `probability` (`Double`), default `0.2`: The probability of setting each bit, which influences the spatial skew and clustering of the generated data.

### Input
Requires an initialized `SparkContext` (`sc`) or `JavaSpatialSparkContext` with Beast implicits imported. Because this is a data generator (part of the Spider component), it does not require input files, formats, or paths. It operates entirely in-memory to produce synthetic geometries.

### Output
Returns `JavaSpatialRDD` (or `SpatialRDD` in Scala) — a distributed collection of synthetic spatial features (points or geometries) distributed according to the specified bit probability, ready for spatial partitioning, joins, or visualization.

### Valid Call Patterns
```scala
// Using the SparkContext extension (idiomatic Scala)
import edu.ucr.cs.bdlab.beast._

val bitData: SpatialRDD = sc.generateSpatialData
  .bit(1000, digits = 10, probability = 0.2)

// Visualizing the generated bit distribution
bitData.plotImage(300, 300, "bit.png", opts = Seq(GeometricPlotter.PointSize -> 0))

// Using the Builder pattern (often used in Java or for advanced configuration)
val builderData: SpatialRDD = new SpatialGeneratorBuilder(sc)
  .config(SpatialGenerator.Seed, 1794)
  .bit(1000, 10, 0.2)
```

### LLM Instruction Prompt
- When benchmarking or testing spatial operations without real datasets, use `sc.generateSpatialData.bit(cardinality, digits, probability)` to create a synthetic `SpatialRDD`.
- Do not invent file paths for this operation; it generates data in-memory.
- Ensure Beast implicits (`import edu.ucr.cs.bdlab.beast._`) are in scope so that `sc.generateSpatialData` is available on the `SparkContext`.

### Prompt Snippet
```text
To generate synthetic spatial data for benchmarking in Beast, use `sc.generateSpatialData.bit(cardinality, digits, probability)`. This returns a `SpatialRDD` generated in-memory using a bit distribution. Requires `import edu.ucr.cs.bdlab.beast._`.
```

### Common Failure Modes
- **Missing Implicits:** Calling `sc.generateSpatialData` will fail with a "value generateSpatialData is not a member of org.apache.spark.SparkContext" compilation error if Beast implicits are not imported.
- **Invalid Probability:** Providing a `probability` outside the valid range of `0.0` to `1.0` will result in invalid distributions or runtime exceptions.
- **Memory Exhaustion:** Providing an excessively large `cardinality` on a small cluster without triggering a save or spatial partition operation can cause out-of-memory errors during action execution.

### Fix Code Hint
```scala
// FIX: Ensure Beast implicits are imported to attach `.generateSpatialData` to `sc`
import edu.ucr.cs.bdlab.beast._

// FIX: Use valid probability (0.0 to 1.0) and reasonable cardinality
val syntheticData: SpatialRDD = sc.generateSpatialData
  .bit(cardinality = 1000000L, digits = 10, probability = 0.2)
```

## API Test: `build`

### Signature
```scala
def build(): VectorTile.Tile.Layer
def build(): Scan
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/VectorLayerBuilder.scala:133  (+4 more definition site/overload)_

_Source doc:_ Finalize the layer and return it @return

### Goal
Finalizes the construction of a Mapbox Vector Tile (MVT) layer (or a data scan operation), compiling all added features and attributes into the final return object.

### Parameters
_None._

### Input
A populated builder instance (such as `VectorLayerBuilder`) that has been initialized and had spatial features added to it (e.g., via `addFeature`). 

### Output
Returns `VectorTile.Tile.Layer` — a compiled Mapbox Vector Tile layer containing the encoded geometries, attribute keys, and values ready for web-based exploration or serialization. (Overloads return a `Scan` object for internal data scanning operations).

### Valid Call Patterns
```scala
// Finalizing a VectorLayerBuilder to create an MVT layer
val factory = FeatureReader.DefaultGeometryFactory
val builder = new VectorLayerBuilder(100, "test")

// Add features to the builder
builder.addFeature(Feature.create(
  factory.createPoint(new CoordinateXY(50, 50)), 
  Array("id", "name"),
  null, 
  Array(10, "pt")
))

// Finalize and build the layer
val layer: VectorTile.Tile.Layer = builder.build()

// The layer can now be inspected or serialized
val featureCount = layer.getFeaturesCount
```

### LLM Instruction Prompt
- When generating Mapbox Vector Tiles (MVT) programmatically using `VectorLayerBuilder`, always call `.build()` with no arguments to finalize the layer after all features have been added.
- Do not pass parameters to `build()`.
- Expect a `VectorTile.Tile.Layer` (or `Scan` depending on the builder type) as the return value, not a Spark RDD or DataFrame.

### Prompt Snippet
```text
To finalize a Mapbox Vector Tile layer after adding features to a `VectorLayerBuilder`, call `builder.build()` to retrieve the compiled `VectorTile.Tile.Layer`.
```

### Common Failure Modes
- **Empty Layer Generation:** Calling `build()` before adding any features to the `VectorLayerBuilder` will result in a valid but empty MVT layer.
- **Type Mismatch:** Assuming `build()` returns a distributed Spark dataset (like `RDD[IFeature]`). It returns a local, finalized protocol buffer object (`VectorTile.Tile.Layer`) for a specific tile.

### Fix Code Hint
```scala
// WRONG: Assuming build() returns an RDD
// val rdd: RDD[IFeature] = builder.build()

// CORRECT: build() returns the finalized MVT layer object
val layer: VectorTile.Tile.Layer = builder.build()
```

## API Test: `buildIndex`

### Signature
```scala
def buildIndex(sparkContext: SparkContext, dir: String, indexFile: String): Unit
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterFileRDD.scala:186_

_Source doc:_ Build a raster index on all GeoTIFF files in a directory. @param sparkContext spark context to parallelize index creation @param dir the directory that contains raster files @param indexFile the path of the index file to write

### Goal
Build a spatial index (typically a CSV) for all GeoTIFF files within a specified directory, using Spark to parallelize the metadata extraction for faster spatial pruning later.

### Parameters
- `sparkContext` (`SparkContext`): The active Spark context used to parallelize the index creation across the cluster.
- `dir` (`String`): The path to the directory that contains the input GeoTIFF raster files.
- `indexFile` (`String`): The destination file path where the spatial index will be written (conventionally named `_index.csv`).

### Input
A directory containing one or more GeoTIFF files. The directory path (`dir`) and the destination path (`indexFile`) must be accessible by the Spark cluster's underlying file system (e.g., HDFS, S3, or local if running locally). 

### Output
Returns `Unit` — writes a spatial index file to the specified `indexFile` path. This index maps raster file paths to their spatial envelopes, allowing operations like `RasterFileRDD.selectFiles` to quickly filter rasters that intersect a specific bounding box without opening every file.

### Valid Call Patterns
```scala
// Build an index for a directory of GeoTIFFs
RasterFileRDD.buildIndex(sparkContext, "path/to/rasters", "path/to/rasters/_index.csv")
```

### LLM Instruction Prompt
- When asked to index a directory of GeoTIFFs for faster spatial querying or filtering in RDPro/Beast, use `RasterFileRDD.buildIndex(sparkContext, dir, indexFile)`. 
- Always call it on the `RasterFileRDD` object.
- The `indexFile` argument must be a full file path (e.g., ending in `.csv`), not just a directory.

### Prompt Snippet
```text
RasterFileRDD.buildIndex(sparkContext, "hdfs:///data/rasters", "hdfs:///data/rasters/_index.csv")
```

### Common Failure Modes
- **Missing Object Qualifier:** Calling `buildIndex(...)` as a bare function or on an RDD instance instead of the `RasterFileRDD` object.
- **Invalid Index File Path:** Providing a directory path for `indexFile` instead of a specific file path (like `_index.csv`), causing a write error.
- **Empty or Invalid Directory:** Pointing `dir` to a location that contains no GeoTIFF files or is inaccessible to the Spark cluster's executors.

### Fix Code Hint
```scala
// WRONG: Calling on an RDD or omitting the object
rasterRdd.buildIndex(sc, dir, indexFile)
buildIndex(sc, dir, indexFile)

// RIGHT: Call on RasterFileRDD object and provide a full file path for the index
RasterFileRDD.buildIndex(sc, "data/my_tiffs", "data/my_tiffs/_index.csv")
```

## API Test: `call`

### Signature
```scala
def call(f: IFeature): Int
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/operations/FeatureWriterSize.scala:31_

_Source doc:_ For Java callers

### Goal
Evaluates a spatial feature to return an integer value, serving as an implementation of Spark's Java `Function` interface for Java callers interacting with Beast's spatial partitioning.

### Parameters
- `f` (`IFeature`): The spatial feature (geometry and attributes) to be evaluated.

### Input
A single `IFeature` object (e.g., a point, line, or polygon loaded from CSV, Shapefile, or GeoJSON). This is typically provided internally by Spark when iterating over a `JavaRDD[IFeature]` during operations like spatial partitioning.

### Output
Returns `Int` — An integer value derived from the feature, such as a constant weight (e.g., `1`) or a computed size, used for load balancing during spatial partitioning.

### Valid Call Patterns
```scala
// Implementing the function for Java-facing APIs like IndexHelper.partitionFeatures
val weightFunction = new org.apache.spark.api.java.function.Function[IFeature, Int]() {
  override def call(v1: IFeature): Int = 1
}
```

### LLM Instruction Prompt
- Use `call` only when implementing `org.apache.spark.api.java.function.Function[IFeature, Int]` for Java-compatible Beast APIs (like `IndexHelper.partitionFeatures`). In idiomatic Scala Spark pipelines, prefer native Scala closures (e.g., `_ => 1`) instead of manually instantiating Java functions and overriding `call`.

### Prompt Snippet
```text
When using Java-facing Beast APIs from Scala (e.g., IndexHelper.partitionFeatures), implement org.apache.spark.api.java.function.Function[IFeature, Int] and override `call(f: IFeature): Int` to provide feature weights.
```

### Common Failure Modes
- **Idiomatic Scala Mismatch:** Attempting to manually invoke or override `call` in standard Scala `RDD[IFeature]` operations (like `map` or `spatialPartition`), which expect native Scala functions `(IFeature => Int)` rather than Java `Function` objects.
- **Null Pointer Exceptions:** Failing to handle null values if the overridden `call` method attempts to access feature geometry or attributes without null checks, as Spark may occasionally pass nulls depending on the upstream data source.

### Fix Code Hint
```scala
// Correct usage when interfacing with Java APIs requiring a Function[IFeature, Int]
val javaFunction = new org.apache.spark.api.java.function.Function[IFeature, Int]() {
  override def call(f: IFeature): Int = {
    if (f == null) 0 else 1
  }
}
```

## API Test: `checkOptions`

### Signature
```scala
def checkOptions(options: ParsedCommandLineOptions, out: PrintStream): Boolean
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/OperationHelper.scala:293_

_Source doc:_ Check if the user options are valid. This means that the user did not add any unexpected options or leave out any required option @param options parsed command line options. @return

### Goal
Validates parsed command-line arguments to ensure all required options for a Beast operation are present and no unexpected or unsupported options were provided.

### Parameters
- `options` (`ParsedCommandLineOptions`): The parsed command-line arguments, typically generated by calling `OperationHelper.parseCommandLineArguments(...)`.
- `out` (`PrintStream`): The output stream where validation error messages (such as missing required options or unrecognized flags) will be printed.

### Input
The caller must provide a valid `ParsedCommandLineOptions` object representing the user's CLI input for a specific Beast command, and an initialized `PrintStream` (such as `System.err`, `System.out`, or a custom stream like `new PrintStream(new NullOutputStream)` to suppress output). 

### Output
Returns `Boolean` — `true` if the options are perfectly valid (all required parameters are found and no unexpected parameters exist), and `false` otherwise.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast.util.OperationHelper
import java.io.PrintStream
import org.apache.commons.io.output.NullOutputStream

// Parse arguments for a specific operation
val parsedOptions = OperationHelper.parseCommandLineArguments(
  "subtest1", "path1", "sparam2:1", "-sparam", "-no-param1[0]", "path2"
)

// Validate the options, suppressing error output in this example
val isValid = OperationHelper.checkOptions(parsedOptions, new PrintStream(new NullOutputStream))

if (!isValid) {
  // Handle invalid options (e.g., exit program or throw exception)
}
```

### LLM Instruction Prompt
- When writing CLI wrappers or custom commands for Beast, always validate the user's input by passing the parsed arguments to `OperationHelper.checkOptions(options, out)`.
- Do not call `checkOptions` as a bare function; it must be called on the `OperationHelper` object.
- Provide a valid `PrintStream` (like `System.err`) as the second argument so the user can see which parameters were missing or unexpected.

### Prompt Snippet
```text
Validate Beast command-line arguments using `OperationHelper.checkOptions(parsedOptions, System.err)`. It returns a Boolean indicating if all required options are present and no unexpected options were provided.
```

### Common Failure Modes
- **Missing Required Parameters:** The user omitted an option that the specific Beast operation requires to run. `checkOptions` will return `false` and print the missing requirements to the provided `PrintStream`.
- **Unexpected Parameters:** The user provided a flag or option that the operation does not recognize (e.g., a typo in a flag name). `checkOptions` will return `false`.
- **Null PrintStream:** Passing `null` for the `out` parameter will cause a `NullPointerException` when the function attempts to print validation errors.

### Fix Code Hint
```scala
// Incorrect: Ignoring the validation result or passing null
OperationHelper.checkOptions(parsedOptions, null)

// Correct: Checking the boolean result and providing a valid PrintStream for user feedback
if (!OperationHelper.checkOptions(parsedOptions, System.err)) {
  System.exit(1) // Exit if options are invalid (missing required or containing unexpected)
}
```

## API Test: `compute`

### Signature
```scala
def compute(split: Partition, context: TaskContext): Iterator[ITile[T]]
def compute(pID: Int, ring: CoordinateSequence, w: Int, h: Int): Unit
def compute(split: Partition, context: TaskContext): Iterator[IFeature]
def compute(split: Partition, context: TaskContext): Iterator[(EnvelopeNDLite, (Iterator[IFeature], Iterator[IFeature]))]
def compute(split: Partition, context: TaskContext): Iterator[(Iterator[T], Iterator[U])]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/PixelsInside.scala:119  (+7 more definition site/overload)_

_Source doc:_ Compute the intersections for the given linear ring @param pID the ID of the polygon @param ring the list of coordinates that make the ring already projected to the raster space @param w the width of the raster in pixels @param h the height of the raster in pixels

### Goal
Compute the pixel intersections for a given linear ring (polygon boundary) projected into raster space, used internally during Raptor joins to match vector polygons to underlying raster pixels.

### Parameters
- `pID` (`Int`): The unique identifier (ID) of the polygon being processed.
- `ring` (`CoordinateSequence`): The list of coordinates forming the linear ring, which must already be projected into the raster's local pixel coordinate space.
- `w` (`Int`): The width of the raster in pixels.
- `h` (`Int`): The height of the raster in pixels.

### Input
A linear ring (`CoordinateSequence`) representing a polygon boundary. **Precondition:** The coordinates must be transformed from their original CRS (e.g., EPSG:4326) into the raster's pixel space prior to calling this method. The exact pixel dimensions of the raster (`w`, `h`) must be known. 

*(Note: The `compute` method is heavily overloaded. The `(Partition, TaskContext)` overloads are standard Spark internal methods used to evaluate RDD partitions for features, tiles, or spatial joins.)*

### Output
Returns `Unit` — mutates the internal state of the calling object (e.g., an `Intersections` tracker) to record which raster pixels intersect the given polygon ring. In Raptor joins, polygons match pixels whose *center* falls inside the polygon boundary.

### Valid Call Patterns
```scala
// 1. Authoritative usage from test suite (using the Geometry/RasterMetadata overload)
val metadata: RasterMetadata = createSimpleGrid(1, 1, 10, 10)
val geometries1 = Array[Geometry](
  GeometryReader.DefaultGeometryFactory.createPoint(new Coordinate(1, 1)),
  GeometryReader.DefaultGeometryFactory.createPoint(new Coordinate(3, 3))
)
val intersections1 = new Intersections
intersections1.compute(geometries1, metadata)

// 2. Inferred from the specific signature (not verified)
val intersections = new Intersections
intersections.compute(polygonID, coordinateSequence, rasterWidth, rasterHeight)
```

### LLM Instruction Prompt
- Do not call `compute` directly for standard user-facing raster-vector joins; prefer the high-level `raster.raptorJoin[T](vector)` API.
- If using `compute` for custom intersection tracking, you MUST ensure the `CoordinateSequence` is projected to raster space first. Do not pass raw geographic coordinates (e.g., lat/lon).
- When implementing custom Spark RDDs in Beast, the `compute(split: Partition, context: TaskContext)` overloads are used to yield iterators of `ITile[T]`, `IFeature`, or joined pairs.

### Prompt Snippet
```text
When performing raster-vector joins, avoid manually calling the internal `compute` intersection methods unless building custom plumbing. Use `raster.raptorJoin[T](vector)` instead. If you must use `compute(pID, ring, w, h)`, ensure the `ring` coordinates are already projected to raster pixel space.
```

### Common Failure Modes
- **Unprojected Coordinates:** Passing a `CoordinateSequence` in its original CRS (like WGS84) instead of raster pixel space, resulting in zero intersections or out-of-bounds errors.
- **Incorrect Raster Dimensions:** Providing `w` and `h` that do not match the actual raster tile or file, causing the intersection algorithm to truncate valid pixels or scan out of bounds.
- **Manual Plumbing Errors:** Attempting to use `compute` for zonal statistics instead of the built-in `raptorJoin`, missing the required quad-split optimizations for complex geometries (triggered automatically when points per geometry > 100).

### Fix Code Hint
```scala
// WRONG: Passing geographic coordinates to compute
// intersections.compute(1, geoRing, 1000, 1000)

// RIGHT: Use the high-level Raptor API for raster-vector joins
val treecover: RDD[ITile[Float]] = sc.geoTiff("treecover")
val countries: RDD[IFeature] = sc.shapefile("ne_10m_admin_0_countries.zip")
val join: RDD[RaptorJoinFeature[Float]] = treecover.raptorJoin(countries)
```

## API Test: `computeForFeatures`

### Signature
```scala
def computeForFeatures(features: SpatialRDD, synopsisSize: Long = 1024 * 1024): Synopsis
def computeForFeatures(features: SpatialRDD, sizeFunction: IFeature => Int = f => f.getStorageSize) : Summary
def computeForFeatures(features : JavaSpatialRDD) : Summary
def computeForFeatures(features: SpatialRDD, numPartitions: Int*): (Summary, RDD[(Array[Int], Summary)])
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/synopses/Synopsis.scala:34  (+3 more definition site/overload)_

### Goal
Computes geometric summaries (such as bounding boxes, feature counts, and storage sizes) for a spatial vector dataset, either globally for the entire dataset or locally partitioned across grid cells.

### Parameters
- `features` (`SpatialRDD`): The distributed set of spatial features (vector data) to summarize.
- `synopsisSize` (`Long`), default `1024 * 1024`: The target size in bytes for the generated synopsis when using the `Synopsis` overload.
- `sizeFunction` (`IFeature => Int`), default `f => f.getStorageSize`: An optional function to compute the size of a single feature.
- `numPartitions` (`Int*`): Either the total number of cells or an array specifying the number of partitions along each dimension for grid-based summaries.

### Input
A `SpatialRDD` (or `JavaSpatialRDD`) containing vector features. This is typically generated by loading vector data via context extensions like `sc.shapefile`, `sc.geojsonFile`, or `sc.readCSVPoint`. It cannot be used directly on raster data (`RasterRDD`).

### Output
Returns `Synopsis` — (or `Summary` / `(Summary, RDD[(Array[Int], Summary)])` depending on the overload). The value represents the computed statistics of the dataset, including the global bounding box (Minimum Bounding Rectangle) of the data, total feature count, and total size. The tuple overload returns one global summary and a set of local summaries for each grid cell.

### Valid Call Patterns
```scala
// 1. Compute a basic global summary (used for partitioner initialization)
val summary = Summary.computeForFeatures(features)

// 2. Compute a global summary with a custom size function
val summaryWithSize = Summary.computeForFeatures(features, f => f.getGeometry.getNumPoints * 2 * 4)

// 3. Use the summary to initialize a spatial partitioner
val partitionedFeatures = IndexHelper.partitionFeatures(
  features, 
  new GridPartitioner(Summary.computeForFeatures(features), 1)
)
```

### LLM Instruction Prompt
- Always call `computeForFeatures` as a static method on the `Summary` object (e.g., `Summary.computeForFeatures(features)`), never as an instance method on the RDD itself.
- Use this function when you need to extract the global bounding box or statistics of a `SpatialRDD` to initialize spatial partitioners (like `GridPartitioner` or `RSGrovePartitioner`).
- Do not use this function on raster datasets (`RasterRDD`); it is strictly for vector features (`SpatialRDD`).

### Prompt Snippet
```text
To compute the bounding box and statistics of a vector dataset in Beast, use `Summary.computeForFeatures(features)`. This is required when manually initializing spatial partitioners that need the global extent of the data.
```

### Common Failure Modes
- **Calling as an instance method:** Attempting to call `features.computeForFeatures()` will fail compilation. It must be called as `Summary.computeForFeatures(features)`.
- **Passing Raster Data:** Passing a `RasterRDD` (e.g., from `sc.geoTiff`) instead of a `SpatialRDD`. Raster metadata should be accessed via the raster's built-in metadata properties, not via vector summaries.

### Fix Code Hint
```scala
// WRONG: Calling as an instance method on the RDD
val summary = features.computeForFeatures()

// RIGHT: Calling as a method on the Summary object
val summary = Summary.computeForFeatures(features)
```

## API Test: `computeForFeaturesWithOutputSize`

### Signature
```scala
def computeForFeaturesWithOutputSize(features: JavaSpatialRDD, opts: BeastOptions) : Summary
def computeForFeaturesWithOutputSize(features : SpatialRDD, opts : BeastOptions) : Summary
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/operations/GeometricSummary.scala:49  (+1 more definition site/overload)_

_Source doc:_ Java shortcut

### Goal
Computes a geometric summary of a spatial dataset (such as bounding box and feature count) while simultaneously estimating the total output file size if the features were written to a specified format.

### Parameters
- `features` (`JavaSpatialRDD` | `SpatialRDD`): The distributed spatial dataset containing the vector geometries to be summarized.
- `opts` (`BeastOptions`): Configuration options specifying the target output format (e.g., `"iformat" -> "geojson"`) used to calculate the size estimate.

### Input
A loaded spatial RDD of vector features (e.g., points, lines, or polygons loaded from Shapefile, GeoJSON, or CSV). 

### Output
Returns `Summary` — A geometric summary object (which can be formatted as JSON) containing the dataset's spatial bounds, feature count, and the estimated output size in bytes for the specified format.

### Valid Call Patterns
```scala
// Estimate the output size if the records are written to GeoJSON
// Note: A tuple like "iformat" -> "geojson" is often implicitly converted to BeastOptions in Beast Scala APIs
val summary = GeometricSummary.computeForFeaturesWithOutputSize(features, "iformat" -> "geojson")

// Explicit BeastOptions construction
import edu.ucr.cs.bdlab.beast.common.BeastOptions
val opts = new BeastOptions().set("iformat", "geojson")
val summaryExplicit = GeometricSummary.computeForFeaturesWithOutputSize(features, opts)
```

### LLM Instruction Prompt
- When you need to compute a geometric summary and estimate the disk size of a spatial RDD before exporting it, call `GeometricSummary.computeForFeaturesWithOutputSize(features, opts)`. Do not call this as an instance method on the RDD. Always provide the target format (e.g., `"iformat" -> "geojson"`) in the `BeastOptions` argument.

### Prompt Snippet
```text
val summary = GeometricSummary.computeForFeaturesWithOutputSize(features, "iformat" -> "geojson")
```

### Common Failure Modes
- **Incorrect Receiver:** Attempting to call this as an instance method on the RDD (e.g., `features.computeForFeaturesWithOutputSize(...)`) instead of calling it statically on the `GeometricSummary` object.
- **Missing Format Option:** Failing to specify the `"iformat"` in the `BeastOptions`, which prevents the engine from accurately estimating the serialization overhead of the target format.

### Fix Code Hint
```scala
// WRONG: Calling as an RDD method
val summary = features.computeForFeaturesWithOutputSize("iformat" -> "geojson")

// RIGHT: Calling on the GeometricSummary object
val summary = GeometricSummary.computeForFeaturesWithOutputSize(features, new BeastOptions().set("iformat", "geojson"))
```

## API Test: `computePointHistogramSparse`

### Signature
```scala
def computePointHistogramSparse(features: SpatialRDD, sizeFunction: IFeature => Int, mbb: EnvelopeNDLite, numBuckets: Int*): UniformHistogram
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/synopses/HistogramOP.scala:72_

_Source doc:_ Compute a point histogram for sparse histograms. It maps each record to a bucket and then aggregate by bucket. This method can be helpful for very large histograms to avoid moving the entire histogram during the reduce step. @param features the features to compute their histogram @param sizeFunction the function that evaluates the size of each feature @param mbb the minimum bounding box of the histogram, typically, this is the same as the input MBB @param numBuckets the number of buckets in the histogram @return the computed histogram

### Goal
Computes a sparse uniform point histogram over a spatial dataset by mapping each feature to a bucket and aggregating, optimized to prevent memory bottlenecks during the reduce step for very large histograms.

### Parameters
- `features` (`SpatialRDD`): The distributed spatial dataset (vector geometries) to be binned into the histogram.
- `sizeFunction` (`IFeature => Int,
                                          mbb: EnvelopeNDLite, numBuckets: Int*`): This parameter block captures three distinct arguments:
  1. `sizeFunction`: A function evaluating the weight or size of each feature (e.g., `_ => 1` for a simple feature count).
  2. `mbb`: The minimum bounding box (`EnvelopeNDLite`) defining the spatial extent of the histogram grid.
  3. `numBuckets`: Varargs (`Int*`) specifying the number of buckets/partitions along the spatial dimensions.

### Input
- A `SpatialRDD` of vector features, typically loaded via context extensions like `sc.shapefile`, `sc.geojsonFile`, or `sc.readCSVPoint`.
- An `EnvelopeNDLite` representing the spatial bounds of the data. This is usually computed dynamically by calling `.summary` on the input `SpatialRDD`.
- Out-of-bound points (features falling outside the provided `mbb`) are safely handled by the sparse computation logic.

### Output
Returns `UniformHistogram` — A spatial histogram object containing the aggregated sizes/counts per grid cell, which can be queried for bucket values or partition counts.

### Valid Call Patterns
```scala
// Compute the Minimum Bounding Box (MBB) first
val mbr: EnvelopeNDLite = points.summary

// Call via the HistogramOP object, providing a size function (e.g., count of 1 per feature)
val h: UniformHistogram = HistogramOP.computePointHistogramSparse(points, _ => 1, mbr, 4)
```

### LLM Instruction Prompt
- When generating histograms for large, sparse spatial datasets in Beast, use the object method `HistogramOP.computePointHistogramSparse` instead of standard RDD histogram methods to avoid moving the entire histogram during the reduce step.
- Always compute or provide the Minimum Bounding Box (MBB) via `rdd.summary` to pass as the `mbb` argument.
- Provide a `sizeFunction` to dictate how features are weighted (use `_ => 1` for standard counting).

### Prompt Snippet
```text
For large sparse spatial datasets, avoid memory bottlenecks by using HistogramOP.computePointHistogramSparse(rdd, sizeFunc, mbb, numBuckets). Compute the mbb using rdd.summary first.
```

### Common Failure Modes
- **Calling as an instance method:** Attempting to call `rdd.computePointHistogramSparse(...)` will fail to compile. Unlike `rdd.uniformHistogramCount`, this specific sparse implementation must be called on the `HistogramOP` object.
- **Uninitialized or incorrect MBB:** Passing a null or manually constructed `EnvelopeNDLite` that does not cover the dataset's true extent may result in skewed histograms, though out-of-bound points are handled without crashing. Always prefer `features.summary`.

### Fix Code Hint
```scala
// WRONG: Called as an instance method
// val hist = features.computePointHistogramSparse(_ => 1, mbb, 100)

// RIGHT: Called on HistogramOP with a dynamically computed summary
val mbb = features.summary
val hist = HistogramOP.computePointHistogramSparse(features, _ => 1, mbb, 100)
```

## API Test: `config`

### Signature
```scala
def config(key: String, value: Any): JavaSpatialGeneratorBuilder
def config(opts: BeastOptions): JavaSpatialGeneratorBuilder
def config(key: String, value: Any): SpatialGeneratorBuilder
def config(opts: BeastOptions): SpatialGeneratorBuilder
def config: Map[String, String]
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:32  (+4 more definition site/overload)_

_Source doc:_ Set configuration of the generated data

### Goal
Sets configuration options for the spatial data generator (Spider) to control the properties of the generated synthetic datasets, such as geometry type, size, and random seed.

### Parameters
- `key` (`String`): The configuration property name (e.g., `UniformDistribution.GeometryType`, `SpatialGenerator.Seed`, `UniformDistribution.MaxSize`).
- `value` (`Any`): The value to assign to the configuration property (e.g., `"box"`, `1794`, `"0.2,0.1"`).

### Input
An initialized `SpatialGeneratorBuilder` or `JavaSpatialGeneratorBuilder` instance, typically created with a `SparkContext` (e.g., `new SpatialGeneratorBuilder(sparkContext)`).

### Output
Returns `SpatialGeneratorBuilder` (or `JavaSpatialGeneratorBuilder`) — the updated builder instance, allowing for fluent method chaining before triggering the final data generation.

### Valid Call Patterns
```scala
// Generate random boxes within a specific Minimum Bounding Rectangle (MBR)
val desiredMBR = new EnvelopeNDLite(2, 2, 3, 9, 8)
val randomPoints: SpatialRDD = new SpatialGeneratorBuilder(sparkContext).mbr(desiredMBR)
  .config(UniformDistribution.MaxSize, "0.2,0.1")
  .config(UniformDistribution.NumSegments, 10)
  .config(UniformDistribution.GeometryType, "box")
  .config(SpatialGenerator.Seed, 1794)
  .uniform(10)

// Generate random polygons
val randomPolygons: SpatialRDD = new SpatialGeneratorBuilder(sparkContext).mbr(desiredMBR)
  .config(UniformDistribution.MaxSize, "0.2,0.1")
  .config(UniformDistribution.NumSegments, 10)
  .config(UniformDistribution.GeometryType, "polygon")
  .config(SpatialGenerator.Seed, 1794)
  .uniform(100)
```

### LLM Instruction Prompt
- When generating synthetic spatial data using `SpatialGeneratorBuilder`, chain `.config(key, value)` calls to specify generation parameters before calling the terminal generation method (like `.uniform(N)`). 
- Use known configuration keys such as `UniformDistribution.GeometryType` (e.g., `"box"`, `"polygon"`), `UniformDistribution.MaxSize` (as a comma-separated string like `"0.2,0.1"`), `UniformDistribution.NumSegments`, and `SpatialGenerator.Seed`.
- Do not invent configuration keys; rely on the constants provided by the Beast library.

### Prompt Snippet
```text
Chain `.config(key, value)` on `SpatialGeneratorBuilder` to set generation parameters (e.g., geometry type, seed) before calling a terminal generation method like `.uniform(N)`.
```

### Common Failure Modes
- **Missing Terminal Operation:** Failing to call a terminal generation method (like `.uniform(N)`) after chaining `.config()` calls, which results in a builder object instead of the expected `SpatialRDD`.
- **Invalid Value Formats:** Providing incorrect types or string formats for complex configuration values (e.g., `MaxSize` expects a comma-separated string like `"0.2,0.1"`, not a single float).

### Fix Code Hint
```scala
// WRONG: Missing terminal generation method
val builder = new SpatialGeneratorBuilder(sc)
  .config(UniformDistribution.GeometryType, "box")

// CORRECT: Chain config and call terminal method to produce the SpatialRDD
val randomData = new SpatialGeneratorBuilder(sc)
  .config(UniformDistribution.GeometryType, "box")
  .uniform(100)
```

## API Test: `construct`

### Signature
```scala
def construct(out: DataOutput, entries: Array[(Long, Long, Int)]): Unit
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/DiskTileHashtable.scala:38_

_Source doc:_ Construct a compact hashtable for the given list of entries and write to the given output @param out the data output to write the hashtable to @param entries the list of entries in the form (key=tileID, val1=Offset, val2=Length)

### Goal
Construct a compact on-disk hashtable mapping spatial tile IDs to their byte offsets and lengths, writing the index directly to a binary output stream.

### Parameters
- `out` (`DataOutput`): The data output stream (typically a Hadoop `FSDataOutputStream`) where the binary hashtable structure will be written.
- `entries` (`Array[(Long, Long, Int)]`): The list of index entries to write, formatted strictly as tuples of `(key=tileID, val1=Offset, val2=Length)`.

### Input
The caller must provide an open, writable `DataOutput` stream (usually created via Hadoop's `FileSystem.create(path)`) and an array of tile metadata tuples. The `entries` array must contain `Long` values for the tile ID and byte offset, and an `Int` for the byte length. This is typically used as internal plumbing when saving multilevel pyramids or MVT (Mapbox Vector Tiles) archives.

### Output
Returns `Unit` — writes the compact hashtable directly to the provided `DataOutput` stream. The caller is responsible for closing the stream afterward.

### Valid Call Patterns
```scala
// Constructing a disk tile hashtable using Hadoop FileSystem
val file = new Path(scratchPath, "tile_index.dat")
val fileSystem = file.getFileSystem(sc.hadoopConfiguration)
val out = fileSystem.create(file)

// entries is an Array[(Long, Long, Int)] representing (tileID, offset, length)
DiskTileHashtable.construct(out, entries)

// The stream must be manually closed after construction
out.close()
```

### LLM Instruction Prompt
- When generating code to write a compact tile index to disk in Beast/RDPro, use `DiskTileHashtable.construct(out, entries)`.
- Ensure the `entries` array strictly matches the `Array[(Long, Long, Int)]` type signature, representing `(tileID, offset, length)`.
- Always instruct the caller to explicitly close the `DataOutput` stream (`out.close()`) after calling `construct` to prevent corrupted or truncated index files.

### Prompt Snippet
```text
To write a compact tile index to disk, use `DiskTileHashtable.construct(out, entries)` where `entries` is an `Array[(Long, Long, Int)]` representing `(tileID, offset, length)`. You must manually close the `DataOutput` stream after calling this method.
```

### Common Failure Modes
- **Unclosed Output Stream:** Failing to call `out.close()` after `construct` finishes, resulting in incomplete file writes or corrupted hashtables on disk.
- **Type Mismatch in Entries:** Providing an array of `(Int, Int, Int)` or `(Long, Int, Int)` instead of the required `(Long, Long, Int)`. Scala will throw a type mismatch compilation error.
- **Closed or Invalid Stream:** Passing a `DataOutput` that has already been closed or is read-only, which will throw an `IOException` during the write process.

### Fix Code Hint
```scala
// Ensure the entries array is correctly typed
val entries: Array[(Long, Long, Int)] = getTileEntries()

val fileSystem = path.getFileSystem(sc.hadoopConfiguration)
val out = fileSystem.create(path)
try {
  DiskTileHashtable.construct(out, entries)
} finally {
  // Always close the stream to flush the hashtable to disk
  out.close()
}
```

## API Test: `count`

### Signature
```scala
def count: Int
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/GeoTiffWriter.scala:860_

### Goal
Evaluates and returns the total number of elements (such as spatial features or intersections) in the underlying spatial dataset or collection.

### Parameters
_None._

### Input
A spatial dataset or collection, such as a `SpatialRDD` resulting from a `rangeQuery`, or a `SpatialIntersectionRDD1` resulting from a spatial join. If the exact distinct count of features is required without duplicates, the underlying dataset must have been partitioned using a disjoint partitioner (e.g., `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner`).

### Output
Returns `Int` — The total count of elements, features, or intersections present in the dataset.

### Valid Call Patterns
```scala
// Example 1: Counting the results of a spatial range query
val filteredData = partitionedData.rangeQuery(new GeometryFactory(new PrecisionModel(), 3857)
  .toGeometry(new Envelope(-11131949.07932735607028, -10018754.171394621953368,
    3503549.843504375312477, 4865942.279503175057471)))
val matchCount = filteredData.count()

// Example 2: Counting the number of spatial intersections between two datasets
val joined = new SpatialIntersectionRDD1(parks, lakes)
val intersectionCount = joined.count()
```

### LLM Instruction Prompt
- Use `count()` to retrieve the total number of elements in a spatial dataset, range query result, or intersection result.
- Remind users that counting features across non-disjoint partitions may include duplicates (features spanning multiple grid cells) unless a disjoint partitioner (like `RSGrovePartitioner` or `GridPartitioner`) was explicitly used prior to the query.

### Prompt Snippet
```text
To get the total number of features or intersections, call `.count()` on the spatial RDD. If you need an exact distinct feature count from a custom algorithm, ensure the RDD was partitioned with a disjoint partitioner (e.g., RSGrovePartitioner) beforehand to avoid duplicate results.
```

### Common Failure Modes
- **Duplicate Overcounting:** Calling `count()` on datasets with non-disjoint partitions (or after custom algorithms lacking duplicate avoidance) will result in overcounting features that span multiple partitions.
- **Missing Preconditions for Joins:** Triggering an action like `count()` on a spatial join using the Distributed Join (`DJ`) algorithm will fail or perform poorly if *both* input datasets were not spatially partitioned first.
- **Type Mismatch:** While standard Spark RDDs return a `Long` for `count()`, this specific Beast/RDPro API signature returns an `Int`. Assigning the result directly to a `Long` type without awareness may cause type inference confusion in strict Scala contexts.

### Fix Code Hint
```scala
// FIX: Ensure data is spatially partitioned with a disjoint partitioner to avoid duplicate counts
val mbr = data.summary
val gridPartitioner = new GridPartitioner(mbr, Array(2, 2))
val partitionedData = data.spatialPartition(gridPartitioner)

// Now range queries and counts will not contain duplicates
val filteredData = partitionedData.rangeQuery(queryGeometry)
val exactCount = filteredData.count()
```

## API Test: `create`

### Signature
```scala
def create[T](tiles: Array[MemoryTile[T]]): MemoryTileWindow[T]
def create[T: ClassTag](tileID: Int, metadata: RasterMetadata, rasterFeature: RasterFeature, numValues: Int): MemoryTileWindow[T]
def create(row: Row, geometry: Geometry): Feature
def create(geometry: Geometry, _names: Array[String], _types: Array[DataType], _values: Array[Any]): Feature
def create(x1: Double, y1:Double, x2: Double, y2:Double, srid: Int, rasterWidth: Int, rasterHeight: Int, tileWidth: Int, tileHeight: Int): RasterMetadata
def create(names: Array[String], values: Array[Any]): RasterFeature
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:324  (+5 more definition site/overload)_

_Source doc:_ Create a raster metadata that represents a geographical region provided by a rectangle. @param x1 the x-coordinate of the left edge of the pixel at (0, 0) @param y1 the y-coordinate of the top edge of the pixel at (0, 0) @param x2 the x-coordinate of the right edge of the pixel at (rasterWidth - 1, rasterHeight - 1) @param y2 the y-coordinate of the bottom edge of the pixel at (rasterWidth - 1, rasterHeight - 1) @param srid the SRID that represents the coordinate reference system of the raster @param rasterWidth the number of columns in the entire raster @param rasterHeight the number of rows in the entire raster @param tileWidth the width of each tile in pixels @param tileHeight the height of each tile in pixels @return a raster metadata wit the given information

### Goal
Creates metadata defining the geographical extent, coordinate reference system (CRS), and grid dimensions of a raster dataset, or instantiates vector features and memory tiles via its overloads.

### Parameters
- `x1` (`Double`): The x-coordinate of the left edge of the pixel at (0, 0).
- `y1` (`Double`): The y-coordinate of the top edge of the pixel at (0, 0).
- `x2` (`Double`): The x-coordinate of the right edge of the pixel at (rasterWidth - 1, rasterHeight - 1).
- `y2` (`Double`): The y-coordinate of the bottom edge of the pixel at (rasterWidth - 1, rasterHeight - 1).
- `srid` (`Int`): The SRID that represents the coordinate reference system of the raster (e.g., 4326).
- `rasterWidth` (`Int`): The number of columns in the entire raster.
- `rasterHeight` (`Int`): The number of rows in the entire raster.
- `tileWidth` (`Int`): The width of each tile in pixels.
- `tileHeight` (`Int`): The height of each tile in pixels.

### Input
Raw coordinate bounds, SRID, and grid dimensions. This metadata is a strict precondition for operations that generate or align rasters, such as `sc.rasterizePixels`, `sc.rasterizePoints`, or `RasterOperationsFocal.reshapeNN` / `reshapeAverage`. For the `Feature.create` overloads, it requires a valid `Geometry` (like `PointND` or `EnvelopeND`) and optional attribute arrays or a `Row`.

### Output
Returns `RasterMetadata` — an object representing the spatial and dimensional configuration of a raster grid. (Overloads return `Feature`, `RasterFeature`, or `MemoryTileWindow[T]`).

### Valid Call Patterns
```scala
// 1. Creating RasterMetadata for rasterization or reshaping
val metadata = RasterMetadata.create(x1 = -50, y1 = 40, x2 = -60, y2 = 30, srid = 4326,
  rasterWidth = 10, rasterHeight = 10, tileWidth = 10, tileHeight = 10)

// 2. Creating a Feature with a Point geometry (from test suite)
val pointFeature = Feature.create(null, new PointND(geometryFactory, 2, 1.0, 1.0))

// 3. Creating a Feature with an Envelope geometry (from test suite)
val envelopeFeature = Feature.create(null, new EnvelopeND(new GeometryFactory, 2, 3.0, 1.0, 5.0, 3.0))
```

### LLM Instruction Prompt
- When generating target grids for `reshapeNN` or `rasterizePixels`, use `RasterMetadata.create` with explicit named arguments to prevent parameter swapping.
- Ensure `x1`, `y1` represent the top-left pixel edge and `x2`, `y2` represent the bottom-right pixel edge.
- Remember that `raster.overlay(...)` requires all input rasters to have identical metadata. If inputs have mixed metadata, you MUST use `RasterMetadata.create` to define a common grid and convert them first using `RasterOperationsFocal.reshapeNN` (for categorical) or `reshapeAverage` (for continuous numerical data).
- For vector features, use `Feature.create(row, geometry)`.

### Prompt Snippet
```text
// Define a common grid to align rasters before an overlay operation
val targetMetadata = RasterMetadata.create(
  x1 = -124, y1 = 42, x2 = -114, y2 = 32, 
  srid = 4326, 
  rasterWidth = 1000, rasterHeight = 1000, 
  tileWidth = 100, tileHeight = 100
)
val reshapedRaster = RasterOperationsFocal.reshapeNN(raster, targetMetadata)
```

### Common Failure Modes
- **Overlay Precondition Violation:** Attempting to call `raster.overlay(...)` on rasters with different resolutions, CRSs, or tile sizes without first reshaping them to a common `RasterMetadata` grid.
- **Parameter Confusion:** Passing positional arguments to `RasterMetadata.create` instead of named arguments, leading to swapped `rasterWidth`/`tileWidth` or `x2`/`y2` coordinates, which results in severely distorted pixel resolutions.
- **Incorrect Reshape Interpolation:** Using `reshapeAverage` with a newly created `RasterMetadata` on categorical data (e.g., land cover). You must use `reshapeNN` for categorical data.

### Fix Code Hint
```scala
// BAD: Overlaying rasters with mismatched metadata
// val combined = raster1.overlay(raster2, ...) 

// GOOD: Aligning rasters to a common metadata grid before overlay
val commonMeta = RasterMetadata.create(
  x1 = -124.0, y1 = 42.0, x2 = -114.0, y2 = 32.0, 
  srid = 4326, rasterWidth = 1000, rasterHeight = 1000, 
  tileWidth = 100, tileHeight = 100
)
val alignedRaster1 = RasterOperationsFocal.reshapeNN(raster1, commonMeta)
val alignedRaster2 = RasterOperationsFocal.reshapeNN(raster2, commonMeta)
val combined = alignedRaster1.overlay(alignedRaster2, (p1: Int, p2: Int) => p1 + p2)
```

## API Test: `createDateFilter`

### Signature
```scala
def createDateFilter(dateStart: String, dateEnd: String): PathFilter
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/HDF4Reader.scala:299_

_Source doc:_ Creates a filter for paths that match the given range of dates inclusive of both start and end dates. Each date is in the format "yyyy.mm.dd". @param dateStart the start date as a string in the "yyyy.mm.dd" format (inclusive) @param dateEnd   the end date (inclusive) @return a PathFilter that will match all dates in the given range

### Goal
Creates a Hadoop `PathFilter` to include only file paths whose names match a specific date range (inclusive), typically used when loading time-series satellite imagery like HDF files.

### Parameters
- `dateStart` (`String`): The start date of the desired range, formatted strictly as "yyyy.mm.dd" (inclusive).
- `dateEnd` (`String`): The end date of the desired range, formatted strictly as "yyyy.mm.dd" (inclusive).

### Input
Requires date strings formatted exactly as "yyyy.mm.dd" (using periods as separators). The resulting filter expects to evaluate Hadoop `Path` objects where the path string or filename represents a date in this same format.

### Output
Returns `PathFilter` — a Hadoop `PathFilter` instance that evaluates to `true` for paths falling within the specified date range, and `false` otherwise.

### Valid Call Patterns
```scala
// Create a filter for a specific date range
val dateFilter = HDF4Reader.createDateFilter("2001.02.15", "2005.02.11")

// The filter can then be used to accept or reject Hadoop Paths
val isAccepted = dateFilter.accept(new Path("2003.07.15")) // returns true
```

### LLM Instruction Prompt
- When filtering time-series raster files (like HDFs) by date in RDPro/Beast, use `HDF4Reader.createDateFilter(startDate, endDate)`. You MUST format the date strings exactly as "yyyy.mm.dd" (using periods, not hyphens). Always call it using the `HDF4Reader` object qualifier.

### Prompt Snippet
```text
Use `HDF4Reader.createDateFilter("yyyy.mm.dd", "yyyy.mm.dd")` to generate a PathFilter for time-series raster loading. Dates must use periods as separators.
```

### Common Failure Modes
- **Incorrect Date Format:** Providing dates in standard ISO format (e.g., "2001-02-15") or with slashes ("2001/02/15") instead of the required "yyyy.mm.dd" format, causing the filter to fail to match paths.
- **Missing Object Qualifier:** Attempting to call `createDateFilter(...)` as a bare function instead of `HDF4Reader.createDateFilter(...)`.

### Fix Code Hint
```scala
// WRONG: Incorrect date format and missing qualifier
// val filter = createDateFilter("2001-02-15", "2005-02-11")

// RIGHT: Use HDF4Reader and "yyyy.mm.dd" format
val filter = HDF4Reader.createDateFilter("2001.02.15", "2005.02.11")
```

## API Test: `createPartitioner`

### Signature
```scala
def createPartitioner(features: SpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], numPartitions: NumPartitions, sizeFunction: IFeature=>Int, opts: BeastOptions ): SpatialPartitioner
def createPartitioner(features: JavaSpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], pcriterion: String, pvalue: Long, sizeFunction: org.apache.spark.api.java.function.Function[IFeature, Int] = {_.getStorageSize}, opts: BeastOptions ): SpatialPartitioner
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/indexing/IndexHelper.scala:136  (+1 more definition site/overload)_

_Source doc:_ Constructs a spatial partitioner for the given features. Returns an instance of the spatial partitioner class that is given which is initialized based on the given features. @param features the features to create the partitioner on @param partitionerClass the class of the partitioner to construct @param numPartitions the desired number of partitions (this is just a loose hint not a strict number) @param sizeFunction a function that calculates the size of each feature for load balancing. Only needed if the partition criterion is specified through partition size [[Size]] @return a constructed spatial partitioner

### Goal
Constructs and initializes a spatial partitioner (such as R*-Grove or GridPartitioner) based on the distribution of the provided spatial features to optimize load balancing and query pruning across a Spark cluster.

### Parameters
- `features` (`SpatialRDD`): The spatial features (vector dataset) used to calibrate and create the partitioner boundaries.
- `partitionerClass` (`Class[_ <: SpatialPartitioner],
                        numPartitions: NumPartitions,
                        sizeFunction: IFeature=>Int`): This represents three logical arguments: 
  1. `partitionerClass`: The specific partitioner class to instantiate (e.g., `classOf[RSGrovePartitioner]`).
  2. `numPartitions`: A loose hint for the desired number of partitions, typically wrapped in `NumPartitions(criterion, value)` (e.g., `NumPartitions(Fixed, n)` or `NumPartitions(IndexHelper.Size, bytes)`).
  3. `sizeFunction`: A function `IFeature => Int` that calculates the size/weight of each feature for load balancing (e.g., `_ => 1` for uniform weighting, or `_.getStorageSize`).
- `opts` (`BeastOptions`): Additional configuration options for the partitioner, such as `"disjoint" -> true` to enforce non-overlapping partition boundaries.

### Input
A `SpatialRDD` of vector features. If the caller requires disjoint partitions (to avoid duplicate results in custom distributed algorithms), they must select a compatible partitioner class. Only `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, and `STRPartitioner` support disjoint partitioning.

### Output
Returns `SpatialPartitioner` — an initialized spatial partitioner instance that can be passed directly to `features.spatialPartition(partitioner)` to physically distribute the RDD.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast.indexing.IndexHelper.{Fixed, NumPartitions}
import edu.ucr.cs.bdlab.beast.indexing.{IndexHelper, RSGrovePartitioner}
import edu.ucr.cs.bdlab.beast.common.BeastOptions

// Pattern 1: Creating a partitioner with a fixed number of partitions and disjoint boundaries
val partitioner = IndexHelper.createPartitioner(
  features, 
  classOf[RSGrovePartitioner],
  NumPartitions(Fixed, features.getNumPartitions), 
  _ => 1, 
  "disjoint" -> true
)
val partitionedFeatures = features.spatialPartition(partitioner)

// Pattern 2: Creating a partitioner based on partition size (bytes)
val sizePartitioner = IndexHelper.createPartitioner(
  dataset, 
  classOf[GridPartitioner],
  NumPartitions(IndexHelper.Size, 1024 * 1024), 
  { f: IFeature => 1024 }, 
  new BeastOptions()
)
```

### LLM Instruction Prompt
- Always call `createPartitioner` via the `IndexHelper` object (`IndexHelper.createPartitioner(...)`). Do not call it as a bare function or a method on the RDD.
- You must provide a `NumPartitions` hint (e.g., `NumPartitions(Fixed, n)` or `NumPartitions(IndexHelper.Size, bytes)`).
- You must provide a size function `IFeature => Int` (e.g., `_ => 1` for uniform feature weighting).
- If disjoint partitions are needed, you must use `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner`, and pass `"disjoint" -> true` in the `BeastOptions`.

### Prompt Snippet
```text
To spatially partition the vector dataset `points` into disjoint partitions using R*-Grove, use `IndexHelper.createPartitioner` to build the partitioner, passing `classOf[RSGrovePartitioner]`, a `NumPartitions` hint, a size function `_ => 1`, and `"disjoint" -> true`. Then apply it using `points.spatialPartition(partitioner)`.
```

### Common Failure Modes
- **Unsupported Disjoint Partitioner:** Requesting `"disjoint" -> true` while passing an incompatible partitioner class (only Grid, RSGrove, KDTree, and STR support disjoint boundaries).
- **Missing Object Qualifier:** Attempting to call `features.createPartitioner(...)` or a bare `createPartitioner(...)` instead of `IndexHelper.createPartitioner(...)`.
- **Missing Imports:** Failing to import `edu.ucr.cs.bdlab.beast.indexing.IndexHelper` or `NumPartitions`, causing compilation errors for the hint parameter.

### Fix Code Hint
```scala
// BAD: Calling createPartitioner directly on the RDD
val partitioner = features.createPartitioner(classOf[RSGrovePartitioner], ...)

// GOOD: Calling via IndexHelper with proper NumPartitions and size function
import edu.ucr.cs.bdlab.beast.indexing.IndexHelper
import edu.ucr.cs.bdlab.beast.indexing.IndexHelper.{Fixed, NumPartitions}

val partitioner = IndexHelper.createPartitioner(
  features, 
  classOf[RSGrovePartitioner],
  NumPartitions(Fixed, 100), 
  _ => 1, 
  "disjoint" -> true
)
```

## API Test: `createPartitions`

### Signature
```scala
def createPartitions(path: String, opts: BeastOptions, conf: Configuration): Array[FilePartition]
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialFileRDD.scala:318_

_Source doc:_ Create all partitions in this RDD for the given input file @return

### Goal
Calculates and creates all logical file partitions for a given spatial input file (or multiple files) to distribute the data reading process across a Spark cluster.

### Parameters
- `path` (`String`): The URI or file system path to the input spatial data. Can be a single path or multiple comma-separated paths (e.g., `input1.getPath + "," + input2.getPath`).
- `opts` (`BeastOptions`): Configuration options for the Beast engine, crucially including the input format (e.g., `"iformat" -> "shapefile"` or `SpatialFileRDD.InputFormat -> "geojson"`).
- `conf` (`Configuration`): The Hadoop configuration object, typically retrieved via `sparkContext.hadoopConfiguration`.

### Input
- **Data/Formats:** Spatial data files supported by Beast (e.g., Esri Shapefile, GeoJSON, CSV, GeoTIFF, HDF). 
- **Preconditions:** The file paths must be accessible via the provided Hadoop `Configuration`. If the format cannot be auto-detected from the extension, the `opts` parameter must explicitly define the format (e.g., `SpatialFileRDD.InputFormat -> "geojson"`).

### Output
Returns `Array[FilePartition]` — An array of logical file splits (`FilePartition` objects) representing the distributed chunks of the input data. These partitions can subsequently be iterated over or passed to `SpatialFileRDD.readPartition` to extract the actual spatial features or pixels.

### Valid Call Patterns
```scala
// Pattern 1: Single file with explicit BeastOptions
val opts: BeastOptions = SpatialFileRDD.InputFormat -> "geojson"
val partitions = SpatialFileRDD.createPartitions(inputFile.getPath, opts, sparkContext.hadoopConfiguration)

// Pattern 2: Multiple comma-separated paths
val partitions = SpatialFileRDD.createPartitions(
  input1.getPath + "," + input2.getPath,
  "iformat" -> "shapefile", 
  sparkContext.hadoopConfiguration
)
```

### LLM Instruction Prompt
- Call `SpatialFileRDD.createPartitions` when you need to manually calculate the distributed splits of a spatial file before reading it (e.g., for custom local iteration or building a custom RDD).
- ALWAYS qualify the call with the `SpatialFileRDD` object; never call `createPartitions` as a bare function.
- ALWAYS pass the Hadoop configuration via `sparkContext.hadoopConfiguration` (or `sc.hadoopConfiguration`).
- Ensure the `BeastOptions` parameter specifies the correct input format if it is not standard, using `SpatialFileRDD.InputFormat -> "<format>"`.

### Prompt Snippet
```text
To manually split a spatial file into partitions for distributed or local reading in Beast, use `SpatialFileRDD.createPartitions(path, opts, sc.hadoopConfiguration)`. Provide the format in `opts` (e.g., `SpatialFileRDD.InputFormat -> "shapefile"`). Multiple input paths can be joined with commas.
```

### Common Failure Modes
- **Bare Function Call:** Attempting to call `createPartitions(...)` without the `SpatialFileRDD.` qualifier, resulting in a compilation error.
- **Missing Input Format:** Failing to specify the `"iformat"` in `BeastOptions` for files without standard extensions, causing Beast to fail to identify the correct `FeatureReader`.
- **Invalid Hadoop Configuration:** Passing `null` or an uninitialized configuration instead of `sparkContext.hadoopConfiguration`, leading to NullPointerExceptions or HDFS connection failures.

### Fix Code Hint
```scala
// WRONG: Bare function call and missing Hadoop conf
// val parts = createPartitions("data.geojson", new BeastOptions(), null)

// RIGHT: Qualified call with proper options and Hadoop configuration
val opts: BeastOptions = SpatialFileRDD.InputFormat -> "geojson"
val parts = SpatialFileRDD.createPartitions(
  "data.geojson", 
  opts, 
  sparkContext.hadoopConfiguration
)
```

## API Test: `createSummaryAccumulator`

### Signature
```scala
def createSummaryAccumulator(sc: SparkContext) : SummaryAccumulator
def createSummaryAccumulator(sc: SparkContext, sizeFunction: IFeature => Int) : SummaryAccumulator
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/synopses/Summary.scala:422  (+1 more definition site/overload)_

_Source doc:_ Create a summary accumulator that uses the method [[IFeature#getStorageSize]] to accumulate the sizes of the features. @param sc the spark context to register the accumulator to @return the initialized and registered accumulator

### Goal
Creates a Spark accumulator to compute geometric summaries (such as bounding boxes, feature counts, and storage sizes) of spatial features during a distributed RDD transformation or action.

### Parameters
- `sc` (`SparkContext`): The active Spark context used to initialize and register the accumulator on the cluster.
- `sizeFunction` (`IFeature => Int`): A custom function to calculate the size of a feature. If omitted (using the 1-argument overload), it defaults to using `IFeature#getStorageSize` to accumulate feature sizes.

### Input
- An initialized `SparkContext` or `JavaSpatialSparkContext`.
- An `RDD[IFeature]` (e.g., loaded via `sc.shapefile` or `sc.geojsonFile`) whose elements will be passed to the accumulator's `.add(f)` method.
- **Precondition:** Because this relies on Spark's accumulator mechanics, the RDD transformations containing the `.add()` calls must be evaluated by a Spark action (e.g., `count()`, `collect()`, or saving to disk) before the accumulator's value is read.

### Output
Returns `SummaryAccumulator` — A registered Spark accumulator. After a Spark action is triggered, calling `.value` on this accumulator yields a geometric summary object containing the Minimum Bounding Rectangle (MBR), total feature count, and total size of the accumulated features.

### Valid Call Patterns
```scala
// 1. Standard usage with default size function (from project README)
var features = sparkContext.shapefile("input.zip")
val accumulator = Summary.createSummaryAccumulator(sparkContext)

// Add features to the accumulator during a transformation
val processedFeatures = features.map(f => {
  accumulator.add(f)
  f
})

// Trigger a Spark action to evaluate the RDD and populate the accumulator
processedFeatures.count()

// Retrieve the computed summary
val summary = accumulator.value
```

### LLM Instruction Prompt
- Use `Summary.createSummaryAccumulator(sc)` to compute spatial summaries in a single pass while transforming data.
- ALWAYS remind the user that Spark accumulators are evaluated lazily. A Spark action (like `count()`, `collect()`, or `saveAs...`) MUST be executed on the RDD where `.add(f)` is called before attempting to read `accumulator.value`.
- Warn users about Spark's execution model: if the RDD is evaluated multiple times without being cached, the accumulator will over-count.

### Prompt Snippet
```text
To compute a geometric summary while processing features, initialize `val acc = Summary.createSummaryAccumulator(sc)`. Inside your `map` or `foreach`, call `acc.add(feature)`. You must trigger a Spark action on the resulting RDD before calling `acc.value` to get the summary.
```

### Common Failure Modes
- **Empty or Zero Summary:** Calling `accumulator.value` immediately after a `.map()` or `.filter()` transformation without triggering a Spark action. The accumulator will return empty bounds and zero counts because the lazy transformation hasn't executed yet.
- **Over-counting Features:** Triggering multiple Spark actions on the RDD containing the `.add(f)` calls without caching the RDD first. Spark will re-evaluate the transformations and add the features to the accumulator multiple times.
- **Missing Qualifier:** Calling `createSummaryAccumulator(sc)` directly instead of `Summary.createSummaryAccumulator(sc)`.

### Fix Code Hint
```scala
// WRONG: Reading accumulator before an action
val acc = Summary.createSummaryAccumulator(sc)
val mapped = features.map(f => { acc.add(f); f })
println(acc.value) // Will be empty!

// RIGHT: Trigger action first
val acc = Summary.createSummaryAccumulator(sc)
val mapped = features.map(f => { acc.add(f); f })
mapped.count() // Force evaluation
println(acc.value) // Contains correct MBR, count, and size
```

## API Test: `createTileIDFilter`

### Signature
```scala
def createTileIDFilter(rect: Rectangle2D): PathFilter
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/HDF4Reader.scala:270_

_Source doc:_ Create a path filter that selects only the tiles that match the given rectangle in the Sinusoidal space. @param rect the extents of the range to compute the filter for in the Sinusoidal space @return a Path filter that will match the tiles based on the file name using the <tt>hxxvyy</tt> part

### Goal
Creates a Hadoop `PathFilter` that identifies and selects HDF tile files whose `hxxvyy` filename pattern intersects a specified bounding box in Sinusoidal projection space.

### Parameters
- `rect` (`Rectangle2D`): The spatial extent (bounding box) in Sinusoidal space used to filter the tiles.

### Input
A `java.awt.geom.Rectangle2D` representing the query window. The coordinates must be provided in Sinusoidal space, which typically requires converting standard WGS84 degrees to radians and scaling them (e.g., using `HDF4Reader.Scale`). The filter is designed to evaluate file paths that follow the standard MODIS/HDF tile naming convention containing the `hxxvyy` grid identifier.

### Output
Returns `PathFilter` — A Hadoop `PathFilter` instance whose `accept(path: Path)` method evaluates to `true` if the file's `hxxvyy` tile ID falls within the specified Sinusoidal rectangle, allowing for efficient spatial pruning before reading data.

### Valid Call Patterns
```scala
// Create a filter for a specific bounding box converted to Sinusoidal space
val tileIDFilter = HDF4Reader.createTileIDFilter(new Rectangle2D.Double(
  Math.toRadians(-145.0) * HDF4Reader.Scale,
  Math.toRadians(5.0) * HDF4Reader.Scale,
  Math.toRadians(29.0) * HDF4Reader.Scale,
  Math.toRadians(49.0) * HDF4Reader.Scale
))

// The filter can then be used to accept/reject Hadoop Paths
val isAccepted = tileIDFilter.accept(new Path("tile-h03v03.hdf"))
```

### LLM Instruction Prompt
- Use `HDF4Reader.createTileIDFilter(rect)` when you need to spatially prune HDF files (like MODIS satellite imagery) based on their filename tile IDs (`hxxvyy`) before loading them into Spark.
- ALWAYS ensure the `Rectangle2D` passed to this function is in Sinusoidal space, not raw WGS84 degrees. Convert degrees to radians and multiply by `HDF4Reader.Scale`.
- Call this method on the `HDF4Reader` object.

### Prompt Snippet
```text
`HDF4Reader.createTileIDFilter(rect: Rectangle2D): PathFilter` creates a Hadoop PathFilter to select HDF files matching a bounding box in Sinusoidal space based on their `hxxvyy` filename pattern. Convert lat/lon to Sinusoidal using `Math.toRadians(deg) * HDF4Reader.Scale`.
```

### Common Failure Modes
- **Unprojected Coordinates:** Passing a `Rectangle2D` with raw WGS84 latitude/longitude degrees. The filter expects Sinusoidal space; failing to convert will result in incorrect tile filtering (either rejecting all tiles or accepting the wrong ones).
- **Incompatible Filenames:** Applying the resulting `PathFilter` to files that do not contain the `<tt>hxxvyy</tt>` pattern in their name (e.g., standard GeoTIFFs or renamed HDFs). The filter relies strictly on parsing this string from the filename.

### Fix Code Hint
```scala
// WRONG: Passing raw degrees
// val filter = HDF4Reader.createTileIDFilter(new Rectangle2D.Double(-145.0, 5.0, 29.0, 49.0))

// RIGHT: Converting degrees to Sinusoidal space using HDF4Reader.Scale
val filter = HDF4Reader.createTileIDFilter(new Rectangle2D.Double(
  Math.toRadians(-145.0) * HDF4Reader.Scale,
  Math.toRadians(5.0) * HDF4Reader.Scale,
  Math.toRadians(29.0) * HDF4Reader.Scale,
  Math.toRadians(49.0) * HDF4Reader.Scale
))
```

## API Test: `crsToSRID`

### Signature
```scala
def crsToSRID(crs: CoordinateReferenceSystem) : Int
```
_Source: beast/cg/src/main/scala/org/apache/spark/beast/CRSServer.scala:270_

_Source doc:_ Get an integer SRID that corresponds to the given CRS according to the following logic. 1. If crs is null, return 0 2. Search the local cache as the fastest method of known CRS. 3. If not found in cache, look up the the EPSG database to find an SRID, cache, and return it. 4a. If the server is running, contact the server to get the SRID 4b. If the server is not running, assign a custom negative SRID and cache it @param crs the CRS to find an SRID for @return a unique SRID that identifies the given CRS

### Goal
Convert a GeoTools `CoordinateReferenceSystem` object into a unique integer Spatial Reference System Identifier (SRID), resolving standard EPSG codes or assigning custom negative IDs for non-standard projections.

### Parameters
- `crs` (`CoordinateReferenceSystem`): The spatial coordinate reference system (e.g., WGS84, Web Mercator, or a custom projection) to be mapped to an integer SRID.

### Input
A valid `CoordinateReferenceSystem` instance, typically obtained via GeoTools (e.g., `CRS.decode("EPSG:4326")`) or constructed manually. 
*Precondition:* If you are working with custom (non-EPSG) projections in a distributed Spark environment, you must start the Beast CRS Server (`CRSServer.startServer(sc)`) before calling this method. This ensures that the custom negative SRID assigned by the driver can be successfully resolved by worker nodes during distributed raster/vector operations.

### Output
Returns `Int` — A unique integer representing the SRID. 
- Returns `0` if the input `crs` is null.
- Returns a positive integer (the EPSG code) if the CRS is found in the local cache or EPSG database.
- Returns a custom negative integer if the CRS is non-standard/custom.

### Valid Call Patterns
```scala
// Example 1: Standard CRS (EPSG lookup)
CRSServer.startServer(sc)
try {
  val wgs84 = CRS.decode("EPSG:4326")
  val sridWGS84 = CRSServer.crsToSRID(wgs84) // Returns 4326
} finally {
  CRSServer.stopServer(true)
}

// Example 2: Custom/Non-standard CRS
CRSServer.startServer(sc)
try {
  val sinusoidal = new DefaultProjectedCRS("Sinusoidal", ...) // Custom CRS definition
  val sridSinusoidal = CRSServer.crsToSRID(sinusoidal) // Returns a negative integer
} finally {
  CRSServer.stopServer(true)
}
```

### LLM Instruction Prompt
- Call `CRSServer.crsToSRID(crs)` to obtain an integer SRID for a given `CoordinateReferenceSystem`.
- Always wrap distributed CRS operations with `CRSServer.startServer(sc)` and `CRSServer.stopServer(true)` to ensure custom projections (which receive negative SRIDs) can be resolved across the Spark cluster.
- Do not assume the returned SRID is always positive; custom projections will return negative integers.

### Prompt Snippet
```text
Use `CRSServer.crsToSRID(crs)` to convert a `CoordinateReferenceSystem` to an integer SRID. Standard EPSG codes return positive integers; custom CRSs return negative integers. Always start `CRSServer` first if running on a cluster to ensure workers can resolve custom SRIDs.
```

### Common Failure Modes
- **Unresolved Custom SRIDs on Workers:** If a custom CRS is passed to `crsToSRID` without `CRSServer.startServer(sc)` running, it will be assigned a custom negative SRID and cached locally on the driver. When worker nodes attempt to resolve this negative SRID during a distributed task (like `raster.reproject`), they will fail because they cannot contact the driver's CRS server to retrieve the WKT definition.
- **Missing GeoTools Dependencies:** Attempting to decode or create the input `CoordinateReferenceSystem` using `CRS.decode` will fail if the required GeoTools EPSG database dependencies are not on the classpath.

### Fix Code Hint
```scala
// FIX: Ensure the CRS Server is running before generating SRIDs for distributed tasks
CRSServer.startServer(sc)
try {
  val myCrs = CRS.decode("EPSG:3857")
  val srid = CRSServer.crsToSRID(myCrs)
  // ... perform distributed Spark operations ...
} finally {
  CRSServer.stopServer(true)
}
```

## API Test: `decodeSpatialParquet`

### Signature
```scala
def decodeSpatialParquet(dataframe: DataFrame, geomColumnName: String): DataFrame
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialParquetSource.scala:69_

_Source doc:_ Decodes a [[DataFrame]] that was encoded using the SpatialParquet format @param dataframe @param geomColumnName @return

### Goal
Decodes a Spark `DataFrame` containing geometry data that was previously encoded in the SpatialParquet format, restoring the spatial geometry column into Beast's native geometry types for downstream geospatial processing.

### Parameters
- `dataframe` (`DataFrame`): The input Spark `DataFrame` containing the encoded SpatialParquet data.
- `geomColumnName` (`String`): The exact name of the column within the `DataFrame` that holds the encoded geometry data (commonly `"geometry"`).

### Input
A Spark `DataFrame` that was either read from a SpatialParquet file or previously encoded in memory using `SpatialParquetSource.encodeSpatialParquet`. The DataFrame must contain the column specified by `geomColumnName`, and that column's binary/encoded contents must conform to the SpatialParquet specification.

### Output
Returns `DataFrame` — A new Spark `DataFrame` where the specified geometry column has been decoded into native spatial geometry objects (e.g., JTS Geometries) that Beast/RDPro can use for spatial joins, partitioning, and raster-vector operations.

### Valid Call Patterns
```scala
// Assuming encodedDataFrame is a DataFrame read from a SpatialParquet source
val decodedDataFrame = SpatialParquetSource.decodeSpatialParquet(encodedDataFrame, "geometry")

// The decoded DataFrame can now be converted to an RDD[IFeature] or used in spatial operations
```

### LLM Instruction Prompt
- When reading SpatialParquet data into a Spark `DataFrame`, you MUST call `SpatialParquetSource.decodeSpatialParquet(df, geomColumnName)` to deserialize the geometry column before performing Beast spatial operations. Do not attempt to parse the binary Parquet geometry column manually. Call it statically on `SpatialParquetSource`.

### Prompt Snippet
```text
To restore geometries from a SpatialParquet DataFrame in Beast, use `SpatialParquetSource.decodeSpatialParquet(df, "geometry")`. The resulting DataFrame contains native geometries ready for spatial processing.
```

### Common Failure Modes
- **Missing Column:** Providing a `geomColumnName` (e.g., `"geom"`) that does not exist in the `dataframe` schema, resulting in an `AnalysisException` from Spark.
- **Invalid Encoding:** Passing a `DataFrame` where the target column contains standard strings or unsupported binary data rather than valid SpatialParquet encoded geometries, causing a deserialization crash.

### Fix Code Hint
```scala
// Verify the column name exists in the schema before decoding
require(encodedDataFrame.columns.contains("geometry"), "Geometry column not found in DataFrame")
val decodedDataFrame = SpatialParquetSource.decodeSpatialParquet(encodedDataFrame, "geometry")
```

## API Test: `diagonal`

### Signature
```scala
def diagonal(cardinality: Long, percentage: Double = 0.5, buffer: Double = 0.2): JavaSpatialRDD
def diagonal(cardinality: Long, percentage: Double = 0.5, buffer: Double = 0.2): SpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:106  (+1 more definition site/overload)_

_Source doc:_ Generate diagonally distributed data @param cardinality the number of records to generate @param percentage the percentage of records exactly on the diagonal line @param buffer the buffer around the diagonal line in which records can be generated @return the RDD that contains the generated data

### Goal
Generate a synthetic spatial dataset where geometries are distributed along a diagonal line, primarily used for benchmarking spatial partitioning and distributed join algorithms (Spider SDG).

### Parameters
- `cardinality` (`Long`): The total number of spatial records (geometries) to generate.
- `percentage` (`Double`), default `0.5`: The fraction of records (from 0.0 to 1.0) placed exactly on the diagonal line.
- `buffer` (`Double`), default `0.2`: The buffer distance around the diagonal line within which the remaining records (not exactly on the line) are randomly scattered.

### Input
Requires an initialized `SparkContext` (`sc`) or `JavaSpatialSparkContext` with Beast context extensions imported. The caller typically configures the spatial generator's Minimum Bounding Rectangle (MBR), geometry type (e.g., points or boxes), and seed using builder methods (`.mbr()`, `.config()`) prior to calling `diagonal`.

### Output
Returns `JavaSpatialRDD` (or `SpatialRDD` in Scala) — a distributed collection of synthetic spatial features (e.g., `IFeature`) distributed diagonally across the configured spatial extent, ready for spatial partitioning, joins, or visualization.

### Valid Call Patterns
```scala
// Pattern 1: Using the SparkContext extension (from README)
val diagonalData: SpatialRDD = sc.generateSpatialData
  .diagonal(1000, percentage = 0.3, buffer = 0.2)

// Pattern 2: Using the builder with explicit MBR and configuration (adapted from test suite)
val desiredMBR = new EnvelopeNDLite(2, 2, 3, 9, 8)
val randomBoxes: SpatialRDD = new SpatialGeneratorBuilder(sc)
  .mbr(desiredMBR)
  .config(UniformDistribution.GeometryType, "box")
  .config(UniformDistribution.MaxSize, "0.2,0.1")
  .config(SpatialGenerator.Seed, 1794)
  .diagonal(10000, 0.6, 0.1)
```

### LLM Instruction Prompt
- Use `sc.generateSpatialData.diagonal(...)` or `new SpatialGeneratorBuilder(sc).diagonal(...)` to create synthetic diagonal datasets for benchmarking spatial operations.
- Always chain `.config(...)` or `.mbr(...)` before calling `diagonal` if you need to control the spatial extent, geometry type (e.g., "box" vs default points), or random seed.
- Ensure `percentage` is between 0.0 and 1.0.

### Prompt Snippet
```text
To generate synthetic diagonal spatial data for benchmarking in Beast, use `sc.generateSpatialData.diagonal(cardinality, percentage, buffer)`. You can configure the bounding box and geometry type by chaining methods before `diagonal`, e.g., `sc.generateSpatialData.mbr(env).config(UniformDistribution.GeometryType, "box").diagonal(1000)`.
```

### Common Failure Modes
- **Missing Context Extensions:** Calling `sc.generateSpatialData` without importing `edu.ucr.cs.bdlab.beast._`, resulting in a compilation error.
- **Unbounded Generation:** Failing to specify an MBR when a specific coordinate reference system or spatial extent is required for downstream joins with real datasets.
- **Invalid Percentage:** Providing a `percentage` value outside the `[0.0, 1.0]` range, which may cause unexpected distributions or runtime errors.

### Fix Code Hint
```scala
// Ensure Beast implicits are imported
import edu.ucr.cs.bdlab.beast._

// Configure the generator before calling diagonal
val syntheticData = sc.generateSpatialData
  .mbr(new EnvelopeNDLite(0, 0, 100, 100)) // Set spatial bounds
  .config(UniformDistribution.GeometryType, "point")
  .diagonal(cardinality = 5000, percentage = 0.8, buffer = 5.0)
```

## API Test: `distribution`

### Signature
```scala
def distribution(distribution: DistributionType): JavaSpatialGeneratorBuilder
def distribution(distribution: DistributionType): SpatialGeneratorBuilder
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:55  (+1 more definition site/overload)_

_Source doc:_ Set the distribution of the generated data @param distribution the distributed of the generated data as one of {[[UniformDistribution]], [[DiagonalDistribution]], [[GaussianDistribution]], [[BitDistribution]], [[SierpinskiDistribution]], [[ParcelDistribution]]} @return

### Goal
Sets the statistical distribution pattern (e.g., Gaussian, Bit, Uniform) for generating synthetic spatial data used in benchmarking and testing distributed algorithms.

### Parameters
- `distribution` (`DistributionType`): The statistical distribution model to apply to the generated spatial data. Must be one of the predefined objects: `UniformDistribution`, `DiagonalDistribution`, `GaussianDistribution`, `BitDistribution`, `SierpinskiDistribution`, or `ParcelDistribution`.

### Input
Requires an active `SparkContext` with Beast context extensions imported (`import edu.ucr.cs.bdlab.beast._`). This method is called on a `SpatialGeneratorBuilder` instance, typically accessed via `sc.generateSpatialData`. No external input files are required as this is a synthetic data generator.

### Output
Returns `SpatialGeneratorBuilder` (or `JavaSpatialGeneratorBuilder` for Java contexts) — a builder object that allows chaining further configurations (like `.config(...)`) before materializing the data into an `RDD[IFeature]` via `.generate(...)`.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast._
import edu.ucr.cs.bdlab.beast.generator._

// Generate random boxes using a Gaussian distribution
val randomBoxes: RDD[IFeature] = sc.generateSpatialData
  .distribution(GaussianDistribution)
  .config(UniformDistribution.GeometryType, "box")
  .config(UniformDistribution.MaxSize, "0.01,0.01")
  .generate(cardinality=10000000)

// Generate random polygons using a Bit distribution
val randomPolygons: RDD[IFeature] = sc.generateSpatialData
  .distribution(BitDistribution)
  .config(UniformDistribution.GeometryType, "polygons")
  .config(UniformDistribution.NumSegments, "20")
  .generate(cardinality=10000000)
```

### LLM Instruction Prompt
- When generating synthetic spatial data for benchmarking, use `sc.generateSpatialData.distribution(...)` to specify the spatial distribution pattern.
- You MUST pass a valid `DistributionType` object (e.g., `GaussianDistribution`, `BitDistribution`), not a string.
- You MUST chain `.generate(cardinality = ...)` at the end of the builder pattern to actually materialize the `RDD[IFeature]`.
- Use `.config(...)` between `.distribution(...)` and `.generate(...)` to set geometry types (e.g., "box", "polygons") and sizes.

### Prompt Snippet
```text
To generate synthetic spatial data with a specific pattern, call `sc.generateSpatialData.distribution(GaussianDistribution)` (or `BitDistribution`, `DiagonalDistribution`, etc.). Chain `.config(...)` for geometry settings, and always terminate the builder with `.generate(cardinality=N)` to return an RDD[IFeature].
```

### Common Failure Modes
- **Missing Terminal Operation:** Forgetting to call `.generate(cardinality = N)` after setting the distribution, which leaves the user with a `SpatialGeneratorBuilder` instead of the expected `RDD[IFeature]`.
- **Invalid Distribution Argument:** Passing a string like `"Gaussian"` instead of the required `DistributionType` object `GaussianDistribution`.
- **Missing Imports:** Failing to import `edu.ucr.cs.bdlab.beast.generator._`, which is required to access the distribution objects like `GaussianDistribution` and `BitDistribution`.

### Fix Code Hint
```scala
// WRONG: Returns a builder, not an RDD, and uses a string for distribution
val badData = sc.generateSpatialData.distribution("GaussianDistribution")

// CORRECT: Uses the DistributionType object and terminates with .generate()
import edu.ucr.cs.bdlab.beast.generator._
val goodData: RDD[IFeature] = sc.generateSpatialData
  .distribution(GaussianDistribution)
  .generate(cardinality = 10000)
```

## API Test: `divideScene`

### Signature
```scala
def divideScene[T: ClassTag](raster: RasterRDD[T], targetMetadata: RasterMetadata, numTilesX: Int, numTilesY: Int): RasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:625_

_Source doc:_ Divides an existing RDD into a new RDD such that every group of tiles is brought together into one Metadata. This is helpful when writing the resulting RDD to files because each group of tiles will be written to a separate file. @param raster the input raster to repartition @param targetMetadata the metadata of the target (output) raster @param numTilesX number of tiles to combine together into one metadata @param numTilesY number of tiles to combine together into one metadata @tparam T @return

### Goal
Repartitions a distributed raster by grouping adjacent tiles together under unified metadata blocks, which is primarily used to control the granularity and number of output files when saving a `RasterRDD` to disk in distributed mode.

### Parameters
- `raster` (`RasterRDD[T]`): The input distributed raster to be repartitioned. The type `T` must match the underlying pixel data type (e.g., `Int`, `Float`).
- `targetMetadata` (`RasterMetadata`): The metadata defining the spatial bounds, CRS, resolution, and base tile dimensions of the target output raster.
- `numTilesX` (`Int`): The number of base tiles along the X-axis (horizontal) to combine together into a single metadata group/partition.
- `numTilesY` (`Int`): The number of base tiles along the Y-axis (vertical) to combine together into a single metadata group/partition.

### Input
- A valid `RasterRDD[T]` loaded via `sc.geoTiff[T]` or generated via other raster operations.
- A `RasterMetadata` object that correctly describes the target grid (often derived from the input raster or constructed manually with matching CRS and resolution).
- The generic type `T` must exactly match the runtime pixel type of the raster (e.g., `Int` for `IntegerType`, `Float` for `FloatType`).

### Output
Returns `RasterRDD[T]` — a repartitioned raster RDD where tiles are grouped into larger blocks (defined by `numTilesX` $\times$ `numTilesY`). When written to disk using a distributed write mode, each of these grouped blocks will be saved as a separate file.

### Valid Call Patterns
```scala
// Assuming `raster` is a RasterRDD[Int] and `targetMetadata` is a RasterMetadata instance
val outputRaster = RasterOperationsFocal.divideScene(raster, targetMetadata, 2, 2)
```

### LLM Instruction Prompt
- Call `divideScene` as a method on the `RasterOperationsFocal` object, NOT as an instance method on the `RasterRDD`.
- Use this function before saving a raster to disk if you need to control the number of output files (e.g., when using `GeoTiffWriter.WriteMode` set to `"distributed"`).
- Ensure the type parameter `T` matches the pixel type of the input raster exactly (e.g., `Int` or `Float`).
- Do not invent a `divideScene` method on `RasterRDD` directly; it will fail to compile.

### Prompt Snippet
```text
To control the number of output files when saving a distributed raster, group the tiles using `RasterOperationsFocal.divideScene(raster, targetMetadata, numTilesX, numTilesY)`. This repartitions the RDD so that each group of tiles shares one Metadata block and writes to a separate file.
```

### Common Failure Modes
- **Method Not Found:** Attempting to call `raster.divideScene(...)` directly on the RDD object instead of using the `RasterOperationsFocal` object.
- **Type Parameter Mismatch:** Providing a `RasterRDD[Float]` but allowing Scala to infer or explicitly passing `[Int]`, causing runtime class cast exceptions.
- **Metadata Misalignment:** Passing a `targetMetadata` that has a different CRS or resolution than the input raster's actual pixels, which can lead to malformed spatial bounds in the output files. (If you need to change resolution or CRS, use `RasterOperationsFocal.reshapeNN` or `reshapeAverage` instead).

### Fix Code Hint
```scala
// WRONG: Calling as an instance method
// val grouped = raster.divideScene(metadata, 4, 4)

// CORRECT: Calling via RasterOperationsFocal
val grouped = RasterOperationsFocal.divideScene(raster, metadata, 4, 4)
```

## API Test: `encodeGeoParquet`

### Signature
```scala
def encodeGeoParquet(dataframe: DataFrame): DataFrame
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialParquetSource.scala:99_

_Source doc:_ Encode the given DataFrame into GeoParquet format by replacing the geometry column with two new columns, MBR and the WKB representation of the geometry. @param dataframe @return

### Goal
Encode a Spark `DataFrame` containing spatial geometries into a GeoParquet-compatible format by replacing the geometry column with its Minimum Bounding Rectangle (MBR) and Well-Known Binary (WKB) representation.

### Parameters
- `dataframe` (`DataFrame`): The input Spark `DataFrame` containing a spatial geometry column to be encoded.

### Input
A Spark `DataFrame` containing spatial features, typically loaded via Spark's DataFrame reader from a supported vector format (e.g., GeoJSON, Shapefile). The DataFrame must contain a valid geometry column that Beast can process.

### Output
Returns `DataFrame` — A transformed Spark DataFrame where the original geometry column has been removed and replaced with two new columns: the MBR (bounding box) and the WKB (Well-Known Binary) byte array representation of the geometry.

### Valid Call Patterns
```scala
// Load a spatial DataFrame (e.g., from GeoJSON)
val dataframe = sparkSession.read.format("geojson").load("path/to/features.geojson")

// Encode the DataFrame for GeoParquet compatibility
val encodedDataFrame = SpatialParquetSource.encodeGeoParquet(dataframe)
```

### LLM Instruction Prompt
- Call `SpatialParquetSource.encodeGeoParquet(df)` to prepare a spatial DataFrame for Parquet serialization.
- Do not call this as an instance method on the DataFrame itself; it is a method on the `SpatialParquetSource` object.
- Understand that the resulting DataFrame will no longer have the original geometry object column, but rather WKB and MBR columns.

### Prompt Snippet
```text
To save spatial DataFrames to Parquet, first encode the geometries to WKB and MBR columns using `val encodedDf = SpatialParquetSource.encodeGeoParquet(df)`.
```

### Common Failure Modes
- **Missing Geometry Column:** Passing a standard, non-spatial DataFrame that lacks a recognized geometry column will cause the encoding process to fail or have no spatial effect.
- **Incorrect Receiver:** Attempting to call `dataframe.encodeGeoParquet()` as if it were an implicit extension method, resulting in a compilation error.

### Fix Code Hint
```scala
// WRONG: dataframe.encodeGeoParquet()
// CORRECT:
val encodedDataFrame = SpatialParquetSource.encodeGeoParquet(dataframe)
```

## API Test: `encodeSpatialParquet`

### Signature
```scala
def encodeSpatialParquet(dataframe: DataFrame): DataFrame
```
_Source doc:_ Parses an existing DataFrame according to the given options that determine the format of the spatial attributes. @param dataframe an existing dataframe @return a dataframe that parses and replaces the spatial attributes with a geometry column

### Goal
Parses an existing Spark DataFrame to identify spatial attributes and encodes them into a standardized geometry column suitable for the Spatial Parquet format.

### Parameters
- `dataframe` (`DataFrame`): An existing Spark DataFrame containing spatial data (e.g., loaded from GeoJSON, CSV, or Shapefile) whose spatial attributes need to be parsed and encoded.

### Input
A Spark `DataFrame` containing spatial features. The DataFrame is typically loaded from a spatial format (like GeoJSON) using Spark's `DataFrameReader` (e.g., `sparkSession.read.format("geojson").load(...)`). The input DataFrame must contain spatial attributes that Beast can parse.

### Output
Returns `DataFrame` — A new Spark DataFrame where the original spatial attributes have been parsed, encoded, and replaced with a standardized geometry column.

### Valid Call Patterns
```scala
// Load a spatial dataset into a DataFrame
val dataframe = sparkSession.read.format("geojson").load("path/to/features.geojson")

// Encode the spatial attributes into a standardized geometry column
val encodedDataFrame = SpatialParquetSource.encodeSpatialParquet(dataframe)
```

### LLM Instruction Prompt
- When preparing a Spark DataFrame for Spatial Parquet storage, use `SpatialParquetSource.encodeSpatialParquet(dataframe)` to parse and replace the spatial attributes with a standardized geometry column.
- Do NOT call this as an instance method on the DataFrame (e.g., `df.encodeSpatialParquet()`); it is a method on the `SpatialParquetSource` object.
- Ensure the input is a valid Spark `DataFrame` containing spatial data.

### Prompt Snippet
```text
To encode spatial attributes in a DataFrame for Spatial Parquet, use `SpatialParquetSource.encodeSpatialParquet(df)`. It takes a DataFrame and returns a new DataFrame with a standardized geometry column. Do not call it as a DataFrame instance method.
```

### Common Failure Modes
- **Method Not Found (Instance Call):** Attempting to call `dataframe.encodeSpatialParquet()` will fail to compile. It must be called on the `SpatialParquetSource` object.
- **Missing Spatial Attributes:** Passing a DataFrame that contains no recognizable spatial attributes or geometry columns, resulting in an output DataFrame with no valid geometry column to decode later.

### Fix Code Hint
```scala
// WRONG: dataframe.encodeSpatialParquet()
// RIGHT:
import edu.ucr.cs.bdlab.beast.io.SpatialParquetSource

val encodedDataFrame = SpatialParquetSource.encodeSpatialParquet(dataframe)
```

## API Test: `end`

### Signature
```scala
def end: Long
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialFilePartition2.scala:26_

### Goal
Retrieves the ending byte offset for a distributed spatial file partition, used internally by Beast's spatial readers for data loading and formatting.

### Parameters
_None._

### Input
An instantiated `SpatialFilePartition2` object. This is an internal plumbing component created by Beast when partitioning large spatial files (such as CSV, GeoJSON, or WKT) into byte-range splits across a Spark cluster.

### Output
Returns `Long` — the absolute byte offset in the underlying file where this specific partition's data segment ends.

### Valid Call Patterns
```scala
// Inferred from signature (not verified by tests/README)
val endOffset: Long = spatialPartition.end
```

### LLM Instruction Prompt
- Use `end` only when interacting with Beast's internal `SpatialFilePartition2` objects (e.g., when writing custom spatial readers or debugging file splits) to determine the byte boundary of a file chunk.
- Do not attempt to call `end` on an `RDD`, `RasterRDD`, or a standard Spark `Partition`. It is specific to Beast's spatial file partition implementation.

### Prompt Snippet
```text
// Inferred usage for internal partition inspection
val partitionEndByte: Long = spatialPartition.end
```

### Common Failure Modes
- **Type Mismatch:** Attempting to call `.end` on a standard Apache Spark `Partition` or an `RDD` object. The `end` method is specific to `SpatialFilePartition2`.
- **User-Facing Confusion:** Trying to use this internal plumbing method for user-facing raster operations (like finding the end of a time-series raster). It strictly represents a file byte offset, not geospatial or temporal metadata.

### Fix Code Hint
```scala
// Ensure the partition is correctly typed as SpatialFilePartition2 before calling end
val sp = partition.asInstanceOf[SpatialFilePartition2]
val offset = sp.end
```

## API Test: `envelope`

### Signature
```scala
def envelope: java.awt.Rectangle
def envelope: Envelope
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/LiteGeometry.scala:24  (+4 more definition site/overload)_

### Goal
Retrieves the spatial bounding box (envelope) that represents the minimum and maximum boundaries of the raster data or geometry in the model space.

### Parameters
_None._

### Input
A spatial object (such as a raster model, raster metadata, or lightweight geometry) that occupies space in a coordinate reference system. 

### Output
Returns `Envelope` (or `java.awt.Rectangle` via overloads) — the minimum bounding box containing the raster data or geometry. An `Envelope` typically represents continuous model-space coordinates (e.g., degrees or meters), while the `java.awt.Rectangle` overloads are often used for discrete pixel-space boundaries or lightweight visualization geometries.

### Valid Call Patterns
```scala
// Note: Example inferred from signature (not verified in test suite).
// The receiver is typically a raster metadata object, tile, or geometry.
val bounds: Envelope = rasterModel.envelope

// For AWT/LiteGeometry overloads:
val pixelBounds: java.awt.Rectangle = liteGeometry.envelope
```

### LLM Instruction Prompt
- Call `.envelope` as a parameterless method (no parentheses) on a valid spatial or raster object to get its bounding box.
- Do not confuse the Scala method `.envelope` with the Beast CSV input format string `"envelope(minX, minY, maxX, maxY)"` used in `sc.spatialFile`.
- Be aware of the return type: depending on the receiver, it may return a Beast/JTS `Envelope` (for geographic model space) or a `java.awt.Rectangle` (for pixel/image space).

### Prompt Snippet
```text
To extract the spatial boundaries of a raster model or geometry in RDPro, use the parameterless `.envelope` method. Ensure you handle the return type correctly, as it may be an `Envelope` (model space) or a `java.awt.Rectangle` (pixel space) depending on the object.
```

### Common Failure Modes
- **Parentheses Error:** Calling `.envelope()` with parentheses will cause a compilation error because it is defined as a parameterless `def`.
- **Type Mismatch:** Assuming `.envelope` always returns a JTS `Envelope`. If called on visualization or pixel-space objects (like `LiteGeometry`), it returns a `java.awt.Rectangle`.
- **Context Confusion:** Attempting to use the Scala method `.envelope` when configuring CSV readers. For CSV loading, use the string format specifier `"envelope(0,1,2,3)"` inside `BeastOptions`, not the Scala method.

### Fix Code Hint
```scala
// WRONG: Using parentheses
val bounds = rasterModel.envelope()

// RIGHT: Parameterless call
val bounds = rasterModel.envelope

// WRONG: Assuming JTS Envelope for AWT objects
val rect: Envelope = liteGeometry.envelope

// RIGHT: Matching the AWT Rectangle overload
val rect: java.awt.Rectangle = liteGeometry.envelope
```

## API Test: `eulerHistogramCount`

### Signature
```scala
def eulerHistogramCount(histogramSize: Array[Int], prefixSum: Boolean = false): AbstractHistogram
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/CGOperationsMixin.scala:98_

_Source doc:_ Computes an Euler histogram that works better for geometries with extents, i.e., envelopes, which calculates the number of records in each cell @param histogramSize the size of the histogram as the number of partitions along each dimension @param prefixSum     compute the prefix sum on the result to speed up range tests @return the created histogram

### Goal
Computes an Euler histogram over a spatial RDD to accurately count the number of records (geometries with extents, such as polygons or envelopes) in each grid cell, properly accounting for features that span multiple cells.

### Parameters
- `histogramSize` (`Array[Int]`): The dimensions of the histogram grid, specified as the number of partitions along each spatial dimension (e.g., `Array(100, 100)` for a 100x100 grid).
- `prefixSum` (`Boolean`), default `false`: If set to `true`, computes the prefix sum on the resulting histogram to accelerate subsequent range tests.

### Input
A `SpatialRDD` (e.g., `RDD[IFeature]`) containing vector geometries loaded from supported formats like Shapefile, GeoJSON, or CSV. This operation is specifically designed for geometries with spatial extents (polygons, lines, envelopes) rather than simple points.

### Output
Returns an `AbstractHistogram` representing the Euler histogram. Unlike simple uniform histograms, this structure maintains four counters per cell (corner, top edge, left edge, overlap) to accurately account for features spanning multiple grid cells without double-counting.

### Valid Call Patterns
```scala
// Compute an Euler histogram with a 100x100 grid
val eulerCountHistogram = polygons.eulerHistogramCount(Array(100, 100))

// Compute an Euler histogram with prefix sum enabled for faster range queries
val eulerCountHistogramPrefix = polygons.eulerHistogramCount(Array(100, 100), prefixSum = true)
```

### LLM Instruction Prompt
- Call `eulerHistogramCount` on a `SpatialRDD` when you need an accurate count of geometries per grid cell for approximate query processing, especially when the dataset contains polygons or envelopes that cross cell boundaries.
- Pass the grid dimensions as an `Array[Int]` matching the dimensionality of the data (typically 2D, e.g., `Array(100, 100)`).
- Be aware of the memory trade-off: Euler histograms consume 4x the memory of simple uniform histograms because they track four counters per cell. Do not use excessively large grid sizes.
- Use `prefixSum = true` if the resulting histogram will be heavily used for range tests.

### Prompt Snippet
```text
To compute an accurate spatial histogram for geometries with extents (polygons/envelopes) that span multiple cells, call `rdd.eulerHistogramCount(Array(numX, numY))`. This returns an `AbstractHistogram` using Euler rules (4 counters per cell) to avoid double-counting. Note that it uses 4x the memory of a uniform histogram.
```

### Common Failure Modes
- **Driver Memory Exhaustion:** Because Euler histograms maintain four counters per cell, providing an excessively large `histogramSize` (e.g., `Array(10000, 10000)`) can cause an `OutOfMemoryError` on the Spark driver when the histogram is collected.
- **Dimensionality Mismatch:** Passing an array with a length that does not match the spatial dimensions of the underlying geometries (e.g., passing a 3D array for 2D data).
- **Using on Point Data:** While it will not fail, using `eulerHistogramCount` on pure point datasets is inefficient. Points do not have extents that span multiple cells, so `uniformHistogramCount` should be used instead to save memory.

### Fix Code Hint
```scala
// If memory issues occur, reduce the histogram size or switch to uniformHistogramCount if the data is purely points
val eulerCountHistogram = polygons.eulerHistogramCount(Array(50, 50), prefixSum = true)
```

## API Test: `eulerHistogramSize`

### Signature
```scala
def eulerHistogramSize(histogramSize: Array[Int], prefixSum: Boolean = false, sizeFunction: IFeature => Int = _.getStorageSize): AbstractHistogram
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/CGOperationsMixin.scala:109_

_Source doc:_ Computes an Euler histogram that works better for geometries with extents, i.e., envelopes, which calculates the total size of features in each cell @param histogramSize the size of the histogram as the number of partitions along each dimension @param prefixSum     compute the prefix sum on the result to speed up range tests @return the created histogram

### Goal
Computes an Euler histogram over a spatial RDD that calculates the total storage size of features in each grid cell, accurately accounting for geometries with spatial extents (like polygons or lines) that span multiple cells.

### Parameters
- `histogramSize` (`Array[Int]`): The dimensions of the histogram grid, specified as the number of partitions/cells along each spatial dimension (e.g., `Array(100, 100)` for a 100x100 grid).
- `prefixSum` (`Boolean`), default `false`: If `true`, computes the prefix sum on the resulting histogram to speed up subsequent range tests and cumulative queries.
- `sizeFunction` (`IFeature => Int`), default `_.getStorageSize`: A function to determine the "size" or weight of each feature. By default, it uses the byte storage size of the feature.

### Input
A spatial Vector RDD (`RDD[IFeature]`) containing geometries (such as polygons, lines, or envelopes) loaded via context extensions like `sc.shapefile` or `sc.geojsonFile`. This method is specifically designed for geometries with spatial extents; while it works on points, its primary benefit is correctly handling features that cross grid cell boundaries.

### Output
Returns `AbstractHistogram` — an Euler histogram object representing the spatial distribution of the dataset's size. Unlike simple histograms, this Euler histogram maintains four counters per cell (corner, top edge, left edge, overlap) to accurately account for features spanning multiple grid cells without double-counting.

### Valid Call Patterns
```scala
val eulerSizeHistogram = polygons.eulerHistogramSize(Array(100, 100))

// With prefix sum enabled
val prefixEulerHistogram = polygons.eulerHistogramSize(Array(100, 100), prefixSum = true)
```

### LLM Instruction Prompt
- Call `eulerHistogramSize` on an `RDD[IFeature]` when you need to estimate the spatial distribution of data *size* (bytes) across a grid, especially for polygons or lines that span multiple cells.
- Pass the grid dimensions as an `Array[Int]` (e.g., `Array(100, 100)`).
- Remember that Euler histograms consume 4x the memory of uniform histograms because they track four counters per cell. Keep the `histogramSize` dimensions reasonable to avoid driver memory exhaustion.
- Do not use this on `RasterRDD`; it is strictly a Vector RDD operation.

### Prompt Snippet
```text
To compute a size-based Euler histogram on a spatial RDD `features` for a 100x100 grid:
val histogram = features.eulerHistogramSize(Array(100, 100))
```

### Common Failure Modes
- **Driver Memory Exhaustion (OOM):** Requesting an excessively large grid size (e.g., `Array(10000, 10000)`). Because Euler histograms maintain four counters per cell, they incur a 4x memory cost compared to standard histograms. The resulting `AbstractHistogram` is collected to the driver.
- **Type Mismatch:** Attempting to call this on a `RasterRDD` or a standard Spark `RDD[String]`. It must be called on an `RDD[IFeature]`.

### Fix Code Hint
```scala
// Ensure the input is a vector RDD and keep grid dimensions reasonable to avoid OOM
val features: RDD[IFeature] = sc.shapefile("polygons.zip")
val eulerSizeHistogram = features.eulerHistogramSize(Array(100, 100))
```

## API Test: `explode`

### Signature
```scala
def explode: RasterRDD[T]
def explode[T](inputRaster: RasterRDD[T]): RasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsLocal.scala:76  (+1 more definition site/overload)_

_Source doc:_ Returns a new RasterRDD where each tile is in its own raster. @param inputRaster the raster data to explore @tparam T @return a new raster RDD with the same number of tiles but each tile is in a separate raster

### Goal
Splits a distributed raster dataset so that each internal tile becomes its own independent raster with distinct metadata.

### Parameters
- `inputRaster` (`RasterRDD[T]`): The tiled raster dataset to be exploded into separate rasters.

### Input
A `RasterRDD[T]` loaded from a GeoTIFF or HDF file, or generated via pixel rasterization. The type parameter `T` must exactly match the runtime pixel type of the raster (e.g., `Int`, `Float`, `Array[Int]`, `Array[Float]`).

### Output
Returns `RasterRDD[T]` representing a new raster RDD with the exact same number of tiles as the input, but where each tile is now encapsulated as an isolated raster with its own `RasterMetadata`.

### Valid Call Patterns
```scala
// Object function call (verified from test suite)
val outputRaster = RasterOperationsLocal.explode(raster)

// Implicit method call (from project context)
val outputRaster = raster.explode
```

### LLM Instruction Prompt
- Use `explode` when you need to break a large, multi-tile raster into individual rasters (e.g., to write each tile to a separate file).
- You can call it as a method on the RDD (`raster.explode`) or via the object (`RasterOperationsLocal.explode(raster)`).
- When saving the output of `explode` to disk, you MUST configure `GeoTiffWriter.WriteMode` to `"distributed"` so that each exploded raster tile is written to a separate file.

### Prompt Snippet
```text
To split a raster into individual files per tile, use `raster.explode` or `RasterOperationsLocal.explode(raster)`. Always follow `explode` with a distributed save operation by ensuring `GeoTiffWriter.WriteMode` is set to `"distributed"`.
```

### Common Failure Modes
- **Incorrect Write Mode:** Saving an exploded `RasterRDD` using the `"compatibility"` write mode. Because `explode` assigns distinct metadata to every single tile, writing in compatibility mode (which attempts to write a single file) defeats the purpose of the operation and may cause metadata conflicts. Always use `"distributed"` mode after exploding.
- **Type Mismatch:** Calling `explode` on a `RasterRDD[T]` where `T` does not match the underlying pixel type (e.g., using `Int` for a `FloatType` raster).

### Fix Code Hint
```scala
// Correct usage: explode and save as distributed files
val explodedRaster = raster.explode

// Ensure the write mode is set to distributed before saving
sparkContext.hadoopConfiguration.set("GeoTiffWriter.WriteMode", "distributed")
explodedRaster.saveAsGeoTiff("exploded_output_directory")
```

## API Test: `extents`

### Signature
```scala
def extents: Geometry
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:181  (+1 more definition site/overload)_

_Source doc:_ Returns a polygon that represents the boundaries of this tile in the model space. @return a polygon (rectangle) that represents the boundaries of this tile

### Goal
Returns a rectangular polygon that represents the exact spatial boundaries (footprint) of a raster tile or dataset in the model space (Coordinate Reference System).

### Parameters
_None._

### Input
A valid `RasterMetadata` instance (typically accessed via a `GeoTiffReader`'s `.metadata` property or an `ITile`'s metadata) that contains the raster's grid dimensions, resolution, and affine transformation.

### Output
Returns `Geometry` — A JTS `Geometry` object (specifically a rectangular polygon) representing the spatial extent of the raster tile in model coordinates.

### Valid Call Patterns
```scala
// Inferred from signature and sibling RasterMetadata tests (not verified)
val rasterPath = new Path("/rasters/FRClouds.tif")
val fileSystem = rasterPath.getFileSystem(new Configuration())
val reader = new GeoTiffReader[Array[Int]]
reader.initialize(fileSystem, rasterPath.toString, "0", new BeastOptions())

// Retrieve the spatial boundary of the raster in model space
val boundary: Geometry = reader.metadata.extents
```

### LLM Instruction Prompt
- Call `extents` as a parameterless method (without parentheses) on a `RasterMetadata` instance.
- Expect a JTS `Geometry` (a polygon) as the return type, not a simple bounding box array or `Envelope`.
- Use this method when you need to extract the spatial footprint of a raster tile to perform geometric operations, such as checking intersections with vector polygons during Raptor joins or spatial filtering.

### Prompt Snippet
```text
To get the spatial bounding box of a raster tile in model space, call `metadata.extents` on its `RasterMetadata` to receive a JTS `Geometry` polygon.
```

### Common Failure Modes
- **Type Mismatch:** Attempting to assign the result to an `Envelope`, `BoundingBox`, or `Array[Double]` instead of a JTS `Geometry`.
- **Syntax Error:** Calling the method with parentheses `extents()`, which may cause compilation errors in strict Scala environments since it is defined without them.

### Fix Code Hint
```scala
// WRONG: Assigning to Envelope and using parentheses
// val bbox: Envelope = reader.metadata.extents()

// CORRECT: Assigning to Geometry without parentheses
val bbox: Geometry = reader.metadata.extents
```

## API Test: `extractTables`

### Signature
```scala
def extractTables(sql: String): Set[String]
```
_Source: beast/dataExplorer/src/main/scala/edu/ucr/cs/bdlab/beast/dataExplorer/SQLQueryHelper.scala:22_

_Source doc:_ Checks if an SQL query is syntactically correct and extracts table names from it. @param sql The SQL query string to be analyzed. @return Either an error message as a string if the query is incorrect, or a set of table names if the query is correct.

### Goal
Parses a given SQL query string to verify its syntax and extracts the set of referenced table names, typically used in data exploration to determine which datasets need to be loaded.

### Parameters
- `sql` (`String`): The SQL query string to be analyzed for syntax correctness and table references.

### Input
A standard SQL query string. No specific Spark RDDs or file formats are required as inputs, as this is a purely string-based parsing utility.

### Output
Returns `Set[String]` — A collection of unique table names extracted from the `FROM` and `JOIN` clauses of the provided SQL query.

### Valid Call Patterns
```scala
// Extracting tables from a valid SQL query
val validSQL = "SELECT * FROM users"
val tables: Set[String] = SQLQueryHelper.extractTables(validSQL)
```

### LLM Instruction Prompt
- Always call this method using the `SQLQueryHelper` object qualifier: `SQLQueryHelper.extractTables(sql)`.
- Do not attempt to pass Spark contexts or RDDs to this function; it strictly takes a single `String`.
- Be aware that if the SQL string is syntactically invalid, the function will throw a `SqlParseException` rather than returning an error string (despite the source doc's phrasing, the signature strictly returns `Set[String]`).

### Prompt Snippet
```text
Use `SQLQueryHelper.extractTables(sqlString)` to parse an SQL query and retrieve a `Set[String]` of referenced table names. Wrap the call in a try-catch block for `SqlParseException` if the SQL input is untrusted or potentially malformed.
```

### Common Failure Modes
- **Invalid SQL Syntax:** Passing a malformed SQL string (e.g., misspelled keywords like `"SELEC * FROM users"`) will cause the parser to fail and throw a `SqlParseException`.

### Fix Code Hint
```scala
import edu.ucr.cs.bdlab.beast.dataExplorer.SQLQueryHelper

val query = "SELEC * FROM users" // Malformed SQL

try {
  val tables = SQLQueryHelper.extractTables(query)
  println(s"Tables found: $tables")
} catch {
  case e: Exception => // Catches SqlParseException
    println(s"Failed to parse SQL query: ${e.getMessage}")
}
```

## API Test: `filterPixels`

### Signature
```scala
def filterPixels(f: T => Boolean)
def filterPixels[T: ClassTag](inputRaster: RasterRDD[T], filter: T => Boolean): RasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsLocal.scala:48  (+1 more definition site/overload)_

_Source doc:_ Retains only the pixels that pass the user-defined filter and clears all other pixels (set to empty) @param inputRaster the input raster @param filter the filter function that tells which pixel values to keep in the output @tparam T the thpe of the pixels in the input @return a new raster where only pixels that pass the test are retained

### Goal
Retains only the pixels in a distributed raster dataset that satisfy a user-defined boolean condition, setting all other pixels to empty (NoData) for downstream masking or zonal statistics.

### Parameters
- `inputRaster` (`RasterRDD[T]`): The input distributed raster dataset. When called as an extension method (`raster.filterPixels(...)`), the raster itself is the implicit receiver.
- `filter` (`T => Boolean`): A serializable closure/function evaluated against each pixel's value. If it returns `true`, the pixel is kept; if `false`, the pixel is cleared (set to empty).

### Input
- A `RasterRDD[T]` typically loaded from a GeoTIFF (`sc.geoTiff[T]`) or HDF file (`sc.hdfFile`).
- **Precondition (Type Selection):** The type parameter `T` must exactly match the runtime pixel type of the source file (e.g., `Int` for `IntegerType`, `Float` for `FloatType`).
- The `filter` function must be fully serializable to execute across the Spark cluster.

### Output
Returns `RasterRDD[T]` — A new distributed raster dataset with identical metadata (resolution, CRS, tile size) where pixels failing the filter condition are marked as empty. The output can be saved directly (`saveAsGeoTiff`) or passed into a Raptor join (`raptorJoinFeature`).

### Valid Call Patterns
```scala
// Pattern 1: Idiomatic extension method (from README)
val raster: RasterRDD[Int] = sc.geoTiff[Int]("glc2000_v1_1.tif")
val trees = raster.filterPixels(lc => lc >= 1 && lc <= 10)

// Pattern 2: Chained with save operation (from README)
val temperatureK: RasterRDD[Float] = sc.hdfFile("MOD11A1.hdf", "LST_Day_1km")
temperatureK.filterPixels(_ > 300f).saveAsGeoTiff("temperature_high")

// Pattern 3: Explicit object call (from Test Suite)
val outputRaster: RDD[ITile[Short]] = RasterOperationsLocal.filterPixels(inputRaster, (x: Short) => x < 50)
```

### LLM Instruction Prompt
- Prefer the extension method syntax `raster.filterPixels(condition)` over the explicit `RasterOperationsLocal` object call.
- Ensure the lambda function's input type strictly matches the `RasterRDD[T]` type parameter (e.g., use `Float` literals like `300f` if `T` is `Float`).
- Do not invent spatial parameters for this function; it operates purely on pixel values, not coordinates.
- Use this function to mask rasters before performing a `raptorJoin` to significantly reduce the data volume processed during the join.

### Prompt Snippet
```text
RDPro `filterPixels(f: T => Boolean)` masks a RasterRDD by keeping only pixels where `f` returns true, setting the rest to empty. Use the extension method `raster.filterPixels(x => x > 10)`. The type `T` must match the raster's pixel type (e.g., Int, Float). Ideal for isolating specific land cover classes or thresholding indices before a `raptorJoin`.
```

### Common Failure Modes
- **Type Mismatch:** Providing a filter function that expects a `Double` or `Int` when the `RasterRDD` is typed as `Float`. The compiler will fail to resolve the extension method or type-check the closure.
- **Serialization Errors (Task not serializable):** Referencing non-serializable objects (like an active SparkContext or un-serializable class instances) inside the `filter` closure.
- **Assuming Spatial Context:** Attempting to filter by X/Y coordinates. `filterPixels` only receives the pixel *value* (`T`), not its spatial location.

### Fix Code Hint
```scala
// BAD: Type mismatch (comparing Float to Double literal, or wrong RDD type)
val temp: RasterRDD[Float] = sc.geoTiff[Float]("temp.tif")
val hot = temp.filterPixels(x => x > 300.0) // 300.0 is Double, x is Float

// GOOD: Match the literal type to the RasterRDD type
val temp: RasterRDD[Float] = sc.geoTiff[Float]("temp.tif")
val hot = temp.filterPixels(x => x > 300.0f)

// GOOD: Filtering integer land cover classes
val landCover: RasterRDD[Int] = sc.geoTiff[Int]("lc.tif")
val forest = landCover.filterPixels(c => c == 1 || c == 2)
```

## API Test: `findTransformationInfo`

### Signature
```scala
def findTransformationInfo(sourceCRS: CoordinateReferenceSystem, targetCRS: CoordinateReferenceSystem): TransformationInfo
def findTransformationInfo(sourceSRID: Int, targetSRID: Int): TransformationInfo
def findTransformationInfo(sourceSRID: Int, targetCRS: CoordinateReferenceSystem): TransformationInfo
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/Reprojector.scala:146  (+2 more definition site/overload)_

_Source doc:_ Creates or retrieves a cached math transform to transform between the given two CRS @param sourceCRS source coordinate reference system @param targetCRS target coordinate reference system @return the math transformation that transforms from source to destination

### Goal
Creates or retrieves a cached mathematical transformation to convert coordinates, geometries, or raster metadata between a source and target Coordinate Reference System (CRS).

### Parameters
- `sourceCRS` (`CoordinateReferenceSystem`): The source coordinate reference system. Can also be provided as an integer SRID/EPSG code (e.g., `4326`) via overloads.
- `targetCRS` (`CoordinateReferenceSystem`): The target coordinate reference system. Can also be provided as an integer SRID/EPSG code via overloads.

### Input
- Requires valid source and target CRSs, provided either as instantiated `CoordinateReferenceSystem` objects (e.g., from GeoTools) or standard integer SRIDs (e.g., `4326` for WGS84, `26911` for NAD83 / UTM zone 11N).
- **Precondition:** The underlying referencing engine must be able to find a valid mathematical transformation path between the two systems. 

### Output
Returns `TransformationInfo` — An object containing the cached math transformation required to reproject geometries or raster metadata from the source CRS to the destination CRS.

### Valid Call Patterns
```scala
// Using integer SRIDs (EPSG codes)
val transformInfo = Reprojector.findTransformationInfo(26911, 4326)

// Using a mix of SRID and a custom CoordinateReferenceSystem object
val targetCRS: CoordinateReferenceSystem = new DefaultProjectedCRS("Sinusoidal", ...)
val transform = Reprojector.findTransformationInfo(4326, targetCRS)
```

### LLM Instruction Prompt
- ALWAYS call this method on the `Reprojector` object (i.e., `Reprojector.findTransformationInfo(...)`). It is not a standalone function or an RDD method.
- Prefer the `(Int, Int)` overload when dealing with standard EPSG codes (like `4326`) for simplicity and readability.
- Do not invent custom `CoordinateReferenceSystem` objects unless explicitly required by the prompt; use standard integer SRIDs where possible.
- Use the returned `TransformationInfo` with `Reprojector.reprojectGeometry` to actually perform the coordinate conversion.

### Prompt Snippet
```text
To get a transformation between two CRSs, use `Reprojector.findTransformationInfo(sourceSRID, targetSRID)`. It returns a `TransformationInfo` object. You can pass integer EPSG codes (like 4326) or GeoTools `CoordinateReferenceSystem` objects. Always call it on the `Reprojector` object.
```

### Common Failure Modes
- **Calling without the Object Qualifier:** Attempting to call `findTransformationInfo` as a bare function or on an RDD instead of the `Reprojector` object will cause a compilation error.
- **Invalid/Unknown SRID:** Passing an integer SRID that does not exist in the EPSG registry will cause a runtime failure when the referencing engine attempts to look it up.
- **No Transform Path:** Attempting to transform between two highly incompatible or custom CRSs where no mathematical transform can be derived by the referencing factory.

### Fix Code Hint
```scala
// BAD: Calling without the Reprojector object qualifier
val t = findTransformationInfo(26911, 4326)

// GOOD: Call on the Reprojector object
val t = Reprojector.findTransformationInfo(26911, 4326)

// GOOD: Using the result to reproject a geometry
val convertedPoint = Reprojector.reprojectGeometry(point, t)
```

## API Test: `flatten`

### Signature
```scala
def flatten[T](raster: RasterRDD[T]): RDD[(Int, Int, RasterMetadata, T)]
def flatten: RDD[(Int, Int, RasterMetadata, T)]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsGlobal.scala:69  (+1 more definition site/overload)_

_Source doc:_ Extract all pixel values into an RDD @param raster the raster to extract its pixels @tparam T the type of pixel values @return an RDD that contains all pixel locations and values

### Goal
Extract all individual pixel values and their spatial grid coordinates from a distributed `RasterRDD` into a flat Spark `RDD` of tuples.

### Parameters
- `raster` (`RasterRDD[T]`): The distributed raster dataset (e.g., loaded from GeoTIFF/HDF or resulting from a focal/math operation) from which to extract individual pixels.

### Input
A `RasterRDD[T]` containing tiled raster data. The type parameter `T` must exactly match the runtime pixel type of the underlying data (e.g., `Int` for `IntegerType`, `Float` for `FloatType`). This operation is typically called after loading a raster via `sc.geoTiff[T]` or after performing pixel math/focal operations.

### Output
Returns `RDD[(Int, Int, RasterMetadata, T)]` — A distributed Spark RDD where each record represents a single pixel. The tuple contains:
1. `Int`: The X coordinate (column index) of the pixel.
2. `Int`: The Y coordinate (row index) of the pixel.
3. `RasterMetadata`: The metadata of the specific raster tile this pixel belongs to.
4. `T`: The actual pixel value.

### Valid Call Patterns
```scala
// Pattern 1: Using the implicit extension method on a RasterRDD
val flatPixels: RDD[(Int, Int, RasterMetadata, Float)] = raster.flatten

// Pattern 2: Using the global object (as seen in the test suite)
val finalPixels: Map[(Int, Int), Double] = RasterOperationsGlobal.flatten(smoothedRaster)
  .map(x => ((x._1, x._2), x._4))
  .collectAsMap()
  .toMap
```

### LLM Instruction Prompt
- Use `flatten` when you need to break a tiled `RasterRDD` into individual pixel records for non-raster distributed processing, filtering by specific pixel coordinates, or exporting to flat formats like CSV.
- The output is an `RDD[(Int, Int, RasterMetadata, T)]`. To get just the coordinates and values, map over the RDD and extract `_1`, `_2`, and `_4`.
- **Warning:** Flattening a large satellite image creates a massive RDD (one row per pixel). Never call `.collect()` directly on the flattened RDD without aggressive filtering or aggregation first.

### Prompt Snippet
```text
RDPro `flatten` extracts all pixels from a RasterRDD[T] into an RDD[(Int, Int, RasterMetadata, T)] containing (x, y, metadata, value). Call it via `raster.flatten` or `RasterOperationsGlobal.flatten(raster)`. Use this to convert tiled rasters into flat coordinate-value pairs. Avoid collecting the raw output on large rasters to prevent driver OOM.
```

### Common Failure Modes
- **Driver OutOfMemoryError (OOM):** Calling `.collect()` or `.collectAsMap()` immediately after `flatten` on a full-scale GeoTIFF. A standard 10,000 x 10,000 satellite tile contains 100 million pixels; collecting this to the Spark driver will crash it. Always filter or aggregate first.
- **Type Mismatch:** Assuming the pixel value `T` is a `Double` when the underlying GeoTIFF was loaded as `sc.geoTiff[Int]`. The type `T` in the output tuple strictly follows the `RasterRDD[T]` type.

### Fix Code Hint
```scala
// BAD: Crashes the driver with OOM on large rasters
val allPixels = raster.flatten.collect()

// GOOD: Filter for specific values or coordinates before collecting, or save distributedly
val highValues = raster.flatten
  .filter { case (x, y, metadata, value) => value > 100.0f }
  .map { case (x, y, metadata, value) => s"$x,$y,$value" }

highValues.saveAsTextFile("high_values_output")
```

## API Test: `gaussian`

### Signature
```scala
def gaussian(cardinality: Long): JavaSpatialRDD
def gaussian(cardinality: Long): SpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:117  (+1 more definition site/overload)_

_Source doc:_ Generate Gaussian distributed data @param cardinality the number of records to generate @return the RDD that contains the generated data

### Goal
Generate a distributed spatial dataset containing geometries distributed according to a Gaussian (normal) distribution, typically used for benchmarking spatial algorithms and systems (part of the Spider Spatial Data Generator).

### Parameters
- `cardinality` (`Long`): The total number of spatial records (geometries) to generate across the Spark cluster.

### Input
Requires an initialized SparkContext (`sc`) and a spatial generator builder instance (obtained via the context extension `sc.generateSpatialData` or by instantiating `new SpatialGeneratorBuilder(sc)`). Any desired configurations—such as the Minimum Bounding Rectangle (MBR), geometry type, or random seed—must be chained *before* calling `gaussian`.

### Output
Returns `SpatialRDD` (or `JavaSpatialRDD` in the Java API) — A distributed collection of generated spatial features (`IFeature`) whose spatial locations follow a Gaussian distribution.

### Valid Call Patterns
```scala
// Pattern 1: Using the SparkContext extension (from README)
val gaussianData: SpatialRDD = sc.generateSpatialData
  .gaussian(1000)

// Pattern 2: Using SpatialGeneratorBuilder with explicit configurations (adapted from test suite)
val desiredMBR = new EnvelopeNDLite(2, 2, 3, 9, 8)
val randomPoints: SpatialRDD = new SpatialGeneratorBuilder(sc)
  .mbr(desiredMBR)
  .config(SpatialGenerator.Seed, 1794)
  .gaussian(10000L)
```

### LLM Instruction Prompt
- When generating synthetic spatial data for benchmarking, use `sc.generateSpatialData.gaussian(cardinality)` or `new SpatialGeneratorBuilder(sc).gaussian(cardinality)`. Always chain configuration methods (like `.mbr()` or `.config()`) *before* calling `.gaussian()`, because `gaussian` executes the generation and returns the `SpatialRDD`, terminating the builder chain.

### Prompt Snippet
```text
To generate Gaussian-distributed spatial data, use `sc.generateSpatialData.gaussian(cardinality)`. Chain configurations like `.mbr(envelope)` or `.config(key, value)` before calling `gaussian()`.
```

### Common Failure Modes
- **Chaining order errors:** Attempting to call builder configuration methods (like `.mbr()` or `.config()`) *after* calling `.gaussian()`. The `gaussian` method returns a `SpatialRDD`, which does not possess the builder methods, resulting in a compilation error.
- **Missing SparkContext:** Attempting to call `gaussian` without an active, initialized SparkContext (`sc`).

### Fix Code Hint
```scala
// WRONG: Calling builder methods after generation
// val badData = sc.generateSpatialData.gaussian(1000).mbr(new EnvelopeNDLite(0, 0, 10, 10))

// RIGHT: Configure the builder first, then generate
val goodData = sc.generateSpatialData
  .mbr(new EnvelopeNDLite(0, 0, 10, 10))
  .config(SpatialGenerator.Seed, 42)
  .gaussian(1000)
```

## API Test: `generate`

### Signature
```scala
def generate(cardinality: Long): JavaSpatialRDD
def generate(cardinality: Long): SpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:87  (+1 more definition site/overload)_

_Source doc:_ Generate the data as an RDD. @param cardinality the number of records to generate @return the RDD that contains the generated data

### Goal
Generate a distributed spatial dataset (SpatialRDD) of a specified size for benchmarking or testing, using previously configured statistical distributions and geometry types.

### Parameters
- `cardinality` (`Long`): The total number of spatial records (features) to generate across the Spark cluster.

### Input
Requires an initialized `SparkContext` (or `JavaSpatialSparkContext`) and a configured spatial generator builder. The builder is typically accessed via the context extension `sc.generateSpatialData` or instantiated directly via `new SpatialGeneratorBuilder(sc)`. Before calling `generate`, the builder should be configured with a spatial distribution (e.g., `GaussianDistribution`, `BitDistribution`) and geometry properties (e.g., `UniformDistribution.GeometryType`, `UniformDistribution.MaxSize`, `UniformDistribution.NumSegments`) using chained `.config(...)` and `.distribution(...)` calls.

### Output
Returns `SpatialRDD` (Scala) or `JavaSpatialRDD` (Java) — an RDD of `IFeature` objects representing the randomly generated spatial geometries (points, boxes, or polygons) distributed across the cluster partitions.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast._
import edu.ucr.cs.bdlab.beast.generator._

// Generate 10 million random boxes using a Gaussian distribution
val randomBoxes: SpatialRDD = sc.generateSpatialData
  .distribution(GaussianDistribution)
  .config(UniformDistribution.GeometryType, "box")
  .config(UniformDistribution.MaxSize, "0.01,0.01")
  .generate(cardinality=10000000L)

// Generate 10 million random polygons using a Bit distribution
val randomPolygons: SpatialRDD = sc.generateSpatialData
  .distribution(BitDistribution)
  .config(UniformDistribution.GeometryType, "polygons")
  .config(UniformDistribution.NumSegments, "20")
  .generate(cardinality=10000000L)
```

### LLM Instruction Prompt
- When generating synthetic spatial data for benchmarking in Beast, use `sc.generateSpatialData` to access the builder.
- Chain `.distribution(...)` and `.config(...)` to define the geometry type ("box", "polygons") and distribution parameters before calling `.generate(cardinality)`.
- Ensure the `cardinality` parameter is a `Long`.
- The output is a `SpatialRDD` (which is an alias for `RDD[IFeature]`).

### Prompt Snippet
```text
To generate synthetic spatial data in Beast, use `sc.generateSpatialData.config(...).generate(cardinality)`. Configure the geometry type (e.g., "box", "polygons") and distribution before calling `generate`. The `cardinality` must be a Long. Returns a SpatialRDD.
```

### Common Failure Modes
- **Missing Configuration:** Calling `generate` without first configuring the `GeometryType` or `NumSegments` will result in default geometries (typically points) being generated instead of the desired complex shapes.
- **Type Mismatch on Cardinality:** Passing an `Int` that exceeds the maximum integer value instead of a `Long` literal (e.g., `10000000000` instead of `10000000000L`), causing compilation errors.
- **Unbounded Generation:** Generating an excessively large cardinality without sufficient cluster memory or partitions, leading to OutOfMemory errors during subsequent actions.

### Fix Code Hint
```scala
// BAD: Calling generate without configuration or with an overflowing Int
val badData = sc.generateSpatialData.generate(3000000000)

// GOOD: Configuring the builder first and using a Long literal
val goodData = sc.generateSpatialData
  .config(UniformDistribution.GeometryType, "box")
  .config(UniformDistribution.MaxSize, "0.1,0.1")
  .generate(3000000000L)
```

## API Test: `generateSpatialData`

### Signature
```scala
def generateSpatialData(distribution: DistributionType, cardinality: Long, numPartitions: Int = 0, opts: BeastOptions = new BeastOptions) : SpatialRDD
def generateSpatialData: SpatialGeneratorBuilder
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:139  (+1 more definition site/overload)_

_Source doc:_ Return a [[SpatialRDD]] of randomly generated geometries according to the given options. @param distribution the type of distribution {[[UniformDistribution]], [[DiagonalDistribution]], [[GaussianDistribution]], [[SierpinskiDistribution]], [[BitDistribution]], [[ParcelDistribution]]} @param cardinality the number of geometries to generate @param opts additional options depending on the type of generator @return an RDD with the generated geometries

### Goal
Generate a `SpatialRDD` of synthetic, randomly distributed geometries (points, boxes, etc.) across a Spark cluster, primarily used for benchmarking, stress-testing spatial joins, and evaluating partitioning algorithms.

### Parameters
- `distribution` (`DistributionType`): The statistical spatial distribution to use for generating geometries. Supported values include `UniformDistribution`, `DiagonalDistribution`, `GaussianDistribution`, `SierpinskiDistribution`, `BitDistribution`, and `ParcelDistribution`.
- `cardinality` (`Long`): The total number of geometries to generate across the entire dataset.
- `numPartitions` (`Int`), default `0`: The number of Spark partitions to divide the generated data into. If `0`, it typically falls back to Spark's default parallelism.
- `opts` (`BeastOptions`), default `new BeastOptions`: Additional configuration options for the generator (e.g., random seed, maximum geometry size, or geometry type). Can often be passed as a `Seq` of key-value pairs due to implicit conversions in Beast.

### Input
Requires an initialized `SparkContext` (`sc`) with Beast context extensions loaded (e.g., `import edu.ucr.cs.bdlab.beast._`). No external files or datasets are required, as the data is generated entirely in-memory by the Spider Spatial Data Generator (SDG) component.

### Output
Returns `SpatialRDD` — A distributed Spark RDD containing the generated spatial features (`IFeature`), which can then be used in downstream operations like `spatialPartition`, `spatialJoin`, or saved to disk.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast._
import edu.ucr.cs.bdlab.beast.generator.UniformDistribution

// Generate 100 uniformly distributed box geometries
val syntheticData: SpatialRDD = sc.generateSpatialData(
  UniformDistribution, 
  100, 
  opts = Seq(
    "seed" -> 42, 
    UniformDistribution.MaxSize -> "0.1,0.1", 
    "geometry" -> "box"
  )
)
```

### LLM Instruction Prompt
- Use `sc.generateSpatialData` when the user needs to create synthetic spatial datasets for benchmarking or testing distributed algorithms.
- Always provide a valid `DistributionType` (e.g., `UniformDistribution`) and the total `cardinality`.
- Pass generator-specific configurations (like `"geometry" -> "box"`, `"seed"`, or `MaxSize`) via the `opts` parameter. Note that Beast supports passing a `Seq[(String, Any)]` for `opts` in Scala.
- Ensure Beast implicits are in scope so the `SparkContext` has the `generateSpatialData` extension method.

### Prompt Snippet
```text
Generate a synthetic dataset of 1,000,000 uniformly distributed spatial boxes to stress-test the PBSM spatial join algorithm. Use a random seed of 1.
```

### Common Failure Modes
- **Missing Context Extensions:** Calling `sc.generateSpatialData` without importing `edu.ucr.cs.bdlab.beast._` will result in a compilation error (`value generateSpatialData is not a member of org.apache.spark.SparkContext`).
- **Out of Memory (OOM):** Generating a massive `cardinality` with `numPartitions` set to a very low number (or default 0 on a local master) can cause individual Spark tasks to run out of memory.
- **Invalid Options:** Providing unrecognized geometry types or malformed `MaxSize` strings in the `opts` parameter may cause runtime parsing exceptions in the generator.

### Fix Code Hint
```scala
// ERROR: value generateSpatialData is not a member of org.apache.spark.SparkContext
// FIX: Ensure Beast implicits are imported
import edu.ucr.cs.bdlab.beast._
import edu.ucr.cs.bdlab.beast.generator.UniformDistribution

val data = sc.generateSpatialData(UniformDistribution, 1000000L, numPartitions = 100)
```

## API Test: `geoTiff`

### Signature
```scala
def geoTiff[T](path: String, iLayer: Int = 0, opts: BeastOptions = new BeastOptions): RDD[ITile[T]]
def geoTiff[T](filename: String, layer: Int, opts: BeastOptions): JavaRasterRDD[T]
def geoTiff[T](filename: String, layer: Int): JavaRasterRDD[T]
def geoTiff[T](filename: String): JavaRasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:40  (+3 more definition site/overload)_

_Source doc:_ Loads a GeoTIFF file as an RDD of tiles @param path the path of the file @param iLayer the index of the band to load (0 by default) @param opts additional options for loading the file @return a [[RasterRDD]] that represents all tiles in the file

### Goal
Loads a GeoTIFF file into a distributed Spark RDD of raster tiles for scalable pixel-level math, reshaping, or raster-vector joins.

### Parameters
- `path` (`String`): The file path or directory containing the GeoTIFF file(s) to load.
- `iLayer` (`Int`), default `0`: The 0-based index of the raster band/layer to load.
- `opts` (`BeastOptions`), default `new BeastOptions`: Additional configuration options for loading the file.

### Input
A valid GeoTIFF file accessible to the Spark cluster. The caller must know the runtime pixel type of the GeoTIFF to provide the correct type parameter `[T]`. The operation requires an initialized `SparkContext` (or `JavaSpatialSparkContext`) with Beast context extensions loaded.

### Output
Returns `RDD[ITile[T]]` — a distributed collection of raster tiles representing the loaded band of the GeoTIFF file, where `T` is the underlying pixel data type (e.g., `Int`, `Float`).

### Valid Call Patterns
```scala
// Explicitly typed method call (recommended)
val raster: RasterRDD[Int] = sc.geoTiff[Int]("glc2000_v1_1.tif")

// Type inferred from the variable declaration
val treecover: RDD[ITile[Float]] = sc.geoTiff("treecover")
```

### LLM Instruction Prompt
- Always call `geoTiff` as an extension method on the SparkContext (`sc.geoTiff[T](...)`).
- You MUST specify the type parameter `[T]` to exactly match the file's runtime pixel type. Selection rules: `IntegerType` $\rightarrow$ `[Int]`, `FloatType` $\rightarrow$ `[Float]`, `ArrayType(IntegerType,true)` $\rightarrow$ `[Array[Int]]`, `ArrayType(FloatType, true)` $\rightarrow$ `[Array[Float]]`.
- Never invent file paths; use only the provided input variables.

### Prompt Snippet
```text
Load GeoTIFFs using the SparkContext extension `sc.geoTiff[T](path)`. You MUST match the type parameter `[T]` to the runtime pixel type (e.g., `[Int]` for IntegerType, `[Float]` for FloatType). Do not invent file paths.
```

### Common Failure Modes
- **Type Parameter Mismatch:** Failing to match the type parameter `[T]` to the actual runtime pixel type of the GeoTIFF (e.g., using `sc.geoTiff[Int]` for a `FloatType` raster) will cause runtime casting errors or data corruption.
- **Missing Context Extension:** Attempting to call `geoTiff` as a standalone function or on an object other than an initialized `SparkContext` (`sc`).
- **Overlaying Unaligned Rasters:** Loading multiple GeoTIFFs with `sc.geoTiff` and immediately attempting to `overlay` them without ensuring they have identical metadata (resolution, CRS, tile size). Unaligned rasters must be aligned using `reshape` first.

### Fix Code Hint
```scala
// BAD: Type parameter missing or mismatched, or called incorrectly
val raster = geoTiff("data.tif")
val floatRaster = sc.geoTiff[Int]("float_data.tif")

// GOOD: Called on SparkContext with the exact matching pixel type
val raster: RasterRDD[Int] = sc.geoTiff[Int]("data.tif")
val floatRaster: RasterRDD[Float] = sc.geoTiff[Float]("float_data.tif")
```

## API Test: `geojsonFile`

### Signature
```scala
def geojsonFile(filename: String) : SpatialRDD
def geojsonFile(filename: String) : JavaSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:84  (+1 more definition site/overload)_

_Source doc:_ Reads data from a Shapefile @param filename the name of the GeoJSON file or a directory that contains GeoJSON file @return an RDD of features

### Goal
Loads vector geometries and their associated properties from a GeoJSON file or directory into a distributed `SpatialRDD` for spatial processing.

### Parameters
- `filename` (`String`): The path to the GeoJSON file or a directory containing GeoJSON files to be loaded.

### Input
A valid GeoJSON file or a directory of GeoJSON files accessible to the Spark cluster (e.g., local file system, HDFS, or S3). This is a vector input format; it is not used for raster data (GeoTIFF/HDF).

### Output
Returns `SpatialRDD` — a distributed Spark RDD of `IFeature` objects representing the parsed GeoJSON geometries (points, lines, polygons) and their attributes. In Java, it returns a `JavaSpatialRDD` (equivalent to `JavaRDD<IFeature>`).

### Valid Call Patterns
```scala
// Scala
val records: SpatialRDD = sparkContext.geojsonFile("input.json")

// Java
JavaRDD<IFeature> records = spatialSparkContext.geojsonFile("input.json");
```

### LLM Instruction Prompt
- When loading GeoJSON vector data in Beast, use the `geojsonFile(path)` extension method directly on the initialized `SparkContext` (or `JavaSpatialSparkContext`). Do not call this on an RDD or a companion object. The returned `SpatialRDD` can then be spatially partitioned, used in vector spatial joins, or used as the vector input for a `raptorJoin` against a raster.

### Prompt Snippet
```text
To load GeoJSON vector data in Beast, use `sparkContext.geojsonFile("path/to/data.json")`. This returns a `SpatialRDD` (an `RDD[IFeature]`). Note that this is a SparkContext extension method. For other vector formats, use `sc.shapefile` or `sc.readCSVPoint`.
```

### Common Failure Modes
- **Incorrect Receiver:** Attempting to call `geojsonFile` on an RDD, a DataFrame, or a generic object instead of the `SparkContext`. It is a context extension.
- **Format Mismatch:** Passing a compressed Esri Shapefile (`.zip`) or a CSV file to this method. Beast has specific loaders for those (`sc.shapefile` and `sc.readCSVPoint`).
- **Missing Spatial Partitioning for Joins:** If the loaded GeoJSON is immediately used in a Distributed Join (`DJ`), it will fail or perform poorly unless it is first spatially partitioned (e.g., `records.spatialPartition(classOf[RSGrovePartitioner])`).

### Fix Code Hint
```scala
// ❌ BAD: Calling geojsonFile on an RDD or using it for a Shapefile
val data = myRdd.geojsonFile("polygons.zip")

// ✅ GOOD: Calling geojsonFile on the SparkContext for a .json file
val data: SpatialRDD = sparkContext.geojsonFile("polygons.json")

// ✅ GOOD: Spatially partitioning the loaded GeoJSON before a distributed join
val partitionedData = data.spatialPartition(classOf[RSGrovePartitioner])
```

## API Test: `geometryType`

### Signature
```scala
def geometryType: GeometryType
def geometryType: DataType
def geometryType: String
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/SpatialPartition.scala:60  (+2 more definition site/overload)_

_Source doc:_ The most inclusive geometry type for this partition. This can be interpreted as below. - Empty: All geometries are empty - Point: Contains at least one point and zero or more empty geometries - LineString: Contains at least one linestring and zero or more empty geometries - Polygon: Contains at least one polygon and zero or more empty geometries - MultiPoint: Contains at least one multipoint, and zero or more point or empty geometry. - MultiLineString: Contains at least one MultiLineString, and zero or more linestrings and empty geometries. - MultiPolygon: Contains at least one MultiPolygon, and zero or more poylgons and empty geometries. - GeometryCollection: Everything else, i.e., none of the above.

### Goal
Determines the most inclusive geometry type present within a spatial partition or geometric summary.

### Parameters
_None._

### Input
A spatial partition or geometric summary object containing vector features (e.g., loaded from Shapefiles, GeoJSON, or CSV). 

### Output
Returns `GeometryType` (with overloads returning Spark SQL `DataType` or `String`) — representing the hierarchical bounding geometry type of the partition's contents. It resolves mixed types to their most inclusive parent (e.g., Points + MultiPoints = MultiPoint; mixed incompatible types = GeometryCollection).

### Valid Call Patterns
```scala
// Note: Call pattern inferred from the signature and sibling methods (e.g., `numFeatures`) on SpatialPartition/Summary.
val summary = GeometricSummary.run(opts, Array(inputfile.getPath), null, sparkContext).asInstanceOf[Summary]

// Parameterless call to get the inclusive geometry type
val geomType = summary.geometryType
```

### LLM Instruction Prompt
- Call `geometryType` as a parameterless method (no parentheses).
- Do not assume the returned type guarantees a strictly homogeneous partition unless it returns `Point`, `LineString`, or `Polygon` (and even then, it may contain empty geometries).
- If the partition contains mixed, incompatible geometries (e.g., Points and Polygons), expect `GeometryCollection` as the return value.
- Use the appropriate overload implicitly based on the expected type (`GeometryType`, `DataType`, or `String`).

### Prompt Snippet
```text
// Determine the most inclusive geometry type of the partition/summary
val partitionGeomType = summary.geometryType
if (partitionGeomType.toString == "GeometryCollection") {
  println("Partition contains mixed geometry types.")
}
```

### Common Failure Modes
- **Adding parentheses:** Calling `summary.geometryType()` will cause a compilation error because it is defined as a parameterless `def`.
- **Assuming strict homogeneity:** Failing to handle `GeometryCollection` when processing datasets that contain mixed geometry types (e.g., a GeoJSON with both Polygons and Points).
- **Misinterpreting Multi-types:** Assuming `MultiPolygon` means *only* MultiPolygons are present; it actually means the partition contains at least one MultiPolygon and zero or more Polygons or empty geometries.

### Fix Code Hint
```scala
// WRONG: Using parentheses
val t = partition.geometryType()

// RIGHT: Parameterless call
val t = partition.geometryType
```

## API Test: `getAttributeName`

### Signature
```scala
def getAttributeName(i: Int): String
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/IFeature.scala:92_

_Source doc:_ If names are associated with attributes, this function returns the name of the attribute at the given position (0-based). @param i the index of the attribute to return its name @return the name of the given attribute index or `null` if it does not exist

### Goal
Retrieves the schema column name of a non-spatial attribute at a specific index from a geospatial feature (`IFeature`).

### Parameters
- `i` (`Int`): The 0-based index of the attribute whose name is being requested.

### Input
An `IFeature` instance (typically obtained from an `RDD[IFeature]`) that has an associated schema or attribute names. For vector formats like CSV or WKT, the file must be loaded with the header flag enabled (e.g., passing `true` for the header argument in `sc.readWKTFile`) so that the column names are parsed and attached to the features.

### Output
Returns `String` — The name of the attribute at the specified 0-based index, or `null` if the feature has no attribute names or the index does not exist.

### Valid Call Patterns
```scala
// Assuming sparkContext is an initialized SparkContext or JavaSpatialSparkContext
val data = sparkContext.readWKTFile(inputPath.getPath, "Geometry", '\t', true)
val feature = data.first()

// Retrieve attribute names by their 0-based index
val firstAttributeName = feature.getAttributeName(0)
val secondAttributeName = feature.getAttributeName(1)
```

### LLM Instruction Prompt
- When inspecting the schema or column names of an `IFeature`, call `feature.getAttributeName(i)` using a 0-based integer index.
- Always account for the possibility that this method returns `null` if the underlying dataset was loaded without header information or if the index is out of bounds.
- For CSV/WKT files, ensure the read operation (e.g., `readWKTFile`) is explicitly instructed to parse the header, otherwise attribute names will not be populated.

### Prompt Snippet
```text
To retrieve the column name of a specific attribute from an `IFeature`, use `feature.getAttributeName(i: Int)`. The index is 0-based. It returns a String, or `null` if the attribute name does not exist (e.g., if a CSV was loaded without parsing the header).
```

### Common Failure Modes
- **Null Returns on Headerless Data:** Calling `getAttributeName` on features loaded from a CSV or WKT file where the header parsing flag was omitted or set to `false`. The method will return `null` because the schema was not initialized with column names.
- **Index Out of Bounds:** Passing an index `i` that is negative or greater than/equal to the total number of attributes on the feature, which may return `null` or throw an exception depending on the underlying feature implementation.

### Fix Code Hint
```scala
// BAD: Loading WKT without specifying that it has a header, leading to null attribute names
val data = sparkContext.readWKTFile(inputPath.getPath, "Geometry", '\t')
val name = data.first().getAttributeName(0) // Likely null

// GOOD: Explicitly passing `true` to parse the header row
val dataWithHeader = sparkContext.readWKTFile(inputPath.getPath, "Geometry", '\t', true)
val validName = dataWithHeader.first().getAttributeName(0)
if (validName != null) {
  println(s"First column is: $validName")
}
```

## API Test: `getBoolean`

### Signature
```scala
def getBoolean(key: String, defaultValue: Boolean): Boolean
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/common/BeastOptions.scala:133_

_Source doc:_ Get value as boolean @param key @param defaultValue @return

### Goal
Retrieves a boolean configuration value for a given key from the parsed Beast options, returning a specified default if the key is absent.

### Parameters
- `key` (`String`): The string identifier for the configuration option (e.g., `"my-flag"`). This should be the base name of the parameter, omitting any command-line prefixes like `-` or `-no-`.
- `defaultValue` (`Boolean`): The fallback boolean value to return if the specified `key` is not found in the configuration options.

### Input
A `BeastOptions` instance (typically accessed via `parsed.options` after calling `OperationHelper.parseCommandLineArguments`) containing parsed command-line flags or job configuration settings. 

### Output
Returns `Boolean` — the boolean state of the requested configuration key (e.g., `true` if `-key` was passed, `false` if `-no-key` was passed), or the `defaultValue` if the key was not provided.

### Valid Call Patterns
```scala
// Assuming `parsed` is the result of OperationHelper.parseCommandLineArguments
// Example 1: Using named arguments for clarity
val isEnabled = parsed.options.getBoolean("option2", defaultValue = false)

// Example 2: Using positional arguments
val isDisabled = parsed.options.getBoolean("option3", true)

// Example 3: Keys can contain dashes in the middle
val hasDashedOption = parsed.options.getBoolean("option-4", false)
```

### LLM Instruction Prompt
- When extracting boolean flags from Beast configuration options, always use `options.getBoolean(key, defaultValue)`. 
- Do not include command-line prefixes (`-` or `-no-`) in the `key` string. Beast's CLI parser automatically maps flags like `-my-flag` to `true` and `-no-my-flag` to `false` under the base key `"my-flag"`.

### Prompt Snippet
```text
To read boolean configuration flags safely in Beast, use `options.getBoolean("flag-name", defaultValue)`. Ensure the key string omits CLI prefixes like `-` or `-no-`.
```

### Common Failure Modes
- **Including CLI prefixes in the key:** Querying for `"-my-flag"` or `"-no-my-flag"` instead of the base key `"my-flag"`. The parser strips these prefixes, so the prefixed key will not be found, causing the method to silently return the `defaultValue`.
- **Type mismatch assumptions:** Assuming a flag provided as a string like `"true"` or `"1"` via array syntax (e.g., `option[1]:true`) requires `getString` and manual parsing; `getBoolean` handles standard boolean representations natively.

### Fix Code Hint
```scala
// ❌ BAD: Including the CLI dash or negation prefix in the key
val flag = parsed.options.getBoolean("-no-cache", true)

// ✅ GOOD: Use the base key name; Beast handles the `-no-` logic internally
val flag = parsed.options.getBoolean("cache", true)
```

## API Test: `getFeatureReaderClass`

### Signature
```scala
def getFeatureReaderClass(path: String, opts: BeastOptions): Class[_ <: FeatureReader]
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialFileRDD.scala:398_

_Source doc:_ The class of the feature reader to use with this RDD. All partitions use the same feature reader.

### Goal
Resolves the specific `FeatureReader` implementation class required to parse a spatial dataset across all Spark partitions based on the file path and configuration options.

### Parameters
- `path` (`String`): The URI or local file path to the input spatial dataset (e.g., a GeoJSON, Shapefile, or CSV file).
- `opts` (`BeastOptions`): Configuration options that can provide explicit format hints (e.g., specifying the input format) to help resolve the correct reader.

### Input
A valid file path string pointing to a supported vector format (such as CSV, Esri Shapefile, GeoJSON, JSON+WKT, or GPX) and a `BeastOptions` object containing any necessary parsing configurations or format overrides.

### Output
Returns `Class[_ <: FeatureReader]` — the Java `Class` object representing the specific reader implementation that Beast will instantiate to extract features from the dataset's partitions.

### Valid Call Patterns
```scala
// Resolving the reader class for manual partition reading
val inputFile = makeFileCopy("/allfeatures.geojson")
val opts: BeastOptions = SpatialFileRDD.InputFormat -> "geojson"

// Call on the SpatialFileRDD object
val featureReaderClass = SpatialFileRDD.getFeatureReaderClass(inputFile.getPath, opts)

// Used subsequently to read partitions
val partitions = SpatialFileRDD.createPartitions(inputFile.getPath, opts, sparkContext.hadoopConfiguration)
for (partition <- partitions) {
  val features = SpatialFileRDD.readPartition(partition, featureReaderClass, true, opts)
  // Process features...
}
```

### LLM Instruction Prompt
- When manually orchestrating low-level spatial partition reads instead of using high-level context extensions (like `sc.shapefile`), use `SpatialFileRDD.getFeatureReaderClass(path, opts)` to determine the correct reader class.
- Always qualify the call with the `SpatialFileRDD` object.
- If the file extension is non-standard or ambiguous, explicitly set the format hint in the `BeastOptions` argument (e.g., `SpatialFileRDD.InputFormat -> "geojson"`).

### Prompt Snippet
```text
To resolve the reader class for manual partition reading in Beast, use `SpatialFileRDD.getFeatureReaderClass(path, opts)`. Provide format hints in `opts` if the file extension does not clearly indicate the vector format.
```

### Common Failure Modes
- **Unqualified Call:** Attempting to call `getFeatureReaderClass(...)` as a bare function instead of qualifying it with `SpatialFileRDD.`.
- **Unresolved Format:** Passing an empty `BeastOptions` for a file with an unrecognized or missing extension, causing Beast to fail to identify the correct `FeatureReader`.
- **Raster Inputs:** Attempting to use this method for raster formats (GeoTIFF, HDF). This API is strictly for vector feature readers; raster loading should use `sc.geoTiff[T]` or `sc.hdfFile`.

### Fix Code Hint
```scala
// Incorrect: val reader = getFeatureReaderClass("data.customext", new BeastOptions())
// Correct: Provide format hints and call on SpatialFileRDD
val opts: BeastOptions = SpatialFileRDD.InputFormat -> "geojson"
val readerClass = SpatialFileRDD.getFeatureReaderClass("data.customext", opts)
```

## API Test: `getGeometry`

### Signature
```scala
def getGeometry: Geometry
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/IFeature.scala:69_

_Source doc:_ The geometry contained in the feature. @return the geometry in this attribute

### Goal
Extracts the underlying spatial geometry (such as a point, polygon, or bounding box) from an `IFeature` object.

### Parameters
_None._

### Input
An `IFeature` instance, typically obtained from loading vector datasets (e.g., via `sc.shapefile`, `sc.geojsonFile`), from spatial joins, or from spatial data generators. 

### Output
Returns `Geometry` — the spatial representation of the feature. Depending on the dataset, this underlying object may be a specific geometry type such as a JTS Geometry or Beast's `EnvelopeND`.

### Valid Call Patterns
```scala
// Extracting the geometry from an IFeature
val geom: Geometry = feature.getGeometry

// Extracting and casting to a specific known type (e.g., EnvelopeND)
val envelope = feature.getGeometry.asInstanceOf[EnvelopeND]
```

### LLM Instruction Prompt
- Call `getGeometry` on an `IFeature` instance when you need to access or manipulate the spatial coordinates, bounding box, or shape of the vector feature.
- The return type is a generic `Geometry`. If you need to access specific coordinate dimensions (e.g., `getMinCoord`), you must cast it to the appropriate subclass (like `EnvelopeND`), ensuring you know the underlying geometry type of the dataset.

### Prompt Snippet
```text
To extract the spatial shape from an `IFeature` in Beast, use `feature.getGeometry`. If you need to manipulate specific dimensions or bounds, cast the returned `Geometry` to the expected type, such as `EnvelopeND`.
```

### Common Failure Modes
- **ClassCastException:** Blindly casting the returned `Geometry` to a specific type (like `EnvelopeND` or a JTS `Polygon`) when the dataset contains mixed geometry types or a different geometry type than expected.
- **NullPointerException:** Attempting to call `getGeometry` on a null feature reference, which can occur if a previous transformation or join produced null values.

### Fix Code Hint
```scala
// Safely handle the extracted geometry using pattern matching
val geom = feature.getGeometry
geom match {
  case env: EnvelopeND => 
    // Safe to use EnvelopeND methods
    val minX = env.getMinCoord(0)
  case _ => 
    // Handle standard JTS geometries or other types
}
```

## API Test: `getInt`

### Signature
```scala
def getInt(i: Int): Int
def getInt(key: String, defaultValue: Int): Int
```
_Source doc:_ Get a value of a key as integer @param key @param defaultValue @return

### Goal
Retrieves an integer value either from a configuration object by its string key (providing a fallback default if missing), or from a Spark SQL `InternalRow` by its column index.

### Parameters
- `key` (`String`): The configuration property name to look up (used in the key-value overload).
- `defaultValue` (`Int`): The fallback integer to return if the specified `key` is not present or cannot be parsed.
- `i` (`Int`): The zero-based column index to retrieve (used in the `InternalRow` overload).

### Input
- For the key-value overload: A configuration object (e.g., `BeastOptions`) containing string-based key-value pairs.
- For the index overload: A Spark SQL `InternalRow` (such as an encoded spatial geometry) where the specified index contains an integer type. The caller should ensure the column is not null before access.

### Output
Returns `Int` — The requested integer value from the row, or the parsed configuration value (falling back to `defaultValue` if the key is absent).

### Valid Call Patterns
```scala
// 1. Retrieving an integer by index from an InternalRow (Authoritative from test suite)
val firstGeom: InternalRow = encoded.head
val geomType: Int = firstGeom.getInt(0)

// 2. Retrieving a configuration value by key (Inferred from signature)
// e.g., reading a Beast configuration option with a safe fallback
val bitsPerSample: Int = options.getInt("GeoTiffWriter.BitsPerSample", 32)
```

### LLM Instruction Prompt
- When extracting integer values from Spark SQL `InternalRow` objects (such as encoded geometries in Parquet), use `row.getInt(index)`. Always check `row.isNullAt(index)` first if the schema allows nulls.
- When reading Beast configuration options, use `options.getInt(key, defaultValue)` to ensure a safe fallback is provided if the user did not specify the setting.

### Prompt Snippet
```text
// Extracting an integer type flag from an encoded geometry row
assertResult(SpatialParquetHelper.PointType)(firstGeom.getInt(0))
```

### Common Failure Modes
- **Null Pointer / Defaulting Errors on Rows:** Calling `getInt(i)` on an `InternalRow` where the value at index `i` is null. This can lead to unexpected behavior or exceptions. Always use `isNullAt(i)` to verify presence before extraction.
- **Type Cast Exceptions:** Calling `getInt(i)` on a column index that actually holds a `DoubleType` or `ArrayType` (e.g., coordinate arrays).
- **Parsing Errors:** Using `getInt(key, default)` on a configuration key where the user provided a non-numeric string value, causing a parsing exception.

### Fix Code Hint
```scala
// Safely extract an integer from an InternalRow by checking for nulls first
val geomType: Int = if (!firstGeom.isNullAt(0)) {
  firstGeom.getInt(0)
} else {
  -1 // or appropriate default/error handling
}
```

## API Test: `getLong`

### Signature
```scala
def getLong(key: String, defaultValue: Long): Long
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/common/BeastOptions.scala:114_

_Source doc:_ Get a key value as long @param key @param defaultValue @return

### Goal
Retrieves a configuration value associated with the specified key as a 64-bit integer (`Long`), returning a fallback default value if the key is missing.

### Parameters
- `key` (`String`): The configuration property name to look up within the `BeastOptions` instance.
- `defaultValue` (`Long`): The fallback value to return if the specified key does not exist in the configuration.

### Input
An initialized `BeastOptions` instance containing configuration properties for the Beast/RDPro Spark environment. 

### Output
Returns `Long` — The parsed 64-bit integer value associated with the configuration key, or the provided `defaultValue` if the key is absent.

### Valid Call Patterns
```scala
// Note: Call pattern inferred from signature and source path (not verified by test suite)
// Assumes `options` is an instance of edu.ucr.cs.bdlab.beast.common.BeastOptions
val maxPixels = options.getLong("rdpro.raster.maxPixels", 1000000000L)
```

### LLM Instruction Prompt
- When extracting configuration parameters that represent large integers (such as memory limits, pixel counts, or partition thresholds) from a `BeastOptions` object, use `getLong` to ensure type safety and always provide a sensible default `Long` value (e.g., `0L`). Do not call this as a standalone function; it must be called on a `BeastOptions` instance.

### Prompt Snippet
```text
Extract large integer configuration properties safely using `options.getLong("my.config.key", 1000L)`.
```

### Common Failure Modes
- **Missing Receiver:** Attempting to call `getLong("key", 0L)` as a bare function rather than a method on a `BeastOptions` instance.
- **Type Mismatch on Default Value:** Passing a standard `Int` (e.g., `1000`) instead of a `Long` (e.g., `1000L`) for the `defaultValue` parameter, which may cause Scala compiler type-inference errors.
- **Parsing Errors:** If the key exists in the configuration but its string representation cannot be parsed into a valid `Long` (e.g., it contains letters or represents a floating-point number), the underlying parser will likely throw a `NumberFormatException`.

### Fix Code Hint
```scala
// Ensure the method is called on a BeastOptions instance and the default value has the 'L' suffix
val options = new BeastOptions()
val threshold = options.getLong("spatial.join.maxRecords", 500000L)
```

## API Test: `getName`

### Signature
```scala
def getName(i: Int): String
```
_Source doc:_ Return the name of the given attribute. @param i the index of the attribute in the range [0, length[ @return the type of the attribute or null if unknown

### Goal
Retrieves the name of a specific attribute at the given index from a spatial feature's schema.

### Parameters
- `i` (`Int`): The zero-based index of the attribute to query, which must be in the range `[0, length)`.

### Input
A spatial feature (such as an `IFeature` loaded from a Shapefile, GeoJSON, or CSV) that contains an attribute schema. The caller must provide a valid integer index `i` that falls within the bounds of the feature's attribute array.

### Output
Returns `String` — The name of the attribute at the specified index. (Note: The original source documentation mentions returning the "type", which is likely a typo for "name"). Returns `null` if the attribute name is unknown or undefined.

### Valid Call Patterns
```scala
// Inferred from signature (not verified in provided test suite)
// Assuming `feature` is an instance of IFeature or a similar schema-bearing object
val attributeName: String = feature.getName(0)

if (attributeName != null) {
  println(s"First attribute is named: $attributeName")
}
```

### LLM Instruction Prompt
- When inspecting the schema of a spatial feature in Beast, use `getName(i)` to retrieve the attribute's name.
- Always ensure the index `i` is within the valid range `[0, length)` to avoid out-of-bounds errors.
- You MUST handle potential `null` return values, as the API explicitly states it returns `null` if the name is unknown (e.g., in best-effort CSV parsing where headers might be missing).

### Prompt Snippet
```text
Use `feature.getName(i: Int)` to get the attribute name at index `i`. Ensure `i` is within bounds and handle `null` returns safely, as undefined attributes return `null`.
```

### Common Failure Modes
- **`IndexOutOfBoundsException`**: Occurs if `i` is negative or greater than or equal to the total number of attributes in the feature.
- **`NullPointerException`**: Occurs if the caller attempts to invoke methods (like `.toLowerCase()`) on the returned `String` without checking if it is `null`, which is common when reading formats without strict schemas (like headerless CSVs).

### Fix Code Hint
```scala
// Check bounds and handle nulls safely
val numAttributes = feature.length // or equivalent method to get attribute count
if (i >= 0 && i < numAttributes) {
  val name = feature.getName(i)
  val safeName = Option(name).getOrElse(s"attribute_$i")
  // Proceed with safeName
}
```

## API Test: `getOperationParams`

### Signature
```scala
def getOperationParams(operation: Operation, opts: BeastOptions): Array[OperationParamInfo]
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/OperationHelper.scala:209_

_Source doc:_ Returns all parameters that are allowed for the given operation. Operation parameters are all parameters annotated with [[OperationParam]] that appear in one of the following: - In the class associated with the given operation - In any additional classes defined in the [[OperationMetadata]] annotation on the class - In any classes that are added through the method [[IConfigurable]].addDependentClasses @param operation the operation in question @param opts any additional user options. This is used to add dependent classes if they depend on some user choice. For example, if the user selects a specific indexer, it can be used to add that specific indexer as a dependent class @return an array of parameters that are allowed

### Goal
Retrieves all valid configuration parameters (annotated with `@OperationParam`) for a specific Beast operation, dynamically including parameters from dependent classes based on user options.

### Parameters
- `operation` (`Operation`): The Beast operation instance to inspect (typically retrieved from the `OperationHelper.operations` map).
- `opts` (`BeastOptions`): Additional user configurations used to resolve dependent classes (e.g., if a specific spatial indexer is selected, its specific parameters are added to the result). Can be `null`.

### Input
Requires a valid `Operation` object registered in Beast. Because this is an internal metadata/reflection API rather than a spatial processing API, it does not require spatial data files, RDDs, or SparkContext initialization.

### Output
Returns `Array[OperationParamInfo]` — an array containing metadata (such as name, description, and type) for every parameter accepted by the specified operation and its dependent classes.

### Valid Call Patterns
```scala
// Retrieve parameters for a specific operation, passing null for options
val params = OperationHelper.getOperationParams(OperationHelper.operations("test"), null)

// Check if a specific parameter exists
val hasSParam = params.exists(_.name == "sparam")
```

### LLM Instruction Prompt
- Use `OperationHelper.getOperationParams(operation, opts)` when you need to programmatically discover, validate, or display the configuration parameters available for a specific Beast operation.
- Always call it via the `OperationHelper` object.
- You may pass `null` for the `opts` parameter if no dynamic user choices (like a specific indexer) are required to resolve dependent classes.

### Prompt Snippet
```text
`OperationHelper.getOperationParams(op: Operation, opts: BeastOptions): Array[OperationParamInfo]` returns all `@OperationParam` annotated fields for the given operation and its dependent classes. `opts` can be `null`.
```

### Common Failure Modes
- **Unregistered Operation:** Attempting to look up an unregistered or misspelled operation name (e.g., `OperationHelper.operations("typo")`) before passing it to this function, which will throw a `NoSuchElementException` from the underlying Map.
- **Missing Dependent Parameters:** Passing `null` for `opts` when the operation relies on user choices (like a specific `RSGrovePartitioner` vs `GridPartitioner`) to expose algorithm-specific parameters, resulting in an incomplete parameter list.

### Fix Code Hint
```scala
// Safely retrieve an operation and its parameters using an empty BeastOptions instead of null
val opName = "spatialJoin"
if (OperationHelper.operations.contains(opName)) {
  val op = OperationHelper.operations(opName)
  val opts = new BeastOptions() // Preferred over null if options might be populated later
  val params = OperationHelper.getOperationParams(op, opts)
  params.foreach(p => println(p.name))
}
```

## API Test: `getPointValue`

### Signature
```scala
def getPointValue(x: Double, y: Double): T
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:93_

_Source doc:_ Return the value of the pixel that contains the given point at model (world) coordinates. @param x the x-coordinate of the point, e.g., longitude @param y the y-coordinate of the point, e.g., latitude @return the value of all components of the given pixel

### Goal
Retrieve the pixel value(s) from a raster tile at a specific geographic (model/world) coordinate.

### Parameters
- `x` (`Double`): The x-coordinate of the point in model (world) coordinates, such as longitude.
- `y` (`Double`): The y-coordinate of the point in model (world) coordinates, such as latitude.

### Input
An `ITile[T]` instance, typically obtained from a `GeoTiffReader[T]` or an RDD of raster tiles. The provided `x` and `y` coordinates must be in the same Coordinate Reference System (CRS) as the raster tile (e.g., EPSG:4326 for longitude/latitude). The point must spatially intersect the specific tile being queried.

### Output
Returns `T` — the value of all components of the pixel containing the point. The type `T` exactly matches the runtime pixel type of the raster (e.g., `Int` for single-band integer, `Float` for single-band float, `Array[Int]` or `Array[Float]` for multi-band rasters).

### Valid Call Patterns
```scala
// Example 1: Single-band integer GeoTIFF
val reader = new GeoTiffReader[Int]
reader.initialize(fileSystem, rasterPath, "0", new BeastOptions)
// Ensure the tile actually contains the point before querying
val tileId = reader.metadata.getTileIDAtPoint(23.224, 32.415)
val tile = reader.readTile(tileId)
val pixelValue: Int = tile.getPointValue(23.224, 32.415)

// Example 2: Multi-band (banded) float GeoTIFF
val bandedReader = new GeoTiffReader[Array[Float]]
bandedReader.initialize(fileSystem, bandedRasterPath, "0", new BeastOptions)
val bandedTileId = bandedReader.metadata.getTileIDAtPoint(31.277, 26.954)
val bandedTile = bandedReader.readTile(bandedTileId)
val pixelValues: Array[Float] = bandedTile.getPointValue(31.277, 26.954)
```

### LLM Instruction Prompt
- Call `tile.getPointValue(x, y)` to extract pixel data at a geographic location.
- NEVER pass pixel/grid indices (column/row) to this function; it strictly requires model/world coordinates (e.g., longitude and latitude).
- Ensure the receiver is an `ITile[T]`. The return type `T` will match the tile's type parameter, which must align with the GeoTIFF's runtime type (`Int`, `Float`, `Array[Int]`, or `Array[Float]`).
- Always verify that the point falls within the tile's spatial bounds before calling, typically by using `metadata.getTileIDAtPoint(x, y)` to fetch the correct tile first.

### Prompt Snippet
```text
To get a pixel value at a specific geographic coordinate from an `ITile[T]`, use `tile.getPointValue(x, y)`. The coordinates must be in the raster's world CRS (e.g., longitude/latitude), not pixel indices. The return type matches the tile's type `T` (e.g., `Int`, `Float`, or `Array[Float]` for multi-band). Ensure the point is actually within the tile's bounds.
```

### Common Failure Modes
- **Coordinate Space Mismatch:** Passing pixel coordinates (x=column, y=row) instead of world coordinates (x=longitude, y=latitude), resulting in out-of-bounds errors or incorrect pixel values.
- **Spatial Out-of-Bounds:** Calling `getPointValue` on a tile that does not spatially cover the requested `(x, y)` point.
- **Type Mismatch:** Expecting a scalar value (e.g., `Float`) when querying a multi-band raster tile, which actually returns an `Array[Float]`.

### Fix Code Hint
```scala
// BAD: Passing pixel indices or querying a random tile
// val value = randomTile.getPointValue(col, row)

// GOOD: Fetching the correct tile using world coordinates first, then querying
val x = -117.32
val y = 33.95
val tileId = reader.metadata.getTileIDAtPoint(x, y)
val tile = reader.readTile(tileId)
val value = tile.getPointValue(x, y)
```

## API Test: `getStorageSize`

### Signature
```scala
def getStorageSize: Int
def getStorageSize(value: Any, dataType: DataType): Int
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/IFeature.scala:112  (+1 more definition site/overload)_

### Goal
Estimates the total storage size in bytes of a spatial feature (including its geometry and attributes) or calculates the estimated size of a specific attribute value based on its Spark SQL data type.

### Parameters
- `value` (`Any`): The specific attribute value or object whose size is being estimated (e.g., a string, number, or geometry). It safely accepts `null`.
- `dataType` (`DataType`): The Spark SQL `DataType` corresponding to the `value` (e.g., `StringType`, `IntegerType`, `MapType`).

### Input
An instantiated spatial feature (`IFeature`) containing a geometry and optional attributes. The function safely handles `null` attribute values and empty collections (such as an empty `Map`) without throwing exceptions. 

### Output
Returns `Int` — The estimated storage size of the feature or value in bytes. Note that this is an in-memory estimate, not necessarily the exact serialized byte size on disk.

### Valid Call Patterns
```scala
// 1. Estimating the total size of a feature (Authoritative from test suite)
val featureSize: Int = feature.getStorageSize

// 2. Estimating the size of a specific attribute value (Inferred from signature)
val valueSize: Int = feature.getStorageSize("sample_string", org.apache.spark.sql.types.StringType)
```

### LLM Instruction Prompt
- When needing to estimate the memory footprint of an `IFeature` in Beast/RDPro, call the parameterless `feature.getStorageSize` method. 
- It returns the size in bytes and is designed to safely handle `null` attributes or empty maps without throwing exceptions. 
- Do not assume it returns an exact serialization size for disk writes; it is an in-memory estimate.

### Prompt Snippet
```text
To estimate the memory footprint of a spatial feature in bytes, call `feature.getStorageSize`. It safely handles null attributes and empty collections without throwing exceptions, returning an estimated `Int` byte size.
```

### Common Failure Modes
- **Expecting Exact Disk Size:** Assuming the returned integer perfectly matches the byte size of the feature when written to a Shapefile or GeoJSON. It is an *estimate* of the in-memory storage size.
- **Null Feature Reference:** While `getStorageSize` safely handles `null` *attributes* inside the feature, calling `feature.getStorageSize` on a null `IFeature` reference will throw a standard `NullPointerException`.
- **Unsupported Data Types:** Passing a custom or unsupported Spark SQL `DataType` to the 2-argument overload may result in inaccurate size estimates if the type's memory footprint cannot be accurately resolved.

### Fix Code Hint
```scala
// Safely check feature size, knowing null attributes won't crash the call
if (feature != null) {
  val estimatedBytes = feature.getStorageSize
  println(s"Feature takes up approximately $estimatedBytes bytes.")
}
```

## API Test: `getTileIDAtPixel`

### Signature
```scala
def getTileIDAtPixel(iPixel: Int, jPixel: Int): Int
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:69_

_Source doc:_ Computes the ID of the tile that contains the given pixel. Tiles are numbered in row-wise ordering. @param iPixel the position of the column of the pixel @param jPixel the position of the row of the pixel @return a unique identifier for the tile that contains this pixel location

### Goal
Computes the unique, row-wise tile ID that contains a specific pixel coordinate within a raster dataset's grid.

### Parameters
- `iPixel` (`Int`): The column index (x-coordinate in pixel space) of the target pixel.
- `jPixel` (`Int`): The row index (y-coordinate in pixel space) of the target pixel.

### Input
This method must be called on a `RasterMetadata` instance, which is typically accessed via a `GeoTiffReader` (e.g., `reader.metadata`) or an `ITile` (e.g., `tile.rasterMetadata`). The input coordinates must be in **pixel grid space** (integers), not model space (e.g., not degrees or meters). If you have model coordinates (longitude/latitude), you must first convert them using `metadata.modelToGrid`.

### Output
Returns `Int` — a unique identifier for the tile that contains the specified pixel location. The IDs are assigned sequentially in row-wise (raster scan) order across the dataset.

### Valid Call Patterns
```scala
// Pattern 1: Using a GeoTiffReader's metadata (e.g., after modelToGrid conversion)
val outPoint = new java.awt.geom.Point2D.Double
reader.metadata.modelToGrid(-0.06, 49.28, outPoint)
val iPixel = outPoint.getX.toInt
val jPixel = outPoint.getY.toInt
val tileID = reader.metadata.getTileIDAtPixel(iPixel, jPixel)

// Pattern 2: Using an ITile's metadata within an RDD transformation
val fileTileRDD = new RasterFileRDD[Int](sparkContext, dirPath, new BeastOptions())
val originTiles = fileTileRDD.filter(t => t.rasterMetadata.getTileIDAtPixel(0, 0) == t.tileID)
```

### LLM Instruction Prompt
- When determining which tile contains a specific pixel, call `getTileIDAtPixel(iPixel, jPixel)` on a `RasterMetadata` object.
- Never call this as a standalone function; it is a method of `RasterMetadata`.
- Ensure `iPixel` represents the column (x) and `jPixel` represents the row (y). Do not swap them.
- Do not pass geographic coordinates (CRS model space) directly to this function. Convert them to pixel coordinates first using `metadata.modelToGrid(x, y, outPoint)`.

### Prompt Snippet
```text
To find the tile ID for a specific pixel, use `metadata.getTileIDAtPixel(iPixel, jPixel)`. Remember that `iPixel` is the column (x) and `jPixel` is the row (y). If you have geographic coordinates, convert them to grid coordinates first using `metadata.modelToGrid`.
```

### Common Failure Modes
- **Calling as a standalone function:** Attempting to use `getTileIDAtPixel(x, y)` without a `RasterMetadata` receiver will cause a compilation error.
- **Passing Model Coordinates:** Passing longitude/latitude or projected meters directly into `iPixel` and `jPixel` will result in wildly incorrect tile IDs or out-of-bounds errors.
- **Swapping Row and Column:** Passing `(row, column)` instead of `(column, row)` will yield the wrong tile ID. `iPixel` is always the column (x-axis).

### Fix Code Hint
```scala
// WRONG: Passing geographic coordinates directly
// val tileID = metadata.getTileIDAtPixel(-117.32, 33.95)

// WRONG: Swapping row and column
// val tileID = metadata.getTileIDAtPixel(row, col)

// RIGHT: Convert model to grid, then extract column (x) and row (y)
val outPoint = new java.awt.geom.Point2D.Double
metadata.modelToGrid(-117.32, 33.95, outPoint)
val tileID = metadata.getTileIDAtPixel(outPoint.getX.toInt, outPoint.getY.toInt)
```

## API Test: `getTileIDAtPoint`

### Signature
```scala
def getTileIDAtPoint(x: Double, y: Double): Int
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:81_

_Source doc:_ Returns the ID of the tile that contains the given point location in model (world) space @param x the x-coordinate of the point, e.g., longitude @param y the y-coordinate of the point, e.g., latitude @return the ID of the tile that contains this pixel or -1 if the point is outside the input space

### Goal
Resolves a geographic coordinate in model (world) space to the internal ID of the raster tile that contains it, based on the dataset's spatial metadata.

### Parameters
- `x` (`Double`): The x-coordinate of the point in model (world) space, typically longitude.
- `y` (`Double`): The y-coordinate of the point in model (world) space, typically latitude.

### Input
Requires an initialized `RasterMetadata` instance (commonly accessed via `reader.metadata` on a `GeoTiffReader`). The provided `x` and `y` coordinates must be in the same Coordinate Reference System (CRS) as the raster dataset. 

### Output
Returns `Int` — The ID of the tile containing the specified pixel. Returns `-1` if the point falls completely outside the spatial bounds of the input raster space.

### Valid Call Patterns
```scala
// Assuming `reader` is an initialized GeoTiffReader[T]
val tileId = reader.metadata.getTileIDAtPoint(23.224, 32.415)

if (tileId != -1) {
  val tile = reader.readTile(tileId)
  val pixelValue = tile.getPointValue(23.224, 32.415)
}
```

### LLM Instruction Prompt
- When you need to read a specific tile or extract a pixel value at a known geographic coordinate, call `getTileIDAtPoint(x, y)` on the raster's `RasterMetadata` object to get the correct tile ID.
- ALWAYS check if the returned tile ID is `-1` (out of bounds) before passing it to `readTile()`.
- Ensure the `x` and `y` coordinates match the CRS of the raster; do not pass unprojected longitude/latitude if the raster uses a projected coordinate system.

### Prompt Snippet
```text
To find which tile contains a specific geographic coordinate, call `metadata.getTileIDAtPoint(x, y)`. It returns the integer tile ID, or `-1` if the point is outside the raster bounds. Always verify the ID is not `-1` before calling `readTile(id)`.
```

### Common Failure Modes
- **Out of Bounds Exception:** Passing the result directly to `readTile(id)` without checking if `id == -1`, causing a failure when the requested point is outside the raster's envelope.
- **Coordinate System Mismatch:** Passing WGS84 longitude/latitude coordinates to a raster that is projected in a different CRS (e.g., Web Mercator or UTM), resulting in an incorrect tile ID or `-1`.
- **Swapped Coordinates:** Passing `(latitude, longitude)` instead of `(longitude, latitude)` for `(x, y)`.

### Fix Code Hint
```scala
// Safely resolve a tile ID and read the tile
val targetX = 31.277
val targetY = 26.954
val tileId = reader.metadata.getTileIDAtPoint(targetX, targetY)

if (tileId != -1) {
  val tile = reader.readTile(tileId)
  // Extract value using the same coordinates
  val value = tile.getPointValue(targetX, targetY)
} else {
  println(s"Point ($targetX, $targetY) is outside the raster bounds.")
}
```

## API Test: `getValue`

### Signature
```scala
def getValue(in: FSDataInputStream, offset: Long, key: Long): (Long, Int)
def getValue(fileSystem: FileSystem, path: Path, key: Long): (Long, Int)
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/DiskTileHashtable.scala:91  (+1 more definition site/overload)_

_Source doc:_ Return the value that corresponds to the given key or null if the value is not found. @param in the hashtable file @param offset the offset of the hashtable in the file @param key the key to search for @return the value of the key if found, or `null` if the key is not found.

### Goal
Retrieves a stored value (typically a file offset and length tuple) associated with a specific key (e.g., a tile ID) from a disk-based hashtable file used in DaVinci visualization pipelines.

### Parameters
- `in` (`FSDataInputStream`): The open Hadoop file input stream pointing to the hashtable file. (In the overload, `fileSystem: FileSystem` and `path: Path` are used to open this stream automatically).
- `offset` (`Long`): The byte offset within the file where the hashtable structure begins.
- `key` (`Long`): The unique identifier (e.g., spatial tile ID) to search for within the hashtable.

### Input
Requires a valid, accessible Hadoop `FileSystem` and `Path` (or an already open `FSDataInputStream`) pointing to a disk-based hashtable file generated by Beast's visualization/MVT components. The `offset` must accurately point to the start of the hashtable block within that file.

### Output
Returns `(Long, Int)` — A tuple representing the value associated with the key (typically the byte offset `Long` and byte length `Int` of the corresponding tile data in the archive). Note: As per the source documentation, this method returns `null` if the key is not found, which requires explicit null-checking despite the Scala Tuple return type.

### Valid Call Patterns
```scala
// Note: Call pattern inferred from signature. 
// (The project's test suite examples demonstrate UniformHistogram#getValue(Array[Int], Array[Int]), 
// which shares the same name but is a completely different API).

// Using an open FSDataInputStream
val tileDataLocation: (Long, Int) = DiskTileHashtable.getValue(inStream, 0L, tileKey)

// Using a FileSystem and Path
val tileDataLocation2: (Long, Int) = DiskTileHashtable.getValue(hadoopFS, indexPath, tileKey)
```

### LLM Instruction Prompt
- DO NOT confuse this `DiskTileHashtable` visualization method with `UniformHistogram.getValue(Array[Int], Array[Int])`. If the user wants to query a spatial histogram, use the array-based signature. If they are querying a DaVinci disk hashtable, use this stream/path-based signature.
- Always check the result for `null` before accessing the tuple elements, as the underlying implementation returns `null` (rather than an `Option`) when a key is missing.
- Ensure the `FSDataInputStream` is open and positioned correctly, or use the `FileSystem` overload to let the method handle stream lifecycle.

### Prompt Snippet
```text
When querying a DaVinci disk-based tile hashtable in Beast, use `getValue(in: FSDataInputStream, offset: Long, key: Long): (Long, Int)`. Because this API returns `null` when a key is missing, you must explicitly check for null before extracting the offset and length from the returned tuple. Do not confuse this with `UniformHistogram.getValue`.
```

### Common Failure Modes
- **NullPointerException:** Failing to check if the returned `(Long, Int)` is `null` before attempting to access `_1` or `_2`.
- **EOFException / Corrupted Reads:** Providing an incorrect `offset` value that does not align with the actual start of the hashtable in the file.
- **Signature Confusion:** Attempting to pass `Array[Int]` coordinates to this method when intending to query a `UniformHistogram`.
- **Closed Stream:** Passing an `FSDataInputStream` that has already been closed by another part of the application.

### Fix Code Hint
```scala
// BAD: Assumes the tuple is always returned and throws NullPointerException if key is missing
val (tileOffset, tileLength) = DiskTileHashtable.getValue(fs, path, key)

// GOOD: Explicitly handles the documented null return value
val result = DiskTileHashtable.getValue(fs, path, key)
if (result != null) {
  val tileOffset = result._1
  val tileLength = result._2
  // process tile
} else {
  // handle missing tile
}
```

## API Test: `gridToModel`

### Signature
```scala
def gridToModel(i: Double, j: Double, outPoint: Point2D.Double): Unit
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:150_

_Source doc:_ Converts a point location from the grid (pixel) space to the model (world) space @param i the position of the column @param j the position of the row @param outPoint the output point that contains the model coordinates

### Goal
Converts a pixel's column and row coordinates (grid space) into real-world geographic coordinates (model space) using the raster's affine transformation metadata.

### Parameters
- `i` (`Double`): The column index (x-axis in grid space) of the pixel location.
- `j` (`Double`): The row index (y-axis in grid space) of the pixel location.
- `outPoint` (`Point2D.Double`): A pre-allocated mutable point object that will be updated in-place to store the resulting real-world X (longitude/easting) and Y (latitude/northing) coordinates.

### Input
Requires a valid `RasterMetadata` instance (often accessed via `reader.metadata` from a `GeoTiffReader` or created manually) to act as the receiver. The caller must also instantiate and provide a `java.awt.geom.Point2D.Double` object to hold the output. The `i` and `j` values typically fall within `0` and the raster's width/height, though the affine transformation will mathematically compute coordinates for out-of-bounds indices as well.

### Output
Returns `Unit` — the result is written in-place to the provided `outPoint` parameter, updating its `x` and `y` fields to the computed model (world) coordinates.

### Valid Call Patterns
```scala
import java.awt.geom.Point2D

// Assuming `reader` is an initialized GeoTiffReader or `metadata` is a RasterMetadata instance
val outPoint = new Point2D.Double()

// Transform the origin point (top-left corner) from raster grid to world coordinates
reader.metadata.gridToModel(0.0, 0.0, outPoint)

// outPoint.x and outPoint.y now contain the geographic coordinates
println(s"World X: ${outPoint.x}, World Y: ${outPoint.y}")
```

### LLM Instruction Prompt
- Always pre-allocate a `java.awt.geom.Point2D.Double` before calling `gridToModel`.
- Remember that `gridToModel` returns `Unit` and mutates the `outPoint` argument in-place. Do not attempt to assign its return value to a variable.
- Call this method on a `RasterMetadata` instance (e.g., `metadata.gridToModel(...)`).
- Note the parameter order: `i` is the column (x-axis in grid), and `j` is the row (y-axis in grid).

### Prompt Snippet
```text
To convert raster pixel coordinates to world coordinates in RDPro, instantiate a `new java.awt.geom.Point2D.Double()`, then call `metadata.gridToModel(col, row, outPoint)`. The method returns `Unit` and mutates `outPoint` in-place. Do not expect a returned tuple or point object.
```

### Common Failure Modes
- **Assigning the Return Value:** Python/rasterio users often expect an affine transform to return a tuple `(x, y)`. In RDPro, `gridToModel` returns `Unit`, so assigning it (e.g., `val pt = metadata.gridToModel(i, j, outPoint)`) results in a `Unit` type mismatch if `pt` is later used as a geometry.
- **Null Pointer Exception:** Passing `null` instead of a pre-instantiated `Point2D.Double` for the `outPoint` parameter will cause a runtime crash.
- **Coordinate Swapping:** Passing the row as `i` and the column as `j`. `i` must be the column (width/x dimension) and `j` must be the row (height/y dimension).

### Fix Code Hint
```scala
// WRONG: Expecting a returned point
// val worldPt = reader.metadata.gridToModel(col, row, new Point2D.Double())

// RIGHT: Mutating a pre-allocated point in-place
val worldPt = new java.awt.geom.Point2D.Double()
reader.metadata.gridToModel(col, row, worldPt)
// Use worldPt.x and worldPt.y
```

## API Test: `hdfFile`

### Signature
```scala
def hdfFile(path: String, layer: String, opts: BeastOptions = new BeastOptions()): RDD[ITile[Float]]
def hdfFile(filename: String, layer: String): JavaRasterRDD[Float]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:46  (+1 more definition site/overload)_

### Goal
Reads a Hierarchical Data Format (HDF) file or a directory of HDF files into a distributed raster RDD, extracting a specific data layer for pixel-level processing.

### Parameters
- `path` (`String`): The path to the HDF file or a directory containing HDF files.
- `layer` (`String`): The specific layer name to read from the HDF file (e.g., `"LST_Day_1km"`).
- `opts` (`BeastOptions`), default `new BeastOptions()`: Optional configuration for reading the file.

### Input
Requires an initialized SparkContext (`sc`) or `JavaSpatialSparkContext` with Beast extensions loaded. The input must be a valid HDF file (or directory of HDF files) accessible to the Spark cluster, and the specified `layer` must exist within the file's hierarchical structure. 

### Output
Returns `RDD[ITile[Float]]` (often aliased as `RasterRDD[Float]`) — a distributed collection of raster tiles containing the pixel data from the specified HDF layer, represented as 32-bit floats.

### Valid Call Patterns
```scala
// Load a specific layer from an HDF file using the SparkContext extension
val temperatureK: RasterRDD[Float] = sc.hdfFile("MOD11A1.A2022173.h08v05.006.2022174092443.hdf", "LST_Day_1km")

// Perform pixel math and save the result (must be saved as GeoTIFF, not HDF)
val temperatureF: RasterRDD[Float] = temperatureK.mapPixels(k => (k - 273.15f) * 9 / 5 + 32)
temperatureF.saveAsGeoTiff("temperature_f")
```

### LLM Instruction Prompt
- Call `hdfFile` as an extension method on the `SparkContext` (e.g., `sc.hdfFile(...)`).
- You MUST provide both the `path` and the `layer` name; HDF files contain multiple sub-datasets, so a layer name is strictly required.
- The returned RDD is always typed to `Float` (`RDD[ITile[Float]]`), as float values are represented in 32-bits in RDPro.
- Do not attempt to save the output back to HDF format. RDPro only supports GeoTIFF as a raster output format.

### Prompt Snippet
```text
To load HDF rasters in RDPro, use `sc.hdfFile(path, layer)`. It requires both the file path and the specific layer name to extract. It always returns an `RDD[ITile[Float]]` (or `RasterRDD[Float]`). If you need to save the processed raster, you must use `saveAsGeoTiff` as HDF output is not supported.
```

### Common Failure Modes
- **Missing Layer Argument:** Attempting to call `sc.hdfFile(path)` without specifying the layer name will fail to compile.
- **Unsupported Output Format:** Attempting to save the resulting RDD back to an HDF file. RDPro only supports writing rasters to GeoTIFF.
- **Incorrect Type Parameter:** Attempting to type the output as `RDD[ITile[Int]]`. `hdfFile` strictly returns `Float` tiles.

### Fix Code Hint
```scala
// WRONG: Missing layer name
// val raster = sc.hdfFile("MOD11A1.A2022173.h08v05.006.2022174092443.hdf")

// WRONG: Attempting to save back to HDF
// raster.saveAsHDF("output.hdf")

// CORRECT: Provide layer name and save as GeoTIFF
val raster: RDD[ITile[Float]] = sc.hdfFile("MOD11A1.A2022173.h08v05.006.2022174092443.hdf", "LST_Day_1km")
raster.saveAsGeoTiff("output_geotiff")
```

## API Test: `id`

### Signature
```scala
def id: Int
```
_Source: beast/dataExplorer/src/main/scala/edu/ucr/cs/bdlab/beast/dataExplorer/DatasetProcessor.scala:58_

### Goal
Retrieves the unique integer identifier of the current object (such as a `DatasetProcessor` handling spatial data exploration tasks).

### Parameters
_None._

### Input
An initialized instance of the class defining this method (e.g., a `DatasetProcessor` instance). No arguments are passed to the method.

### Output
Returns `Int` — the unique integer representing the identifier of the object or dataset.

### Valid Call Patterns
```scala
// Note: Call form is inferred from the signature (not verified by examples)
val processorId: Int = datasetProcessor.id
```

### LLM Instruction Prompt
- Call `id` without parentheses, as it is defined as a parameterless method.
- Expect an `Int` return type; do not treat the identifier as a `String` or UUID.
- Only call this on objects known to expose it (e.g., `DatasetProcessor`), as it is not a universal Spark RDD method in this specific context.

### Prompt Snippet
```text
To retrieve the integer identifier for the dataset processor, call `.id` without parentheses. Ensure you assign the result to an `Int`.
```

### Common Failure Modes
- **Syntax Error (Parentheses):** Calling `obj.id()` with parentheses will cause a compilation error because the method is defined without them (`def id: Int`).
- **Type Mismatch:** Attempting to assign the result to a `String` or using string-specific methods on the returned value without calling `.toString` first.

### Fix Code Hint
```scala
// ❌ Incorrect: Using parentheses or expecting a String
// val strId: String = datasetProcessor.id()

// ✅ Correct: No parentheses, returns Int
val currentId: Int = datasetProcessor.id
```

## API Test: `initialized`

### Signature
```scala
def initialized: Boolean
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/shapefilev2/ShapefileReader.scala:48_

_Source doc:_ A flag that is raised after the file has been initialized

### Goal
Checks whether the underlying spatial file reader (such as a `ShapefileReader`) has completed its initialization phase and is ready to process data.

### Parameters
_None._

### Input
An instantiated low-level file reader object (e.g., `ShapefileReader`) that manages the loading of spatial data formats. 

### Output
Returns `Boolean` — `true` if the file reader has been successfully initialized; `false` otherwise.

### Valid Call Patterns
```scala
// Note: This example is inferred from the signature (not verified) as no direct examples were provided in the context.
val isReady: Boolean = reader.initialized
```

### LLM Instruction Prompt
- Use `initialized` only when manually interacting with low-level Beast readers (like `ShapefileReader`) to verify that the reader's setup phase is complete.
- For standard Spark workflows, prefer high-level context extensions (e.g., `sc.shapefile`, `sc.geoTiff[T]`) which handle reader instantiation and initialization automatically.
- Do not pass any arguments to `initialized`.

### Prompt Snippet
```text
When working with low-level Beast file readers, use `reader.initialized` to check if the file has been successfully initialized before attempting to read records. Note that standard Spark workflows should use `sc.shapefile` instead of manual readers.
```

### Common Failure Modes
- Attempting to extract records or metadata from a low-level reader before `initialized` returns `true`, which can lead to uninitialized state errors.
- Manually managing reader state in distributed Spark transformations instead of relying on Beast's built-in `SparkContext` extensions.

### Fix Code Hint
```scala
// Instead of manually managing low-level readers and checking initialization:
// val isReady = reader.initialized

// Prefer high-level context extensions which manage reader initialization internally:
val features = sc.shapefile("ne_10m_admin_0_countries.zip")
```

## API Test: `isCW`

### Signature
```scala
def isCW: Boolean
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/LiteGeometry.scala:97_

_Source doc:_ Checks whether this list of points form a closed ring stored in CW order @return `true` if the points form a ring and the ring is stored in clock-wise order

### Goal
Checks whether a sequence of points (such as a polygon ring) forms a closed ring and is stored in clockwise (CW) order, typically used to validate winding rules during vector tile generation.

### Parameters
_None._

### Input
A lightweight geometry ring (e.g., an element from `LitePolygon.parts` generated during Mapbox Vector Tile simplification) representing a sequence of coordinates.

### Output
Returns `Boolean` — `true` if the points form a closed ring and are ordered clockwise; `false` otherwise (e.g., if it is counter-clockwise or not a closed ring).

### Valid Call Patterns
```scala
// Assuming simplifiedPolygon is a LitePolygon generated by IntermediateVectorTile
val litePoly = simplifiedPolygon.asInstanceOf[LitePolygon]
val isOuterRingCW = litePoly.parts(0).isCW
```

### LLM Instruction Prompt
- Use `isCW` without parentheses to check the winding order of a lightweight geometry ring.
- Apply this method to parts of a `LitePolygon` (e.g., `litePoly.parts(0)`) during visualization or Mapbox Vector Tile (MVT) generation to verify that outer shells are clockwise and holes are counter-clockwise.
- Do not attempt to call `isCW` directly on standard JTS `Polygon` or `LinearRing` objects; it is specific to Beast's internal lightweight geometry representations.

### Prompt Snippet
```text
To verify polygon winding order for vector tiles, use `isCW` on a lightweight geometry ring. Example: `litePolygon.parts(0).isCW`. Returns true if the ring is closed and clockwise.
```

### Common Failure Modes
- **Calling on standard JTS geometries:** Attempting to call `isCW` directly on a standard JTS `Polygon` or `LinearRing`. The method belongs to Beast's internal lightweight geometry parts (`LiteGeometry`) used in visualization.
- **Unclosed rings:** Calling `isCW` on a sequence of points that do not form a closed ring (where the first and last points are not identical) will return `false`.

### Fix Code Hint
```scala
// WRONG: Calling on a JTS Polygon
// val isClockwise = jtsPolygon.isCW

// RIGHT: Calling on a Beast LitePolygon part during visualization/MVT generation
val isClockwise = litePolygon.parts(0).isCW
```

## API Test: `isDefined`

### Signature
```scala
def isDefined(i: Int, j: Int): Boolean
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:126_

_Source doc:_ Checks if the given pixel is defined (not empty) @param i the index of the column @param j the index of the row @return `true` if pixel has a valid value or `false` if it does not.

### Goal
Checks whether a specific pixel at column `i` and row `j` within a raster tile contains a valid (non-empty or non-NoData) value.

### Parameters
- `i` (`Int`): The index of the column for the pixel within the tile.
- `j` (`Int`): The index of the row for the pixel within the tile.

### Input
An instance of `ITile[T]` (typically accessed when iterating over pixels in a `RasterRDD` or during custom tile-level operations). The caller must provide valid integer indices `i` and `j` that fall within the bounds of the tile's dimensions.

### Output
Returns `Boolean` — `true` if the pixel has a valid data value, or `false` if it is empty (e.g., represents a NoData value in the underlying GeoTIFF or HDF).

### Valid Call Patterns
```scala
// Inferred from the signature (not verified in test suite).
// Note: The test suite examples show Scala's standard Option.isDefined (0 arguments).
// This pattern applies to RDPro's ITile.isDefined(i, j).

// Assuming `tile` is an ITile[T] and we are iterating over its dimensions:
val isValid: Boolean = tile.isDefined(i, j)

if (isValid) {
  // Safe to process the pixel value
}
```

### LLM Instruction Prompt
- When performing pixel-level math or custom raster processing on an `ITile`, always use `tile.isDefined(i, j)` to check for NoData or empty pixels before attempting to read or transform the pixel value. 
- Do not confuse `ITile.isDefined(i: Int, j: Int)` with Scala's standard `Option.isDefined` (which takes no arguments). Ensure you pass the column and row indices.

### Prompt Snippet
```text
// Check if a pixel is valid before applying band math
if (tile.isDefined(col, row)) {
  val pixelValue = tile.getPixelValue(col, row)
  // ...
}
```

### Common Failure Modes
- **Index Out of Bounds:** Passing `i` or `j` values that are less than 0 or greater than or equal to the tile's width or height, respectively, which may throw an exception depending on the underlying tile implementation.
- **Method Signature Confusion:** Attempting to call `isDefined` without arguments on an `ITile`, confusing it with `Option.isDefined`. The compiler will fail because `ITile.isDefined` requires exactly two `Int` arguments.

### Fix Code Hint
```scala
// WRONG: Confusing ITile.isDefined with Option.isDefined
if (tile.isDefined) { ... }

// RIGHT: Passing the specific column and row indices
if (i >= 0 && i < tile.tileWidth && j >= 0 && j < tile.tileHeight) {
  if (tile.isDefined(i, j)) {
    // Process valid pixel
  }
}
```

## API Test: `isEmptyAt`

### Signature
```scala
def isEmptyAt(x: Double, y: Double): Boolean
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:114_

_Source doc:_ Check if the pixel that contains the given location is empty @param x the x-coordinate of the point, e.g., longitude @param y the y-coordinate of the point, e.g., latitude @return `true` if the pixel at the location is empty, i.e., contains no data

### Goal
Checks if the specific spatial location (x, y) falls into a "no data" (empty) pixel within a raster tile.

### Parameters
- `x` (`Double`): The x-coordinate of the point (e.g., longitude) in the same coordinate reference system (CRS) as the raster tile.
- `y` (`Double`): The y-coordinate of the point (e.g., latitude) in the same coordinate reference system (CRS) as the raster tile.

### Input
An `ITile[T]` instance (e.g., obtained from a `GeoTiffReader` or an RDD of tiles). The coordinates provided must be in the spatial reference system of the tile. For this method to accurately detect empty pixels, the underlying raster reader must be aware of the dataset's "no data" or "fill" value (e.g., configured via `"fillvalue"` during reader initialization).

### Output
Returns `Boolean` — `true` if the pixel containing the (x, y) location is empty (contains no data / matches the fill value), `false` otherwise.

### Valid Call Patterns
```scala
// Assuming an initialized GeoTiffReader[Int] named `reader`
val x = 23.224
val y = 32.415

// Fetch the specific tile containing the point
val tileID = reader.metadata.getTileIDAtPoint(x, y)
val tile = reader.readTile(tileID)

// Check if the pixel at the spatial coordinates is empty (no-data)
val isNoData = tile.isEmptyAt(x, y)
```

### LLM Instruction Prompt
- When checking if a spatial location falls on a no-data pixel within an `ITile`, use `tile.isEmptyAt(x, y)`. Ensure `x` and `y` are in the raster's coordinate reference system. Do not confuse spatial coordinates (x, y) with pixel grid coordinates (col, row).

### Prompt Snippet
```text
To check if a spatial location falls on a no-data pixel within an `ITile`, use `tile.isEmptyAt(x, y)`. Ensure `x` and `y` are in the raster's coordinate reference system. The tile must have a defined fill value for this to work accurately.
```

### Common Failure Modes
- **Unconfigured Fill Value:** If the raster's "no data" value is not properly defined in the file metadata or overridden during reader initialization, `isEmptyAt` may return `false` for pixels that are conceptually empty.
- **Coordinate System Mismatch:** Passing unprojected coordinates (e.g., WGS84 lat/lon) to a tile that is in a projected CRS (e.g., Web Mercator). The `x` and `y` must match the tile's CRS.
- **Out of Bounds:** Querying coordinates that do not spatially intersect the specific `ITile` instance being queried.

### Fix Code Hint
```scala
// Ensure the reader is initialized with the correct fill value so isEmptyAt works
val reader = new GeoTiffReader[Int]
reader.initialize(fileSystem, rasterPath, "0", "fillvalue" -> 8) // 8 is the no-data value

val tile = reader.readTile(reader.metadata.getTileIDAtPoint(lon, lat))
if (!tile.isEmptyAt(lon, lat)) {
  // Process valid data
}
```

## API Test: `isSpatiallyPartitioned`

### Signature
```scala
def isSpatiallyPartitioned: Boolean
def isSpatiallyPartitioned(rdd: JavaSpatialRDD): Boolean
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:45  (+1 more definition site/overload)_

_Source doc:_ Tells whether a SpatialRDD is partitioned using any spatial partitioner or not @return {@code true} if the RDD is partitioned using any spatial partitioner

### Goal
Evaluates whether a SpatialRDD is distributed across the Spark cluster using a specialized spatial partitioner (such as R*-Grove, Grid, KDTree, or STR).

### Parameters
- `rdd` (`JavaSpatialRDD`): The Java-based spatial RDD to evaluate (applicable only to the Java API overload; the Scala API operates as a parameterless extension method on the RDD).

### Input
A loaded spatial RDD (e.g., vector features loaded via `sc.shapefile`, `sc.geojsonFile`, or `sc.readCSVPoint`). The RDD does not need to be partitioned to call this method, as its purpose is to check that exact state.

### Output
Returns `Boolean` — `true` if the RDD is currently partitioned using any spatial partitioner, and `false` if it has default Spark partitioning or no spatial partitioner attached.

### Valid Call Patterns
```scala
// Inferred from signature (Scala extension method)
val isPartitioned: Boolean = features.isSpatiallyPartitioned

// Inferred from signature (Java API overload)
val isPartitionedJava: Boolean = JavaSpatialRDDHelper.isSpatiallyPartitioned(javaRdd)
```

### LLM Instruction Prompt
- Use `isSpatiallyPartitioned` to verify the partitioning state of a dataset before executing distributed spatial joins. 
- Enforce spatial join preconditions: The Distributed Join (`DJ`) algorithm requires *both* datasets to return `true` for `isSpatiallyPartitioned`. The Repartition Join (`REPJ`) requires at least *one* dataset to return `true`.
- If a dataset is not spatially partitioned, apply `rdd.spatialPartition(classOf[RSGrovePartitioner])` (or another valid partitioner) before joining.

### Prompt Snippet
```text
Check `rdd.isSpatiallyPartitioned` before performing spatial joins. If using `ESJDistributedAlgorithm.DJ`, both RDDs must be spatially partitioned. If false, partition the data using `rdd.spatialPartition(classOf[RSGrovePartitioner])` first.
```

### Common Failure Modes
- **Algorithm Precondition Violation:** Forcing the `DJ` (Distributed Join) algorithm on datasets where `isSpatiallyPartitioned` is `false`. This violates the algorithm's requirement that both datasets be spatially partitioned first.
- **Assuming Implicit Partitioning:** Assuming an RDD is spatially partitioned simply because it contains spatial data or was loaded from a spatial file format. Spatial partitioning must be explicitly triggered.

### Fix Code Hint
```scala
// Check and partition if necessary before a DJ spatial join
val preparedFeatures = if (!features.isSpatiallyPartitioned) {
  features.spatialPartition(classOf[RSGrovePartitioner])
} else {
  features
}
```

## API Test: `lastNFiles`

### Signature
```scala
def lastNFiles(fs: FileSystem, path: Path, n: Int): Array[(String, Long, Long)]
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/ZipUtil.scala:48_

_Source doc:_ Returns information about the last n files in the archive. **Compatibility Note**: This method is not guaranteed to return the correct answer. For efficiency, it tries to locate the directory entries from the end using the ZIP signature. In rare cases, it might retrieve false information since the signature might appear out of coincidence. To be accurate, this method has to read all ZIP entries until it finds the last ones because directory entries are variable size in ZIP. @param fs the file system that contains the ZIP archive @param path the path to the ZIP file @param n the number of entries to retrieve from the end @return file names, offsets, and lengths for the last n entries if the ZIP file contains at least n entries. Otherwise, it returns all entries in the file.

### Goal
Retrieves the file names, byte offsets, and lengths of the last `n` entries in a ZIP archive (such as a compressed shapefile) by efficiently scanning from the end of the file.

### Parameters
- `fs` (`FileSystem`): The Hadoop `FileSystem` instance that contains the target ZIP archive.
- `path` (`Path`): The Hadoop `Path` pointing to the ZIP or ZIP64 file.
- `n` (`Int`): The number of file entries to retrieve from the end of the archive.

### Input
A valid ZIP or ZIP64 archive (e.g., a compressed Esri Shapefile) accessible via the provided Hadoop `FileSystem`. The file must exist and be readable. 

### Output
Returns `Array[(String, Long, Long)]` — an array of tuples where each tuple contains `(fileName, offset, length)` for the last `n` entries. If the ZIP file contains fewer than `n` entries, it returns all entries in the file.

### Valid Call Patterns
```scala
import org.apache.hadoop.fs.{FileSystem, Path}
import org.apache.hadoop.conf.Configuration
import edu.ucr.cs.bdlab.beast.util.ZipUtil

val fileSystem = FileSystem.getLocal(new Configuration())
val zipPath = new Path("data/ne_10m_admin_0_countries.zip")

// Retrieve the last 2 files in the ZIP archive
val lastFiles: Array[(String, Long, Long)] = ZipUtil.lastNFiles(fileSystem, zipPath, 2)

// Accessing the results
val fileName = lastFiles(0)._1
val offset = lastFiles(0)._2
val length = lastFiles(0)._3
```

### LLM Instruction Prompt
- Call `ZipUtil.lastNFiles(fs, path, n)` to quickly inspect the tail entries of a ZIP archive without scanning the entire file.
- **Warning:** Document that this method uses a heuristic (searching for the ZIP signature from the end of the file) for efficiency. It is not 100% guaranteed to be accurate, as the signature bytes could theoretically appear by coincidence within compressed data.
- Use the returned `offset` (`_2`) and `length` (`_3`) to seek and read specific files directly from the `FileSystem` input stream.

### Prompt Snippet
```text
`ZipUtil.lastNFiles(fs: FileSystem, path: Path, n: Int): Array[(String, Long, Long)]` efficiently gets the (name, offset, length) of the last `n` files in a ZIP. Note: Uses a heuristic signature scan from the end; rarely, coincidental byte matches may yield false info.
```

### Common Failure Modes
- **False Positives (Heuristic Failure):** Because the method scans backwards for the ZIP directory signature to save time, it might accidentally match identical byte sequences occurring naturally inside the compressed data, returning corrupted or incorrect file offsets.
- **File Not Found:** Providing a `Path` that does not exist on the specified `FileSystem` will throw an exception when the method attempts to open the file.

### Fix Code Hint
```scala
// To safely read the extracted file data using the returned offset and length:
val in = fileSystem.open(zipPath)
try {
  val targetFile = lastFiles(0)
  in.seek(targetFile._2) // Seek to the offset
  val data = new Array[Byte](targetFile._3.toInt) // Allocate array of 'length' size
  in.readFully(data)
  // Process 'data' bytes here
} finally {
  in.close()
}
```

## API Test: `listFilesInZip`

### Signature
```scala
def listFilesInZip(fileSystem: fs.FileSystem, zipFilePath: Path): Array[(String, Long, Long)]
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/ZipUtil.scala:478_

_Source doc:_ List all files contained in the given ZIP file @param fileSystem the file system that contains the zip file @param zipFilePath the ZIP file to return its contents @return

### Goal
Lists all files contained within a ZIP archive (including ZIP64) on a Hadoop `FileSystem`, returning their names, byte offsets, and sizes to enable direct random-access reading without full extraction.

### Parameters
- `fileSystem` (`fs.FileSystem`): The Hadoop `FileSystem` instance (e.g., `FileSystem.getLocal(new Configuration())`) that hosts the target ZIP file.
- `zipFilePath` (`Path`): The Hadoop `Path` pointing to the ZIP file whose contents are to be listed.

### Input
A valid ZIP or ZIP64 archive file (such as a compressed Esri Shapefile archive) accessible via the provided Hadoop `FileSystem`. The caller must provide Hadoop-native `FileSystem` and `Path` objects, not standard `java.io.File` or `String` paths.

### Output
Returns `Array[(String, Long, Long)]` — An array of tuples where each tuple represents a file inside the archive. The tuple elements are:
1. `_1` (`String`): The name of the file inside the ZIP.
2. `_2` (`Long`): The starting byte offset of the file's data within the ZIP archive (useful for `FSDataInputStream.seek()`).
3. `_3` (`Long`): The uncompressed size of the file in bytes.

### Valid Call Patterns
```scala
import org.apache.hadoop.fs.{FileSystem, Path}
import org.apache.hadoop.conf.Configuration
import edu.ucr.cs.bdlab.beast.util.ZipUtil

// 1. Initialize FileSystem and Path
val fileSystem = FileSystem.getLocal(new Configuration())
val zipPath = new Path("/path/to/shapefile_archive.zip")

// 2. List files in the ZIP
val contents: Array[(String, Long, Long)] = ZipUtil.listFilesInZip(fileSystem, zipPath)

// 3. Example: Random-access read of a specific file using offset and size
val firstFile = contents.head
val fileName = firstFile._1
val byteOffset = firstFile._2
val byteSize = firstFile._3

val in = fileSystem.open(zipPath)
in.seek(byteOffset)
val data = new Array[Byte](byteSize.toInt)
in.readFully(data)
in.close()
```

### LLM Instruction Prompt
- Call `ZipUtil.listFilesInZip(fileSystem, path)` as a static utility method on `ZipUtil`.
- Remember the return type is an array of tuples: `(String, Long, Long)` mapping to `(filename, byteOffset, byteSize)`.
- Do not invent a `java.io.File` or `String` overload; the method strictly requires a Hadoop `Path` and `FileSystem`.
- When using the returned `byteSize` (the third tuple element) to allocate an in-memory `Array[Byte]`, you must cast it to an integer using `.toInt`.

### Prompt Snippet
```text
edu.ucr.cs.bdlab.beast.util.ZipUtil.listFilesInZip(fileSystem: org.apache.hadoop.fs.FileSystem, zipFilePath: org.apache.hadoop.fs.Path): Array[(String, Long, Long)] // Returns array of (filename, byteOffset, byteSize)
```

### Common Failure Modes
- **Type Mismatch on Path:** Passing a `java.io.File` or a `String` instead of an `org.apache.hadoop.fs.Path`.
- **Type Mismatch on Array Allocation:** Attempting to use the returned file size (`Long`) directly to initialize a Scala `Array[Byte]`, which requires an `Int`.
- **Missing Object Qualifier:** Calling `listFilesInZip(...)` as a bare function instead of qualifying it with `ZipUtil`.

### Fix Code Hint
```scala
// WRONG: ZipUtil.listFilesInZip(fs, "/path/to/file.zip")
// WRONG: val data = new Array[Byte](contents(0)._3) // _3 is a Long

// CORRECT:
val zipPath = new Path("/path/to/file.zip")
val contents = ZipUtil.listFilesInZip(fileSystem, zipPath)
val data = new Array[Byte](contents(0)._3.toInt) // Cast Long to Int for array size
```

## API Test: `makeBoxes`

### Signature
```scala
def makeBoxes(maxSize: Int*): JavaSpatialGeneratorBuilder
def makeBoxes(maxSize: Double*): SpatialGeneratorBuilder
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:76  (+1 more definition site/overload)_

_Source doc:_ Generate boxes around each generated point. The size is measured as a fraction [0, 1] to indicate the ratio of the dataset bounding box. Any value above 1.0 is invalid. @param maxSize the maximum size for each side length of the generated box @return this generator builder

### Goal
Configure a spatial data generator to produce bounding boxes (envelopes) around generated points, typically used for benchmarking spatial joins or indexing.

### Parameters
- `maxSize` (`Int*` or `Double*`): The maximum size for each side length of the generated box. This is measured as a fraction `[0.0, 1.0]` indicating the ratio of the dataset's total bounding box. Any value above `1.0` is invalid. Multiple values can be provided for multi-dimensional boxes (e.g., width and height).

### Input
A `SpatialGeneratorBuilder` or `JavaSpatialGeneratorBuilder` instance, typically initialized via the SparkContext extension `sc.generateSpatialData`. No external files or datasets are required, as this is a synthetic data generation API.

### Output
Returns `SpatialGeneratorBuilder` (or `JavaSpatialGeneratorBuilder`), allowing method chaining to finalize the generation process (e.g., by calling `.uniform(N)` to generate an RDD of spatial features).

### Valid Call Patterns
```scala
// Generate 1,000,000 boxes with max width 30% and max height 40% of the total MBR
val boxesRDD = sparkContext.generateSpatialData
  .makeBoxes(0.3, 0.4)
  .uniform(1000000)

// Generate 100 boxes and plot them to an image
sc.generateSpatialData
  .makeBoxes(0.1, 0.2)
  .uniform(100)
  .plotImage(300, 300, "uniform.png")
```

### LLM Instruction Prompt
- Use `makeBoxes` on a `SpatialGeneratorBuilder` (via `sc.generateSpatialData`) when you need to generate synthetic polygon/envelope data for benchmarking.
- You MUST provide `maxSize` as a fraction between `0.0` and `1.0`. Do not provide absolute map units.
- You MUST chain a terminal generation method like `.uniform(numRecords)` after `makeBoxes` to actually produce the `SpatialRDD`.

### Prompt Snippet
```text
To generate synthetic bounding boxes in Beast, use `sc.generateSpatialData.makeBoxes(widthFraction, heightFraction).uniform(numRecords)`. The `maxSize` arguments must be fractions between 0.0 and 1.0 representing the ratio of the total bounding box. Values > 1.0 are invalid.
```

### Common Failure Modes
- **Invalid Size Fraction:** Passing a `maxSize` value greater than `1.0` (e.g., passing absolute map units like `1000.0` instead of a fraction like `0.1`). This violates the `[0, 1]` constraint and is invalid.
- **Missing Terminal Operation:** Calling `makeBoxes` but forgetting to call a generation method like `.uniform(N)`, resulting in a builder object instead of an actual `SpatialRDD`.

### Fix Code Hint
```scala
// ❌ BAD: Passing absolute sizes (> 1.0) and forgetting the terminal generation call
val badBoxes = sc.generateSpatialData.makeBoxes(500.0, 500.0)

// ✅ GOOD: Passing fractions [0, 1] and chaining .uniform(N) to create the RDD
val goodBoxes = sc.generateSpatialData
  .makeBoxes(0.05, 0.05)
  .uniform(10000)
```

## API Test: `mapPixels`

### Signature
```scala
def mapPixels[U: ClassTag](f: T => U)
def mapPixels[T: ClassTag, U: ClassTag](inputRaster: RasterRDD[T], f: T => U): RasterRDD[U]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsLocal.scala:38  (+1 more definition site/overload)_

_Source doc:_ Apply a user-defined function for each pixel in the input raster to produce the output raster @param inputRaster the input raster RDD @param f the function to apply on each input pixel value to produce the output pixel value @tparam T the type of pixels in the input @tparam U the type of pixels in the output @return the resulting RDD

### Goal
Apply a user-defined function to every pixel in a distributed raster dataset (e.g., for band math, unit conversion, or thresholding) to produce a new raster with transformed values.

### Parameters
- `inputRaster` (`RasterRDD[T]`): The input distributed raster dataset containing the pixels to be transformed. When using the extension method overload, this is the receiver object (e.g., `raster.mapPixels(...)`).
- `f` (`T => U`): A lambda function applied to each individual pixel value, where `T` is the input pixel type and `U` is the resulting output pixel type.

### Input
A `RasterRDD[T]` (which is an alias for `RDD[ITile[T]]`) typically loaded from a GeoTIFF (`sc.geoTiff[T]`) or HDF file (`sc.hdfFile`). 
**Preconditions & Type Rules:** The type parameter `T` must exactly match the runtime pixel type of the source data. For example, if the source GeoTIFF has `IntegerType` pixels, it must be loaded as `sc.geoTiff[Int]` and `f` must be of type `Int => U`.

### Output
Returns `RasterRDD[U]` — A new distributed raster dataset containing the transformed pixel values of type `U`. The output retains the exact spatial metadata, resolution, CRS, and tiling structure of the input raster. It can be subsequently saved as a GeoTIFF.

### Valid Call Patterns
```scala
// Pattern 1: Instance method (Preferred, from README)
val temperatureK: RasterRDD[Float] = sc.hdfFile("MOD11A1.hdf", "LST_Day_1km")
val temperatureF: RasterRDD[Float] = temperatureK.mapPixels(k => (k - 273.15f) * 9 / 5 + 32)
temperatureF.saveAsGeoTiff("temperature_f")

// Pattern 2: Static method (from Test Suite)
val inputRaster: RDD[ITile[Short]] = sparkContext.parallelize(Seq(inputTile))
val outputRaster: RDD[ITile[Int]] = RasterOperationsLocal.mapPixels(inputRaster, (x: Short) => Math.max(x, 50))
```

### LLM Instruction Prompt
- Use `mapPixels` for per-pixel mathematical transformations, such as computing NDVI, converting units, or applying thresholds.
- Prefer the instance method syntax `raster.mapPixels(f)`.
- Ensure the lambda function `f` accepts the exact numeric type of the input raster (`T`) and returns the desired output type (`U`).
- Do NOT use `mapPixels` to change raster resolution, CRS, or tile size; use `RasterOperationsFocal.reshapeNN` or `reshapeAverage` for spatial reshaping.
- If the output type `U` is `Float`, remember that `GeoTiffWriter.CompactBits` cannot be used when saving the output, as bit compaction only works with integer pixel values.

### Prompt Snippet
```text
To perform pixel-level math on a RasterRDD in RDPro, use `raster.mapPixels(f: T => U)`. The input type `T` must match the loaded raster's pixel type (e.g., `Int` or `Float`). The output is a new `RasterRDD[U]` with identical spatial metadata, which can be saved via `saveAsGeoTiff`.
```

### Common Failure Modes
- **Type Mismatch on Load/Map:** Loading a float-based GeoTIFF as `sc.geoTiff[Int]` or applying a `Float => Float` function to a `RasterRDD[Int]`. The generic type `T` must strictly align with the underlying file's data type.
- **Bit Compaction Crash on Save:** Mapping integer pixels to float pixels (e.g., `Int => Float` for an index calculation) and then attempting to save the result using `GeoTiffWriter.CompactBits`. Float values are always represented in 32-bits and do not support bit compaction.
- **Missing ClassTags:** If wrapping `mapPixels` in a generic helper function, failing to provide `[T: ClassTag, U: ClassTag]` context bounds will cause compilation errors because Spark requires ClassTags to serialize the resulting RDD.

### Fix Code Hint
```scala
// BAD: Type mismatch (assuming the file actually contains Float pixels)
val raster = sc.geoTiff[Int]("ndvi_data.tif")
val scaled = raster.mapPixels(p => p * 1.5f) // p is Int, returns Float

// GOOD: Match the runtime type and explicitly type the output
val raster: RasterRDD[Float] = sc.geoTiff[Float]("ndvi_data.tif")
val scaled: RasterRDD[Float] = raster.mapPixels(p => p * 1.5f)
scaled.saveAsGeoTiff("scaled_ndvi")
```

## API Test: `mbr`

### Signature
```scala
def mbr : EnvelopeNDLite
def mbr: EnvelopeNDLite
def mbr(mbr: EnvelopeNDLite): SpatialGeneratorBuilder
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/SpatialGeneratorBuilder.scala:97  (+2 more definition site/overload)_

_Source doc:_ Generates data in the given bounding box @param mbr the bounding box of the generated data @return

### Goal
Sets the bounding box (Minimum Bounding Rectangle) for generating synthetic spatial data using Beast's distributed Spatial Data Generator (Spider).

### Parameters
- `mbr` (`EnvelopeNDLite`): The bounding box defining the spatial extent within which the synthetic data will be generated. Typically constructed with `new EnvelopeNDLite(dimensions, minX, minY, maxX, maxY)`.

### Input
Requires an active `SparkContext` to initialize the `SpatialGeneratorBuilder` (either via the context extension `sc.generateSpatialData` or `new SpatialGeneratorBuilder(sc)`). The caller must provide a valid `EnvelopeNDLite` representing the desired spatial boundaries.

### Output
Returns `SpatialGeneratorBuilder` — a builder object that allows chaining further configuration (e.g., `.config(...)`) before finalizing the generation with a distribution method (e.g., `.uniform(numRecords)`), which ultimately yields a `SpatialRDD`. The parameterless overloads (`def mbr: EnvelopeNDLite`) act as getters returning the currently set bounding box.

### Valid Call Patterns
```scala
// Pattern 1: Using the SparkContext extension (from README)
val generatedData = sparkContext.generateSpatialData
  .mbr(new EnvelopeNDLite(2, 1.0, 0.0, 4.0, 8.0))
  .uniform(1000)

// Pattern 2: Using the builder constructor directly with configurations (from test suite)
val desiredMBR = new EnvelopeNDLite(2, 2.0, 3.0, 9.0, 8.0)
val randomPoints: SpatialRDD = new SpatialGeneratorBuilder(sparkContext)
  .mbr(desiredMBR)
  .config(UniformDistribution.MaxSize, "0.2,0.1")
  .config(UniformDistribution.NumSegments, 10)
  .config(UniformDistribution.GeometryType, "box")
  .config(SpatialGenerator.Seed, 1794)
  .uniform(10)
```

### LLM Instruction Prompt
- Use `mbr(EnvelopeNDLite)` on a `SpatialGeneratorBuilder` to restrict the spatial extent of generated benchmarking data.
- Always chain this method with a terminal generation action, such as `.uniform(n)`, to actually produce the `SpatialRDD`.
- Construct the `EnvelopeNDLite` using the signature `new EnvelopeNDLite(dimensions, minX, minY, maxX, maxY)`.

### Prompt Snippet
```text
To generate synthetic spatial data within a specific bounding box in Beast, use `sc.generateSpatialData.mbr(new EnvelopeNDLite(2, minX, minY, maxX, maxY))`. You must chain this with a distribution method like `.uniform(numRecords)` to return the actual RDD.
```

### Common Failure Modes
- **Missing Terminal Operation:** Calling `.mbr(...)` without subsequently calling `.uniform(...)` or another distribution method. This leaves the user with a `SpatialGeneratorBuilder` instead of the expected `SpatialRDD` (or `RDD[IFeature]`), causing type mismatch errors in downstream spatial operations.
- **Invalid Envelope Bounds:** Providing an `EnvelopeNDLite` where the minimum bounds exceed the maximum bounds, which can result in empty generated datasets or runtime exceptions during the generation phase.

### Fix Code Hint
```scala
// WRONG: Leaves the builder un-materialized
val badData = sparkContext.generateSpatialData.mbr(new EnvelopeNDLite(2, 0, 0, 10, 10))

// RIGHT: Chains a distribution method to generate the RDD
val goodData = sparkContext.generateSpatialData
  .mbr(new EnvelopeNDLite(2, 0.0, 0.0, 10.0, 10.0))
  .uniform(10000) // Generates 10,000 features
```

## API Test: `mergeWith`

### Signature
```scala
def mergeWith(another: VectorCanvas): VectorCanvas
def mergeWith(opts: BeastOptions): BeastOptions
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/VectorCanvas.scala:440  (+1 more definition site/overload)_

_Source doc:_ Merges this canvas with another vector canvas and returns this canvas after the merge. @param another the other canvas to merge with @return this canvas after the merge so that you can chain a number of mergeWidth operations.

### Goal
Merges the geometries and state of another `VectorCanvas` (or `BeastOptions`) into the current instance, returning the updated instance to allow for fluent method chaining during geospatial visualization or configuration tasks.

### Parameters
- `another` (`VectorCanvas`): The secondary vector canvas whose geometries will be merged into the calling canvas.
- `opts` (`BeastOptions`): *(Overload)* Another set of Beast configuration options to merge into the current options.

### Input
- Two initialized `VectorCanvas` objects containing vector geometries (e.g., points, lines, polygons) added via `addGeometry`.
- **Preconditions:** Both canvases should typically share the same spatial `Envelope` and pixel dimensions (width/height) to ensure that geometries from the second canvas align correctly in the merged coordinate space.

### Output
Returns `VectorCanvas` (or `BeastOptions` for the overload) — The original calling instance, mutated in-place to include the contents of the `another` parameter.

### Valid Call Patterns
```scala
import org.locationtech.jts.geom.{Envelope, CoordinateXY}
import edu.ucr.cs.bdlab.beast.geolite.GeometryReader

// Initialize two canvases with identical envelopes and dimensions
val env = new Envelope(0, 1, 0, 1)
val canvas1 = new VectorCanvas(env, 10, 10, 0, 1)
val canvas2 = new VectorCanvas(env, 10, 10, 0, 1)

val factory = GeometryReader.DefaultGeometryFactory

// Add geometries to both canvases
canvas1.addGeometry(factory.createPoint(new CoordinateXY(0, 0)), null)
canvas1.addGeometry(factory.createPoint(new CoordinateXY(0.1, 0.1)), null)

canvas2.addGeometry(factory.createPoint(new CoordinateXY(0.2, 0.2)), null)
canvas2.addGeometry(factory.createPoint(new CoordinateXY(0.3, 0.3)), null)

// Merge canvas2 into canvas1
canvas1.mergeWith(canvas2)
// canvas1 now contains 4 geometries
```

### LLM Instruction Prompt
- Use `mergeWith` to combine two `VectorCanvas` instances during visualization tasks, or to combine two `BeastOptions` configuration objects.
- Remember that `mergeWith` mutates the calling object in-place and returns it.
- When merging `VectorCanvas` objects, ensure both canvases were initialized with the same spatial `Envelope` and pixel dimensions so that the merged geometries share a consistent coordinate space.

### Prompt Snippet
```text
To combine two VectorCanvas objects in Beast's visualization API, use `canvas1.mergeWith(canvas2)`. This mutates `canvas1` by appending `canvas2`'s geometries and returns `canvas1` to allow for method chaining. Ensure both canvases share the same Envelope.
```

### Common Failure Modes
- **Mismatched Envelopes/Dimensions:** Merging canvases that were initialized with different spatial envelopes or pixel dimensions. Because `mergeWith` does not re-project or re-scale geometries that have already been converted to pixel space, the merged geometries will be misaligned.
- **Null Arguments:** Passing `null` instead of a valid `VectorCanvas` or `BeastOptions` object will result in a `NullPointerException`.

### Fix Code Hint
```scala
// Ensure both canvases share the exact same spatial envelope and resolution before merging
val sharedEnvelope = new Envelope(0, 256, 0, 256)
val canvas1 = new VectorCanvas(sharedEnvelope, 256, 256, 0, 1)
val canvas2 = new VectorCanvas(sharedEnvelope, 256, 256, 0, 1)

// ... add geometries ...

// Safe to merge
val mergedCanvas = canvas1.mergeWith(canvas2)
```

## API Test: `mergeZip`

### Signature
```scala
def mergeZip(fileSystem: fs.FileSystem, mergedFile: Path, @varargs zipFiles: Path*): Unit
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/ZipUtil.scala:425_

_Source doc:_ Merges multiple ZIP files into one and deletes the input files. @param mergedFile the output file that contains the merged ZIP files @param zipFiles the input files to be merged

### Goal
Merges multiple ZIP archives (such as distributed outputs for multilevel image pyramids or MVT vector tiles) into a single ZIP file and permanently deletes the original input files.

### Parameters
- `fileSystem` (`fs.FileSystem`): The Hadoop `FileSystem` instance used to resolve and access the file paths (e.g., `FileSystem.getLocal(new Configuration())` or an HDFS file system).
- `mergedFile` (`Path`): The Hadoop `Path` representing the destination output ZIP file that will contain all merged entries.
- `@varargs zipFiles` (`Path*`): A variable-length list of Hadoop `Path` objects representing the input ZIP files to be merged.

### Input
Valid, existing ZIP files located on the provided Hadoop `FileSystem`. The caller must have read access to the input files, write access to the destination directory, and delete permissions for the input files' directories (as the inputs are deleted upon successful merging).

### Output
Returns `Unit` — the operation is performed entirely for its side effects: creating the new merged ZIP file at `mergedFile` and deleting all provided `zipFiles`.

### Valid Call Patterns
```scala
import org.apache.hadoop.fs.{FileSystem, Path}
import org.apache.hadoop.conf.Configuration
import edu.ucr.cs.bdlab.beast.util.ZipUtil

// Initialize the Hadoop FileSystem (local or HDFS depending on environment)
val fileSystem = FileSystem.getLocal(new Configuration())

// Define Hadoop Paths for inputs and output
val file1 = new Path("scratch/test1.zip")
val file2 = new Path("scratch/test2.zip")
val mergedFile = new Path("scratch/merged_output.zip")

// Merge the ZIPs (file1 and file2 will be deleted)
ZipUtil.mergeZip(fileSystem, mergedFile, file1, file2)
```

### LLM Instruction Prompt
- Always call `mergeZip` on the `ZipUtil` object (`ZipUtil.mergeZip(...)`).
- You MUST pass Hadoop `Path` objects for the file arguments, not plain Scala `String` paths.
- You MUST provide a valid Hadoop `FileSystem` instance as the first argument.
- Warn the user that this function is destructive to the inputs: it automatically deletes the input ZIP files after merging them. Do not write code that attempts to read the input files after this call.

### Prompt Snippet
```text
Use `ZipUtil.mergeZip(fileSystem, mergedFile, zipFiles*)` to combine multiple ZIP archives into one. Inputs and outputs must be Hadoop `Path` objects, not strings. Warning: Input files are permanently deleted after merging.
```

### Common Failure Modes
- **Type Mismatch on Paths:** Passing standard `String` file paths instead of Hadoop `Path` objects, causing a compilation error.
- **File Not Found (Post-Execution):** Attempting to access or move the input `zipFiles` after calling `mergeZip`. The function deletes them automatically; subsequent operations on the inputs will throw a `FileNotFoundException`.
- **Missing Permissions:** The Spark/Hadoop user lacks the necessary filesystem permissions to delete the input files, causing the job to crash during the cleanup phase.

### Fix Code Hint
```scala
// WRONG: Passing strings instead of Hadoop Paths
// ZipUtil.mergeZip(fileSystem, "merged.zip", "part1.zip", "part2.zip")

// RIGHT: Wrapping paths in org.apache.hadoop.fs.Path
ZipUtil.mergeZip(fileSystem, new Path("merged.zip"), new Path("part1.zip"), new Path("part2.zip"))
```

## API Test: `metadata`

### Signature
```scala
def metadata: RasterMetadata
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/GeoTiffReader.scala:165  (+2 more definition site/overload)_

### Goal
Retrieves the spatial metadata (dimensions, resolution, and coordinate reference system properties) of an opened raster file.

### Parameters
_None._

### Input
An initialized raster reader instance (such as `GeoTiffReader[T]`) that has successfully opened a valid raster file (e.g., GeoTIFF). The reader must be initialized via `reader.initialize(...)` before accessing its metadata.

### Output
Returns `RasterMetadata` — an object representing the raster's spatial properties. It provides access to dimensions (`rasterWidth`, `rasterHeight`), pixel scale (`getPixelScaleX`), and utility methods for coordinate transformations (`gridToModel`, `modelToGrid`) and tile lookups (`getTileIDAtPoint`, `getTileIDAtPixel`).

### Valid Call Patterns
```scala
import org.apache.hadoop.fs.Path
import org.apache.hadoop.conf.Configuration
import edu.ucr.cs.bdlab.raptor.GeoTiffReader
import edu.ucr.cs.bdlab.beast.common.BeastOptions
import java.awt.geom.Point2D

val rasterPath = new Path("path/to/raster.tif")
val fileSystem = rasterPath.getFileSystem(new Configuration())
val reader = new GeoTiffReader[Int] // Type must match runtime pixel type

try {
  // Reader must be initialized before accessing metadata
  reader.initialize(fileSystem, rasterPath.toString, "0", new BeastOptions())
  
  // Access basic metadata properties
  val width = reader.metadata.rasterWidth
  val height = reader.metadata.rasterHeight
  val scaleX = reader.metadata.getPixelScaleX
  
  // Transform origin point from raster grid (pixels) to vector model (coordinates)
  val outPoint = new Point2D.Double
  reader.metadata.gridToModel(0, 0, outPoint)
  
  // Transform from vector model (coordinates) to raster grid (pixels)
  reader.metadata.modelToGrid(-6.679688, 53.613281, outPoint)
  
  // Look up tile IDs for Raptor processing
  val tileID = reader.metadata.getTileIDAtPoint(23.224, 32.415)
  val tile = reader.readTile(tileID)
} finally {
  reader.close()
}
```

### LLM Instruction Prompt
- Call `metadata` without parentheses on an initialized raster reader (e.g., `GeoTiffReader[T]`).
- Use the returned `RasterMetadata` object to access `rasterWidth`, `rasterHeight`, or to perform spatial transformations like `gridToModel(x, y, outPoint)` and `modelToGrid(x, y, outPoint)`.
- Never access `metadata` before calling `initialize()` on the reader.

### Prompt Snippet
```text
To get raster dimensions or perform pixel-to-coordinate transformations, access the `metadata` property on an initialized `GeoTiffReader`. Do not use parentheses. You can use `metadata.gridToModel` and `metadata.modelToGrid` with a `java.awt.geom.Point2D.Double` to translate between pixel indices and spatial coordinates.
```

### Common Failure Modes
- **NullPointerException / Uninitialized State:** Accessing `reader.metadata` before calling `reader.initialize(...)`. The reader must parse the file headers first.
- **Method Signature Error:** Calling `reader.metadata()` with parentheses. It is defined as a parameterless method (`def metadata: RasterMetadata`) and should be accessed without parentheses in idiomatic Scala.
- **Type Mismatch on Initialization:** Creating a `GeoTiffReader[T]` where `T` does not match the underlying GeoTIFF's runtime pixel type (e.g., using `[Int]` for a Float32 raster), which may cause failures when subsequently reading tiles based on the metadata.

### Fix Code Hint
```scala
// WRONG: Accessing metadata before initialization or using parentheses
val reader = new GeoTiffReader[Float]
val meta = reader.metadata() // Fails: parentheses not allowed
val w = reader.metadata.rasterWidth // Fails: reader not initialized

// CORRECT: Initialize first, then access without parentheses
val reader = new GeoTiffReader[Float]
reader.initialize(fileSystem, path, "0", new BeastOptions())
val w = reader.metadata.rasterWidth
```

## API Test: `modelToGrid`

### Signature
```scala
def modelToGrid(x: Double, y: Double, outPoint: Point2D.Double): Unit
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:161_

_Source doc:_ Converts a point location from model (world) space to grid (pixel) space @param x the x-coordinate in the model space (e.g., longitude) @param y the y-coordinate in the model space (e.g., latitude) @param outPoint the output point that contains the grid coordinates

### Goal
Converts a geographic or projected coordinate (model/world space) into continuous pixel coordinates (grid space) based on the raster's affine transformation metadata.

### Parameters
- `x` (`Double`): The x-coordinate in the model space (e.g., longitude or projected X).
- `y` (`Double`): The y-coordinate in the model space (e.g., latitude or projected Y).
- `outPoint` (`Point2D.Double`): A pre-allocated `java.awt.geom.Point2D.Double` object that will be mutated in-place to store the resulting grid (pixel) coordinates.

### Input
Requires a valid `RasterMetadata` instance (typically accessed via `reader.metadata` from a `GeoTiffReader` or `HDF4Reader`) and a pre-allocated `Point2D.Double` object. The `x` and `y` coordinates must be in the exact Coordinate Reference System (CRS) and scale defined by the raster's model space.

### Output
Returns `Unit` — the function mutates the provided `outPoint` parameter. After the call, `outPoint.x` and `outPoint.y` will contain the continuous grid coordinates (column and row, respectively), which can be cast to integers to find the specific pixel index.

### Valid Call Patterns
```scala
import java.awt.geom.Point2D

// Assuming `reader` is an initialized GeoTiffReader or HDF4Reader
val outPoint = new Point2D.Double()

// Convert a known model coordinate (e.g., longitude, latitude) to grid space
reader.metadata.modelToGrid(-6.679688, 53.613281, outPoint)

// Extract the pixel column and row
val pixelX = outPoint.getX.toInt
val pixelY = outPoint.getY.toInt
```

### LLM Instruction Prompt
- When converting world coordinates to pixel coordinates using `modelToGrid`, you MUST pre-allocate a `java.awt.geom.Point2D.Double` and pass it as the third argument. 
- Do NOT assign the result of `modelToGrid` to a variable, as it returns `Unit`. Read the results directly from the mutated `Point2D.Double` object.
- The receiver is typically a `RasterMetadata` object (e.g., `reader.metadata.modelToGrid(...)`).

### Prompt Snippet
```text
To convert geographic coordinates to raster pixel coordinates in RDPro, pre-allocate a `java.awt.geom.Point2D.Double` and pass it to `metadata.modelToGrid(x, y, outPoint)`. The method returns `Unit` and mutates the point. Cast `outPoint.getX` and `outPoint.getY` to integers to get the pixel column and row.
```

### Common Failure Modes
- **Assigning the return value:** Attempting `val pt = metadata.modelToGrid(x, y, outPoint)` results in a `Unit` assignment, leading to compilation errors if `pt` is later used as a point.
- **Null Pointer Exception:** Passing `null` or an uninitialized variable for `outPoint` instead of explicitly calling `new Point2D.Double()`.
- **CRS Mismatch:** Passing raw latitude/longitude values when the raster's model space is actually in a projected coordinate system (e.g., Web Mercator), resulting in wildly out-of-bounds pixel coordinates.

### Fix Code Hint
```scala
// WRONG: Expecting a return value or missing the outPoint parameter
val gridPt = reader.metadata.modelToGrid(-110.0, 30.0)

// CORRECT: Pre-allocate the point and pass it to be mutated
val gridPt = new java.awt.geom.Point2D.Double()
reader.metadata.modelToGrid(-110.0, 30.0, gridPt)
val col = gridPt.getX.toInt
val row = gridPt.getY.toInt
```

## API Test: `normal`

### Signature
```scala
def normal(mu: Double, sigma: Double): Double
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/SpatialGenerator.scala:40_

_Source doc:_ Generate a random number in the range (-inf, +inf) from a normal distribution

### Goal
Generate a random floating-point number from a normal (Gaussian) distribution, typically used within Beast's Spider component for generating synthetic spatial data or benchmarking datasets.

### Parameters
- `mu` (`Double`): The mean (center) of the normal distribution.
- `sigma` (`Double`): The standard deviation (spread or width) of the normal distribution.

### Input
Two `Double` values representing the statistical parameters of the desired normal distribution. The `sigma` (standard deviation) value should be non-negative. 

### Output
Returns `Double` — a randomly generated number drawn from the specified normal distribution, falling within the range (-inf, +inf).

### Valid Call Patterns
```scala
// Note: Call pattern inferred from signature (not verified by tests/README).
// The exact enclosing object (e.g., SpatialGenerator) is not specified in the source facts.
val randomValue = normal(0.0, 1.0) // Standard normal distribution
```

### LLM Instruction Prompt
- Use `normal(mu, sigma)` when generating synthetic spatial coordinates or random attributes that require a Gaussian distribution. Ensure `sigma` is non-negative. Because the exact enclosing object is unknown from the provided facts, assume it is available in the `SpatialGenerator` scope or requires an appropriate import.

### Prompt Snippet
```text
To generate a random number from a normal distribution for synthetic spatial data, use `normal(mu, sigma)` where `mu` is the mean and `sigma` is the standard deviation.
```

### Common Failure Modes
- **Scope/Resolution Errors:** Calling `normal` without the correct object qualifier or import (e.g., `SpatialGenerator.normal(...)`), resulting in a "not found" compilation error.
- **Invalid Statistical Parameters:** Providing a negative value for `sigma`, which is mathematically invalid for a standard deviation and may cause unexpected behavior or exceptions in the underlying random number generator.

### Fix Code Hint
```scala
// Ensure sigma is non-negative and the function is properly scoped/imported
val mean = 10.0
val stdDev = 2.5
require(stdDev >= 0, "Standard deviation must be non-negative")
val value = normal(mean, stdDev)
```

## API Test: `numFeatures`

### Signature
```scala
def numFeatures: Long
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/SpatialPartition.scala:32_

_Source doc:_ Total number of features (records) in this partition

### Goal
Retrieves the total number of spatial features (records) contained within a specific spatial partition or geometric summary object.

### Parameters
_None._

### Input
A valid `SpatialPartition` (representing a distributed subset of spatial data) or a `Summary` object (representing aggregated dataset statistics, such as those generated by `GeometricSummary.run`). 

### Output
Returns `Long` — the exact count of features (records) present in the partition or summary.

### Valid Call Patterns
```scala
// From the project's test suite: retrieving the feature count from a Summary object
val inputfile = locateResource("/test.partitions")
val opts = new BeastOptions().set("iformat", "wkt(Geometry)")
  .set("skipheader", true)
  .set("separator", "\t")

val summary = GeometricSummary.run(opts, Array(inputfile.getPath), null, sparkContext).asInstanceOf[Summary]
val count: Long = summary.numFeatures
```

### LLM Instruction Prompt
- Call `numFeatures` as a parameterless method (without parentheses) on a `SpatialPartition` or `Summary` object.
- Do not call `numFeatures` directly on a Spark `RDD` (use `.count()` for RDDs); `numFeatures` is specific to Beast's partition and summary metadata objects.

### Prompt Snippet
```text
To get the record count of a Beast spatial partition or summary object, use `value.numFeatures`. It returns a Long. Do not use parentheses.
```

### Common Failure Modes
- **Adding parentheses:** Calling `summary.numFeatures()` will cause a Scala compilation error because the method is defined without parentheses.
- **Calling on an RDD:** Attempting to call `rdd.numFeatures` on a `SpatialRDD` or `RasterRDD`. This method belongs to the underlying `SpatialPartition` or a computed `Summary` object, not the distributed collection itself.

### Fix Code Hint
```scala
// WRONG: val count = summary.numFeatures()
// WRONG: val count = spatialRDD.numFeatures

// RIGHT: val count = summary.numFeatures
// RIGHT: val count = partition.numFeatures
```

## API Test: `numFields`

### Signature
```scala
def numFields: Int
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/shapefilev2/DBFWriter.scala:42_

_Source doc:_ Number of attributes in the file

### Goal
Returns the total number of attributes (fields) present in a spatial feature or record.

### Parameters
_None._

### Input
A spatial feature or record object (e.g., an element yielded by a vector file reader such as `GPXReader2`, or an `IFeature` from a vector RDD).

### Output
Returns `Int` — The count of attributes/fields defined in the record's schema.

### Valid Call Patterns
```scala
// Example derived from the project's test suite (GPXReader2Test)
val input = getClass.getResourceAsStream("/001005279.gpx")
val gpxReader = new GPXReader2(input, "001005279.gpx")

for (r <- gpxReader) {
  // Get the number of attributes in the current record
  val fieldCount: Int = r.numFields
  println(s"Record has $fieldCount fields.")
}
```

### LLM Instruction Prompt
- Use `numFields` when you need to determine the number of attributes in a spatial record or feature (e.g., to validate schema size or iterate over available fields).
- Call it directly on the record instance without parentheses, as it is defined as a parameterless method (`def numFields: Int`).

### Prompt Snippet
```text
To get the number of attributes in a spatial feature or record `r`, use `r.numFields`. Do not use parentheses.
```

### Common Failure Modes
- **Adding parentheses:** Calling `r.numFields()` will cause a compilation error because the method is defined without parentheses in Scala.
- **Misinterpreting the count:** Assuming `numFields` returns the number of geometries or points in a trajectory. It returns the number of *tabular attributes/fields* (e.g., elevation, time, trackname) in the record.

### Fix Code Hint
```scala
// WRONG: Compilation error due to parentheses
val count = r.numFields()

// RIGHT: Parameterless method call
val count = r.numFields
```

## API Test: `numNonEmptyGeometries`

### Signature
```scala
def numNonEmptyGeometries: Long
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/SpatialPartition.scala:35_

_Source doc:_ Number of non-empty geometries in this partition

### Goal
Calculates the total number of valid, non-empty vector geometries present within a specific spatial partition.

### Parameters
_None._

### Input
An instance of `SpatialPartition` containing spatial features (e.g., points, lines, or polygons loaded from formats like Shapefile, GeoJSON, or WKT). 

### Output
Returns `Long` — the exact count of geometries in the partition that contain valid coordinate data (excluding empty geometries like `POLYGON EMPTY`).

### Valid Call Patterns
```scala
// Inferred from signature and sibling methods on SpatialPartition
val validGeometryCount: Long = partition.numNonEmptyGeometries
```

### LLM Instruction Prompt
- Call `numNonEmptyGeometries` directly on a `SpatialPartition` instance to count valid features.
- Do not append parentheses `()` as it is a parameterless method in Scala.
- Do not call this directly on an `RDD[IFeature]`; it is a partition-level property, not a distributed RDD action (like `count()`).

### Prompt Snippet
```text
When analyzing the contents of a `SpatialPartition` in Beast, use `partition.numNonEmptyGeometries` to retrieve the count of valid (non-empty) geometries within that specific partition.
```

### Common Failure Modes
- **Method Not Found on RDD:** Attempting to call `rdd.numNonEmptyGeometries` directly on a `SpatialRDD` or `RDD[IFeature]`. This method belongs to the underlying `SpatialPartition` objects, not the distributed collection.
- **Syntax Error (Parentheses):** Adding parentheses `numNonEmptyGeometries()` to the parameterless method call, which may cause compilation errors in Scala.

### Fix Code Hint
```scala
// WRONG: Calling on an RDD
// val count = spatialRDD.numNonEmptyGeometries

// WRONG: Using parentheses
// val count = partition.numNonEmptyGeometries()

// CORRECT: Calling on a SpatialPartition instance without parentheses
val count = partition.numNonEmptyGeometries
```

## API Test: `numPartitions`

### Signature
```scala
def numPartitions(num: Int): JavaSpatialGeneratorBuilder
def numPartitions(num: Int): SpatialGeneratorBuilder
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:66  (+1 more definition site/overload)_

_Source doc:_ Set the number of partitions in the output. If not set or set to zero, one partition will be generated for each one million records @param num the number of partitions in the generated RDD @return

### Goal
Configures the number of partitions for the output RDD when generating synthetic spatial data using Beast's distributed Spatial Data Generator (Spider).

### Parameters
- `num` (`Int`): The desired number of partitions in the generated RDD. If set to `0`, the system defaults to generating one partition for every one million records.

### Input
A `SpatialGeneratorBuilder` or `JavaSpatialGeneratorBuilder` instance, typically initiated via the SparkContext extension `sc.generateSpatialData`.

### Output
Returns `SpatialGeneratorBuilder` (or `JavaSpatialGeneratorBuilder`) to allow method chaining when configuring the spatial data generator.

### Valid Call Patterns
```scala
// Inferred from signature and context (not verified)
val generatorBuilder = sc.generateSpatialData
  .numPartitions(100)
```

### LLM Instruction Prompt
- When generating synthetic spatial data using Beast's Spider generator, use `.numPartitions(num)` on the builder to explicitly set the cluster parallelism. 
- If the user does not specify a partition count, omit this call or pass `0` to rely on the default heuristic (1 partition per 1,000,000 records). 
- Do not confuse this builder method `numPartitions(Int)` with the parameterless `numPartitions` property found on instantiated partitioners (like `GridPartitioner` or `RSGrovePartitioner`).

### Prompt Snippet
```text
// Set partitions for generated spatial data (0 = 1 partition per 1M records)
sc.generateSpatialData.numPartitions(100)
```

### Common Failure Modes
- **Confusing Builder Method with Partitioner Property:** Attempting to call `numPartitions(Int)` on an instantiated `SpatialPartitioner` or `SpatialFileRDD`. The test suite shows that partitioners have a parameterless getter (`partitioner.numPartitions`), whereas this API is a builder method for data generation.
- **Over-partitioning Small Datasets:** Providing a very large `num` for a small number of generated records, leading to empty partitions and task overhead. If unsure, pass `0` to use the 1-million-record heuristic.

### Fix Code Hint
```scala
// WRONG: Attempting to set partitions on an existing partitioner or RDD using this method
// val p = IndexHelper.createPartitioner(...).numPartitions(10) 

// RIGHT: Chaining on the SpatialGeneratorBuilder
val builder = sc.generateSpatialData.numPartitions(10)
```

## API Test: `numPoints`

### Signature
```scala
def numPoints: Int
def numPoints: Long
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/LiteGeometry.scala:22  (+4 more definition site/overload)_

### Goal
Calculates the total number of coordinate points (vertices) for a given geometry or collection of geometries.

### Parameters
_None._

### Input
A lightweight geometry object (e.g., `LiteLineString`, `LiteList`, or other `LiteGeometry` types) typically generated during vector tile processing, visualization, or geometry simplification.

### Output
Returns `Int` or `Long` — The total count of coordinate points that make up the geometry.

### Valid Call Patterns
```scala
// Example derived from Beast's IntermediateVectorTileTest
val interTile = new IntermediateVectorTile(10, 0)
val line = GeometryReader.DefaultGeometryFactory.createLineString(Array(
  new Coordinate(5, 5), new Coordinate(-5, 5), new Coordinate(-5, 6), new Coordinate(-5, 7),
  new Coordinate(-5, 15), new Coordinate(5, 8)
))

val simplifiedLine = interTile.simplifyGeometry(line)

// Call numPoints on the resulting geometry
val pointCount = simplifiedLine.numPoints
```

### LLM Instruction Prompt
- Use `.numPoints` (without parentheses) on lightweight geometry objects (like `LiteLineString` or `LiteList`) to retrieve the total vertex count.
- Always verify that the geometry object is not `null` before calling `.numPoints`. Operations like `simplifyGeometry` will return `null` if a geometry is completely outside a tile or simplified away, which will cause a `NullPointerException` if `.numPoints` is invoked directly.

### Prompt Snippet
```text
Use `geometry.numPoints` to get the total number of vertices (as an Int or Long) for a Beast LiteGeometry object. Always check for null if the geometry is the result of a simplification step.
```

### Common Failure Modes
- **`NullPointerException`**: Calling `.numPoints` on a geometry reference that is `null`. This frequently happens when processing vector tiles if a geometry (like a `LinearRing` or `LineString`) is completely outside the tile bounds and does not contain the tile, causing `simplifyGeometry` to return `null`.

### Fix Code Hint
```scala
// Safely check for null before accessing numPoints
val simplifiedLine = interTile.simplifyGeometry(line)
val pointCount = if (simplifiedLine != null) simplifiedLine.numPoints else 0
```

## API Test: `numTiles`

### Signature
```scala
def numTiles: Int
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:61_

_Source doc:_ Total number of tiles in the raster layer

### Goal
Retrieves the total number of tiles that make up the raster layer from its metadata.

### Parameters
_None._

### Input
A valid `RasterMetadata` object, typically accessed via a raster reader's `.metadata` property (e.g., `HDF4Reader.metadata`) after the reader has been properly initialized with a file system, path, and options.

### Output
Returns `Int` — The total count of tiles present in the raster layer.

### Valid Call Patterns
```scala
val reader = new HDF4Reader
reader.initialize(fileSystem, hdfFile.toString, "water_mask", new BeastOptions())
val totalTiles: Int = reader.metadata.numTiles
```

### LLM Instruction Prompt
- Call `numTiles` as a parameterless property on a `RasterMetadata` instance (e.g., `reader.metadata.numTiles`).
- Do not append parentheses `()`.
- Ensure the underlying reader or metadata source is fully initialized before accessing this property.

### Prompt Snippet
```text
val totalTiles = reader.metadata.numTiles
```

### Common Failure Modes
- **Syntax Error (Parentheses):** Calling `numTiles()` with parentheses will cause a compilation error because it is defined without parentheses.
- **Uninitialized Metadata:** Attempting to access `reader.metadata.numTiles` before calling `reader.initialize(...)` will result in a null reference or invalid state error.

### Fix Code Hint
```scala
// WRONG: Using parentheses or calling before initialization
// val count = reader.metadata.numTiles()

// CORRECT: Parameterless call after initialization
reader.initialize(fileSystem, path, layerName, new BeastOptions())
val count = reader.metadata.numTiles
```

## API Test: `overlay`

### Signature
```scala
def overlay[V](rasters: RasterRDD[T]*)
def overlay[T: ClassTag, V](@varargs inputs: RDD[ITile[T]]*)
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:96  (+1 more definition site/overload)_

_Source doc:_ Overlays this raster RDD on top other ones @param rasters the other rasters to stack this raster on @return a new RasterRDD which contains the stack of this raster on top of the given ones

### Goal
Stacks multiple raster RDDs on top of each other to create a single multi-band raster RDD where each pixel contains an array of values from the aligned input rasters.

### Parameters
- `rasters` (`RasterRDD[T]*`): A variable number of additional raster RDDs to stack underneath or alongside the base raster.

### Input
Requires two or more `RasterRDD[T]` (or `RDD[ITile[T]]`) datasets of the same pixel type `T`. 
**Crucial Precondition:** The `overlay` operation requires all input rasters to have identical metadata (resolution, CRS, and tile size). If inputs have mixed metadata, you must convert and align them first using `RasterOperationsFocal.reshapeNN` (for categorical/downsizing) or `RasterOperationsFocal.reshapeAverage` (for continuous numerical data).

### Output
Returns `unspecified` — A new `RasterRDD[Array[T]]` (inferred from project examples) which contains the stacked bands. Each pixel in the resulting raster is an array containing the values from the input rasters at that spatial location.

### Valid Call Patterns
```scala
// Instance method form (from project README)
val raster1: RasterRDD[Int] = sc.geoTiff[Int]("glc2000_v1_1.tif")
val raster2: RasterRDD[Int] = sc.geoTiff[Int]("vegetation")
val stacked: RasterRDD[Array[Int]] = raster1.overlay(raster2)

// Object method form (from project test suite)
val raster3: RasterRDD[Array[Short]] = RasterOperationsLocal.overlay(raster1, raster2)
```

### LLM Instruction Prompt
- NEVER call `overlay` on rasters with differing or unknown metadata (resolution, CRS, tile size) without first aligning them using `reshape`.
- Ensure all rasters being overlaid share the exact same underlying pixel type `T` (e.g., both `Int` or both `Float`).
- Expect the output to be a `RasterRDD[Array[T]]`, representing the multi-band stack.

### Prompt Snippet
```text
When stacking rasters using `raster1.overlay(raster2)`, you MUST ensure both rasters have identical metadata (CRS, resolution, tile size). If they differ, align them first using `RasterOperationsFocal.reshapeNN` or `reshapeAverage`. The output will be a `RasterRDD[Array[T]]`.
```

### Common Failure Modes
- **Mismatched Metadata:** Calling `overlay` on rasters with different resolutions, CRSs, or tile sizes will fail or produce incorrect alignments. They must be reshaped first.
- **Type Mismatch:** Attempting to overlay rasters of different pixel types (e.g., mixing `RasterRDD[Int]` and `RasterRDD[Float]`). The type parameter `T` must match across all inputs.

### Fix Code Hint
```scala
// If rasters have different metadata, align them first using reshape
val reshapedRaster2 = RasterOperationsFocal.reshapeNN(raster2,
  RasterMetadata.create(-124, 42, -114, 32, 4326, 1000, 1000, 100, 100))

// Now they can be safely overlaid
val stacked: RasterRDD[Array[Int]] = raster1.overlay(reshapedRaster2)
```

## API Test: `parcel`

### Signature
```scala
def parcel(cardinality: Long, dither: Double = 0.2, splitRange: Double = 0.2): JavaSpatialRDD
def parcel(cardinality: Long, dither: Double = 0.2, splitRange: Double = 0.2): SpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:153  (+1 more definition site/overload)_

_Source doc:_ Generates boxes from the parcel distribution @param cardinality the number of records to generate @param dither the amount of randomization to add to each generated box @param splitRange the range of splitting each box @return the RDD that contains the generated data

### Goal
Generates a distributed `SpatialRDD` containing synthetic bounding boxes following a parcel-like spatial distribution, primarily used for benchmarking spatial operations like distributed joins.

### Parameters
- `cardinality` (`Long`): The total number of synthetic box records to generate across the Spark cluster.
- `dither` (`Double`), default `0.2`: The amount of randomization (noise) to add to the boundaries of each generated box.
- `splitRange` (`Double`), default `0.2`: The range or ratio used when recursively splitting space to create the parcel boxes.

### Input
Requires an initialized `SparkContext` (`sc`) with Beast context extensions imported (`import edu.ucr.cs.bdlab.beast._`). The function must be called on a spatial data generator builder, typically instantiated via `sc.generateSpatialData`. Optionally, the builder can be configured with a specific Minimum Bounding Rectangle (MBR) or seed prior to calling `parcel`.

### Output
Returns `SpatialRDD` (or `JavaSpatialRDD` in the Java API) — a distributed Spark dataset containing the generated synthetic parcel geometries (boxes) ready for spatial partitioning, joins, or visualization.

### Valid Call Patterns
```scala
// Generate a large dataset of parcels for benchmarking
val parcels: SpatialRDD = sc.generateSpatialData
  .parcel(1000000, dither = 0.1, splitRange = 0.4)

// Generate a smaller dataset and visualize it
sc.generateSpatialData
  .parcel(100, dither = 0.2, splitRange = 0.3)
  .plotImage(300, 300, "parcel.png")
```

### LLM Instruction Prompt
- When generating synthetic spatial data for benchmarking or testing, use `sc.generateSpatialData.parcel(cardinality)`.
- Do not call `parcel` as a standalone function; it must be chained onto the `SpatialGeneratorBuilder` provided by `sc.generateSpatialData`.
- You may omit `dither` and `splitRange` to rely on their default values (`0.2`), or provide them explicitly to tune the generated distribution.

### Prompt Snippet
```text
To generate synthetic bounding boxes following a parcel distribution for benchmarking spatial joins, use the Beast spatial data generator: `val parcels = sc.generateSpatialData.parcel(1000000)`. This returns a `SpatialRDD` of generated geometries.
```

### Common Failure Modes
- **Missing Context Extensions:** Calling `sc.generateSpatialData` will fail with a "value not a member of SparkContext" compilation error if Beast implicits are not imported.
- **Standalone Call:** Attempting to call `parcel(...)` directly without the `sc.generateSpatialData` builder receiver.

### Fix Code Hint
```scala
// Ensure Beast implicits are imported to attach .generateSpatialData to SparkContext
import edu.ucr.cs.bdlab.beast._

// Correctly chain the parcel call onto the generator builder
val generatedParcels: SpatialRDD = sc.generateSpatialData.parcel(cardinality = 500000L)
```

## API Test: `part`

### Signature
```scala
def part(i: Int): LiteList
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/LiteGeometry.scala:146_

### Goal
Retrieves a specific component or sub-geometry (part) from a lightweight geometry (`LiteGeometry`) by its index, typically used during vector tile (MVT) generation and visualization.

### Parameters
- `i` (`Int`): The zero-based index of the part to retrieve from the geometry.

### Input
- A valid `LiteGeometry` instance (such as a `LiteLineString` generated by `IntermediateVectorTile.simplifyGeometry`).
- **Preconditions:** The geometry must not be null (simplification can return `null` for collapsed geometries), and the index `i` must be within the valid bounds of the geometry's parts.

### Output
Returns `LiteList` — A lightweight list structure representing the coordinates or sub-elements of the requested geometry part.

### Valid Call Patterns
```scala
// Inferred from signature and sibling methods on LiteGeometry
val interTile = new IntermediateVectorTile(10, 0)
val line = GeometryReader.DefaultGeometryFactory.createLineString(Array(
  new Coordinate(5, 5), new Coordinate(-5, 5), new Coordinate(-5, 6), new Coordinate(-5, 7),
  new Coordinate(-5, 15), new Coordinate(5, 8)
))
val simplifiedLine = interTile.simplifyGeometry(line)

if (simplifiedLine != null) {
  // Retrieve the first part of the lightweight geometry
  val firstPart: LiteList = simplifiedLine.part(0)
}
```

### LLM Instruction Prompt
- Use `liteGeometry.part(i)` to extract a specific sub-geometry or coordinate sequence as a `LiteList` from a `LiteGeometry` instance.
- Always check that the `LiteGeometry` instance is not `null` before calling `part`, as operations like `simplifyGeometry` may return `null` if the geometry collapses entirely.
- Do not invent a standalone `part(...)` function; it must be called as an instance method on a `LiteGeometry` object.

### Prompt Snippet
```text
`LiteGeometry.part(i: Int): LiteList` retrieves a specific sub-geometry part by its zero-based index. Used in visualization/MVT workflows. Ensure the geometry is not null before calling.
```

### Common Failure Modes
- **NullPointerException:** Calling `part(i)` on a `null` reference. In Beast's visualization API, methods like `simplifyGeometry` return `null` if the geometry is simplified out of existence (e.g., too small for the current zoom level).
- **IndexOutOfBoundsException:** Passing an index `i` that is less than 0 or greater than or equal to the number of parts in the `LiteGeometry`.

### Fix Code Hint
```scala
val simplifiedGeom = interTile.simplifyGeometry(originalGeom)
// FIX: Always check for null before attempting to access parts of a LiteGeometry
if (simplifiedGeom != null) {
  val mainPart = simplifiedGeom.part(0)
  // process mainPart...
}
```

## API Test: `partitionBy`

### Signature
```scala
def partitionBy(spatialPartitioner: SpatialPartitioner): PartitionedSpatialRDD
def partitionBy(partitionerKlass: Class[_ <: SpatialPartitioner], numPartitions: Int = rdd.getNumPartitions, opts: BeastOptions = new BeastOptions()): PartitionedSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/indexing/IndexMixin.scala:35  (+1 more definition site/overload)_

### Goal
Distributes spatial vector data across a Spark cluster using a specialized spatial partitioner to optimize load balancing, spatial joins, and query pruning.

### Parameters
- `spatialPartitioner` (`SpatialPartitioner`): An instantiated spatial partitioner (e.g., `new GridPartitioner(...)`) that defines the spatial boundaries for distributing the data.
- *(Overload)* `partitionerKlass` (`Class[_ <: SpatialPartitioner]`): The class type of the partitioner to automatically instantiate and apply (e.g., `classOf[RSGrovePartitioner]`).
- *(Overload)* `numPartitions` (`Int`): The target number of partitions (defaults to the RDD's current partition count).
- *(Overload)* `opts` (`BeastOptions`): Additional configuration options for the partitioning process.

### Input
A `SpatialRDD` (typically containing `IFeature` objects) loaded from vector formats such as Esri Shapefile, GeoJSON, or CSV. 

### Output
Returns `PartitionedSpatialRDD` — an RDD where features are physically grouped by spatial proximity. This sets the RDD's partitioner property, enabling optimized distributed spatial joins, range queries, and spatial indexing.

### Valid Call Patterns
```scala
// Pattern 1: Partitioning by providing a partitioner class (from project README)
val partitionedStates = sparkContext.shapefile("ne_10m_admin_1_states_provinces.zip")
  .partitionBy(classOf[RSGrovePartitioner])

// Pattern 2: Partitioning by providing an instantiated partitioner (adapted from sibling test)
val mbr = data.summary
val gridPartitioner = new GridPartitioner(mbr, Array(2, 2))
val partitionedData = data.partitionBy(gridPartitioner)
```

### LLM Instruction Prompt
- Call `partitionBy` (or its sibling `spatialPartition`) on a `SpatialRDD` before performing distributed spatial joins that require partitioned data.
- The Distributed Join (`DJ`) algorithm requires *both* datasets to be spatially partitioned first. The Repartition Join (`REPJ`) requires at least *one* dataset to be spatially partitioned.
- To avoid duplicate results in custom algorithms, partitions must be disjoint. Only use `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner` if disjoint partitioning is required.

### Prompt Snippet
```text
When preparing vector RDDs for spatial joins in Beast, use `rdd.partitionBy(classOf[RSGrovePartitioner])`. If using the `DJ` (Distributed Join) algorithm, you MUST partition both input RDDs first. If using `REPJ`, partition at least one. For custom algorithms requiring disjoint partitions to avoid duplicates, restrict your choice to `RSGrovePartitioner`, `GridPartitioner`, `KDTreePartitioner`, or `STRPartitioner`.
```

### Common Failure Modes
- **Missing Precondition for DJ Join:** Attempting to run `rdd1.spatialJoin(rdd2, ESJPredicate.Intersects, ESJDistributedAlgorithm.DJ)` without calling `partitionBy` on both `rdd1` and `rdd2` first, leading to execution failures.
- **Duplicate Results in Custom Algorithms:** Using a partitioner that does not support disjoint partitioning, resulting in overlapping boundaries and duplicate feature processing.
- **Calling on Raster Data:** Attempting to call `partitionBy` on a `RasterRDD` instead of a vector `SpatialRDD`. Raster retiling/partitioning is handled via `raster.retile` or `raster.explode`, not `partitionBy`.

### Fix Code Hint
```scala
// BAD: Attempting a DJ join without partitioning
// val sjResults = polygons.spatialJoin(points, ESJPredicate.Contains, ESJDistributedAlgorithm.DJ)

// GOOD: Partition both datasets before a DJ join
val partitionedPolygons = polygons.partitionBy(classOf[RSGrovePartitioner])
val partitionedPoints = points.partitionBy(classOf[RSGrovePartitioner])
val sjResults = partitionedPolygons.spatialJoin(partitionedPoints, ESJPredicate.Contains, ESJDistributedAlgorithm.DJ)
```

## API Test: `partitionFeatures`

### Signature
```scala
def partitionFeatures(features: SpatialRDD, spatialPartitioner: SpatialPartitioner): PartitionedSpatialRDD
def partitionFeatures(features: JavaSpatialRDD, partitioner: SpatialPartitioner): JavaPairRDD[Integer, IFeature]
def partitionFeatures(features: SpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], sizeFunction: IFeature=>Int, opts: BeastOptions): PartitionedSpatialRDD
def partitionFeatures(features: JavaSpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], sizeFunction: org.apache.spark.api.java.function.Function[IFeature, Int], opts: BeastOptions) : JavaPartitionedSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/indexing/IndexHelper.scala:413  (+3 more definition site/overload)_

### Goal
Distributes a spatial RDD across a Spark cluster using a specified spatial partitioner (such as R*-Grove or GridPartitioner) to optimize load balancing, enable query pruning, and satisfy preconditions for distributed spatial joins.

### Parameters
- `features` (`SpatialRDD`): The input RDD of vector geometries (features) to be spatially partitioned.
- `spatialPartitioner` / `partitionerClass` (`SpatialPartitioner` or `Class[_ <: SpatialPartitioner]`): Either an already initialized spatial partitioner instance (e.g., `new GridPartitioner(...)`) or the class type of the partitioner to use (e.g., `classOf[RSGrovePartitioner]`).
- `sizeFunction` (`IFeature=>Int`): A function to estimate the size or weight of a feature, used for load balancing when passing a partitioner class.
- `opts` (`BeastOptions`): Configuration options for the partitioning process when using the class-based overload.

### Input
A `SpatialRDD` of vector features, typically loaded via context extensions like `sc.shapefile` or `sc.geojsonFile`. 
*   **Preconditions:** If initializing a partitioner manually (like `GridPartitioner`), you must precompute the spatial summary of the features (e.g., using `Summary.computeForFeatures(features)`). 
*   **Algorithm Requirements:** Spatial partitioning is a strict precondition for certain spatial join algorithms: the Distributed Join (`DJ`) requires *both* datasets to be spatially partitioned, while the Repartition Join (`REPJ`) requires at least *one*.

### Output
Returns `PartitionedSpatialRDD` (or `JavaPartitionedSpatialRDD` / `JavaPairRDD[Integer, IFeature]` for Java APIs) — an RDD of `(partition number, IFeature)` where features are grouped into partitions based on spatial proximity.

### Valid Call Patterns
```scala
// Pattern 1: Using an initialized partitioner (requires precomputed summary)
val summary = Summary.computeForFeatures(features)
val partitionedFeatures = IndexHelper.partitionFeatures(
  features, 
  new GridPartitioner(summary, 1)
)

// Pattern 2: Using a partitioner class and size function
val partitionedFeatures2 = IndexHelper.partitionFeatures(
  features, 
  classOf[RSGrovePartitioner], 
  (f: IFeature) => 1, 
  new BeastOptions()
)
```

### LLM Instruction Prompt
- **Deprecation Warning:** The `partitionFeatures` method is officially marked as `@deprecated` in the source documentation. Instruct users to prefer `partitionFeatures2` if available, or use the RDD extension `rdd.spatialPartition(classOf[...])` for idiomatic Scala. If `partitionFeatures` must be used, it is called statically via `IndexHelper.partitionFeatures(...)`.
- **Disjoint Partitions:** If the user is implementing custom algorithms and needs to avoid duplicate results, they must use a partitioner that supports disjoint partitioning. Explicitly select `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner`.
- **Join Preparation:** Always partition datasets before attempting a `DJ` (Distributed Join) to avoid runtime failures.

### Prompt Snippet
```text
To spatially partition vector data in Beast, use `IndexHelper.partitionFeatures`. Note that this specific method is deprecated in favor of `partitionFeatures2` or the `rdd.spatialPartition` extension method. If you must use it, ensure you choose a disjoint partitioner like `RSGrovePartitioner` if duplicate avoidance is required. For initialized partitioners like `GridPartitioner`, you must compute the dataset summary first.
```

### Common Failure Modes
- **Missing Summary for Initialization:** Attempting to instantiate a `GridPartitioner` without first computing the bounding box/summary of the `features` RDD, leading to incorrect or failed partitioning.
- **Duplicate Results in Custom Queries:** Using a non-disjoint partitioner for custom spatial algorithms, resulting in features spanning multiple partitions being processed multiple times.
- **Method Not Found:** Attempting to call `features.partitionFeatures(...)` directly on the RDD object instead of using the `IndexHelper` object.

### Fix Code Hint
```scala
// BAD: Calling directly on the RDD or missing the summary for GridPartitioner
val badPartition = features.partitionFeatures(new GridPartitioner(null, 1))

// GOOD: Using IndexHelper and computing the summary first
val summary = Summary.computeForFeatures(features)
val goodPartition = IndexHelper.partitionFeatures(features, new GridPartitioner(summary, 1))

// GOOD: Using the class-based overload with RSGrovePartitioner for disjoint partitions
val grovePartition = IndexHelper.partitionFeatures(
  features, 
  classOf[RSGrovePartitioner], 
  (f: IFeature) => 1, 
  new BeastOptions()
)
```

## API Test: `partitionFeatures2`

### Signature
```scala
def partitionFeatures2(features: SpatialRDD, spatialPartitioner: SpatialPartitioner): SpatialRDD
def partitionFeatures2(features: JavaSpatialRDD, partitioner: SpatialPartitioner): JavaSpatialRDD
def partitionFeatures2(features: SpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], sizeFunction: IFeature=>Int, opts: BeastOptions): SpatialRDD
def partitionFeatures2(features: JavaSpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], sizeFunction: org.apache.spark.api.java.function.Function[IFeature, Int], opts: BeastOptions) : JavaSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/indexing/IndexHelper.scala:429  (+3 more definition site/overload)_

_Source doc:_ Partitions the given features using a partitioner of the given type. This method first initializes the partitioner and then uses this initialized partitioner to partition the data. @param features the set of features to spatially partition @param partitionerClass the type of the spatial partition @param sizeFunction the function used to computed the size @param opts additional options @return the same set of input features after they are partitioned.

### Goal
Distributes a set of spatial features across a Spark cluster using a specified spatial partitioner (such as a Grid or R*-Grove) to optimize load balancing and enable distributed spatial joins.

### Parameters
- `features` (`SpatialRDD`): The input RDD of vector geometries (`IFeature`) to be spatially partitioned.
- `partitionerClass` (`Class[_ <: SpatialPartitioner],
                        sizeFunction: IFeature=>Int`): The class type of the spatial partitioner to initialize (e.g., `classOf[RSGrovePartitioner]`). In the pre-initialized overloads, this is replaced by the instantiated `SpatialPartitioner` itself (e.g., `new GridPartitioner(...)`).
- `opts` (`BeastOptions`): Additional configuration options used when initializing the partitioner from a class.

### Input
A `SpatialRDD` (or `JavaSpatialRDD`) of vector features, typically loaded from formats like Shapefile, GeoJSON, or CSV. If the partitioned data will be used in custom algorithms that require disjoint partitions to avoid duplicate results, the chosen partitioner must support disjoint partitioning (e.g., `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner`).

### Output
Returns `SpatialRDD` — The exact same set of input features, but physically reorganized across Spark partitions according to their spatial locations. The returned RDD will have its Spark `partitioner` property defined as the specified `SpatialPartitioner`.

### Valid Call Patterns
```scala
// Using an explicitly initialized partitioner via IndexHelper
val unitsquare = new EnvelopeNDLite(2, 0.0, 0.0, 1.0, 1.0)
val partitionedFeatures = IndexHelper.partitionFeatures2(
  features, 
  new GridPartitioner(unitsquare, Array(3, 3))
)

// Partitioning for a distributed spatial join
val partitioned1 = IndexHelper.partitionFeatures2(dataset1, new GridPartitioner(unitsquare, Array(5, 5)))
val partitioned2 = IndexHelper.partitionFeatures2(dataset2, new GridPartitioner(unitsquare, Array(5, 5)))
```

### LLM Instruction Prompt
- Call `partitionFeatures2` using the `IndexHelper` object (i.e., `IndexHelper.partitionFeatures2(...)`), as it is a helper method rather than an RDD extension method.
- When preparing datasets for a Distributed Join (`DJ`), you MUST spatially partition *both* datasets first. For a Repartition Join (`REPJ`), you MUST partition at least *one* dataset.
- To avoid duplicate results in custom algorithms, ensure you select a partitioner that supports disjoint partitioning (e.g., `GridPartitioner` or `RSGrovePartitioner`).

### Prompt Snippet
```text
To spatially partition an RDD of features for optimized querying or joining, use `IndexHelper.partitionFeatures2(features, partitioner)`. If preparing for a Distributed Join (DJ), both datasets must be partitioned. Use disjoint partitioners like `GridPartitioner` or `RSGrovePartitioner` to prevent duplicate results in custom algorithms.
```

### Common Failure Modes
- **Duplicate Results in Custom Algorithms:** Using a non-disjoint partitioner when disjoint partitions are required. Fix: Switch to `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner`.
- **Spatial Join Failures (Missing Preconditions):** Attempting to run a Distributed Join (`ESJDistributedAlgorithm.PBSM` or `DJ`) without partitioning both datasets first, or a Repartition Join (`REPJ`) without partitioning at least one.
- **Compilation Error (Method Not Found):** Attempting to call `features.partitionFeatures2(...)` directly on the RDD. While Beast provides `rdd.spatialPartition` as an extension, `partitionFeatures2` specifically belongs to `IndexHelper`.

### Fix Code Hint
```scala
// WRONG: Calling directly on the RDD
val partitioned = features.partitionFeatures2(new GridPartitioner(env, Array(2, 2)))

// RIGHT: Using IndexHelper
val partitioned = IndexHelper.partitionFeatures2(features, new GridPartitioner(env, Array(2, 2)))
```

## API Test: `pixelLocations`

### Signature
```scala
def pixelLocations: Iterator[(Int, Int)]
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:81_

_Source doc:_ An iterator that goes over all pixels in this tile @return an iterator that goes over all pixels (whether empty or not) in this tile

### Goal
Returns an iterator over the local `(x, y)` column and row indices of all pixels within a specific raster tile, regardless of whether the pixels contain valid data or are empty.

### Parameters
_None._

### Input
An `ITile[T]` instance, typically obtained by iterating over a `RasterRDD[T]` (e.g., loaded via `sc.geoTiff[T]`) or by reading individual tiles using a `GeoTiffReader`.

### Output
Returns `Iterator[(Int, Int)]` — an iterator yielding tuples of `(x, y)` integers representing the local column (`x`) and row (`y`) coordinates for every pixel in the tile.

### Valid Call Patterns
```scala
// Example 1: Iterating over all pixels in a tile and checking if they are defined
for ((x, y) <- tile.pixelLocations) {
  if (tile.isDefined(x, y)) {
    // Process valid pixel
  }
}

// Example 2: Using a guard in a for-comprehension to count non-empty pixels
var numNonEmptyPixels = 0
for ((x, y) <- tile.pixelLocations; if tile.isDefined(x, y)) {
  numNonEmptyPixels += 1
}
```

### LLM Instruction Prompt
- Use `tile.pixelLocations` when you need to manually iterate over the pixel coordinates of an `ITile[T]`.
- Because `pixelLocations` yields *all* pixels in the tile's grid (including empty/NoData pixels), you MUST check `tile.isDefined(x, y)` before attempting to read or process the pixel value to avoid processing invalid data.
- Remember that the yielded `(x, y)` values are local pixel indices within the tile, not global spatial coordinates (like longitude/latitude).

### Prompt Snippet
```text
`tile.pixelLocations` returns an `Iterator[(Int, Int)]` of all local (x, y) pixel coordinates in an `ITile`. It includes empty pixels, so always guard pixel access with `if (tile.isDefined(x, y))`.
```

### Common Failure Modes
- **Processing NoData/Empty Pixels:** Failing to check `tile.isDefined(x, y)` inside the loop, leading to incorrect calculations (e.g., treating a NoData fill value as a valid temperature or elevation).
- **Confusing Local Indices with Spatial Coordinates:** Assuming the `(x, y)` returned by `pixelLocations` are projected CRS coordinates (e.g., meters or degrees) rather than integer pixel offsets within the tile.

### Fix Code Hint
```scala
// WRONG: Blindly processing all pixels
for ((x, y) <- tile.pixelLocations) {
  val value = tile.getPixelValue(x, y) // May process NoData/fill values
}

// RIGHT: Guarding with isDefined
for ((x, y) <- tile.pixelLocations; if tile.isDefined(x, y)) {
  val value = tile.getPixelValue(x, y)
}
```

## API Test: `pixelType`

### Signature
```scala
def pixelType: DataType
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:138_

_Source doc:_ Returns the type of the pixel as an SQL data type @return the type of the pixel values

### Goal
Returns the Spark SQL `DataType` (e.g., `FloatType`, `IntegerType`) representing the underlying runtime type of the pixel values within a raster tile.

### Parameters
_None._

### Input
An instance of `ITile` (typically obtained by extracting a tile from a `RasterRDD` or `RasterFileRDD`). 

### Output
Returns `DataType` — A Spark SQL `DataType` object (such as `org.apache.spark.sql.types.FloatType` or `org.apache.spark.sql.types.IntegerType`) that describes the runtime type of the pixels in the tile.

### Valid Call Patterns
```scala
// Inspecting the pixel type of a loaded raster tile
val readRaster = new RasterFileRDD(sparkContext, outputFile.getPath, new BeastOptions())
val tileType: DataType = readRaster.first().pixelType

// Example assertion from the test suite
assertResult(FloatType)(tileType)
```

### LLM Instruction Prompt
- Use `pixelType` on an `ITile` instance (not the `RasterRDD` itself) to inspect the runtime pixel type of a raster.
- This is particularly useful for determining the correct type parameter `T` when subsequently loading typed rasters via `sc.geoTiff[T]` (e.g., if `pixelType` is `IntegerType`, you must use `sc.geoTiff[Int]`; if `FloatType`, use `sc.geoTiff[Float]`).
- Remember that the return value is a Spark SQL `DataType`, not a standard Scala type or a string.

### Prompt Snippet
```text
To check the runtime pixel type of a raster tile in RDPro, call `tile.pixelType`. It returns a Spark SQL `DataType` (e.g., `FloatType`, `IntegerType`). You must call this on an `ITile` instance (e.g., `rasterRDD.first().pixelType`), not directly on the RDD.
```

### Common Failure Modes
- **Calling on the RDD instead of a Tile:** Attempting to call `rasterRDD.pixelType` will fail at compile time. You must extract an `ITile` first (e.g., using `.first()`).
- **Type Mismatch in Typed Loads:** Ignoring the `pixelType` and loading a GeoTIFF with the wrong type parameter (e.g., using `sc.geoTiff[Int]` when `pixelType` is `FloatType`) will cause runtime casting errors.
- **Comparing to Strings:** Attempting to compare the result to a string like `"Float"` instead of the Spark SQL `FloatType` object.

### Fix Code Hint
```scala
// WRONG: Calling pixelType on the RDD
// val pType = rasterRDD.pixelType 

// RIGHT: Extracting a tile first to check its pixel type
val pType = rasterRDD.first().pixelType
if (pType == org.apache.spark.sql.types.FloatType) {
  // Proceed with Float-specific logic
}
```

## API Test: `pixels`

### Signature
```scala
def pixels: Iterator[(Int, Int, T)]
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/ITile.scala:84_

### Goal
Extract an iterator of all pixel values along with their local tile coordinates (column, row) from an `ITile`.

### Parameters
_None._

### Input
An instance of `ITile[T]`, typically obtained by loading a raster dataset (e.g., via `sc.geoTiff[T]`). The type parameter `T` must exactly match the file's runtime pixel type (e.g., `Int` for `IntegerType`, `Float` for `FloatType`, `Array[Int]` for `ArrayType(IntegerType, true)`).

### Output
Returns `Iterator[(Int, Int, T)]` — An iterator yielding a tuple for each pixel in the tile. The tuple contains the local column index (`Int`), the local row index (`Int`), and the pixel value (`T`).

### Valid Call Patterns
```scala
// Inferred from sibling tests and context: mapping over an RDD of ITile
val treecover: RDD[ITile[Float]] = sc.geoTiff[Float]("treecover")

val activePixels = treecover.flatMap { tile =>
  // Extract the iterator of (col, row, value) from the tile
  val pixelIter: Iterator[(Int, Int, Float)] = tile.pixels
  
  // Filter or process the local pixels
  pixelIter.filter { case (col, row, value) => 
    value >= 0.0f && value <= 100.0f 
  }
}
```

### LLM Instruction Prompt
- Use `tile.pixels` to unpack an `ITile[T]` into an iterator of individual pixel values and their local coordinates.
- Ensure the generic type `T` of the `ITile` (and the `sc.geoTiff[T]` used to load it) exactly matches the underlying raster data type to prevent runtime casting errors during iteration.
- Remember that the `(Int, Int)` coordinates returned are local column and row indices within the specific tile, not global spatial coordinates or global pixel coordinates.

### Prompt Snippet
```text
To process individual pixels within an `ITile[T]`, call `tile.pixels`. This returns an `Iterator[(Int, Int, T)]` representing the local column, local row, and the pixel value. Ensure your raster load operation (e.g., `sc.geoTiff[Int]`) uses the correct type parameter for the dataset.
```

### Common Failure Modes
- **Type Mismatch (`ClassCastException`):** Calling `pixels` on an `ITile[T]` where `T` was incorrectly specified during loading (e.g., using `sc.geoTiff[Float]` for an integer GeoTIFF). The type parameter must exactly match the runtime pixel type.
- **Coordinate Confusion:** Treating the returned `(Int, Int)` values as global spatial coordinates (e.g., longitude/latitude) or global raster indices. They are strictly local to the current `ITile`.

### Fix Code Hint
```scala
// BAD: Incorrect type parameter for an integer raster, and assuming global coordinates
val raster = sc.geoTiff[Float]("glc2000_v1_1.tif") 
val badPixels = raster.flatMap(tile => tile.pixels.filter(_._3 > 0))

// GOOD: Match the runtime pixel type (Int) and handle as local tile coordinates
val raster: RDD[ITile[Int]] = sc.geoTiff[Int]("glc2000_v1_1.tif")
val validPixels = raster.flatMap { tile =>
  tile.pixels.filter { case (localCol, localRow, value) => value > 0 }
}
```

## API Test: `plotAllTiles`

### Signature
```scala
def plotAllTiles(features: SpatialDataTypes.JavaSpatialRDD, minLevel: Int, maxLevel: Int, resolution: Int, buffer: Int, opts: BeastOptions): JavaPairRDD[java.lang.Long, IntermediateVectorTile]
def plotAllTiles(features: SpatialDataTypes.SpatialRDD, levels: Range, resolution: Int, buffer: Int = 0, opts: BeastOptions = new BeastOptions()): RDD[(Long, IntermediateVectorTile)]
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/MVTDataVisualizer.scala:170  (+1 more definition site/overload)_

_Source doc:_ Plots all tiles in a range of Zoom levels according to the provided specifications and configuration @param features   the set of features to visualize @param minLevel   the minimum level to visualize (inclusive) @param maxLevel   the maximum level to visualize (inclusive) @param resolution the resolution of each tile @param buffer     the buffer around each tile to consider when visualizing @param opts       additional options for generating the tiles @return an RDD that contains all the generated tiles along with their IDs.

### Goal
Generates a distributed RDD of Mapbox Vector Tiles (MVT) across a specified range of zoom levels for web-based visualization of vector features.

### Parameters
- `features` (`SpatialDataTypes.JavaSpatialRDD` or `SpatialRDD`): The distributed set of vector features (e.g., polygons, lines, points) to visualize.
- `minLevel` (`Int`): The minimum zoom level to visualize (inclusive). Used in the Java API.
- `maxLevel` (`Int`): The maximum zoom level to visualize (inclusive). Used in the Java API.
- `resolution` (`Int`): The pixel resolution of each generated tile (typically 256 or 512).
- `buffer` (`Int`): The buffer around each tile in pixels to consider when visualizing, which prevents clipping artifacts for features that cross tile boundaries.
- `opts` (`BeastOptions`): Additional configuration options for generating the tiles, such as simplification thresholds (e.g., `"threshold" -> "1m"`).

*(Note: The Scala overload replaces `minLevel` and `maxLevel` with a single `levels: Range` parameter).*

### Input
A distributed RDD of vector features (`SpatialRDD`). This is typically loaded from vector formats like Shapefile, GeoJSON, or CSV using SparkContext extensions (e.g., `sc.shapefile(...)`). For massive datasets and deep zoom levels, it is highly recommended that the input features are spatially partitioned and indexed first (e.g., loaded via `sc.spatialFile(...)` from an R-Tree index) to optimize the distributed tile generation.

### Output
Returns `JavaPairRDD[java.lang.Long, IntermediateVectorTile]` (or `RDD[(Long, IntermediateVectorTile)]` in Scala) — an RDD containing the generated vector tiles keyed by their encoded Tile ID (Long). These intermediate tiles are typically passed directly to `MVTDataVisualizer.saveTilesCompact` to be written to disk as a compressed MVT archive.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast.common.BeastOptions
import edu.ucr.cs.bdlab.davinci.MVTDataVisualizer

// Example 1: Standard usage with a loaded shapefile
val opts = new BeastOptions().set("threshold", 0)
val features = sparkContext.shapefile("ne_10m_admin_1_states_provinces.zip")
val tiles = MVTDataVisualizer.plotAllTiles(features, levels = 0 to 6, resolution = 256, buffer = 5, opts)
MVTDataVisualizer.saveTilesCompact(tiles, "provinces_mvt.zip", opts)

// Example 2: Optimized usage with a pre-built spatial index for deep zoom levels
val indexedFeatures = sparkContext.spatialFile("provinces_index")
val deepTiles = MVTDataVisualizer.plotAllTiles(
  indexedFeatures, 
  levels = 0 to 19, 
  resolution = 256, 
  buffer = 5, 
  opts = new BeastOptions().set("threshold", "1m")
)
MVTDataVisualizer.saveTilesCompact(deepTiles, "provinces_deep_mvt.zip", new BeastOptions())
```

### LLM Instruction Prompt
- Call `MVTDataVisualizer.plotAllTiles` to generate multilevel vector tile pyramids for web maps.
- When writing Scala code, prefer the overload that takes a `Range` (e.g., `levels = 0 to 6`) rather than separate `minLevel` and `maxLevel` arguments.
- Always call this method on the `MVTDataVisualizer` object.
- Do not use this API for raster visualization. The DaVinci Server raster visualization is deprecated; MVT is strictly for vector data.
- Always follow up `plotAllTiles` with `MVTDataVisualizer.saveTilesCompact(tiles, outputPath, opts)` to persist the generated tiles to a zip archive.

### Prompt Snippet
```text
To generate Mapbox Vector Tiles (MVT) in Beast, use `MVTDataVisualizer.plotAllTiles(features, levels = min to max, resolution = 256, buffer = 5, opts)`. This returns an RDD of intermediate tiles. You must then save them using `MVTDataVisualizer.saveTilesCompact(tiles, "output.zip", opts)`. For large datasets spanning many zoom levels, spatially partition and index the features first.
```

### Common Failure Modes
- **Missing Receiver:** Attempting to call `features.plotAllTiles(...)` directly on the RDD. It must be called as `MVTDataVisualizer.plotAllTiles(features, ...)`.
- **Using Raster Data:** Passing a `RasterRDD` instead of a `SpatialRDD`. MVT generation is exclusively for vector geometries.
- **Out of Memory on Deep Zooms:** Generating tiles up to zoom level 19 on unpartitioned data can cause massive shuffles and OOM errors. The input should be spatially partitioned (e.g., `RSGrovePartitioner`) and saved as an index first.
- **Missing Save Step:** Forgetting to call `saveTilesCompact`, resulting in the Spark DAG never executing because no action was triggered.

### Fix Code Hint
```scala
// BAD: Calling on the RDD directly or forgetting to save
val tiles = features.plotAllTiles(0, 6, 256, 5, opts)

// GOOD: Calling on MVTDataVisualizer and saving the output
val tiles = MVTDataVisualizer.plotAllTiles(features, levels = 0 to 6, resolution = 256, buffer = 5, opts)
MVTDataVisualizer.saveTilesCompact(tiles, "output_mvt.zip", opts)

// BEST (for large data): Partition, index, then plot
features.partitionBy(classOf[RSGrovePartitioner]).saveAsIndex("my_index", "rtree")
val indexedFeatures = sparkContext.spatialFile("my_index")
val deepTiles = MVTDataVisualizer.plotAllTiles(indexedFeatures, levels = 0 to 14, resolution = 256, buffer = 5, opts)
MVTDataVisualizer.saveTilesCompact(deepTiles, "output_mvt.zip", opts)
```

## API Test: `plotFeatures`

### Signature
```scala
def plotFeatures(features: SpatialDataTypes.SpatialRDD, imageWidth: Int, imageHeight: Int, imagePath: String, plotterClass: Class[_ <: Plotter] = classOf[GeometricPlotter], canvasMBR: EnvelopeNDLite = null, opts: BeastOptions = new BeastOptions()): Unit
def plotFeatures(features: JavaSpatialRDD, minLevel: Int, maxLevel: Int, plotterClass: Class[_ <: Plotter], inputPath: String, outputPath: String, opts: BeastOptions): Unit
def plotFeatures(features: SpatialRDD, levels: Range, plotterClass: Class[_ <: Plotter], inputPath: String, outputPath: String, opts: BeastOptions): Unit
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/SingleLevelPlot.scala:58  (+2 more definition site/overload)_

_Source doc:_ Plots a set of features to a single image. By default, the aspect ratio of the input is maintained and the given dimensions are treated as upper bounds for image width and height, i.e., the produced image might have smaller dimensions. Also, by default, the extents of the canvas will be equal to the input data. This means that the plotted image will occupy the largest portion of the image. If you wish to visualize only a subset of the data or visualize the data on a small portion of the image, you can specify the [[canvasMBR]] parameter. @param features the set of features to plot @param imageWidth the width of the image in pixels @param imageHeight the height of the image in pixels. @param imagePath the path to which the image will be written @param plotterClass the class of the plotter to use for producing the image @param canvasMBR (Optional) the extents of the data (minimum bounding rectangle) @param opts (Optional) additional options to use with the plotter, e.g., colors

### Goal
Plots a distributed set of spatial features to a single image (or a multilevel image pyramid), maintaining the aspect ratio of the input data and optionally filtering the visualization to a specific bounding box.

### Parameters
- `features` (`SpatialDataTypes.SpatialRDD`): The distributed set of vector features (e.g., points, lines, polygons) to visualize.
- `imageWidth` (`Int`): The maximum width of the output image in pixels (treated as an upper bound to maintain aspect ratio).
- `imageHeight` (`Int`): The maximum height of the output image in pixels (treated as an upper bound to maintain aspect ratio).
- `imagePath` (`String`): The file path where the resulting image (e.g., PNG) will be written.
- `plotterClass` (`Class[_ <: Plotter]`), default `classOf[GeometricPlotter]`: The class of the plotter to use for rendering the geometries.
- `canvasMBR` (`EnvelopeNDLite`), default `null`: (Optional) The minimum bounding rectangle specifying the extents of the data to plot. If `null`, defaults to the full extent of the input data.
- `opts` (`BeastOptions`), default `new BeastOptions()`: (Optional) Additional configuration options for the plotter, such as styling (e.g., `"stroke"`, `"fill"`).

### Input
- A `SpatialRDD` of vector features, typically loaded via context extensions like `sc.shapefile`, `sc.geojsonFile`, or `sc.readCSVPoint`.
- Valid output file paths for the generated image (e.g., a `.png` file for single-level plots, or a `.zip` archive for multilevel pyramids).
- Styling configurations passed via `BeastOptions` (e.g., `.set("stroke", "blue")`).

### Output
Returns `Unit` — The operation is executed for its side effect of writing a rendered image file (or a ZIP archive of image tiles for the multilevel overloads) to the specified `imagePath` or `outputPath`.

### Valid Call Patterns
```scala
// Single-level plot (inferred from signature and sibling object usage)
SingleLevelPlot.plotFeatures(
  features = vectorRDD,
  imageWidth = 1024,
  imageHeight = 1024,
  imagePath = "output_image.png",
  plotterClass = classOf[GeometricPlotter],
  canvasMBR = null,
  opts = new BeastOptions().set("stroke", "blue").set("fill", "#9999E6")
)

// Multilevel plot (adapted from the project's Java README example to Scala)
MultilevelPlot.plotFeatures(
  features = vectorRDD,
  levels = 0 to 9,
  plotterClass = classOf[GeometricPlotter],
  inputPath = null,
  outputPath = "counties_multilevel_portable.zip",
  opts = new BeastOptions().set("stroke", "blue").set("fill", "#9999E6").setLong("threshold", 0)
)
```

### LLM Instruction Prompt
- Use `SingleLevelPlot.plotFeatures` to generate a single static image (e.g., PNG) from a `SpatialRDD`.
- Use `MultilevelPlot.plotFeatures` (using the `Range` or `minLevel, maxLevel` overloads) to generate a zoomable image pyramid saved as a ZIP archive.
- Always pass `classOf[GeometricPlotter]` as the `plotterClass` unless a specific custom plotter is requested.
- Use `BeastOptions` to define visual styles like `"stroke"` (outline color) and `"fill"` (interior color).
- Do not invent file paths; use the exact output paths requested by the user.

### Prompt Snippet
```text
To visualize the spatial features, use `SingleLevelPlot.plotFeatures` for a single image or `MultilevelPlot.plotFeatures` for a pyramid. Pass `classOf[GeometricPlotter]` and configure colors using `BeastOptions`. The dimensions provided to the single-level plot act as upper bounds to preserve the data's aspect ratio.
```

### Common Failure Modes
- **Missing Object Qualifier:** Attempting to call `plotFeatures(...)` as a bare function or directly on the RDD without the implicit wrapper (e.g., `rdd.plotFeatures(...)` instead of `SingleLevelPlot.plotFeatures(...)`), resulting in compilation errors.
- **Incorrect Plotter Class Type:** Passing an instantiated object (e.g., `new GeometricPlotter()`) instead of the class type (`classOf[GeometricPlotter]`).
- **Opaque/Invisible Features:** Failing to set `"stroke"` or `"fill"` in `BeastOptions`, which may result in default rendering that is difficult to see depending on the background.

### Fix Code Hint
```scala
// WRONG: rdd.plotFeatures(1000, 1000, "out.png")
// WRONG: SingleLevelPlot.plotFeatures(rdd, 1000, 1000, "out.png", new GeometricPlotter())

// CORRECT:
SingleLevelPlot.plotFeatures(
  rdd, 
  1000, 
  1000, 
  "out.png", 
  classOf[GeometricPlotter], 
  null, 
  new BeastOptions().set("stroke", "red")
)
```

## API Test: `plotImage`

### Signature
```scala
def plotImage(imageWidth: Int, imageHeight: Int, imagePath: String, plotterClass: Class[_ <: Plotter] = classOf[GeometricPlotter], opts: BeastOptions = new BeastOptions()): Unit
def plotImage(rdd: JavaSpatialRDD, imageWidth: Int, imageHeight: Int, imagePath: String, plotterClass: Class[_ <: Plotter], opts: BeastOptions): Unit
def plotImage(rdd: JavaSpatialRDD, imageWidth: Int, imageHeight: Int, imagePath: String, opts: BeastOptions): Unit
def plotImage(rdd: JavaSpatialRDD, imageWidth: Int, imageHeight: Int, imagePath: String): Unit
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:239  (+3 more definition site/overload)_

_Source doc:_ Plots the features to an image using the given plotter @param imageWidth the width of the image in pixels @param imageHeight the height of the image in pixels @param imagePath the path to write the generated image @param plotterClass the plotter class @param opts additional user options

### Goal
Renders a distributed spatial RDD of vector features into a single image file (e.g., PNG) with specified pixel dimensions for quick visualization.

### Parameters
- `rdd` (`JavaSpatialRDD`): The spatial RDD containing the vector features to plot. In Scala, this is typically passed implicitly as the receiver (e.g., `features.plotImage(...)`).
- `imageWidth` (`Int`): The width of the generated output image in pixels.
- `imageHeight` (`Int`): The height of the generated output image in pixels.
- `imagePath` (`String`): The file path where the generated image will be saved (e.g., `"output.png"`).
- `plotterClass` (`Class[_ <: Plotter], opts: BeastOptions`): The class of the plotter to use (defaults to `classOf[GeometricPlotter]`), and an optional `BeastOptions` object for additional user configuration.

### Input
A spatial RDD of vector features (e.g., loaded via `sc.shapefile`, `sc.geojsonFile`, or generated via `sc.generateSpatialData`). The operation requires the features to have valid geometries. 

### Output
Returns `Unit` — writes a single image file (typically a PNG) to the specified `imagePath` on the driver or accessible file system.

### Valid Call Patterns
```scala
// Pattern 1: Plotting a loaded vector dataset (Shapefile, GeoJSON, etc.)
val buildings = sc.shapefile("MSBuildings_data_index.zip")
buildings.plotImage(1000, 1000, "MSBuildings.png")

// Pattern 2: Plotting generated spatial data
sc.generateSpatialData
  .makeBoxes(0.1, 0.2)
  .uniform(100)
  .plotImage(300, 300, "uniform.png")
```

### LLM Instruction Prompt
- Use `rdd.plotImage(width, height, path)` as an implicit method on a spatial RDD to quickly generate a single PNG image of vector features.
- Do not use `plotImage` for massive datasets where a single image would be too dense or exceed memory limits; for web-based exploration of large datasets, prefer generating MVT (Mapbox Vector Tiles) or using `plotPyramid`.
- Do not use `plotImage` for raster visualization, as the DaVinci Server is deprecated and `plotImage` is designed for plotting vector features.

### Prompt Snippet
```text
To visualize the generated spatial data or loaded shapefiles, use the `plotImage` method directly on the RDD. Provide the desired width, height, and output file path (e.g., "output.png").
```

### Common Failure Modes
- **Calling on Raster Data:** Attempting to use `plotImage` on a `RasterRDD` instead of a vector feature RDD. `plotImage` is designed for vector features.
- **OOM on Driver:** Generating an extremely large single image (e.g., `imageWidth = 50000`) which exceeds the driver's memory capacity, as the final image must be collected and written.
- **Missing File Extension:** Providing an `imagePath` without a valid image extension (like `.png`), which may cause the underlying image writer to fail or produce an unreadable file.

### Fix Code Hint
```scala
// BAD: Attempting to plot a raster or missing the implicit receiver
// val raster = sc.geoTiff[Int]("data.tif")
// plotImage(raster, 1000, 1000, "out.png")

// GOOD: Plotting vector features using the implicit class syntax
val features = sc.shapefile("ne_10m_admin_0_countries.zip")
features.plotImage(1920, 1080, "countries.png")
```

## API Test: `plotPyramid`

### Signature
```scala
def plotPyramid(outPath: String, numLevels: Int, plotterClass: Class[_ <: Plotter] = classOf[GeometricPlotter], opts: BeastOptions = new BeastOptions()): Unit
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/VisualizationMixin.scala:53_

_Source doc:_ Plots the dataset as multilevel tiled image and write the output to the given path. @param outPath the output path to write the image tiles to. @param numLevels the number of levels to create @param plotterClass the plotter class to use for plotting @param opts additional options for the plotter

### Goal
Generates a multilevel tiled image pyramid from a spatial dataset and writes the output to a specified path (typically a ZIP archive) for web-based map visualization.

### Parameters
- `outPath` (`String`): The destination path where the image tiles will be written, typically ending in `.zip` to create a compressed archive of the pyramid.
- `numLevels` (`Int`): The number of zoom levels to generate for the pyramid (e.g., 10 or 20).
- `plotterClass` (`Class[_ <: Plotter]`), default `classOf[GeometricPlotter]`: The plotter implementation class used to render the geometries into pixels.
- `opts` (`BeastOptions`), default `new BeastOptions()`: Additional configuration options for the plotter (e.g., `mercator`, `stroke`, `threshold`). Note: Beast provides implicit conversions allowing `Seq[(String, Any)]` to be passed here.

### Input
A spatial RDD of vector features (e.g., loaded via `sc.shapefile` or `sc.spatialFile`). For large datasets, it is highly recommended to spatially partition the data (e.g., using `RSGrovePartitioner`) and optionally write it to an indexed spatial file before plotting to ensure efficient distributed rendering.

### Output
Returns `Unit` — the operation is a side-effect that writes a ZIP archive containing the multilevel image pyramid (PNG tiles organized by zoom level) to the specified `outPath`.

### Valid Call Patterns
```scala
// Example 1: Plotting an indexed spatial file with 20 levels
sparkContext.spatialFile("counties_index")
  .plotPyramid("counties_multilevel.zip", 20,
    opts = Seq("mercator" -> true, "stroke" -> "blue", "threshold" -> "1m"))

// Example 2: Plotting directly from a shapefile with 10 levels
sparkContext.shapefile("tl_2018_us_county.zip")
  .plotPyramid("counties_multilevel_portable.zip", 10,
    opts = Seq("mercator" -> true, "stroke" -> "blue", "threshold" -> 0))
```

### LLM Instruction Prompt
- Call `plotPyramid(outPath, numLevels, ...)` on a spatial RDD to generate a multilevel image pyramid for visualization.
- Always provide a `.zip` extension for `outPath` to package the generated tiles compactly.
- Pass configuration options like `"mercator" -> true` or `"stroke" -> "blue"` using the `opts` parameter (which accepts a `Seq` via implicit conversion).
- Prefer spatially partitioning the RDD (e.g., `classOf[RSGrovePartitioner]`) before plotting large datasets to ensure distributed rendering.
- Be aware that the underlying DaVinci Server visualization is marked for deprecation; for modern vector visualization, prefer generating Mapbox Vector Tiles (MVT).

### Prompt Snippet
```text
To visualize a spatial RDD as a web map, use `rdd.plotPyramid("output.zip", 10, opts = Seq("mercator" -> true, "stroke" -> "blue"))`. For large datasets, partition with `RSGrovePartitioner` first. Note: DaVinci raster visualization is being deprecated in favor of MVT for vectors.
```

### Common Failure Modes
- **Performance bottlenecks:** Calling `plotPyramid` on a massive, unpartitioned dataset can cause memory issues or extremely slow rendering. *Fix:* Spatially partition the RDD using `spatialPartition(classOf[RSGrovePartitioner])` before plotting.
- **Missing Implicit Conversions:** If passing a `Seq` to `opts` fails to compile, ensure the standard Beast implicits are imported so the `Seq` can be implicitly converted to `BeastOptions`.
- **Deprecated Visualization Warning:** Relying heavily on `plotPyramid` for new vector visualization pipelines may incur technical debt, as the DaVinci Server is explicitly marked as "will be deprecated soon." Consider `MVTDataVisualizer` for modern vector tile generation.

### Fix Code Hint
```scala
// Inefficient/Failing: Plotting large unpartitioned data
val features = sc.shapefile("large_dataset.zip")
features.plotPyramid("output.zip", 10)

// Fix: Spatially partition before plotting for distributed rendering
val partitioned = features.spatialPartition(classOf[RSGrovePartitioner])
partitioned.plotPyramid("output.zip", 10, opts = Seq("mercator" -> true, "stroke" -> "red"))
```

## API Test: `plotSingleTileParallel`

### Signature
```scala
def plotSingleTileParallel(features: SpatialDataTypes.SpatialRDD, resolution: Int, tileID: Long, buffer: Int = 0, opts: BeastOptions = new BeastOptions()): VectorTile.Tile
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/MVTDataVisualizer.scala:98_

_Source doc:_ Plots the given set of features as a vector tile according to Mapbox specifications using a Spark job. @param features the set of features to plot @param resolution the resolution of the image in pixels @param tileID the ID of the tile to plot @param buffer additional pixels around the tile to plot from all directions (default is zero) @param opts additional options to customize the plotting @return a vector tile that contains all the given features

### Goal
Generates a single Mapbox Vector Tile (MVT) from a distributed `SpatialRDD` of vector features using a Spark job, projecting the geometries into the tile's image space.

### Parameters
- `features` (`SpatialDataTypes.SpatialRDD`): The distributed set of vector features (e.g., points, lines, polygons) to plot into the tile.
- `resolution` (`Int`): The resolution of the vector tile in pixels (e.g., 128, 256, or 4096 for standard MVT extents).
- `tileID` (`Long`): The encoded ID of the tile to plot, typically generated from Z, X, Y coordinates.
- `buffer` (`Int`), default `0`: Additional pixels around the tile to plot from all directions to prevent clipping artifacts at tile edges.
- `opts` (`BeastOptions`), default `new BeastOptions()`: Additional configuration options to customize the plotting behavior.

### Input
- **Data:** A `SpatialRDD` (alias for `RDD[IFeature]`) containing vector geometries.
- **Preconditions:** The geometries must be loaded and valid. To target a specific tile, the `tileID` must be properly encoded (e.g., using `TileIndex.encode(z, x, y)` as demonstrated in the test suite).

### Output
Returns `VectorTile.Tile` — A Java object representing a Mapbox Vector Tile containing all the given features, with geometries projected and zigzag-encoded into the tile's local coordinate space.

### Valid Call Patterns
```scala
// Assuming `features` is a valid SpatialRDD (RDD[IFeature])
val resolution = 256
val buffer = 0
val tileId = TileIndex.encode(0, 0, 0) // Encode Z, X, Y

val tile = MVTDataVisualizer.plotSingleTileParallel(features, resolution, tileId, buffer)
```

### LLM Instruction Prompt
- Call `plotSingleTileParallel` on the `MVTDataVisualizer` object, passing the `SpatialRDD` as the first argument. Do not attempt to call it as an instance method on the RDD itself.
- Always encode the Z, X, Y tile coordinates into a `Long` using `TileIndex.encode(z, x, y)` before passing it as the `tileID` parameter.
- Ensure the `resolution` parameter is an `Int` representing the tile extent (e.g., 256 or 4096).

### Prompt Snippet
```text
To generate a single Mapbox Vector Tile from a SpatialRDD, use `MVTDataVisualizer.plotSingleTileParallel(features, resolution, TileIndex.encode(z, x, y), buffer)`. Do not call this as an RDD method. The tileID must be an encoded Long, not raw Z/X/Y integers.
```

### Common Failure Modes
- **Method Not Found on RDD:** Attempting to call `features.plotSingleTileParallel(...)` will fail because it is a method on the `MVTDataVisualizer` object, not an implicit RDD extension.
- **Type Mismatch for Tile ID:** Passing raw `z, x, y` integers instead of a single encoded `Long` for the `tileID` parameter.
- **Missing TileIndex Import:** Failing to import or use `TileIndex.encode` to generate the required `Long` ID.

### Fix Code Hint
```scala
// WRONG: Calling on the RDD and passing raw Z, X, Y
// val tile = features.plotSingleTileParallel(256, 0, 0, 0)

// CORRECT: Calling on MVTDataVisualizer and encoding the tile ID
val tileId = TileIndex.encode(0, 0, 0)
val tile = MVTDataVisualizer.plotSingleTileParallel(features, 256, tileId, 0)
```

## API Test: `pointSample`

### Signature
```scala
def pointSample(features: SpatialRDD, sampleSize: Int, sampleRatio: Double, seed: Long = System.currentTimeMillis()): Array[Array[Double]]
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/synopses/PointSampler.scala:47_

_Source doc:_ Reads a point sample from the given spatial RDD. It returns a two dimensional array where the first index is the dimension and the second index is the point. This method runs an action on the given RDD. The method takes both a sample size and sample ratio and it returns whichever is smaller. In other words, it tries to read the given sample ratio and if the result is bigger than the sample size, it truncates it to the sample size. This ensures that the final result will fit in memory regardless of the input size. @param features the input features to sample @param sampleSize number of sample points to read @param sampleRatio the ratio of the points to read @return a two-dimensional array of sample points

### Goal
Extracts a random sample of point coordinates from a distributed vector dataset (`SpatialRDD`), bounding the result by a maximum size to ensure it safely fits in the driver's memory.

### Parameters
- `features` (`SpatialRDD`): The input spatial RDD (typically `RDD[IFeature]`) containing the vector geometries to sample.
- `sampleSize` (`Int`): The absolute maximum number of sample points to read. If the `sampleRatio` yields more points than this limit, the result is truncated to `sampleSize`.
- `sampleRatio` (`Double`): The fraction of the dataset to read (e.g., `0.01` for 1%).
- `seed` (`Long`), default `System.currentTimeMillis()`: The random seed used for sampling to ensure reproducibility if needed.

### Input
- **Data:** A `SpatialRDD` containing vector features (e.g., loaded via `sc.shapefile` or `sc.geojsonFile`).
- **Preconditions:** The RDD can safely contain empty partitions or features with `null` geometries; the sampler is designed to handle these without failing. 

### Output
Returns `Array[Array[Double]]` — A two-dimensional array of the sampled coordinates collected to the Spark driver. **Note the transposed structure:** The *first* index represents the spatial dimension (e.g., `0` for X/Longitude, `1` for Y/Latitude), and the *second* index represents the specific point. For example, `result(0)(5)` gives the X coordinate of the 6th sampled point.

### Valid Call Patterns
```scala
// Extract a sample of up to 10,000 points, targeting 1% of the dataset
val sample: Array[Array[Double]] = PointSampler.pointSample(features, 10000, 0.01)

// Accessing the X and Y coordinates of the first sampled point
val firstX = sample(0)(0)
val firstY = sample(1)(0)
```

### LLM Instruction Prompt
- Call `PointSampler.pointSample(features, sampleSize, sampleRatio)` as an object method, not as an instance method on the RDD.
- Always provide both `sampleSize` and `sampleRatio`. The method evaluates both and returns whichever yields fewer points to prevent driver OutOfMemory errors.
- Remember that the returned 2D array is dimension-major, not point-major. `array(0)` contains all X coordinates, and `array(1)` contains all Y coordinates.

### Prompt Snippet
```text
PointSampler.pointSample(features: SpatialRDD, sampleSize: Int, sampleRatio: Double): Array[Array[Double]]
Samples points from a SpatialRDD. Returns a dimension-major 2D array (index 0 is dimension, index 1 is point). Truncates to sampleSize if sampleRatio yields too many points. Call on the PointSampler object.
```

### Common Failure Modes
- **Assuming a point-major array:** Iterating over the outer array expecting each element to be a `[X, Y]` coordinate pair. The outer array represents dimensions (X-array, Y-array).
- **Calling as an RDD method:** Attempting to call `features.pointSample(...)` will fail to compile. It must be called via the `PointSampler` object.
- **Driver OOM (Avoided):** Users might worry about pulling too much data to the driver. The API explicitly prevents this by enforcing the `sampleSize` cap, so users should set `sampleSize` to a safe memory limit (e.g., `100000`).

### Fix Code Hint
```scala
// WRONG: Assuming point-major format or calling as an instance method
val sample = features.pointSample(1000, 0.1)
val firstPointX = sample(0)(0)
val firstPointY = sample(0)(1) // IndexOutOfBoundsException or wrong data

// RIGHT: Call on PointSampler and use dimension-major indexing
val sample = PointSampler.pointSample(features, 1000, 0.1)
val firstPointX = sample(0)(0) // Dimension 0 (X), Point 0
val firstPointY = sample(1)(0) // Dimension 1 (Y), Point 0
```

## API Test: `printOperationUsage`

### Signature
```scala
def printOperationUsage(operation: Operation, options: BeastOptions, out: PrintStream): Unit
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/OperationHelper.scala:334_

_Source doc:_ Prints the usage of a specific operation. @param operation the operation to print the usage to @param out the print stream to write to

### Goal
Prints the command-line usage instructions and parameter details for a specific Beast operation to a provided output stream.

### Parameters
- `operation` (`Operation`): The metadata object representing the specific Beast operation (e.g., retrieved from the `OperationHelper.operations` registry) for which to print usage.
- `options` (`BeastOptions`): Configuration options for the Beast environment. Can safely be `null` if no specific options are required for formatting the output.
- `out` (`PrintStream`): The Java `PrintStream` (such as `System.out` or one wrapping a `ByteArrayOutputStream`) where the usage text will be written.

### Input
Requires a valid `Operation` instance (typically fetched by name from Beast's internal operation registry) and an open, writable `PrintStream`. 

### Output
Returns `Unit` — performs a side effect by writing the formatted usage string (including expected parameters and descriptions) to the provided `PrintStream`.

### Valid Call Patterns
```scala
import java.io.{ByteArrayOutputStream, PrintStream}
import edu.ucr.cs.bdlab.beast.util.OperationHelper

// 1. Writing usage to a byte array (useful for testing or capturing output)
val baos = new ByteArrayOutputStream()
val printer: PrintStream = new PrintStream(baos)

// Retrieve the operation by name and print its usage (options can be null)
val op = OperationHelper.operations("subtest1")
OperationHelper.printOperationUsage(op, null, printer)

printer.close()
val usageString = new String(baos.toByteArray)

// 2. Writing usage directly to standard output
OperationHelper.printOperationUsage(op, null, System.out)
```

### LLM Instruction Prompt
- Use `OperationHelper.printOperationUsage` when you need to programmatically output or capture the CLI help text and parameter requirements for a specific Beast operation.
- The `options` parameter of type `BeastOptions` can be passed as `null` if no specific configuration is needed.
- Always call this method on the `OperationHelper` object.

### Prompt Snippet
```text
To print or capture the usage instructions for a specific Beast operation, use `OperationHelper.printOperationUsage(operation, options, printStream)`. You can retrieve the `Operation` object from `OperationHelper.operations("operationName")`. The `options` parameter can safely be `null`.
```

### Common Failure Modes
- **Null Pointer Exception on Operation:** Attempting to fetch an unregistered operation name from `OperationHelper.operations("invalid_name")` will yield an error or `null` before `printOperationUsage` is even called.
- **Closed Stream:** Passing a `PrintStream` that has already been closed will result in the usage text not being written or throwing an `IOException`.

### Fix Code Hint
```scala
// Ensure the operation exists in the registry before printing
val opName = "my_operation"
if (OperationHelper.operations.contains(opName)) {
  val op = OperationHelper.operations(opName)
  OperationHelper.printOperationUsage(op, null, System.out)
} else {
  println(s"Operation $opName not found.")
}
```

## API Test: `putStoredFile`

### Signature
```scala
def putStoredFile(zip: ZipOutputStream, filename: String, data: Array[Byte]): Unit
def putStoredFile(zip: org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream, filename: String, data: Array[Byte]): Unit
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/ZipUtil.scala:584  (+1 more definition site/overload)_

_Source doc:_ Add a file to the given ZIP file using [[ZipEntry.STORED]] method, i.e., no compression. @param zip the ZIP file to write the entry to @param filename the name of the entry in the ZIP file @param data the binary data of the file

### Goal
Writes a file entry into an open ZIP archive without applying compression (using the `STORED` method), which is useful when packaging pre-compressed geospatial artifacts like MVT vector tiles or image pyramids.

### Parameters
- `zip` (`ZipOutputStream`): The open ZIP output stream (either `java.util.zip.ZipOutputStream` or Apache Commons `ZipArchiveOutputStream`) to which the new file entry will be appended.
- `filename` (`String`): The name and internal path of the entry to create within the ZIP archive (e.g., `"README.bin"` or `"data.bin"`).
- `data` (`Array[Byte]`): The raw binary data of the file to be written into the archive.

### Input
The caller must provide an open, writable `ZipOutputStream` (typically wrapping a `FileOutputStream` or Hadoop `FileSystem` output stream). The `data` must be a fully materialized byte array. The stream must not be closed prior to calling this method.

### Output
Returns `Unit` — modifies the provided `ZipOutputStream` in-place by appending a new uncompressed `ZipEntry` containing the provided byte array, calculating and setting the necessary CRC-32 checksum and size headers automatically.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast.util.ZipUtil
import java.util.zip.ZipOutputStream
import java.io.{File, FileOutputStream}

val file1 = new File(scratchDir, "test1.zip")
val zip1 = new ZipOutputStream(new FileOutputStream(file1))

// Write uncompressed files to the ZIP stream
ZipUtil.putStoredFile(zip1, "README.bin", Array[Byte](1, 2, 3, 4, 5, 6))
ZipUtil.putStoredFile(zip1, "data.bin", Array[Byte](1, 2, 3))

// The caller is responsible for closing the stream
zip1.close()
```

### LLM Instruction Prompt
- When writing raw byte arrays to a ZIP archive in Beast/RDPro without compression, use `ZipUtil.putStoredFile(zip, filename, data)`. Do not manually create `ZipEntry` objects or calculate CRC checksums, as this utility handles the `STORED` method requirements automatically. Always ensure the caller closes the `ZipOutputStream` after all files are added.

### Prompt Snippet
```text
ZipUtil.putStoredFile(zipStream, "filename.ext", byteArray)
```

### Common Failure Modes
- **Closed Stream Exception:** Calling this method on a `ZipOutputStream` that has already been closed will throw an `IOException`.
- **Corrupted Archive:** Failing to call `.close()` on the `ZipOutputStream` after adding all files will result in an incomplete or corrupted ZIP file that cannot be read by standard tools.
- **Duplicate Entry:** Attempting to write multiple files with the exact same `filename` to the same `ZipOutputStream` will throw a `ZipException`.

### Fix Code Hint
```scala
val zipStream = new ZipOutputStream(fileSystem.create(outPath))
try {
  ZipUtil.putStoredFile(zipStream, "tile_0_0.mvt", tileDataBytes)
} finally {
  zipStream.close() // Always close the stream to finalize the ZIP directory
}
```

## API Test: `rangeQuery`

### Signature
```scala
def rangeQuery(range: Geometry, mbrCount: LongAccumulator = null): SpatialRDD
def rangeQuery(range: Geometry, mbrCount: LongAccumulator = null): PartitionedSpatialRDD
def rangeQuery(rdd: JavaSpatialRDD, range: Geometry): JavaSpatialRDD
def rangeQuery(rdd: JavaSpatialRDD, range: Geometry, mbrCount: LongAccumulator): JavaSpatialRDD
def rangeQuery(partitionedRDD: JavaPartitionedSpatialRDD, range: Geometry): JavaPartitionedSpatialRDD
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:131  (+4 more definition site/overload)_

_Source doc:_ Performs a range query while counting the number of MBR tests for profiling the performance. @param rdd the RDD that contains the spatial features @param range the query range @param mbrCount (out) an accumulator that counts the number of MBR tests @return a filtered RDD with the features that intersect the given query range

### Goal
Filters a spatial RDD to return only the vector features that intersect a specified geometric bounding box or spatial range.

### Parameters
- `rdd` (`JavaSpatialRDD` / `JavaPartitionedSpatialRDD`): The input RDD containing spatial features (explicit in the Java API overloads; in Scala, this is the implicit receiver of the extension method).
- `range` (`Geometry`): The spatial range to search for, typically provided as a JTS `Geometry`, `EnvelopeND`, or `EnvelopeNDLite`.
- `mbrCount` (`LongAccumulator`): An optional Spark accumulator used to count the number of Minimum Bounding Rectangle (MBR) tests performed during the query, useful for performance profiling. Defaults to `null`.

### Input
- **Data:** A `SpatialRDD` or `PartitionedSpatialRDD` of vector features (e.g., loaded from Shapefile, GeoJSON, or CSV).
- **Preconditions:** 
  - For optimal performance (query pruning), the input RDD should be spatially partitioned first (e.g., using `GridPartitioner` or `RSGrovePartitioner`). If it is not partitioned, a full dataset scan will occur.
  - The `range` geometry must be in the same Coordinate Reference System (CRS) as the input RDD. If they differ, the query geometry must be explicitly created with the matching SRID.

### Output
Returns `SpatialRDD` (or `PartitionedSpatialRDD` / `JavaSpatialRDD` depending on the overload) — A filtered distributed collection containing only the features that intersect the provided query range. If the input was partitioned, the output retains the partitioning scheme but typically contains fewer partitions (only those intersecting the range).

### Valid Call Patterns
```scala
// Pattern 1: Using EnvelopeNDLite (from README)
val range = new EnvelopeNDLite(2, -117.337182, 33.622048, -117.241395, 33.72865)
val matchedPolygons: RDD[IFeature] = polygons.rangeQuery(range)

// Pattern 2: Using EnvelopeND on a partitioned RDD (from test suite)
val mbr = data.summary
val gridPartitioner = new GridPartitioner(mbr, Array(2, 2))
val partitionedData = data.spatialPartition(gridPartitioner)
val filteredData = partitionedData.rangeQuery(
  new EnvelopeND(new GeometryFactory, 2, -100, 30, -90, 40)
)

// Pattern 3: Handling a specific CRS (from test suite)
val rangeWithCRS = new GeometryFactory(new PrecisionModel(), 3857)
  .toGeometry(new Envelope(-11131949.07, -10018754.17, 3503549.84, 4865942.27))
val filteredDataCRS = partitionedData.rangeQuery(rangeWithCRS)
```

### LLM Instruction Prompt
- Always call `rangeQuery` as an instance method on a `SpatialRDD` or `PartitionedSpatialRDD` in Scala (e.g., `rdd.rangeQuery(range)`).
- Pass a valid JTS `Geometry`, `EnvelopeND`, or `EnvelopeNDLite` as the `range` parameter.
- If the input RDD has a specific Coordinate Reference System (CRS), ensure the query geometry is created with the matching SRID using a `GeometryFactory`.
- To avoid duplicate results when features span multiple partitions, ensure the RDD is partitioned using a disjoint partitioner (`GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner`).

### Prompt Snippet
```text
To filter spatial features within a bounding box, use `rdd.rangeQuery(range)`. For best performance, ensure the RDD is spatially partitioned first (e.g., `rdd.spatialPartition(classOf[RSGrovePartitioner])`). The `range` can be an `EnvelopeNDLite` or a JTS `Geometry`. If your data uses a specific CRS (like EPSG:3857), construct the query geometry with a matching `GeometryFactory`.
```

### Common Failure Modes
- **CRS Mismatch:** Querying with a geometry in a different CRS than the RDD features will yield empty or incorrect results. The `rangeQuery` does not automatically reproject the bounding box.
- **Duplicate Results:** If the RDD is partitioned using a non-disjoint partitioner, features overlapping partition boundaries might be returned multiple times.
- **Unpartitioned Full Scan:** Calling `rangeQuery` on an unpartitioned RDD works but requires a full scan of the dataset, negating the performance benefits of spatial indexing.

### Fix Code Hint
```scala
// Fix CRS mismatch by assigning the correct SRID to the query geometry
val geomFactory = new GeometryFactory(new PrecisionModel(), 3857)
val range = geomFactory.toGeometry(new Envelope(minX, maxX, minY, maxY))
val filtered = rdd.rangeQuery(range)

// Fix duplicate results by ensuring disjoint partitioning before the query
val partitionedData = rdd.spatialPartition(classOf[RSGrovePartitioner])
val deduplicatedFiltered = partitionedData.rangeQuery(range)
```

## API Test: `raptorJoin`

### Signature
```scala
def raptorJoin(features: SpatialRDD, opts: BeastOptions = new BeastOptions)
def raptorJoin[T](vectors: JavaSpatialRDD, rasters: JavaRasterRDD[T], opts: BeastOptions): JavaRDD[RaptorJoinFeature[T]]
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:269  (+1 more definition site/overload)_

_Source doc:_ Performs a raster X vector join (Raptor join) between the two given RDDs. @param vectors the set of vector features @param rasters the set of raster tiles @param opts additional options for the algorithm @return the intersection between the feature vectors and all raster pixels.

### Goal
Performs a Raptor (Raster-Plus-Vector) join to concurrently match vector geometries (polygons, lines, points) with underlying raster pixels at scale, typically used for zonal statistics and masking.

### Parameters
- `vectors` (`JavaSpatialRDD` / `SpatialRDD`): The set of vector features (e.g., administrative boundaries, points of interest) to join against the raster. In the Scala API, this is named `features`.
- `rasters` (`JavaRasterRDD[T]`): The raster dataset containing the pixels to be joined. In the idiomatic Scala API, this is the implicit receiver (e.g., `rasters.raptorJoin(vectors)`).
- `opts` (`BeastOptions`): Additional options to configure the join operation (defaults to `new BeastOptions`).

### Input
- **Vector Data:** Must be loaded via Beast context extensions like `sc.shapefile`, `sc.geojsonFile`, or `sc.readCSVPoint`.
- **Raster Data:** Must be loaded via `sc.geoTiff[T]` or `sc.hdfFile`.
- **Type-Parameter Selection Rule:** The type parameter `[T]` of the raster (and consequently the join) must exactly match the file's runtime pixel type (e.g., `FloatType` $\rightarrow$ `sc.geoTiff[Float]`, `IntegerType` $\rightarrow$ `sc.geoTiff[Int]`).
- **Geometric Matching Predicates:** 
  - *Points* match the single pixel containing them.
  - *Lines* match pixels intersecting the line's crosshair.
  - *Polygons* match pixels whose **center** falls inside the polygon boundary.

### Output
Returns `JavaRDD[RaptorJoinFeature[T]]` (or `RDD[RaptorJoinFeature[T]]` in Scala) — an RDD representing all overlaps between the given features and the pixels. Each `RaptorJoinFeature` contains the matched vector feature geometry and the underlying pixel value (accessible via the `.m` property).

### Valid Call Patterns
```scala
val treecover: RDD[ITile[Float]] = sc.geoTiff("treecover")
val countries: RDD[IFeature] = sc.shapefile("ne_10m_admin_0_countries.zip")
val join: RDD[RaptorJoinFeature[Float]] = treecover.raptorJoin(countries)
  .filter(v => v.m >= 0 && v.m <= 100.0)
```

### LLM Instruction Prompt
- Use the instance method `raster.raptorJoin(vector)` for idiomatic Scala Spark pipelines.
- ALWAYS ensure the type parameter `T` matches the pixel type of the loaded raster (e.g., `Float` for `sc.geoTiff[Float]`).
- Remember the Raptor polygon predicate: pixels are only joined if their *center* falls inside the polygon. Do not assume edge-touching pixels are included.
- Access the matched pixel value in the resulting `RaptorJoinFeature` using the `.m` property.

### Prompt Snippet
```text
To perform zonal statistics or raster-vector joins in RDPro, use `raster.raptorJoin(vector)`. Ensure the raster is loaded with the correct exact pixel type (e.g., `sc.geoTiff[Float]`). The result is an RDD of `RaptorJoinFeature[T]`. You can access the pixel value via `.m`. Note that for polygons, Raptor only matches pixels whose center falls inside the polygon boundary.
```

### Common Failure Modes
- **Type Mismatch:** Loading a raster as `sc.geoTiff[Int]` when the underlying GeoTIFF is `FloatType`, causing the `raptorJoin` to fail or return garbage data. The type `T` must strictly match the runtime pixel type.
- **Missing Edge Pixels in Polygons:** Users expecting a polygon to match a pixel it barely touches. Polygons only match pixels if the pixel's *center* falls inside the polygon boundary.
- **Calling as a Static Method in Scala:** Attempting `raptorJoin(vectors, rasters)` in Scala instead of the idiomatic implicit extension `rasters.raptorJoin(vectors)`.

### Fix Code Hint
```scala
// WRONG: Type mismatch (assuming Int for Float data) and incorrect static call
val raster = sc.geoTiff[Int]("float_data.tif")
val join = raptorJoin(vectors, raster)

// CORRECT: Match the exact pixel type (Float), use instance method, and access pixel via .m
val raster = sc.geoTiff[Float]("float_data.tif")
val join = raster.raptorJoin(vectors)
  .filter(pixel => pixel.m >= 0.0) // .m holds the pixel value of type Float
```

## API Test: `raptorJoinFeature`

### Signature
```scala
def raptorJoinFeature[T](raster: RasterRDD[T], features: RDD[IFeature], opts: BeastOptions = new BeastOptions(), numTiles: LongAccumulator = null): RDD[RaptorJoinFeature[T]]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorJoin.scala:73_

_Source doc:_ Performs a raptor join between a raster RDD and a set of features. The output contains information about all pixels that match with the set of features. @param raster the raster RDD that contains all the tiles to test @param features the set of features to join with the raster data @param opts additional options for the query processor @param numTiles an optional accumulator to count the number of tiles accesses during the query processing. @tparam T the type of the pixel values @return the set of overlaps between pixels and features

### Goal
Performs a distributed raster-vector join (Raptor join) to find all raster pixels that intersect with a set of vector features, enabling zonal statistics and spatial masking at scale.

### Parameters
- `raster` (`RasterRDD[T]`): The raster RDD containing the tiles and pixel data to test against the vector geometries.
- `features` (`RDD[IFeature]`): The set of vector features (polygons, lines, or points) to join with the raster data.
- `opts` (`BeastOptions`), default `new BeastOptions()`: Additional configuration options for the query processor.
- `numTiles` (`LongAccumulator`), default `null`: An optional Spark accumulator used to count the number of raster tiles accessed during query processing.

### Input
- **Raster Data:** A `RasterRDD[T]` loaded via `sc.geoTiff[T]` or `sc.hdfFile`. The type parameter `T` must exactly match the file's runtime pixel type (e.g., `Int` for `IntegerType`, `Float` for `FloatType`).
- **Vector Data:** An `RDD[IFeature]` loaded via context extensions like `sc.shapefile`, `sc.geojsonFile`, or `sc.readCSVPoint`.
- **Preconditions (Raptor Predicates):** The join matches geometries to pixels based on specific rules:
  - *Points* match the single pixel containing them.
  - *Lines* match pixels intersecting the line's crosshair.
  - *Polygons* match pixels whose **center** falls inside the polygon boundary.

### Output
Returns `RDD[RaptorJoinFeature[T]]` — an RDD containing the overlaps between individual raster pixels and vector features. Each record pairs a matched pixel value of type `T` with its corresponding vector feature, which can then be aggregated (e.g., grouped by feature ID) to compute zonal statistics.

### Valid Call Patterns
```scala
// Load raster with exact type matching the file
val raster: RasterRDD[Int] = sc.geoTiff[Int]("glc2000_v1_1.tif")

// Load vector features
val countries: RDD[IFeature] = sc.shapefile("ne_10m_admin_0_countries.zip")

// Perform the Raptor join using the object method
val result: RDD[RaptorJoinFeature[Int]] = RaptorJoin.raptorJoinFeature(raster, countries, new BeastOptions())

// Example aggregation: count pixels per country
val pixelCounts = result.map(x => x.feature.getAs[String]("NAME")).countByValue()
```

### LLM Instruction Prompt
- Use `RaptorJoin.raptorJoinFeature(raster, features)` to perform raster-vector joins for zonal statistics.
- **Crucial Type Rule:** The type parameter `T` of the `RasterRDD` must exactly match the underlying GeoTIFF pixel type (e.g., `Int` for IntegerType, `Float` for FloatType).
- **Crucial Matching Rule:** Remember that polygon joins only match pixels whose *center* falls inside the polygon boundary. Very small polygons may yield empty results if they do not cover any pixel centers.

### Prompt Snippet
```text
To join raster pixels with vector features for zonal statistics, use `RaptorJoin.raptorJoinFeature(raster, features)`. Ensure the raster's type parameter `T` matches the physical file type (e.g., `sc.geoTiff[Int]`). Polygons match pixels by their center point.
```

### Common Failure Modes
- **Type Mismatch Exceptions:** Loading the raster with the wrong type parameter (e.g., using `sc.geoTiff[Float]` for an integer raster) will cause runtime serialization or cast errors during the join.
- **Missing Pixel Matches for Small Polygons:** Because polygons only match pixels if the pixel's *center* falls inside the boundary, very small polygons (relative to the raster resolution) might not match any pixels, resulting in missing features in the output.
- **Incorrect Method Invocation:** Attempting to call `.raptorJoinFeature(...)` directly on the `RasterRDD` instance may fail if the implicit conversions are not in scope; always prefer the explicit `RaptorJoin.raptorJoinFeature(...)` object method.

### Fix Code Hint
```scala
// Ensure the raster type matches the file (e.g., Int)
val raster: RasterRDD[Int] = sc.geoTiff[Int]("landcover.tif")
val features: RDD[IFeature] = sc.shapefile("zones.zip")

// Call the object method directly rather than relying on implicits
val joined: RDD[RaptorJoinFeature[Int]] = RaptorJoin.raptorJoinFeature(raster, features, new BeastOptions())
```

## API Test: `raptorJoinIDFull`

### Signature
```scala
def raptorJoinIDFull[T](raster: RDD[ITile[T]], vector: RDD[(Long, IFeature)], opts: BeastOptions, numTiles: LongAccumulator = null, numRanges: LongAccumulator = null) : RDD[RaptorJoinResult[T]]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorJoin.scala:180_

_Source doc:_ A Raptor join implementation that returns all the matches between features and pixels along with the raster metadata that puts the pixel in context. @param raster the RDD that contains the raster tiles @param vector the RDD that contains the vector features and their unique IDs @param opts additional options for the query processor @tparam T the type of the pixel values @return RDD that contains all overlaps between pixels and geometries

### Goal
Performs a distributed Raptor join between a raster dataset and a vector dataset, returning all pixel-geometry matches along with the pixel values, coordinates, and raster metadata for contextual analysis.

### Parameters
- `raster` (`RDD[ITile[T]]`): The RDD containing the raster tiles (e.g., loaded via `sc.geoTiff[T]` or instantiated as a `RasterFileRDD[T]`).
- `vector` (`RDD[(Long, IFeature)]`): The RDD containing the vector features paired with a unique `Long` identifier.
- `opts` (`BeastOptions`): Additional configuration options for the query processor (often just `new BeastOptions()`).
- `numTiles` (`LongAccumulator`), default `null`: An optional Spark accumulator to track the total number of raster tiles processed during the join.
- `numRanges` (`LongAccumulator`), default `null`: An optional Spark accumulator to track the total number of intersection ranges processed.

### Input
- **Raster Data:** Must be an `RDD[ITile[T]]`. The type parameter `T` must exactly match the file's runtime pixel type. Selection rules: `IntegerType` $\rightarrow$ `Int`, `FloatType` $\rightarrow$ `Float`, `ArrayType(IntegerType,true)` $\rightarrow$ `Array[Int]`, `ArrayType(FloatType, true)` $\rightarrow$ `Array[Float]`.
- **Vector Data:** Must be an `RDD[(Long, IFeature)]`. If you load vectors via `sc.shapefile` or similar (which returns `RDD[IFeature]`), you must map it to include a unique `Long` ID (e.g., using `zipWithIndex`).
- **Preconditions (Raptor Predicates):** The join matches geometries to pixels based on specific rules: Points match the single pixel containing them; Lines match pixels intersecting the line's crosshair; Polygons match pixels whose *center* falls inside the polygon boundary.

### Output
Returns `RDD[RaptorJoinResult[T]]` — an RDD representing all overlaps between pixels and geometries. Each `RaptorJoinResult` contains the pixel value (accessible via `.m`), the pixel coordinates (accessible via `.x` and `.y`), and the associated raster metadata.

### Valid Call Patterns
```scala
// Example 1: Single-band raster join
val raster: RasterFileRDD[Int] = new RasterFileRDD[Int](sparkContext, "glc2000_small.tif", new BeastOptions())
val features: RDD[IFeature] = sparkContext.parallelize(Seq(Feature.create(null, testPoly)))
val vector: RDD[(Long, IFeature)] = features.zipWithUniqueId().map(kv => (kv._2, kv._1))

val values: RDD[RaptorJoinResult[Int]] = RaptorJoin.raptorJoinIDFull(raster, vector, new BeastOptions())

// Example 2: Multiband raster join
val multiRaster: RasterFileRDD[Array[Int]] = new RasterFileRDD[Array[Int]](sparkContext, "FRClouds.tif", IRasterReader.OverrideSRID -> 4326)
val multiValues: RDD[RaptorJoinResult[Array[Int]]] = RaptorJoin.raptorJoinIDFull(multiRaster, vector, new BeastOptions())
```

### LLM Instruction Prompt
- Call `RaptorJoin.raptorJoinIDFull(raster, vector, opts)` as a method on the `RaptorJoin` object, not as an instance method on the raster RDD.
- Ensure the vector RDD is of type `RDD[(Long, IFeature)]`. If you have an `RDD[IFeature]`, you must assign unique IDs first (e.g., using `zipWithUniqueId()`).
- Ensure the generic type `T` matches the underlying raster data type exactly (e.g., `Int`, `Float`, `Array[Int]`, `Array[Float]`).

### Prompt Snippet
```text
When performing a full Raptor join to get pixel coordinates and metadata, use `RaptorJoin.raptorJoinIDFull(raster, vectorWithIds, new BeastOptions())`. The vector RDD must be mapped to `(Long, IFeature)` to provide unique IDs for the join.
```

### Common Failure Modes
- **Type Mismatch on Vector RDD:** Passing an `RDD[IFeature]` directly to `vector` will cause a compilation error. It must be `RDD[(Long, IFeature)]`.
- **Type Mismatch on Raster RDD:** Using `Int` for a float raster (or vice versa) will cause runtime casting exceptions. The type `T` must match the GeoTIFF/HDF pixel type.
- **Method Not Found:** Attempting to call `raster.raptorJoinIDFull(...)` directly on the RDD. While `raptorJoin` is available as an implicit extension, `raptorJoinIDFull` is typically called statically via the `RaptorJoin` object.

### Fix Code Hint
```scala
// WRONG: Passing RDD[IFeature] directly
// val join = RaptorJoin.raptorJoinIDFull(raster, features, new BeastOptions())

// RIGHT: Assign unique IDs to features first
val vectorWithIds: RDD[(Long, IFeature)] = features.zipWithUniqueId().map { case (f, id) => (id, f) }
val join = RaptorJoin.raptorJoinIDFull(raster, vectorWithIds, new BeastOptions())
```

## API Test: `rasterHeight`

### Signature
```scala
def rasterHeight: Int
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:52_

_Source doc:_ Total number of rows (scanlines) in the raster layer

### Goal
Retrieves the total number of pixel rows (scanlines) in the raster layer from its metadata.

### Parameters
_None._

### Input
A valid `RasterMetadata` instance, typically accessed via a raster reader (e.g., `GeoTiffReader[T].metadata`) after it has been initialized with a raster file (like a GeoTIFF or HDF).

### Output
Returns `Int` — the total vertical pixel dimension (number of rows) of the raster dataset.

### Valid Call Patterns
```scala
val rasterPath = new Path("/rasters/glc2000_small.tif")
val fileSystem = rasterPath.getFileSystem(new Configuration())
val reader = new GeoTiffReader[Int]
reader.initialize(fileSystem, rasterPath.toString, "0", new BeastOptions)

val height: Int = reader.metadata.rasterHeight
```

### LLM Instruction Prompt
- When you need the vertical pixel dimension (number of rows) of a raster, call `rasterHeight` on the `RasterMetadata` object. Do not confuse this with the spatial/geographic height (which requires calculating the difference between Y coordinates using the model envelope). Always access it via the `metadata` property of a reader or raster object.

### Prompt Snippet
```text
val rows: Int = reader.metadata.rasterHeight
```

### Common Failure Modes
- **Calling on the wrong object:** Attempting to call `rasterHeight` directly on a `GeoTiffReader` or `RasterRDD` instead of the `RasterMetadata` object.
- **Confusing pixel dimensions with spatial extent:** Assuming `rasterHeight` returns the geographic height in CRS units (e.g., degrees or meters) rather than the discrete integer count of pixel rows.

### Fix Code Hint
```scala
// WRONG: val h = reader.rasterHeight
// RIGHT: val h = reader.metadata.rasterHeight
```

## API Test: `rasterWidth`

### Signature
```scala
def rasterWidth: Int
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:49_

_Source doc:_ Total number of columns in the raster layer

### Goal
Retrieve the total number of pixel columns (the X-axis dimension) in a raster layer.

### Parameters
_None._

### Input
A valid `RasterMetadata` object, typically accessed via a `GeoTiffReader` instance after it has been initialized with a raster file (e.g., GeoTIFF or HDF).

### Output
Returns `Int` — the total number of columns (pixels) across the entire raster dataset.

### Valid Call Patterns
```scala
// Example derived from the project's test suite
val rasterPath = new Path("path/to/raster.tif")
val fileSystem = rasterPath.getFileSystem(new Configuration())
val reader = new GeoTiffReader[Int] // Type must match runtime pixel type

try {
  reader.initialize(fileSystem, rasterPath.toString, "0", new BeastOptions)
  val width: Int = reader.metadata.rasterWidth
  println(s"Raster has $width columns.")
} finally {
  reader.close()
}
```

### LLM Instruction Prompt
- When asked to find the dimensions or number of columns of a raster, access `.rasterWidth` on a `RasterMetadata` object.
- Do not call `rasterWidth` directly on a `RasterRDD` or `SparkContext`; it is a property of the raster's metadata.
- Remember that `rasterWidth` represents the pixel count, not the geographic width in map units (CRS units). To find the geographic width, multiply `rasterWidth` by the pixel scale (e.g., `reader.metadata.getPixelScaleX`).

### Prompt Snippet
```text
To get the number of columns (pixels) in a raster layer, access `.rasterWidth` on its `RasterMetadata` object (e.g., `reader.metadata.rasterWidth`).
```

### Common Failure Modes
- **Calling on the wrong object:** Attempting to call `rasterWidth` directly on a `RasterRDD` instead of extracting or reading the `RasterMetadata` first.
- **Confusing pixels with map units:** Assuming `rasterWidth` returns the spatial extent (e.g., degrees or meters). It strictly returns the integer number of pixel columns.
- **Uninitialized Reader:** Calling `reader.metadata.rasterWidth` before calling `reader.initialize(...)`, resulting in a null reference or unpopulated metadata.

### Fix Code Hint
```scala
// ❌ WRONG: Calling directly on the RDD or reader
// val width = myRasterRdd.rasterWidth
// val width = reader.rasterWidth

// ✅ CORRECT: Accessing via the initialized reader's metadata
val width = reader.metadata.rasterWidth

// ✅ CORRECT: Calculating geographic width using metadata
val geoWidth = reader.metadata.rasterWidth * reader.metadata.getPixelScaleX
```

## API Test: `rasterizePixels`

### Signature
```scala
def rasterizePixels[T: ClassTag](pixels: RDD[(Int, Int, T)], metadata: RasterMetadata, rasterFeature: RasterFeature): RasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsGlobal.scala:35  (+1 more definition site/overload)_

_Source doc:_ Creates a [[RasterRDD]] from a given set of pixel locations and values. @param pixels the pixel values @param metadata the metadata that describes the raster @tparam T the type of pixels @return a raster RDD that holds the given pixels

### Goal
Creates a distributed `RasterRDD` from an RDD of individual pixel coordinates and values, aligning them into tiles based on the provided spatial metadata grid.

### Parameters
- `pixels` (`RDD[(Int, Int, T)]`): A Spark RDD containing tuples of `(x, y, value)`, where `x` is the column index, `y` is the row index, and `value` is the pixel data of type `T`.
- `metadata` (`RasterMetadata`): The spatial configuration defining the raster's grid, including total width/height, tile dimensions, CRS (SRID), and the affine transform mapping pixel coordinates to geographic space.
- `rasterFeature` (`RasterFeature`): Metadata attributes for the resulting raster dataset, typically containing identifying information like the target file name.

### Input
- **Data:** An RDD of sparse or dense pixel values. The type `T` must match the runtime pixel type (e.g., `Int` for integer data, `Float` for continuous data).
- **Preconditions:** 
  - The `x` and `y` coordinates in the `pixels` RDD must fall within the bounds defined by `metadata` (i.e., `0 <= x < rasterWidth` and `0 <= y < rasterHeight`).
  - The `metadata` must specify uniform tile sizes (e.g., 90x90 or 1000x1000). According to GeoTIFF standards, all tiles must be of the same width and height, even if the last tile extends outside the raster boundary (outside pixels are filled with a fill value).

### Output
Returns `RasterRDD[T]` — A distributed raster dataset (an alias for `RDD[ITile[T]]`) partitioned into tiles. This output is ready for further RDPro operations (like `mapPixels` or `raptorJoin`) or can be saved directly to disk as a GeoTIFF using `GeoTiffWriter.saveAsGeoTiff`.

### Valid Call Patterns
```scala
// Construct metadata (x1, y1, x2, y2, tileWidth, tileHeight, srid, affineTransform)
val metadata = new RasterMetadata(0, 0, 360, 180, 90, 90, 4326, 
  new AffineTransform(1, 0, 0, -1, -180, 90))

// Create an RDD of pixel coordinates and values
val pixels = sparkContext.parallelize(Seq(
  (0, 0, 100f),
  (180, 0, 200f),
  (100, 50, 300f)
))

// Rasterize using RasterOperationsGlobal
val rasterRDD: RasterRDD[Float] = RasterOperationsGlobal.rasterizePixels(
  pixels, 
  metadata, 
  RasterFeature.create(Array("fileName"), Array("testFile.tif"))
)
```

### LLM Instruction Prompt
- When generating code to rasterize pixels, always use the 3-parameter signature `RasterOperationsGlobal.rasterizePixels(pixels, metadata, rasterFeature)`.
- Do not use the 2-parameter `sc.rasterizePixels` shorthand if the environment strictly requires the `rasterFeature` argument.
- Create the `rasterFeature` argument using `RasterFeature.create(Array("fileName"), Array("your_filename.tif"))`.
- Ensure the type parameter `T` (e.g., `Float`, `Int`) exactly matches the type of the values in the `pixels` RDD.

### Prompt Snippet
```text
To convert an RDD of (x, y, value) tuples into a RasterRDD, use `RasterOperationsGlobal.rasterizePixels(pixels, metadata, rasterFeature)`. You must provide a `RasterMetadata` object defining the grid and tile sizes, and a `RasterFeature` created via `RasterFeature.create(Array("fileName"), Array("out.tif"))`. Ensure the generic type `T` matches your pixel data type.
```

### Common Failure Modes
- **Missing `rasterFeature` Argument:** Attempting to call `rasterizePixels(pixels, metadata)` based on outdated documentation, resulting in a compilation error due to the missing third parameter.
- **Type Mismatch:** Providing an RDD of `(Int, Int, Double)` but expecting a `RasterRDD[Float]`. RDPro strictly binds the generic type `T` to the underlying GeoTIFF tile types (e.g., `FloatType` -> `Float`).
- **Out-of-Bounds Pixels:** Providing pixel coordinates `(x, y)` that exceed the `rasterWidth` or `rasterHeight` defined in the `RasterMetadata`, which may cause out-of-bounds exceptions during tile assignment.

### Fix Code Hint
```scala
// FIX: Ensure all 3 parameters are passed and types match exactly
val metadata = RasterMetadata.create(-180, 90, 180, -90, 4326, 360, 180, 90, 90)
val feature = RasterFeature.create(Array("fileName"), Array("output.tif"))

// If pixels are Float, the RDD and the method type parameter must be Float
val pixels: RDD[(Int, Int, Float)] = sc.parallelize(Seq((0, 0, 1.5f)))
val raster = RasterOperationsGlobal.rasterizePixels[Float](pixels, metadata, feature)
```

## API Test: `rasterizePoints`

### Signature
```scala
def rasterizePoints[T: ClassTag](points: RDD[(Double, Double, T)], metadata: RasterMetadata, rasterFeature: RasterFeature): RasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsGlobal.scala:55  (+1 more definition site/overload)_

_Source doc:_ Creates a raster from a list of point locations and values. @param points point locations and raster values @param metadata the metadata that describes the raster location @tparam T the type of raster values @return a raster that contains the given point locations

### Goal
Converts a distributed collection of spatial point coordinates and their associated values into a distributed raster dataset (`RasterRDD`) based on a defined spatial grid.

### Parameters
- `points` (`RDD[(Double, Double, T)]`): An RDD of tuples representing the point locations and their raster values. The tuple format is `(X/Longitude, Y/Latitude, Value)`.
- `metadata` (`RasterMetadata`): The metadata that describes the target raster's spatial extent (bounds), coordinate reference system (SRID), overall resolution (width/height), and tile dimensions.
- `rasterFeature` (`RasterFeature`): Additional raster feature attributes. In practice (as seen in the test suite), this is often passed as `null` when calling the global operation directly.

### Input
- **Data:** An initialized Spark `RDD` containing coordinate-value tuples.
- **Preconditions:** 
  - A valid `RasterMetadata` object must be created first (e.g., via `RasterMetadata.create(...)`) to define the grid into which the points will be rasterized.
  - The type parameter `T` must match the runtime pixel type you intend to use (e.g., `Int` or `Float`).
  - The coordinates in the `points` RDD should fall within the spatial bounds defined by the `metadata`.

### Output
Returns `RasterRDD[T]` — a distributed raster dataset containing the given point locations mapped to pixels within the specified grid tiles.

### Valid Call Patterns
```scala
// Pattern 1: Explicit call using RasterOperationsGlobal (Authoritative from test suite)
val metadata = RasterMetadata.create(0, 0, 6, 4, 4326, 60, 40, 60, 40)
val pixels = sparkContext.parallelize(Seq(
  (2.20, 1.7, 100),
  (2.7, 2.0, 50),
  (5.3, 2.2, 25)
))
val raster: RasterRDD[Int] = RasterOperationsGlobal.rasterizePoints(pixels, metadata, null)

// Pattern 2: Implicit SparkContext extension (Most portable, from README)
val metadata2 = RasterMetadata.create(x1 = -50, y1 = 40, x2 = -60, y2 = 30, srid = 4326,
  rasterWidth = 10, rasterHeight = 10, tileWidth = 10, tileHeight = 10)
val pixels2 = sc.parallelize(Seq(
  (-51.3, 30.4, 100),
  (-55.2, 34.5, 200),
  (-56.4, 39.2, 300)
))
val raster2 = sc.rasterizePoints(pixels2, metadata2)
```

### LLM Instruction Prompt
- When converting point data to a raster, use `sc.rasterizePoints(pixels, metadata)` if relying on SparkContext implicits, or `RasterOperationsGlobal.rasterizePoints(pixels, metadata, null)` if calling the object directly.
- Always construct a `RasterMetadata` object first to define the target grid's bounds, SRID, and tile sizes.
- Ensure the type parameter `T` (e.g., `Int`, `Float`) matches the value type in the `RDD[(Double, Double, T)]`.

### Prompt Snippet
```text
Create a RasterMetadata object for SRID 4326 with bounds (-124, 42) to (-114, 32) and tile size 100x100. Then, given an RDD of (Double, Double, Float) named `pointData`, rasterize it into a RasterRDD[Float] using the explicit RasterOperationsGlobal call.
```

### Common Failure Modes
- **Missing Arguments in Explicit Call:** Calling `RasterOperationsGlobal.rasterizePoints(pixels, metadata)` without the third `rasterFeature` argument (which should be `null` if unavailable) will cause a compilation error.
- **Type Mismatch:** Providing an `RDD[(Double, Double, Double)]` but expecting a `RasterRDD[Float]` or `RasterRDD[Int]`. The type `T` must be consistent and align with supported GeoTIFF pixel types if you intend to save the output.
- **Out of Bounds:** Points in the RDD that fall outside the spatial envelope defined in `RasterMetadata` will not be rasterized into the resulting tiles.

### Fix Code Hint
```scala
// BAD: Missing the third argument for the explicit global call
val raster = RasterOperationsGlobal.rasterizePoints(pixels, metadata)

// GOOD: Pass null for rasterFeature if not using the implicit sc.rasterizePoints
val raster = RasterOperationsGlobal.rasterizePoints(pixels, metadata, null)

// GOOD: Use the implicit extension on SparkContext
val raster = sc.rasterizePoints(pixels, metadata)
```

## API Test: `readCSVPoint`

### Signature
```scala
def readCSVPoint(filename: String, xColumn: Any = 0, yColumn: Any = 1, delimiter: Char = ',', skipHeader: Boolean = false): SpatialRDD
def readCSVPoint(filename: String, xColumn: String, yColumn: String, delimiter: Char, skipHeader: Boolean): JavaSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:97  (+1 more definition site/overload)_

_Source doc:_ Reads points from a CSV file given the names of the columns that contain the x and y coordinates @param filename the name of the file or directory that contains the data @param xColumn the name of the column that contains the x coordinate @param yColumn the name of the column that contains the y coordinate @param delimiter the field delimiter, comma by default @param skipHeader whether to skip the header line or not. If either xColumn or yColumn is String, this option will be ignored a header line will be assumed. Otherwise, it is false by default @return the set of records in the file

### Goal
Reads point geometries from a CSV file into a distributed `SpatialRDD` by specifying the columns containing the X (longitude) and Y (latitude) coordinates.

### Parameters
- `filename` (`String`): The path to the CSV file or directory containing the data.
- `xColumn` (`Any`), default `0`: The index (`Int`) or name (`String`) of the column containing the X coordinate.
- `yColumn` (`Any`), default `1`: The index (`Int`) or name (`String`) of the column containing the Y coordinate.
- `delimiter` (`Char`), default `','`: The character used to separate fields in the CSV file.
- `'`: A parsing artifact from the source code's default comma character; ignore this parameter.
- `skipHeader` (`Boolean`), default `false`: Whether to skip the first line. If `xColumn` or `yColumn` is provided as a `String`, this option is ignored and a header line is automatically assumed.

### Input
A CSV file (or directory of CSVs) containing point data. The caller must have an initialized `SparkContext` (e.g., `sparkContext` or `sc`) because this function is provided as a Context Extension. If using column names instead of indices, the CSV must have a header row.

### Output
Returns `SpatialRDD` — a distributed Spark RDD of spatial features (`IFeature`) representing the points parsed from the CSV file.

### Valid Call Patterns
```scala
// Using default column indices (0 for X, 1 for Y)
val data: SpatialRDD = sparkContext.readCSVPoint(testFile.getPath)

// Using explicit column names (automatically assumes a header exists)
val dataNamed: SpatialRDD = sparkContext.readCSVPoint("points.csv", "longitude", "latitude")

// Using explicit integer indices and skipping the header
val dataIndexed: SpatialRDD = sparkContext.readCSVPoint("points.csv", 2, 3, ',', skipHeader = true)
```

### LLM Instruction Prompt
- Always call `readCSVPoint` as an extension method on an initialized `SparkContext` (e.g., `sc.readCSVPoint(...)`).
- If passing `xColumn` or `yColumn` as `String` names, do not worry about setting `skipHeader` to `true`, as Beast will automatically assume a header exists.
- If passing `xColumn` or `yColumn` as `Int` indices for a file that *does* have a header, you must explicitly set `skipHeader = true`.
- Never invent file paths; use only the provided input variables.

### Prompt Snippet
```text
Use `sc.readCSVPoint(filename, xColumn, yColumn)` to load CSV point data into a SpatialRDD. Pass column indices (Int) or names (String). If using indices on a file with a header, set `skipHeader = true`.
```

### Common Failure Modes
- **Header Parsing Errors:** Using integer indices for `xColumn` and `yColumn` on a CSV that has a header row, but forgetting to set `skipHeader = true`. This causes Beast to attempt to parse the string header names as numeric coordinates.
- **Missing SparkContext:** Attempting to call `readCSVPoint(...)` as a standalone function rather than a method on `SparkContext` (e.g., `sc.readCSVPoint(...)`).
- **Column Not Found:** Providing a `String` column name that does not exactly match the header in the CSV file, or an `Int` index that is out of bounds for the row length.

### Fix Code Hint
```scala
// If parsing fails due to a header row when using integer indices, explicitly skip the header:
val points = sc.readCSVPoint(filename, xColumn = 0, yColumn = 1, skipHeader = true)

// If using column names, skipHeader is handled automatically:
val points = sc.readCSVPoint(filename, xColumn = "lon", yColumn = "lat")
```

## API Test: `readConfigurationXML`

### Signature
```scala
def readConfigurationXML(filename: String): java.util.Map[String, java.util.List[String]]
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/util/OperationHelper.scala:60_

_Source doc:_ Read all XML configuration files of the given name in the class path and merge them into one object. This method internally caches the configuration so it does not have to be loaded multiple times. The XML is organized in three levels. The first level is the root element and it is always &lt;beast&gt;. The second level is a name of a collection, e.g., &lt;Indexers&gt;. Finally, the third level contains the contents of the collection in their text part. @param filename A path to an XML file that contains the configuration. @return the beast configuration as a map from each key to all values under this key.

### Goal
Reads, merges, and caches XML configuration files from the classpath into a map, organizing Beast configuration properties by their collection names.

### Parameters
- `filename` (`String`): The name or path of the XML configuration file to locate within the classpath (e.g., `"test-beast.xml"`).

### Input
An XML file present in the Java classpath. The XML must strictly follow a three-level hierarchy:
1. The root element must be `<beast>`.
2. The second level defines the collection name (e.g., `<Indexers>`, `<Operations>`), which becomes the map key.
3. The third level contains the actual configuration values in their text part, which populate the list for that key.

### Output
Returns `java.util.Map[String, java.util.List[String]]` — A Java Map where each key is a collection name (from the second-level XML tags) and the value is a Java List of strings representing the text contents of the third-level elements under that key.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast.util.OperationHelper
import java.util

// Read configuration from the classpath
val conf: util.Map[String, util.List[String]] = OperationHelper.readConfigurationXML("test-beast.xml")

// Access values using standard Java Map/List methods
val operations: util.List[String] = conf.get("Operations")
val firstOp: String = operations.get(0)
```

### LLM Instruction Prompt
- Use `OperationHelper.readConfigurationXML(filename)` to load Beast XML configurations from the classpath.
- Remember that the return type is a `java.util.Map` containing `java.util.List` values, not Scala collections. You must use Java collection methods (e.g., `.get()`, `.size()`) or explicitly convert them using Scala's Java converters if idiomatic Scala operations are required.
- Do not invent configuration file paths; use the exact filename expected in the classpath.

### Prompt Snippet
```text
To load Beast XML configurations, use `OperationHelper.readConfigurationXML("filename.xml")`. It parses a 3-level XML (`<beast>` -> `<Collection>` -> `<Item>value</Item>`) and returns a `java.util.Map[String, java.util.List[String]]`. Use Java collection methods to access the keys.
```

### Common Failure Modes
- **NullPointerException on Missing Keys:** Because the method returns a `java.util.Map`, calling `.get("NonExistentKey")` returns `null` rather than a Scala `Option`. Attempting to call `.size()` or `.get(0)` on the result will throw an NPE.
- **Malformed XML Structure:** If the XML does not have `<beast>` as the root element or lacks the required three-level depth, the configuration will not parse correctly into the expected Map/List structure.
- **File Not in Classpath:** Providing a local filesystem path instead of a classpath-relative filename will result in the file not being found, as the method specifically searches the classpath.

### Fix Code Hint
```scala
// WRONG: Using Scala map methods or assuming the key always exists
val conf = OperationHelper.readConfigurationXML("beast.xml")
val ops = conf.getOrElse("Operations", List()) // Fails: java.util.Map has no getOrElse

// RIGHT: Handling the Java Map safely
val conf: java.util.Map[String, java.util.List[String]] = OperationHelper.readConfigurationXML("beast.xml")
val opsList = conf.get("Operations")
if (opsList != null && opsList.size() > 0) {
  val firstOp = opsList.get(0)
  println(s"First operation: $firstOp")
}
```

## API Test: `readInput`

### Signature
```scala
def readInput(sc: JavaSparkContext, opts: BeastOptions, filename: String, iFormat: String): JavaSpatialRDD
def readInput(sc: SparkContext, opts: BeastOptions, filename: String, iFormat: String) : SpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialReader.scala:205  (+1 more definition site/overload)_

_Source doc:_ Java shortcut

### Goal
Loads spatial vector data from a specified file or directory into a distributed Spark RDD, supporting various formats like shapefile, GeoJSON, and CSV.

### Parameters
- `sc` (`JavaSparkContext` or `SparkContext`): The active Spark context used to distribute the data loading.
- `opts` (`BeastOptions`): Configuration options for the reader (e.g., CSV parsing options). Can be empty (`new BeastOptions()`).
- `filename` (`String`): The path to the input file or directory (e.g., `"input.zip"`, `"Tweets.geojson.gz"`).
- `iFormat` (`String`): The string identifier for the input format (e.g., `"shapefile"`, `"geojson"`, `"csv"`).

### Input
Vector data files accessible to the Spark cluster. Supported input formats include CSV (points, WKT, envelopes), Esri Shapefile (compressed `.zip` or uncompressed), GeoJSON, JSON+WKT, and GPX. 
*Precondition:* This function is strictly for vector data. Raster data (GeoTIFF, HDF) must be loaded using raster-specific APIs like `sc.geoTiff[T]` or `new RasterFileRDD`.

### Output
Returns `JavaSpatialRDD` (or `SpatialRDD` for the Scala overload) — representing a distributed collection of spatial features (`IFeature`), which contain both geometries and their associated attributes.

### Valid Call Patterns
```scala
// Scala usage (from test suite)
val vectorFile = locateResource("/vectors/ne_110m_admin_1_states_provinces.zip")
val polygons: RDD[IFeature] = SpatialReader.readInput(sparkContext, new BeastOptions(), vectorFile.getPath, "shapefile")

// Java usage (from README)
JavaRDD<IFeature> points = SpatialReader.readInput(sparkContext, new BeastOptions(), "Tweets.geojson.gz", "geojson");
```

### LLM Instruction Prompt
- Use `SpatialReader.readInput` to load vector datasets when an explicit format string is required or when writing Java code.
- Always provide an instantiated `BeastOptions` object (e.g., `new BeastOptions()`) as the second argument.
- Ensure the `iFormat` string exactly matches the intended vector format (e.g., `"shapefile"`, `"geojson"`).
- Do NOT use `readInput` for raster files (GeoTIFF/HDF); use `sc.geoTiff[T]` instead.
- Do not invent file paths; use only provided input variables.

### Prompt Snippet
```text
To load vector data explicitly by format, use `SpatialReader.readInput(sc, new BeastOptions(), path, format)`. Valid formats include "shapefile", "geojson", and "csv". Do not use this for rasters.
```

### Common Failure Modes
- **Passing Raster Files:** Attempting to load a GeoTIFF or HDF file using `readInput`. This will fail because `readInput` expects vector formats. Rasters require `sc.geoTiff[T]`.
- **Missing `BeastOptions`:** Forgetting the `opts` parameter. The signature strictly requires a `BeastOptions` instance, even if no custom options are needed.
- **Mismatched Format String:** Providing an `iFormat` string that does not match the actual file contents (e.g., passing `"csv"` for a `.geojson` file).
- **CSV Geometry Auto-detection Failure:** When loading CSVs, geometry column auto-detection is a "best-effort" guess. If it fails, the resulting features may lack valid geometries unless explicitly configured in `BeastOptions`.

### Fix Code Hint
```scala
// ❌ BAD: Missing BeastOptions and using readInput for a raster
val raster = SpatialReader.readInput(sc, "image.tif", "geotiff")

// ✅ GOOD: Using readInput correctly for vectors with BeastOptions
val polygons: RDD[IFeature] = SpatialReader.readInput(sc, new BeastOptions(), "input.zip", "shapefile")

// ✅ GOOD: Using the correct API for rasters
val raster: RDD[ITile[Int]] = sc.geoTiff[Int]("image.tif")
```

## API Test: `readLocal`

### Signature
```scala
def readLocal(path: String, iformat: String, opts: BeastOptions, conf: Configuration): Iterator[IFeature]
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialFileRDD.scala:492_

_Source doc:_ Reads the given path locally without creating any RDDs. Useful for reading a small file when SparkContext is not accessible, e.g., inside a mapPartition function. @param path path to a single file or a directory @param iformat the format of the data @param opts additional options for reading the file @return an iterator to features in the given path

### Goal
Reads spatial vector data from a local file or directory directly into a local Scala iterator without creating a Spark RDD, which is ideal for loading small auxiliary datasets inside distributed operations (like `mapPartitions`).

### Parameters
- `path` (`String`): The path to a single file or a directory containing the spatial data to be read.
- `iformat` (`String`): The format identifier of the data (e.g., `"wkt(1)"`, `"shapefile"`, `"geojson"`).
- `opts` (`BeastOptions`): Additional configuration options for reading the file (e.g., skipping headers or setting separators). Can often be passed as a `Seq` of key-value pairs via implicit conversion.
- `conf` (`Configuration`): The Hadoop `Configuration` object, typically obtained via `sparkContext.hadoopConfiguration`.

### Input
A local file path or directory containing supported vector data (such as CSV, Shapefile, or GeoJSON). 
**Preconditions:** 
- The file must be physically accessible on the node executing the code. If `readLocal` is called inside a Spark task (e.g., `mapPartitions`), the file must exist on that specific worker node's local filesystem, or be accessible via a shared mount/HDFS path that the worker can resolve locally.
- The `iformat` string must correctly match the underlying data format.

### Output
Returns `Iterator[IFeature]` — a local, non-distributed Scala iterator over the spatial features parsed from the specified path.

### Valid Call Patterns
```scala
// From the project's test suite (using implicit Seq to BeastOptions conversion)
val input = new File(scratchDir, "inputdir")
val features = SpatialFileRDD.readLocal(
  input.getPath, 
  "wkt(1)",
  Seq(CSVFeatureReader.SkipHeader -> true, CSVFeatureReader.FieldSeparator -> '\t'), 
  sparkContext.hadoopConfiguration
)
```

### LLM Instruction Prompt
- Use `SpatialFileRDD.readLocal` ONLY when you need to read a small spatial file directly into local memory (e.g., inside a `mapPartitions` block where `SparkContext` is unavailable).
- Do not use `readLocal` for large datasets; use SparkContext extensions like `sc.shapefile` or `sc.geojsonFile` to leverage distributed partitioning.
- Always pass `sparkContext.hadoopConfiguration` for the `conf` parameter if executing on the driver.
- Ensure the `iformat` string accurately reflects the geometry column index or format (e.g., `"wkt(1)"` for WKT in the second column).

### Prompt Snippet
```text
`SpatialFileRDD.readLocal(path, iformat, opts, conf)` reads a spatial file directly into an `Iterator[IFeature]` without creating an RDD. Use this for loading small auxiliary files inside `mapPartitions` where `SparkContext` is inaccessible. Requires a Hadoop `Configuration` (e.g., `sc.hadoopConfiguration`).
```

### Common Failure Modes
- **FileNotFoundException on Workers:** Calling `readLocal` inside a distributed Spark transformation with a local file path (e.g., `C:\data\file.csv`) that only exists on the driver machine, causing worker nodes to fail when they attempt to resolve the path.
- **Memory Exhaustion (OOM):** Attempting to read a massive vector dataset using `readLocal` and converting the resulting `Iterator` to a `List` or `Array`, bypassing Spark's distributed memory management and crashing the JVM.
- **Format Parsing Errors:** Providing an incorrect `iformat` (like `"csv"` instead of `"wkt(1)"`) or failing to provide necessary `BeastOptions` (like `CSVFeatureReader.SkipHeader -> true`), causing the parser to fail on the header row or misinterpret geometry columns.

### Fix Code Hint
```scala
// ❌ BAD: Using readLocal for a large dataset on the driver, losing distributed processing
val largeDataIter = SpatialFileRDD.readLocal("hdfs:///large_polygons.shp", "shapefile", new BeastOptions(), sc.hadoopConfiguration)
val largeDataRDD = sc.parallelize(largeDataIter.toSeq) // OOM risk!

// ✅ GOOD: Use SparkContext extensions for large distributed loads
val largeDataRDD = sc.shapefile("hdfs:///large_polygons.shp")

// ✅ GOOD: Using readLocal inside mapPartitions for a small, locally distributed file
val joined = largeDataRDD.mapPartitions { partition =>
  // Assuming "small_reference.csv" was distributed to workers via SparkFiles
  val localRef = SpatialFileRDD.readLocal(SparkFiles.get("small_reference.csv"), "wkt(0)", new BeastOptions(), new Configuration()).toList
  // ... perform local operations ...
}
```

## API Test: `readPartition`

### Signature
```scala
def readPartition(partition: FilePartition, featureReaderClass: Class[_ <: FeatureReader], applyDuplicateAvoidance: Boolean, opts: BeastOptions): Iterator[IFeature]
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialFileRDD.scala:441_

_Source doc:_ Reads the given partition @param partition the partition to read @param featureReaderClass the class of the feature reader @param opts the user options @return an iterator to the features

### Goal
Reads a specific file partition of spatial data using a designated feature reader and returns an iterator of spatial features, acting as the internal plumbing for distributed vector data loading in Beast.

### Parameters
- `partition` (`FilePartition`): The specific chunk or partition of the file to read, typically generated by `SpatialFileRDD.createPartitions`.
- `featureReaderClass` (`Class[_ <: FeatureReader],
                    applyDuplicateAvoidance: Boolean, opts: BeastOptions`): This parameter block encompasses three arguments from the signature:
  1. `featureReaderClass`: The class of the reader responsible for parsing the specific file format (e.g., GeoJSON, Shapefile), usually obtained via `SpatialFileRDD.getFeatureReaderClass`.
  2. `applyDuplicateAvoidance`: A boolean flag indicating whether to filter out duplicate features that might span across multiple non-disjoint partitions.
  3. `opts`: The `BeastOptions` containing user configurations, such as the input format.

### Input
The caller must provide a valid `FilePartition` pointing to a supported vector data file (e.g., CSV, Esri Shapefile, GeoJSON, JSON+WKT). The `featureReaderClass` must exactly match the format of the data being read. The `opts` must be configured with the correct format (e.g., `SpatialFileRDD.InputFormat -> "geojson"`). 

### Output
Returns `Iterator[IFeature]` — an iterator over the spatial features (geometries and their associated attributes) contained within the specified file partition.

### Valid Call Patterns
```scala
val inputFile = makeFileCopy("/allfeatures.geojson")
val opts: BeastOptions = SpatialFileRDD.InputFormat -> "geojson"
val featureReaderClass = SpatialFileRDD.getFeatureReaderClass(inputFile.getPath, opts)
val partitions = SpatialFileRDD.createPartitions(inputFile.getPath, opts, sparkContext.hadoopConfiguration)

var featureCount: Int = 0
for (partition <- partitions) {
  val features = SpatialFileRDD.readPartition(partition, featureReaderClass, true, opts)
  featureCount += features.length
}
```

### LLM Instruction Prompt
- Call `readPartition` as a method on the `SpatialFileRDD` object.
- Do not call this method in standard high-level Spark pipelines; prefer context extensions like `sc.shapefile` or `sc.geojsonFile` unless you are explicitly writing custom partition iteration logic.
- Always derive the `featureReaderClass` dynamically using `SpatialFileRDD.getFeatureReaderClass(path, opts)` rather than hardcoding a reader class.
- Set `applyDuplicateAvoidance` to `true` if the partitions are not strictly disjoint to prevent double-counting features that intersect partition boundaries.

### Prompt Snippet
```text
When manually iterating over spatial file partitions in Beast, use `SpatialFileRDD.readPartition(partition, readerClass, applyDuplicateAvoidance, opts)`. Ensure you first generate the partitions using `SpatialFileRDD.createPartitions` and obtain the correct reader class via `SpatialFileRDD.getFeatureReaderClass`.
```

### Common Failure Modes
- **Mismatched Reader Class:** Passing a `featureReaderClass` that does not match the actual file format (e.g., using a Shapefile reader for a GeoJSON partition), resulting in parsing errors.
- **Missing Input Format Option:** Failing to set `SpatialFileRDD.InputFormat` in the `BeastOptions`, causing the system to fail to resolve the correct `featureReaderClass`.
- **Duplicate Features:** Setting `applyDuplicateAvoidance` to `false` when reading from non-disjoint partitions, which can cause features spanning multiple partitions to be yielded multiple times.

### Fix Code Hint
```scala
// Ensure options and reader class are correctly initialized before reading
val opts = new BeastOptions().set(SpatialFileRDD.InputFormat, "geojson")
val readerClass = SpatialFileRDD.getFeatureReaderClass(filePath, opts)
val partitions = SpatialFileRDD.createPartitions(filePath, opts, sc.hadoopConfiguration)

// Read the first partition safely with duplicate avoidance enabled
val firstPartitionFeatures = SpatialFileRDD.readPartition(partitions(0), readerClass, true, opts)
```

## API Test: `readTile`

### Signature
```scala
def readTile(tileID: Int): ITile[T]
def readTile(tileID: Int): ITile[Float]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/GeoTiffReader.scala:167  (+2 more definition site/overload)_

### Goal
Reads a specific tile from an initialized raster file (such as a GeoTIFF) into memory, returning an independent tile object that supports concurrent access and remains valid even after the reader is closed.

### Parameters
- `tileID` (`Int`): The integer identifier of the tile to read. This should not be guessed; it is typically obtained by querying the reader's metadata (e.g., `reader.metadata.getTileIDAtPixel(x, y)` or `reader.metadata.getTileIDAtPoint(x, y)`).

### Input
Requires an instantiated and initialized raster reader (e.g., `GeoTiffReader[T]`). The reader must have been initialized against a valid raster file (like a GeoTIFF) using a Hadoop `FileSystem` and `Path`. 

**Type-Parameter Selection Rule:** The type parameter `T` of the reader (and thus the returned `ITile[T]`) must exactly match the file's runtime pixel type:
*   `IntegerType` $\rightarrow$ `GeoTiffReader[Int]`
*   `FloatType` $\rightarrow$ `GeoTiffReader[Float]`
*   `ArrayType(IntegerType,true)` $\rightarrow$ `GeoTiffReader[Array[Int]]`
*   `ArrayType(FloatType, true)` $\rightarrow$ `GeoTiffReader[Array[Float]]`

### Output
Returns `ITile[T]` — an object containing the pixel data and spatial information for the requested tile. The returned tile is independent and stays valid even after the raster reader is closed.

### Valid Call Patterns
```scala
// Pattern 1: Reading a tile using pixel coordinates
val tileID = reader.metadata.getTileIDAtPixel(37, 24)
val tile = reader.readTile(tileID)

// Pattern 2: Reading a tile using spatial (model) coordinates
val spatialTileID = reader.metadata.getTileIDAtPoint(23.224, 32.415)
val spatialTile = reader.readTile(spatialTileID)
```

### LLM Instruction Prompt
- Always obtain the `tileID` dynamically from the reader's `metadata` (using `getTileIDAtPixel` or `getTileIDAtPoint`) rather than hardcoding or inventing integer IDs.
- Ensure the `GeoTiffReader[T]` type parameter exactly matches the underlying raster's pixel type, or `readTile` will fail or return corrupted data.
- Wrap reader usage in a `try...finally` block to ensure `reader.close()` is called, noting that the `ITile[T]` returned by `readTile` safely outlives the reader.

### Prompt Snippet
```text
To read a specific tile from a raster, initialize a `GeoTiffReader[T]` where `T` matches the exact pixel type (e.g., `Int`, `Float`). Query `reader.metadata.getTileIDAtPoint(x, y)` or `getTileIDAtPixel(x, y)` to get the correct `tileID`, then call `reader.readTile(tileID)`. Close the reader in a `finally` block; the returned `ITile[T]` remains valid.
```

### Common Failure Modes
- **Type Mismatch:** Initializing `GeoTiffReader[T]` with the wrong type parameter (e.g., using `Int` for a float raster) will cause failures when `readTile` attempts to parse the underlying bytes.
- **Invalid Tile ID:** Passing an arbitrary or out-of-bounds integer instead of querying the metadata for a valid tile ID.
- **Uninitialized Reader:** Calling `readTile` before calling `reader.initialize(...)` with the file system and path.

### Fix Code Hint
```scala
val reader = new GeoTiffReader[Int]
try {
  reader.initialize(fileSystem, rasterPath.toString, "0", new BeastOptions())
  // Correctly obtain the tile ID from metadata before reading
  val tileID = reader.metadata.getTileIDAtPoint(23.224, 32.415)
  val tile: ITile[Int] = reader.readTile(tileID)
  
  // tile can now be used (e.g., tile.getPointValue(23.224, 32.415))
} finally {
  reader.close()
}
```

## API Test: `readWKTFile`

### Signature
```scala
def readWKTFile(filename: String, wktColumn: Any, delimiter: Char = '\t', skipHeader: Boolean = false): SpatialRDD
def readWKTFile(filename: String, wktColumn: String, delimiter: Char, skipHeader: Boolean): JavaSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:118  (+1 more definition site/overload)_

_Source doc:_ Read a CSV file with WKT-encoded geometry @param filename the name of the file or directory fo the input @param wktColumn the column that includes the WKT-encoded geometry, either an Integer for the index of the attribute or String for its name @param delimiter the field delimiter, tab by default @param skipHeader whether to skip the header line or not, if wktColumn is a string, this has to be true, if wktColumn is an Integer, this is false by default but can be overloaded @return the set of features in the input file

### Goal
Reads a delimited text file (such as CSV or TSV) containing Well-Known Text (WKT) geometries into a distributed `SpatialRDD` of vector features.

### Parameters
- `filename` (`String`): The path to the input file or directory containing the WKT data.
- `wktColumn` (`Any`): The column containing the WKT-encoded geometry. This can be an `Integer` representing the 0-based index of the column, or a `String` representing the column's name.
- `delimiter` (`Char`), default `'\t'`: The character used to separate fields in the file (defaults to a tab character).
- `skipHeader` (`Boolean`), default `false`: Whether to skip the first line of the file. **Precondition:** If `wktColumn` is provided as a `String`, this parameter *must* be set to `true`.

### Input
A delimited text file (e.g., CSV, TSV) containing WKT-encoded geometries. The caller must have an initialized `SparkContext` (typically `sc` or `sparkContext`) with Beast context extensions loaded.

### Output
Returns `SpatialRDD` — a distributed Spark RDD of spatial features (`RDD[IFeature]`) parsed from the input file, ready for spatial partitioning, joins, or Raptor raster-vector operations.

### Valid Call Patterns
```scala
// Using an integer column index (0-based) with default tab delimiter
val data: RDD[IFeature] = sparkContext.readWKTFile(testFile.getPath, 0)

// Using a string column name with a comma delimiter (requires skipHeader = true)
val data: RDD[IFeature] = sc.readWKTFile("data.csv", "geometry", ',', true)
```

### LLM Instruction Prompt
- Call `sc.readWKTFile(filename, wktColumn)` to load WKT geometries from delimited text files.
- **CRITICAL:** If `wktColumn` is a `String` (column name), you MUST explicitly set `skipHeader = true`.
- If the file is a standard CSV, you MUST override the default tab delimiter by passing `delimiter = ','`.
- The receiver is always the SparkContext (`sc` or `sparkContext`).

### Prompt Snippet
```text
When loading WKT files using `sc.readWKTFile`, remember that the default delimiter is a tab ('\t'). If reading a CSV, pass `','` as the third argument. If specifying the WKT column by name (String) instead of index (Integer), you must set the fourth argument `skipHeader` to `true`.
```

### Common Failure Modes
- **Header Parsing Error:** Passing a `String` for `wktColumn` but leaving `skipHeader` as `false` (the default). Beast requires the header to be skipped to resolve the column name correctly.
- **Delimiter Mismatch:** Calling `sc.readWKTFile("file.csv", 0)` on a comma-separated file without specifying `delimiter = ','`. The parser will default to tab-separated and fail to extract the geometry.

### Fix Code Hint
```scala
// BAD: String column name without skipHeader=true, and missing comma delimiter for CSV
val badData = sc.readWKTFile("polygons.csv", "wkt_geom")

// GOOD: Explicitly providing the delimiter and setting skipHeader to true
val goodData = sc.readWKTFile("polygons.csv", "wkt_geom", ',', true)
```

## API Test: `reproject`

### Signature
```scala
def reproject(targetSRID: Int)
def reproject(targetCRS: CoordinateReferenceSystem, unifiedRaster: Boolean = false, interpolationMethod: InterpolationMethod.InterpolationMethod = InterpolationMethod.NearestNeighbor)
def reproject[T: ClassTag](raster: RasterRDD[T], targetCRS: CoordinateReferenceSystem, unifiedRaster: Boolean = false, interpolationMethod: InterpolationMethod.InterpolationMethod = InterpolationMethod.NearestNeighbor): RasterRDD[T]
def reproject(sourceCRS: CoordinateReferenceSystem, targetCRS: CoordinateReferenceSystem): SpatialRDD
def reproject(targetCRS: CoordinateReferenceSystem): SpatialRDD
def reproject(targetSRID: Int): SpatialRDD
def reproject(targetCRS: CoordinateReferenceSystem): RasterMetadata
def reproject(metadata: Array[RasterMetadata], targetCRS: CoordinateReferenceSystem): RasterMetadata
def reproject(rdd: JavaSpatialRDD, targetCRS: CoordinateReferenceSystem): JavaSpatialRDD
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:517  (+8 more definition site/overload)_

_Source doc:_ Reproject a raster to a target coordinate reference system. This method uses the same resolution (number of pixels) of the first tile in the source raster. You can use the other [[reshapeAverage()]] method that takes [[RasterMetadata]] to change all the information. @param raster the raster layer to reproject @param targetCRS the target coordinate reference system @param unifiedRaster if set to true, all output tiles will belong to a single RasterMetadata @param interpolationMethod how to handle a target pixel that overlaps multiple source pixels @tparam T the type of the pixels @return

### Goal
Reproject a distributed raster dataset (`RasterRDD`), vector dataset (`SpatialRDD`), or `RasterMetadata` to a new target Coordinate Reference System (CRS) while maintaining the original pixel resolution.

### Parameters
- `raster` (`RasterRDD[T]`): The source raster layer to reproject. Often passed implicitly when calling `.reproject(...)` directly on a `RasterRDD`.
- `targetCRS` (`CoordinateReferenceSystem`): The target coordinate reference system (e.g., `CRS.decode("EPSG:4326")`). Overloads also allow passing an integer `targetSRID` directly.
- `unifiedRaster` (`Boolean`), default `false`: If set to `true`, all output tiles will belong to a single unified `RasterMetadata` grid.
- `interpolationMethod` (`InterpolationMethod.InterpolationMethod`), default `InterpolationMethod.NearestNeighbor`: Determines how to handle a target pixel that overlaps multiple source pixels. Use `InterpolationMethod.Average` for continuous numerical data and `NearestNeighbor` for categorical data.

### Input
A `RasterRDD[T]` loaded from a GeoTIFF or HDF file (e.g., via `sc.geoTiff[T]` or `sc.hdfFile`), or a `RasterMetadata` object. The type parameter `T` must exactly match the file's runtime pixel type (e.g., `Float` for `FloatType`, `Int` for `IntegerType`). 

### Output
Returns `RasterRDD[T]` — A new distributed raster dataset with pixels transformed to the target CRS, ready for saving (e.g., `saveAsGeoTiff`), overlaying, or further pixel math. (Overloads return `SpatialRDD` or `RasterMetadata` depending on the input).

### Valid Call Patterns
```scala
// Reproject a RasterRDD using an integer SRID
val temperature: RasterRDD[Float] = 
  sc.hdfFile("MOD11A1.A2022173.h08v05.006.2022174092443.hdf", "LST_Day_1km")
temperature.reproject(4326)

// Reproject a RasterRDD using a CRS object and specific interpolation method
val temperature2: RasterRDD[Float] =
  sc.hdfFile("MOD11A1.A2022173.h08v05.006.2022174092443.hdf", "LST_Day_1km")
temperature2.reproject(CRS.decode("EPSG:4326"), RasterOperationsFocal.InterpolationMethod.Average)

// Reproject RasterMetadata
val metadata = RasterMetadata.create(-180, 45, -90, 0, 4326, 90, 45, 10, 10)
val metadata2 = metadata.reproject(CRS.decode("EPSG:3857"))
```

### LLM Instruction Prompt
- Call `reproject` as an extension method directly on the `RasterRDD` or `RasterMetadata` object.
- You can pass either an integer SRID (e.g., `4326`) or a decoded CRS object (e.g., `CRS.decode("EPSG:4326")`).
- **Interpolation Rule:** If the raster contains continuous numerical data (like temperature or elevation), you MUST explicitly pass `RasterOperationsFocal.InterpolationMethod.Average`. The default is `NearestNeighbor`, which is only appropriate for categorical data or general downsizing.
- **Resolution Rule:** `reproject` keeps the resolution (number of pixels) of the first tile. If you need to change the resolution, tile size, or bounding box simultaneously, do not use `reproject`; use `RasterOperationsFocal.reshapeAverage` or `reshapeNN` with a custom `RasterMetadata` instead.

### Prompt Snippet
```text
To reproject a RasterRDD to a new CRS, use `raster.reproject(targetSRID)` or `raster.reproject(CRS.decode("EPSG:..."), unifiedRaster = false, interpolationMethod)`. Use `InterpolationMethod.Average` for continuous data. To change resolution alongside CRS, use `reshapeAverage` instead.
```

### Common Failure Modes
- **Incorrect Interpolation:** Relying on the default `NearestNeighbor` interpolation for continuous data (e.g., temperature, NDVI), resulting in aliased or statistically inaccurate resampling.
- **Attempting to Change Resolution:** Expecting `reproject` to alter the pixel dimensions or tile sizes. `reproject` strictly uses the resolution of the first tile in the source raster.
- **Overlay Precondition Failures:** Reprojecting two rasters to the same CRS but failing to realize they still have mismatched resolutions or tile sizes, which will cause `raster.overlay(...)` to fail. (Use `reshape` to perfectly align rasters for overlay).

### Fix Code Hint
```scala
// Wrong: Using default NearestNeighbor for continuous temperature data
val reprojected = tempRaster.reproject(4326)

// Correct: Specify Average interpolation for continuous data
val reprojected = tempRaster.reproject(
  CRS.decode("EPSG:4326"), 
  unifiedRaster = false, 
  RasterOperationsFocal.InterpolationMethod.Average
)
```

## API Test: `reprojectEnvelope`

### Signature
```scala
def reprojectEnvelope(envelope: Envelope, sourceSRID: Int, targetSRID: Int): Envelope
def reprojectEnvelope(envelope: Envelope, sourceCRS: CoordinateReferenceSystem, targetCRS: CoordinateReferenceSystem): Envelope
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/Reprojector.scala:427  (+1 more definition site/overload)_

_Source doc:_ Reprojects an envelope from one SRID to another SRID @param envelope the envelope to reproject with dimensions in source SRID @param sourceSRID the SRID of the given envelope @param targetSRID the desired SRID of the reprojected envelope @return the envelope after being reprojected to target SRID

### Goal
Transforms a spatial bounding box (`Envelope`) from one Coordinate Reference System (CRS/SRID) to another, ensuring spatial queries, raster reshaping, and vector alignments use matching coordinate spaces.

### Parameters
- `envelope` (`Envelope`): The JTS `Envelope` representing the bounding box with dimensions in the source coordinate system.
- `sourceSRID` (`Int`): The integer EPSG code (e.g., `4326` for WGS84) of the input envelope. In the overloaded method, this is a GeoTools `CoordinateReferenceSystem` object.
- `targetSRID` (`Int`): The desired integer EPSG code (e.g., `3857` for Web Mercator) for the output envelope. In the overloaded method, this is a GeoTools `CoordinateReferenceSystem` object.

### Input
A valid JTS `Envelope` object and valid source/target EPSG codes (or instantiated `CoordinateReferenceSystem` objects). The coordinates in the envelope must fall within the valid bounds of the `sourceSRID`.

### Output
Returns `Envelope` — A new JTS `Envelope` representing the minimum bounding box that fully contains the reprojected corners and edges of the original envelope in the target coordinate reference system.

### Valid Call Patterns
```scala
// Inferred from the signature and the Reprojector object context in the test suite
import org.locationtech.jts.geom.Envelope
import edu.ucr.cs.bdlab.beast.cg.Reprojector

val sourceEnvelope = new Envelope(-124.0, -114.0, 32.0, 42.0) // minX, maxX, minY, maxY
val targetEnvelope = Reprojector.reprojectEnvelope(sourceEnvelope, 4326, 3857)
```

### LLM Instruction Prompt
- When aligning bounding boxes for spatial partitioning, raster reshaping, or filtering across different coordinate systems, use `Reprojector.reprojectEnvelope`.
- Call it as a static method on the `Reprojector` object.
- Ensure you pass the correct integer EPSG codes (e.g., `4326`, `3857`) or valid GeoTools `CoordinateReferenceSystem` objects.
- Do not use this method to reproject complex geometries (polygons/lines); use `Reprojector.reprojectGeometry` for those.

### Prompt Snippet
```text
To reproject a bounding box in Beast, use `Reprojector.reprojectEnvelope(envelope, sourceSRID, targetSRID)`. This is useful when preparing an Envelope for `RasterOperationsFocal.reshapeNN` or spatial queries where the target dataset uses a different CRS.
```

### Common Failure Modes
- **Invalid or Unsupported SRID:** Passing an unrecognized integer as an SRID will cause a failure when Beast attempts to decode the EPSG code.
- **Axis Order Confusion:** JTS Envelopes are constructed using `(minX, maxX, minY, maxY)`. For EPSG:4326, this corresponds to `(minLongitude, maxLongitude, minLatitude, maxLatitude)`. Passing latitude as X will result in an out-of-bounds reprojection error.
- **Out of Bounds Coordinates:** Attempting to reproject an envelope whose coordinates fall outside the valid domain of the source CRS (e.g., longitudes > 180 in EPSG:4326) will throw a transformation exception.

### Fix Code Hint
```scala
// BAD: Passing latitude as X (minX, maxX, minY, maxY)
val badEnv = new Envelope(32.0, 42.0, -124.0, -114.0) 
val reprojected = Reprojector.reprojectEnvelope(badEnv, 4326, 3857) // Fails or yields garbage

// GOOD: Longitude is X, Latitude is Y
val goodEnv = new Envelope(-124.0, -114.0, 32.0, 42.0)
val reprojected = Reprojector.reprojectEnvelope(goodEnv, 4326, 3857)
```

## API Test: `reprojectEnvelopeInPlace`

### Signature
```scala
def reprojectEnvelopeInPlace(envelope: Array[Double], sourceSRID: Int, targetSRID: Int): Unit
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/Reprojector.scala:465_

_Source doc:_ Reproject an envelope (orthogonal rectangle) to the target CRS in-place @param envelope the input envelope to convert in the form (x1, y1, x2, y2) @param sourceSRID the source coordinate reference system (CRS) @param targetSRID the target coordinate reference system (CRS) @return the converted envelope

### Goal
Transforms the coordinates of a spatial bounding box (envelope) from a source Coordinate Reference System (CRS) to a target CRS, modifying the provided array directly.

### Parameters
- `envelope` (`Array[Double]`): A mutable 4-element array representing the input bounding box in the form `(x1, y1, x2, y2)`.
- `sourceSRID` (`Int`): The EPSG code of the original coordinate reference system (e.g., `4326` for WGS84).
- `targetSRID` (`Int`): The EPSG code of the destination coordinate reference system (e.g., `3857` for Web Mercator).

### Input
A mutable `Array[Double]` of exactly 4 elements representing an orthogonal rectangle's extents. The caller must provide valid integer EPSG codes for both the source and target spatial reference systems. If the envelope extends beyond the valid bounds of the target CRS, the resulting coordinates will be limited to the target's maximum extents.

### Output
Returns `Unit` — the operation performs an in-place mutation. The original `envelope` array is updated to contain the reprojected `(x1, y1, x2, y2)` coordinates in the target CRS.

### Valid Call Patterns
```scala
// Reprojecting an envelope from WGS84 (4326) to Web Mercator (3857)
val envelope = Array(-180.0, 0.0, 0.0, 90.0)
Reprojector.reprojectEnvelopeInPlace(envelope, 4326, 3857)

// The envelope array now contains the reprojected coordinates
// e.g., envelope(0) is approximately -20037508.0
```

### LLM Instruction Prompt
- When reprojecting an envelope, you MUST call `Reprojector.reprojectEnvelopeInPlace(envelope, source, target)`.
- Do NOT assign the result of this function to a variable; it returns `Unit` and modifies the `envelope` array in-place.
- Ensure the `envelope` argument is a mutable `Array[Double]` of exactly size 4 `(x1, y1, x2, y2)`. Do not pass a Tuple or a custom Envelope object.

### Prompt Snippet
```text
`Reprojector.reprojectEnvelopeInPlace(env: Array[Double], src: Int, tgt: Int): Unit` mutates a 4-element array `(x1, y1, x2, y2)` in-place to the target EPSG code. Do not assign its return value.
```

### Common Failure Modes
- **Type Mismatch on Return:** Assigning the result to a variable (e.g., `val newEnv = Reprojector.reprojectEnvelopeInPlace(...)`) and attempting to use `newEnv` as an array. The function returns `Unit`.
- **Array Bounds Error:** Passing an array with fewer than 4 elements, which will cause an `IndexOutOfBoundsException` during the in-place update.
- **Immutable Collection:** Passing an immutable collection (like a `List` or `Tuple4`) instead of a mutable `Array[Double]`.

### Fix Code Hint
```scala
// WRONG: Assigning the result of an in-place operation
val reprojectedEnv = Reprojector.reprojectEnvelopeInPlace(Array(-180.0, 0, 0, 90), 4326, 3857)
// reprojectedEnv is of type Unit!

// CORRECT: Mutating the array in-place
val envelope = Array(-180.0, 0.0, 0.0, 90.0)
Reprojector.reprojectEnvelopeInPlace(envelope, 4326, 3857)
// Use 'envelope' directly for subsequent operations
```

## API Test: `reprojectGeometry`

### Signature
```scala
def reprojectGeometry(geometry: Geometry, sourceCRS: CoordinateReferenceSystem, targetCRS: CoordinateReferenceSystem): Geometry
def reprojectGeometry(geometry: Geometry, targetSRID: Int): Geometry
def reprojectGeometry(geometry: Geometry, transform: TransformationInfo): Geometry
```
_Source doc:_ Reprojects the given geometry from source to target CRS. This method ignores the SRID of the geometry and assumes it to be in the source CRS. @param geometry the geometry to transform @param sourceCRS source coordinate reference system @param targetCRS target coordinate reference system @return a new geometry that is transformed

### Goal
Reprojects a spatial geometry from a source Coordinate Reference System (CRS) to a target CRS, returning a newly transformed geometry object.

### Parameters
- `geometry` (`Geometry`): The JTS `Geometry` (e.g., `Point`, `LineString`, `Polygon`) or Beast spatial type (e.g., `PointND`, `EnvelopeND`) to be transformed.
- `sourceCRS` (`CoordinateReferenceSystem`): The GeoTools coordinate reference system representing the original projection of the input geometry.
- `targetCRS` (`CoordinateReferenceSystem`): The GeoTools coordinate reference system representing the desired output projection.

### Input
A valid spatial `Geometry` object. The caller must provide valid GeoTools `CoordinateReferenceSystem` instances (typically obtained via `CRS.decode`). 
*Precondition:* The method explicitly ignores the internal SRID set on the input `geometry` and strictly assumes its coordinates are in the provided `sourceCRS`. 

### Output
Returns `Geometry` — A new JTS or Beast `Geometry` instance containing the transformed coordinates in the target CRS. The original input geometry is never mutated.

### Valid Call Patterns
```scala
import org.geotools.referencing.CRS
import edu.ucr.cs.bdlab.beast.cg.Reprojector

// Decode CRSs (using 'true' to force standard longitude/latitude X/Y axis order)
val sourceCRS = CRS.decode("EPSG:4326", true)
val targetCRS = CRS.decode("EPSG:3857", true)

// Reproject a geometry from source to target CRS
val transformedGeom = Reprojector.reprojectGeometry(originalGeometry, sourceCRS, targetCRS)

// Reproject using the target SRID overload (assumes source is known/handled by context)
val transformedGeomSrid = Reprojector.reprojectGeometry(originalGeometry, 3857)
```

### LLM Instruction Prompt
- Call `Reprojector.reprojectGeometry(...)` to transform vector geometries between coordinate systems.
- ALWAYS capture the return value; the function returns a new `Geometry` object and does not mutate the input geometry in place.
- Be aware that `reprojectGeometry` ignores the geometry's internal SRID property. You must explicitly provide the correct `sourceCRS` if using the full signature.
- When decoding EPSG codes for the CRS parameters, prefer `CRS.decode("EPSG:XXXX", true)` to enforce standard (longitude/latitude) axis ordering and prevent axis-flipping bugs.

### Prompt Snippet
```text
To reproject a geometry in Beast, use `Reprojector.reprojectGeometry(geom, sourceCRS, targetCRS)`. It returns a new `Geometry` and ignores the input's internal SRID. Capture the output. Use `CRS.decode("EPSG:...", true)` to ensure correct X/Y axis order.
```

### Common Failure Modes
- **Ignoring the Return Value:** Calling `Reprojector.reprojectGeometry(geom, ...)` without assigning the result, mistakenly assuming the original `geom` was modified in place.
- **Axis Order Reversal:** Passing a `CoordinateReferenceSystem` decoded without the `true` flag (e.g., `CRS.decode("EPSG:4326")`), which can result in flipped X/Y (Latitude/Longitude instead of Longitude/Latitude) coordinates during the math transformation.
- **Relying on Geometry SRID:** Expecting the method to automatically detect the source projection from `geometry.getSRID()`. The method explicitly ignores the geometry's SRID and relies entirely on the provided `sourceCRS` argument.

### Fix Code Hint
```scala
// WRONG: Assumes in-place mutation and relies on default axis order
val crs = CRS.decode("EPSG:3857")
Reprojector.reprojectGeometry(myPoint, crs) 

// CORRECT: Captures the new geometry and forces Longitude/Latitude axis order
val targetCRS = CRS.decode("EPSG:3857", true)
val sourceCRS = CRS.decode("EPSG:4326", true)
val projectedPoint = Reprojector.reprojectGeometry(myPoint, sourceCRS, targetCRS)
```

## API Test: `reprojectRDD`

### Signature
```scala
def reprojectRDD(sourceRDD: SpatialRDD, targetCRS: CoordinateReferenceSystem): SpatialRDD
def reprojectRDD(sourceRDD: SpatialRDD, targetSRID: Int): SpatialRDD
def reprojectRDD(sourceRDD: SpatialRDD, transform: TransformationInfo): SpatialRDD
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/Reprojector.scala:235  (+2 more definition site/overload)_

_Source doc:_ Reproject the given RDD to the target CRS. The source CRS is retrieved from the first element of the source RDD. @param sourceRDD the RDD to transform @param targetCRS the target Coordinate Reference System @return the transformed RDD

### Goal
Reproject a distributed dataset of vector geometries (`SpatialRDD`) from its original Coordinate Reference System (CRS) to a new target CRS.

### Parameters
- `sourceRDD` (`SpatialRDD`): The input RDD of vector features (equivalent to `RDD[IFeature]`) to be transformed. The source CRS is automatically retrieved from the first element of this RDD.
- `targetCRS` (`CoordinateReferenceSystem`): The destination Coordinate Reference System to which the geometries will be projected. Overloads allow passing an `Int` (target SRID) or a `TransformationInfo` object instead.

### Input
A `SpatialRDD` (typically loaded via `sc.shapefile`, `sc.geojsonFile`, etc.) containing vector features. 
*   **Precondition:** The RDD must not be empty, and the first feature in the RDD *must* have a valid CRS attached to its geometry, as the source CRS is inferred directly from it.
*   **Type Rule:** This function is strictly for vector data (`SpatialRDD` / `RDD[IFeature]`). It cannot be used for raster data.

### Output
Returns `SpatialRDD` — A new RDD of vector features (`IFeature`) where all geometries have been mathematically transformed to the target CRS.

### Valid Call Patterns
```scala
// 1. Reprojecting using a CoordinateReferenceSystem object
val projectedPolygons: RDD[IFeature] = Reprojector.reprojectRDD(polygons, CRSServer.sridToCRS(3857))

// 2. Reprojecting using an integer SRID (via overload)
val projectedPolygonsSrid: RDD[IFeature] = Reprojector.reprojectRDD(polygons, 3857)
```

### LLM Instruction Prompt
- Call `Reprojector.reprojectRDD(sourceRDD, targetSRID)` to reproject vector datasets (`SpatialRDD` / `RDD[IFeature]`).
- NEVER use `Reprojector.reprojectRDD` for raster data (`RasterRDD` / `RDD[ITile[T]]`). To reproject or rescale rasters, you MUST use `RasterOperationsFocal.reshapeNN` or `RasterOperationsFocal.reshapeAverage`.
- Do not provide a source CRS argument; Beast automatically infers the source CRS from the first element of the `sourceRDD`.

### Prompt Snippet
```text
To reproject vector geometries in Beast, use `Reprojector.reprojectRDD(vectorRdd, targetSrid)`. The source CRS is automatically inferred from the first element. Do not use this function for rasters; raster reprojection requires `RasterOperationsFocal.reshapeNN` or `reshapeAverage` with a target `RasterMetadata`.
```

### Common Failure Modes
- **Passing a Raster RDD:** Attempting to pass a `RasterRDD` or `RDD[ITile[T]]` to `reprojectRDD`. This will fail compilation because `reprojectRDD` expects a `SpatialRDD` (vector features).
- **Empty RDD or Missing Source CRS:** If the `sourceRDD` is empty, or if the first feature's geometry lacks a defined CRS, the automatic source CRS inference will fail at runtime.
- **Calling as an instance method:** Attempting to call `sourceRDD.reprojectRDD(...)` instead of the correct object method `Reprojector.reprojectRDD(sourceRDD, ...)`.

### Fix Code Hint
```scala
// WRONG: Attempting to reproject a raster using Reprojector
// val projectedRaster = Reprojector.reprojectRDD(raster, 3857)

// RIGHT: Reprojecting a vector SpatialRDD
val projectedPolygons = Reprojector.reprojectRDD(polygons, 3857)

// RIGHT: Reprojecting a raster requires reshape API
// val reshapedRaster = RasterOperationsFocal.reshapeNN(raster, targetRasterMetadata)
```

## API Test: `rescale`

### Signature
```scala
def rescale(rasterWidth: Int, rasterHeight: Int, unifiedRaster: Boolean = false, interpolationMethod: InterpolationMethod.InterpolationMethod = InterpolationMethod.NearestNeighbor)
def rescale[T: ClassTag](raster: RasterRDD[T], rasterWidth: Int, rasterHeight: Int, unifiedRaster: Boolean = false, interpolationMethod: InterpolationMethod.InterpolationMethod = InterpolationMethod.NearestNeighbor): RasterRDD[T]
def rescale(newRasterWidth: Int, newRasterHeight: Int): RasterMetadata
def rescale(metadata: Array[RasterMetadata], rasterWidth: Int, rasterHeight: Int): RasterMetadata
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:542  (+3 more definition site/overload)_

_Source doc:_ Changes the resolution of the raster to the desired resolution without changing tile size or CRS. @param raster the raster to rescale @param rasterWidth the new raster width in terms of pixels @param rasterHeight the new height of the raster layer in terms of pixels @param unifiedRaster if set to true, all output tiles will belong to a single RasterMetadata @param interpolationMethod how to handle a target pixel that overlaps multiple source pixels @return a new raster RDD with the desired width and height

### Goal
Changes the resolution of a raster to a new desired width and height in pixels without altering the tile size or Coordinate Reference System (CRS).

### Parameters
- `raster` (`RasterRDD[T]`): The input raster RDD to be rescaled.
- `rasterWidth` (`Int`): The new total width of the raster layer in terms of pixels.
- `rasterHeight` (`Int`): The new total height of the raster layer in terms of pixels.
- `unifiedRaster` (`Boolean`), default `false`: If set to `true`, all output tiles will belong to a single `RasterMetadata` object.
- `interpolationMethod` (`InterpolationMethod.InterpolationMethod`), default `InterpolationMethod.NearestNeighbor`: The strategy used to calculate pixel values when a target pixel overlaps multiple source pixels (e.g., `NearestNeighbor` or `Average`).

### Input
A `RasterRDD[T]` (typically loaded via `sc.geoTiff[T]` or `sc.hdfFile`) where the type parameter `T` exactly matches the runtime pixel type of the file (`Int`, `Float`, `Array[Int]`, or `Array[Float]`). Alternatively, a `RasterMetadata` object can be provided to compute new metadata dimensions without processing pixel data.

### Output
Returns `RasterRDD[T]` — a new distributed raster dataset with the desired pixel width and height, ready for saving or further focal operations. (Returns `RasterMetadata` if using the metadata overloads).

### Valid Call Patterns
```scala
// 1. Rescale a categorical raster (uses default NearestNeighbor interpolation)
val raster: RasterRDD[Int] = sc.geoTiff[Int]("glc2000_v1_1.tif")
val rescaled = raster.rescale(360, 180)
rescaled.saveAsGeoTiff("glc_small", GeoTiffWriter.WriteMode -> "compatibility")

// 2. Rescale a continuous raster (requires Average interpolation)
val temperature: RasterRDD[Float] = sc.hdfFile("MOD11A1.hdf", "LST_Day_1km")
val rescaledTemp = temperature.rescale(360, 180, interpolationMethod = InterpolationMethod.Average)

// 3. Rescale RasterMetadata directly
val sourceMetadata = new RasterMetadata(0, 0, 100, 100, 100, 100, 4326, new AffineTransform())
val targetMetadata = sourceMetadata.rescale(10, 10)
```

### LLM Instruction Prompt
- Call `rescale` as an extension method directly on a `RasterRDD` or `RasterMetadata` object (e.g., `raster.rescale(width, height)`).
- You MUST choose the correct interpolation method based on the data type: use `InterpolationMethod.Average` for continuous numerical data (e.g., temperature, elevation). Rely on the default `NearestNeighbor` for categorical data (e.g., land cover).
- When specifying the interpolation method, use named arguments (e.g., `interpolationMethod = InterpolationMethod.Average`) to avoid type mismatch errors with the `unifiedRaster` boolean parameter.

### Prompt Snippet
```text
When changing the resolution of a raster in RDPro, use the `rescale` extension method: `raster.rescale(newWidth, newHeight)`. For continuous data (like temperature), you MUST specify `interpolationMethod = InterpolationMethod.Average`. For categorical data, leave it as the default `NearestNeighbor`. Always use named arguments for the interpolation method to skip the `unifiedRaster` boolean.
```

### Common Failure Modes
- **Invalid Interpolation on Categorical Data:** Applying `Average` interpolation to categorical rasters (like land cover), which averages class IDs and results in invalid, non-existent fractional classes.
- **Positional Argument Mismatch:** Passing the interpolation method as the third positional argument. Because the third argument in the signature is `unifiedRaster: Boolean`, this causes a compilation error.
- **Type Parameter Mismatch:** Loading the initial raster with the wrong type parameter (e.g., `sc.geoTiff[Int]` for float data), causing runtime crashes before the rescale operation can even execute.

### Fix Code Hint
```scala
// WRONG: Positional argument mismatch (Boolean expected) and wrong interpolation for continuous data
val rescaled = tempRaster.rescale(360, 180, InterpolationMethod.Average)

// CORRECT: Use named arguments for interpolationMethod
val rescaled = tempRaster.rescale(360, 180, interpolationMethod = InterpolationMethod.Average)
```

## API Test: `reshapeAverage`

### Signature
```scala
def reshapeAverage[T: ClassTag](raster: RasterRDD[T], targetMetadataConv: RasterMetadata => RasterMetadata, _numPartitions: Int = 0): RasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:58_

_Source doc:_ Converts the metadata of the input raster to the target metadata. This might involve any combination of the following: - reproject: Change the coordinate reference system (CRS) - regrid: Change the tiling of the raster - rescale: Change the resolution, i.e., number of pixels, in the raster - subset: Retrieve a subset of the data, even though, it would be an inefficient way to do just the subsetting Note: This is a low-level method that is normally not called directly by users. Instead, we provide higher-level easier to use functions for real use cases that all call this low-level function. Note: This method uses the average method to determine the final value of each pixel. If one pixel in the answer overlaps multiple pixels in the source, their average is computed. This method should only be used when pixels represent continuous values, e.g., red, infrared, temperature, or vegetation. If the pixels represent categorical values, e.g., land type, then the nearest neighbor method [[reshapeNN]] should be used instead. @param raster the input raster that should be reshaped @param targetMetadataConv a function that returns the desired metadata for source metadata @param _numPartitions the number of partitions of the produces RDD. If not set, it will be the same as the input @return the new raster with the target metadata

### Goal
Reshapes a raster (reprojecting, regridding, rescaling, or subsetting) by computing the average value of overlapping source pixels, designed specifically for continuous numerical data like temperature or vegetation indices.

### Parameters
- `raster` (`RasterRDD[T]`): The input raster dataset that needs to be reshaped.
- `targetMetadataConv` (`RasterMetadata => RasterMetadata,
                                  _numPartitions: Int`), default `0`: A function that takes the source `RasterMetadata` and returns the desired target `RasterMetadata`. The `_numPartitions` parameter (default 0) specifies the number of partitions for the produced RDD; if 0 or not set, it retains the same number of partitions as the input.

### Input
- A `RasterRDD[T]` containing continuous numerical data (e.g., `Float` or `Int` representing temperature, elevation, infrared, etc.).
- **Precondition:** Do not use this method for categorical data (e.g., land cover classes), as averaging class IDs produces invalid data. Use `reshapeNN` instead for categorical data.
- **Precondition:** Often used to align rasters (matching resolution, CRS, and tile size) before calling `raster.overlay(...)`, which strictly requires identical metadata across all inputs.

### Output
Returns `RasterRDD[T]` — A new raster RDD conforming to the target metadata, where each pixel's value is the computed average of the overlapping source pixels.

### Valid Call Patterns
```scala
// Pattern 1: Rescaling a raster (e.g., reducing resolution)
val targetMetadata = sourceMetadata.rescale(10, 10)
val outputRaster = RasterOperationsFocal.reshapeAverage(inputRaster, _ => targetMetadata)

// Pattern 2: Retiling or reprojecting using a newly constructed RasterMetadata
val targetMetadata = new RasterMetadata(0, 0, 100, 100, 10, 10, 4326, new AffineTransform())
val outputRaster = RasterOperationsFocal.reshapeAverage(inputRaster, _ => targetMetadata)
```

### LLM Instruction Prompt
- Call `RasterOperationsFocal.reshapeAverage(raster, _ => targetMetadata)` to align, rescale, or reproject rasters containing continuous values (e.g., NDVI, temperature).
- NEVER use `reshapeAverage` for categorical data (like land cover); use `RasterOperationsFocal.reshapeNN` instead.
- Pass a lambda function `_ => targetMetadata` as the second argument to satisfy the `RasterMetadata => RasterMetadata` signature.
- Use this method to align rasters to identical metadata before performing a `raster.overlay(...)` operation.

### Prompt Snippet
```text
To reshape/align continuous rasters (temperature, NDVI), use `RasterOperationsFocal.reshapeAverage(raster, _ => targetMetadata)`. For categorical data, use `reshapeNN`. This is required before `overlay` if rasters have differing CRS, resolution, or tile sizes.
```

### Common Failure Modes
- **Categorical Data Corruption:** Using `reshapeAverage` on land cover or classification rasters, resulting in meaningless fractional class IDs (e.g., averaging class 1 and class 2 to get 1.5).
- **Method Not Found:** Attempting to call `raster.reshapeAverage(...)` as an instance method on the RDD. It is an object method on `RasterOperationsFocal`.
- **Type Mismatch on Metadata:** Passing a raw `RasterMetadata` object instead of a function `RasterMetadata => RasterMetadata`. You must wrap it in a lambda (e.g., `_ => targetMetadata`).

### Fix Code Hint
```scala
// WRONG: Instance method call and passing raw metadata
// val reshaped = raster.reshapeAverage(targetMetadata)

// WRONG: Using average on categorical data
// val reshaped = RasterOperationsFocal.reshapeAverage(landCoverRaster, _ => targetMetadata)

// CORRECT: Object method call, lambda for metadata, used on continuous data
val reshaped = RasterOperationsFocal.reshapeAverage(temperatureRaster, _ => targetMetadata)
```

## API Test: `reshapeNN`

### Signature
```scala
def reshapeNN[T: ClassTag](raster: RasterRDD[T], targetMetadataConv: RasterMetadata => RasterMetadata, numPartitions: Int = 0): RasterRDD[T]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:408_

_Source doc:_ Converts the metadata of the input raster to the target metadata. This might involve any combination of the following: - reproject: Change the coordinate reference system (CRS) - regrid: Change the tiling of the raster - rescale: Change the resolution, i.e., number of pixels, in the raster - subset: Retrieve a subset of the data, even though, it would be an inefficient way to do just the subsetting Note: This is a low-level method that is normally not called directly by users. Instead, we provide higher-level easier to use functions for real use cases that all call this low-level function. Note: This method uses the nearest neighbor method to match source to target pixels. Each target pixel gets its value from the nearest source pixel. If that source pixel is empty or outside the range of the source raster, the target pixel will be empty. @param raster the input raster that should be reshaped @param targetMetadataConv a function that converts a source RasterMetadata to target RasterMetadata @param numPartitions the number of partitions in the output RDD. If not set, the input numPartitions is used @return the new raster with the target metadata

### Goal
Reshapes a raster dataset by altering its coordinate reference system (CRS), resolution, tiling, or spatial extent, using nearest-neighbor interpolation to assign pixel values.

### Parameters
- `raster` (`RasterRDD[T]`): The input raster dataset that needs to be reshaped, reprojected, rescaled, or retiled.
- `targetMetadataConv` (`RasterMetadata => RasterMetadata,
                             numPartitions: Int`), default `0`: A function that takes the source `RasterMetadata` and returns the target `RasterMetadata` (defining the new CRS, resolution, bounds, and tile size). The `numPartitions` parameter dictates the number of partitions in the output RDD; if `0` or not set, the input's partition count is preserved.

### Input
- A `RasterRDD[T]` typically loaded via `sc.geoTiff[T](...)` where `T` exactly matches the runtime pixel type of the file (e.g., `Int` for `IntegerType`, `Float` for `FloatType`).
- **Preconditions & Type Selection:** `reshapeNN` (Nearest Neighbor) should specifically be used for **categorical data** (e.g., land cover classes) or general downsizing. If the pixel data is numerical and continuous (e.g., temperature), `reshapeAverage` must be used instead.

### Output
Returns `RasterRDD[T]` — A new distributed raster dataset conforming to the target metadata. Empty source pixels or pixels outside the source range result in empty target pixels. The output can be saved directly via `saveAsGeoTiff` or used safely in multi-raster operations like `overlay`.

### Valid Call Patterns
```scala
// From the original project README (using an implicit or simplified metadata conversion)
val raster: RasterRDD[Int] = sc.geoTiff[Int]("glc2000_v1_1.tif")
val reshaped = RasterOperationsFocal.reshapeNN(raster,
  RasterMetadata.create(-124, 42, -114, 32, 4326, 1000, 1000, 100, 100))
reshaped.saveAsGeoTiff("glc_ca")

// Strict signature-matching pattern (derived from sibling test `reshapeAverage`)
val targetMetadata = RasterMetadata.create(-124, 42, -114, 32, 4326, 1000, 1000, 100, 100)
val reshapedStrict = RasterOperationsFocal.reshapeNN(raster, _ => targetMetadata)
```

### LLM Instruction Prompt
- Use `RasterOperationsFocal.reshapeNN` to align rasters before an `overlay` operation, as `overlay` strictly requires all input rasters to have identical metadata (resolution, CRS, and tile size).
- Always choose `reshapeNN` for categorical rasters. Do not use it for continuous numerical data; use `reshapeAverage` for that.
- Pass a function `_ => targetMetadata` as the second argument to satisfy the `RasterMetadata => RasterMetadata` signature when defining a completely new target grid.
- Ensure the type parameter `T` matches the underlying GeoTIFF pixel type (e.g., `Int` or `Float`).

### Prompt Snippet
```text
I have two categorical land-cover GeoTIFFs with different resolutions and CRSs. 
I need to combine them using `overlay`. How do I align their metadata first?
```

### Common Failure Modes
- **Interpolation Mismatch:** Using `reshapeNN` on continuous numerical data (like temperature or elevation) instead of `reshapeAverage`, leading to aliasing, blocky artifacts, or loss of precision.
- **Overlay Precondition Violation:** Attempting to call `raster1.overlay(raster2)` without first using `reshapeNN` to perfectly align their CRS, resolution, and tile sizes.
- **Type Mismatch:** Loading the raster with the wrong type (e.g., `sc.geoTiff[Float]` for an integer raster) before reshaping, causing runtime casting exceptions.

### Fix Code Hint
```scala
// BAD: Calling overlay on unaligned rasters
// val combined = raster1.overlay(raster2, ...)

// GOOD: Aligning the second raster to the first raster's metadata using reshapeNN before overlay
val alignedRaster2 = RasterOperationsFocal.reshapeNN(raster2, _ => raster1.metadata)
val combined = raster1.overlay(alignedRaster2, (p1: Int, p2: Int) => if (p1 > 0) p1 else p2)
```

## API Test: `retainIndex`

### Signature
```scala
def retainIndex(index: Int): BeastOptions
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/common/BeastOptions.scala:168_

_Source doc:_ Keep only the parameters that do not have an index or the ones with the given index. In other words, remove any indexed parameter that have a different index than the one given. The index of the parameter is a suffix between square brackets, e.g., param[1] @param index the index to retain @return a new options with the given index retained

### Goal
Filters a `BeastOptions` configuration object to keep only unindexed parameters and parameters matching a specific integer index, stripping the index suffix from the retained keys.

### Parameters
- `index` (`Int`): The integer index to retain (e.g., passing `1` will keep keys formatted like `param[1]`).

### Input
A `BeastOptions` instance containing configuration key-value pairs. This is typically used when a single configuration object holds parameters for multiple inputs or operations simultaneously, distinguished by an index suffix in square brackets (e.g., `key[1]`, `key[2]`).

### Output
Returns `BeastOptions` — A new `BeastOptions` instance containing only the unindexed keys and the retained indexed keys. The retained indexed keys will have their `[index]` suffix removed in the returned object.

### Valid Call Patterns
```scala
val opts = new BeastOptions()
  .set("key1[1]", "val1")
  .set("key1[2]", "val2")
  .set("key3", "val3")
  .set("key4[2]", "val4")

// Retains "key1[1]" (renamed to "key1") and unindexed "key3"
val opts1 = opts.retainIndex(1)

// Retains "key1[2]" (renamed to "key1"), "key4[2]" (renamed to "key4"), and unindexed "key3"
val opts2 = opts.retainIndex(2)
```

### LLM Instruction Prompt
- Use `retainIndex` when you need to extract configuration parameters specific to a single dataset or operation from a combined `BeastOptions` object containing indexed keys (like `param[1]`, `param[2]`). 
- Remember that the returned `BeastOptions` will have the index suffix stripped from the keys (e.g., `key[1]` becomes `key`).
- Unindexed keys (e.g., global settings) are always retained regardless of the index provided.

### Prompt Snippet
```text
Use `opts.retainIndex(idx)` to filter a `BeastOptions` object, keeping unindexed keys and keys matching `[idx]`. The returned keys will have the `[idx]` suffix removed.
```

### Common Failure Modes
- **Querying with the old indexed key:** Attempting to retrieve a value from the new `BeastOptions` using the original indexed key string (e.g., `opts1("key1[1]")`). The method strips the suffix, so the key becomes just `"key1"`.
- **Losing parameters:** Passing an index that does not match any indexed keys in the `BeastOptions`. This will silently drop all indexed parameters and return an object containing *only* the unindexed parameters.

### Fix Code Hint
```scala
// WRONG: Trying to access the key with the index suffix after retaining
val opts1 = opts.retainIndex(1)
val value = opts1("key1[1]") // Will fail or return null

// RIGHT: Access the key without the suffix
val opts1 = opts.retainIndex(1)
val value = opts1("key1") // Returns "val1"
```

## API Test: `retile`

### Signature
```scala
def retile(tileWidth: Int, tileHeight: Int)
def retile[T: ClassTag](raster: RasterRDD[T], tileWidth: Int, tileHeight: Int): RasterRDD[T]
def retile(newTileWidth: Int, newTileHeight: Int): RasterMetadata
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:566  (+2 more definition site/overload)_

_Source doc:_ Regrids the given raster to the target tile width and height @param raster the raster to regrid @param tileWidth the new tile width in pixels @param tileHeight the new tile height in pixels @tparam T the type of the pixel values in the raster @return a new raster with the given tile width and height

### Goal
Regrids a distributed raster dataset into new internal tile dimensions (width and height in pixels) without altering the overall spatial resolution, extent, or pixel values.

### Parameters
- `raster` (`RasterRDD[T]`): The input distributed raster dataset to be regridded.
- `tileWidth` (`Int`): The new tile width in pixels (e.g., 64, 256).
- `tileHeight` (`Int`): The new tile height in pixels (e.g., 64, 256).

### Input
A `RasterRDD[T]` typically loaded from a GeoTIFF or HDF file. The type parameter `T` must exactly match the file's runtime pixel type (e.g., `Int` for `IntegerType`, `Float` for `FloatType`, `Array[Int]` for `ArrayType(IntegerType, true)`). 

### Output
Returns `RasterRDD[T]` — A new raster dataset containing the exact same pixel data and metadata (CRS, resolution), but partitioned internally into tiles of the newly specified width and height.

### Valid Call Patterns
```scala
// 1. Instance method (Implicit extension on RasterRDD)
val raster: RasterRDD[Int] = sc.geoTiff[Int]("glc2000_v1_1.tif")
val retiled = raster.retile(64, 64)
retiled.saveAsGeoTiff("glc_retiled")

// 2. Chained with explode for distributed writing
val retiledExploded = raster.retile(64, 64).explode
retiledExploded.saveAsGeoTiff("glc_retiled", GeoTiffWriter.WriteMode -> "distributed")

// 3. Static method call (RasterOperationsFocal)
val retiledStatic: RasterRDD[Int] = RasterOperationsFocal.retile(raster, 20, 20)
```

### LLM Instruction Prompt
- Use `raster.retile(width, height)` to change the internal chunking/tile size of a raster. Do not confuse this with `reshapeNN` or `reshapeAverage`, which are used to change the actual spatial resolution or CRS.
- When breaking large tiles into smaller ones for distributed processing, chain `.retile(w, h)` with `.explode`.
- If saving a raster after calling `.explode`, you MUST use `GeoTiffWriter.WriteMode -> "distributed"` to write each partition to a separate file, avoiding driver OOMs.
- Ensure the type parameter `T` of the `RasterRDD` matches the underlying data type (e.g., `Int` or `Float`).

### Prompt Snippet
```text
To change the internal tile dimensions of a RasterRDD without altering its resolution or CRS, use `raster.retile(tileWidth, tileHeight)`. This is often chained with `.explode` to break large monolithic tiles into smaller distributed partitions. When saving an exploded raster, always pass `GeoTiffWriter.WriteMode -> "distributed"` to `saveAsGeoTiff`.
```

### Common Failure Modes
- **Driver OutOfMemoryError on Save:** Calling `raster.retile(w, h).explode.saveAsGeoTiff("out")` without specifying the `"distributed"` write mode. The default `"compatibility"` mode attempts to collect all tiles to the driver to write a single file, crashing the application.
- **Type Mismatch on Load:** Loading the raster with the wrong type (e.g., `sc.geoTiff[Int]` for a FloatType raster) will cause runtime casting exceptions before or during the `retile` operation.
- **Excessive Overhead:** Retiling to extremely small dimensions (e.g., 1x1 or 2x2 pixels) creates massive object overhead in Spark, leading to severe performance degradation.

### Fix Code Hint
```scala
// Incorrect: Exploding and saving without distributed mode
// val retiled = raster.retile(64, 64).explode
// retiled.saveAsGeoTiff("output")

// Correct: Retile, explode, and save in distributed mode
val raster: RasterRDD[Float] = sc.geoTiff[Float]("input.tif")
val retiled = raster.retile(256, 256).explode
retiled.saveAsGeoTiff("output_dir", GeoTiffWriter.WriteMode -> "distributed")
```

## API Test: `run`

### Signature
```scala
def run(opts: BeastOptions, inputs: Array[String], outputs: Array[String], sc: SparkContext): Any
def run(opts: BeastOptions, inputs: Array[String], outputs: Array[String], sc: SparkContext): Unit
def run(source: String, tileDir: String, indexFile:FileStatus, z: Int, currX: Int, currY: Int, sc: SparkContext): (BufferedImage,Int)
def run(inputs: Array[String], sc: SparkContext): String
def run(inputs: Array[String], sc: SparkContext): Array[Int]
def run(opts: BeastOptions, inputs: Array[String], sc: SparkContext): String
def run(inputs: Array[String], sc: SparkContext): BufferedImage
def run(): Unit
def run(opts: BeastOptions, inputs: Array[String], outputs: Array[String], sc: JavaSparkContext): Any
def run(opts: BeastOptions, inputs: Array[String], outputs: Array[String], ss: SparkSession): Any
```
_Source: beast/dynoviz/src/main/scala/edu/ucr/cs/bdlab/dynoviz/NPYTileGeneratorOnthefly.scala:29  (+28 more definition site/overload)_

### Goal
Executes a Beast/RDPro operation. The primary documented overload runs a main function (like `GeometricSummary` or `BeastServer`) using user command-line options, input/output paths, and a Spark context, while other internal overloads handle tasks like on-the-fly tile generation.

### Parameters
- `source` (`String`): Unknown (not provided in authoritative API facts; likely the source data path for tile generation).
- `tileDir` (`String`): Unknown (not provided in authoritative API facts; likely the directory for output tiles).
- `indexFile` (`FileStatus`): Unknown (not provided in authoritative API facts; likely the spatial index file).
- `z` (`Int`): Unknown (not provided in authoritative API facts; likely the zoom level).
- `currX` (`Int`): Unknown (not provided in authoritative API facts; likely the X coordinate of the tile).
- `currY` (`Int`): Unknown (not provided in authoritative API facts; likely the Y coordinate of the tile).
- `sc` (`SparkContext`): The Spark context used to run the operation.

*(Note: The authoritative API facts primarily document the `(opts: BeastOptions, inputs: Array[String], outputs: Array[String], sc: SparkContext)` overload).*

### Input
For the primary operation runner: requires a `BeastOptions` object configuring the operation (e.g., setting `iformat`, `skipheader`, `separator`), an `Array[String]` of input file paths, an `Array[String]` of output paths (or `null` if no output is written), and an initialized `SparkContext`. 
For the tile generator overload (pre-filled parameters): requires a source path, tile directory, spatial index `FileStatus`, and XYZ tile coordinates (exact semantics are unknown as they are not in the authoritative facts).

### Output
Returns `(BufferedImage,Int)` — Unknown (not provided in authoritative API facts; likely an image buffer of the generated tile and a status/count integer). 
*(Note: The primary documented `run` overload returns `Any`, representing an optional result of the operation, such as a `Summary` object, which must be cast by the caller).*

### Valid Call Patterns
```scala
// Example 1: Running a geometric summary operation (primary overload)
val inputfile = locateResource("/test.partitions")
val opts = new BeastOptions().set("iformat", "wkt(Geometry)")
  .set("skipheader", true)
  .set("separator", "\t")
val summary = GeometricSummary.run(opts, Array(inputfile.getPath), null, sparkContext).asInstanceOf[Summary]

// Example 2: Starting the Beast server (primary overload)
new BeastServer().run(new BeastOptions(), null, null, sparkContext)
```

### LLM Instruction Prompt
- Use the `run` method to execute Beast operations (e.g., `GeometricSummary.run` or `new BeastServer().run`).
- Always pass inputs and outputs as `Array[String]`. If an operation does not produce file output, pass `null` for the `outputs` array.
- The primary `run` method returns `Any`. You MUST cast the result to the expected type (e.g., `.asInstanceOf[Summary]`) to access its properties.
- Do not invent parameters. The authoritative JSON facts only define the `(opts, inputs, outputs, sc)` signature, despite internal overloads existing for tile generation.

### Prompt Snippet
```text
val opts = new BeastOptions().set("iformat", "wkt(Geometry)")
val summary = GeometricSummary.run(opts, Array("input.csv"), null, sc).asInstanceOf[Summary]
```

### Common Failure Modes
- **Type Mismatch on Inputs/Outputs:** Passing a single `String` instead of an `Array[String]` for the `inputs` or `outputs` parameters.
- **Missing Cast:** Failing to cast the `Any` return type of the primary `run` method, leading to compilation errors when trying to access result properties (like `summary.numFeatures`).
- **Null Pointer Exceptions:** Passing `null` for `inputs` when the specific operation (like `GeometricSummary`) requires an input dataset to process.

### Fix Code Hint
```scala
// WRONG: Passing a single string and forgetting to cast the result
// val summary = GeometricSummary.run(opts, "data.csv", null, sc)

// CORRECT: Wrap the input path in an Array and cast the return type
val summary = GeometricSummary.run(opts, Array("data.csv"), null, sc).asInstanceOf[Summary]
```

## API Test: `saveAsCSVPoints`

### Signature
```scala
def saveAsCSVPoints(filename: String, xColumn: Int = 0, yColumn: Int = 1, delimiter: Char = ',', header: Boolean = true): Unit
def saveAsCSVPoints(rdd: JavaSpatialRDD, filename: String, xColumn: Int, yColumn: Int, delimiter: Char, header: Boolean): Unit
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:212  (+1 more definition site/overload)_

_Source doc:_ Save features to a CSV or text-delimited file. This method should be used only for point features. @param filename the name of the output file @param xColumn the index of the column that contains the x-coordinate in the output file @param yColumn the index of the column that contains the y-coordinate in the output file @param delimiter the delimiter in the output file, comma by default @param header whether to write a header line, true by default

### Goal
Save a distributed collection of point features (a `SpatialRDD`) to a CSV or text-delimited file, explicitly defining which columns will hold the X and Y coordinates.

### Parameters
- `filename` (`String`): The path or name of the output file/directory where the CSV data will be written.
- `xColumn` (`Int`), default `0`: The 0-based index of the column that will contain the X-coordinate (longitude) in the output file.
- `yColumn` (`Int`), default `1`: The 0-based index of the column that will contain the Y-coordinate (latitude) in the output file.
- `delimiter` (`Char`), default `'`: The character used to separate fields in the output file (defaults to a comma `,`).
- `'`: An artifact from documentation parsing (represents the closing quote of the default `','` delimiter); not a real parameter.
- `header` (`Boolean`), default `true`: Whether to write a header line at the top of the output file.

### Input
A `SpatialRDD` (in Scala) or `JavaSpatialRDD` (in Java) containing **only point features**. The caller must ensure the dataset does not contain polygons or linestrings, as this method is strictly designed for point geometries. 

### Output
Returns `Unit` — writes the point features to the specified `filename` as a distributed CSV or text-delimited file (typically as a directory containing part-files, following standard Spark output behavior).

### Valid Call Patterns
```scala
// Scala (called as an extension method on a SpatialRDD)
records.saveAsCSVPoints("output.csv", 1, 2, ',', true)

// Java (called via the helper class)
JavaSpatialRDDHelper.saveAsCSVPoints(records, "output.csv", 1, 2, ',', true);
```

### LLM Instruction Prompt
- Use `saveAsCSVPoints` to export a `SpatialRDD` to a CSV file, but ONLY if the RDD consists entirely of point features.
- Do not use this method for polygons or lines.
- Specify `xColumn` and `yColumn` to control the 0-based column indices for the X and Y coordinates in the resulting CSV.
- In Scala, call it directly on the RDD (`rdd.saveAsCSVPoints(...)`). In Java, use `JavaSpatialRDDHelper.saveAsCSVPoints(rdd, ...)`.

### Prompt Snippet
```text
To export point geometries to a CSV file, use `rdd.saveAsCSVPoints(filename, xColumn, yColumn, delimiter, header)`. Ensure the RDD contains only points.
```

### Common Failure Modes
- **Non-Point Geometries:** Calling this method on an RDD that contains polygons or linestrings. The source documentation explicitly restricts this to point features.
- **Column Index Conflicts:** Providing `xColumn` and `yColumn` indices that overwrite or conflict with existing attribute columns if the user expects attributes to be preserved in specific positions.
- **File Already Exists:** Standard Spark behavior applies; if the `filename` directory already exists, the job will fail unless the Spark output mode is configured to overwrite.

### Fix Code Hint
```scala
// Ensure you are working with point data before saving
val pointRecords = sparkContext.readCSVPoint("input.csv")

// Save the points, placing X in column 1 and Y in column 2
pointRecords.saveAsCSVPoints("output.csv", 1, 2, ',', true)
```

## API Test: `saveAsGeoJSON`

### Signature
```scala
def saveAsGeoJSON(filename: String, opts: BeastOptions = new BeastOptions()): Unit
def saveAsGeoJSON(rdd: JavaSpatialRDD, filename: String): Unit
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:201  (+1 more definition site/overload)_

_Source doc:_ Save features in GeoJSON format @param filename the output filename

### Goal
Save a distributed collection of spatial vector features (an RDD of geometries) to a file or directory in GeoJSON format.

### Parameters
- `filename` (`String`): The output path or filename where the GeoJSON data will be written.
- `opts` (`BeastOptions`), default `new BeastOptions()`: Optional configuration parameters for the Beast environment and underlying Spark writer.
- `rdd` (`JavaSpatialRDD`): *(Java overload only)* The Java spatial RDD containing the features to be saved.

### Input
A spatial vector RDD (e.g., `RDD[IFeature]` in Scala or `JavaSpatialRDD` in Java) containing geometries (points, lines, or polygons). This method is strictly for vector data and cannot be used on raster data (GeoTIFF/HDF).

### Output
Returns `Unit` — The operation produces no return value. Its side effect is writing the vector features to the specified `filename` as GeoJSON. Because Beast is built on Spark, this may write a directory containing multiple part-files if the RDD has multiple partitions.

### Valid Call Patterns
```scala
// Scala (via implicit extension on RDD[IFeature])
records.saveAsGeoJSON("output.geojson")

// Java (via static helper)
JavaSpatialRDDHelper.saveAsGeoJSON(records, "output.geojson")
```

### LLM Instruction Prompt
- Use `rdd.saveAsGeoJSON("path")` in Scala to export vector features to GeoJSON.
- Use `JavaSpatialRDDHelper.saveAsGeoJSON(rdd, "path")` when writing Java code.
- NEVER use `saveAsGeoJSON` on a `RasterRDD` or `RDD[ITile[T]]`. Raster data must be saved using `saveAsGeoTiff`.
- Do not invent a `saveAsGeoJSON` method on the `SparkContext` or `JavaSpatialSparkContext`; it is an action called directly on the RDD.

### Prompt Snippet
```text
RDPro/Beast vector export: Use `rdd.saveAsGeoJSON("path.geojson")` in Scala or `JavaSpatialRDDHelper.saveAsGeoJSON(rdd, "path.geojson")` in Java. Only valid for vector RDDs (`RDD[IFeature]`), not rasters.
```

### Common Failure Modes
- **Type Mismatch (Raster vs. Vector):** Attempting to call `saveAsGeoJSON` on a `RasterRDD` (e.g., after `mapPixels` or `reshapeNN`). GeoJSON is a vector format; rasters must use `saveAsGeoTiff`.
- **File Already Exists:** Like standard Spark actions, if the target `filename` directory already exists, the job will fail unless the output directory is cleared first or Spark's overwrite mode is configured.
- **Missing Implicit Conversions:** In Scala, if `saveAsGeoJSON` is not recognized on the RDD, the caller may have forgotten to import Beast's SparkContext extensions.

### Fix Code Hint
```scala
// WRONG: Attempting to save a raster as GeoJSON
val raster = sc.geoTiff[Int]("input.tif")
raster.saveAsGeoJSON("output.geojson") // Fails: saveAsGeoJSON is for vectors

// RIGHT: Save raster as GeoTiff
raster.saveAsGeoTiff("output_raster")

// RIGHT: Save vector features as GeoJSON
val features: RDD[IFeature] = sc.shapefile("input.zip")
features.saveAsGeoJSON("output.geojson")
```

## API Test: `saveAsGeoTiff`

### Signature
```scala
def saveAsGeoTiff(path: String, opts: BeastOptions = new BeastOptions): Unit
def saveAsGeoTiff[T](rasterRDD: RDD[ITile[T]], outPath: String, opts: BeastOptions): Unit
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/GeoTiffWriter.scala:476  (+1 more definition site/overload)_

### Goal
Save a distributed RasterRDD (a collection of image tiles) to disk as one or more GeoTIFF files.

### Parameters
- `rasterRDD` (`RDD[ITile[T]]`): The distributed raster dataset to be saved. (This parameter is implicit when calling the extension method directly on a `RasterRDD`).
- `outPath` (`String`): The destination directory or file path where the output GeoTIFF file(s) will be written (named `path` in the extension method).
- `opts` (`BeastOptions`): Additional configuration options for the writer, such as `GeoTiffWriter.BitsPerSample`, `GeoTiffWriter.BigTiff`, or `GeoTiffWriter.WriteMode`. Defaults to empty options.

### Input
A `RasterRDD` or `RDD[ITile[T]]` containing the processed raster data. 
**Preconditions and Configuration Rules:**
*   **Write Modes:** `GeoTiffWriter.WriteMode` supports `"distributed"` (writes each RDD partition to a separate file) and `"compatibility"` (writes a single file compatible with traditional GIS software). `"distributed"` is highly recommended if the raster was previously reshaped using `explode`.
*   **Bit Compaction:** `GeoTiffWriter.CompactBits` only works with integer pixel values. Float values are always represented in 32-bits. 
*   **Performance:** If using bit compaction on integers, you must explicitly provide `GeoTiffWriter.BitsPerSample` in the options; otherwise, the writer is forced to perform a full dataset scan to determine the maximum value.

### Output
Returns `Unit` — writes the raster data to the specified path as GeoTIFF file(s).

### Valid Call Patterns
```scala
// Pattern 1: Extension method on RasterRDD (most common)
val temperatureF: RasterRDD[Float] = temperatureK.mapPixels(k => (k-273.15f) * 9 / 5 + 32)
temperatureF.saveAsGeoTiff("temperature_f")

// Pattern 2: Extension method with inline filtering
temperatureK.filterPixels(_ > 300).saveAsGeoTiff("temperature_high")

// Pattern 3: Object method with specific BeastOptions (e.g., BitsPerSample)
val outputFile = new File(scratchDir, "glc.tif")
GeoTiffWriter.saveAsGeoTiff(rasterRDD, outputFile.getPath, GeoTiffWriter.BitsPerSample -> 8)

// Pattern 4: Object method with multiple BeastOptions
GeoTiffWriter.saveAsGeoTiff(rasterRDD, outputFile.getPath, 
  Seq(GeoTiffWriter.BitsPerSample -> 8, GeoTiffWriter.BigTiff -> "yes"))
```

### LLM Instruction Prompt
- Use `saveAsGeoTiff` to persist the results of raster operations (like `mapPixels`, `filterPixels`, or `reshapeNN`) to disk.
- Prefer the instance method `raster.saveAsGeoTiff("path")` for simple saves.
- When using `GeoTiffWriter.saveAsGeoTiff`, pass options using the `->` tuple syntax (e.g., `GeoTiffWriter.BitsPerSample -> 8`).
- NEVER attempt to use bit compaction on `Float` rasters; they are strictly 32-bit.
- ALWAYS specify `GeoTiffWriter.WriteMode -> "distributed"` if saving a raster immediately after an `explode` operation to avoid massive single-file bottlenecks.
- ALWAYS provide `GeoTiffWriter.BitsPerSample` if using integer bit compaction to prevent an expensive full-dataset scan.

### Prompt Snippet
```text
Write a Spark pipeline using RDPro that loads a GeoTIFF of integer land cover classes, filters for class 5, and saves the result to "forest_class.tif" using 8 bits per sample.
```

### Common Failure Modes
- **Full Dataset Scan Bottleneck:** Omitting `GeoTiffWriter.BitsPerSample` when saving integer rasters with bit compaction enabled, causing Spark to trigger an unexpected full action to compute the maximum pixel value.
- **OOM / Driver Crash on Large Rasters:** Attempting to save a massive, highly-partitioned raster (especially after `explode`) in `"compatibility"` mode (the default single-file mode) instead of `"distributed"` mode.
- **Invalid Bit Compaction:** Trying to compact a `RasterRDD[Float]` to 8-bit or 16-bit. Float rasters will ignore this and always save as 32-bit.

### Fix Code Hint
```scala
// BAD: Forces a full dataset scan to determine bit depth for compaction
GeoTiffWriter.saveAsGeoTiff(landCoverRDD, "output.tif", GeoTiffWriter.CompactBits -> true)

// GOOD: Explicitly provides BitsPerSample to avoid the scan
GeoTiffWriter.saveAsGeoTiff(landCoverRDD, "output.tif", 
  Seq(GeoTiffWriter.CompactBits -> true, GeoTiffWriter.BitsPerSample -> 8))

// BAD: Saving an exploded raster as a single file (can cause OOM)
explodedRaster.saveAsGeoTiff("huge_output")

// GOOD: Saving an exploded raster in distributed mode
GeoTiffWriter.saveAsGeoTiff(explodedRaster, "huge_output", GeoTiffWriter.WriteMode -> "distributed")
```

## API Test: `saveAsIndex`

### Signature
```scala
def saveAsIndex(indexPath: String, oformat: String = "rtree"): Unit
def saveAsIndex(partitionedRDD: JavaPartitionedSpatialRDD, indexPath: String): Unit
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/indexing/IndexMixin.scala:92  (+1 more definition site/overload)_

### Goal
Writes a spatially partitioned RDD to disk as a set of files (one for each partition) and generates a `_master` file that stores spatial metadata about the partitions for efficient future querying.

### Parameters
- `indexPath` (`String`): The output directory path where the partitioned files and the `_master` index file will be written.
- `oformat` (`String`), default `"rtree"`: The format of the local index to build within each partition file.

### Input
A spatially partitioned RDD of vector features. The RDD **must** be partitioned prior to calling this method using a spatial partitioner (e.g., `rdd.spatialPartition(classOf[RSGrovePartitioner])` or `rdd.partitionBy(...)`). If downstream tasks require disjoint partitions to avoid duplicate results, you must use a partitioner that supports disjoint partitioning (`GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, or `STRPartitioner`).

### Output
Returns `Unit` — writes the partitioned data and a `_master` index file to the specified `indexPath` on the file system.

### Valid Call Patterns
```scala
// Indexing a dataset after spatial partitioning (from project README)
sparkContext.shapefile("ne_10m_admin_1_states_provinces.zip")
    .partitionBy(classOf[RSGrovePartitioner])
    .saveAsIndex("provinces_index", "rtree")

// Alternative using spatialPartition (based on test suite sibling patterns)
val data = sparkContext.readCSVPoint("points.csv")
val partitionedData = data.spatialPartition(classOf[RSGrovePartitioner])
partitionedData.saveAsIndex("points_index", "rtree")
```

### LLM Instruction Prompt
- ALWAYS ensure the RDD is spatially partitioned (e.g., via `spatialPartition` or `partitionBy`) before calling `saveAsIndex`.
- Use the instance method syntax `rdd.saveAsIndex(path, format)` for Scala RDDs.
- Do not invent file paths; use the exact output path provided by the user.
- If the user requires disjoint partitions, explicitly use `RSGrovePartitioner`, `GridPartitioner`, `KDTreePartitioner`, or `STRPartitioner` before saving.

### Prompt Snippet
```text
To persist a spatially partitioned RDD with an index, use `rdd.saveAsIndex(indexPath: String, oformat: String = "rtree")`. The RDD MUST be partitioned first (e.g., `rdd.spatialPartition(classOf[RSGrovePartitioner])`). This writes one file per partition plus a `_master` metadata file.
```

### Common Failure Modes
- **Missing Partitioning:** Calling `saveAsIndex` directly on an unpartitioned RDD (like the immediate output of `sc.shapefile`) will fail or produce an invalid index. It requires a spatially partitioned RDD.
- **Overlapping Partitions for Strict Queries:** Using a non-disjoint partitioner before saving, which can lead to duplicate results in custom algorithms or range queries loaded from this index later.

### Fix Code Hint
```scala
// WRONG: Calling saveAsIndex on an unpartitioned RDD
val features = sparkContext.shapefile("data.zip")
features.saveAsIndex("output_index") // Missing spatial partitioning

// CORRECT: Spatially partition the RDD first
val partitionedFeatures = features.spatialPartition(classOf[RSGrovePartitioner])
partitionedFeatures.saveAsIndex("output_index", "rtree")
```

## API Test: `saveAsKML`

### Signature
```scala
def saveAsKML(filename: String): Unit
def saveAsKML(rdd: JavaSpatialRDD, filename: String): Unit
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:86  (+1 more definition site/overload)_

_Source doc:_ Save features in KML format @param filename the name of the output file

### Goal
Save a distributed collection of spatial vector features to disk in KML (Keyhole Markup Language) format, typically for visualization in GIS software or virtual globes.

### Parameters
- `rdd` (`JavaSpatialRDD`): The spatial RDD containing the vector features to be saved. This parameter is only used in the Java API overload (`JavaSpatialRDDHelper.saveAsKML`). In Scala, the RDD is the implicit receiver.
- `filename` (`String`): The destination file path or directory name where the KML output will be written.

### Input
A spatial RDD containing vector geometries (e.g., `RDD[IFeature]` in Scala or `JavaSpatialRDD` in Java). The input must consist of vector data (points, lines, polygons) loaded from formats like Shapefile, GeoJSON, or CSV, or generated via vector operations (like spatial joins or summaries). It cannot be a `RasterRDD`.

### Output
Returns `Unit` — this is a terminal action that triggers Spark job execution and writes the vector features to the specified `filename` as KML data.

### Valid Call Patterns
```scala
// Scala (called as an extension method on a Spatial RDD)
records.saveAsKML("output.kml")

// Java (called via the static helper)
JavaSpatialRDDHelper.saveAsKML(records, "output.kml")
```

### LLM Instruction Prompt
- Use `saveAsKML(filename)` as an extension method on vector RDDs (`RDD[IFeature]`) in Scala to export geometries to KML.
- For Java pipelines, use the static method `JavaSpatialRDDHelper.saveAsKML(rdd, filename)`.
- NEVER call `saveAsKML` on a `RasterRDD`. KML is strictly a vector output format in Beast; rasters must be saved using `saveAsGeoTiff`.

### Prompt Snippet
```text
To export vector features to KML in Beast, use `rdd.saveAsKML("path.kml")` in Scala or `JavaSpatialRDDHelper.saveAsKML(rdd, "path.kml")` in Java. Do not use this method for raster data (use `saveAsGeoTiff` instead).
```

### Common Failure Modes
- **Type Mismatch (Raster vs. Vector):** Attempting to call `saveAsKML` on a `RasterRDD` (e.g., after `sc.geoTiff` or `mapPixels`). KML is a vector-only format.
- **Missing Implicits in Scala:** If `saveAsKML` is not resolved on an `RDD[IFeature]`, the Beast SparkContext implicits may not be imported, preventing the extension method from being attached to the RDD.

### Fix Code Hint
```scala
// INCORRECT: Attempting to save a RasterRDD as KML
// val raster = sc.geoTiff[Int]("input.tif")
// raster.saveAsKML("output.kml") // Fails: KML is for vectors

// CORRECT: Saving vector features (e.g., from a Shapefile) as KML
import edu.ucr.cs.bdlab.beast._
val records = sc.shapefile("ne_10m_admin_0_countries.zip")
records.saveAsKML("countries_output.kml")
```

## API Test: `saveAsShapefile`

### Signature
```scala
def saveAsShapefile(filename: String, opts: BeastOptions = new BeastOptions()): Unit
def saveAsShapefile(rdd: JavaSpatialRDD, filename: String): Unit
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:194  (+1 more definition site/overload)_

_Source doc:_ Save features as a shapefile @param filename the output filename

### Goal
Save a distributed collection of spatial vector features (an RDD) to disk as an Esri Shapefile.

### Parameters
- `filename` (`String`): The output path and filename where the shapefile will be written (e.g., `"output.shp"` or a compressed `"output.zip"`).
- `opts` (`BeastOptions`), default `new BeastOptions()`: Optional configuration parameters to customize the write behavior.

### Input
A `SpatialRDD` (in Scala) or `JavaSpatialRDD` (in Java) containing vector features (points, lines, or polygons). This operation is strictly for vector data and cannot be used directly on raster data (`RasterRDD`).

### Output
Returns `Unit` — The operation produces no return value. Its side effect is writing the vector features to the specified file path as an Esri Shapefile (compressed `.zip` or uncompressed).

### Valid Call Patterns
```scala
// Scala (as an extension method on a SpatialRDD)
records.saveAsShapefile("output.shp")

// Java (using the helper class)
JavaSpatialRDDHelper.saveAsShapefile(records, "output.shp");
```

### LLM Instruction Prompt
- When saving vector features to a Shapefile in Scala, use the extension method `rdd.saveAsShapefile(filename)`.
- When writing Java code, use the static method `JavaSpatialRDDHelper.saveAsShapefile(rdd, filename)`.
- Never invent file paths; strictly use the output filename provided in the task.
- Ensure the dataset being saved is a vector RDD (e.g., `RDD[IFeature]`), not a `RasterRDD`. If you have raster data, use `saveAsGeoTiff` instead.

### Prompt Snippet
```text
To save vector features as a Shapefile in Beast:
Scala: `vectorRdd.saveAsShapefile("path/to/output.shp")`
Java: `JavaSpatialRDDHelper.saveAsShapefile(vectorRdd, "path/to/output.shp");`
Do not use this on RasterRDDs. Never invent file paths.
```

### Common Failure Modes
- **Type Mismatch (Raster vs Vector):** Attempting to call `saveAsShapefile` on a `RasterRDD` or `RDD[ITile[T]]`. Shapefiles only support vector geometries.
- **Missing Java Helper:** Attempting to call `rdd.saveAsShapefile(...)` in Java instead of using `JavaSpatialRDDHelper.saveAsShapefile(rdd, ...)`.

### Fix Code Hint
```scala
// WRONG: Calling saveAsShapefile on a RasterRDD
val raster = sc.geoTiff[Int]("input.tif")
raster.saveAsShapefile("output.shp") // Fails: RasterRDD does not support saveAsShapefile

// RIGHT: Calling saveAsShapefile on a Vector RDD
val vectors: RDD[IFeature] = sc.shapefile("input.zip")
val filtered = vectors.filter(f => f.getAsGeom.getArea > 100)
filtered.saveAsShapefile("output.shp")
```

## API Test: `saveAsWKTFile`

### Signature
```scala
def saveAsWKTFile(filename: String, wktColumn: Int, delimiter: Char = '\t', header: Boolean = true): Unit
def saveAsWKTFile(rdd: JavaSpatialRDD, filename: String, wktColumn: Int, delimiter: Char, header: Boolean): Unit
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:79  (+1 more definition site/overload)_

_Source doc:_ Save features to a CSV file where the geometry is encoded in WKT format @param filename the name of the output file @param wktColumn the index of the column that contains the WKT attribute @param delimiter the delimiter between attributes, tab by default @param header whether to write a header line or not, true by default

### Goal
Save a distributed collection of spatial features to a CSV or TSV file where the vector geometry is encoded in Well-Known Text (WKT) format.

### Parameters
- `rdd` (`JavaSpatialRDD`): (Java API overload only) The distributed collection of spatial features to be saved. In Scala, this method is called directly on the RDD as an extension method.
- `filename` (`String`): The path or name of the output file/directory where the data will be written.
- `wktColumn` (`Int`): The zero-based index of the column that will contain the WKT geometry string in the output file.
- `delimiter` (`Char`): The character used to separate attributes in the output file (defaults to `\t` for tab-separated values).
- `header` (`Boolean`): Whether to write a header line containing attribute names at the top of the file (defaults to `true`).

### Input
A Spatial RDD (`RDD[IFeature]` in Scala or `JavaSpatialRDD` in Java) containing vector geometries and their associated attributes. The caller must provide a valid output path (`filename`) that does not already exist, as per standard Spark behavior.

### Output
Returns `Unit` — writes the spatial features to the specified `filename` path as a distributed text file (typically a directory containing `part-xxxxx` files) formatted as CSV/TSV with WKT geometries.

### Valid Call Patterns
```scala
// Scala: Called as an extension method on a Spatial RDD
records.saveAsWKTFile("output.csv", 0, '\t', false)

// Java: Called via the JavaSpatialRDDHelper utility class
JavaSpatialRDDHelper.saveAsWKTFile(records, "output.csv", 0, '\t', false)
```

### LLM Instruction Prompt
- Use `saveAsWKTFile` to export vector RDDs to a text-based format (CSV/TSV) with geometries represented as WKT strings.
- In Scala, call this as an extension method directly on the `RDD[IFeature]` (e.g., `rdd.saveAsWKTFile(...)`). Do not pass the RDD as the first argument in Scala.
- Always specify the `wktColumn` index to dictate where the geometry string should be placed in the output row.
- Remember that Spark will write this as a directory of part-files, not a single flat file, and the target path must not already exist.

### Prompt Snippet
```text
To export vector features to a CSV with WKT geometries in Beast, use the `saveAsWKTFile` extension method on the RDD. Specify the output path, the zero-based index for the WKT column, the delimiter, and whether to include a header. Example: `features.saveAsWKTFile("out_path", 0, ',', true)`.
```

### Common Failure Modes
- **Path Already Exists:** Spark will throw an exception if the `filename` directory already exists. Ensure the output path is clear before saving.
- **Invalid Column Index:** Providing a `wktColumn` index that is out of bounds for the feature's schema or desired output format.
- **Syntax Error in Scala:** Attempting to call `saveAsWKTFile(rdd, ...)` in Scala. The explicit `rdd` parameter is only for the `JavaSpatialRDDHelper` Java API. In Scala, it must be called as `rdd.saveAsWKTFile(...)`.

### Fix Code Hint
```scala
// WRONG: Calling the Java signature in Scala
saveAsWKTFile(myRdd, "output.csv", 0, ',', true)

// CORRECT: Using the Scala extension method
myRdd.saveAsWKTFile("output.csv", 0, ',', true)
```

## API Test: `saveFeatures`

### Signature
```scala
def saveFeatures(features: SpatialRDD, oFormat: String, outPath: String, opts: BeastOptions): Unit
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/SpatialWriter.scala:123_

_Source doc:_ Saves the given set of features to the output using the provided output format. @param features the set of features to store to the output @param oFormat the output format to use for writing @param outPath the path to write the output to @param opts user options to configure the writer

### Goal
Saves a distributed collection of spatial vector features (`SpatialRDD`) to a specified output path in a supported vector format (e.g., GeoJSON, Shapefile).

### Parameters
- `features` (`SpatialRDD`): The distributed dataset of spatial features (`RDD[IFeature]`) to be written to disk.
- `oFormat` (`String`): The short name of the output format to use (e.g., `"geojson"`, `"shapefile"`, `"csv"`, `"kml"`, `"kmz"`).
- `outPath` (`String`): The destination file or directory path where the output will be written.
- `opts` (`BeastOptions`): Configuration options for the writer, such as compression settings or format-specific flags.

### Input
The caller must provide a valid `SpatialRDD` containing vector geometries. The `oFormat` string must match one of Beast's supported vector output formats: CSV, Esri Shapefile, GeoJSON, JSON+WKT, KML, or KMZ. Note that this API is strictly for vector data; raster data (GeoTIFF/HDF) uses different save methods (e.g., `saveAsGeoTiff`).

### Output
Returns `Unit` — writes the features to the filesystem at `outPath`. Depending on the format and `BeastOptions`, this may produce a single file, a directory of partitioned files, or compressed archives (e.g., `.bz2` or `.zip`). For example, writing a `"shapefile"` will generate the required `.shp`, `.shx`, and `.dbf` files.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast.io.SpatialWriter
import edu.ucr.cs.bdlab.beast.common.BeastOptions

// Example 1: Save features as a GeoJSON file
SpatialWriter.saveFeatures(features, "geojson", "output_path.geojson", new BeastOptions())

// Example 2: Save features as an Esri Shapefile
SpatialWriter.saveFeatures(features, "shapefile", "output_path.shp", new BeastOptions())
```

### LLM Instruction Prompt
- Always call `saveFeatures` statically on the `SpatialWriter` object, not as a method on the RDD itself.
- Ensure `oFormat` is a supported vector output format string (e.g., `"geojson"`, `"shapefile"`, `"csv"`, `"kml"`, `"kmz"`).
- Always provide a `BeastOptions` instance for the `opts` parameter, even if no special configuration is needed (use `new BeastOptions()`).
- Do not use this method for saving raster data; use `saveAsGeoTiff` for `RasterRDD`.

### Prompt Snippet
```text
To save a SpatialRDD of vector features to disk, use `SpatialWriter.saveFeatures(features, format, path, new BeastOptions())`. Supported formats include "geojson", "shapefile", "csv", "kml", and "kmz".
```

### Common Failure Modes
- **Calling on the RDD:** Attempting to call `features.saveFeatures(...)` will fail compilation. It must be called via `SpatialWriter.saveFeatures(...)`.
- **Missing Options Parameter:** Forgetting to pass the fourth argument (`opts: BeastOptions`) will cause a signature mismatch.
- **Unsupported Format:** Passing a raster format like `"geotiff"` or an unrecognized string to `oFormat` will cause a runtime failure, as this writer is designed for vector features.

### Fix Code Hint
```scala
// WRONG: features.saveFeatures("shapefile", "out.shp")
// WRONG: SpatialWriter.saveFeatures(features, "shapefile", "out.shp") // Missing BeastOptions

// RIGHT: 
SpatialWriter.saveFeatures(features, "shapefile", "out.shp", new BeastOptions())
```

## API Test: `saveIndex2`

### Signature
```scala
def saveIndex2(partitionFeatures: SpatialRDD, path: String, opts: BeastOptions): Unit
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/indexing/IndexHelper.scala:541_

_Source doc:_ Saves a partitioned RDD to disk. Each partition is stored to a separate file and an additional master file that stores the partition information. @param partitionFeatures a set of partitioned features @param path the path to store the files @param opts additional options for storing the data

### Goal
Saves a spatially partitioned RDD of vector features to disk, writing each partition to a separate file alongside a master index file that stores the partition boundaries and metadata.

### Parameters
- `partitionFeatures` (`SpatialRDD`): The spatially partitioned RDD of vector features (`RDD[IFeature]`) to be saved.
- `path` (`String`): The destination directory path where the partition files and the master index file will be written.
- `opts` (`BeastOptions`): Additional configuration options for storing the data, such as specifying the output format (e.g., `"oformat" -> "wkt(0)"`).

### Input
- **Data:** A `SpatialRDD` containing vector geometries.
- **Preconditions:** The input RDD **must** be spatially partitioned prior to calling this method (e.g., using `rdd.spatialPartition(classOf[RSGrovePartitioner])` or `IndexHelper.partitionFeatures2`). The RDD must have a defined `SpatialPartitioner` so that the master index file can be generated correctly.
- **Formats:** Output formats are controlled via `opts`. Valid vector output formats include CSV (WKT/points), Esri Shapefile, GeoJSON, KML, and KMZ.

### Output
Returns `Unit` — writes a directory to the specified `path` containing individual data files for each spatial partition and a master index file (which stores the partition information for optimized future loading).

### Valid Call Patterns
```scala
// Authoritative usage from the project test suite
val partitionedFeatures: RDD[IFeature] = IndexHelper.partitionFeatures2(features, 
  new GridPartitioner(new EnvelopeNDLite(2, 0.0, 0.0, 4.0, 4.0), Array(2, 2)))

val outPath = new File(scratchDir, "index")
IndexHelper.saveIndex2(partitionedFeatures, outPath.getPath, "oformat" -> "wkt(0)")
```

### LLM Instruction Prompt
- Call `saveIndex2` statically via the `IndexHelper` object (i.e., `IndexHelper.saveIndex2(...)`).
- **Crucial Precondition:** Ensure the input `SpatialRDD` is spatially partitioned before calling this method.
- Pass output format options via `BeastOptions`. If implicit conversions are in scope, a tuple like `"oformat" -> "wkt(0)"` or `"oformat" -> "csv"` can be passed directly as the `opts` argument.

### Prompt Snippet
```text
Use `IndexHelper.saveIndex2(partitionedRDD, path, opts)` to save a spatially partitioned vector RDD to disk along with a master index file. The RDD must be partitioned first (e.g., via `spatialPartition`).
```

### Common Failure Modes
- **Unpartitioned RDD:** Passing an RDD that lacks a `SpatialPartitioner`. The method expects the RDD to be partitioned so it can extract partition boundaries for the master index file.
- **Path Already Exists:** Spark will throw an exception if the target output directory already exists.
- **Missing Implicits for Options:** If Beast's implicit conversions are not in scope, passing a tuple like `"oformat" -> "wkt(0)"` will fail to compile. In such cases, explicitly instantiate the options object: `new BeastOptions().set("oformat", "wkt(0)")`.

### Fix Code Hint
```scala
// FIX: Ensure the RDD is partitioned before saving, and call via IndexHelper
val partitioned = features.spatialPartition(classOf[RSGrovePartitioner])
IndexHelper.saveIndex2(partitioned, "output_path", new BeastOptions().set("oformat", "geojson"))
```

## API Test: `saveTiles`

### Signature
```scala
def saveTiles(tiles: JavaPairRDD[java.lang.Long, IntermediateVectorTile], outPath: String, opts: BeastOptions): Unit
def saveTiles(tiles: RDD[(Long, IntermediateVectorTile)], outPath: String, opts: BeastOptions): Unit
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/MVTDataVisualizer.scala:453  (+1 more definition site/overload)_

_Source doc:_ Save an RDD of tiles to the given output @param tiles   the set of tiles to save @param outPath the path to save the tiles to

### Goal
Saves a distributed RDD of intermediate Mapbox Vector Tiles (MVT) to a specified output path for web-based map visualization.

### Parameters
- `tiles` (`JavaPairRDD[java.lang.Long, IntermediateVectorTile]`): The distributed set of vector tiles to save, where the key is an encoded tile ID (Long) and the value is the intermediate tile data.
- `outPath` (`String`): The destination file system path where the MVT vector tile archive or directory structure will be written.
- `opts` (`BeastOptions`): Configuration options for the Beast environment and writer settings.

### Input
Requires an RDD of `(Long, IntermediateVectorTile)` pairs. This data is typically produced by upstream visualization APIs (such as `MVTDataVisualizer.plotAllTiles` or similar plotting functions) that convert raw vector geometries into tiled vector formats. 

### Output
Returns `Unit` — writes the provided tiles to the filesystem at `outPath` as MVT (Mapbox Vector Tiles) data.

### Valid Call Patterns
```scala
// Inferred from signature and sibling MVTDataVisualizer methods
import edu.ucr.cs.bdlab.beast.common.BeastOptions
import edu.ucr.cs.bdlab.davinci.MVTDataVisualizer

// Assuming `tiles` is an existing RDD[(Long, IntermediateVectorTile)]
val opts = new BeastOptions()
MVTDataVisualizer.saveTiles(tiles, "output_mvt_path", opts)
```

### LLM Instruction Prompt
- Call `MVTDataVisualizer.saveTiles(tiles, outPath, opts)` to write an RDD of intermediate vector tiles to disk.
- Do not call this on raw `RDD[IFeature]` or `RasterRDD`; the data must first be converted to `IntermediateVectorTile` using the visualization API.
- Always use the `MVTDataVisualizer` object as the receiver; `saveTiles` is not an implicit method on the RDD itself.

### Prompt Snippet
```text
To save generated vector tiles, use `MVTDataVisualizer.saveTiles(tilesRDD, outPath, opts)`. Ensure the input is an `RDD[(Long, IntermediateVectorTile)]` and not raw features.
```

### Common Failure Modes
- **Type Mismatch:** Attempting to pass an `RDD[IFeature]` or `RasterRDD` directly to `saveTiles`. It strictly requires `RDD[(Long, IntermediateVectorTile)]`.
- **Missing Object Qualifier:** Calling `saveTiles(...)` as a bare function or attempting to call it as an RDD extension method (e.g., `tiles.saveTiles(...)`) instead of `MVTDataVisualizer.saveTiles(...)`.

### Fix Code Hint
```scala
// WRONG: Calling as an RDD method or passing raw features
// features.saveTiles("output_path", new BeastOptions())

// RIGHT: Calling on the MVTDataVisualizer object with the correct tile RDD
MVTDataVisualizer.saveTiles(tiles, "output_path", new BeastOptions())
```

## API Test: `saveTilesCompact`

### Signature
```scala
def saveTilesCompact(tiles: JavaPairRDD[java.lang.Long, IntermediateVectorTile], outPath: String, _opts: BeastOptions): Unit
def saveTilesCompact(tiles: RDD[(Long, IntermediateVectorTile)], outPath: String, _opts: BeastOptions): Unit
```
_Source: beast/visualization/src/main/scala/edu/ucr/cs/bdlab/davinci/MVTDataVisualizer.scala:495  (+1 more definition site/overload)_

_Source doc:_ A wrapper around [[saveTilesCompact()]]. Saves all the given tiles to a ZIP file. @param tiles   the set of tiles ot visualize @param outPath the path of the output ZIP file @param _opts   additional options that were used for visualization.

### Goal
Saves a distributed collection of intermediate Mapbox Vector Tiles (MVT) into a single compact ZIP archive for web-based exploration and serving.

### Parameters
- `tiles` (`JavaPairRDD[java.lang.Long, IntermediateVectorTile]` or `RDD[(Long, IntermediateVectorTile)]`): The distributed set of intermediate vector tiles to save, keyed by their encoded tile ID.
- `outPath` (`String`): The destination file path where the output ZIP archive will be written (e.g., `"provinces_mvt.zip"`).
- `_opts` (`BeastOptions`): Additional configuration options that were used during the visualization/plotting phase (e.g., threshold settings).

### Input
- **Data/Formats:** Requires an RDD of intermediate vector tiles, which is typically generated by calling `MVTDataVisualizer.plotAllTiles(...)` on a vector dataset (like a Shapefile or GeoJSON). 
- **Preconditions:** The input vector data used to generate the tiles should ideally be spatially partitioned and indexed (e.g., using `RSGrovePartitioner` and saved as an rtree index) for efficient multilevel visualization. The `_opts` provided here should match the options used when generating the tiles.

### Output
Returns `Unit` — writes a ZIP file containing the MVT vector tile archive to the specified `outPath`. This archive can be served by the BeastServer or other MVT-compatible web map servers.

### Valid Call Patterns
```scala
// Define visualization options
val opts: BeastOptions = "threshold" -> 0

// Generate the multilevel visualization tiles from vector features
val tiles = MVTDataVisualizer.plotAllTiles(features, levels=0 to 6, resolution=256, buffer=5, opts)

// Save the tiles to a compact ZIP archive
MVTDataVisualizer.saveTilesCompact(tiles, "provinces_mvt.zip", opts)
```

### LLM Instruction Prompt
- When saving Mapbox Vector Tiles (MVT) generated by Beast, always call `MVTDataVisualizer.saveTilesCompact(tiles, outPath, opts)`.
- Do NOT attempt to call `saveTilesCompact` as a method directly on the RDD (e.g., `tiles.saveTilesCompact(...)`); it is a method on the `MVTDataVisualizer` object.
- Always pass the exact same `BeastOptions` instance to `saveTilesCompact` that was used in the preceding `plotAllTiles` call to ensure consistency.
- The `outPath` should typically end with `.zip` as the output format is a ZIP archive containing the tile hierarchy.

### Prompt Snippet
```text
To save generated vector tiles, use `MVTDataVisualizer.saveTilesCompact(tiles, "output.zip", opts)`. Do not call it as an RDD method. Pass the same `BeastOptions` used during `plotAllTiles`.
```

### Common Failure Modes
- **Method Not Found on RDD:** Attempting to call `tiles.saveTilesCompact(...)` will fail compilation because `saveTilesCompact` is not an implicit extension on `RDD`; it must be called on the `MVTDataVisualizer` object.
- **Mismatched Options:** Passing a new, empty `BeastOptions` instead of the one used during `plotAllTiles` can result in missing metadata or incorrect tile formatting in the final archive.
- **Invalid Output Path:** Providing an output path for a directory instead of a file path (e.g., ending in `.zip`) may cause write errors, as the function explicitly writes a single ZIP file.

### Fix Code Hint
```scala
// WRONG: Calling as an RDD method
tiles.saveTilesCompact("output_mvt.zip", opts)

// RIGHT: Calling on the MVTDataVisualizer object
MVTDataVisualizer.saveTilesCompact(tiles, "output_mvt.zip", opts)
```

## API Test: `selectFiles`

### Signature
```scala
def selectFiles(fileSystem: FileSystem, dir: String, range: Geometry): Array[String]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterFileRDD.scala:233_

_Source doc:_ Selects all the raster files that could potentially overlap the given query range from a directory of files. If that directory contains an index file, i.e., "_index.csv", then this index is used to prune files that are not relevant. If no index file is there, then all files are returned. @param fileSystem the file system at which the raster files exist @param dir the directory that contains the raster files @param range the query range to limit the files @return the list of files that potentially overlap the given query range

### Goal
Selects raster files from a directory that potentially overlap a given spatial query range, utilizing an optional `_index.csv` file for efficient pruning.

### Parameters
- `fileSystem` (`FileSystem`): The Hadoop `FileSystem` instance where the raster files reside (typically obtained via `FileSystem.get(sparkContext.hadoopConfiguration)`).
- `dir` (`String`): The path to the directory containing the raster files (and optionally the `_index.csv` file).
- `range` (`Geometry`): A JTS `Geometry` representing the spatial query range (e.g., a bounding box or polygon) used to limit the returned files.

### Input
A directory containing raster files (such as GeoTIFFs or HDFs) accessible via the provided Hadoop `FileSystem`. For the spatial pruning to work, the directory must contain an index file named `_index.csv` (usually generated via `RasterFileRDD.buildIndex`). If this index file is missing, the function will fall back to returning all files in the directory. The `range` parameter must be a valid JTS `Geometry` (often created from a JTS `Envelope`).

### Output
Returns `Array[String]` — An array of file paths (as strings) pointing to the raster files in the directory that potentially overlap the provided query range.

### Valid Call Patterns
```scala
// Assuming sparkContext is an initialized SparkContext and dir is a valid directory path
val geometryFactory = new GeometryFactory(new PrecisionModel(PrecisionModel.FLOATING_SINGLE), 4326)
val queryRange = geometryFactory.toGeometry(new Envelope(-100, -99, 27, 28))

val matchingFiles = RasterFileRDD.selectFiles(
  FileSystem.get(sparkContext.hadoopConfiguration), 
  dir.toString,
  queryRange
)
```

### LLM Instruction Prompt
- Call `selectFiles` on the `RasterFileRDD` object.
- Pass a valid Hadoop `FileSystem` object, the directory path as a `String`, and a JTS `Geometry` for the spatial range.
- Note that this function relies on the presence of an `_index.csv` file in the target directory to actually prune files; otherwise, it returns all files. If pruning is required, ensure `RasterFileRDD.buildIndex` is called beforehand.

### Prompt Snippet
```text
To find raster files overlapping a spatial range without loading them all into memory, use `RasterFileRDD.selectFiles(fileSystem, dir, geometry)`. It uses `_index.csv` in the directory to prune non-overlapping files, returning an Array[String] of matching file paths.
```

### Common Failure Modes
- **Silent Fallback (No Pruning):** Expecting the function to filter files when no `_index.csv` exists in the directory. The function will silently return all files instead of failing.
- **Uninitialized FileSystem:** Passing a null or improperly configured `FileSystem` object, which will cause runtime exceptions when attempting to read the directory or index file.
- **CRS Mismatch:** Providing a `Geometry` range in a Coordinate Reference System (CRS) that does not match the CRS of the bounding boxes stored in the `_index.csv`, leading to incorrect pruning (either missing files or returning non-overlapping files).

### Fix Code Hint
```scala
// Ensure the index is built before querying to guarantee pruning behavior
RasterFileRDD.buildIndex(sparkContext, dir.toString, new File(dir, "_index.csv").toString)

// Obtain the FileSystem from the SparkContext
val fs = FileSystem.get(sparkContext.hadoopConfiguration)

// Query the files
val matchingFiles = RasterFileRDD.selectFiles(fs, dir.toString, queryGeometry)
```

## API Test: `set`

### Signature
```scala
def set(key: String, value: Any): BeastOptions
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/common/BeastOptions.scala:83_

_Source doc:_ Set a key to any value by conerting it to string @param key key name @param value value @return

### Goal
Sets a configuration key to a specified value (converting it to a string) within a `BeastOptions` instance, used to configure Beast operations like data loading, summarization, or visualization.

### Parameters
- `key` (`String`): The configuration property name to set (e.g., `"iformat"`, `"skipheader"`, `"separator"`, `"stroke"`, `"fill"`).
- `value` (`Any`): The value to assign to the key. It accepts any type (e.g., `Boolean`, `String`, `Int`) and automatically converts it to a string representation internally.

### Input
An instantiated `BeastOptions` object. The caller must provide a valid configuration key recognized by the downstream Beast operation (e.g., `SpatialReader`, `GeometricSummary`, or plotting APIs) and the desired value.

### Output
Returns `BeastOptions` — The updated `BeastOptions` instance, allowing for fluent method chaining.

### Valid Call Patterns
```scala
// Configuring options for reading and summarizing a CSV/WKT file
val opts = new BeastOptions()
  .set("iformat", "wkt(Geometry)")
  .set("skipheader", true)
  .set("separator", "\t")

// Configuring options for visualization/plotting
val plotOpts = new BeastOptions()
  .set("stroke", "blue")
  .set("fill", "#9999e6")
```

### LLM Instruction Prompt
- Use `.set(key, value)` on a `BeastOptions` instance to configure Beast operations.
- Chain multiple `.set()` calls fluently.
- Pass primitive types (like `true`, `false`, or numbers) directly as the `value` argument; do not manually call `.toString`, as the method accepts `Any` and handles the string conversion internally.
- Ensure the `key` matches expected Beast configuration properties (e.g., `"iformat"` for input format, `"oformat"` for output format, `"skipheader"`, `"separator"`).

### Prompt Snippet
```text
To configure Beast operations, instantiate `new BeastOptions()` and chain `.set(key, value)` calls. The `value` parameter accepts `Any` and converts it to a string, so you can pass booleans or numbers directly (e.g., `.set("skipheader", true)`).
```

### Common Failure Modes
- **Silent failures from misspelled keys:** Providing an invalid or misspelled configuration key (e.g., `"format"` instead of `"iformat"`) will not throw an error during the `.set()` call, but the downstream operation will ignore it and fall back to default behavior.
- **Assuming type preservation:** Because `value` is converted to a string, passing complex objects expecting them to be retrieved as their original type later will fail.

### Fix Code Hint
```scala
// WRONG: Misspelled key and manual string conversion
val badOpts = new BeastOptions().set("format", "wkt(Geometry)").set("skipheader", "true")

// RIGHT: Correct keys and passing primitives directly
val goodOpts = new BeastOptions().set("iformat", "wkt(Geometry)").set("skipheader", true)
```

## API Test: `setBoolean`

### Signature
```scala
def setBoolean(key: String, value: Boolean): BeastOptions
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/common/BeastOptions.scala:141_

_Source doc:_ Set key to a boolean value @param key @param value @return

### Goal
Sets a boolean configuration property within a `BeastOptions` object, returning the updated options to enable fluent method chaining.

### Parameters
- `key` (`String`): The configuration property name to set (e.g., `"fs.file.impl.disable.cache"`).
- `value` (`Boolean`): The boolean flag (`true` or `false`) to assign to the specified key.

### Input
An instantiated `BeastOptions` object that needs to be configured before passing it to a Beast/RDPro operation.

### Output
Returns `BeastOptions` — the updated configuration object itself, allowing multiple `.setBoolean()` or other setter calls to be chained sequentially.

### Valid Call Patterns
```scala
// Inferred from the signature and adapted from test-suite configuration patterns
val opts = new BeastOptions()
opts.setBoolean("fs.file.impl.disable.cache", true)
    .setBoolean("spatial.join.broadcast", false)
```

### LLM Instruction Prompt
- When configuring Beast operations that require boolean flags, call `setBoolean(key, value)` on a `BeastOptions` instance. Remember that it returns the `BeastOptions` object, so you can chain multiple configuration calls fluently. Do not pass string representations of booleans (e.g., `"true"`).

### Prompt Snippet
```text
Use `opts.setBoolean("key", true)` to set boolean flags in BeastOptions. Chain calls fluently since it returns the BeastOptions instance.
```

### Common Failure Modes
- **Type Mismatch:** Passing a string `"true"` or `"false"` instead of a native Scala `Boolean`.
- **Confusing with Hadoop Configuration:** Assuming the method returns `Unit` (like Hadoop's `Configuration.setBoolean`) and failing to take advantage of the fluent API for cleaner code.

### Fix Code Hint
```scala
// WRONG: Passing a string instead of a boolean
opts.setBoolean("fs.file.impl.disable.cache", "true")

// RIGHT: Passing a native boolean and chaining
opts.setBoolean("fs.file.impl.disable.cache", true)
    .setBoolean("another.flag", false)
```

## API Test: `setLong`

### Signature
```scala
def setLong(key: String, value: Long): BeastOptions
```
_Source: beast/common/src/main/scala/edu/ucr/cs/bdlab/beast/common/BeastOptions.scala:122_

_Source doc:_ Set a key to a long value @param key @param value @return

### Goal
Sets a configuration key to a 64-bit integer (`Long`) value within a `BeastOptions` instance, used to parameterize Beast operations like multilevel plotting, spatial data loading, or algorithm tuning.

### Parameters
- `key` (`String`): The configuration property name to set (e.g., `"threshold"`).
- `value` (`Long`): The numeric value to assign to the specified property.

### Input
An existing or newly instantiated `BeastOptions` object. The `key` must be a valid configuration string recognized by the downstream Beast operation (such as visualization or spatial partitioning). 

### Output
Returns `BeastOptions` — The updated `BeastOptions` instance itself, enabling fluent method chaining.

### Valid Call Patterns
```scala
// From the project's documented usage for configuring a multilevel plot
val opts = new BeastOptions()
  .set("stroke", "blue")
  .set("fill", "#9999E6")
  .setLong("threshold", 0)
```

### LLM Instruction Prompt
- When configuring Beast operations (like `MultilevelPlot.plotFeatures`) that require numeric parameters, use `setLong(key, value)` on a `BeastOptions` instance. Because it returns `BeastOptions`, always chain it fluently with other `.set()` or `.setLong()` calls. Do not confuse this with `sparkContext.hadoopConfiguration.setLong`, which returns `Unit` and cannot be chained.

### Prompt Snippet
```text
Use `.setLong("key", value)` on a `BeastOptions` instance to configure numeric parameters for Beast operations. Chain it fluently with other configuration methods (e.g., `new BeastOptions().set("color", "red").setLong("threshold", 100L)`).
```

### Common Failure Modes
- **Type Mismatch:** Passing a `String` (e.g., `"0"`) instead of a numeric `Long` or `Int` value, which will cause a compilation error.
- **Chaining Hadoop Configuration:** Attempting to chain `setLong` calls on `sparkContext.hadoopConfiguration`. While Hadoop's configuration also has a `setLong` method, it returns `Unit` (void) and will break the chain, unlike `BeastOptions.setLong`.

### Fix Code Hint
```scala
// Incorrect: Passing a string instead of a Long
// val opts = new BeastOptions().setLong("threshold", "0")

// Incorrect: Attempting to chain Hadoop's Configuration
// sparkContext.hadoopConfiguration.setLong(SpatialFileRDD.MaxSplitSize, 1024).setBoolean(...)

// Correct: Chaining on BeastOptions with a valid numeric type
val opts = new BeastOptions()
  .set("stroke", "blue")
  .setLong("threshold", 0L)

// Correct: Sequential calls for Hadoop Configuration (no chaining)
sparkContext.hadoopConfiguration.setLong(SpatialFilePartitioner.MaxSplitSize, 500L)
sparkContext.hadoopConfiguration.setBoolean("fs.file.impl.disable.cache", true)
```

## API Test: `setPixelValue`

### Signature
```scala
def setPixelValue(i: Int, j:Int, value: T): Unit
def setPixelValue(i: Int, j: Int, value: T): Unit
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/MemoryTile.scala:147  (+1 more definition site/overload)_

_Source doc:_ Sets the value of the given pixel @param i the column position of the pixel @param j the row position of the pixel @param value the value to set at the given pixel

### Goal
Mutates a specific pixel in a local raster tile (such as a `MemoryTile`) by setting its value at the given column and row coordinates.

### Parameters
- `i` (`Int`): The column position (x-coordinate) of the pixel within the tile.
- `j` (`Int`): The row position (y-coordinate) of the pixel within the tile.
- `value` (`T`): The value to set at the given pixel. The type must exactly match the tile's generic type parameter `T` (e.g., `Float` for single-band, `Array[Float]` for multi-band).

### Input
A mutable tile instance (e.g., `MemoryTile[T]`) that has been initialized with valid `RasterMetadata`. The coordinates `i` and `j` must fall within the tile's local dimensions. The type of the `value` provided must strictly align with the tile's runtime pixel type (e.g., `Int`, `Float`, `Array[Int]`, or `Array[Float]`).

### Output
Returns `Unit` — this is an in-place mutation that updates the internal pixel array of the tile.

### Valid Call Patterns
```scala
// Single-band tile mutation
val tile1 = new MemoryTile[Float](0, metadata, RasterFeature.create(Array("fileName"), Array("testFile.tif")))
tile1.setPixelValue(0, 0, 0.5f)
tile1.setPixelValue(1, 0, 0.25f)

// Multi-band tile mutation
val tile2 = new MemoryTile[Array[Float]](0, metadata, RasterFeature.create(Array("fileName"),Array("testFile.tif")))
tile2.setPixelValue(0, 0, Array(0.5f, 0.1f))
tile2.setPixelValue(1, 0, Array(0.25f, 0.4f))
```

### LLM Instruction Prompt
- When mutating a local raster tile (like `MemoryTile[T]`), use `tile.setPixelValue(i, j, value)`. 
- Ensure the type of `value` exactly matches the tile's type parameter `T`. Do not pass a scalar `Float` to a `MemoryTile[Array[Float]]`, and do not pass an `Int` to a `MemoryTile[Float]`.
- Remember that `i` represents the column (x) and `j` represents the row (y).
- This is a local, low-level tile operation, not a distributed `RasterRDD` operation.

### Prompt Snippet
```text
To set a pixel value in a local RDPro tile, use `tile.setPixelValue(i, j, value)`. Ensure `value` matches the tile's generic type `T` (e.g., `Float` for single-band, `Array[Float]` for multi-band). `i` is the column index and `j` is the row index.
```

### Common Failure Modes
- **Type Mismatch:** Passing an integer (e.g., `5`) to a `MemoryTile[Float]`, which expects a `Float` (e.g., `5.0f`). Scala's strict typing requires exact matches for generic type `T`.
- **Multi-band vs Single-band Confusion:** Attempting to pass a single numeric value to a multi-band tile (`MemoryTile[Array[Float]]`), which requires an `Array` of values.
- **Index Out of Bounds:** Providing `i` or `j` values that exceed the tile's width or height as defined by its `RasterMetadata`.

### Fix Code Hint
```scala
// BAD: Type mismatch (passing Int to a Float tile)
tile.setPixelValue(0, 0, 5) 

// GOOD: Match the generic type T exactly
tile.setPixelValue(0, 0, 5.0f)

// BAD: Passing a scalar to a multi-band tile
multiBandTile.setPixelValue(0, 0, 5.0f)

// GOOD: Passing an Array to a multi-band tile
multiBandTile.setPixelValue(0, 0, Array(5.0f, 2.0f))
```

## API Test: `shapefile`

### Signature
```scala
def shapefile(filename: String) : SpatialRDD
def shapefile(filename: String) : JavaSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:76  (+1 more definition site/overload)_

_Source doc:_ Reads features from an Esri Shapefile(c) @param filename the name of the .shp file, a compressed ZIP file that contains shapefiles, or a directory that contains shapefiles or ZIP files. @return an RDD of features

### Goal
Reads vector features from an Esri Shapefile into a distributed `SpatialRDD` for large-scale geospatial analysis, spatial joins, or raster-vector (Raptor) joins.

### Parameters
- `filename` (`String`): The path to the `.shp` file, a compressed `.zip` file that contains shapefiles, or a directory that contains shapefiles or ZIP files.

### Input
- Requires an initialized `SparkContext` (or `JavaSpatialSparkContext`) typically named `sc` or `sparkContext` with Beast context extensions loaded.
- The target file must be a valid Esri Shapefile format (either uncompressed `.shp`, compressed `.zip`, or a directory of these).
- Do not invent file paths; use only the paths provided by the user or environment.

### Output
Returns `SpatialRDD` — a distributed Spark RDD of vector features (`IFeature`) representing the geometries and attributes from the shapefile. For Java APIs, it returns a `JavaSpatialRDD`.

### Valid Call Patterns
```scala
// Load a compressed shapefile archive
val records = sparkContext.shapefile("input.zip")

// Load an uncompressed shapefile
val buildings = sc.shapefile("MSBuildings_data_index.shp")

// Typical usage in a Raptor Join pipeline
val countries: SpatialRDD = sc.shapefile("ne_10m_admin_0_countries.zip")
val join = treecover.raptorJoin(countries)
```

### LLM Instruction Prompt
- Always call `shapefile` as an extension method on an initialized `SparkContext` (e.g., `sc.shapefile(path)` or `sparkContext.shapefile(path)`). Do not call it as a standalone function.
- Pass the exact file path provided in the task; never invent file paths.
- Remember that `shapefile` natively supports reading compressed `.zip` archives containing shapefiles, so there is no need to unzip them manually before loading.

### Prompt Snippet
```text
Use `sc.shapefile(filename)` to load Esri Shapefiles (.shp, .zip, or directories) into a SpatialRDD. Call it as an extension on the SparkContext.
```

### Common Failure Modes
- **Missing Context Extension:** Attempting to call `shapefile` without importing Beast implicits, resulting in a "value shapefile is not a member of org.apache.spark.SparkContext" compilation error.
- **Invented File Paths:** Hardcoding a path like `"data.shp"` instead of using the variable provided in the user's prompt.
- **Incorrect Receiver:** Calling `shapefile(path)` directly instead of `sc.shapefile(path)`.

### Fix Code Hint
```scala
// Ensure Beast context extensions are imported to enable sc.shapefile
import edu.ucr.cs.bdlab.beast._

// Use the provided SparkContext (sc) and the provided file path variable
val features: SpatialRDD = sc.shapefile(providedFilePath)
```

## API Test: `sierpinski`

### Signature
```scala
def sierpinski(cardinality: Long): JavaSpatialRDD
def sierpinski(cardinality: Long): SpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/JavaSpatialGeneratorBuilder.scala:127  (+1 more definition site/overload)_

_Source doc:_ Generate data from the Sierpinski distribution @param cardinality the number of records to generate @return the RDD that contains the generated data

### Goal
Generate synthetic spatial data following a Sierpinski (fractal) distribution using Beast's Spider component, typically used for benchmarking and testing distributed spatial algorithms.

### Parameters
- `cardinality` (`Long`): The total number of spatial records (geometries/points) to generate across the Spark cluster.

### Input
Requires an initialized `SparkContext` (`sc`) or `JavaSpatialSparkContext` with Beast extensions loaded. The generator can optionally be pre-configured with a bounding box (MBR), random seed, or geometry type using the `SpatialGeneratorBuilder` before invoking `sierpinski`.

### Output
Returns `SpatialRDD` (or `JavaSpatialRDD` in the Java API) — A distributed Spark RDD containing the generated synthetic spatial features (e.g., points) distributed according to a Sierpinski triangle pattern.

### Valid Call Patterns
```scala
// Pattern 1: Direct generation using SparkContext extensions (from README)
val fractalData: SpatialRDD = sc.generateSpatialData
  .sierpinski(1000L)

// Pattern 2: Configured generation using the builder pattern (adapted from test suite)
val desiredMBR = new EnvelopeNDLite(0, 0, 100, 100)
val configuredFractalData: SpatialRDD = new SpatialGeneratorBuilder(sc)
  .mbr(desiredMBR)
  .config(SpatialGenerator.Seed, 1794)
  .sierpinski(1000000L)
```

### LLM Instruction Prompt
- When generating synthetic spatial data for benchmarking or testing, use `sc.generateSpatialData.sierpinski(cardinality)` to create a `SpatialRDD` with a Sierpinski fractal distribution. 
- Ensure the `cardinality` argument is a `Long`. 
- If specific bounds or seeds are required, chain `.mbr(...)` and `.config(...)` on a `SpatialGeneratorBuilder(sc)` before calling `.sierpinski(...)`.

### Prompt Snippet
```text
Use `sc.generateSpatialData.sierpinski(cardinality)` to generate a SpatialRDD of synthetic data following a Sierpinski distribution for benchmarking. Append `L` to large cardinality numbers.
```

### Common Failure Modes
- **Missing Context Extensions:** Attempting to call `sc.generateSpatialData` without importing Beast implicits, resulting in a "value generateSpatialData is not a member of org.apache.spark.SparkContext" compilation error.
- **Integer Overflow:** Passing a massive integer literal without the `L` suffix (e.g., `3000000000`) causing a compilation error before it even reaches the `Long` parameter.

### Fix Code Hint
```scala
// Ensure Beast implicits are imported to enable sc.generateSpatialData
import edu.ucr.cs.bdlab.beast._

// Append 'L' to the cardinality to ensure it is treated as a Long
val data = sc.generateSpatialData.sierpinski(5000000000L)
```

## API Test: `size`

### Signature
```scala
def size: Long
def size: Int
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/SpatialPartition.scala:41  (+2 more definition site/overload)_

_Source doc:_ Size in bytes

### Goal
Retrieves the size of a spatial object, representing either the memory footprint in bytes (e.g., for a `SpatialPartition`) or the total number of elements (e.g., for spatial join result collections and iterators).

### Parameters
_None._

### Input
A valid Beast spatial data structure, such as a `SpatialPartition` (to get byte size), or a collection/iterator of spatial join results like `PlaneSweepSpatialJoinIterator` or an `Array` of features (to get element count).

### Output
Returns `Long` — The size in bytes when called on specific spatial data structures (like partitions). The overloaded `def size: Int` returns the number of elements when called on standard collections or spatial iterators.

### Valid Call Patterns
```scala
// 1. Element count on an array of spatial join results (from test suite)
val results = SpatialJoin.spatialJoinIntersectsPlaneSweepFeatures(r.toArray, s.toArray,
  new EnvelopeNDLite(2, 2.0, 0.0, 5.0, 3.0), ESJPredicate.Intersects, null)
val count: Int = results.size

// 2. Element count on a spatial join iterator (from test suite)
val joinResults = new PlaneSweepSpatialJoinIterator(s1, s2, null)
val iteratorCount: Int = joinResults.size

// 3. Size in bytes on a spatial partition (inferred from signature and source doc)
val byteSize: Long = partition.size
```

### LLM Instruction Prompt
- Use `.size` to determine the memory footprint (in bytes, returning `Long`) of Beast spatial partitions, or to count the number of elements (returning `Int`) in spatial join result arrays and iterators.
- **Warning:** When calling `.size` on a Scala `Iterator` (such as `PlaneSweepSpatialJoinIterator`), the iterator will be fully consumed. Do not call `.size` if you intend to iterate over the results afterward.

### Prompt Snippet
```text
Calculate the number of intersecting feature pairs from the `PlaneSweepSpatialJoinIterator` and store it in a variable, keeping in mind that this will consume the iterator.
```

### Common Failure Modes
- **Consuming Iterators:** Calling `.size` on a `PlaneSweepSpatialJoinIterator` or similar one-time traversal object exhausts the iterator. Subsequent attempts to map, filter, or collect the iterator will yield empty results.
- **Semantic Confusion:** Assuming `.size` always returns an element count. On core Beast partition objects (like `SpatialPartition`), it returns the estimated size in bytes (`Long`), not the number of features.

### Fix Code Hint
```scala
// BAD: Consumes the iterator, making the subsequent .toArray call return an empty array
val joinResults = new PlaneSweepSpatialJoinIterator(s1, s2, null)
println(s"Found ${joinResults.size} matches") 
val data = joinResults.toArray 

// GOOD: Convert to an array or collection first if you need both the size and the data
val joinResults = new PlaneSweepSpatialJoinIterator(s1, s2, null)
val data = joinResults.toArray
println(s"Found ${data.size} matches")
```

## API Test: `slidingWindow`

### Signature
```scala
def slidingWindow[T: ClassTag, U: ClassTag](raster: RasterRDD[T], w: Int, f: (Array[T], Array[Boolean]) => U): RasterRDD[U]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RasterOperationsFocal.scala:711_

_Source doc:_ Performs a sliding window calculation for a window of size (2w + 1) &times; (2w + 1) given an integer value w. The user-defined window calculation function takes all values in the window ordered in row-major order. Additionally, a Boolean array of the same size is passed to indicate which values are defined and which are not. The Boolean array is useful for two scenarios. 1. When the window is near the edge of the raster, there must be some undefined values outside the raster. 2. Some pixel values in raster might be undefined, e.g., due to cloud coverage. *Note*: This function will only work correctly if all input tiles have the same raster metadata. @param raster the input raster to process @param w the radius of the square window. The window size will be (2w + 1) &times; (2w + 1) @param f the function to perform the calculation. @tparam T the type of values in the input raster @tparam U the type of output values (the result of the user-defined function). @return a new raster with the same dimensions as the input after applying the window function.

### Goal
Performs a focal (neighborhood) operation over a raster by applying a user-defined function to a sliding window of size (2w + 1) × (2w + 1) around each pixel.

### Parameters
- `raster` (`RasterRDD[T]`): The input distributed raster dataset to process.
- `w` (`Int`): The radius of the square window. For example, `w = 1` creates a 3×3 window, `w = 2` creates a 5×5 window.
- `f` (`(Array[T], Array[Boolean]) => U`): The user-defined function applied to each window. It receives an array of pixel values in row-major order and a corresponding boolean array indicating which pixels are valid/defined (true) versus out-of-bounds or NoData (false).

### Input
A `RasterRDD[T]` loaded from a GeoTIFF or HDF file (e.g., via `sc.geoTiff[T]`), or generated via rasterization. 
**Precondition:** This function will only work correctly if all input tiles have the exact same raster metadata (resolution, CRS, and tile size). If the input raster has mixed metadata, you must align it first using the Reshape API (e.g., `RasterOperationsFocal.reshapeNN` or `reshapeAverage`).

### Output
Returns `RasterRDD[U]` — A new distributed raster with the same dimensions and metadata as the input, where each pixel's value is the computed result of the user-defined sliding window function.

### Valid Call Patterns
```scala
// Example: 3x3 window smoothing (average) over an integer raster
val smoothedRaster: RasterRDD[Double] = RasterOperationsFocal.slidingWindow(
  raster, 
  1, 
  (values: Array[Int], defined: Array[Boolean]) => {
    var sum: Int = 0
    var count: Int = 0
    for (i <- values.indices; if defined(i)) {
      sum += values(i)
      count += 1
    }
    if (count == 0) 0.0 else sum.toDouble / count
  }
)
```

### LLM Instruction Prompt
- Always call this function using the object qualifier: `RasterOperationsFocal.slidingWindow(raster, w, f)`.
- The window size is determined by the radius `w`. To get a 3x3 window, pass `w = 1`.
- The user-defined function `f` MUST check the `defined` boolean array before utilizing a value from the `values` array. This prevents errors at the edges of the raster or when encountering undefined pixels (like cloud coverage).
- Ensure the input `RasterRDD` has uniform tile metadata. If the data comes from disparate sources or unaligned tiles, instruct the user to use `RasterOperationsFocal.reshapeNN` or `reshapeAverage` prior to calling `slidingWindow`.

### Prompt Snippet
```text
To perform focal operations like smoothing or edge detection, use `RasterOperationsFocal.slidingWindow(raster, w, f)`. The radius `w` defines a (2w+1)x(2w+1) window. Your function `f` receives `(values, defined)` arrays; always check `if (defined(i))` before using `values(i)` to safely handle raster edges and NoData pixels.
```

### Common Failure Modes
- **Mismatched Tile Metadata:** Calling `slidingWindow` on a raster whose tiles have varying resolutions, CRSs, or sizes. This violates the precondition and yields incorrect spatial calculations.
- **Ignoring the `defined` Array:** Blindly iterating over the `values` array without checking the `defined` array, leading to skewed calculations (incorporating garbage/NoData values) or errors at the raster boundaries where the window extends outside the image.

### Fix Code Hint
```scala
// WRONG: Fails to check if the pixel is defined, leading to edge-case bugs
val badRaster = RasterOperationsFocal.slidingWindow(raster, 1, (vals, defs) => vals.sum / vals.length)

// CORRECT: Safely filters using the `defined` array
val goodRaster = RasterOperationsFocal.slidingWindow(raster, 1, (vals, defs) => {
  val validVals = vals.indices.filter(defs).map(vals)
  if (validVals.isEmpty) 0 else validVals.sum / validVals.length
})
```

## API Test: `spatialFile`

### Signature
```scala
def spatialFile(filename: String, format: String = null, opts: BeastOptions = new BeastOptions): SpatialRDD
def spatialFile(filename: String, opts: BeastOptions): SpatialRDD
def spatialFile(filename: String, iformat: String, opts: BeastOptions): JavaSpatialRDD
def spatialFile(filename: String, iformat: String): JavaSpatialRDD
def spatialFile(filename: String, opts: BeastOptions): JavaSpatialRDD
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/io/ReadWriteMixin.scala:46  (+4 more definition site/overload)_

_Source doc:_ Reads the given file according to the given spatial format. If spatial format is not given, it auto-detects the input based on the extension and then file contents (for CSV files only) @param filename the name of the file or directory of files @return the [[SpatialRDD]] that contains the records

### Goal
Reads a spatial vector file or directory of files into a distributed `SpatialRDD`, optionally auto-detecting the format based on the file extension and contents.

### Parameters
- `filename` (`String`): The path to the input file or directory of files (e.g., local file system or HDFS path).
- `format` (`String`), default `null`: The spatial format of the file (e.g., `"wkt"`, `"envelope"`, `"gpx"`, `"envelope(0,1,2,3)"`). If `null`, Beast attempts to auto-detect the format.
- `opts` (`BeastOptions`), default `new BeastOptions`: Additional configuration options for the reader, such as specifying a custom delimiter (e.g., `new BeastOptions("separator:,")`).

### Input
- **Data/Formats:** Supported vector input formats include CSV (points, WKT, envelopes), Esri Shapefile (compressed `.zip` or uncompressed), GeoJSON, JSON+WKT, and GPX.
- **Preconditions:** The caller must invoke this method on an initialized `SparkContext` (or `JavaSpatialSparkContext`). 
- **Auto-detection Warning:** If `format` is omitted or `null`, CSV auto-detection for geometry columns is a "best-effort" guess with no guarantee of correctness. It is highly recommended to explicitly provide the `format` string.
- **Raster Data:** Do *not* use this method for raster formats (GeoTIFF, HDF). Use `sc.geoTiff[T]` or `sc.hdfFile` instead.

### Output
Returns `SpatialRDD` — A distributed Spark RDD containing spatial vector records (features).

### Valid Call Patterns
```scala
// Explicitly specifying the format (Recommended)
val parks = sparkContext.spatialFile(parksFile.getPath, "wkt")

// Loading a GPX file
val records = sparkContext.spatialFile("input.gpx", "gpx")

// Loading an envelope index
val r1Disk: SpatialRDD = sparkContext.spatialFile(index1Path, "envelope")

// Java API usage with BeastOptions
JavaRDD<IFeature> rects = spatialSparkContext.spatialFile("rects.csv", "envelope(0,1,2,3)", new BeastOptions("separator:,"));
```

### LLM Instruction Prompt
- Always call `spatialFile` as an extension method on an initialized `SparkContext` (e.g., `sc.spatialFile(...)` or `sparkContext.spatialFile(...)`). Never call it as a bare function.
- Always explicitly provide the `format` parameter (e.g., `"wkt"`, `"gpx"`, `"envelope"`) to avoid the unreliable best-effort CSV auto-detection.
- Use `spatialFile` strictly for vector data. For raster data, you must use `sc.geoTiff[T]` or `sc.hdfFile`.

### Prompt Snippet
```text
Load the vector dataset using `sc.spatialFile` and explicitly specify the format to avoid auto-detection issues. Do not use this for rasters.
```

### Common Failure Modes
- **Calling on Raster Data:** Attempting to load a GeoTIFF or HDF file using `spatialFile`. This will fail or yield garbage data; rasters require `sc.geoTiff[T]` or `sc.hdfFile`.
- **Missing SparkContext Receiver:** Calling `spatialFile("data.csv")` without the `sc.` or `sparkContext.` prefix, resulting in a compilation error.
- **Incorrect CSV Parsing:** Omitting the `format` parameter for a complex CSV file, causing Beast's best-effort auto-detection to misidentify the geometry column.

### Fix Code Hint
```scala
// BAD: Bare function call and relying on CSV auto-detection
val vectors = spatialFile("data.csv")
val rasters = sc.spatialFile("image.tif")

// GOOD: Called on SparkContext with explicit format for vectors, and using geoTiff for rasters
val vectors = sc.spatialFile("data.csv", "wkt")
val rasters = sc.geoTiff[Int]("image.tif")
```

## API Test: `spatialJoin`

### Signature
```scala
def spatialJoin(rdd2: SpatialRDD, joinPredicate: ESJPredicate = ESJPredicate.Intersects, method: ESJDistributedAlgorithm = null, mbrCount: LongAccumulator = null, opts: BeastOptions = new BeastOptions()): RDD[(IFeature, IFeature)]
def spatialJoin(partitionedRDD2: PartitionedSpatialRDD, joinPredicate: ESJPredicate = ESJPredicate.Intersects, mbrCount: LongAccumulator = null): RDD[(IFeature, IFeature)]
def spatialJoin(rdd1: JavaSpatialRDD, rdd2: JavaSpatialRDD, predicate: SpatialJoinAlgorithms.ESJPredicate, algorithm: SpatialJoinAlgorithms.ESJDistributedAlgorithm): JavaPairRDD[IFeature, IFeature]
def spatialJoin(rdd1: JavaSpatialRDD, rdd2: JavaSpatialRDD): JavaPairRDD[IFeature, IFeature]
def spatialJoin(r1: SpatialRDD, r2: SpatialRDD, joinPredicate: ESJPredicate = ESJPredicate.Intersects, joinMethod: ESJDistributedAlgorithm = null, mbrCount: LongAccumulator = null, opts: BeastOptions = new BeastOptions()): RDD[(IFeature, IFeature)]
def spatialJoin(r1: JavaSpatialRDD, r2: JavaSpatialRDD, joinPredicate: ESJPredicate, joinMethod: ESJDistributedAlgorithm, mbrCount: LongAccumulator, opts: BeastOptions): JavaPairRDD[IFeature, IFeature]
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/operations/SpatialJoin.scala:146  (+5 more definition site/overload)_

_Source doc:_ The main entry point for spatial join operations. Performs a spatial join between the given two inputs and returns an RDD of pairs of matching features. This method is a transformation. However, if the [[ESJDistributedAlgorithm.PBSM]] is used, the MBR of the two inputs has to be calculated first which runs a reduce action on each dataset even if the output of the spatial join is not used. You can specify a specific spatial join method through the [[joinMethod]] parameter. If not specified, an algorithm will be picked automatically based on the following rules. - If both datasets are spatially partitioned, the distributed join [[ESJDistributedAlgorithm.DJ]] algorithm is used. - If the product of the number of partitions of both datasets is less than [[SparkContext.defaultParallelism]], then the block nested loop join is used [[ESJDistributedAlgorithm.BNLJ]] - If at least one dataset is partition, then the repartition join is used [[ESJDistributedAlgorithm.REPJ]] - If none of the above, then the partition based spatial merge join is used [[ESJDistributedAlgorithm.PBSM]] @param r1 the first (left) dataset @param r2 the second (right) dataset @param joinPredicate the join predicate. The default is [[ESJPredicate.Intersects]] which finds all non-disjoint features @param joinMethod the join algorithm. If not specified the algorithm automatically chooses an algorithm based on the heuristic described above. @param mbrCount an (optional) accumulator to count the number of MBR tests during the algorithm. @return an RDD that contains pairs of matching features.

### Goal
Finds overlapping or contained features between two massive vector datasets using distributed spatial join algorithms.

### Parameters
- `r1` (`SpatialRDD`): The first (left) spatial dataset to join. When using the instance method `rdd1.spatialJoin(...)`, `rdd1` acts as this parameter.
- `r2` (`SpatialRDD`): The second (right) spatial dataset to join.
- `joinPredicate` (`ESJPredicate`), default `ESJPredicate.Intersects`: The spatial relationship to test (e.g., `ESJPredicate.Intersects`, `ESJPredicate.Contains`). The default finds all non-disjoint features.
- `joinMethod` (`ESJDistributedAlgorithm`), default `null`: The specific distributed join algorithm to use (e.g., `ESJDistributedAlgorithm.DJ`, `PBSM`, `REPJ`, `BNLJ`). If `null`, Beast automatically selects the optimal algorithm based on the partitioning state of the inputs and cluster parallelism.
- `mbrCount` (`LongAccumulator`), default `null`: An optional Spark accumulator to count the number of Minimum Bounding Rectangle (MBR) tests performed during the algorithm.
- `opts` (`BeastOptions`), default `new BeastOptions()`: Additional configuration options for the Beast engine.

### Input
Two vector datasets loaded as `SpatialRDD` (e.g., from Shapefile, GeoJSON, CSV, or WKT). 
**Preconditions:**
*   If explicitly requesting the Distributed Join (`ESJDistributedAlgorithm.DJ`), **both** datasets must be spatially partitioned first (e.g., using `rdd.spatialPartition(classOf[RSGrovePartitioner])`).
*   If explicitly requesting the Repartition Join (`ESJDistributedAlgorithm.REPJ`), at least **one** dataset must be spatially partitioned.
*   To avoid duplicate results in custom algorithms, partitions must be disjoint. Only `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, and `STRPartitioner` support disjoint partitioning.

### Output
Returns `RDD[(IFeature, IFeature)]` — an RDD containing pairs of matching features from the left and right datasets that satisfy the spatial join predicate.

### Valid Call Patterns
```scala
// 1. Auto-selected algorithm (recommended if unsure about partitioning)
val joinResults = dataset1.spatialJoin(dataset2, ESJPredicate.Intersects)

// 2. Explicit algorithm (PBSM)
val sjResults: RDD[(IFeature, IFeature)] = matchedPolygons.spatialJoin(
  matchedPoints, 
  ESJPredicate.Contains, 
  ESJDistributedAlgorithm.PBSM
)

// 3. Distributed Join (DJ) on explicitly partitioned data
val partitioned1 = dataset1.spatialPartition(classOf[RSGrovePartitioner])
val partitioned2 = dataset2.spatialPartition(classOf[RSGrovePartitioner])
val djResults = partitioned1.spatialJoin(
  partitioned2, 
  ESJPredicate.Intersects, 
  ESJDistributedAlgorithm.DJ
)
```

### LLM Instruction Prompt
- Always prefer the instance method syntax `rdd1.spatialJoin(rdd2, predicate, algorithm)`.
- If you specify `ESJDistributedAlgorithm.DJ`, you MUST ensure both RDDs are spatially partitioned first using `spatialPartition`.
- If you specify `ESJDistributedAlgorithm.REPJ`, you MUST ensure at least one RDD is spatially partitioned.
- If you are unsure of the partitioning state, omit the `joinMethod` parameter to let Beast auto-select the algorithm (it will choose PBSM, DJ, REPJ, or BNLJ based on heuristics).
- Be aware that using `ESJDistributedAlgorithm.PBSM` triggers an immediate Spark reduce action to calculate MBRs, even if the join output is not immediately collected.

### Prompt Snippet
```text
To perform a spatial join in Beast, use `rdd1.spatialJoin(rdd2, predicate, algorithm)`. If using `ESJDistributedAlgorithm.DJ`, you MUST spatially partition both RDDs first (e.g., `rdd.spatialPartition(classOf[RSGrovePartitioner])`). Omit the algorithm parameter to let Beast auto-select the best strategy based on the partitioning state.
```

### Common Failure Modes
- **Missing Partitioning for DJ:** Calling `spatialJoin` with `ESJDistributedAlgorithm.DJ` on unpartitioned RDDs will fail. Both datasets must be partitioned first.
- **Missing Partitioning for REPJ:** Calling `spatialJoin` with `ESJDistributedAlgorithm.REPJ` when neither dataset is partitioned will fail.
- **Duplicate Results:** Using non-disjoint partitions with custom algorithms can yield duplicate pairs. Ensure you use disjoint partitioners like `GridPartitioner` or `RSGrovePartitioner`.
- **Unexpected Action Execution:** Using `PBSM` triggers an immediate reduce action to calculate MBRs, which might cause unexpected execution delays in what is normally a lazy transformation pipeline.

### Fix Code Hint
```scala
// BAD: Requesting Distributed Join (DJ) without partitioning the inputs
val results = rdd1.spatialJoin(rdd2, ESJPredicate.Intersects, ESJDistributedAlgorithm.DJ)

// GOOD: Partition both datasets first for DJ
val p1 = rdd1.spatialPartition(classOf[RSGrovePartitioner])
val p2 = rdd2.spatialPartition(classOf[RSGrovePartitioner])
val results = p1.spatialJoin(p2, ESJPredicate.Intersects, ESJDistributedAlgorithm.DJ)

// GOOD: Let Beast auto-select the algorithm if partitioning is unknown
val autoResults = rdd1.spatialJoin(rdd2, ESJPredicate.Intersects)
```

## API Test: `spatialJoinBNLJ`

### Signature
```scala
def spatialJoinBNLJ(r1: SpatialRDD, r2: SpatialRDD, joinPredicate: ESJPredicate, numMBRTests: LongAccumulator = null) : RDD[(IFeature, IFeature)]
def spatialJoinBNLJ(r1: JavaSpatialRDD, r2: JavaSpatialRDD, joinPredicate: ESJPredicate, numMBRTests: LongAccumulator): JavaPairRDD[IFeature, IFeature]
def spatialJoinBNLJ(r1: JavaSpatialRDD, r2: JavaSpatialRDD, joinPredicate: ESJPredicate): JavaPairRDD[IFeature, IFeature]
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/operations/SpatialJoin.scala:418  (+2 more definition site/overload)_

_Source doc:_ Runs a spatial join between the two given RDDs using the block-nested-loop join algorithm. @param r1            the first set of features @param r2            the second set of features @param joinPredicate the predicate that joins a feature from r1 with a feature in r2 @return

### Goal
Runs a distributed spatial join between two vector datasets using the block-nested-loop join (BNLJ) algorithm to find all pairs of features that satisfy a specified spatial relationship.

### Parameters
- `r1` (`SpatialRDD`): The first set of spatial features (vector geometries) to join.
- `r2` (`SpatialRDD`): The second set of spatial features (vector geometries) to join.
- `joinPredicate` (`ESJPredicate`): The spatial relationship condition that must be met to join a feature from `r1` with a feature in `r2` (e.g., `ESJPredicate.MBRIntersects`, `ESJPredicate.Contains`).
- `numMBRTests` (`LongAccumulator`), default `null`: An optional Spark accumulator used to track and count the total number of Minimum Bounding Rectangle (MBR) intersection tests performed during the execution of the join.

### Input
Two `SpatialRDD`s containing vector data (e.g., loaded from Shapefiles, GeoJSON, CSV, or parallelized collections). Unlike the Distributed Join (`DJ`) or Repartition Join (`REPJ`) algorithms which require one or both datasets to be spatially partitioned first, the Block-Nested-Loop Join evaluates the Cartesian product of the partitions of `r1` and `r2`. 

### Output
Returns `RDD[(IFeature, IFeature)]` — A Spark RDD containing pairs (tuples) of matched vector features. The first element is from `r1` and the second is from `r2`.

### Valid Call Patterns
```scala
// Using the SpatialJoin object to perform a Block-Nested-Loop Join
val results: RDD[(IFeature, IFeature)] = SpatialJoin.spatialJoinBNLJ(
  r1, 
  r2, 
  joinPredicate = ESJPredicate.MBRIntersects
)
```

### LLM Instruction Prompt
- Call `spatialJoinBNLJ` as a method on the `SpatialJoin` object, passing both RDDs as arguments, rather than as an instance method on the RDD itself.
- Always provide an `ESJPredicate` (e.g., `ESJPredicate.MBRIntersects` or `ESJPredicate.Contains`) to define the join condition.
- Do not confuse this explicit algorithm call with the general `rdd.spatialJoin(...)` instance method. Use `SpatialJoin.spatialJoinBNLJ` when you specifically need the block-nested-loop join algorithm.

### Prompt Snippet
```text
To perform a block-nested-loop spatial join in Beast, use the object method `SpatialJoin.spatialJoinBNLJ(r1, r2, ESJPredicate.MBRIntersects)`. Do not call it as an instance method (`r1.spatialJoinBNLJ(r2)`). Ensure both inputs are SpatialRDDs.
```

### Common Failure Modes
- **Method Not Found:** Attempting to call `r1.spatialJoinBNLJ(r2)` as an instance method on the RDD. It must be called as `SpatialJoin.spatialJoinBNLJ(r1, r2, ...)`.
- **Performance Degradation / OOM:** Because BNLJ compares every partition of `r1` against every partition of `r2`, using it on massive datasets without prior filtering or when a partitioned join (like PBSM or DJ) would be more appropriate can lead to severe performance bottlenecks or Out Of Memory errors.
- **Missing Predicate:** Failing to specify the `joinPredicate`, which is a required parameter (unlike some general join wrappers that might default to intersects).

### Fix Code Hint
```scala
// WRONG: Called as an instance method
val joined = r1.spatialJoinBNLJ(r2, ESJPredicate.Contains)

// RIGHT: Called as an object method on SpatialJoin
val joined = SpatialJoin.spatialJoinBNLJ(r1, r2, ESJPredicate.Contains)
```

## API Test: `spatialJoinDJ`

### Signature
```scala
def spatialJoinDJ(r1: SpatialRDD, r2: SpatialRDD, joinPredicate: ESJPredicate, numMBRTests: LongAccumulator = null): RDD[(IFeature, IFeature)]
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/operations/SpatialJoin.scala:461_

_Source doc:_ Distributed join algorithm between spatially partitioned RDDs @param r1            the first set of features @param r2            the second set of features @param joinPredicate the predicate that joins a feature from r1 with a feature in r2 @param numMBRTests   a counter that will contain the number of MBR tests @return a pair RDD for joined features

### Goal
Executes the Distributed Join (DJ) algorithm to find overlapping or contained features between two massive vector datasets that have already been spatially partitioned.

### Parameters
- `r1` (`SpatialRDD`): The first set of vector features, which must be spatially partitioned.
- `r2` (`SpatialRDD`): The second set of vector features, which must also be spatially partitioned.
- `joinPredicate` (`ESJPredicate`): The spatial relationship condition that must be met to join a feature from `r1` with a feature in `r2` (e.g., `ESJPredicate.Contains`, `ESJPredicate.Intersects`).
- `numMBRTests` (`LongAccumulator`), default `null`: An optional Spark accumulator used to track and count the number of Minimum Bounding Rectangle (MBR) intersection tests performed during the join.

### Input
Two `SpatialRDD` vector datasets (e.g., loaded from Shapefiles, GeoJSON, or CSV). 
**Crucial Precondition:** The Distributed Join (`DJ`) algorithm strictly requires *both* datasets to be spatially partitioned prior to calling this method. To avoid duplicate results in the output, the partitions must be disjoint. Only `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, and `STRPartitioner` support disjoint partitioning.

### Output
Returns `RDD[(IFeature, IFeature)]` — A pair RDD containing tuples of matched features. The first element is a feature from `r1` and the second is the matching feature from `r2` that satisfies the `joinPredicate`.

### Valid Call Patterns
```scala
// Inferred from signature (not verified in tests)
import edu.ucr.cs.bdlab.beast.indexing.RSGrovePartitioner
import edu.ucr.cs.bdlab.beast.operations.SpatialJoin

// Both datasets MUST be spatially partitioned first
val partitionedR1 = r1.spatialPartition(classOf[RSGrovePartitioner])
val partitionedR2 = r2.spatialPartition(classOf[RSGrovePartitioner])

// Execute the Distributed Join (DJ)
val joinedFeatures = SpatialJoin.spatialJoinDJ(
  partitionedR1, 
  partitionedR2, 
  ESJPredicate.Contains
)
```

### LLM Instruction Prompt
- When calling `spatialJoinDJ`, you MUST ensure both input `SpatialRDD`s are spatially partitioned first. If only one is partitioned, use `REPJ` instead, or partition the other.
- To prevent duplicate join results, instruct the user to partition the data using a disjoint partitioner like `RSGrovePartitioner`.
- Do not invent a method on the RDD itself for this specific algorithm; call it statically via `SpatialJoin.spatialJoinDJ(r1, r2, predicate)` unless using the general `rdd.spatialJoin(...)` wrapper.

### Prompt Snippet
```text
The `spatialJoinDJ` method implements the Distributed Join algorithm and requires both input datasets to be spatially partitioned beforehand. Use `rdd.spatialPartition(classOf[RSGrovePartitioner])` on both inputs to ensure disjoint partitions, which prevents duplicate matches in the output RDD.
```

### Common Failure Modes
- **Unpartitioned Inputs:** Passing raw `SpatialRDD`s that have not been spatially partitioned. The DJ algorithm relies on partition metadata to prune the search space; missing this metadata will cause the join to fail or produce incorrect results.
- **Duplicate Results:** Using a non-disjoint partitioner (or failing to partition correctly) can cause features spanning multiple partitions to be evaluated and joined multiple times, leading to duplicate `(IFeature, IFeature)` pairs in the output.

### Fix Code Hint
```scala
// BAD: Calling spatialJoinDJ on raw RDDs
// val joined = SpatialJoin.spatialJoinDJ(rawPoints, rawPolygons, ESJPredicate.Intersects)

// GOOD: Partition both datasets with a disjoint partitioner first
val partitionedPoints = rawPoints.spatialPartition(classOf[RSGrovePartitioner])
val partitionedPolygons = rawPolygons.spatialPartition(classOf[RSGrovePartitioner])
val joined = SpatialJoin.spatialJoinDJ(partitionedPoints, partitionedPolygons, ESJPredicate.Intersects)
```

## API Test: `spatialJoinPBSM`

### Signature
```scala
def spatialJoinPBSM(r1: SpatialRDD, r2: SpatialRDD, joinPredicate: ESJPredicate, numMBRTests: LongAccumulator = null, opts: BeastOptions = new BeastOptions()): RDD[(IFeature, IFeature)]
def spatialJoinPBSM(r1: JavaSpatialRDD, r2: JavaSpatialRDD, joinPredicate: ESJPredicate, numMBRTests: LongAccumulator): JavaPairRDD[IFeature, IFeature]
def spatialJoinPBSM(r1: JavaSpatialRDD, r2: JavaSpatialRDD, joinPredicate: ESJPredicate) : JavaPairRDD[IFeature, IFeature]
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/operations/SpatialJoin.scala:297  (+2 more definition site/overload)_

_Source doc:_ Performs a partition-based spatial-merge (PBSM) join as explained in the following paper. Jignesh M. Patel, David J. DeWitt: Partition Based Spatial-Merge Join. SIGMOD Conference 1996: 259-270 https://doi.org/10.1145/233269.233338 @param r1            the first dataset @param r2            the second dataset @param joinPredicate the join predicate @param numMBRTests   (output) the number of MBR tests done during the algorithm @param opts          Additional options for the PBSM algorithm @return a pair RDD for joined features

### Goal
Performs a distributed Partition-Based Spatial-Merge (PBSM) join to find overlapping or contained features between two massive vector datasets.

### Parameters
- `r1` (`SpatialRDD`): The first spatial dataset to be joined.
- `r2` (`SpatialRDD`): The second spatial dataset to be joined.
- `joinPredicate` (`ESJPredicate`): The spatial relationship condition that must be met for a pair to be joined (e.g., `ESJPredicate.MBRIntersects`, `ESJPredicate.Contains`).
- `numMBRTests` (`LongAccumulator`), default `null`: An optional Spark accumulator used as an output variable to track the total number of Minimum Bounding Rectangle (MBR) intersection tests performed during the execution of the algorithm.
- `opts` (`BeastOptions`), default `new BeastOptions()`: Additional configuration options for tuning the PBSM algorithm.

### Input
- Two `SpatialRDD`s (typically loaded from vector formats like Shapefile, GeoJSON, or CSV via `sc.shapefile`, `sc.geojsonFile`, etc.).
- Unlike the Distributed Join (`DJ`) algorithm which requires both datasets to be spatially partitioned first, PBSM can operate on unpartitioned datasets by dynamically partitioning them using a grid.
- If the average number of points per geometry exceeds 100, Beast will automatically trigger a quad-split optimization to recursively split complex geometries before joining.

### Output
Returns `RDD[(IFeature, IFeature)]` — A Spark Pair RDD containing tuples of matched features from `r1` and `r2` that satisfy the specified `joinPredicate`.

### Valid Call Patterns
```scala
// Direct call via the SpatialJoin object
import edu.ucr.cs.bdlab.beast.operations.SpatialJoin
import edu.ucr.cs.bdlab.beast.cg.SpatialJoinAlgorithms.ESJPredicate

val result = SpatialJoin.spatialJoinPBSM(dataset1, dataset2, ESJPredicate.MBRIntersects)

// With disjoint datasets, it efficiently returns an empty RDD
val emptyResult = SpatialJoin.spatialJoinPBSM(disjointData1, disjointData2, ESJPredicate.Intersects)
```

### LLM Instruction Prompt
- Call `spatialJoinPBSM` as a static-like method on the `SpatialJoin` object (`SpatialJoin.spatialJoinPBSM(r1, r2, predicate)`), NOT as an instance method on the RDD.
- Always provide a valid `ESJPredicate` (e.g., `ESJPredicate.MBRIntersects`, `ESJPredicate.Contains`, `ESJPredicate.Intersects`).
- Do not invent spatial predicates; use only those defined in `ESJPredicate`.
- If you need to join datasets using the generic RDD method instead of calling the algorithm directly, use `r1.spatialJoin(r2, ESJPredicate.Contains, ESJDistributedAlgorithm.PBSM)`.

### Prompt Snippet
```text
To perform a Partition-Based Spatial-Merge join directly, use `SpatialJoin.spatialJoinPBSM(r1, r2, ESJPredicate.MBRIntersects)`. Do not call `r1.spatialJoinPBSM(r2)`. Ensure both inputs are `SpatialRDD`s. Beast will automatically apply quad-split optimization if geometries are highly complex (>100 points/geometry).
```

### Common Failure Modes
- **Method Not Found:** Attempting to call `r1.spatialJoinPBSM(r2)` directly on the RDD. The specific PBSM function is located on the `SpatialJoin` object.
- **Type Mismatch:** Passing standard Spark `RDD[Row]` or `DataFrame` instead of Beast's `SpatialRDD` (`RDD[IFeature]`).
- **Out of Memory (OOM) on Driver:** Attempting to `collect()` the result of a massive spatial join without filtering or aggregating first. Always apply transformations or save the distributed output.

### Fix Code Hint
```scala
// ❌ WRONG: Calling as an instance method on the RDD
val joined = points.spatialJoinPBSM(polygons, ESJPredicate.Contains)

// ✅ RIGHT: Calling via the SpatialJoin object
val joined = SpatialJoin.spatialJoinPBSM(points, polygons, ESJPredicate.Contains)

// ✅ RIGHT (Alternative): Using the generic spatialJoin instance method with the PBSM enum
val joined = points.spatialJoin(polygons, ESJPredicate.Contains, ESJDistributedAlgorithm.PBSM)
```

## API Test: `spatialJoinRepJ`

### Signature
```scala
def spatialJoinRepJ(r1: SpatialRDD, r2: SpatialRDD, joinPredicate: ESJPredicate, numMBRTests: LongAccumulator = null): RDD[(IFeature, IFeature)]
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/operations/SpatialJoin.scala:488_

_Source doc:_ Repartition join algorithm between two datasets: r1 is spatially disjoint partitioned and r2 is not @param r1 the first dataset @param r2 the second dataset @param joinPredicate the join predicate @param numMBRTests an optional accumulator that counts the number of MBR tests @return an RDD of pairs of matching features

### Goal
Executes a distributed Repartition Join (REPJ) between two vector datasets to find matching features, optimized for scenarios where exactly one dataset is already spatially partitioned with disjoint boundaries.

### Parameters
- `r1` (`SpatialRDD`): The first vector dataset, which **must** be spatially partitioned with disjoint partitions prior to calling this function.
- `r2` (`SpatialRDD`): The second vector dataset, which is typically unpartitioned.
- `joinPredicate` (`ESJPredicate`): The spatial condition to evaluate between features (e.g., `ESJPredicate.Intersects`, `ESJPredicate.Contains`).
- `numMBRTests` (`LongAccumulator`), default `null`: An optional Spark accumulator used to track and count the number of Minimum Bounding Rectangle (MBR) intersection tests performed during the join.

### Input
Two `SpatialRDD`s containing vector geometries (e.g., loaded from Shapefiles, GeoJSON, or CSV). 
**Preconditions:** 
1. `r1` MUST be spatially partitioned using a disjoint partitioner. To avoid duplicate results, only `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, and `STRPartitioner` support the required disjoint partitioning.
2. `r2` does not need to be partitioned. If both datasets are already partitioned, the Distributed Join (`DJ`) algorithm is more appropriate.

### Output
Returns `RDD[(IFeature, IFeature)]` — A distributed collection of paired features (one from `r1`, one from `r2`) that satisfy the specified `joinPredicate`.

### Valid Call Patterns
```scala
// Inferred from the signature (no verbatim example provided in documentation)
// Note: r1 must be partitioned first
val partitionedR1: SpatialRDD = r1.spatialPartition(classOf[RSGrovePartitioner])

val joinedFeatures: RDD[(IFeature, IFeature)] = spatialJoinRepJ(
  partitionedR1, 
  unpartitionedR2, 
  ESJPredicate.Intersects
)
```

### LLM Instruction Prompt
- Use `spatialJoinRepJ` when explicitly implementing the Repartition Join (REPJ) algorithm where one dataset is disjoint-partitioned and the other is not.
- Ensure `r1` is partitioned using a disjoint partitioner (e.g., `RSGrovePartitioner`) before calling.
- Do not use this function if both datasets are partitioned (use `DJ` instead) or if neither is partitioned (use `PBSM` or the standard `rdd.spatialJoin` which auto-selects the algorithm).
- Note that Beast automatically triggers a quad-split optimization during spatial joins if the average number of points per geometry exceeds 100.

### Prompt Snippet
```text
spatialJoinRepJ(partitionedR1, unpartitionedR2, ESJPredicate.Contains)
```

### Common Failure Modes
- **Duplicate Results / Incorrect Join:** Occurs if `r1` is not partitioned using a disjoint partitioner. The REPJ algorithm relies on the disjoint boundaries of `r1`'s partitions to route `r2`'s features without producing duplicates.
- **Performance Degradation or Crash:** Passing an unpartitioned RDD as `r1` will cause the algorithm to fail or perform poorly, as it assumes `r1`'s partitions define the spatial boundaries for broadcasting and shuffling `r2`.

### Fix Code Hint
```scala
// FIX: Ensure r1 is partitioned with a disjoint partitioner before calling spatialJoinRepJ
val disjointPartitionedR1 = r1.spatialPartition(classOf[RSGrovePartitioner])
val joined = spatialJoinRepJ(disjointPartitionedR1, r2, ESJPredicate.Intersects)
```

## API Test: `spatialPartition`

### Signature
```scala
def spatialPartition(spatialPartitioner: SpatialPartitioner): SpatialRDD
def spatialPartition(partitionerKlass: Class[_ <: SpatialPartitioner], numPartitions: Int = rdd.getNumPartitions, opts: BeastOptions = new BeastOptions()): SpatialRDD
def spatialPartition(rdd: JavaSpatialRDD, spatialPartitioner: SpatialPartitioner): JavaPartitionedSpatialRDD
def spatialPartition(rdd: JavaSpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], numPartitions: Int): JavaPartitionedSpatialRDD
def spatialPartition(rdd: JavaSpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner], numPartitions: Int, opts: BeastOptions): JavaPartitionedSpatialRDD
def spatialPartition(rdd: JavaSpatialRDD, partitionerClass: Class[_ <: SpatialPartitioner]): JavaPartitionedSpatialRDD
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:179  (+5 more definition site/overload)_

_Source doc:_ Partition a set of features according to a created spatial partitioner @param spatialPartitioner the partitioner for the data @return partitioned records

### Goal
Distribute a set of spatial features across a Spark cluster using a specialized spatial partitioner (e.g., R*-Grove or GridPartitioner) to optimize load balancing, query pruning, and enable distributed spatial joins.

### Parameters
- `rdd` (`JavaSpatialRDD`): The input Java spatial RDD to be partitioned (applicable when using the Java API overloads).
- `spatialPartitioner` (`SpatialPartitioner`): An initialized spatial partitioner instance (e.g., `GridPartitioner`) or class type (e.g., `classOf[RSGrovePartitioner]`) that defines how geometries are distributed across partitions.

### Input
A `SpatialRDD` (or `JavaSpatialRDD`) containing vector features, typically loaded from formats like CSV, Shapefile, or GeoJSON. 
*   **Precondition for Initialized Partitioners:** If passing an instantiated partitioner like `GridPartitioner`, you must first compute the dataset's Minimum Bounding Rectangle (MBR) using `rdd.summary`.
*   **Precondition for Distributed Joins:** The Distributed Join (`DJ`) algorithm requires *both* input datasets to be spatially partitioned first. The Repartition Join (`REPJ`) requires at least *one* dataset to be spatially partitioned.

### Output
Returns `JavaPartitionedSpatialRDD` (or `SpatialRDD` in the Scala API) — the exact same set of input features, but physically reorganized across Spark partitions according to their spatial locations, with the spatial partitioner attached to the RDD metadata.

### Valid Call Patterns
```scala
// Pattern 1: Using an initialized partitioner (requires computing summary/MBR first)
val mbr = data.summary
val gridPartitioner = new GridPartitioner(mbr, Array(2, 2))
val partitionedData = data.spatialPartition(gridPartitioner)

// Pattern 2: Using a partitioner class (automatically initializes)
val partitionedFeatures: RDD[IFeature] = features.spatialPartition(classOf[RSGrovePartitioner])

// Pattern 3: Using IndexHelper for advanced configuration (e.g., enforcing disjoint partitions)
import edu.ucr.cs.bdlab.beast.indexing.IndexHelper.{Fixed, NumPartitions}
import edu.ucr.cs.bdlab.beast.indexing.{IndexHelper, RSGrovePartitioner}
val partitioner = IndexHelper.createPartitioner(features, classOf[RSGrovePartitioner],
  NumPartitions(Fixed, features.getNumPartitions), _ => 1, "disjoint" -> true)
val partitionedFeatures = features.spatialPartition(partitioner)
```

### LLM Instruction Prompt
- Always spatially partition datasets before performing a Distributed Join (`DJ`) or Repartition Join (`REPJ`).
- If duplicate avoidance is required for custom algorithms, ensure the partitioner supports disjoint partitioning. Only `GridPartitioner`, `RSGrovePartitioner`, `KDTreePartitioner`, and `STRPartitioner` support disjoint partitioning.
- When passing an instantiated `GridPartitioner`, you must compute the dataset's summary (`rdd.summary`) first to provide the bounding box. Alternatively, pass the class type (e.g., `classOf[RSGrovePartitioner]`) to let Beast handle initialization.

### Prompt Snippet
```text
To optimize spatial joins or range queries, partition the RDD using `spatialPartition`. For disjoint partitions (to avoid duplicate results), prefer `RSGrovePartitioner` or `GridPartitioner`. Remember that the `DJ` spatial join algorithm requires both datasets to be spatially partitioned beforehand.
```

### Common Failure Modes
- **Missing Pre-Partitioning for Joins:** Attempting to run a `DJ` (Distributed Join) without calling `spatialPartition` on both input RDDs first, which will cause the join to fail or fall back to a less efficient algorithm.
- **Uninitialized MBR:** Attempting to instantiate a `GridPartitioner` without first calling `rdd.summary` to get the dataset's spatial envelope.
- **Duplicate Results in Custom Algorithms:** Using a non-disjoint partitioner when disjoint partitions are strictly required, leading to features being duplicated across partition boundaries.

### Fix Code Hint
```scala
// FIX: Compute summary first if using an initialized GridPartitioner
val mbr = features.summary
val partitioner = new GridPartitioner(mbr, Array(10, 10))
val partitioned = features.spatialPartition(partitioner)

// FIX: Or use the class-based overload for automatic initialization
val partitionedAuto = features.spatialPartition(classOf[RSGrovePartitioner])
```

## API Test: `splitGeometryAcrossDateLine`

### Signature
```scala
def splitGeometryAcrossDateLine(geometry: Geometry): Geometry
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/GeometryQuadSplitter.scala:122_

_Source doc:_ Splits the given geometry across the dateline (-180 or +180 meridian) to avoid errors. 1. This function assumes that the input consists of a polygon with a single ring (outer shell). 1. We assume that the width cannot be greater than 180 degrees. 1. If the geometry width is greater than 180, we assume that it crosses the dateline. 1. To fix the geometry, we rotate all negative longitudes by adding 360. 1. After that, we split the geometry by intersecting it with the western hemisphere once and with the easter hemisphere once. @param geometry the input geometry to detect and split @return Either the same geometry if it does not cross the dateline, or the same one split into two if it crosses the dateline.

### Goal
Splits a single-ring polygon geometry across the International Date Line (-180 or +180 meridian) to prevent spatial join or rendering errors caused by coordinate wrapping.

### Parameters
- `geometry` (`Geometry`): The input JTS `Geometry` to evaluate and potentially split.

### Input
A JTS `Geometry` object representing spatial data in geographic coordinates (longitude/latitude). 
**Preconditions:** 
1. The input must be a polygon consisting of a single ring (outer shell only, no holes).
2. The actual physical width of the geometry must not exceed 180 degrees. The function uses a bounding box width > 180 degrees as the heuristic to detect dateline crossing.

### Output
Returns `Geometry` — Either the exact original geometry if it does not cross the dateline, or a new multi-part geometry split into two pieces (one intersected with the western hemisphere, one with the eastern hemisphere) if it does cross.

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast.cg.GeometryQuadSplitter

// Assuming `geometry` is a JTS Polygon crossing the dateline
val splitGeometry = GeometryQuadSplitter.splitGeometryAcrossDateLine(geometry)
```

### LLM Instruction Prompt
- Use `GeometryQuadSplitter.splitGeometryAcrossDateLine(geometry)` to fix polygons that wrap around the antimeridian.
- Ensure the input geometry is a single-ring polygon (no holes) and its true physical width is <= 180 degrees before calling this function.
- Do not call this as an instance method on the geometry; it is a static method on `GeometryQuadSplitter`.

### Prompt Snippet
```text
To handle dateline-crossing polygons in Beast, use `GeometryQuadSplitter.splitGeometryAcrossDateLine(geom)`. The input must be a single-ring polygon with a true width <= 180 degrees. It returns a split multi-part geometry if it crosses the dateline, or the original geometry otherwise.
```

### Common Failure Modes
- **Multi-ring or MultiPolygon inputs:** Passing a polygon with holes or a `MultiPolygon` violates the single-ring assumption, leading to incorrect coordinate rotation and malformed outputs.
- **Massive geometries:** Passing a geometry whose actual physical width is greater than 180 degrees. The function will falsely assume the geometry crosses the dateline and will incorrectly rotate its negative longitudes by +360 degrees.
- **Missing object qualifier:** Attempting to call `geometry.splitGeometryAcrossDateLine()` instead of `GeometryQuadSplitter.splitGeometryAcrossDateLine(geometry)`.

### Fix Code Hint
```scala
// FIX: Ensure the geometry is a simple polygon and call via GeometryQuadSplitter
if (geometry.getGeometryType == "Polygon" && geometry.asInstanceOf[Polygon].getNumInteriorRing == 0) {
  val fixedGeom = GeometryQuadSplitter.splitGeometryAcrossDateLine(geometry)
}
```

## API Test: `sridToCRS`

### Signature
```scala
def sridToCRS(srid: Int): CoordinateReferenceSystem
```
_Source: beast/cg/src/main/scala/org/apache/spark/beast/CRSServer.scala:352_

_Source doc:_ Convert the given SRID to CRS according to the following logic. 1. If the SRID is zero, it indicates an invalid SRID and `null` is returned. 2. It searches the local cache and retrieves the SRID. 3a. If SRID is positive, use it as an EPSG, retrieve the CRS, cache and return it. 3b. If SRID is negative, contact the server, retrieve the CRS, cache and return it. @param srid the SRID that needs to be converted to a CRS @return the converted CRS.

### Goal
Convert an integer Spatial Reference System Identifier (SRID) into a `CoordinateReferenceSystem` object, resolving standard EPSG codes locally and custom projections via the Beast `CRSServer`.

### Parameters
- `srid` (`Int`): The integer identifier for the CRS. Positive values are treated as standard EPSG codes, negative values indicate custom CRSs managed by the Beast server, and 0 indicates an invalid SRID.

### Input
An integer SRID. If the SRID is negative (indicating a custom, non-standard CRS), the Beast `CRSServer` must be actively running on the Spark cluster (via `CRSServer.startServer(sc)`) so the method can contact the server to retrieve the CRS definition.

### Output
Returns `CoordinateReferenceSystem` — A GeoTools/OpenGIS CRS object representing the spatial reference system. Returns `null` if the input SRID is `0`.

### Valid Call Patterns
```scala
// Standard EPSG resolution (e.g., WGS84)
val wgs84Crs = CRSServer.sridToCRS(4326)

// Custom CRS resolution (requires CRSServer to be running)
CRSServer.startServer(sc)
try {
  val customCrs = CRSServer.sridToCRS(sridSinusoidal) // where sridSinusoidal < 0
} finally {
  CRSServer.stopServer(true)
}
```

### LLM Instruction Prompt
- When needing to instantiate a `CoordinateReferenceSystem` from an integer SRID in Beast, use `CRSServer.sridToCRS(srid)`. 
- Remember the resolution logic: positive integers are treated as standard EPSG codes, negative integers are fetched from the Beast `CRSServer` (which must be running), and `0` returns `null`. Always handle the potential `null` return value if the SRID source is untrusted.

### Prompt Snippet
```text
Use CRSServer.sridToCRS(srid) to convert an integer SRID to a CoordinateReferenceSystem. Positive values are EPSG codes; negative values require a running CRSServer. Handle nulls if srid might be 0.
```

### Common Failure Modes
- **NullPointerException Downstream:** Passing `0` as the SRID explicitly returns `null`. If the caller immediately invokes methods on the returned CRS without a null check, it will crash.
- **Server Unreachable / Connection Refused:** Passing a negative SRID when `CRSServer.startServer(sc)` has not been called, or if the server has been stopped. The method will fail to contact the server to retrieve the custom CRS.
- **Unknown EPSG Code:** Passing a positive SRID that does not exist in the standard EPSG registry will fail during the local EPSG lookup phase.

### Fix Code Hint
```scala
// Ensure CRSServer is running if dealing with potentially custom (negative) SRIDs
CRSServer.startServer(sc)
try {
  val crs = CRSServer.sridToCRS(srid)
  if (crs != null) {
    // Proceed with valid CoordinateReferenceSystem
    println(crs.getName.toString)
  } else {
    // Handle invalid SRID (0)
    println("Invalid SRID provided.")
  }
} finally {
  CRSServer.stopServer(true)
}
```

## API Test: `startServer`

### Signature
```scala
def startServer(defaultPort: Int = DefaultPort): Int
def startServer(sc: SparkContext): Boolean
def startServer(jsc: JavaSparkContext): Boolean
```
_Source: beast/cg/src/main/scala/org/apache/spark/beast/CRSServer.scala:91  (+2 more definition site/overload)_

_Source doc:_ Starts the server and returns the port on which it is listening @return the port on which the server is started

### Goal
Starts the Coordinate Reference System (CRS) HTTP server to manage and distribute non-standard CRS definitions across worker nodes in a Spark cluster.

### Parameters
- `defaultPort` (`Int`), default `DefaultPort`: The preferred network port number to bind the server to.
- `sc` (`SparkContext`) / `jsc` (`JavaSparkContext`): The active Spark context to attach the server to (used in the overloads).

### Input
- Requires an initialized `SparkContext` or `JavaSparkContext` when using the context-based overloads.
- The environment must allow binding to the specified network port (or an available fallback port).

### Output
Returns `Int` — The actual network port number on which the server is listening. (Note: The `SparkContext` and `JavaSparkContext` overloads return a `Boolean` indicating whether the server started successfully).

### Valid Call Patterns
```scala
// Start the server using an active SparkContext
CRSServer.startServer(sparkContext)
try {
  // Perform operations requiring custom/non-standard CRS definitions
  val port = sparkContext.getLocalProperty(CRSServer.CRSServerPort)
  // ...
} finally {
  // Always ensure the server is stopped to prevent resource leaks
  CRSServer.stopServer(true)
}
```

### LLM Instruction Prompt
- When generating code that registers or uses non-standard Coordinate Reference Systems (CRS) in Beast, you MUST start the `CRSServer` using `CRSServer.startServer(sc)`.
- Always wrap the subsequent spatial operations in a `try-finally` block and call `CRSServer.stopServer(true)` in the `finally` block to prevent resource leaks.
- Do not call `startServer` as a bare method; it must be qualified with the `CRSServer` object.

### Prompt Snippet
```text
To distribute non-standard CRS definitions across a Beast Spark cluster, call `CRSServer.startServer(sc)`. You MUST wrap subsequent operations in a `try-finally` block and invoke `CRSServer.stopServer(true)` in the `finally` clause to release the port.
```

### Common Failure Modes
- **Resource Leaks:** Failing to call `CRSServer.stopServer(true)` after the spatial operations complete, leaving the HTTP server running and the port bound.
- **Uninitialized Context:** Passing a null or stopped `SparkContext` to the overload, causing the server startup to fail or properties to not be set.
- **Missing Qualifier:** Attempting to call `startServer(sc)` without the `CRSServer` object qualifier, resulting in a compilation error.

### Fix Code Hint
```scala
// WRONG: No try-finally block, risking a leaked server process
CRSServer.startServer(sc)
val myCrs = CRS.decode("EPSG:3857")
// ... operations ...

// RIGHT: Safely start and stop the server
CRSServer.startServer(sc)
try {
  val myCrs = CRS.decode("EPSG:3857")
  // ... operations ...
} finally {
  CRSServer.stopServer(true)
}
```

## API Test: `sumSideLength`

### Signature
```scala
def sumSideLength: Array[Double]
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/SpatialPartition.scala:47_

_Source doc:_ The sum of side length along each dimension. Combined with numNonEmptyGeometries, it can be used to compute average side length per dimension.

### Goal
Computes the total sum of the bounding box side lengths along each spatial dimension for a collection of geometries, enabling the calculation of average spatial extents.

### Parameters
_None._

### Input
A spatial summary or partition object (e.g., `Summary` or `SpatialPartition`) that contains aggregated geometric statistics from a vector dataset. This is typically obtained via `GeometricSummary.run(...)` or by calling `.summary` on a spatial RDD.

### Output
Returns `Array[Double]` — an array where each element represents the total sum of side lengths for a specific spatial dimension (e.g., index `0` for the X/longitude dimension, index `1` for the Y/latitude dimension).

### Valid Call Patterns
```scala
// Inferred from sibling API `numFeatures` on Summary/SpatialPartition
val inputfile = locateResource("/test.partitions")
val opts = new BeastOptions().set("iformat", "wkt(Geometry)")
  .set("skipheader", true)
  .set("separator", "\t")

val summary = GeometricSummary.run(opts, Array(inputfile.getPath), null, sparkContext).asInstanceOf[Summary]

// Retrieve the sum of side lengths per dimension
val sideLengths: Array[Double] = summary.sumSideLength

// Compute average side length per dimension (as recommended by source docs)
val avgSideLengthX = sideLengths(0) / summary.numNonEmptyGeometries
val avgSideLengthY = sideLengths(1) / summary.numNonEmptyGeometries
```

### LLM Instruction Prompt
- When calculating average geometry extents or side lengths per dimension in Beast, call `.sumSideLength` on a spatial summary object. 
- It takes no arguments and returns an `Array[Double]`, not a single scalar value. 
- To find the average side length per dimension, divide the respective array elements by `numNonEmptyGeometries`.

### Prompt Snippet
```text
def sumSideLength: Array[Double] // Call on a spatial summary/partition object. Returns sum of side lengths per dimension (index 0=X, 1=Y). Divide by numNonEmptyGeometries for averages.
```

### Common Failure Modes
- **Type Mismatch on Return:** Assuming the method returns a single `Double` representing total area or perimeter, rather than an `Array[Double]` representing lengths per dimension.
- **Passing Arguments:** Attempting to pass a dimension index directly to the method (e.g., `summary.sumSideLength(0)`). The method takes no arguments; you must index the returned array.

### Fix Code Hint
```scala
// WRONG: Attempting to get a single scalar or passing an argument
// val totalLength: Double = summary.sumSideLength
// val xLength = summary.sumSideLength(0) // Fails if interpreted as method argument

// RIGHT: Assign to an array first, or index the result of the parameterless call
val lengths: Array[Double] = summary.sumSideLength
val avgX = lengths(0) / summary.numNonEmptyGeometries
val avgY = lengths(1) / summary.numNonEmptyGeometries
```

## API Test: `summary`

### Signature
```scala
def summary: Summary
def summary(rdd: JavaSpatialRDD): Summary
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:171  (+2 more definition site/overload)_

_Source doc:_ Compute the geometric summary of a set of features which includes size (in bytes), number of records, number of points, number of non empty geometries, average side length (width and height), and the geometry type. @return the computed summaries

### Goal
Compute the geometric summary and Minimum Bounding Rectangle (MBR) of a distributed vector dataset, providing essential statistics like feature count, size, and geometry type for approximate query processing or spatial partitioning.

### Parameters
- `rdd` (`JavaSpatialRDD`): The spatial RDD to compute the summary for. *Note: This parameter is only required when using the Java API (`JavaSpatialRDDHelper.summary(rdd)`). In Scala, `summary` is called as a parameterless extension method directly on the RDD (`rdd.summary`).*

### Input
A loaded vector `SpatialRDD` or `JavaSpatialRDD` containing spatial features (e.g., points, lines, or polygons loaded from CSV, Shapefile, or GeoJSON). The dataset does not need to be spatially partitioned prior to calling this method. This operation is specific to vector data and is not used for `RasterRDD` objects.

### Output
Returns `Summary` — an object representing the computed geometric summaries of the dataset. This includes the dataset's spatial envelope (MBR), size (in bytes), number of records, number of points, number of non-empty geometries, average side length (width and height), and the geometry type. The `Summary` object can be used directly as an `EnvelopeND` or bounding box when initializing spatial partitioners.

### Valid Call Patterns
```scala
// Scala: Parameterless extension method on a SpatialRDD
val data: SpatialRDD = sparkContext.readCSVPoint("points.csv")
val mbr = data.summary

// Using the summary to initialize a spatial partitioner
val gridPartitioner = new GridPartitioner(mbr, Array(2, 2))
val partitionedData = data.spatialPartition(gridPartitioner)

// Java: Using the helper class
// Summary summary = JavaSpatialRDDHelper.summary(rdd);
```

### LLM Instruction Prompt
- Use `rdd.summary` (Scala) or `JavaSpatialRDDHelper.summary(rdd)` (Java) to compute the bounding box and statistics of a vector dataset.
- Do not pass arguments to `summary` in Scala; it is a parameterless extension method on `SpatialRDD`.
- Use the returned `Summary` object when a spatial partitioner (like `GridPartitioner`) requires the dataset's Minimum Bounding Rectangle (MBR) for initialization.
- Do not attempt to call `summary` on a `RasterRDD`; it is a vector RDD operation.

### Prompt Snippet
```text
RDPro/Beast `summary`: Computes geometric stats (MBR, feature count, size) for a vector SpatialRDD. Call as `val mbr = rdd.summary` in Scala (no args). The returned `Summary` object acts as the dataset's bounding box and is typically passed to spatial partitioners like `new GridPartitioner(mbr, Array(2, 2))`.
```

### Common Failure Modes
- **Passing arguments in Scala:** Attempting to call `rdd.summary(something)` in Scala will fail to compile. The Scala signature is `def summary: Summary`.
- **Calling on Raster Data:** Attempting to call `summary` on a `RasterRDD` (e.g., loaded via `sc.geoTiff`). This is a vector-specific operation.
- **Type Mismatch for Partitioners:** Forgetting to compute the summary before initializing partitioners that require an MBR (like `GridPartitioner`), or trying to pass the raw RDD instead of the `Summary` object.

### Fix Code Hint
```scala
// WRONG: Passing arguments to summary in Scala
// val stats = data.summary(data)

// WRONG: Initializing a partitioner without the summary MBR
// val partitioner = new GridPartitioner(data, Array(2, 2))

// CORRECT: Call parameterless summary to get the MBR, then partition
val mbr = data.summary
val gridPartitioner = new GridPartitioner(mbr, Array(2, 2))
val partitionedData = data.spatialPartition(gridPartitioner)
```

## API Test: `tileIDs`

### Signature
```scala
def tileIDs: Iterator[Int]
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadata.scala:91_

_Source doc:_ An iterators that goes over all tile IDs @return an iterator that iterates over all tile IDs in this raster

### Goal
Provides an iterator over all integer tile IDs defined in a raster's metadata, enabling sequential access to the raster's underlying tiles.

### Parameters
_None._

### Input
A `RasterMetadata` instance. This is typically accessed via a low-level raster reader (e.g., `reader.metadata`) or created manually for reshaping operations (e.g., `RasterMetadata.create(...)`).

### Output
Returns `Iterator[Int]` — An iterator yielding the integer ID for every tile present in the raster dataset.

### Valid Call Patterns
```scala
// Iterating over tile IDs from a GeoTiffReader's metadata
val reader = new GeoTiffReader
reader.initialize(fileSystem, rasterPath.toString, "0", new BeastOptions())

for (tileID <- reader.metadata.tileIDs) {
  val tile = reader.readTile(tileID)
  for ((x, y) <- tile.pixelLocations) {
    tile.isDefined(x, y)
  }
}
```

### LLM Instruction Prompt
- When low-level tile extraction or iteration is required, call `tileIDs` on a `RasterMetadata` instance (e.g., `reader.metadata.tileIDs`) to retrieve an `Iterator[Int]` of all available tile IDs. Do not attempt to call this directly on a high-level `RasterRDD`.

### Prompt Snippet
```text
Use `metadata.tileIDs` to get an `Iterator[Int]` of all tile IDs in a raster, typically for use with `reader.readTile(tileID)` in local or partition-level processing.
```

### Common Failure Modes
- **Calling on RDD:** Attempting to call `tileIDs` directly on a `RasterRDD` instead of its underlying `RasterMetadata`.
- **Distributed Execution Context:** Using the local `Iterator[Int]` directly in a Spark distributed operation without parallelizing it or properly scoping it within a `mapPartitions` block.
- **Uninitialized Reader:** Attempting to access `reader.metadata.tileIDs` before calling `reader.initialize(...)`, resulting in null reference or empty metadata errors.

### Fix Code Hint
```scala
// Correct: Initialize reader, access metadata, and iterate tile IDs
val reader = new GeoTiffReader
reader.initialize(fileSystem, path, "0", new BeastOptions())
val ids: Iterator[Int] = reader.metadata.tileIDs
```

## API Test: `uniform`

### Signature
```scala
def uniform(cardinality: Long): JavaSpatialRDD
def uniform(cardinality: Long): SpatialRDD
def uniform(a: Double, b: Double): Double
```
_Source: beast/io/src/main/scala/edu/ucr/cs/bdlab/beast/generator/SpatialGenerator.scala:37  (+2 more definition site/overload)_

_Source doc:_ Generate a random value in the range [a, b) from a uniform distribution

### Goal
Generate a random numeric value within a specified range, or (via its overloads) generate a distributed `SpatialRDD` of synthetic spatial geometries (points, boxes, or polygons) uniformly distributed across a spatial extent for benchmarking and testing.

### Parameters
- `a` (`Double`): The inclusive lower bound of the uniform distribution range (for the scalar mathematical function).
- `b` (`Double`): The exclusive upper bound of the uniform distribution range (for the scalar mathematical function).

### Input
- **For the scalar function (`uniform(a, b)`):** Requires two `Double` values where `a < b`.
- **For the RDD generator (`uniform(cardinality)`):** Requires an initialized `SparkContext` (`sc`). The caller must provide a `cardinality` (`Long`) representing the total number of spatial features to generate. It is typically called on `sc.generateSpatialData` or a `SpatialGeneratorBuilder`.
- **Preconditions (RDD Generator):** If generating complex geometries (boxes or polygons), the builder should be configured first using `.config()` with keys like `UniformDistribution.GeometryType` (e.g., `"box"`, `"polygon"`), `UniformDistribution.MaxSize` (e.g., `"0.2,0.1"`), and optionally bounded by an MBR using `.mbr(envelope)`.

### Output
Returns `Double` — A randomly generated numeric value in the range `[a, b)`. 
*(Note: The overloads return a `SpatialRDD` or `JavaSpatialRDD` representing a distributed Spark dataset of generated spatial features (`IFeature`) uniformly distributed across the configured space).*

### Valid Call Patterns
```scala
import edu.ucr.cs.bdlab.beast._
import edu.ucr.cs.bdlab.beast.generator._
import edu.ucr.cs.bdlab.beast.geolite.EnvelopeNDLite

// 1. Generate a massive SpatialRDD of uniform random points using the context extension
val randomPoints: SpatialRDD = sc.generateSpatialData.uniform(1000000000L)

// 2. Generate a configured SpatialRDD of uniform random polygons within a specific MBR
val desiredMBR = new EnvelopeNDLite(2.0, 2.0, 3.0, 9.0, 8.0)
val randomPolygons: SpatialRDD = new SpatialGeneratorBuilder(sc)
  .mbr(desiredMBR)
  .config(UniformDistribution.GeometryType, "polygon")
  .config(UniformDistribution.MaxSize, "0.2,0.1")
  .config(UniformDistribution.NumSegments, 10)
  .config(SpatialGenerator.Seed, 1794)
  .uniform(100L)
```

### LLM Instruction Prompt
- When generating synthetic spatial data for benchmarking in Beast, use the `uniform(cardinality: Long)` overload via `sc.generateSpatialData.uniform(...)` or `new SpatialGeneratorBuilder(sc).uniform(...)`.
- Always configure the generator *before* calling `.uniform(cardinality)` if you need non-point geometries. Use `.config(UniformDistribution.GeometryType, "box")` or `"polygon"`.
- When configuring `UniformDistribution.MaxSize`, provide the dimensions as a comma-separated string (e.g., `"0.01,0.01"`).
- Do not confuse the scalar math utility `uniform(a: Double, b: Double)` with the RDD generator `uniform(cardinality: Long)`.

### Prompt Snippet
```text
Generate a SpatialRDD of 10 million random boxes uniformly distributed across the default space.
```

### Common Failure Modes
- **Missing Configuration Imports:** Failing to import `edu.ucr.cs.bdlab.beast.generator._` will cause compilation errors when trying to access configuration constants like `UniformDistribution.GeometryType`.
- **Malformed Configuration Values:** Passing invalid string formats to `.config()` (e.g., passing a single number to `MaxSize` instead of a comma-separated string like `"width,height"`) will cause runtime parsing errors during generation.
- **Type Mismatch on Cardinality:** Passing an `Int` instead of a `Long` for massive datasets (e.g., `10000000000` without the `L` suffix) will cause standard Scala integer overflow or compilation errors.

### Fix Code Hint
```scala
// BAD: Missing configuration for boxes, and missing 'L' on large cardinality
val badBoxes = sc.generateSpatialData.uniform(10000000000)

// GOOD: Properly configured builder with Long cardinality
import edu.ucr.cs.bdlab.beast.generator._
val goodBoxes = sc.generateSpatialData
  .config(UniformDistribution.GeometryType, "box")
  .config(UniformDistribution.MaxSize, "0.01,0.01")
  .uniform(10000000000L)
```

## API Test: `uniformHistogramCount`

### Signature
```scala
def uniformHistogramCount(histogramSize: Array[Int], prefixSum: Boolean = false): AbstractHistogram
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/CGOperationsMixin.scala:67_

_Source doc:_ Computes a uniform histogram with the given size that counts number of features in each cell @param histogramSize the size of the histogram as the number of partitions along each dimension @param prefixSum     compute the prefix sum on the result to speed up range tests @return the created histogram

### Goal
Computes a uniform spatial histogram over a vector dataset, counting the number of features that fall into each grid cell of a specified multi-dimensional grid.

### Parameters
- `histogramSize` (`Array[Int]`): The dimensions of the grid (e.g., `Array(100, 100)` for a 100x100 2D grid) representing the number of partitions/cells along each spatial axis.
- `prefixSum` (`Boolean`), default `false`: If `true`, computes the prefix sum (cumulative sum) over the grid cells, which allows for constant-time range queries (e.g., `histogram.getValue(min, max)`).

### Input
A spatial RDD of vector features (e.g., `RDD[IFeature]` or `SpatialRDD`) loaded via Beast context extensions like `sc.shapefile`, `sc.geojsonFile`, or `sc.readCSVPoint`. The data must have valid spatial geometries.

### Output
Returns `AbstractHistogram` — an object representing the spatial distribution of feature counts across the uniform grid. If `prefixSum` is true, it can be queried in constant time for range estimates.

### Valid Call Patterns
```scala
// Basic uniform histogram count
val countHistogram = features.uniformHistogramCount(Array(100, 100))

// Uniform histogram with prefix sum enabled for fast range queries
val histogram = polygons.uniformHistogramCount(Array(100, 100), prefixSum = true)
// The following function will run in constant time regardless of the size of the range
val rangeCount = histogram.getValue(Array(4, 3), Array(10, 10))
```

### LLM Instruction Prompt
- Call `uniformHistogramCount` directly on a spatial RDD (`RDD[IFeature]`).
- Provide the grid dimensions as an `Array[Int]` matching the spatial dimensions of the data (typically 2D, e.g., `Array(100, 100)`).
- Set `prefixSum = true` if the resulting histogram will be used for fast range tests or approximate query processing.
- Note that this is a simple histogram. It counts the number of features in each cell but does not account for features spanning multiple grid cells (which may lead to double-counting). If accurate accounting of overlapping features is required, use `eulerHistogramSize` instead.

### Prompt Snippet
```text
To compute a spatial distribution of vector features, use `rdd.uniformHistogramCount(Array(numX, numY))`. Set `prefixSum = true` if you need to perform constant-time range queries on the resulting `AbstractHistogram`. Remember that simple histograms may double-count features spanning multiple cells.
```

### Common Failure Modes
- **Dimension Mismatch:** Providing a 1D or 3D `histogramSize` array for 2D spatial data. The length of `histogramSize` must match the coordinate dimensions of the geometries.
- **Double Counting Large Features:** Assuming the sum of all cells equals the exact total feature count. Features that intersect multiple grid cells will be counted in each intersecting cell. (Use Euler histograms if exact topological accounting is needed).
- **Missing Spatial Context:** Attempting to call this on a standard Spark `RDD[String]` or `DataFrame` before parsing it into an `RDD[IFeature]` using Beast's spatial readers.

### Fix Code Hint
```scala
// Incorrect: Calling on raw text or missing prefixSum for range queries
// val lines = sc.textFile("data.csv")
// val hist = lines.uniformHistogramCount(Array(100, 100))

// Correct: Load as SpatialRDD first, then compute histogram
val points: RDD[IFeature] = sc.readCSVPoint("data.csv", "x", "y")
val hist = points.uniformHistogramCount(Array(100, 100), prefixSum = true)
val countInRange = hist.getValue(Array(0, 0), Array(50, 50))
```

## API Test: `uniformHistogramSize`

### Signature
```scala
def uniformHistogramSize(histogramSize: Array[Int], prefixSum: Boolean = false, sizeFunction: IFeature => Int = _.getStorageSize): AbstractHistogram
```
_Source: beast/cg/src/main/scala/edu/ucr/cs/bdlab/beast/cg/CGOperationsMixin.scala:78_

_Source doc:_ Computes a uniform histogram with the given size that calculates the size of the data in each cell @param histogramSize the size of the histogram as the number of partitions along each dimension @param prefixSum     compute the prefix sum on the result to speed up range tests @param sizeFunction  an optional function that computes the size of a feature. @return the created histogram

### Goal
Computes a uniform spatial histogram over a vector dataset where each grid cell records the total storage size (in bytes) of the features it intersects, which is useful for load balancing and approximate query processing.

### Parameters
- `histogramSize` (`Array[Int]`): The dimensions of the histogram grid, specified as the number of partitions/bins along each spatial axis (e.g., `Array(100, 100)` for a 100x100 2D grid).
- `prefixSum` (`Boolean`), default `false`: A flag indicating whether to compute a prefix sum over the histogram cells, which optimizes subsequent range tests.
- `sizeFunction` (`IFeature => Int`), default `_.getStorageSize`: A custom function to calculate the size of an individual `IFeature`. Defaults to the in-memory storage size, but can be overridden to estimate serialized size (e.g., using `FeatureWriterSizeFunction`).

### Input
A Spatial RDD of vector features (`RDD[IFeature]`), typically loaded via `sc.shapefile`, `sc.geojsonFile`, or similar context extensions. This operation is specific to vector data and cannot be called directly on a Raster RDD.

### Output
Returns `AbstractHistogram` — a spatial grid representation where each cell contains the aggregated size (based on `sizeFunction`) of all features falling within its spatial bounds.

### Valid Call Patterns
```scala
// Standard usage with default in-memory storage size
val sizeHistogram = features.uniformHistogramSize(Array(100, 100))

// Custom usage estimating the size if features were written as GeoJSON
val sizeGeoJsonHistogram = features.uniformHistogramSize(Array(100, 100),
    sizeFunction = new FeatureWriterSizeFunction("iformat" -> "geojson"))
```

### LLM Instruction Prompt
- Call `uniformHistogramSize` as an extension method on a Spatial RDD (`RDD[IFeature]`).
- Provide the grid dimensions as an `Array[Int]` matching the dimensionality of the data (typically 2D, e.g., `Array(100, 100)`).
- Use this method when you need to estimate data volume or storage size per spatial region (e.g., for spatial partitioning). If you only need the number of features per cell, use `uniformHistogramCount` instead.
- To estimate the size of features for a specific output format rather than in-memory size, override `sizeFunction` with `new FeatureWriterSizeFunction("iformat" -> "<format>")`.

### Prompt Snippet
```text
Use rdd.uniformHistogramSize(Array(x, y)) to compute a spatial grid of feature storage sizes for load balancing or partitioning.
```

### Common Failure Modes
- **Calling on Raster Data:** Attempting to call this on a `RasterRDD` or `RDD[ITile]`. This method is part of `CGOperationsMixin` and requires an `RDD[IFeature]`.
- **Dimensionality Mismatch:** Providing a 1D array for `histogramSize` when the underlying geometries are 2D. The array length must match the spatial dimensions.
- **Missing Imports:** Failing to import Beast implicits, which are required to expose `uniformHistogramSize` on a standard Spark `RDD`.

### Fix Code Hint
```scala
// Ensure the receiver is a vector RDD (RDD[IFeature]) and the array matches 2D space
import edu.ucr.cs.bdlab.beast._
val features: RDD[IFeature] = sc.shapefile("data.zip")
val sizeHistogram = features.uniformHistogramSize(Array(256, 256))
```

## API Test: `using`

### Signature
```scala
def using[A <: AutoCloseable, B](resource: A)
```
_Source: inferred from provided API facts and test suite usage_

### Goal
Safely manages an `AutoCloseable` resource (such as a database connection, statement, or result set) by executing a block of code and ensuring the resource is automatically closed afterward to prevent resource leaks.

### Parameters
- `resource` (`A`): An instance of a class that implements `java.lang.AutoCloseable` (e.g., JDBC `Connection`, `PreparedStatement`, `ResultSet`). Note: While the reflected signature shows one parameter list, real usage requires a second parameter list containing the closure block to execute.

### Input
An initialized, open resource that implements the `AutoCloseable` interface. 

### Output
Returns `unspecified` — The result of the executed closure block (type `B`), with the guarantee that the provided resource has been safely closed upon completion or exception.

### Valid Call Patterns
```scala
// Managing a JDBC database connection
using(DriverManager.getConnection(s"jdbc:h2:$datasetsPath/beast", "sa", "")) { dbConnection =>
  DatasetProcessor.createDB(dbConnection)
  
  // Managing a PreparedStatement
  val insertSQL: String = "INSERT INTO datasets(name, dir_name, source_uri, source_format, status) VALUES (?, ?, ?, ?, ?)"
  using(dbConnection.prepareStatement(insertSQL)) { insertStatement =>
    insertStatement.setString(1, "cities")
    insertStatement.setString(2, "cities")
    // ...
    insertStatement.executeUpdate()
  }
}

// Managing a Statement and ResultSet
using(dbConnection.createStatement()) { statement =>
  using(statement.executeQuery("SELECT * FROM datasets WHERE name='cities'")) { data =>
    assert(data.next())
    val status = data.getString("status")
  }
}
```

### LLM Instruction Prompt
- When generating code that interacts with `AutoCloseable` resources (like JDBC connections, statements, or file streams) in Beast/RDPro, wrap the resource initialization in the `using(...) { resource => ... }` loan pattern to ensure safe closure and prevent resource leaks. Do not manually call `.close()`.

### Prompt Snippet
```text
using(dbConnection.createStatement()) { statement =>
  // perform operations with statement
}
```

### Common Failure Modes
- **Accessing Resource Outside Block:** Attempting to use the resource or any derived iterators (like a `ResultSet`) after the `using` block has terminated. The resource will already be closed, throwing an exception (e.g., `SQLException: Statement is closed`).
- **Type Mismatch:** Passing an object to `using` that does not implement `java.lang.AutoCloseable`. The compiler will reject it due to the `A <: AutoCloseable` type bound.

### Fix Code Hint
```scala
// BAD: Resource leaks if an exception occurs, or manual close is forgotten
val stmt = dbConnection.createStatement()
stmt.executeQuery("...")
stmt.close()

// GOOD: Wrapped in `using`
using(dbConnection.createStatement()) { stmt =>
  stmt.executeQuery("...")
}
```

## API Test: `writeSpatialFile`

### Signature
```scala
def writeSpatialFile(filename: String, oformat: String, opts: BeastOptions = new BeastOptions): Unit
def writeSpatialFile(rdd: JavaSpatialRDD, filename: String, oformat: String, opts: BeastOptions): Unit
def writeSpatialFile(rdd: JavaSpatialRDD, filename: String, oformat: String): Unit
```
_Source: beast/beast-spark/src/main/scala/edu/ucr/cs/bdlab/beast/JavaSpatialRDDHelper.scala:94  (+2 more definition site/overload)_

_Source doc:_ Write this RDD as a spatial file with the given format and additional options @param filename the output file name @param oformat the output file format (short name) @param opts additional user options

### Goal
Write a distributed `SpatialRDD` to disk as a spatial file in a specified format (e.g., CSV, GeoJSON, Shapefile) with optional configuration parameters.

### Parameters
- `rdd` (`JavaSpatialRDD`): The spatial RDD to write. This parameter is explicitly required when using the Java API (`JavaSpatialRDDHelper.writeSpatialFile`); in Scala, the function is called as an extension method directly on the `SpatialRDD` instance.
- `filename` (`String`): The destination file path or directory name where the output will be saved.
- `oformat` (`String`): The short name of the output file format (e.g., `"envelope"`, `"csv"`, `"shapefile"`, `"geojson"`, `"kml"`, `"kmz"`).
- `opts` (`BeastOptions`): Additional user options to configure the writer (e.g., specifying an output separator for CSVs). Defaults to an empty `BeastOptions`.

### Input
A `SpatialRDD` (or `JavaSpatialRDD`) containing vector features or geometric envelopes. The RDD can be spatially partitioned (e.g., via `spatialPartition`) or unpartitioned. The caller must provide a valid output format string supported by Beast for vector data. 

### Output
Returns `Unit` — the operation triggers a Spark job that writes the distributed RDD partitions to the specified `filename` on the file system in the requested `oformat`.

### Valid Call Patterns
```scala
// Scala: Writing an RDD of envelopes to disk without extra options
sparkContext.parallelize(r1)
  .asInstanceOf[SpatialRDD]
  .spatialPartition(grid)
  .writeSpatialFile(index1Path, "envelope")

// Scala: Writing with additional BeastOptions (passed as implicit tuples)
records.writeSpatialFile("output.csv", "envelope", "oseparator" -> ",")

// Java: Using the helper class
JavaSpatialRDDHelper.writeSpatialFile(records, "output.csv", "envelope", new BeastOptions("oseparator:,"));
```

### LLM Instruction Prompt
- In Scala, call `writeSpatialFile` as an extension method directly on a `SpatialRDD`.
- Always provide the `filename` and the `oformat` (e.g., `"csv"`, `"shapefile"`, `"geojson"`, `"envelope"`).
- Pass additional configuration options (like `"oseparator" -> ","`) as trailing arguments in Scala, which implicitly convert to `BeastOptions`.
- **Do not** use `writeSpatialFile` to save Raster RDDs (GeoTIFFs). For raster data, use `raster.saveAsGeoTiff(filename)` instead.

### Prompt Snippet
```text
To save vector features or spatial partitions to disk in Beast, use the `writeSpatialFile` extension method on the `SpatialRDD`. Specify the output path and the format short-name (e.g., "csv", "geojson", "shapefile"). You can pass extra options like `"oseparator" -> ","` for CSVs. Note: For saving raster data, use `saveAsGeoTiff` instead.
```

### Common Failure Modes
- **Using `writeSpatialFile` for Rasters:** Attempting to save a `RasterRDD` using `writeSpatialFile` instead of the dedicated `saveAsGeoTiff` method, leading to type errors or unsupported format exceptions.
- **Unsupported Output Format:** Providing an `oformat` string that Beast does not support for writing (e.g., trying to write to `"gpx"`, which is input-only). Supported vector outputs are CSV, Esri Shapefile, GeoJSON, JSON+WKT, KML, KMZ, and envelope.
- **Missing Separator Options:** Writing to `"csv"` or `"envelope"` without specifying the `"oseparator"` option when a specific delimiter is required by downstream tasks, resulting in default formatting that may not match expectations.

### Fix Code Hint
```scala
// Incorrect: Trying to save a raster using writeSpatialFile
// raster.writeSpatialFile("output.tif", "geotiff")

// Correct: Saving a raster
raster.saveAsGeoTiff("output.tif")

// Correct: Saving a vector SpatialRDD to CSV with a custom separator
vectorRdd.writeSpatialFile("output.csv", "csv", "oseparator" -> "|")
```

## API Test: `x1`

### Signature
```scala
def x1: Int
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/SlidingWindowTile.scala:14_

### Goal
Retrieves the minimum X coordinate (starting column index) of the raster tile's pixel grid.

### Parameters
_None._

### Input
An instantiated raster tile object (such as `ITile[T]` or `MemoryTile[T]`) representing a chunk of a raster dataset.

### Output
Returns `Int` — the starting column index (minimum X coordinate) of the tile's pixel grid.

### Valid Call Patterns
```scala
// Iterate over all defined pixels in a tile using x1, x2, y1, and y2
var pixelCount = 0
for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
  pixelCount += 1
  // Access pixel value with tile.getPixelValue(x, y)
}
```

### LLM Instruction Prompt
- When generating code to iterate over pixels in an `ITile` or `MemoryTile`, use `tile.x1` as the starting bound for the X (column) loop. 
- Do not confuse `x1` with spatial coordinates (e.g., longitude or easting); it is strictly a pixel grid index.
- Always call `x1` on an individual tile instance, not on a distributed `RasterRDD`.

### Prompt Snippet
```text
To iterate over a tile's columns in RDPro, use `x <- tile.x1 to tile.x2`. Remember that `x1` is a pixel grid index, not a spatial coordinate.
```

### Common Failure Modes
- **Confusing grid indices with spatial coordinates:** Assuming `x1` returns a geographic bounding box coordinate (like longitude) rather than the integer column index of the pixel grid.
- **Calling on the wrong abstraction level:** Attempting to call `x1` directly on a `RasterRDD` instead of mapping over its constituent `ITile` elements.
- **Out-of-bounds access:** Iterating from `0` instead of `tile.x1`, which will fail or yield incorrect results if the tile's local grid does not start at `0`.

### Fix Code Hint
```scala
// WRONG: Assuming tile starts at 0 or using spatial coordinates
// for (x <- 0 to tile.width) { ... }

// RIGHT: Use x1 and x2 for the exact column bounds of the tile
for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
  val value = tile.getPixelValue(x, y)
}
```

## API Test: `x2`

### Signature
```scala
def x2: Int
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/SlidingWindowTile.scala:16_

### Goal
Returns the maximum X-coordinate (column index) of the raster tile's pixel grid, representing the inclusive upper bound of the tile's width in pixel space.

### Parameters
_None._

### Input
A raster tile instance (such as `ITile[T]` or `MemoryTile[T]`) that has been loaded into memory, typically as part of a `RasterRDD` generated from reading a GeoTIFF or HDF file.

### Output
Returns `Int` — the maximum X-coordinate (column index) of the tile.

### Valid Call Patterns
```scala
// Pattern 1: Iterating over all valid pixels in a tile
var pixelCount = 0
for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
  pixelCount += 1
}

// Pattern 2: Accessing or modifying the boundary pixel
tile.setPixelValue(tile.x2, tile.y2, Array[Byte](10, 20, 30))
```

### LLM Instruction Prompt
- Use `tile.x2` to retrieve the inclusive maximum X-coordinate (column index) of a raster tile.
- Combine `x2` with `x1`, `y1`, and `y2` to construct standard Scala `for` comprehensions (`x1 to x2`) when iterating over a tile's pixel grid.
- Do not confuse `x2` (a pixel/column index) with spatial coordinates (e.g., longitude or projected meters).
- Call this method on an individual tile (e.g., inside a `mapPixels` or `map` operation), not directly on a `RasterRDD`.

### Prompt Snippet
```text
To iterate over the pixels of an RDPro raster tile, use a for-comprehension with the tile's pixel bounds: `for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y))`. `x2` provides the inclusive maximum column index.
```

### Common Failure Modes
- **Calling on the RDD instead of the Tile:** Attempting to call `rasterRDD.x2` will fail. `x2` is a property of the individual `ITile` or `MemoryTile` objects contained within the RDD.
- **Off-by-one errors (Exclusive vs. Inclusive):** Treating `x2` as an exclusive upper bound (e.g., using `until x2`). The test suite explicitly uses `to tile.x2`, indicating it is the inclusive maximum index.
- **Confusing Pixel Coordinates with Spatial Coordinates:** Assuming `x2` returns a geographic bounding box coordinate (like maximum longitude). It strictly returns an integer representing the pixel column index.

### Fix Code Hint
```scala
// WRONG: Attempting to get bounds from the RDD directly
// val maxX = rasterRDD.x2 

// RIGHT: Accessing x2 on the individual tiles within the RDD
val processedRaster = rasterRDD.map(tile => {
  for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
    // Perform pixel-level math here
  }
  tile
})
```

## API Test: `y1`

### Signature
```scala
def y1: Int
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/SlidingWindowTile.scala:15_

### Goal
Returns the minimum Y coordinate (starting row index) of the raster tile's pixel grid.

### Parameters
_None._

### Input
An initialized raster tile object (such as `ITile[T]`, `MemoryTile[T]`, or `SlidingWindowTile`) that has been loaded from a raster dataset or created in memory.

### Output
Returns `Int` — the starting Y coordinate (row index) of the tile's bounding box in pixel space.

### Valid Call Patterns
```scala
// Iterate over all defined pixels in a tile using its coordinate bounds
var pixelCount = 0
for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
  pixelCount += 1
}

// Accessing the boundary directly
val startY: Int = tile.y1
```

### LLM Instruction Prompt
- Use `tile.y1` in conjunction with `tile.y2`, `tile.x1`, and `tile.x2` to establish the correct bounding loops when iterating over the pixels of an `ITile`.
- NEVER assume a tile's local pixel grid starts at `0`. Distributed raster tiles often retain their global pixel coordinates or specific offsets.
- ALWAYS guard pixel access within the `y1` to `y2` range with `tile.isDefined(x, y)` to safely handle sparse tiles or masked pixels.

### Prompt Snippet
```text
To iterate over a raster tile's pixels in RDPro, loop from `tile.y1 to tile.y2` and `tile.x1 to tile.x2`, ensuring you check `if tile.isDefined(x, y)` before calling `getPixelValue`.
```

### Common Failure Modes
- **Assuming 0-based indexing:** Hardcoding loops from `0 until height` instead of using `y1` to `y2`. This will fail or read incorrect data for tiles that represent a sub-region of a larger global raster.
- **Unsafe pixel access:** Iterating from `y1` to `y2` and blindly calling `getPixelValue(x, y)` without checking `isDefined(x, y)`, which throws errors on sparse or masked pixels.

### Fix Code Hint
```scala
// Incorrect: Hardcoding 0-based indices and missing definition checks
for (y <- 0 until 100; x <- 0 until 100) {
  val v = tile.getPixelValue(x, y) 
}

// Correct: Using y1/y2 bounds and checking if the pixel is defined
for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
  val v = tile.getPixelValue(x, y)
}
```

## API Test: `y2`

### Signature
```scala
def y2: Int
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/SlidingWindowTile.scala:17_

### Goal
Returns the maximum Y coordinate (inclusive row index) of the raster tile's pixel grid.

### Parameters
_None._

### Input
A valid raster tile object (such as `MemoryTile[T]` or `ITile[T]`) that has been loaded into memory or yielded by a raster RDD operation (e.g., during a Raptor join or pixel iteration).

### Output
Returns `Int` — the maximum Y coordinate (row index) of the tile.

### Valid Call Patterns
```scala
// Pattern 1: Iterating over all pixels in a tile using inclusive bounds
var pixelCount = 0
for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
  pixelCount += 1
}

// Pattern 2: Accessing or modifying the bottom-most row of the tile
tile.setPixelValue(tile.x2, tile.y2, Array[Byte](10, 20, 30))
```

### LLM Instruction Prompt
- Use `tile.y2` to get the maximum Y coordinate (row index) of a raster tile.
- Always treat `y2` as an **inclusive** bound when iterating over the tile's grid (use `to tile.y2`, not `until tile.y2`).
- Combine `y2` with `y1`, `x1`, and `x2` to define the complete bounding box of the tile's pixel coordinates.

### Prompt Snippet
```text
To iterate over all pixels in an RDPro raster tile, use `tile.y1 to tile.y2` for the Y-axis and `tile.x1 to tile.x2` for the X-axis. `y2` represents the inclusive maximum row index of the tile. Always check `tile.isDefined(x, y)` before accessing the pixel value.
```

### Common Failure Modes
- **Off-by-one errors during iteration:** Treating `y2` as an exclusive upper bound (using `until tile.y2` instead of `to tile.y2`), which causes the bottom-most row of the tile to be skipped during processing.
- **Confusing pixel indices with spatial coordinates:** Assuming `y2` returns a spatial coordinate (like latitude or projected Y). It returns a discrete pixel row index.

### Fix Code Hint
```scala
// WRONG: 'until' skips the last row of the tile
for (y <- tile.y1 until tile.y2; x <- tile.x1 until tile.x2) {
  // ...
}

// RIGHT: 'to' correctly includes the y2 boundary
for (y <- tile.y1 to tile.y2; x <- tile.x1 to tile.x2; if tile.isDefined(x, y)) {
  // ...
}
```

## API Test: `zigzagDecode`

### Signature
```scala
def zigzagDecode(x: Int): Int
```
_Source doc:_ Decodes a value from Zigzag encoding

### Goal
Decodes a Zigzag-encoded integer back into its original signed integer value, typically used when parsing or inspecting raw Mapbox Vector Tile (MVT) geometry coordinates and commands.

### Parameters
- `x` (`Int`): The Zigzag-encoded integer value to decode.

### Input
A Zigzag-encoded integer. In the context of Beast's visualization and MVT generation, this is usually extracted directly from the raw geometry array of a compiled MVT feature (e.g., `feature.getGeometry(index)`).

### Output
Returns `Int` — The decoded signed integer, which typically represents a coordinate delta or command integer in the MVT image space.

### Valid Call Patterns
```scala
// Assuming `feature` is a VectorTile.Tile.Feature from an MVT layer
val encodedX = feature.getGeometry(1)
val encodedY = feature.getGeometry(2)

val decodedX = VectorLayerBuilder.zigzagDecode(encodedX)
val decodedY = VectorLayerBuilder.zigzagDecode(encodedY)
```

### LLM Instruction Prompt
- Use `VectorLayerBuilder.zigzagDecode(x)` to decode Zigzag-encoded integers when manually inspecting or parsing Mapbox Vector Tile (MVT) geometries.
- Do not use this for general raster pixel math or standard vector coordinates; it is strictly a low-level utility for MVT protocol buffer decoding.
- Always qualify the call with the `VectorLayerBuilder` object.

### Prompt Snippet
```text
To decode Zigzag-encoded integers from raw MVT geometries, use `VectorLayerBuilder.zigzagDecode(x)`.
```

### Common Failure Modes
- **Passing standard (non-encoded) integers:** Passing an already decoded or standard coordinate integer will result in an incorrect, mangled signed integer output. Only pass values known to be Zigzag-encoded.
- **Missing object qualifier:** Calling `zigzagDecode(x)` without the `VectorLayerBuilder` object qualifier will cause a compilation error.

### Fix Code Hint
```scala
// WRONG: Calling without the object qualifier
// val x = zigzagDecode(feature.getGeometry(1))

// RIGHT: Qualify with VectorLayerBuilder
val x = VectorLayerBuilder.zigzagDecode(feature.getGeometry(1))
```

## API Test: `zonalStats2`

### Signature
```scala
def zonalStats2[T](zones: RDD[IFeature], raster: RDD[ITile[T]], collectorClass: Class[_ <: Collector], opts: BeastOptions, numTiles: LongAccumulator = null)
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ZonalStatistics.scala:128_

_Source doc:_ Computes zonal statistics between a set of zones (polygons) and a raster file given by its path and a layer in that file. The result is an RDD of pairs of a feature and a collector value @param zones a set of polygons that represent the regions or zones @param raster the RDD of tiles @param collectorClass the class that collects the pixel values to compute the statistics @param opts additional user-defined options @param numTiles an optional accumulator to collect the total number of processed tiles @return a set of (Feature, Statistics)

### Goal
Computes zonal statistics (such as count, sum, min, max) by matching a set of vector zones (polygons) against a distributed raster dataset, returning an RDD of features paired with their computed statistics.

### Parameters
- `zones` (`RDD[IFeature]`): An RDD of vector features (typically polygons) representing the regions or administrative boundaries over which to aggregate raster pixels.
- `raster` (`RDD[ITile[T]]`): An RDD of raster tiles containing the pixel values to be aggregated. The type `T` must match the underlying raster data type.
- `collectorClass` (`Class[_ <: Collector],
                  opts: BeastOptions, numTiles: LongAccumulator`), default `null`: 
  *Note: The JSON signature parser merged three parameters here. They represent:*
  1. `collectorClass`: The class of the `Collector` (e.g., `classOf[Statistics]`) used to aggregate pixel values.
  2. `opts`: `BeastOptions` for user-defined configuration.
  3. `numTiles`: An optional Spark `LongAccumulator` to track the total number of processed tiles (defaults to `null`).

### Input
- **Vector Zones:** An `RDD[IFeature]` loaded from formats like Shapefile, GeoJSON, or CSV. If the vectors and raster have different Coordinate Reference Systems (CRS), the vectors must be reprojected first (e.g., using `Reprojector.reprojectRDD`).
- **Raster Tiles:** An `RDD[ITile[T]]` loaded via `sc.geoTiff[T]` or `new RasterFileRDD[T]`. 
- **Preconditions & Type Selection:** 
  - The generic type `T` must exactly match the raster's runtime pixel type (e.g., `Int` for `IntegerType`, `Float` for `FloatType`).
  - **Raptor Predicate Rule:** Polygons match pixels whose *center* falls inside the polygon boundary.

### Output
Returns `unspecified` — Represents an `RDD[(IFeature, Collector)]`. Each tuple contains the original vector feature and a `Collector` instance (e.g., `Statistics`) holding the aggregated pixel math (count, sum, etc.) for that specific zone.

### Valid Call Patterns
```scala
// Assuming sparkContext is available and BeastOptions is imported
val vectorFile = locateResource("/vectors/ne_110m_admin_1_states_provinces.zip")
val rasterFile = locateResource("/rasters/glc2000_small.tif")

val polygons: RDD[IFeature] = SpatialReader.readInput(sparkContext, new BeastOptions(), vectorFile.getPath, "shapefile")
val raster: RDD[ITile[Int]] = new RasterFileRDD[Int](sparkContext, rasterFile.getPath, new BeastOptions())

// Call ZonalStatistics.zonalStats2 statically
val zsResults: RDD[(IFeature, Collector)] = ZonalStatistics.zonalStats2(
  polygons, 
  raster, 
  classOf[Statistics], 
  new BeastOptions()
)

// Extracting statistics requires casting the Collector
val processedStats = zsResults.map { case (feature, collector) =>
  val stats = collector.asInstanceOf[Statistics]
  val count = stats.count(0)
  val sum = stats.sum(0)
  (feature, count, sum)
}
```

### LLM Instruction Prompt
- Call `ZonalStatistics.zonalStats2(zones, raster, classOf[Statistics], new BeastOptions())` statically; it is not an implicit method on the RDD.
- Ensure the generic type `T` of the raster `RDD[ITile[T]]` exactly matches the physical pixel type of the GeoTIFF (e.g., `Int` or `Float`).
- The returned `Collector` must be cast to the specific class passed in `collectorClass` (e.g., `.asInstanceOf[Statistics]`) before you can access its aggregation methods like `.count(band)` or `.sum(band)`.
- If the vector and raster datasets are in different CRSs, reproject the vector `RDD[IFeature]` to match the raster before calling `zonalStats2`.

### Prompt Snippet
```text
To compute zonal statistics in RDPro, use `ZonalStatistics.zonalStats2(zones, raster, classOf[Statistics], new BeastOptions())`. The raster type `T` must match the file's pixel type. Cast the resulting `Collector` to `Statistics` to access `.count(0)` and `.sum(0)`.
```

### Common Failure Modes
- **Type Mismatch:** Loading a Float GeoTIFF as `sc.geoTiff[Int]` or passing an `RDD[ITile[Float]]` to `zonalStats2` while expecting integer statistics. The type `T` must be strictly aligned.
- **ClassCastException on Output:** Attempting to call methods directly on the returned `Collector` trait without first casting it to the concrete class (e.g., `Statistics`) provided in the `collectorClass` parameter.
- **Empty Results due to CRS Mismatch:** Passing vector zones that do not overlap the raster because they are in a different coordinate reference system. Vectors must be reprojected to the raster's CRS prior to the join.

### Fix Code Hint
```scala
// BAD: Calling methods directly on the Collector trait
val badResults = ZonalStatistics.zonalStats2(zones, raster, classOf[Statistics], opts)
  .map(fc => fc._2.sum(0)) // ERROR: value sum is not a member of Collector

// GOOD: Cast the Collector to Statistics first
val goodResults = ZonalStatistics.zonalStats2(zones, raster, classOf[Statistics], opts)
  .map(fc => fc._2.asInstanceOf[Statistics].sum(0))
```

## API Test: `zonalStatsLocal`

### Signature
```scala
def zonalStatsLocal[T](geometries: Array[Geometry], raster: IRasterReader[T], collectorClass: Class[_ <: Collector]) : Array[Collector]
def zonalStatsLocal[T](zones: Array[IFeature], raster: IRasterReader[T], collectorClass: Class[_ <: Collector]) : Array[Collector]
```
_Source: beast/raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ZonalStatistics.scala:162  (+1 more definition site/overload)_

_Source doc:_ Run zonal statistics locally in one thread. This is useful when the array of geometries is small and the overhead of partitioning could be high. @param zones the array of features that describe the zones. @param raster the raster reader that points to the raster file being aggregated @param collectorClass the class that computes the statistics @return an array of collectors that is equal in length to the input array of features with the result for each. Features that do not overlap any pixels will have null.

### Goal
Compute zonal statistics (e.g., count, sum) locally in a single thread for a small set of vector geometries against a raster, avoiding the overhead of distributed Spark partitioning.

### Parameters
- `geometries` (`Array[Geometry]`): The array of vector geometries (or `IFeature` via overload) that define the zones for aggregation.
- `raster` (`IRasterReader[T]`): The initialized raster reader (e.g., `GeoTiffReader[T]`) pointing to the raster file being aggregated.
- `collectorClass` (`Class[_ <: Collector]`): The class that computes the statistics (e.g., `classOf[Statistics]`).

### Input
- **Geometries:** An array of geometries or features small enough to be processed efficiently in a single thread on the driver.
- **Raster Reader:** An initialized `IRasterReader[T]`. The type parameter `T` must exactly match the file's runtime pixel type (e.g., `Int` for `IntegerType`, `Float` for `FloatType`).
- **Preconditions:** Raptor join predicates apply to the intersection logic: Points match the single pixel containing them; Lines match pixels intersecting the line's crosshair; Polygons match pixels whose *center* falls inside the polygon boundary.

### Output
Returns `Array[Collector]` — An array of statistics collectors equal in length to the input array of features, containing the aggregated results for each zone. Features that do not overlap any pixels will have `null` at their corresponding index.

### Valid Call Patterns
```scala
// Assuming features: Array[IFeature] and rasterReader: IRasterReader[Int] are already initialized
val zsResults: Array[Collector] = ZonalStatistics.zonalStatsLocal(features, rasterReader, classOf[Statistics])

// Filter out nulls (features with no overlapping pixels) and cast to the specific collector
val actualCounts: Array[Int] = zsResults.filter(_ != null).map(s => s.asInstanceOf[Statistics].count(0).toInt)
val actualSums: Array[Int] = zsResults.filter(_ != null).map(s => s.asInstanceOf[Statistics].sum(0).toInt)
```

### LLM Instruction Prompt
- Call `ZonalStatistics.zonalStatsLocal(...)` when performing zonal statistics on a small, local array of geometries where Spark's distributed `raptorJoin` overhead is unnecessary.
- Ensure the `IRasterReader[T]` type parameter `T` matches the underlying raster's pixel type.
- You MUST handle `null` values in the returned `Array[Collector]`, as any geometry that does not overlap a pixel's center (for polygons) will return `null`.
- Cast the non-null `Collector` objects to the specific collector class passed in (e.g., `asInstanceOf[Statistics]`) to access metrics like `.count(0)` or `.sum(0)`.

### Prompt Snippet
```text
When computing zonal statistics for a small number of geometries without Spark overhead, use `ZonalStatistics.zonalStatsLocal(featuresArray, rasterReader, classOf[Statistics])`. Filter out `null` results (which indicate no overlapping pixels) and cast the remaining collectors to your specific collector class to extract metrics.
```

### Common Failure Modes
- **NullPointerException:** Failing to filter out or check for `null` in the returned `Array[Collector]` before casting or accessing metrics.
- **Type Mismatch:** The type `T` of `IRasterReader[T]` does not match the actual pixel type of the raster file (e.g., using `GeoTiffReader[Int]` for a float raster).
- **Out of Memory / Performance Degradation:** Passing a massive array of geometries that should have been processed using the distributed `raster.raptorJoin(vector)` instead of this local, single-threaded method.

### Fix Code Hint
```scala
val zsResults = ZonalStatistics.zonalStatsLocal(features, rasterReader, classOf[Statistics])

// FIX: Filter nulls (no overlap) and cast to the specific Collector class before accessing metrics
val validStats = zsResults.filter(_ != null).map(_.asInstanceOf[Statistics])
val sums = validStats.map(_.sum(0))
```

