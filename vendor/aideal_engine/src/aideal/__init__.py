"""AIDEAL: AI Documentation Evaluation and Alias Library.

AIDEAL is the BACKEND: a generic, codebase-agnostic toolkit that tests and
improves how LLM-ready a codebase is. Applications (like GRAIL) sit on top of
it — they supply the codebase, the runner commands, and the demo UI.

Pipeline (driven by `python -m aideal.cli`):
  readme         find or create LLM_readme.md
  form           structure of every API entry
  comprehension  readme unit test — given ONLY the doc, write correct code
  completeness   all public functions covered?
  puzzle         integration tasks + fix loop (notes_to_self injected on retry)

Workspace files (all paths set in one YAML config):
  LLM_readme.md           LLM-facing API documentation under test
  notes_to_self.md        distilled memory: issue {{}} fix {{}} pattern {{}}
  integration_tasks.yaml  NL goals / benchmark tasks to solve
  aliases/aliases.json    proposed AND added aliases, per model
  logs/error_log.jsonl    structured accumulated errors (run_id, root_cause, fix)
"""

__version__ = "0.2.0"
