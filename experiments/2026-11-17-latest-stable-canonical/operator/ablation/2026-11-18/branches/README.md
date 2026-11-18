# Generated README branches

All six libraries now have the completed, unchanged authoring outputs on their `readme-only` and `combined` branches. Local Git references, cluster Git references and GitHub point to the same commits. Installation does not establish evaluation success.

**Combined is incomplete:** aliases and native source-embedded fix hints still require generation, validation and installation.

| Library | API entries | Commit | Generated documentation |
|---|---:|---|---|
| rdpro | 330 | [fd788737](https://github.com/ZhuochengShang/AIDEAL-RDPro/commit/fd7887376e0c0b4f9f4cdaa88cc58797b6b7f207) | [rdpro_java](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/fd7887376e0c0b4f9f4cdaa88cc58797b6b7f207/docs/LLM_readme.java.md), [rdpro_scala](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/fd7887376e0c0b4f9f4cdaa88cc58797b6b7f207/docs/LLM_readme.scala.md) |
| mdanalysis | 1538 | [abb2a0c2](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/commit/abb2a0c22ebfd684ea635d6de7da4008f6664431) | [mdanalysis](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/blob/abb2a0c22ebfd684ea635d6de7da4008f6664431/docs/LLM_readme.md) |
| tslearn | 362 | [043079c3](https://github.com/ZhuochengShang/AIDEAL-tslearn/commit/043079c3a230ec7efb55c4ffe31486d98c262da4) | [tslearn](https://github.com/ZhuochengShang/AIDEAL-tslearn/blob/043079c3a230ec7efb55c4ffe31486d98c262da4/docs/LLM_readme.md) |
| mir_eval | 178 | [477d66dc](https://github.com/ZhuochengShang/AIDEAL-mir_eval/commit/477d66dcca3929b56e8771cd4e74b00875251b97) | [mir_eval](https://github.com/ZhuochengShang/AIDEAL-mir_eval/blob/477d66dcca3929b56e8771cd4e74b00875251b97/docs/LLM_readme.md) |
| thumbnailator | 225 | [6fad1626](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/commit/6fad1626d2b045c14063515534f04e1e75fa3205) | [thumbnailator](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/blob/6fad1626d2b045c14063515534f04e1e75fa3205/docs/LLM_readme.md) |
| sedonadb | 217 | [3c55de8b](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/commit/3c55de8b087ec181741c4890241f8cedb00de499) | [sedonadb](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/blob/3c55de8b087ec181741c4890241f8cedb00de499/docs/LLM_readme.md) |

## What changed

- Only generated documentation files were added. Each commit directly descends from the pinned public baseline.
- RDPro keeps separate Java and Scala files in one commit, at `docs/LLM_readme.java.md` and `docs/LLM_readme.scala.md`. Other libraries use `docs/LLM_readme.md`.
- Original, Alias only and Error hints only remain at their recorded baseline commits. Historical branches remain unchanged.
- Installation did not switch a checkout or alter its index. Both treatment references changed in one atomic transaction per repository.
- The README files match the author completion receipts and cover 2,850 selected targets.

## Review a version

The commit links open the exact files. All five branch names use the prefix `study/2026-11-17-latest-stable-canonical/`, followed by `original`, `readme-only`, `alias-only`, `error-hints-only` or `combined`.

For an existing RDPro clone, this fetches documentation without switching working files:

```bash
git fetch https://github.com/ZhuochengShang/AIDEAL-RDPro.git study/2026-11-17-latest-stable-canonical/readme-only
git show FETCH_HEAD:docs/LLM_readme.scala.md
```

Use the corresponding repository and file names for another library. Evaluation must bind the documentation and runtime explicitly. A branch name alone does not select experiment inputs.

## Evidence

- `BRANCHES.json` records commits, document hashes, counts and branch states.
- `PLAN.json` binds baselines and author completion receipts.
- `CLUSTER_INSTALLATION.json` records checkout/index preservation and protected references.
- Eight existing installation tests and four study-specific tests passed. They cover two-document atomic installation, interruption recovery, changed inputs and changed branches.

Library repositories hold the actual documentation. The shared AIDEAL study holds this plan and verification evidence.
