# Six real API microbenchmark examples

These are **six saved, executed R0 examples**, one per library. Each includes the exact model request, response, wrapped executable program, console output, execution command, and recorded verdict. No new model calls or test executions were made to build this guide.

**Scope.** These examples belong to the current `explicit-inputs-r0` protocol and use `gemini-3.1-flash-lite`. The audience writes both the API call and its assertions. A native pass means the generated program passed execution checks and emitted the required exact-target witness; it is **not** independent validation of all API behavior. These six examples were selected for readability and are not a representative performance sample. R1/R2 repairs, D2 revision, aliases, embedded hints, and puzzle evaluation are not part of these runs.

The RDPro walkthrough below uses **Scala only**. The separate Java bank and its earlier failure evidence remain available in the bank index and existing report evidence.

## Open one example from beginning to end

1. Open `request.json` to read the complete `system` and `user` messages, API target, selected documentation, supplied-variable descriptions, model, and output allowance.
2. Open `response.txt` to see the exact returned program fragment. Then open the wrapped program to see its imports, initialized inputs, execution wrapper, and inserted fragment.
3. Open `INPUTS.json` for fixture paths, hashes, preamble, and shared input contract. For mir_eval, reuse the full wrapped program and existing source evidence; the four intervals are shown below.
4. Open `execution.json`, `stdout.txt`, and `stderr.txt` to see the command, elapsed execution time, exit status, output, and any diagnostics. `provider.json` separately records request time and tokens.
5. Open `VERDICT_AND_PROVENANCE.json` (or the existing mir_eval `evidence.json`) for the native verdict, original result location, and file hashes.

| Library | Saved condition | API | Recorded output | Native verdict |
|---|---|---|---|---|
| RDPro (Scala) | Generated README D1 | `RasterMetadata` | `462836` | Pass at R0 |
| SedonaDB | Generated README D1 | `ST_Distance` | `5.0; 111195.10117748393` | Pass at R0 |
| MDAnalysis | Original documentation | `calc_bonds` | `5 bonds; mean 2.7657` | Pass at R0 |
| tslearn | Generated README D1 | `dtw` | `Constrained distance 0.1175` | Pass at R0 |
| mir_eval | Generated README D1 | `intervals_to_durations` | `2.0` | Pass at R0 |
| Thumbnailator | Generated README D1 | `Thumbnails.Builder.asBufferedImage` | `16x12@ffffff00` | Pass at R0 |

## RDPro (Scala)

**Selected API:** `RasterMetadata`. **Documentation condition:** Generated README D1.

**Actual input.** A synthetic raster extent with width 737 and height 628, 256×256 tiles, SRID 4326, and an explicitly constructed affine transform. The test creates metadata; it does not resize pixels or establish that its transform describes the supplied GeoTIFF.

**What the saved program checks.** The generated program checks the constructor fields against the values it supplied, then prints the extent pixel count.

[Full prompt](rdpro/request.json) | [LLM response](rdpro/response.txt) | [Complete executable program](rdpro/ApiTest.scala) | [Actual output](rdpro/stdout.txt) | [Errors/warnings](rdpro/stderr.txt)

[Execution command and time](rdpro/execution.json) | [Model time and tokens](rdpro/provider.json) | [Verdict and provenance](rdpro/VERDICT_AND_PROVENANCE.json)

[Fixture paths, hashes, and initialization](rdpro/INPUTS.json)

**Exact returned fragment**

```scala
import edu.ucr.cs.bdlab.beast.geolite.RasterMetadata
import java.awt.geom.AffineTransform

// Define parameters for a 737x628 raster (matching the provided rasterRDD dimensions)
val x1 = 0
val y1 = 0
val x2 = 737
val y2 = 628
val tileWidth = 256
val tileHeight = 256
val srid = 4326

// Create an AffineTransform: scale 0.01, shear 0, 0, -0.01, minX -180, maxY 90
val g2m = new AffineTransform(0.01, 0.0, 0.0, -0.01, -180.0, 90.0)

// Construct the RasterMetadata
val meta = new RasterMetadata(x1, y1, x2, y2, tileWidth, tileHeight, srid, g2m)

// Verify the metadata properties match the input parameters
val isCorrect = (meta.x1 == x1) && 
                (meta.y1 == y1) && 
                (meta.x2 == x2) && 
                (meta.y2 == y2) && 
                (meta.tileWidth == tileWidth) && 
                (meta.tileHeight == tileHeight) && 
                (meta.srid == srid)

assert(isCorrect, "RasterMetadata properties do not match the provided constructor arguments")

// Witness: The total number of pixels in the defined extent
val totalPixels = (meta.x2 - meta.x1) * (meta.y2 - meta.y1)
println(s"__CHECK__ scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata $totalPixels")
```

