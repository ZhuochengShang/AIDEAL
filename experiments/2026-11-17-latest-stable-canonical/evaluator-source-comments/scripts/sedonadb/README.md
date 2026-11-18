# SedonaDB native Original R0 adapter

This stages real audience-written Python assertion snippets against the official
SedonaDB SQL connection. It does not replay the 322 archived SQL examples.

Install `sedonadb==0.5.0`, `pyarrow`, `rasterio`, `pyproj`, and `pyyaml` in the
measured Python environment. Official PyPI provides CPython 3.9–3.15 Linux
manylinux_2_28 wheels for x86_64 and aarch64. The measured wheel and the historical
source commit have separate identities; matching version numbers do not prove
matching source revisions.

Use official release tag `apache-sedona-db-0.5.0`, commit
`751453f04cd6e09842adf3073b2b3dac7d1777bc`, for the new 0.5.0 baseline.
`sedonadb-release-0.5.0.tar.gz` and `release_source_provenance.json` supply the
exact source archive, its checksum, official commit, and Git tree ID. The release
has 212 SQL function reference pages plus an index. Runtime scope is determined
from the measured wheel; the first remote inventory found 219 scalar functions
and seven aggregate functions, totaling 226.

Integrate `api_registry.py` into `vendor/aideal_engine/src/aideal/` and apply
`native_sql_inventory.patch`. Also include `api_registry.py` in the README
generation engine fingerprint list. The changes are opt-in through
`codebase.api_inventory` plus its mandatory SHA-256. They make registered SQL
names a distinct API surface, allow original `.qmd` documents, and put each SQL
function's own original page before related examples in retrieval.

Run the following with the measured interpreter, substituting actual paths:

```sh
python preflight.py --output runtime.json \
  --expected-registry WORKFLOW/studies/sedonadb/evidence/configured_registry.json \
  --fixtures WORKFLOW/studies/sedonadb/evidence
python build_setup.py --workflow WORKFLOW --source PINNED_SEDONA_SOURCE \
  --output NEW_SETUP_DIRECTORY --python MEASURED_PYTHON --preflight runtime.json \
  --source-revision 751453f04cd6e09842adf3073b2b3dac7d1777bc \
  --source-provenance release_source_provenance.json
```

The setup builder produces a catalog entry suitable for
`scripts/run_original_micro.py`, a native configuration, frozen manifest, source
evidence inventory, project profile, local fixtures, and runtime helpers.
Without a successful preflight the catalog stays explicitly blocked. The runtime
registry supersedes the historical registry when it differs; newly observed
names retain source/documentation evidence or explicitly labeled measured
registry evidence when no literal source registration is found. No model calls occur
during preflight or preparation.

Before importing SedonaDB, the helper replaces inherited PROJ/GDAL path settings
with the measured wheels' data paths. Rasterio/GDAL use Rasterio's bundled PROJ
database; Sedona's standalone PROJ engine explicitly uses pyproj's database and
library. Both database checksums and schema-layout versions are recorded.

Historical inventory: 198 Sedona scalar names plus seven Sedona aggregate names
make 205 registered targets. Of these, 200 have individual original reference
pages and five do not. The original reference has 201 function pages plus an
index; `ST_NumPoints` is documented but absent by that name from the historical
registry. These counts are not interchangeable with Rust methods or example
blocks. A new runtime's registry, source mapping, and count are recorded afresh.

Execution uses the existing native R0 engine: one audience response, no repairs,
original relevant documents, an actual Python assertion, and an emitted
`__CHECK__ <target> <witness>` line. The helper records actual target SQL calls
and requires successful materialization before `__DONE__`. SQL comments and
string literals do not qualify as target use. The snippet's own assertion is
the correctness check; this is not an independent semantic oracle and cannot
prove that every audience assertion is meaningful. Operator smoke tests and
their negative controls remain separate from audience scores.

The unchanged source and documentation are bound by checksums. Reuse prepared
outputs only with identical inputs. On Linux, use new Linux interpreter and
extension paths; archived macOS binaries and dylib paths are not reusable.

Validation performed locally without an LLM: seven focused adapter tests pass;
an isolated patched native engine loads all 205 historical records and manifest
names, resolves 203 original documents, accepts the project profile, and retrieves
the ST_Area and RS_Example original contracts. Real library smoke validation must
run in the measured environment with `preflight.py`.
