# AIDEAL live pipeline audit

Read-only snapshot at **2026-11-19T00:18:42.034934-08:00**, **2026-11-19T08:18:42.034934+00:00 UTC**. The worker can advance between file reads.

The current run is progressing. The controller, supervisor and MDAnalysis worker are alive, and the relevant launch/queue/condition/execution locks belong to these processes. No restart, paid call or frozen-file change was made in this audit.

## Progress

- **13 of 14 condition arms complete**.
- **4729/5646 logical outcomes recorded**, across 2823 selected APIs and two README conditions.
- MDAnalysis Generated README remains pending at **602/1519 completed outcomes, 253 accepted**. The 603 returned provider receipts include the next target being executed.
- Exactly one provider error remains recorded, the previously recovered 503 temporary-capacity error at `NucPairDist`. No new provider error was observed.
- All 13 completed result hashes match their completion receipts. Their result lengths match the selected denominators.
- Model `gemini-3.1-flash-lite`; initial programs R0 only, no program repairs or D2. These are **native acceptance**, not independently checked task accuracy.

| Bank | Selected APIs | Original accepted | Generated README accepted |
|---|---:|---:|---|
| rdpro_java | 69 | 12/69 | 4/69 |
| rdpro_scala | 261 | 20/261 | 14/261 |
| sedonadb | 217 | 87/217 | 96/217 |
| mdanalysis | 1519 | 592/1519 | Pending (602 outcomes, 253 accepted so far) |
| tslearn | 354 | 211/354 | 221/354 |
| mir_eval | 178 | 134/178 | 144/178 |
| thumbnailator | 225 | 109/225 | 97/225 |

## Integrity and synchronization

- Frozen release `2026-11-18-corrected-r0-d8ba3815cf95`: **146/146 files match the deployment manifest**; the manifest matches the readiness receipt.
- GitHub study branch head `7ac965c80f390fb8cf0403c1c8f7a0d810823d3b`: all 146 evaluator-file Git blob hashes match the deployed release. The fetched tree is not truncated.
- All 146 published documentation paths match canonical local and workflow copies; all 145 unique cluster paths match their publication receipt. Two repository pointers map to the same identical cluster pointer.
- The current local development checkout differs from the frozen evaluator in four files: `tests/test_native_execution_contract.py`, `vendor/aideal_engine/src/aideal/doc_check_execution.py`, `doc_check_provenance.py`, and `native_execution_contract.py`. These are development changes being reviewed separately. **The active cluster run has not adopted them.** This audit does not claim the whole mutable workspace is identical across operating systems.

## New scope finding

Three empty fallback classes remain selected even though they exist only when optional imports fail.

| Selected target | Definition/guard | Actual runtime |
|---|---|---|
| `MDAnalysis.coordinates.GSD.MockHOOMDTrajectory` | GSD.py:62, `except ImportError` at 58 | `HAS_GSD=True`; class absent |
| `MDAnalysis.coordinates.H5MD.MockH5pyFile` | H5MD.py:227, `except ImportError` at 221 | `HAS_H5PY=True`; class absent |
| `MDAnalysis.coordinates.IMD.MockIMDClient` | IMD.py:157, `except ImportError` at 150 | `HAS_IMDCLIENT=True`; class absent |

A source scan of all selected Python definitions found exactly these three retained definitions inside ImportError handlers. This is a selected-scope problem, not a missing-dependency problem. The scanner visits exception handlers but saves only `Try@line`, omitting the exception type, and labels empty class constructors as implementations. A future inventory revision should record branch conditions and source-proven fallback exclusions. **The current 1519 denominator is unchanged.** Source paths, hashes, line numbers and runtime availability probes are in the companion JSON.

## Bounded failure review

The latest eight MDAnalysis failures include API-contract mistakes such as assigning to `MemoryReader.frame`, passing a Timestep to `NullWriter.write`, and asserting a particular representation-string format. Recent import labels include invented converter module names; they do not prove an absent dependency. No new shared runtime/setup failure was established by this bounded sample, but the three selected fallback targets above are confirmed unusable in the configured runtime.

The earlier RDPro Scala URI input-contract limitation remains open. Its scores must remain provisional. Current native acceptance also lacks independent fixed-task oracles. Neither limitation can be resolved by relabeling or silently adjusting the recorded counts.

## Evidence

- Machine-readable audit: `live.json`
- Conditional fallback evidence: `fallbacks.json`
- Cross-location hash comparison: `sync.json`
- Active cluster namespace: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/explicit-inputs-r0`
- Published study branch: https://github.com/ZhuochengShang/AIDEAL/tree/study/2026-11-17-latest-stable-canonical

The machine-readable audit retains exact result/completion/checkpoint/evidence paths and their checked hashes. No credential files, credential values or excluded quickrun source were read.
