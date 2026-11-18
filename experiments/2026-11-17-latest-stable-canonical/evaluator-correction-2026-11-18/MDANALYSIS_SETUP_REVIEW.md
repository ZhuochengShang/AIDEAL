# MDAnalysis setup review — 18 November 2026

This folder records **setup checks, not experiment accuracy**. Every check described here used a known program or a mocked model response. No paid model request was made.

## Current inputs

| Item | Reviewed version |
|---|---|
| Library | MDAnalysis 2.11.0; MDAnalysisTests 2.11.0 |
| Historical API bank | 1,538 targets, preserved with its original results |
| Corrected bank | 1,519 targets |
| Selection correction | 15 private Distopia forwarding functions, one empty documentation mock, and three direct NumPy/RDKit forwarding wrappers excluded by source structure |
| Module audit | All 160 defining modules for retained targets imported successfully |
| Data | 18 named input roles; a catalog binds 523 public upstream data files by path and SHA256 |
| Execution | A separate Python overlay; old packages and measured programs remain unchanged |

Use these files together:

- [Reviewed runtime profile](runtime-mdanalysis-final-2026-11-18/runtime_profile.json)
- [Matched input bundle](fixture-development-v1/mdanalysis/input_bundle_final.json)
- [Selection revision](fixture-development-v1/mdanalysis/selection-correction-final/selection_revision.json)
- [Source evidence for all 19 exclusions](fixture-development-v1/mdanalysis/selection-correction-final/exclusion_audit.json)
- [Setup report and validation limits](runtime-mdanalysis-final-2026-11-18/setup_report.json)

The paths inside machine receipts refer to the lab cluster. This local folder mirrors evidence and small supplied inputs; it does not duplicate the installed environments or the 109 MB upstream data collection.

## What changed

The isolated runtime adds Biopython 1.85, OpenMM 8.3.1, ParmEd 4.3.1, PyTNG 0.3.4, Gemmi 0.7.5, IMDClient 0.2.4, and Chemfiles 0.10.4. MDAnalysis, tslearn, NumPy and Torch retain their earlier versions. The original installed MDAnalysis, tslearn and Biopython files matched their installation records after setup.

The official BSD-licensed 3DNA 2.4 source was built separately at commit `43eafa8407be1a8292e38ca995ab16adfbeffcac`. Its real executable produced numeric output through MDAnalysis's legacy wrapper. No replacement implementation or fake executable alias was installed.

## Data and fixture lifecycle

| Input family | Provision and check |
|---|---|
| Protein system | Existing PSF/DCD/PDB/GRO/XTC inputs remain available |
| TNG, H5MD, mmCIF, GSD, TPR, EDR, XVG, FASTA | Small official upstream fixtures copied into the new versioned input folder; each checked with the corresponding reader/parser |
| Chemfiles | Uses a validated TRR trajectory; the earlier rejected short-CRYST1 PDB probe remains recorded |
| IMD | A real loopback IMDv3 server supplies a frozen TRR trajectory; a fresh port and cleanup belong to each attempt |
| X3DNA | Official DNA structure plus the installed executable path |
| Other formats | The upstream catalog records available files, including deliberately invalid specimens; catalog inclusion alone does not establish semantic validity |

The [shared scaffold](fixture-development-v1/mdanalysis/api_test_scaffold.py) starts IMD support only for an IMD/StreamReaderBase target identified by `requested_target.json`. It closes the stream when the candidate succeeds or fails. Audience programs still call the actual library. Newly created data and output files belong under the isolated attempt's output directory.

## What the audience receives

The task identifies the selected API and its declaration. The documentation condition selects Original documentation or the saved generated README. Both conditions receive identical input paths, setup descriptions and output-directory rules. The bundle explains the format-specific paths and, when relevant, `imd_url`, `imd_host`, `imd_port`, `imd_n_atoms`, `dna_pdb_path`, and `x3dna_executable`. It supplies no expected numeric answers.

The native control driver saves the full rendered requests, returned control programs, execution records, output and errors under `current/preflight/native-controls/mdanalysis/`. These requests show what would be sent to the model, while the control responses are explicitly mocked.

## Limits of the evidence

Imports and representative capability checks establish that the audited prerequisites work. They do not certify a successful independent reference program for every retained API. The upstream catalog includes negative test inputs. New setup failures must remain identifiable and must not disappear from the scheduled denominator. The earlier 1,538-target results and the corrected 1,519-target study have different identities and must remain separate.

## Execution controls

The actual prepared Original and Generated D1 settings passed six expected-outcome controls with a mocked provider and real execution: valid distance calculations passed, intentionally wrong assertions failed, and real IMD streaming passed and failed exactly as specified. The final 1,519-target profile also passed independent positive/negative replay controls. These are setup controls, not audience-model results.

The native control driver took about 50 seconds per independent invocation, but its recorded API loop took 5.4–5.9 seconds. Inventory and provenance setup plus final coverage scans account for the remaining time and run once per full evaluator invocation. Separate warm runtime-file verification took about 0.67 seconds.
