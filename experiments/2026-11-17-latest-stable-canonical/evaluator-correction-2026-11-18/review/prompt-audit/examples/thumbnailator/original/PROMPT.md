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