**Exact standard output**

```text
__CHECK__ scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadata 462836
__DONE__ object=GeoJob
```

## SedonaDB

**Selected API:** `ST_Distance`. **Documentation condition:** Generated README D1.

**Actual input.** Two planar points (0,0) and (3,4), followed by geographic points (0°,0°) and (0°,1°), created directly in the SQL expressions. No raster/vector file is consumed by these calls.

**What the saved program checks.** The generated program checks planar distance 5 within 1e−9 and geographic distance between 110,000 and 112,000.

[Full prompt](sedonadb/request.json) | [LLM response](sedonadb/response.txt) | [Complete executable program](sedonadb/ApiTest.py) | [Actual output](sedonadb/stdout.txt) | [Errors/warnings](sedonadb/stderr.txt)

[Execution command and time](sedonadb/execution.json) | [Model time and tokens](sedonadb/provider.json) | [Verdict and provenance](sedonadb/VERDICT_AND_PROVENANCE.json)

[Fixture paths, hashes, and initialization](sedonadb/INPUTS.json)

**Exact returned fragment**

```python
table_geom = sd.sql("SELECT ST_Distance(ST_Point(0.0, 0.0), ST_Point(3.0, 4.0)) as dist").to_arrow_table()
dist_geom = table_geom.column("dist")[0].as_py()
assert abs(dist_geom - 5.0) < 1e-9
print(f"__CHECK__ sql:ST_Distance {dist_geom}")

table_geog = sd.sql("SELECT ST_Distance(ST_GeogPoint(0.0, 0.0), ST_GeogPoint(0.0, 1.0)) as dist").to_arrow_table()
dist_geog = table_geog.column("dist")[0].as_py()
# 1 degree of latitude is approximately 111,319 meters
assert dist_geog > 110000 and dist_geog < 112000
print(f"__CHECK__ sql:ST_Distance {dist_geog}")
```

**Exact standard output**

```text
__CHECK__ sql:ST_Distance 5.0
__CHECK__ sql:ST_Distance 111195.10117748393
__DONE__
```

## MDAnalysis

**Selected API:** `calc_bonds`. **Documentation condition:** Original documentation.

**Actual input.** The provided molecular Universe supplies its first five atoms and next five atoms as five coordinate pairs. The exact PSF/topology and DCD/trajectory paths and hashes appear in INPUTS.json.

**What the saved program checks.** The generated program checks an ndarray of shape (5,) and nonnegative distances. It does not check each distance against an independent numerical answer.

[Full prompt](mdanalysis/request.json) | [LLM response](mdanalysis/response.txt) | [Complete executable program](mdanalysis/api_test.py) | [Actual output](mdanalysis/stdout.txt) | [Errors/warnings](mdanalysis/stderr.txt)

[Execution command and time](mdanalysis/execution.json) | [Model time and tokens](mdanalysis/provider.json) | [Verdict and provenance](mdanalysis/VERDICT_AND_PROVENANCE.json)

[Fixture paths, hashes, and initialization](mdanalysis/INPUTS.json)

**Exact returned fragment**

```python
import MDAnalysis.lib.distances as dists
import numpy as np

# Use the preloaded universe and select two small groups of atoms
# to calculate bond lengths between corresponding pairs.
# We select the first 5 atoms and the next 5 atoms to form 5 pairs.
ag1 = universe.atoms[:5]
ag2 = universe.atoms[5:10]

# Calculate bond lengths
bond_lengths = dists.calc_bonds(ag1, ag2)

# Verify the result shape matches the number of pairs
assert bond_lengths.shape == (5,)
assert isinstance(bond_lengths, np.ndarray)

# Verify that the bond lengths are non-negative (physical constraint)
assert np.all(bond_lengths >= 0)

# Print witness: the number of bonds calculated and the mean bond length
print(f"__CHECK__ python:MDAnalysis.lib.distances.calc_bonds {bond_lengths.shape[0]} {np.mean(bond_lengths):.4f}")
```

**Exact standard output**

```text
__CHECK__ python:MDAnalysis.lib.distances.calc_bonds 5 2.7657
__DONE__
```

## tslearn

**Selected API:** `dtw`. **Documentation condition:** Generated README D1.

**Actual input.** The provided s1 and s2 series come from the pinned Trace NPZ fixture. The program also creates the tiny series [0,1] and [0,2].

**What the saved program checks.** It checks zero DTW distance for identical series, a nonnegative constrained distance, and distance 1 for the tiny explicit pair.

