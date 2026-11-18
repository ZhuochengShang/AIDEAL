#!/usr/bin/env python3
"""Check this checkout offline; never start or resume a library experiment.

Run with the intended project interpreter. --tests runs synthetic regression
tests and the code-map interface tests. The report records skipped tests and
does not certify live providers or library-specific execution environments.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


SCOPES = ('workflow', 'vendor/aideal_engine/src/aideal', 'scripts', 'tests',
          'studies/sedonadb', 'studies/historical')


def check(root, output, tests=False):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Choose a fresh output directory to preserve the previous report')
    output.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    for key in ('OPENAI_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY'):
        environment.pop(key, None)
    records = []

    def run(name, command, timeout=60, extra_env=None):
        started = time.monotonic()
        log = output / (name + '.log')
        with log.open('w', encoding='utf-8') as stream:
            try:
                result = subprocess.run(command, cwd=root,
                                        env={**environment, **(extra_env or {})},
                                        stdout=stream, stderr=subprocess.STDOUT,
                                        timeout=timeout, check=False)
                status, code = ('pass' if result.returncode == 0 else 'fail'), result.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                stream.write('\n' + type(exc).__name__ + ': ' + str(exc) + '\n')
                status, code = 'error', None
        text = log.read_text(encoding='utf-8', errors='replace')
        record = {'name': name, 'status': status, 'returncode': code,
                  'seconds': round(time.monotonic() - started, 3),
                  'command': command, 'log': log.name}
        if name == 'python_tests':
            match = re.search(r'Ran (\d+) tests?', text)
            record['tests_run'] = int(match[1]) if match else None
            match = re.search(r'skipped=(\d+)', text)
            record['tests_skipped'] = int(match[1]) if match else 0
        records.append(record)
        print(name + ': ' + status, flush=True)

    files = sorted({p for scope in SCOPES for p in (root / scope).rglob('*.py')
                    if '__pycache__' not in p.parts})
    syntax_errors, bindings = [], []
    for path in files:
        content = path.read_bytes()
        bindings.append({'path': path.relative_to(root).as_posix(),
                         'sha256': hashlib.sha256(content).hexdigest()})
        try:
            ast.parse(content, filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            syntax_errors.append({'path': str(path), 'error': str(exc)})
    records.append({'name': 'python_syntax', 'status': 'fail' if syntax_errors else 'pass',
                    'files_checked': len(files), 'errors': syntax_errors})
    packages = {}
    for name in ('yaml', 'langchain_core', 'langchain_openai', 'openai', 'google.genai', 'mcp'):
        try:
            packages[name] = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            packages[name] = False
    run('controller_help', [sys.executable, 'scripts/aideal', '--help'])
    run('controller_status', [sys.executable, 'scripts/aideal', 'status'])
    run('engine_help', [sys.executable, '-m', 'aideal.cli', '--help'],
        extra_env={'PYTHONPATH': str(root / 'vendor/aideal_engine/src')})
    if tests:
        run('python_tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], 1800)
        node = shutil.which('node')
        if node:
            run('code_map_tests', [node, '--test', 'tests/test_code_map_ui.cjs'])
        else:
            records.append({'name': 'code_map_tests', 'status': 'unavailable',
                            'reason': 'Node.js is not on PATH; UI checks did not run'})
    current_files = {p for scope in SCOPES for p in (root / scope).rglob('*.py')
                     if '__pycache__' not in p.parts}
    stable = current_files == set(files) and all((root / b['path']).is_file() and
                 hashlib.sha256((root / b['path']).read_bytes()).hexdigest() == b['sha256']
                 for b in bindings)
    records.append({'name': 'source_unchanged_during_check', 'status': 'pass' if stable else 'fail'})
    result = {'created_utc': datetime.now(timezone.utc).isoformat(), 'root': str(root),
              'python': sys.executable, 'python_version': sys.version,
              'dependencies_present': packages, 'full_tests_requested': tests,
              'passed': all(r['status'] == 'pass' for r in records),
              'checks': records, 'source_files': bindings,
              'limits': ['No live model call or real-library study was launched.',
                         'Synthetic checks do not prove arbitrary generated programs correct.',
                         'Skipped tests and absent optional providers remain unverified.',
                         'Frozen studies and live runtime dependencies require their own preflight.']}
    (output / 'checks.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True, help='Fresh directory for check results')
    parser.add_argument('--tests', action='store_true', help='Also run the offline regression suite')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Use the project Python environment, version 3.10 or newer')
    result = check(args.root, args.output, args.tests)
    print('Report: ' + str(args.output.resolve() / 'checks.json'))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
