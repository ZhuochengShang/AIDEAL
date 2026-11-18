#!/usr/bin/env python3
"""Build a local, searchable function map without importing or running AIDEAL.

Names and explicit imports are resolved statically. Dynamic dispatch remains
listed as unresolved; the map is a reading aid, not an execution trace.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path


SCOPES = (('workflow', 'workflow'), ('vendor/aideal_engine/src/aideal', 'aideal'),
          ('studies/historical', 'studies.historical'), ('studies/sedonadb', 'studies.sedonadb'))


def source_files(root):
    """Current Python controller, engine and bundled study adapters only."""
    for directory, package in SCOPES:
        for path in sorted((root / directory).glob('*.py')):
            # This local credential scratch file is not application source.
            # Exclude it before reading so offline guides never copy its contents.
            if directory == 'workflow' and path.name == 'quickrun.py':
                continue
            module = package if path.stem == '__init__' else package + '.' + path.stem
            yield path, module


def imported_module(module, node, is_package):
    if not node.level:
        return node.module or ''
    parts = module.split('.') if is_package else module.split('.')[:-1]
    prefix = parts[:len(parts) - node.level + 1]
    return '.'.join(prefix + ([node.module] if node.module else []))


class Definitions(ast.NodeVisitor):
    """Collect lexical definitions and imports, including deferred imports."""
    def __init__(self, module, path, source):
        self.module, self.path, self.source = module, path, source
        self.scope = ()
        self.nodes = {}
        self.imports = defaultdict(dict)
        self.bound = defaultdict(set)
        self.classes = set()

    def definition(self, node, kind):
        scope = self.scope + (node.name,)
        key = '.'.join(scope)
        self.nodes[key] = (node, kind, self.scope)
        if kind == 'class':
            self.classes.add(scope)
        before, self.scope = self.scope, scope
        if kind != 'class':
            args = node.args
            self.bound[scope].update(a.arg for a in args.posonlyargs + args.args + args.kwonlyargs)
            self.bound[scope].update(a.arg for a in (args.vararg, args.kwarg) if a)
        for statement in node.body:
            self.visit(statement)
        self.scope = before

    def visit_FunctionDef(self, node):
        self.definition(node, 'method' if self.scope in self.classes else 'function')

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.definition(node, 'class')

    def visit_ImportFrom(self, node):
        module = imported_module(self.module, node, self.path.name == '__init__.py')
        for item in node.names:
            if item.name != '*':
                self.imports[self.scope][item.asname or item.name] = module + '.' + item.name

    def visit_Import(self, node):
        for item in node.names:
            self.imports[self.scope][item.asname or item.name.split('.')[0]] = (
                item.name if item.asname else item.name.split('.')[0])

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.bound[self.scope].add(node.id)


class DirectCalls(ast.NodeVisitor):
    """A nested function's calls belong to that function, not its parent."""
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        pass

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = dotted(node.value)
        return left + '.' + node.attr if left else None
    return None


def resolve_export(target, modules, seen=None):
    """Follow explicit facade re-exports to the implementation definition."""
    seen = set() if seen is None else seen
    if target in seen:
        return None
    seen.add(target)
    for module in sorted(modules, key=len, reverse=True):
        if not target.startswith(module + '.'):
            continue
        name = target[len(module) + 1:]
        parsed = modules[module]
        if name in parsed.nodes:
            return module + ':' + name
        first, _, rest = name.partition('.')
        alias = parsed.imports[()].get(first)
        if alias:
            return resolve_export(alias + ('.' + rest if rest else ''), modules, seen)
    return None


