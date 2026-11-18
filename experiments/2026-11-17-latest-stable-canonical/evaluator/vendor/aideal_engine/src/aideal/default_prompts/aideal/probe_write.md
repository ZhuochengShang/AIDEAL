SYSTEM:
You write {language} code that will be spliced into a runnable test harness to
PROBE one function whose documentation does not exist yet.
{execution_context}

You are given ONLY the function's SIGNATURE — there is no prose documentation,
and you must not invent any. Your job is to find a call that actually compiles
and runs, so that its real behavior can be documented afterward.

Pick the input variable(s) whose type matches the signature's parameters. Preserve
the most likely receiver. Do not redeclare provided variables or write wrapper
boilerplate unless the execution context explicitly asks for it. Output ONLY the
body statements. Output only code, no markdown fences.

{project_context}

USER:
Probe the {language} function `{api_name}`. You have only its signature:

- signature: {signature}
- parameters: {params}
- returns: {returns}

Available input path variables already in scope (choose the matching one(s) by type):
{available_inputs}

{known_failures}

Write minimal body statements that INVOKE `{api_name}` using the type-matched
input(s) above, then VERIFY the call actually did something — not just that it
compiled (some frameworks are lazy; a wrong element/type can read garbage without
throwing).
End with a CORRECTNESS CHECK:
- force the result to materialize and compute a small witness — a count, a size, or
  a sampled element;
- assert the witness is non-degenerate with `require(...)`, e.g.
  `require(n > 0, "empty result for {api_name}")`;
- then print it as a structured line exactly like:
  `println("__CHECK__ {api_name} " + n)`.
If `{api_name}` is itself a writer/output API, write to `output_dir`, then `require`
the output exists / is non-empty and print the same `__CHECK__` line.
Keep the body focused on `{api_name}` so the run isolates that one call.
{io_hints}
{exec_hints}
