"""Bridge recorded native R0 attempts into the existing hint development path.

Native markers are not independent oracles. Only an exact runtime frame and a
matching existing literal exception qualify a failure for hint authoring; paired
validation still supplies the independent oracle. All other attempts stay in the
intake ledger. This module reads evidence; it never imports or executes a library.
"""
import json
import hashlib
from pathlib import Path
import re

from .ablation import bind, digest, load, seal_record, verify_artifact
from .execution import atomic_json

PROTOCOL = 'native_original_r0/v1'


def _bound(ref, root=None):
    """Read only unchanged, explicitly bound files in the permitted run root."""
    if not isinstance(ref, dict) or not verify_artifact(ref):
        raise ValueError('Missing or changed native R0 evidence')
    path = Path(ref['path']).resolve(strict=True)
    if root is not None and not path.is_relative_to(root):
        raise ValueError('Native evidence escaped its run root')
    return path


def _inputs(manifest):
    """Verify run, source, documentation and exact defining-API provenance."""
    # The development CLI also runs from an uninstalled checkout.
    import sys
    engine = str(Path(__file__).resolve().parents[1] / "vendor/aideal_engine/src")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    from aideal.config import load_config
    from aideal.api_discovery import public_api_details
    from aideal.api_registry import target_key
    from aideal.doc_check_provenance import _sha256_files
    from aideal.original_documentation import original_document_paths
    from .source_hint_development import _baseline, _scope
    from .treatment_versions import _run as git

    _scope(manifest)
    source = _baseline(manifest['source_root'], manifest['baseline_revision'])
    native = manifest['native_run']
    root = Path(native['root']).resolve(strict=True)
    refs = [native[key] for key in ('result', 'launch', 'config', 'api_manifest')]
    paths = [_bound(ref, root) for ref in refs]
    result, launch, cfg = load(paths[0]), load(paths[1]), load_config(paths[2])
    api_manifest = load(paths[3])
    # Match the evaluator's manifest reader: a frozen bank is a list or an
    # object whose `apis` field is that ordered list. Keep the complete bound
    # artifact above; the run fingerprint below still hashes only these IDs.
    names = api_manifest.get('apis') if isinstance(api_manifest, dict) else api_manifest
    if (not isinstance(names, list)
            or any(not isinstance(name, str) or not name for name in names)
            or len(set(names)) != len(names)):
        raise ValueError('Native API manifest must contain distinct exact IDs')
    run = result.get('run', {})
    components = run.get('fingerprint_components', {})
    if (result.get('check') != 'comprehension' or result.get('mode') != 'execute'
            or result.get('doc_source') != 'original' or launch.get('documentation') != 'original'
            or components.get('doc_source') != 'original'
            or run.get('experiment_fingerprint') != digest(components)
            or Path(launch.get('source', '')).resolve() != source
            or launch.get('mode') == 'trace-mock'
            or run.get('manifest_sha256') != components.get('manifest_sha256')
            or run.get('manifest_sha256') != hashlib.sha256('\n'.join(names).encode()).hexdigest()
            or components.get('execute_config') != cfg.comprehension.get('execute', {})):
        raise ValueError('Native run lacks matching Original/source/config provenance')
    documents = manifest['original_documents']
    actual = [bind(path) for path in original_document_paths(cfg)]
    if (not isinstance(documents, list) or not documents
            or {digest(ref) for ref in documents} != {digest(ref) for ref in actual}
            or not all(verify_artifact(ref) for ref in documents)
            or components.get('original_document_files') != _sha256_files(
                [Path(ref['path']) for ref in actual], cfg.root)):
        raise ValueError('Native run original documentation changed or differs from the manifest')
    refs += documents
    codebase = cfg.raw.get('codebase', {})
    if codebase.get('identity_mode') != 'qualified':
        raise ValueError('Native evidence bridge requires exact qualified API identities')
    inventory_path = (cfg.root / codebase['api_inventory']).resolve()
    inventory = load(inventory_path)
    if (bind(inventory_path)['sha256'] != codebase.get('api_inventory_sha256')
            or inventory.get('source_commit') != manifest['baseline_revision']):
        raise ValueError('Native inventory does not bind the pristine source revision')
    refs.append(bind(inventory_path))
    records = {target_key(row): row for row in public_api_details(cfg)}
    if set(names) - set(records) or set(result.get('metrics', {})) - set(names):
        raise ValueError('Native results contain an API outside the frozen bank')
    apis, public_paths = {}, {}
    tracked = set(git(source, 'ls-files').splitlines())
    if inventory.get('kind') != 'registered_sql':
        for api, row in records.items():
            file = (cfg.root / row.get('defining_file', row['file'])).resolve()
            if not file.is_relative_to(source):
                raise ValueError('Native defining source escaped the pinned repository')
            relative = file.relative_to(source).as_posix()
            ref = bind(file)
            if relative not in tracked or ref['sha256'] != row.get('source_sha256', row.get('file_sha256')):
                raise ValueError('Native defining source changed or is not tracked')
            name = row['qualified_name'] if file.suffix == '.py' else row['name']
            apis[api] = f"{relative}:{row['line']}:{name}"
            public_paths[api] = row.get('public_access_paths', [])
            refs.append(ref)
    supplied = manifest.get('api_function_ids', {})
    if supplied and supplied != apis:
        raise ValueError('Supplied source-location map differs from the frozen inventory')
    # A resumed result can reference an earlier invocation's run ID. The
    # append-only checkpoint binds those exact attempts to this fingerprint and
    # also retains earlier provider failures replaced in the final metrics.
    checkpoint = Path(run['checkpoint']).resolve(strict=True)
    if not checkpoint.is_relative_to(root / 'execution'):
        raise ValueError('Native checkpoint escaped execution evidence')
    refs.append(bind(checkpoint))
    attempts = {}
    historical = []
    for line in checkpoint.read_text().splitlines():
        row = json.loads(line)
        api = row.get('name')
        if row.get('experiment_fingerprint') != run['experiment_fingerprint']:
            historical.append({'api_id': api, 'disposition': 'historical_fingerprint_excluded'})
            continue
        if api not in names or not isinstance(row.get('attempt_evidence'), list):
            raise ValueError('Native checkpoint target differs from its bank')
        hashes = row.get('rendered_prompt_sha256')
        if not isinstance(hashes, list) or not hashes:
            raise ValueError('Native checkpoint lacks exact rendered prompt hashes')
        for directory in row['attempt_evidence']:
            key = (api, str(Path(directory).resolve(strict=True)))
            if key in attempts and attempts[key] != hashes:
                raise ValueError('Native checkpoint gives conflicting prompt evidence')
            attempts[key] = hashes
    for api, metric in result.get('metrics', {}).items():
        for directory in metric.get('attempt_evidence', []):
            if (api, str(Path(directory).resolve(strict=True))) not in attempts:
                raise ValueError('Native result attempt is not bound to this checkpoint fingerprint')
    return root, source, cfg, result, names, records, apis, public_paths, refs, attempts, historical


