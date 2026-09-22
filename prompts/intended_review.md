SYSTEM:
{project_context}

You adjudicate whether each symbol is intended for USER-FACING documentation,
using ONLY the compact evidence provided (qualified name, owner, signature,
doc, static score/signals, and available receiver types) and the role/domain
above. Include genuine user-facing operations that can be exercised with a
meaningful lightweight correctness check. Exclude internal helpers, abstract
hooks, lifecycle/iterator/serializer plumbing, obscure format internals, and
operations whose receiver/input cannot be obtained from the configured test
fixtures. Do not request or assume source code. Never merge different owners
that happen to share a bare method name.

USER:
Records (one per symbol):
{records}

Rate every dimension from 0 (none/poor) to 3 (strong). Use the same rubric in
every batch:
- user_facing: a researcher would intentionally call it as a supported API
- fixture_runnable: its receiver and inputs can be built from the listed fixtures
- oracle_strength: a lightweight test can verify meaningful behavior, not merely no-crash
- domain_relevance: it represents a substantive operation in this project's domain

Also assign a concise, reusable `capability_family` describing the operation,
not its class or spelling. Use lower-case hierarchical labels such as
`selection/query`, `trajectory/io`, `geometry/distance`, or
`analysis/dimensionality-reduction`. APIs with equivalent user intent should
receive the same family even when their names or owners differ; behaviorally
different variants should receive different families. Avoid one unique family
per API.

Set decision=include only when user_facing and fixture_runnable are each at
least 2 and a meaningful correctness check is plausible. The numeric ratings
are used by a deterministic cross-batch ranker; do not rank only within this
batch.

Return ONLY a JSON array, one object per input name:
[{{"name":"...","decision":"include"|"exclude","capability_family":"category/operation","ratings":{{"user_facing":0,"fixture_runnable":0,"oracle_strength":0,"domain_relevance":0}},"reason":"<short>"}}]
