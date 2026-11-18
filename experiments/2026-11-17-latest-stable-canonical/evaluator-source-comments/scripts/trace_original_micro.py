#!/usr/bin/env python3
"""Inspect Original-document microbenchmarks, exact prompts and R0/R1/R2.

    python scripts/trace_original_micro.py --pause
    python scripts/trace_original_micro.py --library rdpro --pause
    python scripts/trace_original_micro.py --library rdpro --live --pause

Default replies are scripted; execution is real. --live enables Gemini calls.
This inspects evaluation. README authoring and treatment installation are separate.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import inspect
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(REPOSITORY / 'vendor/aideal_engine/src'))

import yaml
from aideal.config import load_config
from aideal.doc_check_comprehension import comprehension_check
from aideal.doc_check_execution import _comprehension_execute
from aideal.doc_check_inputs import _fill_scaffold
from aideal.doc_check_errors import _classify_error
from aideal.doc_check_sources import _comprehension_inventory
from aideal.execution import run_command
from aideal.error_log import ErrorLog
from aideal.prompts import load as load_prompt, prompt_path
from aideal.fixreport import write_report
from aideal.llm import invoke_text, reset_usage, usage_snapshot, usage_delta
from aideal.readme_format import api_storage_key
from workflow.execution import atomic_json
from scripts.run_original_micro import prepare
from scripts.trace_view import build_trace_view, snapshot_sources


class Transcript:
    """Mirror terminal output into trace.log, flushing each printed step."""
    def __init__(self, terminal, file):
        self.terminal, self.file = terminal, file

    def write(self, text):
        self.terminal.write(text)
        self.file.write(text)
        self.flush()
        return len(text)

    def flush(self):
        self.terminal.flush()
        self.file.flush()


def prepare_demo(root: Path, repairs: int):
    """Create the small Python example without touching an attached library."""
    (root / 'library').mkdir()
    (root / 'configs').mkdir()
    source = 'def double(value):\n    """Return twice the supplied number."""\n    return 2 * value\n'
    readme = '# Tiny arithmetic library\n\nUse double(value) to return twice a number.\nExample: double(3) returns 6.\n'
    (root / 'library/example.py').write_text(source)
    (root / 'library/README.md').write_text(readme)
    (root / 'api_manifest.json').write_text('["double"]\n')
    (root / 'scaffold.py').write_text(
        'import sys\n' + f'sys.path.insert(0, {str(root / "library")!r})\n'
        'from example import double\n'
        '# AIDEAL_DATA_BINDINGS\n# BEGIN TEST\n# END TEST\nprint("__DONE__")\n')
    profile = {'project': {'name': 'Tiny arithmetic', 'language': 'Python',
                          'description': 'A demonstration library with one numeric function.'},
               'domain': 'arithmetic', 'target_users': ['Python developers'],
               'use_cases': ['Double a number']}
    (root / 'configs/project_profile.yaml').write_text(yaml.safe_dump(profile))
    config = {
        'project': {'name': 'Original repair-loop walkthrough', 'language': 'Python'},
        'codebase': {'source_globs': ['library/*.py']},
        'files': {'original_readme': 'library/README.md',
                  'project_profile': 'configs/project_profile.yaml',
                  'llm_readme': 'docs/unused.md', 'error_log': 'logs/errors.jsonl'},
        'models': {'registry': {'demo': {'provider': 'mock', 'model': 'offline-demo'}},
                   'roles': {'audience': 'demo', 'author': 'demo', 'fixer': 'demo'}},
        'comprehension': {'class_context': False, 'execute': {
            'command': shlex.quote(sys.executable) + ' "{test_file}"',
            'scaffold': 'scaffold.py', 'region': ['# BEGIN TEST', '# END TEST'],
            'test_filename': 'Generated.py', 'work_dir': 'execution',
            'output_dir': 'outputs', 'build': '', 'max_fix_rounds': repairs, 'stuck_repeats': 0,
            'success_marker': '__DONE__', 'check_marker': '__CHECK__',
            'require_correctness': True, 'stop_on_provider_error': True,
            'auto_report': False, 'timeout_seconds': 10,
            'execution_context': 'The scaffold already imports double from example.',
        }},
    }
    config_path = root / 'configs/aideal.yaml'
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    cfg = load_config(config_path)
    return cfg, root / 'api_manifest.json'


def walkthrough(root: Path, args):
    """Observe the existing native loop; never implement a second repair loop."""
    def show(label, value):
        print(f'\n{label}\n' + '-' * len(label), flush=True)
        print(value if isinstance(value, str) else json.dumps(value, indent=2), flush=True)

    def wait(label):
        # Publish the latest evidence before every review pause. The browser
        # can reload this file; advancing Python still requires Enter here.
        atomic_json(root / 'trace_state.json', {'label': label})
        try:
            view = build_trace_view([root], root / 'TRACE.html')
            print(f'Interactive view: {view}', flush=True)
        except (OSError, ValueError) as exc:
            print(f'View not ready: {exc}', flush=True)
        if args.pause:
            input(f'\n[Pause] {label}. Press Enter to continue. ')

    name = args.api or ('detectType' if args.library == 'rdpro' else 'double')
    repairs, live = args.repairs, args.live
    show('1. Inputs supplied by the developer',
         ('LIVE GEMINI TRACE. Model responses and execution are real.\n' if live else
          'OFFLINE DEMO. Only model responses are scripted; execution is real.\n') +
         f'Library: {args.library}; API: {name}; maximum repairs: {repairs}.\n'
         'Original documentation is supplied, not generated.\n'
         'This uses the native loop used by run_original_micro.py.\n'
         f'Output folder: {root}')
    if args.library == 'rdpro':
        spec = yaml.safe_load(args.catalog.read_text())['rdpro']
        if spec.get('blocked'):
            raise ValueError('RDPro runtime is not ready: ' + spec['blocked'])
        # Shared preparation validates inputs and records the exact API/repair scope.
        # It writes only under this fresh trace folder. The full batch remains R0.
        cfg, _ = prepare(spec, root, args.model, None, max_fix_rounds=repairs,
                         api=name, mode='trace-live' if live else 'trace-mock')
        manifest = root / 'inputs/api_manifest.json'
    else:
        cfg, manifest = prepare_demo(root, repairs)
    snapshot_sources(root)
    config_path = root / 'configs/aideal.yaml'
    execution = cfg.raw['comprehension']['execute']
    # Match the native evaluator's directory key while preserving the full API
    # identity in prompts and results. Owners must never share an output folder.
    work_api = cfg.root / execution['work_dir'] / f'run_{api_storage_key(name)}'
    program = work_api / execution['test_filename']
    inventory, _, error = _comprehension_inventory(
        cfg, 'original', manifest=[name], doc_scope='relevant')
    if error or not inventory:
        raise ValueError(f'Cannot select original documentation: {error}')
    (root / 'inputs').mkdir(exist_ok=True)
    document = root / 'inputs/selected_documentation.txt'
    document.write_text(inventory[0].body, encoding='utf-8')
    show('Original documentation actually selected for the prompt', document.read_text())
    show('Original documentation files considered', '\n'.join(map(str, cfg.original_readme_files)))
    show('2. Configuration and selected API', {
        'resolved_config': str(config_path), 'manifest': str(manifest), 'api': name,
        'model': cfg.model_for_role('audience').model,
        'provider': cfg.model_for_role('audience').provider,
        'google_sdk_attempts': int(os.getenv('AIDEAL_GOOGLE_MAX_RETRIES', '1')) if live else None,
        'max_fix_rounds': repairs, 'doc_source': 'original', 'doc_scope': 'relevant',
        'class_context': False, 'test_filename': program.name,
        'execution_timeout_s': execution.get('timeout_seconds'),
        'output_folder': str(root),
    })
    show('Execution scaffold supplied to AIDEAL',
         (cfg.root / execution['scaffold']).read_text())
    # Derive locations from the installed functions, so refactoring cannot leave
    # the printed review map pointing at stale lines.
    functions = (prepare, load_config, _comprehension_inventory, comprehension_check,
                 _comprehension_execute, load_prompt, invoke_text, _fill_scaffold,
                 run_command, _classify_error, ErrorLog.append, ErrorLog.failures_for)
    locations = []
    for function in functions:
        function = inspect.unwrap(function)
        locations.append(f'{function.__module__}.{function.__qualname__} -> '
                         f'{inspect.getsourcefile(function)}:{inspect.getsourcelines(function)[1]}')
    show('Function call chain and code-review entry points', '\n'.join(locations))
    show('Selected prompt template', str(prompt_path(cfg, 'aideal/comprehension_write_exec')))
    loop_lines, first_line = inspect.getsourcelines(inspect.unwrap(_comprehension_execute))
    loop_index = next(i for i, line in enumerate(loop_lines) if 'for attempt in range(' in line)
    show('Actual loop in doc_check_execution.py',
         f'line {first_line + loop_index}: {loop_lines[loop_index].strip()}\n'
         f'max_fix_rounds={repairs} -> at most {repairs + 1} requests, R0 through R{repairs}.\n'
         'R0 uses audience. R1/R2 use fixer with previously recorded failures.\n'
         'Pass ends the loop immediately. No repair is forced in live mode.')
    wait('Inspect the configuration, functions and loop')
    model_calls = 0

    def trace_model(spec, system, user):
        """Print the exact messages before calling Gemini or supplying a demo reply."""
        nonlocal model_calls
        number = model_calls
        model_calls += 1
        role = 'audience' if number == 0 else 'fixer'
        evidence = work_api / f'attempt_{model_calls:04d}'
        show(f'R{number} saved input/output directory', str(evidence))
        show(f'3. R{number} {role} input — exact system prompt', system)
        show(f'R{number} {role} input — exact user prompt (including prior failures on retry)', user)
        wait(f'Inspect R{number} prompt before ' + ('sending it to Gemini' if live else 'scripted response'))
        before, started = usage_snapshot(), time.monotonic()
        try:
            if live:
                # This saved reference is the genuine provider call, not the patched observer.
                response = invoke_text(spec, system, user)
            elif args.library == 'rdpro':
                expected = ['StringType', 'DoubleType', 'LongType' if args.fail else 'IntegerType'][number]
                response = (f'val actual = RasterSchemaHelper.detectType(1)\n'
                            f'assert(actual == {expected}, s"Expected {expected}, got $actual")\n'
                            'println(s"__CHECK__ detectType value=1 type=${actual.typeName}")')
            else:
                expected = [5, 7, 9 if args.fail else 6][number]
                response = (f'value = double(3)\nassert value == {expected}, f"expected {expected}, got {{value}}"\n'
                            'print(f"__CHECK__ double(3)={value}")')
        except Exception as exc:
            show(f'R{number} provider error; no program will execute', f'{type(exc).__name__}: {exc}')
            raise  # The native engine saves this as an incomplete provider attempt.
        finally:
            observed = {'live': live, 'call_wall_s': time.monotonic() - started,
                        'usage': usage_delta(before) if live else None,
                        'note': 'Call interval excludes trace printing and Enter pauses.'}
            atomic_json(evidence / 'trace_provider.json', observed)
        # The native engine saves response.txt after this observer returns.
        # This separate receipt makes the returned response visible while paused.
        (evidence / 'trace_response.txt').write_text(response, encoding='utf-8')
        show(f'R{number} {role} output — ' + ('actual model response' if live else 'mocked snippet'), response)
        show(f'R{number} model accounting', observed)
        wait(f'Inspect R{number} input/output before its real execution')
        return response

    def trace_execution(command, **kwargs):
        """Observe the real compiler/process; keep full commands in saved evidence."""
        number = model_calls - 1
        evidence = work_api / f'attempt_{model_calls:04d}'
        show(f'4. R{number} complete test before execution', program.read_text())
        command_file = evidence / 'command.txt'
        command_file.write_text(command + '\n')
        # RDPro's resolved dependency classpath exceeds 100 KB. Preserve it in
        # full without burying the prompts and verdicts in repeated jar paths.
        show(f'R{number} actual execution command', command if len(command) < 1500 else
             f'Compile Scala, then execute GeoJobMain. Full {len(command):,}-character command: {command_file}')
        # Generated tests need the library runtime, not model credentials.
        kwargs['env'] = {key: value for key, value in kwargs.get('env', {}).items()
                         if not key.endswith('_API_KEY') and key != 'GOOGLE_APPLICATION_CREDENTIALS'}
        started = time.monotonic()
        try:
            process = run_command(command, **kwargs)
        except subprocess.TimeoutExpired:
            show(f'R{number} execution timed out', f'Limit: {kwargs.get("timeout")} seconds. Native engine records stdout/stderr.')
            raise
        finally:
            atomic_json(evidence / 'trace_execution.json', {
                'process_wall_s': time.monotonic() - started,
                'note': 'Process interval excludes trace printing and Enter pauses.'})
        # Publish the completed process before the native verdict is computed.
        atomic_json(evidence / 'trace_execution.json', {
            'process_wall_s': time.monotonic() - started,
            'note': 'Process interval excludes trace printing and Enter pauses.',
            'process': {'exit_code': process.returncode, 'command': command, 'cwd': str(kwargs.get('cwd'))},
            'stdout': process.stdout, 'stderr': process.stderr})
        show(f'R{number} actual exit code', process.returncode)
        show(f'R{number} standard output', process.stdout or '(empty)')
        show(f'R{number} standard error', process.stderr or '(empty)')
        wait(f'Inspect R{number} execution output before verdict/next round')
        return process

    arguments = dict(api=name, doc_source='original', execute=True, show_code=True,
                     max_fix_rounds=repairs, class_context=False, doc_scope='relevant',
                     manifest=str(manifest), resume=True)
    reset_usage()
    with patch('aideal.llm.invoke_text', side_effect=trace_model), \
            patch('aideal.execution.run_command', side_effect=trace_execution):
        result = comprehension_check(cfg, **arguments)
    atomic_json(root / 'result.json', result)
    metric = result.get('metrics', {}).get(name, {})
    if metric:
        write_report(cfg, root / 'result.json', out_path=root / 'REPORT.md')
    detail = result.get('details', {}).get(name, {})
    rounds = detail.get('rounds', []) if isinstance(detail, dict) else []
    complete = bool(metric) and result.get('run', {}).get('complete', False)
    if not complete:
        reason = 'incomplete: provider or setup failure; inspect result.json and provider.json'
    elif metric.get('status') == 'pass':
        reason = f'passed at R{metric["pass_round"]}'
    elif metric.get('error_category') == 'infra':
        reason = 'execution infrastructure failure'
    elif any(r.get('status') == 'stuck-stop' for r in rounds):
        reason = 'repeated-error stop'
    else:
        reason = f'repair limit reached after R{repairs}'
    summary = {
        'library': args.library, 'api': name, 'mode': 'live' if live else 'scripted',
        'complete': complete, 'status': metric.get('status', 'not_run'),
        'rounds': rounds, 'requests': model_calls, 'repair_rounds_allowed': repairs,
        'stop_reason': reason, 'error_category': metric.get('error_category'),
        'score_with_infra': result.get('score_with_infra') if complete else None,
        'wall_seconds': metric.get('wall_s'),
        'timing_note': 'Native walkthrough time includes printing and pauses; not experimental timing. See trace_* intervals.',
        'tokens': ({'input': metric.get('input_tokens'), 'output': metric.get('output_tokens'),
                    'note': 'Provider-reported counters; failed requests may have unknown usage.'}
                   if live else 'Unavailable: no provider call. Recorded zero counters are mock placeholders.'),
        'output': str(root),
    }
    atomic_json(root / 'summary.json', summary)
    table = ['| Round | Status | Error category |', '|---|---|---|']
    table += [f'| R{r["round"]} | {r["status"]} | {r.get("category", "—")} |' for r in rounds]
    (root / 'SUMMARY.md').write_text(
        f'# {args.library}: {name}\n\nMode: {summary["mode"]}. {reason}.\n\n' + '\n'.join(table) +
        '\n\nNative microbenchmarks execute model-written assertions and check exit/markers; '
        'this is not an independent hidden-answer test.\n\n' +
        '\n'.join(f'- [{label}]({path})' for label, path in (
            ('Transcript', root / 'trace.log'), ('Selected documentation', document),
            ('Round evidence', work_api), ('Native result', root / 'result.json'),
            ('Accounting', root / 'summary.json'))) + '\n')
    show('5. Final verdict and accounting', summary)
    wait('Inspect the recorded verdict and stopping reason')
    if complete:
        show('Checkpoint row', Path(result['run']['checkpoint']).read_text())
        # Only completed work can be reused without a model call. Provider
        # failures remain pending and must never trigger an automatic paid retry.
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('Resume must reuse the completed API')) as provider:
            resumed = comprehension_check(cfg, **arguments)
        atomic_json(root / 'resume_result.json', resumed)
        show('6. Resume reads the completed checkpoint', {
            'new_model_calls': provider.call_count, 'reused_apis': resumed['run']['resumed_apis'],
            'status': resumed['metrics'][name]['status'],
            'meaning': 'Both completed passes and failures at the repair limit are reused.'})
        assert provider.call_count == 0 and resumed['run']['resumed_apis'] == 1
    else:
        show('6. Resume demonstration skipped', 'No automatic retry of incomplete/provider-failed work.')
    show('7. Open these files to follow the same evidence', '\n'.join(str(path) for path in (
        root / 'SUMMARY.md', root / 'trace.log', config_path, work_api,
        root / 'result.json', root / 'REPORT.md', root / 'summary.json')))
    print(f'Each executed attempt retains request.json, response.txt, provider.json, {program.name}, execution.json, stdout.txt and stderr.txt.')
    build_trace_view([root], root / 'TRACE.html')
    print(f'Interactive view: {root / "TRACE.html"}', flush=True)
    if args.library == 'demo':
        assert metric.get('status') == ('pass' if repairs == 2 and not args.fail else 'fail')
        assert model_calls == repairs + 1
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', choices=('demo', 'rdpro'), default='demo')
    parser.add_argument('--api', help='Exact API name; RDPro defaults to detectType')
    parser.add_argument('--catalog', type=Path, default=REPOSITORY / 'configs/original_micro_libraries.yaml')
    parser.add_argument('--live', action='store_true', help='Use actual Gemini responses for RDPro; consumes API credits')
    parser.add_argument('--model', default='gemini-3.1-flash-lite', help='Live Gemini model identifier')
    parser.add_argument('--output', type=Path, help='Fresh empty folder; RDPro defaults to .local/rdpro-trace-<time>-<mode>')
    parser.add_argument('--repairs', type=int, choices=(0, 1, 2), default=2)
    parser.add_argument('--fail', action='store_true', help='Keep the scripted R2 reply failing; unavailable with --live')
    parser.add_argument('--pause', action='store_true', help='Wait for Enter before model requests and at execution/review steps')
    args = parser.parse_args()
    if args.live and (args.library != 'rdpro' or args.fail):
        parser.error('--live requires --library rdpro and cannot use --fail')
    if not args.live and args.api and args.api != ('detectType' if args.library == 'rdpro' else 'double'):
        parser.error('Scripted replies support only RDPro detectType or demo double')
    if args.live:
        # This existing SDK knob counts total attempts, including the first.
        # One attempt disables transport retries; R1/R2 remain code repairs.
        os.environ.setdefault('AIDEAL_GOOGLE_MAX_RETRIES', '1')
        if not (os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')):
            parser.error('Set GOOGLE_API_KEY or GEMINI_API_KEY in this terminal before --live; never put a key in the script')
        if not os.getenv('GOOGLE_API_KEY'):
            os.environ['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']
    if args.output:
        root = args.output.resolve()
    elif args.library == 'rdpro':
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        root = REPOSITORY / '.local' / f'rdpro-trace-{stamp}-{"live" if args.live else "scripted"}'
    else:
        root = Path(tempfile.mkdtemp(prefix='aideal-original-trace-')).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        parser.error('--output must be empty; existing results are never overwritten')
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'trace.log').open('w', buffering=1) as log:
        with redirect_stdout(Transcript(sys.stdout, log)), redirect_stderr(Transcript(sys.stderr, log)):
            try:
                status = walkthrough(root, args)
            except (OSError, ValueError, RuntimeError) as exc:
                print(f'Trace stopped: {type(exc).__name__}: {exc}', flush=True)
                atomic_json(root / 'trace_error.json', {'type': type(exc).__name__, 'error': str(exc)})
                status = 2
    print(f'Walkthrough stopped. Read {root / "trace.log"}')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
