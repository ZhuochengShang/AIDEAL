# Optional API source ownership

`codebase.api_origin` filters **definition sites**, using their defining source
file and qualified declaring namespace. It does not filter by a bare API name,
parameter types, called functions, imports appearing in a function body, or an
external base class. A library-defined `mapPixels` calling Spark is retained;
a library-defined override is retained too.

The option is absent by default. Existing frozen configurations, inventories,
selection rules and outputs are unchanged unless a new configuration explicitly
enables it. It does not establish new final API counts, change same-name owner
selection, restore previously omitted definitions, or prove semantic equivalence.

## Configuration examples

These examples are prospective settings, not changes to existing experiments.
Roots are relative to the effective configuration root; absolute roots are also
accepted. Check that they cover every intended production source directory.

```yaml
# Entire Beast, using a source checkout at the project's source/ path.
codebase:
  api_origin:
    source_roots: [source]
    library_namespaces: [edu.ucr.cs.bdlab, org.apache.spark.beast]
    external_namespaces:
      - java
      - javax
      - scala
      - org.apache.spark
      - org.locationtech.jts
```

```yaml
# Python package example; keep the source-glob/visibility policy separately.
codebase:
  api_origin:
    source_roots: [source/package/MDAnalysis]
    library_namespaces: [MDAnalysis]
    external_namespaces: [builtins, math, numpy, scipy, pandas]
```

All three keys must be explicit lists. Source roots and library namespaces must
be nonempty. Namespace matching respects qualified-name boundaries: `ownlib`
does not match `ownlibrary`. External namespaces are project configuration,
not hard-coded library-specific exclusions.

The most specific matching qualified namespace wins. For example, the custom
`org.apache.spark.beast` and `org.apache.spark.beast.sql` definitions use the
library rule above even though `org.apache.spark` is an external rule. Unrelated
Spark definitions remain external. A more specific external rule likewise
overrides a broader library rule. If the same most-specific prefix occurs on
both sides, ownership stays unresolved (`conflicting_namespace_rules`). A winning
library namespace still requires an owned source file and valid applicable hashes.
The policy version is `source_file_and_declaring_namespace_v2`, so ownership
receipts distinguish this rule from the earlier overlap-conflict policy.

The pinned Beast 0.10.1 source has four production files under this custom
Spark namespace: `cg/src/main/scala/org/apache/spark/beast/CRSServer.scala`,
`SparkSQLRegistration.scala`, `sql/EnvelopeDataType.scala`, and
`sql/GeometryDataType.scala`. Two additional matching files are tests, not
additional production APIs. Keep the production/test source-scope rules separate
from this ownership rule.

## Discovery and audit

```python
from aideal.api_discovery import (
    api_origin_audit, public_api_details, public_api_surface, render_api_surface,
)

names = public_api_surface(cfg)
definitions = public_api_details(cfg)
audit = api_origin_audit(cfg)
print(render_api_surface(cfg))
```

When enabled, normal details/surface outputs contain only `library_defined`
sites. `api_origin_audit` retains every supplied declaration decision, including
excluded and unresolved evidence. The rendered surface prints policy/hash,
status counts, and excluded/unresolved identities and reasons.

| Status | Example reason | Interpretation |
|---|---|---|
| `library_defined` | `owned_source_and_declaring_namespace` | Both the resolved source path and declaring namespace belong to the configured library. |
| `external_defined` | `external_declaring_namespace` | An explicit external defining namespace identifies the API as a dependency API. |
| `unresolved` | `exposure_without_defining_source` | An inherited/import-only exposure lacks actual defining-source evidence. |
| `unresolved` | `conflicting_defining_owner_evidence` | Defining/declaring ownership claims disagree. |
| `unresolved` | `namespace_not_classified` | No configured library/external namespace establishes ownership. |
| `unresolved` | `defining_file_outside_source_roots` | The definition is outside the allowed roots, including a nested symlink escape. |
| `unresolved` | `defining_file_hash_mismatch` | At least one applicable same-file hash claim is stale or contradictory. |

Each included row gains an `api_origin` decision. The audit binds the policy,
qualified identity, site/line/signature, actual source path and observed file
SHA256 into `ownership_sha256`. Supplied file hashes are verified. If no prior
hash was supplied, the observed hash is recorded without claiming a previous
immutable binding. An explicitly configured source-root symlink is supported;
a nested file symlink resolving outside all configured roots cannot be included.

Readers with inherited/re-exported exposure records should supply
`defining_file`, `defining_owner` (or `declaring_owner`), and where available
`defining_file_sha256`. These facts describe the actual declaration, not the
importing/calling file. A relative Python owner can be qualified through a
matching defining module or same-file qualified identity. All hash claims tied
to the same resolved file are checked.

## Scope and limits

- Existing compiler/source-audited readers already return declared source
  sites, and Python AST discovery excludes import statements and inherited-only
  members. Origin filtering therefore need not shrink the old selection count.
- Ownership consumes the defining identities supplied by those readers; it is
  not an independent replacement for their parser/provenance validation.
- Legacy Java/Scala regex details lack qualified ownership and remain unresolved
  when this option is enabled. Use source-bound/compiler inventories for them.
- This is an API inclusion filter, not a filesystem read sandbox. Legacy
  discovery can read a source-glob symlink before this later filter rejects it.
- SQL registrations remain unchanged when the option is absent. A SQL
  documentation page or invented `SQL` namespace is not defining-source proof.
  Enabling it on current ownerless SQL rows yields
  `registered_sql_requires_defining_source_binding`. Do not enable SQL origin
  filtering until the existing Rust-registration provenance is explicitly
  mapped to defining files/namespaces; this patch does not invent that mapping.
- Unresolved rows remain visible for review. Excluding them from ordinary
  discovery is not approval to launch a revised study; the separate review gate
  and source/owner selection policy still apply.

## Verified synthetic example

The offline test fixture contains `from math import sqrt`, an uninstalled
`pyspark.RDD` import, a local `mapPixels` that calls `sqrt`, and a locally
overridden `LocalRDD.map`. Discovery parses that file without importing it.
The actual discovered names are `LocalRDD`, `map`, and `mapPixels`; imported
`sqrt` and inherited-only Spark members are absent. A separate same-name test
proves an external `map` declaration cannot supply documentation-selection
evidence to a custom `map` declaration.

The staged validation includes 24 origin tests and 22 existing offline
discovery/compiler-registry contracts, all passing. No provider, compiler,
subject-library execution or measured experiment is required by these tests.
