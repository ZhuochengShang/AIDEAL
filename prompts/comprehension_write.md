SYSTEM:
You write {language} code. You may use ONLY the documentation provided —
no other knowledge of the library.
If available input variables are listed, use those variable names rather than
inventing file paths.
Output only code.

{project_context}

USER:
Documentation:
{api_body}

Available input path variables, if useful:
{available_inputs}

Write a minimal snippet that uses `{api_name}` correctly per the documentation.
Verify the result with a LIGHTWEIGHT action only — e.g. `.count()`, `.first()`,
or printing one sampled value. Do NOT write large outputs to disk or call other
heavyweight operations unless `{api_name}` itself is the output/writer API; keep
the snippet focused on `{api_name}` so the test isolates that one call.
