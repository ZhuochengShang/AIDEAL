# RDPro Java Generated README R0 review

The run completed all 69 targets with **5 passes (7.2%)**, compared with **13/69 (18.8%)** for Original. There were 63 compilation failures and one runtime assertion failure, with zero repairs. The model was `google:gemini-3.1-flash-lite`; all 69 requests returned recorded responses. Eight previously passing targets now fail; there are no new passes.

## Configuration and runtime

The complete execution configuration is identical to Original. Frozen source, API inventory, selected declarations, manifest, scaffold, fixtures, engine, prompt contract, model, transport contract and repair limit match. All 365 configured classpath files exist. The configured Beast 0.10.1 jar contains the relevant Raptor classes and the correctly packaged TIFF readers and BeastOptions. The inspected missing-symbol diagnostics therefore do not establish a missing shared classpath.

## Main failure patterns

| First diagnostic group | Targets |
| --- | ---: |
| Private field access | 2 |
| Invalid constructor | 27 |
| Type mismatch | 3 |
| Invalid Java snippet structure | 13 |
| Unknown symbol / wrong package or member | 10 |
| Instance method called statically | 6 |
| Other method/argument mismatch | 2 |
| Incorrect expected behavior / assertion | 1 |

These groups use the first compiler diagnostic per target; one program can contain additional mistakes.

## Verified documentation mistakes

| Target | Saved README guidance | Actual requirement / result |
| --- | --- | --- |
| `GeoTiffMetadata.getGeoKey` | `new GeoTiffMetadata(tiffFilePath)` | Constructor requires `ITiffReader, TiffRaster` (source line 46). |
| `Intersections.compute` | Calls `Intersections.compute(...)` statically. | It is an instance method (source line 155). |
| `Statistics.isValid` | A fresh, unpopulated instance returns `false`. | Saved execution observes `true`; the audience follows the README and fails its assertion. |

The recorded audience requests contain these erroneous generated README entries. The returned programs follow them. This gives concrete evidence for targeted README revision, while it does not prove the cause of every failure.

The `GeoKeyEntry.getKeyID` response also starts with imports despite a prompt explicitly requesting Java body statements only. The scaffold inserts them inside its method body and javac reports `illegal start of expression`. The inspected instance-method prompts show `(receiver type not resolved)`; owner-qualified signatures are still supplied. This limitation also exists in Original.

Wrong-package examples include `raptor.ITiffReader` / `raptor.TiffReader` instead of `beast.io.tiff`, and `beast.util.BeastOptions` instead of `beast.common.BeastOptions`. The correct classes are present in the configured jar.

## Evidence and next step

- Generated evidence: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java`
- Original evidence: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/qualified-raptor/runs/original/rdpro_java/rdpro_java`
- `RDPRO_JAVA_REVIEW.json` contains exact target IDs, diagnostics, execution paths and matching configuration fields.
- `RDPRO_JAVA_CONTEXT_REVIEW.json` preserves four inspected request excerpts, response texts and source declarations with request hashes.

Preserve this completed R0 result. Feed the diagnosed documentation errors into the planned development/deep-dive stage, then evaluate a separately frozen revised README. Changing snippet handling, receiver metadata or prompts also requires a new version and a matched comparison. No reruns, edits or model calls were performed by this audit.
