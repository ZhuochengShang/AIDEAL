#!/usr/bin/env python3
"""Run one native audience-written assertion snippet against real SedonaDB."""
import ast
from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import sys
import textwrap


def validate_snippet(text):
    start = "# TODO API_TEST_START"
    end = "# TODO API_TEST_END"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("Expected exactly one audience snippet region")
    body = text.split(start, 1)[1].split(end, 1)[0]
    tree = ast.parse(textwrap.dedent(body))
    if not any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
        raise ValueError("Audience snippet must contain a Python assert statement")


if __name__ == "__main__":
    path = Path(sys.argv[1]).resolve()
    validate_snippet(path.read_text())
    class Tee(io.StringIO):
        def write(self, text):
            sys.__stdout__.write(text)
            return super().write(text)

    output = Tee()
    with redirect_stdout(output):
        runpy.run_path(str(path), run_name="__main__")
    target = path.parent.name.removeprefix("run_")
    if not any(line.startswith(f"__CHECK__ {target} ") for line in output.getvalue().splitlines()):
        raise AssertionError("Missing target-specific structured correctness witness")

