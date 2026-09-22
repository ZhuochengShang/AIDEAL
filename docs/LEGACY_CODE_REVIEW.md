# Review of remaining legacy code

The unused `aideal/alias_functions.py` predefined RDPro wrapper renderer has been retired. Its 106 lines supplied seeded raster/shapefile wrappers; it had no caller in the inspected CLI, MCP, configuration, facades or tests, or across 21 inspected external runtime roots. Recovery bytes and hashes are preserved in the local cleanup archive.

The current alias path is `preview-library` → `propose-library` → `bundle-proposals` → `install-treatments`. It uses an explicit model prompt, source/API context and validation records. A generated suggestion is not proof of correct behavior.

| Retained component | Actual consumer |
| --- | --- |
| `aideal/fix_guide.py` | Native comprehension repair imports its classifier in `doc_check_execution.py` |
| `aideal/alias_registry.py` | Native CLI, MCP and API-overload audits |
| `studies/historical/` | Explicit historical reporting CLI and reproduction tests |
| Portable `run-arm` command | Compatibility response directing old callers to explicit freeze/run commands |

Older code is retained when it supports a working interface or historical reproduction. Static call graphs alone cannot establish whether external users import a public function. This review covers the inspected project/runtime roots; it does not claim knowledge of every external caller.

All 36 native CLI commands have dispatch branches. Original evaluation controllers, model adapter, existing freezes and measured evidence were preserved. Live maps were regenerated; historical snapshots retain the old module reference. No old evidence manifest was rewritten to hide the removal.