[Full prompt](tslearn/request.json) | [LLM response](tslearn/response.txt) | [Complete executable program](tslearn/api_test.py) | [Actual output](tslearn/stdout.txt) | [Errors/warnings](tslearn/stderr.txt)

[Execution command and time](tslearn/execution.json) | [Model time and tokens](tslearn/provider.json) | [Verdict and provenance](tslearn/VERDICT_AND_PROVENANCE.json)

[Fixture paths, hashes, and initialization](tslearn/INPUTS.json)

**Exact returned fragment**

```python
from tslearn.metrics import dtw
import numpy as np

# Use the provided 1D series s1 and s2
# DTW distance between identical series should be 0.0
dist_identical = dtw(s1, s1)
assert dist_identical == 0.0, f"Expected 0.0 for identical series, got {dist_identical}"

# Compute DTW with Sakoe-Chiba constraint
# Using a small radius on a subset of the provided data
s1_sub = s1[:10]
s2_sub = s2[:10]
dist_constrained = dtw(s1_sub, s2_sub, global_constraint="sakoe_chiba", sakoe_chiba_radius=2)

# Verify the result is a non-negative float
assert isinstance(dist_constrained, float), "Result must be a float"
assert dist_constrained >= 0.0, "Distance must be non-negative"

# Verify against a known simple case: distance between [0, 1] and [0, 2]
# Path: (0,0) -> (1,1) => sqrt((0-0)^2 + (1-2)^2) = 1.0
dist_simple = dtw([0, 1], [0, 2])
assert np.isclose(dist_simple, 1.0), f"Expected 1.0, got {dist_simple}"

print(f"__CHECK__ python:tslearn.metrics._dtw.dtw {dist_constrained:.4f}")
```

**Exact standard output**

```text
__CHECK__ python:tslearn.metrics._dtw.dtw 0.1175
__DONE__
```

## mir_eval

**Selected API:** `intervals_to_durations`. **Documentation condition:** Generated README D1.

**Actual input.** The preloaded ref_intervals is [[0,0.5],[0.5,1],[1,1.5],[1.5,2]]. No annotation file is needed for this particular example.

**What the saved program checks.** The generated program checks the output shape (four entries) and verifies the first duration equals its interval end minus start; it prints the duration sum.

[Full prompt](../evidence/examples/intervals-to-durations/generated_d1/request.json) | [LLM response](../evidence/examples/intervals-to-durations/generated_d1/response.txt) | [Complete executable program](../evidence/examples/intervals-to-durations/generated_d1/api_test.py) | [Actual output](../evidence/examples/intervals-to-durations/generated_d1/stdout.txt) | [Errors/warnings](../evidence/examples/intervals-to-durations/generated_d1/stderr.txt)

[Execution command and time](../evidence/examples/intervals-to-durations/generated_d1/execution.json) | [Model time and tokens](../evidence/examples/intervals-to-durations/generated_d1/provider.json) | [Verdict and provenance](../evidence/examples/intervals-to-durations/generated_d1/evidence.json)

This example reuses the existing verified evidence files; no duplicate copy was made. The Original-condition comparison is alongside it in the existing `intervals-to-durations/original` folder.

**Exact returned fragment**

```python
import numpy as np
import mir_eval.util

# Use the provided ref_intervals (shape (4, 2))
durations = mir_eval.util.intervals_to_durations(ref_intervals)

# Verify the shape matches the number of intervals
assert durations.shape == (4,)

# Verify the invariant: duration = end - start
# We check the first interval specifically
expected_first = ref_intervals[0, 1] - ref_intervals[0, 0]
assert np.isclose(durations[0], expected_first)

# Witness: print the sum of durations
total_duration = np.sum(durations)
print(f"__CHECK__ python:mir_eval.util.intervals_to_durations {total_duration}")
```

**Exact standard output**

```text
__CHECK__ python:mir_eval.util.intervals_to_durations 2.0
__DONE__
```

## Thumbnailator

**Selected API:** `Thumbnails.Builder.asBufferedImage`. **Documentation condition:** Generated README D1.

**Actual input.** The preamble creates a 32×24 RGB image with a blue background and a yellow rectangle. The generated program requests a 16×12 thumbnail.

**What the saved program checks.** It throws AssertionError unless the returned image is 16×12, then prints its center pixel. The pixel color is recorded, not asserted by this program.

[Full prompt](thumbnailator/request.json) | [LLM response](thumbnailator/response.txt) | [Complete executable program](thumbnailator/ApiTest.java) | [Actual output](thumbnailator/stdout.txt) | [Errors/warnings](thumbnailator/stderr.txt)

[Execution command and time](thumbnailator/execution.json) | [Model time and tokens](thumbnailator/provider.json) | [Verdict and provenance](thumbnailator/VERDICT_AND_PROVENANCE.json)