def _frame_site(source, diagnostic, apis, runtime_roots=()):
    """Attribute a source exception from runtime frames, never task intent."""
    from .native_hints import _literal_site
    from .source_hints import _identity

    frames = []
    for match in re.finditer(r'^\s*File "([^"]+)", line (\d+), in ([\w<>]+)\s*$', diagnostic, re.M):
        path = Path(match[1])
        if path.is_absolute() and path.resolve().is_relative_to(source):
            frames.append((path.resolve().relative_to(source).as_posix(), int(match[2]), match[3], None, None))
        elif path.is_absolute():
            # Installed wheels report site-packages paths. Only explicit runtime
            # roots may be read, and the complete file must equal pinned source.
            for runtime_root, source_root in runtime_roots:
                resolved = path.resolve()
                if resolved.is_relative_to(runtime_root):
                    counterpart = (source_root / resolved.relative_to(runtime_root)).resolve()
                    if (counterpart.is_relative_to(source) and counterpart.is_file()
                            and resolved.is_file() and counterpart.suffix == '.py'
                            and bind(resolved)['sha256'] == bind(counterpart)['sha256']):
                        frames.append((counterpart.relative_to(source).as_posix(), int(match[2]),
                                       match[3], None, bind(resolved)))
    for match in re.finditer(r'^\s*at ([\w.$]+)\(([^():]+):(\d+)\)\s*$', diagnostic, re.M):
        frames.append((match[2], int(match[3]), match[1].rsplit('.', 1)[-1], match[1], None))
    messages = {match[1] for match in re.finditer(
        r'^\s*(?:Caused by:\s*)?[\w.$]*(?:Error|Exception):\s*(.*)$', diagnostic, re.M)}
    matches = {}
    for api, identity in apis.items():
        relative, _, name = _identity(identity)
        for frame_path, line, frame_name, owner, runtime_source in frames:
            if (frame_path != relative if owner is None else Path(relative).name != frame_path):
                continue
            if name.rsplit('.', 1)[-1] != frame_name:
                continue
            if owner is not None and api.rsplit(':', 1)[-1].replace('$', '.') != owner.replace('$', '.').replace('..', '.'):
                continue
            try:
                text = (source / relative).read_text()
                _, _, message = _literal_site(text, relative, identity, line)
            except (ValueError, SyntaxError):
                continue
            if message in messages:
                matches[identity] = {'api_id': api, 'function_id': identity, 'error_line': line,
                    'original_message': message, 'method': 'runtime_frame_and_exact_source_exception',
                    **({'runtime_source': runtime_source} if runtime_source is not None else {})}
    if len(matches) == 1:
        return next(iter(matches.values())), None
    return None, 'ambiguous_runtime_source' if matches else 'no_supported_source_exception_frame'


