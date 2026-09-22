"""Strict source review and independent paired development probes for Scala aliases.

Preparation is read-only apart from a new output directory. `run` compiles and
executes the prepared standalone examples, never a task bank or private oracle.
"""
import argparse
import importlib.util
from pathlib import Path
import re
import sys

from alias_development_cases import program
from alias_probe_evidence import bind, core_ref, digest, git, load, relative_path, save, verified, verify_runtime
from alias_forwarders import (IMPORTABLE, Parser, ReviewRequired, canonical_signature,
                              certify, parse_module, split_descriptor, type_descriptor)

HERE = Path(__file__).resolve().parent
MODULES = ('alias_probe.py', 'alias_forwarders.py', 'alias_development_cases.py',
           'alias_probe_evidence.py', 'alias_probe_execution.py')


def owner_module(path):
    ref = bind(path); name = '_alias_probe_owner_' + ref['sha256'][:16]
    spec = importlib.util.spec_from_file_location(name, ref['path'])
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_targets(path, root, owner_helper):
    """Tie method metadata to the exact current baseline declaration and owner."""
    root = Path(root).resolve(strict=True); result = {}
    owner = owner_module(owner_helper)
    for target in load(path)['targets']:
        source_path = relative_path(root, target['source']); text = source_path.read_text()
        lexical = owner.owner_at_line(text, target['line'], target['method'])
        package = re.findall(r'^package\s+([\w.]+)\s*$', text, re.M)
        expected_kind = 'object' if target['jvm_owner'].endswith('$') else 'class'
        if (len(package) != 1 or lexical['owner_kind'] != expected_kind
                or package[0] + '.' + lexical['owner_path'] + '.' + target['method'] != target['api']
                or target['jvm_owner'].rstrip('$') != target['api'].rsplit('.', 1)[0]):
            raise ReviewRequired('Canonical source ownership differs: ' + target['api'])
        signature = canonical_signature(text, target['line'], target['method'])
        module = {'package':package[0], 'imports': sorted(IMPORTABLE)}
        args, result_type = split_descriptor(target['descriptor'])
        if [type_descriptor(p['type'], module) for p in signature['parameters']] != args:
            raise ReviewRequired('Canonical source and JVM parameter types differ')
        if signature['returns'] and type_descriptor(signature['returns'], module) != result_type:
            raise ReviewRequired('Canonical source and JVM return types differ')
        identity = target['source'] + ':' + str(target['line']) + ':' + target['method']
        if identity in result: raise ReviewRequired('Duplicate canonical function identity')
        result[identity] = {'target': target, 'signature': signature, 'source': bind(source_path)}
    return result


