# Fix-loop report — result

_Generated 2026-11-18 09:34 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-172105Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **83/225** raw (36.9%)  ·  scored **83/225** (36.9%) after excluding 0 infra
- wall 0.23 h  ·  tokens in 455,856 / out 47,313 ·  llm calls 225  ·  max_fix_rounds 0
- pass-by-round: r0:83  ·  **0 rescued by the fix loop** (pass@0 = 83)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **9x** [runtime] IllegalStateException: Maker not ready to make thumbnail.
  - `java:net.coobird.thumbnailator.makers.FixedSizeThumbnailMaker.keepAspectRatio`, `java:net.coobird.thumbnailator.makers.FixedSizeThumbnailMaker.make`, `java:net.coobird.thumbnailator.makers.FixedSizeThumbnailMaker.size`, `java:net.coobird.thumbnailator.makers.ThumbnailMaker`, `java:net.coobird.thumbnailator.makers.ThumbnailMaker.defaultImageType`, `java:net.coobird.thumbnailator.makers.ThumbnailMaker.defaultResizer`, `java:net.coobird.thumbnailator.makers.ThumbnailMaker.defaultResizerFactory`, `java:net.coobird.thumbnailator.makers.ThumbnailMaker.imageType`, `java:net.coobird.thumbnailator.makers.ThumbnailMaker.resizer`
- **8x** [compile] <path>:<n>
  - `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.fitWithinDimensions`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.keepAspectRatio`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.resizerFactory`, `java:net.coobird.thumbnailator.resizers.configurations.AlphaInterpolation.getKey`, `java:net.coobird.thumbnailator.tasks.io.AbstractImageSink.preferredOutputFormatName`, `java:net.coobird.thumbnailator.tasks.io.AbstractImageSource.setThumbnailParameter`, `java:net.coobird.thumbnailator.tasks.io.InputStreamImageSource.setThumbnailParameter`, `java:net.coobird.thumbnailator.util.exif.ExifFilterUtils.getFilterForOrientation`
- **7x** [compile] <path>:<n>: error:
  - `java:net.coobird.thumbnailator.ThumbnailParameter.getHeightScalingFactor`, `java:net.coobird.thumbnailator.ThumbnailParameter.getWidthScalingFactor`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.build`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.region`, `java:net.coobird.thumbnailator.resizers.DefaultResizerFactory.getResizer`, `java:net.coobird.thumbnailator.resizers.configurations.Rendering.getKey`, `java:net.coobird.thumbnailator.tasks.StreamThumbnailTask.getDestination`
