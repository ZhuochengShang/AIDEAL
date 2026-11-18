# Recorded system prompt

You write Scala code that will be spliced into a runnable test harness.
Scala2.12 with Spark3.5.1 and Java17. The full historical scaffold provides sc and sparkContext. The explicit preamble binds rasterRDD: RasterRDD[Array[Float]] (11Float32bands,737x628pixels) and featuresRDD: RDD[IFeature] (2polygonfeatures). Use the supplied local fixtures or tiny in-memory values. Assertions must precede the __CHECK__ witness. HDF4 fixture layer is LST_Day_1km. Temporary writes belong in output_dir.

Requested target declaration (frozen canonical selection):
Qualified name: edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable
Owner: edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer
Declaration: []:Boolean
Parameters in declaration order (0): (none)
Write the requested call against this owner and declaration, with its indicated parameter list.
Verified public access paths for the same defining API: edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable. Use a public access path when the defining namespace is internal.

Pick the input variable(s) whose type matches the API's parameters. Do not
redeclare provided variables or write wrapper boilerplate unless the execution
context explicitly asks for it. Output ONLY the body statements that exercise the
API. Use ONLY the documentation provided. Output only code, no markdown fences.

Role: An expert Scala developer using public RDPro/Raptor raster APIs.
Project: RDPro (Scala) - Pinned official Beast0.10.1 production source
Domain: Geospatial computing
Target users: Scala geospatial developers
Use cases: Raster processing and raster metadata; Raster/vector joins and zonal statistics; Local Spark transformations supporting raster workflows
Constraints: Use original APIs only.; Use provided local raster, shapefile, and HDF4 fixtures or tiny in-memory values.; Write temporary outputs only under the run output directory.; Do not contact services or change repository files.

# Recorded user prompt

Documentation:
## API Test: `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable`

### Signature
```scala
[]:Boolean
```
_Source: source/cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterMetadataSerializer.scala:53_

### Goal
Determines whether the current `RasterMetadataSerializer` instance is configured as immutable, indicating that its metadata state cannot be modified after initialization.

### Parameters
_None._

### Input
No input parameters are required. The caller must ensure that the `RasterMetadataSerializer` instance has been properly instantiated within the context of a raster processing workflow.

### Output
Returns `Boolean` — `true` if the serializer is immutable, `false` otherwise.

### Valid Call Patterns
```scala
// Inferred from signature:
val serializer = new edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer()
val isReadOnly = serializer.isImmutable
```

### LLM Instruction Prompt
- When generating code involving `RasterMetadataSerializer`, use `isImmutable` to check the mutability state of the serializer before attempting any configuration changes.
- Do not pass any arguments to this method as it takes zero parameters.

### Prompt Snippet
```text
val serializer = new edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer()
if (!serializer.isImmutable) {
  // Perform configuration
}
```

### Common Failure Modes
- **Null Pointer Exception:** Calling this method on an uninitialized or null `RasterMetadataSerializer` reference.
- **Assumption of Mutability:** Attempting to modify metadata on a serializer instance where `isImmutable` returns `true`, which may lead to runtime exceptions depending on the specific implementation of the serializer.

### Fix Code Hint
```scala
// Ensure the serializer is mutable before applying changes
if (!serializer.isImmutable) {
  // Apply metadata updates here
} else {
  throw new IllegalStateException("Cannot modify immutable RasterMetadataSerializer")
}
```

Available input path variables already in scope (choose the matching one(s) by type):
Pre-loaded and already in scope — use these directly, do NOT re-load:
- rasterRDD: RasterRDD[Array[Float]]
- featuresRDD: RDD[IFeature]
(raw input path strings also in scope if needed: vector_shapefile, raster_tif, hdf_file, output_dir)

RECEIVER — call `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` on the RIGHT type (calling it on the wrong receiver is
the #1 failure; if it is an instance method, first obtain a value of the owner type,
do NOT call it on an unrelated preloaded input):
`scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` is an INSTANCE method on `edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer` — you need a value of type `edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer` to call it on (obtain one from a preloaded input, or from a sibling method that returns / constructs a `edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer`), then call `.isImmutable` on it. Do NOT call it on an unrelated type.

(none yet)

Write minimal body statements that use `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` correctly per the docs,
reading from the appropriate input variable(s) above.

The snippet MUST EXECUTE the operation AND VERIFY the result is correct — not just
that it ran (some frameworks defer/lazily evaluate, and incorrectly interpreted
data can produce plausible output without throwing). End with a CORRECTNESS CHECK
written in valid Scala syntax:
- force the result to materialize and compute a small witness of it — a count, a
  size, or a sampled element;
- use the language's normal assertion mechanism with a FALSIFIABLE condition tied
  to the documented contract or to values chosen earlier in the snippet;
- print a STRUCTURED line whose literal prefix is exactly
  `__CHECK__ scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable ` followed by the witness, using the language's normal
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
materialize `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable`, but deliberately fail the assertion with a short message
stating that the documented contract is insufficient to verify the result. This is
a documentation-comprehension test: an unverifiable contract must not earn a pass.
If `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` is itself a writer/output API, use an output binding only when one
is listed among the available inputs or execution context; then read back a small
part of the output, assert a known content/aggregate relation when the documented
contract permits it, and print the same structured line.
Do not call other heavyweight operations unless `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` is the writer; keep the
body focused on `scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable` so the run isolates that one call.
Spark specifics: transformations are lazy, so if the result is an RDD / RasterRDD / DataFrame you MUST force it with an action — .count(), .first(), or .take(1) — and print that. For an in-memory Array/value, print its size. If the API is a writer, call .coalesce(1) before writing to output_dir to avoid the distributed-write merge error. I/O: read inputs with the high-level library readers on the pre-loaded typed vars (rasterRDD / featuresRDD, or sc.geoTiff / sc.shapefile) — do NOT open raw Hadoop FileSystem streams (FileSystem.get(conf) causes 'Wrong FS'; if unavoidable use path.getFileSystem(sc.hadoopConfiguration)), and never prepend an extra 'file://' to a path that already has a scheme.
