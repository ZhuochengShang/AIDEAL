SYSTEM:
You design verifiable benchmark tasks for coding agents.

{project_context}

USER:
Available documented APIs:
{api_list}

Write {n} benchmark tasks grounded in the project's use cases above.
Rules:
- each task must be solvable using ONLY the listed APIs (3-5 APIs per task)
- the goal is one natural-language sentence a target user would actually ask
- the result must be verifiable from program output (a count, a CSV, a file)
- do not reuse the same API combination twice

Output YAML only, exactly this shape:

tasks:
  - id: short_snake_case_id
    language: {language}
    goal: "..."
    apis: [api1, api2, api3]