- **6x** [compile] <path>:<n>: error: cannot
  - `java:net.coobird.thumbnailator.ThumbnailParameter.getImageFilters`, `java:net.coobird.thumbnailator.ThumbnailParameter.getOutputFormat`, `java:net.coobird.thumbnailator.ThumbnailParameter.getSourceRegion`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder`, `java:net.coobird.thumbnailator.tasks.SourceSinkThumbnailTask.read`, `java:net.coobird.thumbnailator.tasks.io.URLImageSource.getSource`
- **5x** [runtime] FileNotFoundException: /home/zshan011/apps/aideal/studies/<num>-11-17-latest-stable-canonical/ablation-<num>-11-18/generated-readme-r0/thumb
  - `java:net.coobird.thumbnailator.Thumbnails.Builder.allowOverwrite`, `java:net.coobird.thumbnailator.Thumbnails.Builder.determineOutputFormat`, `java:net.coobird.thumbnailator.Thumbnails.Builder.outputQuality`, `java:net.coobird.thumbnailator.Thumbnails.Builder.useOriginalFormat`, `java:net.coobird.thumbnailator.tasks.io.FileImageSink.write`
- **4x** [compile] <path>:<n>: error: cannot find
  - `java:net.coobird.thumbnailator.Thumbnails.Builder.addFilters`, `java:net.coobird.thumbnailator.tasks.SourceSinkThumbnailTask`, `java:net.coobird.thumbnailator.tasks.ThumbnailTask.getParam`, `java:net.coobird.thumbnailator.util.exif.IfdStructure.getTag`
- **4x** [compile] <path>:<n>: error: cannot fin
  - `java:net.coobird.thumbnailator.Thumbnails.Builder.scalingMode`, `java:net.coobird.thumbnailator.tasks.StreamThumbnailTask.read`, `java:net.coobird.thumbnailator.tasks.io.OutputStreamImageSink`, `java:net.coobird.thumbnailator.util.exif.IfdStructure.isValue`
- **4x** [runtime] IllegalStateException: The size nor the scaling factor has been set.
  - `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.format`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.imageType`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.quality`, `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.resizer`
- **4x** [compile] <path>:<n>: error: cannot find symbo
  - `java:net.coobird.thumbnailator.geometry.Region.getSize`, `java:net.coobird.thumbnailator.resizers.BicubicResizer`, `java:net.coobird.thumbnailator.tasks.FileThumbnailTask`, `java:net.coobird.thumbnailator.tasks.io.URLImageSource`
- **4x** [compile] <path>:<n>: error: canno
  - `java:net.coobird.thumbnailator.name.ConsecutivelyNumberedFilenames`, `java:net.coobird.thumbnailator.resizers.ProgressiveBilinearResizer`, `java:net.coobird.thumbnailator.tasks.SourceSinkThumbnailTask.write`, `java:net.coobird.thumbnailator.tasks.StreamThumbnailTask.getSource`
- **3x** [compile] <path>:<n>: error: can
  - `java:net.coobird.thumbnailator.ThumbnailParameter.fitWithinDimenions`, `java:net.coobird.thumbnailator.ThumbnailParameter.useExifOrientation`, `java:net.coobird.thumbnailator.util.exif.IfdStructure.getOffsetValue`
- **3x** [compile] <path>:<n>: error: no su
  - `java:net.coobird.thumbnailator.ThumbnailParameter.getOutputQuality`, `java:net.coobird.thumbnailator.builders.BufferedImageBuilder.build`, `java:net.coobird.thumbnailator.builders.BufferedImageBuilder.width`

## Why each API fails (142 failing)

### `java:net.coobird.thumbnailator.ThumbnailParameter.fitWithinDimenions` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:980`
- last error: ApiTest.java:58: error: can
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getHeightScalingFactor` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:840`
- last error: ApiTest.java:53: error:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getImageFilters` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:919`
- last error: ApiTest.java:58: error: cannot
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getOutputFormat` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:878`
- last error: ApiTest.java:52: error: cannot
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getOutputFormatType` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:891`
- last error: ApiTest.java:51: error: no
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getOutputQuality` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:907`
- last error: ApiTest.java:51: error: no su
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getResizer` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:930`
- last error: ApiTest.java:51: error: no suitable
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getResizerFactory` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:942`
- last error: ApiTest.java:51: error: no s
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getSize` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:808`
- last error: ApiTest.java:57: error: cannot find sy
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getSourceRegion` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:967`
- last error: ApiTest.java:57: error: cannot
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getType` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:850`
- last error: ApiTest.java:51: error: no suitable co
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.getWidthScalingFactor` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:826`
- last error: ApiTest.java:51: error: 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.isKeepAspectRatio` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:861`
- last error: ApiTest.java:51: error: cann
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.useExifOrientation` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:993`
- last error: ApiTest.java:62: error: can
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.ThumbnailParameter.useOriginalImageType` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/ThumbnailParameter.java:953`
- last error: ApiTest.java:51: error: n
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnailator.createThumbnail` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnailator.java:356`
- last error: RuntimeException: I/O error during thumbnail processing
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] RuntimeException: I/O error during thumbnail processing

### `java:net.coobird.thumbnailator.Thumbnailator.createThumbnails` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnailator.java:453`
- last error: ApiTest.java:51: error: illegal st
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.addFilters` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:2016`
- last error: ApiTest.java:51: error: cannot find
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.allowOverwrite` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1265`
- last error: FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/output/thumbnail.png/test_overwrite.jpg (No such file or directory)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/exe

