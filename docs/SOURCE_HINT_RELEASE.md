# Source-embedded guidance release

This September 24, 2026 software update extends the previously published AIDEAL
controller. It contains reusable implementation, tests, a development prompt and
configuration examples. Private fixtures, expected answers, model payloads,
credentials, runtime binaries and machine-specific ledgers are excluded.

## Behavior

1. `preview-source-hints` collects attributable failures from a pinned Original
   development R0 manifest, excluding held-out cases and incomplete generations.
2. `propose-source-hints` records a development model request containing relevant
   source, signature, candidate program and diagnostic evidence. A proposal alone
   cannot certify a correction.
3. `validate-source-hints` replays the failing misuse, proposed correction, valid
   use and unrelated failure. All required controls must pass.
4. `install-source-hints` checks validation/source identities and creates new
   branches with identical annotation-only changes. Historical branches remain
   unchanged. The new descendants remove their legacy JSON hint file.
5. A fresh schema-2 freeze binds source notes, execution adapters and task inputs.
  The evaluator attributes the actual failing function and requirement, then
  retrieves matching source guidance after failure.

The validated installer enforces development replay evidence. The generic
evaluation freeze checks source identities and backend controls, but does not
itself authenticate that development-validation receipt. A study that claims
validated hints must use the validated installation path before freezing.

The repair request preserves the complete latest candidate, exact matched
signature, diagnostic and corrective guidance while removing repeated context.
Initial and repair output limits remain separate configuration values. Incomplete,
refused and empty responses retain their requests and usage but are not compiled
or counted as verified API failures. Invocation and provider audit records remain
bound to the attempt evidence.

Slash-comment annotations reject compiler Unicode escape sequences both when
created and when read back. This prevents Java's pre-comment escape processing
from turning guidance text into executable source while passing a raw-text
annotation-removal comparison.

Optional measured-condition selection supports a two-arm follow-up while still
validating all five backends. A separate source-function inventory supports helper
attribution without changing the task bank or score denominator. Existing
selective README designs, complete execution logs and fixed study budget ledgers
remain available.

## Scope of validation

| Check | Result |
|---|---|
| Full integrated Python suite | 482 tests passed |
| Final affected suites after comment-escape and dependency-binding changes | 97 tests passed |
| Navigation interface checks | 6 tests passed |
| Publication inventory | All 276 bound files verified |

The full suite ran before the final comment-escape guard. The 97-test follow-up
checked the final source-hint parser, proposal/validation/installation path,
native provider bridge, recorded pipeline and generation evidence. These counts
overlap and must not be added as distinct tests.

The offline test suites exercise local synthetic adapters and temporary libraries.
They check source-comment parsing, attribution, complete versus incomplete output,
tamper detection, Git branch installation, repeated-run behavior and matched
condition controls. They do not establish improvements on the held-out RDPro bank.

Validation commands from the repository root:

```sh
python -m unittest discover -s tests -v
node --test tests/test_code_map_ui.cjs
python -m workflow verify
```

The release integrity manifest identifies this new publication snapshot. Earlier
commits preserve earlier manifests; no frozen experiment receipt is rewritten.

## Experiment status

The RDPro development R0 run contains eight completed cases. Four failures support
source attribution and four remain unresolved. The four-case hint-authoring
preview has not been sent. No real source annotations have yet been installed for
this new study, and the planned 192-trial Error Hints only/Combined comparison has
not started. Its planned protocol uses R0 and up to two program-repair rounds.

The previous completed five-condition comparison used external JSON hints and a
different repair allowance. Its outcomes must remain separate from the new study.
