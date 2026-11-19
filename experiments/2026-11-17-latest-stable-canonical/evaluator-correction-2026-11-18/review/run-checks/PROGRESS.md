# AIDEAL experiment progress — November 18, 2026, evening

Snapshot before resume: 11:23 p.m. Pacific. This replaces the earlier launch-only progress snapshot; it does not replace historical measurements.

**13 of 14 Original/D1 condition runs are complete.** All Original banks are complete. MDAnalysis D1 is the only incomplete condition. Seven execution banks represent six libraries because RDPro Java and Scala are reported separately.

The saved checkpoint contains **4,332 returned responses and execution outcomes out of 5,646 planned targets (76.7%)**. Another target has a recorded provider failure. Thus 1,314 targets still require a response, including that failed request. No completed target is scheduled for regeneration.

| Bank | Original R0 | Existing generated README D1, R0 |
|---|---:|---:|
| RDPro Java | 12/69 (17.4%) | 4/69 (5.8%) |
| RDPro Scala | 20/261 (7.7%) | 14/261 (5.4%) |
| MDAnalysis | 592/1519 (39.0%) | In progress; 205/1,519 executed at checkpoint |
| tslearn | 211/354 (59.6%) | 221/354 (62.4%) |
| mir_eval | 134/178 (75.3%) | 144/178 (80.9%) |
| Thumbnailator | 109/225 (48.4%) | 97/225 (43.1%) |
| SedonaDB | 87/217 (40.1%) | 96/217 (44.2%) |

These are single-trial native execution/self-check acceptance results with Gemini `gemini-3.1-flash-lite`, zero code repairs, and no D2 revision. They are not independently verified fixed-task accuracy. The audience chooses its usage program and checks; differences do not by themselves establish documentation quality or causal improvement.

## Issues and actions

1. **Temporary provider interruption, resumed.** At 10:39 p.m. Pacific the MDAnalysis D1 worker stopped at `MDAnalysis.analysis.nucleicacids.NucPairDist` after Gemini returned 503 UNAVAILABLE with a high-demand message. This was not a billing or library-installation error. At 11:23 p.m. Pacific the unchanged controller was relaunched after runtime/readiness and all 13 completed-condition hash checks. The 205 delivered MDAnalysis D1 targets remain preserved; the failed request receives a new physical attempt. The original error receipt remains evidence.
2. **RDPro Scala path-description issue, confirmed.** Four recorded failures use `output_dir` as a plain filesystem path although the scaffold supplies a `file:///...` URI. The shared model-visible instructions did not disclose that representation. Keep these results unchanged and flag interpretation for a separate, matched input-contract correction. Do not attribute these four failures solely to documentation or model ability.
3. **Most inspected RDPro failures are compilation errors.** Original/D1 Java have 54/62 compile failures; Scala has 229/227. An example is the nonexistent `rasterRDD.metadata` property. Spark's background `BlockManagerId` message also occurs in passing runs, so its presence alone is not the reason a program failed.
4. **Other bounded failure review.** Forty recent non-RD failures showed incorrect calls/assertions or invented imports without establishing a new setup fault. The tslearn `dependency-unverified` labels include invented module paths and TensorFlow imports despite a configured Torch backend; those labels are not proof of missing infrastructure.

5. **Concrete D1 documentation defects.** The bounded RDPro audit found a `GeoTiffMetadata.getGeoKey` entry describing a nonexistent String constructor, and a `Statistics.isValid` entry claiming an unpopulated instance returns false when the source does not support that claim. Example audience programs follow these instructions and fail. These are candidates for a separately validated D2 revision; the measured D1 remains frozen. This sample does not establish the cause of every regression.

[RDPro bounded audit with source, prompt and execution paths](2026-11-18-night-RDPRO_FAILURE_AUDIT.json).

## Evidence and scope

All 13 completion receipts match their result files and saved native results. [Detailed integrity audit](2026-11-18-night-progress-audit.json) and [summary with failure categories and recorded usage](2026-11-18-night-progress-summary.json).

The resume receipt is `explicit-inputs-r0/operator/resumes/20261119T072353Z/RESUME.json`; controller PID at restart was 3289545. The immutable code release remains `2026-11-18-corrected-r0-d8ba3815cf95`. No model prompt, README, source implementation, scoring rule, fixture, or selection changed during this resume.

The zero-model historical replay phase has not started; it follows completion of Original/D1. R1/R2, D2 and the full eight-condition study remain separate planned work. The earlier stopped `fresh-original-d1` cohort remains separate.
