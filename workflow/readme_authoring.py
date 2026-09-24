"""Offline, qualified README authoring preparation; no model or target execution."""
from dataclasses import replace
import glob
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

from .preparation import _engine_config_module
from .readme_spans import inspect_sections, validate_spans

REPORT_MARKER = '[[AIDEAL_FROZEN_DEEP_DIVE_RESULT]]'


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path.read_bytes())}


def engine_imports():
    directory = Path(__file__).resolve().parents[1] / 'vendor/aideal_engine/src'
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    import aideal.readme_generation as generation
    if Path(generation.__file__).resolve() != directory / 'aideal/readme_generation.py':
        raise ValueError('A different native engine is already imported')
    return generation


def repository_files(repository, revision, cfg):
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-C', str(repository), *args])
    if git('rev-parse', 'HEAD').decode().strip() != revision:
        raise ValueError('Repository HEAD differs from the pinned manifest revision')
    tracked = set(git('ls-tree', '-r', '--name-only', '-z', revision).decode().split('\0'))
    groups = []
    for patterns in (cfg.source_globs, cfg.test_globs):
        selected = set()
        for pattern in patterns:
            for name in glob.glob(str(cfg.root / pattern), recursive=True):
                path = Path(name)
                if not path.is_file():
                    continue
                if path.is_symlink() or not path.resolve().is_relative_to(repository):
                    raise ValueError('Source/test input escapes pinned repository')
                rel = path.resolve().relative_to(repository).as_posix()
                if rel not in tracked:
                    raise ValueError('Untracked source/test input: ' + rel)
                if path.read_bytes() != git('show', revision + ':' + rel):
                    raise ValueError('Source/test bytes differ from pinned revision: ' + rel)
                selected.add(path.resolve())
        groups.append(sorted(selected))
    if not groups[0]:
        raise ValueError('No pinned source files selected')
    return groups


def validate_definitions(manifest, discovered, repository):
    seen = set()
    rows = {}
    for entry in manifest['entries']:
        if not all(isinstance(entry.get(k), str) and entry[k].strip() for k in ('id', 'heading')):
            raise ValueError('Entry id and heading must be nonempty strings')
        defs = entry.get('definitions')
        if not isinstance(defs, list) or not defs:
            raise ValueError('Each entry needs explicit definition descriptors')
        matched = []
        for definition in defs:
            if not all(isinstance(definition.get(k), str) and definition[k] for k in ('path', 'name', 'receiver', 'signature')):
                raise ValueError('Definition needs path, name, receiver and exact signature')
            path = PurePosixPath(definition['path'])
            if path.is_absolute() or '..' in path.parts or type(definition.get('line')) is not int:
                raise ValueError('Invalid definition path/line')
            matches = [d for d in discovered if d['visibility'] == 'public' and
                       (d['file'], d['line'], d['name'], d['signature']) ==
                       (str(path), definition['line'], definition['name'], definition['signature'])]
            if len(matches) != 1:
                raise ValueError('Unknown/ambiguous exact definition: ' + entry['id'])
            key = (str(path), definition['line'])
            if key in seen:
                raise ValueError('Definition assigned to multiple entries')
            seen.add(key)
            row = matches[0]
            if path.suffix == '.scala':
                from .scala_owners import owner_at_line
                owner = owner_at_line((repository / path).read_text(), definition['line'], definition['name'])
                if (definition['receiver'], definition.get('owner_kind')) != (owner['receiver'], owner['owner_kind']):
                    raise ValueError('Receiver/kind disagrees with enclosing Scala declaration')
                if definition.get('owner_path', owner['owner_path']) != owner['owner_path']:
                    raise ValueError('Nested owner path disagrees with the declaration')
                qualified = definition.get('qualified_receiver')
                if qualified and not (qualified == owner['owner_path'] or qualified.endswith('.' + owner['owner_path'])):
                    raise ValueError('Qualified receiver disagrees with lexical owner path')
                row = {**row, 'lexical_owner_path': owner['owner_path']}
            elif row.get('owner'):
                if not definition['receiver'].endswith(row['owner']):
                    raise ValueError('Receiver disagrees with discovered owner')
            else:
                receiver = definition['receiver'].split('.')[-1]
                text = (repository / path).read_text()
                if not re.search(r'\b(?:class|object|trait|interface|struct|enum|impl)\s+' + re.escape(receiver) + r'\b', text):
                    raise ValueError('Declared receiver not found in definition file')
            matched.append({**row, **{k: definition[k] for k in ('receiver', 'owner_kind', 'qualified_receiver') if k in definition}})
        if len({(d['file'], d['receiver'], d.get('owner_kind'), d.get('lexical_owner_path'), d['name']) for d in matched}) != 1:
            raise ValueError('A family cannot merge different receivers or method names')
        receiver, name = matched[0]['receiver'], matched[0]['name']
        if entry['id'] == name or '.' not in entry['id']:
            raise ValueError('Bare-name identities are not accepted')
        rows[entry['id']] = matched
    return rows


