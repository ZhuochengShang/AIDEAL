# RDPro pilot harness and offline tests

These source and test files are byte-identical copies from the completed GPT-5.3-Codex study. They make the actual checker and preparation logic reviewable. This directory is **not a standalone full repeat**: private cases, fixture values, reference programs, expected answers, runtime manifests and compiled dependencies are omitted.

| File | Role |
|---|---|
| [build_backends.py](build_backends.py) | Verify installed treatment branches; compile the three measured RDPro classes and new Scala aliases; bind source, binary and class-origin evidence. |
| [execute.py](execute.py) | Verify backend identity; compile a generated function body; compare numerical outputs; check exact qualified target descriptors; publish evidence receipts. |
| [Harness.java](Harness.java) | Invoke the generated `solve(Array[Double]): Array[Double]` implementation under the study's Java restrictions. |
| [TraceRunner.java](TraceRunner.java) | Observe the configured canonical target methods through JDI breakpoints. |
| [ClassOrigin.java](ClassOrigin.java) | Check which archive supplies each compiled class. |
| [public_helpers/StudySupport.scala](public_helpers/StudySupport.scala) | Public input and output helpers supplied in the task contract; not the private reference solutions. |
| [prepare_conditions.py](prepare_conditions.py) | Construct the five-condition protocol from installed treatments and real backend identities. |
| [test_adapter.py](test_adapter.py) | Four offline tests for oracle/target separation, malformed outputs, class origins and compilation-failure receipts. |
| [development/test_codex_preparation.py](development/test_codex_preparation.py) | Twelve offline tests for build/preparation contracts, artifact routing and tamper detection. |

## Run the 16 offline checks

Use Python 3.10 or newer, Git, and the repository's base dependency, PyYAML (`python -m pip install -e .`). From the **repository root**:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$PWD:$PWD/studies/rdpro/2026-09-21-gpt-5.3-codex-five-conditions/harness" \
python -m unittest discover \
  -s studies/rdpro/2026-09-21-gpt-5.3-codex-five-conditions/harness -p test_adapter.py -v

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$PWD:$PWD/studies/rdpro/2026-09-21-gpt-5.3-codex-five-conditions/harness" \
python -m unittest discover \
  -s studies/rdpro/2026-09-21-gpt-5.3-codex-five-conditions/harness/development -p test_codex_preparation.py -v
```

The preparation test retains its original import statement; `PYTHONPATH` supplies the relocated harness and the repository's `workflow` package. These tests use synthetic data and temporary files. Compiler/JVM operations are mocked. Two preparation tests create temporary local Git repositories to check branch and source tampering. No provider, JVM, RDPro function or network request runs.

## What a full repeat additionally requires

- The selected RDPro baseline and all five installed treatment worktrees, with matching `attachment.json` and treatment application records.
- Java 17 (`java` and `javac`), the pinned Scala 2.12.18 compiler/runtime and Spark 3.5.1 dependency set, plus RDPro/Beast artifacts. The measured runtime used 271 explicitly listed dependency jars, including Beast/Raptor 0.10.1. The builder does not download dependencies.
- A local `runtime.json` beside `build_backends.py` containing actual `java`, `javac` and `jars` paths. Each resulting backend has its own runtime/build identity and overlay archives.
- The private eight-case bank with its three fixtures per case and control programs; the original documentation, selected generated README and its provenance; and the study records expected by `prepare_conditions.py`, including `refactor_pair_v2.yaml` as the inherited bank/documentation pointer.
- The repository's controller and OpenAI adapter, authenticated provider access, and a preserved shared budget ledger for new paid generation. Offline tests require none of these provider credentials.

Relocating files changes path-bound identities. A new execution needs a new configuration, builds and freeze, followed by all 120 controls before the 40 audience units; copying old hashes does not recreate the original evidence. The harness measures an isolated three-class overlay, not a full distributed Spark deployment. Method reachability can be transitive and does not establish causal API use. Java restrictions are defense in depth, not an operating-system sandbox.
