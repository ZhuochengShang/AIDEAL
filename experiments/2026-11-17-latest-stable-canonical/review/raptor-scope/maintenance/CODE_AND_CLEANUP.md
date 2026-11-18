# Code review and cleanup

The strict RDPro selection added **76 net runtime lines in four existing modules**, one helper and no new production module or public command. These counts compare `aedf677` with `21e5f20`; they include comments and blank lines. This navigation update adds no runtime behavior.

## Follow these four files

All paths below start at `AIDEAL_workflow/vendor/aideal_engine/src/aideal/`.

| Read order | File and starting line | Responsibility |
|---|---|---|
| 1 | `api_public_inventory.py:475`, `qualified_inventory_details` | Read the bound source ledger and review; verify identities and hashes. |
| 2 | `api_canonical_selection.py:302`, `reviewed_selection_exclusion_ids` | Validate explicit source exclusions before choosing overloads. This is the only new runtime helper. |
| 3 | `api_canonical_selection.py:471`, `_select_qualified` | Keep the largest eligible overload within each qualified owner/API. |
| 4 | `api_registry.py:87` | Carry the review binding when preparing an output directory. |
| 5 | `doc_check_inputs.py:332` and `:394` | Build correct constructor/type context instead of treating every target as an instance method. |

The existing R0 and README commands consume the same selected manifest. There is no second selection CLI. The new regression tests cover exclusion integrity and constructor context; test code is separate from runtime code. [Exact footprint](code-footprint.json).

## Everyday review

1. Read [the current experiment guide](../../../EXPERIMENT_GUIDE.md).
2. Inspect the [330 selected APIs](../strict-no-wrappers/SELECTED_APIS.json) and [source exclusions](../strict-no-wrappers/selection_exclusions.json).
3. Inspect [the recorded queue commands](../operator/QUEUE.json). Do not start a duplicate queue while these outputs are owned by a running process.
4. On the cluster, read live progress with the existing monitor:

```bash
/home/zshan011/apps/aideal/venv/bin/python \
  /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/qualified-raptor/launch/progress_all.py
```

The study's audit/rebuild scripts are preserved preparation evidence with machine-specific paths. They are not extra daily commands. Two missing dependencies used by `validate_strict.py` have been restored under `document-audit/`; no frozen script was rewritten.

## Cleanup performed

Removed **88 task-generated temporary files, 40,609,868 bytes (38.7 MiB)**: a reconstructible full debug receipt, three obsolete temporary Git indexes and 84 Python bytecode files. The compact published receipt binds the removed debug receipt's normalized content. [Exact removal receipt](cleanup-receipt.json).

No newly introduced runtime helper was unused: the exclusion helper is called by the source reader. Removing it would disable the requested review checks. No measured results or library source were deleted.

Older 171/422/406 records now appear under the history section of the [entry page](../README.md). Their files stay in place because frozen reconstruction inputs refer to them. Moving them during the run would break those references. The current route uses `strict-no-wrappers/`, `plan/` and `operator/`.

## Policy boundary

RDPro has the strict reviewed exclusions. The other libraries share parts of the extraction infrastructure but still need the reviews listed in [Selection policy](SELECTION_POLICY.md). Existing runs retain their original denominators and cannot be relabeled as strictly filtered results.