def development_diagnostics(path, ids):
    if path is None:
        return {}, []
    path = Path(path).resolve()
    grouped = {key: [] for key in ids}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        metadata = row.get('metadata') or {}
        if not isinstance(metadata, dict):
            raise ValueError('Diagnostic metadata must be an object')
        if row.get('split') != 'development' or row.get('function_id') not in grouped:
            raise ValueError('Diagnostics require split=development and exact manifest function_id')
        if any(str(obj.get(k, '')).lower() in ('held_out', 'held-out', 'evaluation', 'test')
               for obj in (row, metadata) for k in ('split', 'phase', 'scope')):
            raise ValueError('Held-out diagnostics are forbidden')
        allowed = {k: row[k] for k in ('function_id', 'split', 'error', 'code', 'root_cause') if k in row}
        if any(not isinstance(v, str) for v in allowed.values()):
            raise ValueError('Diagnostic fields must be text')
        grouped[row['function_id']].append(allowed)
    return grouped, [binding(path)]


def _source_context(repository, definitions):
    blocks = []
    for d in definitions:
        lines = (repository / d['file']).read_text().splitlines()
        lo, hi = max(0, d['line'] - 31), min(len(lines), d['line'] + 160)
        blocks.append(f"// {d['receiver']}.{d['name']} — {d['file']}:{d['line']}\n" +
                      '\n'.join(f'{i + 1}: {lines[i]}' for i in range(lo, hi)))
    return '\n\n'.join(blocks)[:14000]