def resolve_call(name, parsed, scope, modules):
    first, _, rest = name.partition('.')
    if first in ('self', 'cls'):
        for size in range(len(scope), 0, -1):
            if scope[:size] in parsed.classes:
                return resolve_export(parsed.module + '.' + '.'.join(scope[:size]) + '.' + rest, modules)
    for size in range(len(scope), -1, -1):
        current = scope[:size]
        candidate = '.'.join(current + (name,))
        if candidate in parsed.nodes:
            return parsed.module + ':' + candidate
        if first in parsed.bound[current]:
            return None  # A parameter/local binding makes this a dynamic call.
        alias = parsed.imports[current].get(first)
        if alias:
            return resolve_export(alias + ('.' + rest if rest else ''), modules)
    return resolve_export(name, modules)


def build_map(root):
    modules = {}
    for path, module in source_files(root):
        source = path.read_text(encoding='utf-8')
        parsed = Definitions(module, path, source)
        parsed.visit(ast.parse(source))
        modules[module] = parsed
    records = []
    module_records = []
    for module, parsed in sorted(modules.items()):
        module_records.append({'name': module, 'path': parsed.path.relative_to(root).as_posix(),
                               'lines': len(parsed.source.splitlines()),
                               'sha256': hashlib.sha256(parsed.source.encode()).hexdigest()})
        for name, (node, kind, parent) in parsed.nodes.items():
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            visitor = DirectCalls()
            if kind != 'class':
                for statement in node.body:
                    visitor.visit(statement)
            calls, unresolved, prompts = set(), set(), set()
            for call in visitor.calls:
                expression = dotted(call.func)
                target = resolve_call(expression, parsed, parent + (node.name,), modules) if expression else None
                if target:
                    calls.add(target)
                else:
                    unresolved.add(ast.unparse(call.func))
                if target == 'aideal.prompts:load' and len(call.args) > 1:
                    value = call.args[1]
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        prompts.add(value.value)
            signature = node.name + ('(' + ast.unparse(node.args) + ')' if kind != 'class' else '')
            records.append({'id': module + ':' + name, 'module': module, 'name': name, 'kind': kind,
                            'path': parsed.path.relative_to(root).as_posix(), 'line': start,
                            'end_line': node.end_lineno, 'signature': signature,
                            'summary': (ast.get_docstring(node) or '').split('\n\n')[0],
                            'calls': sorted(calls), 'called_by': [],
                            'unresolved_calls': sorted(unresolved), 'prompts': sorted(prompts),
                            'source': '\n'.join(parsed.source.splitlines()[start - 1:node.end_lineno])})
    by_id = {record['id']: record for record in records}
    aliases = {}
    for module, parsed in modules.items():
        for name, imported in parsed.imports[()].items():
            target = resolve_export(imported, modules)
            if target and module + ':' + name not in by_id:
                aliases[module + ':' + name] = target
    for record in records:
        for target in record['calls']:
            by_id[target]['called_by'].append(record['id'])
    for record in records:
        record['called_by'].sort()
        record['aliases'] = sorted(alias for alias, target in aliases.items() if target == record['id'])
    pipeline = root / 'docs/pipeline_reference.json'
    data = {'schema': 1, 'scope': [directory for directory, _ in SCOPES],
            'limitations': 'Static Python names/imports only; unresolved calls include dynamic methods, callbacks and external libraries. A link does not prove execution. Tests and the separate rdpro_section_codegen demo are excluded.',
            'modules': module_records, 'functions': sorted(records, key=lambda row: row['id']),
            'aliases': dict(sorted(aliases.items())),
            'pipeline': json.loads(pipeline.read_text()) if pipeline.exists() else {}}
    data['review_paths'] = review_paths(data)
    return data


