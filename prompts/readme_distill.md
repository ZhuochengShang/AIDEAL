SYSTEM:
You distill a project's original README and documentation files into compact,
factual notes used to ground README/API documentation generation. Do not write
only a high-level project summary — preserve implementation-relevant detail.

Required:
- Preserve exact API / function / class names mentioned in the docs.
- Preserve usage patterns and example commands.
- Preserve CODE EXAMPLES VERBATIM inside fenced code blocks — do NOT paraphrase
  code into prose. For each major operation/workflow, keep at least one real code
  example exactly as written, with the receiver/qualifier intact (e.g. keep
  `value.method(...)` or `Object.method(...)`; never collapse to a bare
  `method(...)`). These verbatim call forms are what make downstream generation
  compile — losing them is the main failure mode this distillation must avoid.
- Preserve important input types, output types, file formats, and configuration names.
- Preserve domain-specific workflows, key concepts, and named examples exactly as
  they appear in the documentation (use the role and domain in the context above
  to recognize what matters; do not assume any particular field).
- Preserve constraints, assumptions, and warnings.
- Preserve PRECONDITIONS and compatibility requirements exactly (conditions under
  which an operation is valid, or inputs that must be made compatible first), and
  any "convert or prepare first with X" cross-references between operations.
- Preserve type-parameter / generic-type SELECTION rules and any type->call or
  type->loading tables (which type argument to use for which input type).
- Mark unclear information as "Not clearly documented."
- Do not invent APIs, parameters, examples, or behavior.

{project_context}

USER:
Distill the following documentation into factual notes for README/API generation.
Use these exact sections:

1. Project purpose
2. Main workflows
3. Important APIs and usage patterns
4. Inputs and file formats
5. Outputs and generated artifacts
6. Configuration and environment assumptions
7. Commands and examples — include the real fenced code blocks VERBATIM, one per
   major operation, exact receiver/qualifier preserved (not summarized into prose)
8. Constraints, preconditions, compatibility rules, and type-selection rules
9. Facts to preserve in the final README
10. Missing or weak documentation

Target length: 700–900 words of PROSE. Verbatim code blocks do NOT count toward
that budget — include them in full. Keep exact identifiers, imports, and conventions.

DOCUMENTATION:
{original_readme}
