# Recorded author system prompt

You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

Role: An expert in deterministic Java image processing, image I/O, and safe headless test harnesses.
Project: Thumbnailator (Java) - A small Java image-processing library for producing thumbnails from files, streams, URLs, and in-memory images.
Domain: Deterministic Java image processing; selected for this latest-stable study.
Target users: Java imaging and media developers; scientific software users needing deterministic image transformations; coding agents composing type-safe thumbnail pipelines
Use cases: Resize, crop, rotate, watermark, and transform BufferedImages.; Read and write thumbnails through files and streams.; Exercise filters, geometry, resizers, naming, and task abstractions.
Constraints: Use only in-memory images and 95 checked-in test files.; Run headless and prohibit network, cameras, and desktop UI.; Compile snippets with JDK 17 javac --release 8; execute headlessly on JDK 17 with the official Maven 0.4.21 binary.; Use every name in the frozen 94-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.

# Recorded author user prompt

Document the Java function `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` of Thumbnailator.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{
  "name": "java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage",
  "signature": "():BufferedImage",
  "params": [],
  "returns": "BufferedImage",
  "source_doc": null,
  "overloads": [],
  "api_id": "java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage",
  "display_name": "asBufferedImage",
  "identity_version": "language_qualified_api_v1",
  "parameter_count": 0,
  "parameter_count_status": "compiler_declared",
  "exposure_ids": [
    "java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage"
  ],
  "preferred_public_path": "net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage",
  "qualified_name": "net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage",
  "owner": "net.coobird.thumbnailator.Thumbnails.Builder",
  "source": {
    "file": "source/src/main/java/net/coobird/thumbnailator/Thumbnails.java",
    "line": 2342,
    "site_id": "Java:thumbnailator:src/main/java/net/coobird/thumbnailator/Thumbnails.java:80822:method:asBufferedImage"
  },
  "definition_sites": [
    {
      "signature": "():BufferedImage",
      "qualified_name": "net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage",
      "owner": "net.coobird.thumbnailator.Thumbnails.Builder",
      "source": {
        "file": "source/src/main/java/net/coobird/thumbnailator/Thumbnails.java",
        "line": 2342,
        "site_id": "Java:thumbnailator:src/main/java/net/coobird/thumbnailator/Thumbnails.java:80822:method:asBufferedImage"
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
===== Original documentation part 1/2 =====
### 1. Project purpose
Thumbnailator is a Java library designed to simplify high-quality thumbnail generation. It abstracts the complexities of the Java Image I/O and Java 2D APIs, providing a fluent interface for common image processing tasks such as resizing, cropping, rotating, and watermarking. It is a single-JAR library with no external dependencies, suitable for headless environments.

### 2. Main workflows
*   **Fluent Pipeline:** The primary entry point is the `Thumbnails` class, which provides a builder-style fluent interface to define source, transformation, and destination parameters in a single chain.
*   **Task-Based Processing:** For more granular control, developers can use `ThumbnailTask` implementations (e.g., `FileThumbnailTask`, `StreamThumbnailTask`, `SourceSinkThumbnailTask`) to manage specific I/O operations.
*   **Filtering:** Image transformations are handled by classes implementing the `ImageFilter` interface, which can be chained using the `Pipeline` class.
*   **Exif Handling:** The library includes utilities (`ExifUtils`, `ExifFilterUtils`) to detect and apply orientation corrections based on Exif metadata.

### 3. Important APIs and usage patterns
*   **Entry Point:** `net.coobird.thumbnailator.Thumbnails` is the primary class for initiating thumbnail generation.
*   **Builders:** `Thumbnails.Builder<T>` manages the configuration of the generation task.
*   **Makers:** `FixedSizeThumbnailMaker` and `ScaledThumbnailMaker` handle the core resizing logic.
*   **Geometry:** `Position` (and the `Positions` enum) and `Size` (and its implementations `AbsoluteSize`, `RelativeSize`) define where and how elements like watermarks or captions are placed.
*   **Naming:** The `Rename` class provides standard strategies for generating output filenames (e.g., `PREFIX_DOT_THUMBNAIL`).
*   **Filters:** `ImageFilter` implementations include `Watermark`, `Caption`, `Canvas`, `Rotation`, `Flip`, `Colorize`, and `Transparency`.

### 4. Inputs and file formats
Thumbnailator supports various input sources:
*   **Files:** `File` objects via `FileImageSource`.
*   **Streams:** `InputStream` via `InputStreamImageSource`.
*   **URLs:** `URL` via `URLImageSource`.
*   **In-memory:** `BufferedImage` via `BufferedImageSource`.
*   **Format Support:** Relies on standard Java Image I/O; supported formats can be queried via `ThumbnailatorUtils.getSupportedOutputFormats()`.

### 5. Outputs and generated artifacts
*   **Files:** `FileImageSink` writes to the filesystem.
*   **Streams:** `OutputStreamImageSink` writes to an `OutputStream`.
*   **In-memory:** `BufferedImageSink` returns a `BufferedImage`.
*   **Naming:** `ConsecutivelyNumberedFilenames` can be used to generate sequential filenames for batch operations.

### 6. Configuration and environment assumptions
*   **Headless:** Designed to run in headless environments; avoids UI components.
*   **System Properties:** Configuration properties (e.g., `thumbnailator.disableExifWorkaround`, `thumbnailator.debugLog`) can be set via JVM `-D` flags or a `thumbnailator.properties` file on the classpath.
*   **Memory:** A `CONSERVE_MEMORY_WORKAROUND` is available for large images, though it is not enabled by default.

### 7. Commands and examples

**Fluent API Usage:**
```java
Thumbnails.of(new File("path/to/directory").listFiles())
    .size(640, 480)
    .outputFormat("jpg")
    .toFiles(Rename.PREFIX_DOT_THUMBNAIL);
```

**Fixed Size Maker:**
```java
BufferedImage img = ImageIO.read(new File("sourceImage.jpg"));
BufferedImage thumbnail = new FixedSizeThumbnailMaker()
    .size(200, 200)
    .keepAspectRatio(true)
    .make(img);
```

**Scaled Maker:**
```java
BufferedImage img = ImageIO.read(new File("sourceImage.jpg"));
BufferedImage thumbnail = new ScaledThumbnailMaker()
    .scale(0.25)
    .make(img);
```

### 8. Constraints, preconditions, compatibility rules, and type-selection rules
*   **Preconditions:** For `FixedSizeThumbnailMaker`, the size must be set before calling `make()`.
*   **Constraints:** `ThumbnailTask` implementations only process the first image in a multi-image file; subsequent images are ignored.
*   **Type Selection:** `IfdType` and `Orientation` enums are used for Exif metadata parsing. `IfdType` defines data types (e.g., `BYTE`, `ASCII`, `SHORT`, `LONG`, `RATIONAL`) as per Exif 2.3.
*   **Compatibility:** The `PREFIX_HYPTHEN_THUMBNAIL` and `SUFFIX_HYPTHEN_THUMBNAIL` constants in `Rename` are deprecated and will be removed in 0.5.0.

### 9. Facts to preserve in the final README
*   Thumbnailator is a single-JAR library with no external dependencies.
*   The library is released under the MIT License.
*   The fluent interface is the recommended way to perform complex tasks in a single step.
*   The library provides specific workarounds for memory management and Exif metadata handling in JRE-bundled JPEG readers.

### 10. Missing or weak documentation
*   The documentation does not explicitly detail the full list of supported image formats beyond stating it relies on the Java Image I/O API.
*   The `ThumbnailParameter` class is mentioned as a core component but lacks a detailed breakdown of all available parameters in the provided snippets.
*   The `Caption` class constructor details were truncated in the provided documentation.

===== Original documentation part 2/2 =====
### 1. Project purpose
Thumbnailator is a Java library designed for high-quality, deterministic image processing. It provides a fluent, readable API for generating thumbnails from various sources (files, streams, URLs, and `BufferedImage` objects). It supports resizing, cropping, rotation, watermarking, and applying custom image filters, while abstracting away the complexities of Java's `ImageIO` and `Graphics2D` APIs.

### 2. Main workflows
*   **Fluent Pipeline:** The primary workflow involves starting with a `Thumbnails.of(...)` or `Thumbnails.from...(...)` entry point, chaining configuration methods (e.g., `.size()`, `.rotate()`, `.watermark()`), and terminating with an output method (e.g., `.toFile()`, `.asBufferedImage()`).
*   **Batch Processing:** The library supports processing collections of inputs (files, streams, etc.) and outputting them to directories or lists using `Rename` strategies.
*   **Custom Resizing:** Users can select specific resizing algorithms (e.g., `Bilinear`, `Bicubic`, `ProgressiveBilinear`) via the `Resizers` enum or `ResizerFactory` implementations.
*   **Filter Application:** Users can apply `ImageFilter` implementations (like `Caption`) to images after the resizing step.

### 3. Important APIs and usage patterns
*   **`Thumbnails.Builder<T>`:** The core fluent interface. It is recommended to chain methods directly from the `Thumbnails.of` call to the terminal output method without storing the builder in a variable.
*   **`ThumbnailParameter`:** Holds the configuration for a thumbnail task. It is mutable and should not be reused across multiple tasks.
*   **`Resizer` / `ResizerFactory`:** Interfaces for defining how images are scaled. `DefaultResizerFactory` is the standard implementation, selecting the optimal algorithm based on source/destination dimensions.
*   **`Rename`:** A functional interface used during batch file operations to determine output filenames (e.g., `Rename.PREFIX_DOT_THUMBNAIL`).
*   **`BufferedImageBuilder`:** A utility for creating `BufferedImage` instances with specific dimensions and types.

### 4. Inputs and file formats
*   **Sources:** `File`, `String` (filenames), `URL`, `InputStream`, and `BufferedImage`.
*   **Formats:** Supports any format recognized by the Java Image I/O API. Use `ImageIO.getWriterFormatNames()` to check supported output formats.
*   **Metadata:** Supports using Exif metadata for orientation via `useExifOrientation(boolean)`.

### 5. Outputs and generated artifacts
*   **Destinations:** `File`, `OutputStream`, `BufferedImage`, or `List<BufferedImage>`.
*   **Quality:** Controlled via `outputQuality(double)` (0.0 to 1.0).
*   **Format:** Controlled via `outputFormat(String)`. `determineOutputFormat()` can infer the format from file extensions.

### 6. Configuration and environment assumptions
*   **Headless:** Designed for headless environments; avoids UI components.
*   **Memory:** For large batches, `iterableBufferedImages()` is preferred over `asBufferedImages()` to avoid `OutOfMemoryError`.
*   **Thread Safety:** `ThumbnailParameter` is not thread-safe.
*   **Compatibility:** Designed for JDK 8+.

### 7. Commands and examples

**Basic Resize and Save:**
```java
Thumbnails.of("path/to/image")
    .size(200, 200)
    .toFile("path/to/thumbnail");
```

**Batch Processing with Rename:**
```java
Thumbnails.of(directory.listFiles())
    .size(200, 200)
    .outputFormat("jpeg")
    .asFiles(Rename.PREFIX_DOT_THUMBNAIL);
```

**Using a Specific Resizer:**
```java
BufferedImage sourceImage = new BufferedImageBuilder(400, 400).build();
BufferedImage destImage = new BufferedImageBuilder(200, 200).build();
Resizers.BILINEAR.resize(sourceImage, destImage);
```

**Applying a Caption Filter:**
```java
// Note: Caption implements ImageFilter
Thumbnails.of("image.jpg")
    .size(200, 200)
    .addFilter(new Caption("My Caption", Font.decode("Arial"), Color.WHITE, Positions.BOTTOM_RIGHT, 10))
    .toFile("output.jpg");
```

### 8. Constraints, preconditions, compatibility rules, and type-selection rules
*   **IllegalStateExceptions:** Calling `scale()` after `size()` (or vice versa) throws an `IllegalStateException`.
*   **Overwriting:** `allowOverwrite(boolean)` controls whether existing files are replaced.
*   **Image Types:** When writing to files, avoid `asBufferedImages()` if the image has an alpha channel, as the default JPEG writer may cause color issues; use `toFiles()` instead.
*   **Resizer Selection:** `DefaultResizerFactory` automatically chooses `ProgressiveBilinearResizer` for most downscaling, `BicubicResizer` for upscaling, and `NullResizer` for identical dimensions.

### 9. Facts to preserve in the final README
*   Thumbnailator is a fluent, chainable API.
*   It is designed for headless operation.
*   It provides deterministic resizing via `Resizer` implementations.
*   It handles Exif orientation automatically if enabled.
*   It provides memory-efficient batch processing via `Iterable` interfaces.

### 10. Missing or weak documentation
*   The `ThumbnailTask` class is mentioned in `Thumbnailator.createThumbnail(ThumbnailTask)`, but its specific implementation details and usage are not fully elaborated in the provided docs.
*   The exact behavior of `ImageIO` writer support for specific formats (like WebP or HEIF) is dependent on the underlying JRE/JDK environment, which is not explicitly detailed.

Real usage from the project's existing test suite (these compile and pass — base
the Valid Call Patterns and realistic Common Failure Modes on them; may be empty):
```Java
(no existing test found for this API)
```

Verbatim code example(s) from the ORIGINAL project README that call `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage`
(the project's real, documented usage — may be empty):
```Java
===== Shared original document: README.md =====
_*October 1, 2025: Thumbnailator 0.4.21 has been released!
See [Changes](https://github.com/coobird/thumbnailator/wiki/Changes) for details.*_

_*Thumbnailator is now available through
[Maven](https://github.com/coobird/thumbnailator/wiki/Maven)!*_

# What is Thumbnailator?

![](https://raw.githubusercontent.com/wiki/coobird/thumbnailator/img/home/home-image.png)

_Thumbnailator_ is a thumbnail generation library for Java.

# Why Thumbnailator?
Making high-quality thumbnails in Java can be a fairly difficult task.

Learning how to use the Image I/O API, Java 2D API, image processing,
image scaling techniques, ... but fear not! _Thumbnailator_ will take care
of all those things for you!

Thumbnailator is a single JAR file with no dependencies to external libraries,
making development and deployment simple and easy. It is also available on
the Maven Central Repository for easy inclusion in Maven projects.

# How simple is Thumbnailator?

_Thumbnailator_'s fluent interface can be used to perform fairly complicated
thumbnail processing task in one simple step.

For example, creating JPEG thumbnails of image files in a directory, all
resized to a maximum dimension of 640 pixels by 480 pixels while preserving
the aspect ratio of the original image can be performed by the following:

```
Thumbnails.of(new File("path/to/directory").listFiles())
    .size(640, 480)
    .outputFormat("jpg")
    .toFiles(Rename.PREFIX_DOT_THUMBNAIL);
```

The fluent interface provided by the _Thumbnailator_ simplifies the task of
making thumbnails into a single method call!

No need to access the Image I/O API and manually manipulate `BufferedImage`s
through `Graphics2D` objects. _Thumbnailator_ does all of that for you.

# What can Thumbnailator do?

The following pages have more information on what _Thumbnailator_ can do:

* [Features](https://github.com/coobird/thumbnailator/wiki/Features)
* [Examples](https://github.com/coobird/thumbnailator/wiki/Examples)
* [Thumbnailator API Documentation](https://coobird.github.io/thumbnailator/javadoc/0.4.21/)
* [Frequently Asked Questions](https://github.com/coobird/thumbnailator/wiki/FAQ)

# Disclaimer
*Thumbnailator is still early in its development, and the APIs are subject to
change at any time.*

# License
Thumbnailtor is released under the MIT License.


===== https://javadoc.io/static/net.coobird/thumbnailator/0.4.21/net/coobird/thumbnailator/Thumbnails.Builder.html#asBufferedImage() =====
asBufferedImage
public
BufferedImage
asBufferedImage
()
throws
IOException
Creates a thumbnail and returns it as a
BufferedImage
.
To call this method, the thumbnail must have been created from a
single source.
If you intend to write the
BufferedImage
to a file,
you're strongly encouraged to use one of the
toFile(...)
methods instead. See "Notes on image types" for details.
Notes on image types
The image type of the
BufferedImage
depends on the type
of the input image. (Specifically, the type emitted by the
ImageReader
associated for the file type.)
Thumbnailator will attempt to use the same image type as the
input if it is not specified through
imageType(int)
.
This has implications when writing
BufferedImage
to files
using the default JPEG writer bundled with Java. There are issues
with the JPEG writer
outputting wrong colors
or
throwing exceptions
when writing a image containing an alpha channel.
If outputting to a file, consider using one of the
toFile(File)
or
toFile(String)
methods instead,
as it contains workarounds to prevent issues mentioned in the
previous paragraph.
For more information on
BufferedImage
types, refer to
BufferedImage.getType()
.
Returns:
A thumbnail as a
BufferedImage
.
Throws:
IOException
- If a problem occurred during
the reading of the original
image.
IllegalArgumentException
- If multiple original images are
specified.

```

GROUND THE CALL FORM by combining the sources above, in this priority order — and
NEVER invent a call shape that appears in none of them:
1. If a test-suite example is shown, its call form is authoritative (it compiles
   and passes) — reproduce that exact receiver and argument order.
2. Otherwise use the original-README example's call form.
3. If BOTH are shown, reproduce a real form verbatim (either compiles); when they
   differ, the instance/implicit form `value.java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage(...)` is the most portable.
4. If NEITHER is shown, derive the call from the Signature/API facts and say in the
   entry that the example is inferred from the signature (not verified).
Preserve the receiver/qualifier EXACTLY as written — if it is
`value.java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage(...)` or `Object.java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage(...)`, keep it; do NOT collapse it to
a bare `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage(...)`, which usually will not compile.

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

## API Test: `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage`

### Signature
```java
():BufferedImage
```
_Source: source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:2342_

### Goal
TODO: one sentence describing what `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` does, in the project's domain terms.

### Parameters
_None._

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `BufferedImage` — TODO: what the value represents and its format.

### Valid Call Patterns
```java
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage`.

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

