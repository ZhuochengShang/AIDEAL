"""Give Python evaluation snippets local copies of preloaded input bindings.

Fixtures live outside the nested test function in some scaffolds. Capturing
those bindings as default parameters makes read-then-reassign statements work
without rewriting candidate code or changing the fixture objects themselves.
"""
from __future__ import annotations

import ast
import copy
import io
import tokenize


def _region_lines(text, region):
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.strip() == region[0].strip()]
    ends = [i for i, line in enumerate(lines) if line.strip() == region[1].strip()]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        return None
    return lines, starts[0], ends[0]


def _scope_names(statements):
    """Names local to this scope, excluding bodies of nested scopes."""
    names, declarations = set(), set()

    def visit(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            return
        if isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            declarations.update(node.names)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or (alias.name.split('.')[0] if isinstance(node, ast.Import)
                                         else alias.name) for alias in node.names if alias.name != '*')
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in statements:
        visit(statement)
    return names - declarations, declarations


def _argument_names(args):
    return {arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs,
                               *((args.vararg,) if args.vararg else ()),
                               *((args.kwarg,) if args.kwarg else ()))}


def bind_python_scaffold_inputs(program: str, scaffold: str | None = None,
                               region=('# TODO API_TEST_START', '# TODO API_TEST_END')) -> str:
    """Bind visible scaffold inputs as keyword defaults on the test function.

    Use after snippet insertion, or on a saved wrapped program for isolated
    rescoring. If no scaffold is supplied, blank the marked snippet first so
    candidate assignments cannot become trusted scaffold bindings. Only values
    definitely bound by preceding unconditional scaffold statements are captured.
    Explicit global/nonlocal declarations and existing arguments are preserved.
    Invalid candidate syntax is left to the ordinary execution checker.
    """
    if len(region) != 2:
        return program
    located = _region_lines(program, region)
    if located is None:
        return program
    lines, start, end = located
    if scaffold is None:
        blank = list(lines)
        indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
        blank[start + 1:end] = [indent + 'pass\n'] + ['\n'] * max(0, end - start - 2)
        scaffold = ''.join(blank)
    source_region = _region_lines(scaffold, region)
    if source_region is None:
        return program
    try:
        base, actual = ast.parse(scaffold), ast.parse(program)
    except SyntaxError:
        return program
    marker = source_region[1] + 1
    scopes = sorted((node for node in ast.walk(base)
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and node.lineno < marker <= node.end_lineno), key=lambda node: node.lineno)
    if not scopes:
        return program
    # Class namespaces are not enclosing lexical scopes for method bodies.
    if any(isinstance(node, ast.ClassDef) and node.lineno < marker <= node.end_lineno
           for node in ast.walk(base)):
        return program
    available = set()
    for outer, inner in zip([base, *scopes[:-1]], scopes):
        if not isinstance(outer, ast.Module):
            local, _ = _scope_names(outer.body)
            available.difference_update(local)
            available.update(_argument_names(outer.args))
        for statement in outer.body:
            if statement.end_lineno >= inner.lineno:
                break
            if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.Import, ast.ImportFrom,
                                      ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if isinstance(statement, ast.AnnAssign) and statement.value is None:
                    continue
                available.update(_scope_names([statement])[0])
            elif isinstance(statement, ast.Delete):
                available.difference_update(_scope_names([statement])[0])
    candidates = [node for node in ast.walk(actual)
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and node.lineno < start + 1 <= node.end_lineno]
    target = max(candidates, key=lambda node: node.lineno) if candidates else None
    if target is None:
        return program
    _, declarations = _scope_names(target.body)
    captures = sorted(available - _argument_names(target.args) - declarations)
    if not captures:
        return program
    args = copy.deepcopy(target.args)
    args.kwonlyargs.extend(ast.arg(arg=name) for name in captures)
    args.kw_defaults.extend(ast.Name(id=name, ctx=ast.Load()) for name in captures)
    # Replace only the function header, retaining every candidate statement,
    # comment, fixture, call site, and line after the header.
    offset = sum(len(line) for line in lines[:target.lineno - 1]) + target.col_offset
    tail = program[offset:]
    depth = 0
    for token in tokenize.generate_tokens(io.StringIO(tail).readline):
        if token.type == tokenize.OP:
            depth += token.string in ('(', '[', '{')
            depth -= token.string in (')', ']', '}')
            if token.string == ':' and depth == 0:
                stop = sum(len(line) for line in tail.splitlines(keepends=True)[:token.end[0] - 1]) + token.end[1]
                prefix = 'async ' if isinstance(target, ast.AsyncFunctionDef) else ''
                returns = ' -> ' + ast.unparse(target.returns) if target.returns else ''
                header = f'{prefix}def {target.name}({ast.unparse(args)}){returns}:'
                return program[:offset] + header + tail[stop:]
    return program
