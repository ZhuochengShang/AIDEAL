#!/usr/bin/env python3
"""Offline native runtime controls: real scaffolds/execution, scripted responses.

These are infrastructure checks, not measured audience outcomes. No model provider
is contacted. All outputs use a fresh explicit checks namespace and mock identity.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

import yaml

SENTINEL = 'AIDEAL_EXPECTED_ASSERTION_FAILURE'
CASES = ('pass', 'assertion_failure', 'witness_omitted')
APIS = {'rdpro': 'detectType', 'mdanalysis': 'Universe', 'tslearn': 'dtw',
        'mir_eval': 'f_measure', 'thumbnailator': 'size'}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_launcher(toolkit):
    sys.path.insert(0, str(toolkit))
    sys.path.insert(0, str(toolkit / 'vendor/aideal_engine/src'))
    spec = importlib.util.spec_from_file_location('preflight_native_launcher', toolkit / 'scripts/run_original_micro.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def python_identity(name, source, spec):
    module, suffix = {'mdanalysis': ('MDAnalysis', 'package/MDAnalysis/__init__.py'),
                      'tslearn': ('tslearn', 'tslearn/__init__.py'),
                      'mir_eval': ('mir_eval', 'mir_eval/__init__.py')}[name]
    expected = str(source / suffix)
    interpreters = [Path(p) for p in spec.get('runtime_artifacts', []) if Path(p).name in ('python', 'python3', 'python3.10', 'python3.11', 'python3.12', 'python3.13')]
    if len(interpreters) != 1:
        raise ValueError('Python library catalog must list exactly one interpreter runtime artifact')
    expected_environment = str(interpreters[0].parent.parent.resolve())
    return (f'import {module} as _preflight_package\n'
            'from pathlib import Path as _PreflightPath\n'
            'import json as _preflight_json\nimport sys as _preflight_sys\n'
            f'assert _PreflightPath(_preflight_package.__file__).resolve() == _PreflightPath({expected!r}).resolve(), "wrong package source"\n'
            f'assert _PreflightPath(_preflight_sys.prefix).resolve() == _PreflightPath({expected_environment!r}).resolve(), "wrong scientific Python environment"\n'
            'print("__IDENTITY__ " + _preflight_json.dumps({"module": _preflight_package.__name__, "file": _preflight_package.__file__, '
            '"version": getattr(_preflight_package, "__version__", "unknown"), "python": _preflight_sys.executable}))\n')


def snippet(name, spec, case):
    source = Path(spec['source_link']['target']).resolve()
    if name == 'rdpro':
        jar = next(str(Path(p).resolve()) for p in spec['runtime_artifacts'] if p.endswith('-library_overlay.jar') or Path(p).name == 'library_overlay.jar')
        code = ('val actual = RasterSchemaHelper.detectType(1)\n'
                'require(actual == IntegerType, "detectType integer result")\n'
                'val origin = java.nio.file.Paths.get(RasterSchemaHelper.getClass.getProtectionDomain.getCodeSource.getLocation.toURI).toRealPath().toString\n'
                f'require(origin == {json.dumps(jar)}, "wrong RDPro runtime JAR: " + origin)\n'
                'println("__IDENTITY__ " + origin + " java=" + System.getProperty("java.version"))\n')
        witness = 'println("__CHECK__ detectType integer")\n'
        failure = f'assert(false, "{SENTINEL}")\n'
    elif name == 'thumbnailator':
        jar = next(str(Path(p).resolve()) for p in spec['runtime_artifacts'] if p.endswith('-thumbnailator-0.4.21.jar') or Path(p).name == 'thumbnailator-0.4.21.jar')
        code = ('BufferedImage resized = Thumbnails.of(sourceImage).size(16, 12).asBufferedImage();\n'
                'if (resized.getWidth() != 16 || resized.getHeight() != 12) throw new AssertionError("resize dimensions");\n'
                'for (String fixture : new String[] {grid_png, grid_jpeg, exif_jpeg}) {\n'
                '    BufferedImage decoded = ImageIO.read(new File(fixture));\n'
                '    if (decoded == null || decoded.getWidth() <= 0 || decoded.getHeight() <= 0) throw new AssertionError("image fixture");\n'
                '}\n'
                'String origin = Paths.get(Thumbnails.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath().toString();\n'
                f'if (!origin.equals({json.dumps(jar)})) throw new AssertionError("wrong Thumbnailator JAR: " + origin);\n'
                'System.out.println("__IDENTITY__ " + origin + " java=" + System.getProperty("java.version"));\n')
        witness = 'System.out.println("__CHECK__ size 16x12 PNG/JPEG fixtures");\n'
        # The corrected runner must enable Java assertions. This control fails
        # if assertions work, and refuses readiness if they are silently disabled.
        failure = f'assert sourceImage == null : "{SENTINEL}";\n'
    else:
        code = python_identity(name, source, spec)
        if name == 'mdanalysis':
            code += ('from MDAnalysis.lib import c_distances as _preflight_ext\n'
                     f'assert _PreflightPath(_preflight_ext.__file__).resolve().is_relative_to(_PreflightPath({str(source / "package/MDAnalysis")!r}).resolve())\n'
                     'assert _preflight_ext.__file__.endswith(".so") and "darwin" not in _preflight_ext.__file__\n'
                     '_preflight_universe = _preflight_package.Universe(psf_path, dcd_path)\n'
                     'assert len(_preflight_universe.atoms) == 3341 and len(_preflight_universe.trajectory) == 98\n'
                     'assert np.isfinite(_preflight_universe.trajectory[0].positions).all()\n'
                     '_preflight_xtc = _preflight_package.Universe(gro_path, xtc_path)\n'
                     'assert len(_preflight_xtc.atoms) > 0 and len(_preflight_xtc.trajectory) > 0\n'
                     'assert np.isfinite(_preflight_xtc.trajectory[0].positions).all()\n'
                     'assert len(_preflight_package.Universe(pdb_path).atoms) > 0\n'
                     'print("__FIXTURES__ PSF/DCD=3341 atoms,98 frames; GRO/XTC and PDB readable")\n')
        elif name == 'tslearn':
            code += ('from tslearn.metrics import dtw as _preflight_dtw\n'
                     'assert np.load(trace_npz)["X_train"].shape == (100, 275, 1)\n'
                     'assert _preflight_dtw([1., 2., 3.], [1., 2., 3.]) == 0.0\n'
                     'assert X.shape == (8, 40, 1) and X2.shape == (4, 32, 1)\n'
                     'print("__FIXTURES__ Trace train=100x275x1; balanced scaffold X=8x40x1")\n')
        else:
            code += ('_preflight_reference = _preflight_package.io.load_events(beat_reference_file)\n'
                     '_preflight_estimate = _preflight_package.io.load_events(beat_estimate_file)\n'
                     'assert len(_preflight_reference) > 0 and len(_preflight_estimate) > 0\n'
                     '_preflight_intervals, _preflight_labels = _preflight_package.io.load_labeled_intervals(chord_reference_file)\n'
                     'assert len(_preflight_intervals) == len(_preflight_labels) > 0\n'
                     '_preflight_times, _preflight_freqs = _preflight_package.io.load_time_series(melody_reference_file)\n'
                     'assert len(_preflight_times) == len(_preflight_freqs) > 0\n'
                     '_preflight_scores = _preflight_package.onset.f_measure(np.array([0., 1., 2.]), np.array([0., 1., 2.]))\n'
                     'assert np.allclose(_preflight_scores, (1., 1., 1.))\n'
                     'print("__FIXTURES__ beat/chord/melody fixtures readable")\n')
        witness = f'print("__CHECK__ {APIS[name]} offline runtime verified")\n'
        failure = f'assert False, "{SENTINEL}"\n'
    if case == 'witness_omitted':
        return code
    return code + witness + (failure if case == 'assertion_failure' else '')


def audit_inputs(name, spec, launcher):
    cfg = launcher.load_config(spec['base_config'])
    names = launcher._load_manifest(cfg, spec['manifest'])
    if APIS[name] not in names:
        raise ValueError(f'Missing chosen native API: {APIS[name]}')
    source = Path(spec['source_link']['target']).resolve()
    if not source.is_dir():
        raise ValueError(f'Source snapshot absent: {source}')
    if not cfg.original_readme_files:
        raise ValueError('No original documentation resolved')
    checked = [Path(spec['base_config']), Path(spec['manifest']), source,
               cfg.root / cfg.raw['files']['project_profile'], cfg.root / cfg.comprehension['execute']['scaffold'],
               *cfg.original_readme_files, *(Path(p) for p in spec.get('runtime_artifacts', []))]
    fixture_paths = []
    for value in cfg.comprehension['execute'].get('sample_data', {}).values():
        value = value.get('path') if isinstance(value, dict) else value
        if not isinstance(value, str):
            raise ValueError('Fixture must be a path string or path record')
        fixture_paths.append((cfg.root / value).resolve())
    checked += fixture_paths
    missing = [str(p) for p in checked if not p.exists()]
    if missing:
        raise ValueError('Missing runtime/input paths: ' + ', '.join(missing))
    for p in checked:
        if any(s in str(p) for s in ('/Users/', '/Library/Java/', '-darwin')):
            raise ValueError('Mac path remains in runtime input: ' + str(p))
    for p in (Path(spec['base_config']), cfg.root / cfg.raw['files']['project_profile'], cfg.root / cfg.comprehension['execute']['scaffold']):
        if any(s in p.read_text() for s in ('/Users/', '/Library/Java/', '-darwin')):
            raise ValueError('Mac path remains inside config/profile/scaffold: ' + str(p))
    if not cfg.comprehension['execute'].get('require_correctness'):
        raise ValueError('Native correctness witness gate must be enabled')
    if name == 'mdanalysis':
        extensions = sorted(p.resolve() for p in (source / 'package/MDAnalysis').rglob('*.so'))
        artifacts = {Path(p).resolve() for p in spec.get('runtime_artifacts', [])}
        if not extensions or not set(extensions).issubset(artifacts):
            raise ValueError('Build Linux MDAnalysis extensions and add every .so to catalog runtime_artifacts before preflight')
        fixture_dir = Path(cfg.comprehension['execute']['sample_data']['mdanalysis_fixture_dir'])
        writable = [str(p) for p in [fixture_dir, *(q for q in fixture_dir.rglob('*') if q.is_dir())] if p.stat().st_mode & 0o222]
        if writable:
            raise ValueError('Make MDAnalysis fixture directories read-only before preflight to prevent hash-changing offset caches: ' + writable[0])
    return {'selected_api': APIS[name], 'manifest_names': len(names), 'source': str(source),
            'original_document_files': len(cfg.original_readme_files), 'fixture_paths': [str(p) for p in fixture_paths],
            'runtime_artifacts': len(spec.get('runtime_artifacts', [])), 'config': spec['base_config']}


def check_case(name, spec, case, destination, launcher):
    cfg, names = launcher.prepare(spec, destination, 'offline-native-runtime-preflight', None,
                                  api=APIS[name], mode='trace-mock', max_fix_rounds=0)
    scripted = snippet(name, spec, case)
    (destination / 'OFFLINE_PREFLIGHT.json').write_text(json.dumps(
        {'purpose': 'offline infrastructure control; not a measured audience result',
         'model_calls': 0, 'scripted_provider_responses': 1, 'case': case, 'library': name}, indent=2) + '\n')
    with patch('aideal.llm.invoke_text', return_value=scripted) as provider:
        with redirect_stdout(io.StringIO()):
            launcher.run_library(cfg, destination, None)
    if provider.call_count != 1:
        raise AssertionError(f'Expected one intercepted response, saw {provider.call_count}')
    result = json.loads((destination / 'result.json').read_text())
    metric = result['metrics'][APIS[name]]
    evidence = Path(metric['attempt_evidence'][0])
    execution = json.loads((evidence / 'execution.json').read_text())
    stdout, stderr = (evidence / 'stdout.txt').read_text(), (evidence / 'stderr.txt').read_text()
    returncode = execution.get('returncode', execution.get('exit_code'))
    success_marker = cfg.comprehension['execute']['success_marker']
    if returncode is None:
        raise AssertionError('Execution evidence has no exit code')
    require(result['run']['complete'] and result['run']['max_fix_rounds'] == 0, 'Incomplete or repaired native control')
    require(metric['attempts'] == 1 and len(metric['attempt_evidence']) == 1, 'Control generated multiple attempts')
    require('__IDENTITY__' in stdout, 'Real execution never reached package/JAR identity check')
    if case == 'pass':
        require(metric['status'] == 'pass' and returncode == 0, 'Known-good native control did not pass')
        require('__CHECK__' in stdout and success_marker in stdout, 'Success/correctness markers missing')
    elif case == 'assertion_failure':
        require(metric['status'] == 'fail' and returncode != 0, 'Assertion failure was masked')
        require(metric['error_category'] == 'runtime', 'Deliberate assertion did not classify as runtime failure')
        require(SENTINEL in stderr and 'AssertionError' in stderr, 'Failure arose before the deliberate assertion')
        require('__CHECK__' in stdout, 'Assertion control did not emit the witness before failure')
        require(success_marker not in stdout, 'Failed program reached success marker')
    else:
        require(metric['status'] == 'fail' and returncode == 0, 'Witness omission did not execute successfully then fail the gate')
        require(metric['error_category'] == 'no-correctness-check', 'Wrong missing-witness classification')
        require('__CHECK__' not in stdout and success_marker in stdout, 'Witness omission control markers are wrong')
    return {'status': 'verified', 'native_status': metric['status'], 'native_category': metric['error_category'],
            'returncode': returncode, 'evidence': str(evidence), 'intercepted_provider_calls': provider.call_count,
            'actual_model_calls': 0, 'expected_outcome': case,
            'identity': [line for line in stdout.splitlines() if line.startswith('__IDENTITY__')]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toolkit', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--libraries', nargs='+', choices=list(APIS), default=list(APIS))
    parser.add_argument('--cases', nargs='+', choices=CASES, default=list(CASES))
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new check output directory; existing evidence is never replaced')
    args.output.mkdir(parents=True)
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg',
                      MPLCONFIGDIR=str(args.output / 'cache/matplotlib'),
                      NUMBA_CACHE_DIR=str(args.output / 'cache/numba'),
                      OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    launcher = load_launcher(args.toolkit.resolve())
    catalog = yaml.safe_load(args.catalog.read_text())
    summary = {'kind': 'offline_runtime_preflight_not_experiment', 'actual_model_calls': 0, 'libraries': {}}
    failed = False
    with patch('aideal.llm.invoke_text', side_effect=AssertionError('Unplanned provider invocation in offline preflight')):
        for name in args.libraries:
            row = summary['libraries'][name] = {'status': 'checking', 'cases': {}}
            try:
                spec = catalog[name]
                row['inputs'] = audit_inputs(name, spec, launcher)
                for case in args.cases:
                    row['cases'][case] = check_case(name, spec, case, args.output / name / case, launcher)
                    print(name, case, 'verified', flush=True)
                row['status'] = 'verified'
            except Exception as exc:
                failed = True
                row.update(status='failed', error_type=type(exc).__name__, error=str(exc))
                print(name, 'FAILED:', str(exc), flush=True)
            (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 2 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