def inspect_proposal(path, targets, root):
    """No code is executed. Every definition must have exact metadata and one route."""
    proposal_ref = bind(path); proposal = load(verified(proposal_ref)); revision = proposal['baseline_revision']
    if not re.fullmatch('[0-9a-f]{40}', revision) or git(root, 'rev-parse', 'HEAD') != revision:
        raise ReviewRequired('Original checkout is not the proposal baseline')
    for row in targets.values():
        target = row['target']; data = verified(row['source']).read_bytes()
        if git(root, 'show', revision + ':' + target['source'], binary=True) != data:
            raise ReviewRequired('Canonical source differs from the pinned Git blob')
    artifacts = proposal.get('artifacts', {})
    aliases = [r for key, r in artifacts.items() if key == 'alias' or re.fullmatch(r'alias_\d+', key)]
    metadata = proposal.get('aliases', [])
    if not isinstance(metadata, list): raise ReviewRequired('Alias metadata must be a list')
    names = [r['name'] for r in metadata]
    if len(names) != len(set(names)): raise ReviewRequired('Duplicate alias metadata name')
    modules, defs, destinations, owners = [], {}, set(), set()
    baseline_files = set(git(root, 'ls-tree', '-r', '--name-only', revision).splitlines())
    for ref in aliases:
        source = verified(core_ref(ref)); target_path = ref['target']
        relative_path(root, target_path)
        if target_path in destinations or target_path in baseline_files or not target_path.endswith('.scala'):
            raise ReviewRequired('Alias must add one unique new Scala source file')
        destinations.add(target_path); module = parse_module(source.read_text())
        owner = module['package']+'.'+module['owner']
        if owner in owners: raise ReviewRequired('Multiple source files define one alias object')
        owners.add(owner)
        # A package path is a useful source-layout check, not a Scala guarantee.
        if '/' + module['package'].replace('.', '/') + '/' not in '/' + target_path:
            raise ReviewRequired('Alias package disagrees with destination source layout')
        modules.append(module)
        for method in module['methods']:
            if method['name'] in defs: raise ReviewRequired('Duplicate alias definition across files')
            defs[method['name']] = (module, method, ref)
    if set(defs) != set(names): raise ReviewRequired('Every Scala definition must match exactly one alias metadata row')
    rows = []
    for metadata_row in metadata:
        identity = metadata_row['target_function']
        if identity not in targets: raise ReviewRequired('Alias points outside the declared canonical target scope')
        canonical = targets[identity]; module, method, ref = defs[metadata_row['name']]
        sig = canonical['signature']
        cert = certify(module, method, canonical['target'], sig['parameters'], sig['parentheses'])
        cert.update(function_id=identity, source=core_ref(ref), installed_target=ref['target'],
                    canonical_source=canonical['source'], canonical_signature=sig,
                    status='supported_thin_forwarding_syntax', behavior_validated=False)
        # This also requires a known independent development recipe, before any
        # installation/execution. It does not run or validate that recipe.
        text, count = program(cert)
        rows.append({'certificate':cert, 'program':text, 'example_count':count})
    verified(proposal_ref)
    return {'proposal':proposal_ref, 'aliases':aliases, 'rows':rows, 'baseline_revision':revision}


def new_output(path, roots):
    path = Path(path).resolve()
    for root in roots:
        root = Path(root).resolve()
        if path == root or root in path.parents:
            raise ValueError('Keep development output outside every source worktree')
    path.mkdir(parents=True, exist_ok=False)
    return path


def controller_refs(owner_helper):
    return [*(bind(HERE / name) for name in MODULES), bind(owner_helper)]


def source_review(proposals, targets_path, root, owner_helper, output):
    targets = source_targets(targets_path, root, owner_helper)
    checks = [inspect_proposal(path, targets, root) for path in proposals]
    all_names = [row['certificate']['alias_name'] for check in checks for row in check['rows']]
    if not all_names or len(all_names) != len(set(all_names)):
        raise ReviewRequired('Need at least one alias and unique names across proposals')
    owners = {}
    for check in checks:
        for row in check['rows']:
            cert = row['certificate']; previous = owners.setdefault(cert['alias_owner'],cert['source'])
            if previous != cert['source']: raise ReviewRequired('Separate proposals collide on one alias object')
    out = new_output(output, [root]); refs = []
    for i, check in enumerate(checks, 1):
        refs.append(save(out / ('source_check_%04d.json' % i), {
            'status':'verified_forwarding_source', 'proposal':check['proposal'],
            'certificates':[row['certificate'] for row in check['rows']],
            'behavior_validated':False, 'hint_correctness_validated':False}))
    covered = sorted({row['certificate']['canonical_api'] for check in checks for row in check['rows']})
    value = {'status':'validated_proposal_sources', 'held_out_bank_used_for_development':False,
             'proposal_bindings':[c['proposal'] for c in checks], 'source_checks':refs,
             'targets':bind(targets_path), 'controllers':controller_refs(owner_helper),
             'alias_target_coverage':covered,
             'untreated_targets':sorted({r['target']['api'] for r in targets.values()}-set(covered)),
             'scope':'Strict source/signature/forwarding syntax only; independent runtime probes still required; hint correctness not established.'}
    save(out / 'review.json', value)
    return value