def prepare_readme_session(config, manifest, base_readme, context, output, diagnostics=None):
    """Save exact offline requests. Full=one entry call; refresh=deep-dive+rewrite.

    The caller supplies a reconciled, complete base skeleton for full authoring.
    Refresh preserves every non-selected byte. Neither mode imports legacy
    journals or generates/reads README-derived preamble/io_hints caches.
    """
    inputs = [Path(p).resolve() for p in (config, manifest, base_readme, context)]
    config_path, manifest_path, base_path, context_path = inputs
    value = json.loads(manifest_path.read_text())
    if value.get('schema_version') != 1 or value.get('mode') not in ('full', 'refresh'):
        raise ValueError('Expected README manifest schema 1 with full or refresh mode')
    if value.get('cache_policy') != 'isolated_no_legacy_cache':
        raise ValueError('Only isolated_no_legacy_cache is supported')
    repository = Path(value['repository']).resolve()
    revision = value['revision']
    if not re.fullmatch('[a-f0-9]{40}', revision):
        raise ValueError('Manifest requires a full pinned Git commit')
    output = Path(output).resolve()
    if output.exists() or output == repository or output.is_relative_to(repository) or any(p.is_relative_to(output) for p in inputs):
        raise ValueError('Use a new output outside source and all input files')
    base = base_path.read_bytes()
    validate_spans(base, value['entries'])
    ids = [e['id'] for e in value['entries']]
    selected = value['selected_ids']
    if not selected or len(set(selected)) != len(selected) or set(selected) - set(ids):
        raise ValueError('Selected identities are empty, duplicated or unknown')
    if value['mode'] == 'full' and set(selected) != set(ids):
        raise ValueError('Full authoring must select the complete reconciled manifest')
    generation = engine_imports()
    engine = _engine_config_module()
    cfg = engine.load_config(config_path)
    if ((cfg.comprehension or {}).get('execute') or {}).get('probe_on_missing'):
        raise ValueError('Execution-first probes are not supported by offline README sessions')
    from aideal.profile import profile_path, require_profile
    from aideal.prompts import DEFAULT_PROMPTS, load as load_prompt, prompts_dir
    require_profile(cfg)
    source_files, test_files = repository_files(repository, revision, cfg)
    local = replace(cfg, root=repository, source_globs=[glob.escape(str(p)) for p in source_files],
                    test_globs=[glob.escape(str(p)) for p in test_files])
    definitions = validate_definitions(value, generation.public_api_details(local), repository)
    from .native_provider_bridge import guarded_native_contract
    phase_roles = {'entry': 'author'} if value['mode'] == 'full' else {'deep_dive': 'reviewer', 'rewrite': 'fixer'}
    providers = {role: guarded_native_contract(cfg.model_for_role(role)) for role in set(phase_roles.values())}
    if len(providers) > 1:
        common_budget = {(p['budget_ledger'], digest(p['budget_identity'])) for p in providers.values()}
        if len(common_budget) != 1:
            raise ValueError('All refresh phases must share one immutable study budget')
        if len({p['stage'] for p in providers.values()}) != len(providers) or len({p['evidence_dir'] for p in providers.values()}) != len(providers):
            raise ValueError('Deep-dive and rewrite need distinct stage/evidence namespaces')
    diagnostics_by_id, diagnostic_bindings = development_diagnostics(diagnostics, ids)
    test_index = generation.api_test_examples(local)
    originals = generation._original_readme_snippets(cfg, {r['name'] for ds in definitions.values() for r in ds})
    note = context_path.read_text()
    requests = []
    name_families = {}
    for key, recs in definitions.items():
        name_families.setdefault(recs[0]['name'], set()).add(key)
    for entry in value['entries']:
        if entry['id'] not in selected:
            continue
        recs = definitions[entry['id']]
        primary = generation._subsume_overloads(recs, generation._dedup_deprioritize(cfg))[0][0]
        examples = test_index.get(primary['name'], [])
        if len(name_families[primary['name']]) > 1:
            # A bare-name match cannot assign a variable-receiver example to
            # this family. Keep only explicit receiver-qualified call forms.
            qualified_call = re.compile(r'(?<![\w.])' + re.escape(primary['receiver']) +
                                        r'\s*\.\s*' + re.escape(primary['name']) + r'\s*[\[(]')
            examples = [e for e in examples if qualified_call.search(e['code'])]
        tests = '\n\n'.join(f"// from {e['file']} — test({e['test']})\n{e['code']}" for e in examples) or '(no existing test found for this API)'
        facts = {'name': primary['name'], 'qualified_id': entry['id'], 'receiver': primary['receiver'],
                 'signature': primary['signature'], 'params': primary['params'], 'returns': primary['returns'],
                 'source_doc': primary['description'], 'overloads': [r['signature'] for r in recs if r is not primary],
                 'definitions': recs, 'source_context': _source_context(repository, recs),
                 'example_evidence_limit': 'Mined by method name; check exact receiver against these pinned facts. Not executed by preparation.'}
        start, end = entry['span']['start_byte'], entry['span']['end_byte']
        body = base[start:end].decode()
        if value['mode'] == 'full':
            system, user = load_prompt(cfg, 'aideal/readme_entry', api_name=entry['heading'],
                api_facts=json.dumps(facts, ensure_ascii=False, indent=2), original_readme_context=note,
                original_examples='\n\n'.join(originals.get(primary['name'], [])) or '(no original example)',
                test_examples=tests, template=generation._entry_skeleton(entry['heading'], cfg.language.lower(), recs))
            phases = {'entry': {'system': system, 'prompt': user}}
        else:
            system, user = load_prompt(cfg, 'aideal/deep_dive', api_name=entry['heading'],
                source_window=json.dumps(facts, ensure_ascii=False, indent=2),
                other_sites=', '.join(f"{r['file']}:{r['line']}" for r in recs),
                type_context='No independent type expansion performed; use the pinned receiver/source windows and state remaining uncertainty.',
                call_sites=tests, entry_body=body,
                failure_history=json.dumps(diagnostics_by_id.get(entry['id'], []), ensure_ascii=False))
            rs, ru = load_prompt(cfg, 'aideal/docfix_rewrite', api_name=entry['heading'],
                diagnosis='Use the bounded deep-dive report below; no separate diagnosis call was made.',
                deep_dive_report=REPORT_MARKER, source_window=json.dumps(facts, ensure_ascii=False, indent=2),
                entry_body=body, required_sections=', '.join(cfg.required_sections))
            if (rs + ru).count(REPORT_MARKER) != 1:
                raise ValueError('Rewrite template must contain exactly one deep-dive result placeholder')
            phases = {'deep_dive': {'system': system, 'prompt': user}, 'rewrite': {'system': rs, 'prompt': ru}}
        requests.append({'id': entry['id'], 'heading': entry['heading'], 'phase_roles': phase_roles, 'phases': phases})
    template_names = ['readme_entry'] if value['mode'] == 'full' else ['deep_dive', 'docfix_rewrite']
    template_paths = []
    for name in template_names:
        path = prompts_dir(cfg) / f'aideal/{name}.md'
        template_paths.append(path if path.exists() else DEFAULT_PROMPTS / f'aideal/{name}.md')
    module_paths = list((Path(__file__).resolve().parents[1] / 'vendor/aideal_engine/src/aideal').glob('*.py'))
    module_paths += [Path(__file__).resolve(), Path(__file__).with_name('readme_spans.py'), Path(__file__).with_name('readme_session.py'), Path(__file__).with_name('readme_receipts.py'), Path(__file__).with_name('scala_owners.py')]
    bound = [binding(p) for p in sorted(set(inputs + source_files + test_files + cfg.original_readme_files +
                                          [profile_path(cfg)] + template_paths + module_paths))]
    payload = {'schema_version': 1, 'mode': value['mode'], 'manifest': value, 'base_sha256': digest(base),
               'inputs': bound + diagnostic_bindings, 'effective_config': cfg.raw, 'config_path': str(config_path),
               'provider_contracts': providers, 'requests': requests, 'requests_sha256': digest(requests),
               'cache_policy': value['cache_policy'], 'repair_policy': 'one_fresh_deep_dive_then_one_rewrite_no_execution' if value['mode'] == 'refresh' else 'author_only',
               'validation_status': 'not_executed', 'model_calls': 0}
    payload['identity_sha256'] = digest(payload)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'base.md').write_bytes(base)
    (output / 'session.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    for i, request in enumerate(requests):
        directory = output / f'entry_{i:04d}'
        directory.mkdir()
        (directory / 'prepared.json').write_text(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
    return {'session': str(output / 'session.json'), 'identity_sha256': payload['identity_sha256'],
            'entries': len(requests), 'planned_calls': len(requests) * (2 if value['mode'] == 'refresh' else 1), 'model_calls': 0}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('inspect'); p.add_argument('--base', required=True)
    p = sub.add_parser('prepare')
    for name in ('config', 'manifest', 'base', 'context', 'output'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--diagnostics')
    args = parser.parse_args()
    value = inspect_sections(Path(args.base).read_bytes()) if args.action == 'inspect' else prepare_readme_session(
        args.config, args.manifest, args.base, args.context, args.output, args.diagnostics)
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()
