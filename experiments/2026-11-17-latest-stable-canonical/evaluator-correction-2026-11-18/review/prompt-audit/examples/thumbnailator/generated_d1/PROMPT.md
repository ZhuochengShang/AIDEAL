# Recorded system prompt

You write Java code that will be spliced into a runnable test harness.
A Java headless harness compiled for Java 8 compatibility and run on JDK 17 is already in scope. Write statements only for the marked region. Reuse the in-memory images, output stream/path, and checked-in image paths. Exercise the target public API, assert a stable dimension/pixel/byte/file property, and print a compact witness.

Requested target declaration (frozen canonical selection):
Qualified name: net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage
Owner: net.coobird.thumbnailator.Thumbnails.Builder
Declaration: ():BufferedImage
Parameters in declaration order (0): (none)
Write the requested call against this owner and declaration, with its indicated parameter list.
Verified public access paths for the same defining API: net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage. Use a public access path when the defining namespace is internal.

Pick the input variable(s) whose type matches the API's parameters. Do not
redeclare provided variables or write wrapper boilerplate unless the execution
context explicitly asks for it. Output ONLY the body statements that exercise the
API. Use ONLY the documentation provided. Output only code, no markdown fences.

Role: An expert in deterministic Java image processing, image I/O, and safe headless test harnesses.
Project: Thumbnailator (Java) - A small Java image-processing library for producing thumbnails from files, streams, URLs, and in-memory images.
Domain: Deterministic Java image processing; selected for this latest-stable study.
Target users: Java imaging and media developers; scientific software users needing deterministic image transformations; coding agents composing type-safe thumbnail pipelines
Use cases: Resize, crop, rotate, watermark, and transform BufferedImages.; Read and write thumbnails through files and streams.; Exercise filters, geometry, resizers, naming, and task abstractions.
Constraints: Use only in-memory images and 95 checked-in test files.; Run headless and prohibit network, cameras, and desktop UI.; Compile snippets with JDK 17 javac --release 8; execute headlessly on JDK 17 with the official Maven 0.4.21 binary.; Use every name in the frozen 94-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.

# Recorded user prompt

Documentation:
## API Test: `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage`

### Signature
```java
():BufferedImage
```
_Source: source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:2342_

### Goal
Generates a thumbnail from a single source image and returns the result as an in-memory `BufferedImage` object.

### Parameters
_None._

### Input
The caller must provide a single source image (e.g., `File`, `InputStream`, `URL`, or `BufferedImage`) via the `Thumbnails.of()` or `Thumbnails.from...()` entry points. The builder must be configured with a valid transformation (e.g., `.size()`, `.scale()`) before calling this method.

### Output
Returns `BufferedImage` — The processed thumbnail image. The image type typically matches the input image type unless explicitly overridden via `imageType(int)`.

### Valid Call Patterns
```java
BufferedImage thumbnail = Thumbnails.of("image.jpg")
    .size(200, 200)
    .asBufferedImage();
```

### LLM Instruction Prompt
- Use `asBufferedImage()` only when the builder is configured with a single source image.
- Ensure the builder has a defined transformation (size or scale) before invocation.
- Do not use this method if the intent is to write the result directly to a file; use `toFile()` instead to avoid potential color issues with the default JPEG writer when handling alpha channels.

### Prompt Snippet
```text
// Example of generating a thumbnail in-memory
BufferedImage result = Thumbnails.of(sourceFile)
    .size(100, 100)
    .asBufferedImage();
```

### Common Failure Modes
- **`IllegalArgumentException`**: Thrown if the builder was initialized with multiple source images (e.g., a directory of files).
- **`IOException`**: Thrown if an error occurs during the reading of the original image.
- **`IllegalStateException`**: Thrown if both `size()` and `scale()` are called on the same builder instance.
- **Color/Alpha Issues**: Using the returned `BufferedImage` with the default Java JPEG writer may result in incorrect colors or exceptions if the image contains an alpha channel.

### Fix Code Hint
```java
// If writing to a file, prefer toFile() to handle color/alpha workarounds
Thumbnails.of("input.png")
    .size(100, 100)
    .toFile("output.png");
```

Available input path variables already in scope (choose the matching one(s) by type):
Pre-loaded and already in scope — use these directly, do NOT re-load:
- sourceImage: BufferedImage
- graphics: Graphics2D
- destinationImage: BufferedImage
- imageBytes: ByteArrayOutputStream
- outputPath: Path
(raw input path strings also in scope if needed: grid_png, grid_jpeg, exif_jpeg, output_dir)

RECEIVER — call `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` on the RIGHT type (calling it on the wrong receiver is
the #1 failure; if it is an instance method, first obtain a value of the owner type,
do NOT call it on an unrelated preloaded input):
(receiver type not resolved)

(none yet)

Write minimal body statements that use `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` correctly per the docs,
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
  `__CHECK__ java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage ` followed by the witness, using the language's normal
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
materialize `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage`, but deliberately fail the assertion with a short message
stating that the documented contract is insufficient to verify the result. This is
a documentation-comprehension test: an unverifiable contract must not earn a pass.
If `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` is itself a writer/output API, use an output binding only when one
is listed among the available inputs or execution context; then read back a small
part of the output, assert a known content/aggregate relation when the documented
contract permits it, and print the same structured line.
Do not call other heavyweight operations unless `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` is the writer; keep the
body focused on `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` so the run isolates that one call.
Use Java 8 syntax. Prefer BufferedImage and the provided tiny PNG/JPEG fixtures. Do not open windows, URLs, cameras, or network resources. Close streams you create and avoid overwriting repository fixtures.