def _attempt(root, directory, api, cfg):
    """Bind exact native artifacts without copying private checker data."""
    directory = Path(directory).resolve(strict=True)
    if not directory.is_relative_to(root / 'execution'):
        raise ValueError('Native attempt directory escaped execution evidence')
    filename = cfg.comprehension['execute']['test_filename']
    if Path(filename).name != filename or filename.startswith('.'):
        raise ValueError('Native program filename must be a plain filename')
    refs = {}
    for key, name in [('provider_request', 'request.json'), ('provider_process', 'provider.json'),
                      ('response', 'response.txt'), ('execution_process', 'execution.json'),
                      ('stdout', 'stdout.txt'), ('stderr', 'stderr.txt'), ('executed_program', filename)]:
        path = directory / name
        if path.exists():
            refs[key] = bind(path)
            _bound(refs[key], directory)
    if 'provider_request' not in refs or 'provider_process' not in refs:
        raise ValueError('Native attempt lacks its request/provider receipt')
    request, provider = load(refs['provider_request']['path']), load(refs['provider_process']['path'])
    if (request.get('api') != api or not all(isinstance(request.get(key), str) for key in ('system', 'user'))):
        raise ValueError('Native request belongs to a different API or lacks exact prompts')
    identifier = 'native-' + digest([api, str(directory.relative_to(root))])[:24]
    return identifier, refs, request, provider