### `java:net.coobird.thumbnailator.Thumbnails.Builder.antialiasing` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1425`
- last error: ApiTest.java:51: error: illegal s
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:2342`
- last error: AssertionError: Dimension mismatch: expected 50x50, got 50x38
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Dimension mismatch: expected 50x50, got 50x38

### `java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImages` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:2277`
- last error: AssertionError: Dimension mismatch: 50x38
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Dimension mismatch: 50x38

### `java:net.coobird.thumbnailator.Thumbnails.Builder.asFiles` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:2519`
- last error: ApiTest.java:57: error: cannot find sy
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.determineOutputFormat` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1720`
- last error: FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/output/thumbnail.png/test_output.png (No such file or directory)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/exe

### `java:net.coobird.thumbnailator.Thumbnails.Builder.outputFormat` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1658`
- last error: ApiTest.java:51: error: cannot fi
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.outputQuality` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1550`
- last error: FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/output/thumbnail.png/quality_test.jpg (No such file or directory)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/exe

### `java:net.coobird.thumbnailator.Thumbnails.Builder.rendering` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1448`
- last error: ApiTest.java:51: error: illegal star
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.rotate` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1969`
- last error: IllegalStateException: scale is not set.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: scale is not set.

### `java:net.coobird.thumbnailator.Thumbnails.Builder.scalingMode` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1300`
- last error: ApiTest.java:53: error: cannot fin
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.size` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:843`
- last error: IllegalStateException: Output format not specified.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Output format not specified.

### `java:net.coobird.thumbnailator.Thumbnails.Builder.toFile` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:2652`
- last error: ApiTest.java:51: error: cannot find sym
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.Builder.useOriginalFormat` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1680`
- last error: FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/output/thumbnail.png/test_original_format.png (No such file or directory)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundException: /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/exe

### `java:net.coobird.thumbnailator.Thumbnails.Builder.watermark` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:1944`
- last error: ArrayIndexOutOfBoundsException: Coordinate out of bounds!
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ArrayIndexOutOfBoundsException: Coordinate out of bounds!

### `java:net.coobird.thumbnailator.Thumbnails.fromInputStreams` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:347`
- last error: ApiTest.java:51: error: cannot find s
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.Thumbnails.of` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/Thumbnails.java:208`
- last error: ApiTest.java:51: error: cannot find symbol
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.BufferedImageBuilder.build` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/BufferedImageBuilder.java:110`
- last error: ApiTest.java:51: error: no su
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.BufferedImageBuilder.height` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/BufferedImageBuilder.java:167`
- last error: ApiTest.java:53: error: no s
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.BufferedImageBuilder.size` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/BufferedImageBuilder.java:138`
- last error: ApiTest.java:53: error: no sui
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.BufferedImageBuilder.width` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/BufferedImageBuilder.java:150`
- last error: ApiTest.java:53: error: no su
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:105`
- last error: ApiTest.java:56: error: cannot
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.build` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:362`
- last error: ApiTest.java:57: error: 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.filters` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:267`
- last error: ApiTest.java:53: error
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.fitWithinDimensions` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:330`
- last error: ApiTest.java:56
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.format` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:243`
- last error: IllegalStateException: The size nor the scaling factor has been set.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: The size nor the scaling factor has been set.

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.formatType` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:254`
- last error: ApiTest.java:55: er
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.imageType` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:113`
- last error: IllegalStateException: The size nor the scaling factor has been set.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: The size nor the scaling factor has been set.

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.keepAspectRatio` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:214`
- last error: ApiTest.java:56
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.quality` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:232`
- last error: IllegalStateException: The size nor the scaling factor has been set.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: The size nor the scaling factor has been set.

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.region` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:200`
- last error: ApiTest.java:53: error:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.resizer` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:288`
- last error: IllegalStateException: The size nor the scaling factor has been set.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: The size nor the scaling factor has been set.

### `java:net.coobird.thumbnailator.builders.ThumbnailParameterBuilder.resizerFactory` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/builders/ThumbnailParameterBuilder.java:311`
- last error: ApiTest.java:52
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.Caption` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Caption.java:92`
- last error: ApiTest.java:51: error: illegal start of expressi
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.Pipeline` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Pipeline.java:73`
- last error: ApiTest.java:51: error: constructor Flip in clas
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.Pipeline.add` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Pipeline.java:99`
- last error: ApiTest.java:52: error: constructor Flip in 
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.Pipeline.addAll` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Pipeline.java:125`
- last error: ApiTest.java:53: error: constructor Rotat
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.Pipeline.addFirst` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Pipeline.java:112`
- last error: ApiTest.java:52: error: constructor Rot
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.Pipeline.apply` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Pipeline.java:144`
- last error: ApiTest.java:52: error: constructor Flip i
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.Pipeline.getFilters` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Pipeline.java:140`
- last error: ApiTest.java:52: error: cannot find s
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.SwapDimensions.apply` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/SwapDimensions.java:44`
- last error: ApiTest.java:51: error: SwapDimensio
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.filters.SwapDimensions.getInstance` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/SwapDimensions.java:40`
- last error: AssertionError: SwapDimensions failed: expected 24x32 but got 32x24
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: SwapDimensions failed: expected 24x32 but got 32x24