[Fixture paths, hashes, and initialization](thumbnailator/INPUTS.json)

**Exact returned fragment**

```java
java.awt.image.BufferedImage result = net.coobird.thumbnailator.Thumbnails.of(sourceImage)
    .size(16, 12)
    .asBufferedImage();

if (result.getWidth() != 16 || result.getHeight() != 12) {
    throw new AssertionError("Thumbnail dimensions mismatch: expected 16x12, got " + result.getWidth() + "x" + result.getHeight());
}

int pixel = result.getRGB(8, 6);
System.out.println("__CHECK__ java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage " + result.getWidth() + "x" + result.getHeight() + "@" + Integer.toHexString(pixel));
```

**Exact standard output**

```text
__CHECK__ java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage 16x12@ffffff00
__DONE__
```

## Complete current API banks

The local manifests below list every selected target, not only the six examples. Original and D1 use the same manifest within each bank. The readable catalog includes each target’s recorded status and its actual attempt directory in both conditions.

[All 2,823 selected API targets and attempt locations](banks/ALL_CURRENT_API_TARGETS.csv) · [Bank roots, hashes, configurations, and task-bank status](banks/BANK_INDEX.json)

| Library / bank | Selected API targets | Complete target list | Current bank type |
|---|---:|---|---|
| RDPro Scala (walkthrough bank) | 261 | [Open manifest](banks/rdpro_scala_selected_api_manifest.json) | Native API-target prompts |
| RDPro Java (separate preserved bank) | 69 | [Open manifest](banks/rdpro_java_selected_api_manifest.json) | Native API-target prompts |
| SedonaDB | 217 | [Open manifest](banks/sedonadb_selected_api_manifest.json) | Native API-target prompts |
| MDAnalysis | 1,519 | [Open manifest](banks/mdanalysis_selected_api_manifest.json) | Native API-target prompts |
| tslearn | 354 | [Open manifest](banks/tslearn_selected_api_manifest.json) | Native API-target prompts |
| mir_eval | 178 | [Open manifest](banks/mir_eval_selected_api_manifest.json) | Native API-target prompts |
| Thumbnailator | 225 | [Open manifest](banks/thumbnailator_selected_api_manifest.json) | Native API-target prompts |

The CSV uses short attempt paths to avoid repeating long cluster paths thousands of times. To open a complete trace, take the corresponding `original_run_directory` or `generated_run_directory` from `BANK_INDEX.json`, append the CSV attempt path, then open `request.json`, `response.txt`, the named program, `execution.json`, `stdout.txt`, or `stderr.txt`. Blank attempt paths mean no recorded attempt was available in this snapshot. Pending MDAnalysis D1 rows are not failures.

For example, in a VS Code Remote SSH window connected to `lab`, open the exact attempt directory from the bank root and CSV. Its `request.json` contains the full request actually sent for that API. The six examples above are copied locally for immediate review; all other per-API prompts and outputs remain in their original cluster run directories. No large input datasets were copied.

## What exists and what is still planned

| Artifact | Current state |
|---|---|
| Selected API inventory | Complete local lists for all six libraries; RDPro has distinct Scala and Java banks. |
| Actual R0 model prompts, snippets, console outputs, and native verdicts | Recorded per attempted target in the linked run directories; six representative traces are available locally above. |
| Fixed independently authored microbenchmark tasks with expected outputs | Not supplied by this current native API-evaluation cohort. The model chooses a small check from the target API, supplied documentation, and available inputs. |
| Current puzzle bank | Not executed in this cohort. The six current configurations refer to `integration_tasks.yaml` paths that were absent when this index was captured; exact paths and existence checks are in BANK_INDEX.json. This R0 path does not read those files. |
| R1/R2 program-repair traces | Not present for these R0-only runs. |
| Generated README revision D2 and remaining ablations | Separate planned or later stages; no measurements are invented here. |

Historical puzzle banks elsewhere in the project may remain useful, but they must be reviewed, versioned, and bound to a new study before being presented as the puzzle bank for this protocol. A manifest of API names is not a substitute for fixed task inputs and independently checked expected answers.

## Storage and verification

Only small trace files and API indexes were copied. `INPUTS.json` links the original fixtures and records their hashes; the complete wrapped program preserves any synthetic inputs. Full prompts are copied exactly, rather than reconstructed from a newer template. The main examples reuse the existing mir_eval evidence and leave earlier Java evidence untouched.

[Verification receipt](VERIFICATION.json)

Bank index captured at `2026-11-19T07:56:40.350132+00:00`. MDAnalysis D1 may continue after this snapshot.