def review_paths(data):
    """Validate curated entry points and put their direct dependencies underneath.

    These are reading paths, not a claim of runtime reachability or unused code.
    Keep every definition in the full reference, including unresolved callbacks.
    """
    records = {row['id']: row for row in data['functions']}
    stages = {row['id'] for row in data['pipeline'].get('stages', [])}
    paths = []
    seen = set()
    for path in data['pipeline'].get('review_paths', []):
        if path['id'] in seen:
            raise ValueError(f"Duplicate review path: {path['id']}")
        seen.add(path['id'])
        entries = []
        for entry in path['entries']:
            primary = entry['function']
            canonical = data['aliases'].get(primary, primary)
            if canonical is not None and canonical not in records:
                raise ValueError(f'Unknown review entry point: {primary}')
            if canonical is None and not entry['status'].startswith('not_implemented'):
                raise ValueError('An implemented entry needs a function')
            if not set(entry['stage_ids']) <= stages:
                raise ValueError(f"Unknown stages in entry: {entry['id']}")
            if entry['id'] in seen:
                raise ValueError(f"Duplicate review entry: {entry['id']}")
            seen.add(entry['id'])
            helpers = records[canonical]['calls'] if canonical else []
            entries.append({**entry, 'function': canonical,
                            'helper_ids': [h for h in helpers if h != canonical]})
        if not set(path['extra_stage_ids']) <= stages:
            raise ValueError(f"Unknown extra stages in path: {path['id']}")
        paths.append({**path, 'entries': entries})
    return paths


def write_markdown(data, output, source_root):
    """A portable source index plus complete internal caller/callee links."""
    lines = ['# Function index', '',
             'Generated by `scripts/build_code_map.py`; use [the interactive map](CODE_MAP.html) for search and source previews.',
             '', data['limitations'], '']
    rows = data['functions']
    anchors = {r['id']: f'function-{index}' for index, r in enumerate(rows)}

    for path in data.get('review_paths', []):
        lines += [f"## Start here: {path['title']}", '', path['summary'], '']
        for entry in path['entries']:
            target = entry['function']
            label = f"[{entry['title']}](#{anchors[target]})" if target else entry['title']
            lines += [f"- {label}: {entry['summary']}"]
        lines.append('')

    def links(ids):
        return ', '.join(f"[{item}](#{anchors[item]})" for item in ids) or 'None resolved'

    lines += ['## Complete reference', '', 'Helpers and supporting APIs follow below.', '']
    for module in data['modules']:
        lines += [f"## {module['name']}", '', f"{module['lines']} lines · `{module['path']}`", '']
        for row in rows:
            if row['module'] != module['name']:
                continue
            # Absolute links are for Codex; the HTML also embeds the exact source.
            source = (source_root / row['path']).as_posix()
            lines += [f'<a id="{anchors[row["id"]]}"></a>',
                      f"### [{row['name']}]({source}:{row['line']})", '',
                      row['summary'] or f"{row['kind'].capitalize()} in `{row['module']}`.", '',
                      f"Calls: {links(row['calls'])}", '', f"Called by: {links(row['called_by'])}", '']
            if row['prompts']:
                lines += ['Prompt keys: ' + ', '.join(f'`{p}`' for p in row['prompts']), '']
    output.write_text('\n'.join(lines), encoding='utf-8')


def generate(root, source_root=None):
    root = Path(root).resolve()
    data = build_map(root)
    data['source_root'] = str(Path(source_root or root).resolve())
    docs = root / 'docs'
    docs.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    (docs / 'function_map.json').write_text(payload + '\n', encoding='utf-8')
    template = (root / 'templates/code_map.html').read_text(encoding='utf-8')
    safe = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    # Embed the authored assets so the generated navigator remains one offline file.
    for marker, name in [('__CODE_MAP_STYLE__', 'code_map.css'), ('__CODE_MAP_SCRIPT__', 'code_map.js')]:
        if marker in template:
            template = template.replace(marker, (root / 'templates' / name).read_text(encoding='utf-8'))
    (docs / 'CODE_MAP.html').write_text(template.replace('__CODE_MAP_DATA__', safe), encoding='utf-8')
    write_markdown(data, docs / 'FUNCTION_INDEX.md', Path(data['source_root']))
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-root', type=Path, help='Source links destination when generating from a staging copy')
    args = parser.parse_args()
    data = generate(args.root, args.source_root)
    print(f"Indexed {len(data['functions'])} definitions in {len(data['modules'])} modules; no project code executed.")


if __name__ == '__main__':
    main()