### `java:net.coobird.thumbnailator.filters.Transparency` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Transparency.java:58`
- last error: AssertionError: Transparency filter did not modify alpha channel as expected. Alpha: 255
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Transparency filter did not modify alpha channel as expected. Alpha: 255

### `java:net.coobird.thumbnailator.filters.Transparency.apply` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/filters/Transparency.java:85`
- last error: AssertionError: Transparency filter did not correctly apply alpha: 255
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Transparency filter did not correctly apply alpha: 255

### `java:net.coobird.thumbnailator.geometry.AbsoluteSize` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/geometry/AbsoluteSize.java:64`
- last error: ApiTest.java:55: error: method calculate in
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.geometry.Coordinate.calculate` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/geometry/Coordinate.java:61`
- last error: ApiTest.java:51: error: constructor
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.geometry.Region` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/geometry/Region.java:59`
- last error: ApiTest.java:55: error: method calculate in class
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.geometry.Region.calculate` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/geometry/Region.java:109`
- last error: ApiTest.java:52: error: Size is abstrac
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.geometry.Region.getSize` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/geometry/Region.java:86`
- last error: ApiTest.java:53: error: cannot find symbo
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.geometry.RelativeSize` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/geometry/RelativeSize.java:52`
- last error: ApiTest.java:54: error: method calculate in
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.makers.FixedSizeThumbnailMaker.keepAspectRatio` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/FixedSizeThumbnailMaker.java:215`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.FixedSizeThumbnailMaker.make` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/FixedSizeThumbnailMaker.java:264`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.FixedSizeThumbnailMaker.size` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/FixedSizeThumbnailMaker.java:176`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.ThumbnailMaker` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/ThumbnailMaker.java:163`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.ThumbnailMaker.defaultImageType` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/ThumbnailMaker.java:240`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.ThumbnailMaker.defaultResizer` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/ThumbnailMaker.java:263`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.ThumbnailMaker.defaultResizerFactory` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/ThumbnailMaker.java:290`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.ThumbnailMaker.imageType` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/ThumbnailMaker.java:229`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.ThumbnailMaker.resizer` — runtime

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/ThumbnailMaker.java:251`
- last error: IllegalStateException: Maker not ready to make thumbnail.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IllegalStateException: Maker not ready to make thumbnail.

### `java:net.coobird.thumbnailator.makers.ThumbnailMaker.resizerFactory` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/makers/ThumbnailMaker.java:277`
- last error: ApiTest.java:52: error: cann
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.name.ConsecutivelyNumberedFilenames` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/name/ConsecutivelyNumberedFilenames.java:295`
- last error: ApiTest.java:51: error: canno
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

### `java:net.coobird.thumbnailator.name.ConsecutivelyNumberedFilenames.iterator` — compile

- canonical source: `source/src/main/java/net/coobird/thumbnailator/name/ConsecutivelyNumberedFilenames.java:343`
- last error: ApiTest.java:51: err
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [compile] /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator/execution/run_java_net.coo

_… 62 more failing APIs omitted (--max-api-detail to raise)._
