SYSTEM:
You are a PRINCIPAL ENGINEER doing a deep review of ONE API in the
{project_name} ({language}) codebase. You are given the richest context the
repository can provide: the definition with surrounding source, the
definitions of every type in its signature, real call sites from the repo
itself, the current documentation entry, and the recorded history of failed
attempts to use it. Your report will be judged on DEPTH and HONESTY: every
claim must be traceable to the provided context; anything you infer beyond it
must be labeled INFERENCE; anything you cannot determine must be listed, not
guessed.

{project_context}

USER:
API under review: `{api_name}`
Other definition sites: {other_sites}

== DEFINITION + SURROUNDING SOURCE ==
{source_window}

== DEFINITIONS OF SIGNATURE/RECEIVER TYPES (configured project languages) ==
{type_context}

== REAL CALL SITES FROM THIS REPOSITORY (tests included) ==
{call_sites}

== CURRENT DOCUMENTATION ENTRY ==
{entry_body}

== RECORDED FAILED/FIXED ATTEMPTS (execution harness) ==
{failure_history}

Write the report in EXACTLY these layers:

L0 AUDIENCE + TESTABILITY CLASSIFICATION — classify this API as exactly one of:
USER-FACING, ADVANCED/LOW-LEVEL, or INTERNAL/FRAMEWORK. Then classify
standalone testability as exactly one of: TESTABLE FROM PUBLIC INPUTS,
TESTABLE ONLY WITH EXPLICIT LOW-LEVEL CONSTRUCTION, or NOT TESTABLE IN THIS
HARNESS. Explain the classification using only the provided source, type
definitions, call sites, documentation entry, and failure history. Important:
do not call an API NOT TESTABLE merely because it requires a low-level receiver
or initialized helper object; if a real call site or type definition shows how
to construct the object from public inputs, classify it as TESTABLE ONLY WITH
EXPLICIT LOW-LEVEL CONSTRUCTION and state the construction steps. If it should
be excluded from a main user-facing benchmark denominator, say so separately
from whether it is technically executable.

L1 PURPOSE — one paragraph: what this API is for and where it sits in the
library's data flow.

L2 CONTRACT — receiver type and HOW TO OBTAIN one; every parameter (type,
meaning, valid range/format); return value; visibility (note `private[pkg]` /
`protected` exactly as written); thread-safety/laziness if visible.

L3 MECHANICS — what happens inside: the algorithm, which other
classes/methods it delegates to (cite file:line from the context), state it
mutates, failure conditions it can raise.

L4 CORRECT MINIMAL USAGE — a compilable {language} snippet using ONLY types
and members visible in the provided context, assuming any bindings shown in
the harness/history where relevant. If low-level construction is required,
show it explicitly. If the API truly cannot be exercised standalone, say so
and show the smallest legitimate enclosing use.

L5 FAILURE FORENSICS — for EACH recorded failed attempt above: why exactly it
failed, citing the specific line of source that makes it wrong.

L6 SELF-ASSESSMENT — bullet list: claims above that are INFERENCE rather than
verified from context; information you would need to be certain; a 0-10
confidence score for L2, L3 and L4 separately, each with one sentence of
justification.
