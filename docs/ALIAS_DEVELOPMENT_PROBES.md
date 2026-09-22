# Independent alias development probes

These helpers prepare and run fresh paired examples for the 16 declared RDPro
methods. They accept no task bank, reference solution, fixture or private oracle.
The generated aliases can cover a subset of the methods; every actual alias is
checked in both `alias_only` and `combined`, with untreated targets reported.

`source-review` checks the exact proposal collection before installation:

```sh
python alias_probe.py source-review --proposal batch1/proposal.json \
  --proposal batch2/proposal.json --targets targets.json \
  --source-root /baseline/source --owner-helper /engine/workflow/scala_owners.py \
  --output /new/source_review
```

The whole Scala file must contain only a package, supported imports, and one
object of explicitly typed, single-expression forwarding methods. Every
definition must match proposal metadata. The canonical owner, source line,
signature/defaults, receiver, argument mapping and JVM descriptor are checked.
Initializers, transformations, extra helpers, ambiguous imports, overloads and
unsupported syntax stop for review. The `review.json` verdict certifies this
limited source grammar, not compilation, all-input behavior, or hint accuracy.

After installation and source-bound builds, prepare and run:

```sh
python alias_probe.py prepare --proposal bundle/proposal.json \
  --targets targets.json --source-root /baseline/source \
  --owner-helper /engine/workflow/scala_owners.py \
  --backends backends.json --backend-receipts backend_receipts.json \
  --trace-runner /assets/TraceRunner.java --output /new/alias_plan
python alias_probe.py run --plan /new/alias_plan/plan.json --output /new/alias_runs
```

Use `PYTHONDONTWRITEBYTECODE=1`. Each output must be new and outside source
worktrees. Existing output is never overwritten or silently resumed. A failed
run retains evidence and requires a new output after review.

The runner compiles one standalone Scala program per alias, then executes it
in separate canonical and alias JVMs. Both sides receive fresh, identical
development examples. Observations include selected values and structures,
stream bytes/positions, receiver mutations, identity relationships and exception
classes. At least one example must succeed; matching failures alone cannot pass.
Exception messages/stacks and every possible input are not compared. Omitted
default arguments are checked statically but not invoked by the examples.

Each alias-side trace must contain the exact alias and canonical JVM method
events. The canonical-side trace cannot satisfy this requirement. Class-loading
logs must locate both methods' owners in the source-bound overlay. Traces
aggregate examples within each JVM; they do not prove per-example or causal use.
JVMs have normal host permissions, so this helper is not an OS sandbox.

`receipt.json` has status `verified_alias_behavior` only after all actual aliases
pass in both arms and all bound input/build/controller files revalidate. It
links requests, compiled classes, compiler/JVM logs, separate raw traces and
class-loading logs, comparisons, source certificates, build identities and
dependency hashes. `failure.json` preserves completed units and the failure.
Atomic exclusive receipts avoid overwriting earlier evidence.

The offline test module uses synthetic source/evidence and mocks process launch;
it never calls a provider, compiler, library or held-out checker. Any separate
synthetic-wrapper runtime smoke is helper validation, not treatment validation.
