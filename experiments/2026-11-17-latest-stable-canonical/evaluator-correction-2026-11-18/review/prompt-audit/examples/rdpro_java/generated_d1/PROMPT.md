# Recorded system prompt

You write Java code that will be spliced into a runnable test harness.
Java17 with Spark3.5.1. Write Java statements only. The scaffold provides JavaSparkContext sc, SparkSession spark, a tiny EnvelopeNDLite envelope, JTS point/geometryFactory, 4x4 RasterMetadata metadata, and JavaRDD<Integer> numbers. Local raster_tif, vector_shapefile, hdf_file paths are available. Assert a stable result before printing __CHECK__.

Requested target declaration (frozen canonical selection):
Qualified name: edu.ucr.cs.bdlab.raptor.Statistics.isValid
Owner: edu.ucr.cs.bdlab.raptor.Statistics
Declaration: ():boolean
Parameters in declaration order (0): (none)
Write the requested call against this owner and declaration, with its indicated parameter list.
Verified public access paths for the same defining API: edu.ucr.cs.bdlab.raptor.Statistics.isValid. Use a public access path when the defining namespace is internal.

Pick the input variable(s) whose type matches the API's parameters. Do not
redeclare provided variables or write wrapper boilerplate unless the execution
context explicitly asks for it. Output ONLY the body statements that exercise the
API. Use ONLY the documentation provided. Output only code, no markdown fences.

Role: An expert Java developer using public RDPro/Raptor raster APIs.
Project: RDPro Java (Java) - Pinned official Beast0.10.1 production source
Domain: Geospatial computing
Target users: Java geospatial developers
Use cases: Raster processing and raster metadata; Raster/vector joins and zonal statistics; Local Spark transformations supporting raster workflows
Constraints: Use original APIs only.; Use provided local raster, shapefile, and HDF4 fixtures or tiny in-memory values.; Write temporary outputs only under the run output directory.; Do not contact services or change repository files.

# Recorded user prompt

Documentation:
## API Test: `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid`

### Signature
```java
():boolean
```
_Source: source/raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Statistics.java:131_

### Goal
Checks if the current `Statistics` object contains valid, computed statistical data ready for retrieval or further processing.

### Parameters
_None._

### Input
The caller must have an initialized `edu.ucr.cs.bdlab.raptor.Statistics` object. This method is typically called after a raster-vector join or a zonal statistics operation has been performed on the object to ensure the computation completed successfully.

### Output
Returns `boolean` — `true` if the statistics have been successfully calculated and are valid; `false` otherwise.

### Valid Call Patterns
```java
// Inferred from signature:
edu.ucr.cs.bdlab.raptor.Statistics stats = new edu.ucr.cs.bdlab.raptor.Statistics();
// ... perform operations ...
if (stats.isValid()) {
    // Access statistical results
}
```

### LLM Instruction Prompt
- When generating code that accesses statistical results from an `edu.ucr.cs.bdlab.raptor.Statistics` instance, always wrap the access in a conditional check using `isValid()` to prevent processing uninitialized or invalid data.

### Prompt Snippet
```text
if (statisticsInstance.isValid()) {
    // Proceed with data extraction
}
```

### Common Failure Modes
- **Uninitialized State:** Calling `isValid()` on a `Statistics` object that has not yet been populated by a Raptor operation will return `false`.
- **Post-Processing Errors:** If a raster-vector join fails due to CRS mismatch or incompatible data types, the associated `Statistics` object may remain in an invalid state. Always verify `isValid()` before attempting to read values from the object.

### Fix Code Hint
```java
// Ensure the statistics object is valid before usage
if (!stats.isValid()) {
    throw new IllegalStateException("Statistics computation failed or was not performed.");
}
```

Available input path variables already in scope (choose the matching one(s) by type):
Pre-loaded and already in scope — use these directly, do NOT re-load:
- envelope: EnvelopeNDLite
- geometryFactory: GeometryFactory
- point: Point
- metadata: RasterMetadata
- numbers: JavaRDD<Integer>
(raw input path strings also in scope if needed: vector_shapefile, raster_tif, hdf_file, output_dir)

RECEIVER — call `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` on the RIGHT type (calling it on the wrong receiver is
the #1 failure; if it is an instance method, first obtain a value of the owner type,
do NOT call it on an unrelated preloaded input):
(receiver type not resolved)

(none yet)

Write minimal body statements that use `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` correctly per the docs,
reading from the appropriate input variable(s) above.

The snippet MUST EXECUTE the operation AND VERIFY the result is correct — not just
that it ran (some frameworks defer/lazily evaluate, and incorrectly interpreted
data can produce plausible output without throwing). End with a CORRECTNESS CHECK
written in valid Java syntax:
- force the result to materialize and compute a small witness of it — a count, a
  size, or a sampled element;
- use the language's normal assertion mechanism with a FALSIFIABLE condition tied
  to the documented contract or to values chosen earlier in the snippet;
- print a STRUCTURED line whose literal prefix is exactly
  `__CHECK__ java:edu.ucr.cs.bdlab.raptor.Statistics.isValid ` followed by the witness, using the language's normal
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
materialize `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid`, but deliberately fail the assertion with a short message
stating that the documented contract is insufficient to verify the result. This is
a documentation-comprehension test: an unverifiable contract must not earn a pass.
If `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` is itself a writer/output API, use an output binding only when one
is listed among the available inputs or execution context; then read back a small
part of the output, assert a known content/aggregate relation when the documented
contract permits it, and print the same structured line.
Do not call other heavyweight operations unless `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` is the writer; keep the
body focused on `java:edu.ucr.cs.bdlab.raptor.Statistics.isValid` so the run isolates that one call.
Use Java syntax and public library APIs; fully qualify types missing from imports. Throw AssertionError on an unexpected result. Use only tiny local inputs and outputs under output_dir. No network or repository writes. Use the selected target owner and declaration provided in the request.
