SYSTEM:
{project_context}

Using the role and domain above, identify which functions form the COMMONLY-USED,
user-facing API of this codebase — the operations a typical user actually calls in
real workflows — as opposed to internal helpers, lifecycle / iterator / serializer
plumbing, framework callbacks, builders, or rarely-used accessors. Judge each
function by what it does (its domain meaning and signature), not by its name
length or superficial wording. Make no assumption about the problem domain beyond
what the role and signatures imply.

USER:
Candidate functions (name: signature):
{api_list}

Return ONLY a JSON array of the names that are commonly-used, user-facing
operations — nothing else. No prose, no explanation, no code fences. Example
format: ["functionA", "functionB"].
