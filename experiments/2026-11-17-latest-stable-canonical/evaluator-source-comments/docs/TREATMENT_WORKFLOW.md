# Current treatment workflow

Use one batch proposal path for aliases and one native exception-message path
for embedded fix hints. Main CLI help shows these current routes. Earlier
commands remain callable by their original names for existing scripts and saved
artifacts; their own `--help` explains the migration.

## Alias proposals

`preview-library` → `propose-library` → `bundle-proposals` → `install-treatments`

Use `preview-library --api NAME` to select a small scope. One batch uses the same
workflow as a library-wide proposal. Previews save the API/source evidence;
proposals retain the model request and response; bundling selects the complete
treatment files; installation records source versions. A proposal or installation
alone does not establish wrapper correctness. Validate the library builds and
independent controls before freezing the evaluation.

The model proposal format may still record legacy JSON hint candidates. The
default `bundle-proposals` installs only README/alias artifacts and retains those
candidates in `legacy_hint_selection.json`, with the source bindings and omitted
count. Raw batch proposals remain unchanged. JSON candidates do not constitute
native exception guidance.

For an explicitly selected schema 1 study, `bundle-proposals
--include-legacy-hints` includes the earlier JSON hint artifact. This requires a
new output directory; an existing bundle is never rewritten or reinterpreted.

## Native exception hints

`preview-native-hints` → `propose-native-hints` → `validate-native-hints`
→ `install-native-hints`

1. `preview-native-hints --manifest MANIFEST --output DIRECTORY` collects pinned
   Original R0 **development** failures, diagnoses their API/source locations,
   and records unsupported cases. This is the existing evidence intake under a
   name that identifies its current use. It does not make a model call.
2. `propose-native-hints --preview PREVIEW --model-config CONFIG --output DIRECTORY`
   asks the author model for source-supported guidance. Each supplied case must
   receive a proposal or be explicitly marked unsupported. The command prepares
   candidate changes to supported existing exception messages.
3. `validate-native-hints --proposal PROPOSAL --validation-plan PLAN --output DIRECTORY`
   executes the triggering misuse, corrected program, valid use, and unrelated
   error against both source versions. The library-specific validation plan is
   still required.
4. Install the complete README/alias bundle with `install-treatments` **before**
   adding native source edits. Then run `install-native-hints --validation
   VALIDATION --target CHECKOUT` separately on the Error Hints only and Combined
   targets. Each target must match the validated source baseline and contain no
   earlier JSON hint treatment.
5. Review and commit the native source edits and their validation receipt, rebuild
   each condition library, then freeze the source/build identities. The native
   installer intentionally leaves edits uncommitted.

For a later README/alias change, create a new study/version with fresh worktrees
and repeat the applicable native validation and installation. Do not rerun the
old bundle installation over branches containing native edits. The bundle
installer checks the expected commits and refuses unexpected changes; a bundle
is a complete replacement of its owned artifacts, not a source-merge operation.

`prepare-native-hints --source-root ROOT --spec SPEC --output DIRECTORY` is the
deterministic entry point for an already prepared edit specification. It does not
replace the required paired validation or claim LLM authorship.

During evaluation, the compiled library emits the hint in its normal diagnostic.
The audience receives it in repair feedback. This workflow does not retrieve
hint JSON or source comments into the audience prompt. Guidance remains fixed
throughout a frozen evaluation.

Use [the current condition configuration](../configs/condition_evaluation.example.yaml)
for a new five-condition study. It selects native messages (schema 3) and two
program repair rounds. Fill in and validate the library-specific inputs before
`freeze-conditions` and `run-conditions`. The draft schema in `prepare-study`
metadata is preparation bookkeeping, not the evaluation protocol.

## Compatibility commands

| Earlier command | Current route for a new study |
| --- | --- |
| `preview-source-hints` | `preview-native-hints`; both use the same development evidence intake |
| `propose-source-hints` | `propose-native-hints`; creates a different artifact, not a converted comment proposal |
| `validate-source-hints` | `validate-native-hints`, with a native proposal and validation plan |
| `install-source-hints` | `install-native-hints`, with its native validation receipt |
| `preview-improvements` | `preview-library`, with a selected API scope if needed |
| `propose-improvements` | `propose-library`, then `bundle-proposals` |
| `show-fix-hints` | Inspect native diagnostics in saved execution feedback; no retrieval step |

Existing JSON-hint, comment-hint, and single-preview commands still interpret
their original inputs. Do not feed an old proposal or receipt to a new command
by renaming it. Existing frozen studies retain their original protocol and
artifact identities; the help cleanup does not migrate or rerun them.
