# RDPro official-source verification

Verified against a fresh HTTPS clone of [the official Beast/RDPro repository](https://bitbucket.org/bdlabucr/beast.git) on 2026-09-22T18:00:07.532920+00:00.

| Identity | Value |
|---|---|
| Official default branch | `master` |
| Official default commit and `beast-0.10.1` tag | `547f7f912131a8032f6b5d26991415a5faf05cef` |
| Official release date | `2025-02-26T22:28:30-08:00` |
| Existing published Original snapshot | `5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8` |
| Exact shared Git tree | `757142fe21ba53b1388880d6abc7423aff844295` |

The two commits have **identical source content**. Verification compared every recursive tracked path, mode, type and Git object ID, then independently calculated SHA-256 for all **886 unique blobs** in both stores: **921 tracked entries, 28,982,293 bytes, zero differences**. The current official default is this same release.

The existing snapshot commit is a publication identity, not an upstream commit: it deliberately omits historical parents. This distinction does not change its source bytes. The study can retain its existing source-content pin and measured evidence while recording the official source identity precisely.

## Origin of the disputed methods

`RasterSchemaHelper.inferSchema` (line 101) and `RasterSchemaHelper.detectType` (lines 108–128) already exist in the official release at:

`cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/RasterSchemaHelper.scala`

Their lines originate in official commit `fa531896a8cb6ec0b50eb2cc435d44fe08a8b2a7`, “Refactor RasterFeature”, authored by Ahmed Eldawy on 2024-06-11. The file was introduced earlier that day in `8fef8400beed393cbf6584dfe02e27f7cf7457ea`, “new RasterMetadata with extent Row”, authored by Zhuocheng Shang. Both commits are ancestors of the official release and are present in the fresh clone. These are existing library methods, not generated AIDEAL aliases.

## Historical Git integrity

The fresh upstream clone itself reports `duplicateEntries` in historical tree `90b33f9e36ee3d4f833f496f37c50530aba8571c` under `git fsck --full --strict --no-reflogs`. That object is reachable from the release history. This explains why source-tree equality must be distinguished from clean historical Git objects, and why copying the original ancestry to a stricter host may be rejected. The current release tree and all study source blobs match; this check does not rewrite or bypass validation of the malformed ancestor.

[Machine-readable proof](provenancePUBLIC.json) includes the selected source/README/license hashes, method origins and exact integrity diagnostic. Existing measured treatment versions, frozen protocols and results remain unchanged. This verification used no model calls or target-library execution.
