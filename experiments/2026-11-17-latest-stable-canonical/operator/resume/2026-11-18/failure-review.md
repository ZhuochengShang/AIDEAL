# Completed-run failure review

All 14 Original R0/README-authoring jobs completed. Completion does not mean the selected environments, API bank, or generated programs are free of issues. This audit made no environment changes, model calls, or reruns.

## Reviewed classifications

| Library | Recorded category | Review |
|---|---|---|
| tslearn | 4 infrastructure | 1 nonexistent internal import; 3 TensorFlow imports added by the model under the configured Keras/torch runtime |
| tslearn | 4 API import | 4 incorrect symbol/import paths |
| tslearn | 1 timeout | Bulk `cache_all()` exceeded 300 seconds |
| MDAnalysis | 17 infrastructure | 11 absent optional dependencies; 2 Biopython compatibility errors; 4 nonexistent internal imports |
| MDAnalysis | 7 API import | 2 unavailable conditional fallback classes; 5 incorrect symbol/import paths |
| MDAnalysis | 4 timeout | 3 programs feed fake text EDR files to a binary reader; 1 BAT analysis timeout with unresolved stall point |
| MDAnalysis | 3 unknown | Native process exits −6/−11; preserve as failed runs even where a completion marker was printed |
| SedonaDB | 65 unknown | 58 invalid SQL function names; 2 expression/type errors; 5 kernel/signature mismatches |

## Confirmed setup and inventory corrections

**MDAnalysis optional dependencies are absent for these 11 targets.** Installed-distribution metadata and execution diagnostics agree.

- `python:MDAnalysis.converters.OpenMMParser.OpenMMAppTopologyParser.parse` — missing module/import: No module named 'openmm'
- `python:MDAnalysis.converters.ParmEd.ParmEdConverter` — missing module/import: ParmEd is required for ParmEdConverter but is not installed. Try installing it with
- `python:MDAnalysis.converters.ParmEd.ParmEdConverter.convert` — missing module/import: ParmEd is required for ParmEdConverter but is not installed. Try installing it with
- `python:MDAnalysis.converters.ParmEdParser.ParmEdParser.parse` — missing module/import: No module named 'parmed'
- `python:MDAnalysis.coordinates.IMD.IMDReader` — missing module/import: IMDReader requires the imdclient package. Please install it with 'pip install imdclient'.
- `python:MDAnalysis.coordinates.IMD.IMDReader.close` — missing module/import: IMDReader requires the imdclient package. Please install it with 'pip install imdclient'.
- `python:MDAnalysis.coordinates.MMCIF.MMCIFReader` — missing module/import: MMCIFReader: To read mmCIF files, please install gemmi
- `python:MDAnalysis.coordinates.TNG.TNGReader.Writer` — missing module/import: TNGReader: To read TNG files please install pytng
- `python:MDAnalysis.coordinates.TNG.TNGReader.parse_n_atoms` — missing module/import: TNGReader: To read TNG files please install pytng
- `python:MDAnalysis.topology.MMCIFParser.MMCIFParser` — missing module/import: MMCIFParser: To read a Topology from an mmCIF file, please install gemmi
- `python:MDAnalysis.topology.MMCIFParser.MMCIFParser.parse` — missing module/import: MMCIFParser: To read a Topology from an mmCIF file, please install gemmi

**Biopython compatibility affects two targets.** Biopython 1.88 is installed, but `Bio.Align.Applications` is absent. MDAnalysis 2.11.0 imports it in `analysis/align.py:200–207`, then reports Biopython unavailable. Installing the same version again would not fix this.

- `python:MDAnalysis.analysis.align.fasta2select`
- `python:MDAnalysis.analysis.align.sequence_alignment`

**Two API-bank entries are conditional empty fallback classes.** The source defines them only when the corresponding dependency import fails; gsd 5.0.1 and h5py 3.16.0 are installed, so these names are absent. Keep them as conditional context or exclude them in a newly frozen bank.

- `python:MDAnalysis.coordinates.GSD.MockHOOMDTrajectory` — source/package/MDAnalysis/coordinates/GSD.py:62
- `python:MDAnalysis.coordinates.H5MD.MockH5pyFile` — source/package/MDAnalysis/coordinates/H5MD.py:227

## SedonaDB interpretation

The 65 unknown outcomes contain real SQL errors and nonzero exits. The classifier fails to recognize qualified exception names such as `sedonadb._lib.SedonaError`. All 58 invalid-function names are setup/helper calls in the generated programs, not the assigned target API: 56 uses of `RS_FromGeoTiff`, one `ST_FromGeoRaster`, and one `read_binary`. This confirms the location of the failure, not the provenance of every helper choice; only one request was checked for whether it supplied the name.

The kernel failures need source/documentation comparison. In particular, original documentation advertises overloads absent from the pinned implementations for `ST_ClosestPoint` and `ST_MakeValid`. Do not describe every such failure as a missing dependency or an invented API. The separate Sedona audit records the relevant source and documentation excerpts.

## Limits and next action

- The optional-dependency and conditional-target findings are confirmed. Exact causes of the BAT timeout, native XTC crash, and timeout process-pipe behavior remain provisional. No rerun was performed.
- Preserve the completed results, denominator and original error labels. Attach these distinctions in a derived report; classification corrections do not require another model call.
- Dependency versions, fixtures, target selection, prompt or execution changes require a new environment/bank fingerprint and output namespace. Do not overwrite or silently combine them with this completed R0.
- Before later conditions, review dependency compatibility, optional formats, conditional API eligibility, safe native-buffer contracts, and bounded external-I/O tasks.

Evidence: [structured review](failure-review.json), [Python execution excerpts](failure-review-python-raw.json), [installed versions and source excerpts](failure-environment-evidence.json), and [Sedona review](sedona-failure-review.json).