def build_native_r0_preview(manifest_path, manifest, output, *, max_cases=16):
    """Save all intake dispositions, then share accepted cases with native hints."""
    from .source_hint_development import _destination, _facts
    if type(max_cases) is not int or not 1 <= max_cases <= 100:
        raise ValueError('max_cases must be between 1 and 100')
    root, source, cfg, result, names, records, apis, public_paths, refs, attempts, historical = _inputs(manifest)
    runtime_roots = []
    for mapping in manifest.get('runtime_source_roots', []):
        relative = Path(mapping['source_root'])
        runtime_root = Path(mapping['runtime_root'])
        source_root = (source / relative).resolve(strict=True)
        if (relative.is_absolute() or '..' in relative.parts or not source_root.is_relative_to(source)
                or not runtime_root.is_absolute() or not runtime_root.is_dir()):
            raise ValueError('Runtime source mapping requires explicit contained source and absolute runtime roots')
        runtime_roots.append((runtime_root.resolve(strict=True), source_root))
    output = _destination(source, output)
    from . import source_hint_development, native_hints, source_hints, ablation
    refs += [bind(manifest_path), bind(__file__), *[bind(module.__file__) for module in
             (source_hint_development, native_hints, source_hints, ablation)]]
    held_out = manifest.get('held_out_case_ids')
    held_apis = manifest.get('held_out_api_ids', [])
    selected = manifest.get('native_case_ids')
    if (not isinstance(held_out, list) or not isinstance(held_apis, list)
            or (selected is not None and (not isinstance(selected, list) or len(set(selected)) != len(selected)))):
        raise ValueError('Declare held-out IDs and any selected native case IDs explicitly')
    cases, skipped, intake, seen = [], [], list(historical), set()
    execution = cfg.comprehension['execute']
    for api in names:
        directories = [directory for name, directory in attempts if name == api]
        if not directories:
            intake.append({'api_id': api, 'disposition': 'not_recorded_in_checkpoint'})
            continue
        for directory in directories:
            identifier, evidence, request, provider = _attempt(root, directory, api, cfg)
            if identifier in seen:
                raise ValueError('Duplicate native attempt evidence')
            seen.add(identifier)
            refs.extend(evidence.values())
            row = {'case_id': identifier, 'api_id': api, 'round': request.get('round'),
                   'provider_status': provider.get('status'), 'evidence': evidence}
            intake.append(row)
            def omit(reason):
                row['disposition'] = reason
                skipped.append({'case_id': identifier, 'api_id': api, 'reason': reason})
            if api in held_apis or identifier in held_out:
                omit('held_out'); continue
            prompt_hash = hashlib.sha256(json.dumps([request['system'], request['user']]).encode()).hexdigest()
            if prompt_hash not in attempts[(api, directory)]:
                raise ValueError('Native rendered prompt differs from its checkpoint binding')
            row['recorded_run_id'] = request.get('run_id')
            if type(request.get('round')) is not int or request['round'] != 0:
                omit('not_r0'); continue
            target = request.get('requested_target_declaration', {})
            if (target.get('api_id') != api or target.get('target_fingerprint') != digest(
                    {key: value for key, value in target.items() if key != 'target_fingerprint'})
                    or any(target.get(key) != records[api].get(key) for key in ('qualified_name', 'owner', 'signature'))):
                raise ValueError('Native requested target differs from the frozen API definition')
            if provider.get('status') != 'returned':
                omit('provider_failure'); continue
            if not {'response', 'execution_process', 'stdout', 'stderr', 'executed_program'} <= set(evidence):
                omit('incomplete_execution_evidence'); continue
            if any(ref['bytes'] > 2_000_000 for ref in evidence.values()):
                omit('oversized_native_evidence'); continue
            process = load(evidence['execution_process']['path'])
            stdout = Path(evidence['stdout']['path']).read_text()
            stderr = Path(evidence['stderr']['path']).read_text()
            code = Path(evidence['executed_program']['path']).read_text()
            response = Path(evidence['response']['path']).read_text()
            if type(process.get('exit_code')) is not int:
                raise ValueError('Native execution receipt lacks an integer exit code')
            diagnostic = stdout + '\n' + stderr
            row['exit_code'] = process['exit_code']
            row['oracle_status'] = 'not_independently_recorded'
            if process['exit_code'] == 0:
                # Missing witnesses are recorded separately; neither case is a
                # proven thrown source exception suitable for a native message edit.
                success = execution.get('success_marker', '')
                check = execution.get('correctness_marker', '__CHECK__')
                error = execution.get('error_marker', '')
                passed = ((not success or success in diagnostic) and (not error or error not in diagnostic)
                          and (not execution.get('require_correctness_check', True) or check in diagnostic))
                omit('recorded_marker_pass' if passed else 'marker_or_oracle_failure_without_exception'); continue
            if process['exit_code'] == 124:
                omit('timeout'); continue
            attribution, reason = _frame_site(source, diagnostic, apis, runtime_roots)
            if attribution is None:
                omit(reason); continue
            if attribution.get('runtime_source'):
                refs.append(attribution['runtime_source'])
            row['failing_api_id'] = attribution['api_id']
            if attribution['api_id'] in held_apis:
                omit('held_out_failing_api'); continue
            try:
                facts = _facts(source, attribution['function_id'])
            except (ValueError, SyntaxError) as exc:
                omit('unsupported_source_context'); row['reason'] = str(exc); continue
            if selected is not None and identifier not in selected:
                omit('not_selected_for_batch'); continue
            if len(cases) >= max_cases:
                omit('batch_limit'); continue
            item = {'evidence_id': identifier, 'function_id': attribution['function_id'],
                    'requested_api_id': api, 'failing_api_id': attribution['api_id'],
                    'code': code, 'diagnostic': diagnostic, 'attribution': attribution,
                    'audience_request': {'system': request['system'], 'prompt': request['user']},
                    'facts': facts, 'duplicate_case_ids': [], 'evidence': evidence,
                    'native_evidence': {'protocol': PROTOCOL, 'provider_status': provider['status'],
                        'requested_target_declaration': {key: target[key] for key in
                            ('api_id', 'qualified_name', 'owner', 'signature', 'target_fingerprint')},
                        'model_response': response, 'response_completion': provider.get('output_status', 'not_recorded_by_native_engine'),
                        'execution_exit_code': process['exit_code'], 'oracle_status': 'not_independently_recorded',
                        'prompt_mapping': 'system unchanged; native user copied exactly to prompt'}}
            if len(json.dumps(item)) > 90000:
                omit('context_limit'); continue
            refs.append(facts['source']); cases.append(item); row['disposition'] = 'accepted_for_diagnosis'
    if selected is not None and set(selected) - seen:
        raise ValueError('Selected native case ID is not present in this run')
    # A crash can leave request/output files before the checkpoint is appended.
    # Retain these bounded attempt directories, but never infer their treatment
    # membership or promote them without a matching checkpoint record.
    bound_directories = {directory for _, directory in attempts}
    filenames = ('request.json', 'provider.json', 'response.txt', 'execution.json',
                 'stdout.txt', 'stderr.txt', execution['test_filename'])
    for directory in sorted((root / 'execution').glob('run_*/attempt_*')):
        if not re.fullmatch(r'attempt_\d+', directory.name):
            continue
        if not directory.resolve().is_relative_to(root / 'execution'):
            raise ValueError('Unbound attempt escaped native execution evidence')
        if str(directory.resolve()) in bound_directories:
            continue
        evidence = {}
        for name in filenames:
            path = directory / name
            if path.is_file():
                ref = bind(path); _bound(ref, directory.resolve())
                evidence[name] = ref; refs.append(ref)
        intake.append({'attempt_directory': str(directory), 'disposition': 'unbound_attempt_not_promoted',
                       'evidence': evidence})
    refs = list({ref['path']: ref for ref in refs}.values())
    if not all(verify_artifact(ref) for ref in refs):
        raise ValueError('Native evidence changed during intake')
    preview = seal_record({'schema_version': 1, 'evidence_protocol': PROTOCOL,
        'source_root': str(source), 'baseline_revision': manifest['baseline_revision'],
        'split': 'development', 'condition': 'original', 'round': 0,
        'api_function_ids': apis, 'api_public_paths': public_paths,
        'cases': cases, 'skipped': skipped, 'intake': intake, 'artifacts': refs})
    output.mkdir(parents=True)
    atomic_json(output / 'preview.json', preview)
    return {'preview': str(output / 'preview.json'), 'cases': len(cases), 'skipped': len(skipped),
            'intake_records': len(intake), 'status': 'ready_for_diagnosis' if cases else 'no_supported_native_failures',
            'llm_calls': 0}
