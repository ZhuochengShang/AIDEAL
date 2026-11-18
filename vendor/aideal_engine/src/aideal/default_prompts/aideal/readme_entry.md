SYSTEM:
You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

{project_context}

USER:
Document the {language} function `{api_name}` of {project_name}.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{api_facts}
```

Project context distilled from the original README (grounding — may say none exists):
{original_readme_context}

Retrieved snippets from the project's test files (source evidence, not execution
validation; may be empty). Do not claim that these snippets passed unless the
provided context includes execution evidence:
```{language}
{test_examples}
```

Retrieved original documentation for API identity `{api_name}`. This may include
surrounding prose or state that no matching example exists; do not assume it
contains a callable example merely because it was retrieved:
```text
{original_examples}
```

The canonical API identity is a registry label, not executable syntax. Never
copy its language prefix into a call. The API facts separately provide the
actual display_name, qualified_name, public_access_paths or preferred_public_path
when known. An access path alone does not establish whether a method is static,
an instance member, a property, or an implicit extension.

Ground the call form in the supplied evidence:
1. Preserve the receiver, public access path and argument order of a relevant
   source/test/documentation example that matches the selected declaration.
2. Resolve conflicting examples against the selected declaration and owner.
   Do not assume an instance form is more portable or convert it to a static call.
3. If no matching call example exists, infer only what the API facts establish.
   Explicitly label inferred examples as unverified and state unresolved receiver
   or construction requirements instead of inventing them.
4. Preserve parameterless/property access when shown. Do not add parentheses or
   drop qualifiers merely to make the call look like a generic function.

Fill in the template below. Replace every TODO. Keep the Signature block and the
pre-filled Parameters types and Output type exactly as given; add the meaning of
each parameter, the Input (data/formats/preconditions), and what the Output
represents. Tailor Goal, examples, and Common Failure Modes to the target users
and use cases above, honoring the project constraints.

If the context states PRECONDITIONS or compatibility rules (conditions under which
the call is valid, or inputs that must be made compatible or converted/prepared
first with another operation) or TYPE-PARAMETER selection rules (which generic /
type argument to use for a given input type), you MUST state them explicitly under
Input and Common Failure Modes. These rules are what make generated code correct —
do not drop them. Output ONLY the filled template, nothing else.

{template}