def prepare(proposal, targets_path, root, owner_helper, backends_path, receipts_path, trace_runner, output):
    targets = source_targets(targets_path, root, owner_helper)
    check = inspect_proposal(proposal, targets, root)
    if not check['rows']: raise ReviewRequired('At least one supported alias is required')
    backends, receipts = load(backends_path), load(receipts_path)
    runtimes = {}
    for arm in ('alias_only','combined'):
        runtime, build = verify_runtime(backends[arm], receipts[arm], check['aliases'], trace_runner)
        expected = {r['certificate']['alias_owner']+'$' for r in check['rows']}
        if not expected <= set(build['alias_classes']):
            raise ReviewRequired('Compiled build does not contain every alias object')
        compiled_sources = {r['path']:r for r in build['inputs']['source']}
        for canonical in targets.values():
            current = bind(relative_path(build['worktree'],canonical['target']['source']))
            if (any(current[k] != canonical['source'][k] for k in ('sha256','bytes'))
                    or compiled_sources.get(current['path']) != current):
                raise ReviewRequired('Compiled canonical implementation differs from source baseline')
        runtimes[arm] = bind(backends[arm]['runtime'])
    out = new_output(output, [root, *(r['worktree'] for r in receipts.values())])
    entries = []
    for index, row in enumerate(check['rows'], 1):
        unit = out / ('alias_%04d' % index); unit.mkdir()
        cert = row['certificate']; cert_ref = save(unit/'certificate.json', cert)
        (unit/'AliasDevelopmentProbe.scala').write_text(row['program'])
        events = [cert['canonical_event'], cert['alias_event']]
        policy = []
        for event in events:
            call, desc = event.split('(',1); owner, method = call.rsplit('.',1)
            policy.append(owner+'\t'+method+'\t('+desc+'\n')
        (unit/'trace_policy.tsv').write_text(''.join(policy))
        entries.append({'api':cert['canonical_api'], 'alias_name':cert['alias_name'],
            'canonical_event':cert['canonical_event'], 'alias_event':cert['alias_event'],
            'certificate':cert_ref, 'program':bind(unit/'AliasDevelopmentProbe.scala'),
            'trace_policy':bind(unit/'trace_policy.tsv'), 'example_count':row['example_count']})
    covered = sorted({row['api'] for row in entries})
    value = {'schema_version':1, 'status':'prepared_not_executed',
        'protocol':'independent_development_alias_probe_v1', 'proposal':check['proposal'],
        'targets':bind(targets_path), 'baseline_root':str(Path(root).resolve()),
        'baseline_revision':check['baseline_revision'], 'backends':bind(backends_path),
        'backend_receipts':bind(receipts_path), 'runtimes':runtimes, 'aliases':check['aliases'],
        'trace_runner':bind(trace_runner), 'controllers':controller_refs(owner_helper),
        'canonical_sources':list({r['source']['path']:r['source'] for r in targets.values()}.values()),
        'held_out_bank_used_for_development':False, 'entries':entries,
        'alias_target_coverage':covered,
        'untreated_targets':sorted({r['target']['api'] for r in targets.values()}-set(covered)),
        'limits':'Paired observations on independently authored finite examples; no all-input equivalence or causal proof; normal host JVM permissions.'}
    save(out/'plan.json', value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    for name in ('source-review','prepare'):
        p = sub.add_parser(name)
        p.add_argument('--proposal', required=True, action='append' if name == 'source-review' else 'store')
        for field in ('targets','source-root','owner-helper','output'): p.add_argument('--'+field, required=True)
        if name == 'prepare':
            for field in ('backends','backend-receipts','trace-runner'): p.add_argument('--'+field, required=True)
    p = sub.add_parser('run'); p.add_argument('--plan', required=True); p.add_argument('--output', required=True)
    args = vars(parser.parse_args()); command = args.pop('command')
    try:
        if command == 'run':
            from alias_probe_execution import run
            value = run(args['plan'], args['output'])
        elif command == 'source-review':
            value = source_review(args['proposal'], args['targets'], args['source_root'], args['owner_helper'], args['output'])
        else:
            value = prepare(args['proposal'], args['targets'], args['source_root'], args['owner_helper'],
                args['backends'], args['backend_receipts'], args['trace_runner'], args['output'])
    except (ReviewRequired, ValueError) as error:
        print(__import__('json').dumps({'status':'requires_review', 'reason':str(error)})); return 2
    print(__import__('json').dumps({'status':value['status'], 'output':str(Path(args['output']).resolve())})); return 0


if __name__ == '__main__':
    raise SystemExit(main())
