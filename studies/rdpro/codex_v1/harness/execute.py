"""RDPro condition checker: source-bound JVM routing, numeric oracle, JDI calls.

The model writes only a solve(Array[Double]):Array[Double] body. Oracle expected
values remain in this parent checker. Java17 harness restrictions are defense
in depth, not an OS sandbox or a proof against adversarial generated programs.
"""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote, urlparse

from build_backends import bind, digest, git, load

HERE = Path(__file__).resolve().parent
CHILD_ENV = {k: v for k, v in os.environ.items()
             if not any(word in k.upper() for word in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL'))}
TARGETS = {'edu.ucr.cs.bdlab.beast.geolite.' + item for item in
           ('Feature.readType', 'RasterSchemaHelper.readType', 'RasterMetadata.rescale', 'RasterMetadata.numTiles')}
PREFIX = 'edu.ucr.cs.bdlab.beast.geolite.'
TARGET_EVENTS = {
    PREFIX + 'Feature.readType': PREFIX + 'Feature$.readType(Ljava/io/ObjectInput;)Lorg/apache/spark/sql/types/DataType;',
    PREFIX + 'RasterSchemaHelper.readType': PREFIX + 'RasterSchemaHelper$.readType(Ljava/io/ObjectInput;)Lorg/apache/spark/sql/types/DataType;',
    PREFIX + 'RasterMetadata.rescale': PREFIX + 'RasterMetadata.rescale(II)Ledu/ucr/cs/bdlab/beast/geolite/RasterMetadata;',
    PREFIX + 'RasterMetadata.numTiles': PREFIX + 'RasterMetadata.numTiles()I'}


def validate_backend(request, runtime_path):
    runtime = load(runtime_path)
    backend = request['backend']
    if request.get('protocol') != 'condition_evaluation_v1' or not set(request['target_apis']) <= TARGETS:
        raise ValueError('Unsupported condition protocol or canonical API target')
    if not request['target_apis'] or backend.get('sha256') != digest({k: v for k, v in backend.items() if k != 'sha256'}):
        raise ValueError('Malformed backend receipt request')
    root = Path(runtime['worktree']).resolve(strict=True)
    if (str(root) != backend['worktree'] or runtime['revision'] != backend['revision']
            or git(root, 'rev-parse', 'HEAD') != backend['revision']
            or git(root, 'rev-parse', 'HEAD^{tree}') != backend['tree']):
        raise ValueError('Configured RDPro backend does not match requested checkout')
    if bind(runtime['build_identity']['path']) != runtime['build_identity']:
        raise ValueError('Build identity file changed')
    build = load(runtime['build_identity']['path'])
    if (build.get('sha256') != digest({k: v for k, v in build.items() if k != 'sha256'})
            or build['worktree'] != str(root) or build['revision'] != backend['revision']):
        raise ValueError('Build identity does not match source checkout')
    refs = [*build['inputs']['source'], *build['inputs']['dependencies'], build['inputs']['helper'],
            build['inputs']['builder'], build['overlay'], build['helper']]
    if any(bind(r['path']) != r for r in refs):
        raise ValueError('Compiled source, dependency or backend binary changed')
    requested = {r['path']: r for r in backend['source_artifacts']}
    required = [bind(runtime_path), runtime['build_identity'], *build['inputs']['dependencies'],
                build['overlay'], build['helper'], build['inputs']['helper'], build['inputs']['builder'],
                *(bind(HERE / name) for name in ('execute.py', 'Harness.java', 'TraceRunner.java', 'ClassOrigin.java'))]
    if any(requested.get(r['path']) != r for r in required):
        raise ValueError('Runtime inputs are not completely bound by the frozen backend')
    if runtime['overlay'] != build['overlay']['path'] or runtime['helper'] != build['helper']['path']:
        raise ValueError('Runtime overlay differs from proven build')
    dependency_paths = {r['path'] for r in build['inputs']['dependencies']}
    if any(p not in dependency_paths for p in [runtime['java'], runtime['javac'], *runtime['compiler_jars'], *runtime['runtime_jars']]):
        raise ValueError('Unbound compiler/runtime dependency')
    return runtime, build, backend['sha256']


def command(args, prefix, timeout=60):
    with open(prefix + '.stdout', 'w') as out, open(prefix + '.stderr', 'w') as err:
        result = subprocess.run(args, stdout=out, stderr=err, timeout=timeout, env=CHILD_ENV)
    return result.returncode


def observed_program(args, target, stdout, stderr):
    # Keep the controller's process group; terminate the observer gracefully on
    # the shorter internal timeout so its shutdown hook also stops the child.
    process = subprocess.Popen(args, cwd=target, stdout=stdout, stderr=stderr, env=CHILD_ENV)
    try:
        return process.wait(timeout=45)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()
        raise


def check_outputs(oracle, stdout, trace, targets, returncode):
    if not oracle.get('tests') or not targets:
        raise ValueError('Nonempty oracle fixtures and targets required')
    reached = all(TARGET_EVENTS.get(target) in trace for target in targets)
    marked = [s.split('=', 1)[1] for s in stdout.splitlines() if s.startswith('AIDEAL_RESULT=')]
    outcomes = []
    for index, test in enumerate(oracle['tests']):
        actual = None
        try:
            if len(marked) == len(oracle['tests']):
                actual = json.loads(marked[index])
        except ValueError:
            pass
        correct = (returncode == 0 and isinstance(actual, list) and len(actual) == len(test['expected'])
                   and all(type(x) in (int, float) and math.isfinite(x)
                           and math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-8)
                           for x, y in zip(actual, test['expected'])))
        outcomes.append({'execution_pass': returncode == 0, 'oracle_pass': correct,
                         'target_reached': reached, 'actual': actual})
    verdict = {key: all(row[key] for row in outcomes) for key in ('execution_pass', 'oracle_pass', 'target_reached')}
    verdict['public_feedback'] = ('Independent numerical and required-library-call checks passed.' if all(verdict.values()) else
                                  'Independent numerical or required-library-call checks failed. Review the public task contract and implementation.')
    return verdict, outcomes


def verify_class_loading(log, build, trace):
    loaded = {}
    for line in log.splitlines():
        if '] ' not in line or ' source: ' not in line:
            continue
        name, source = line.split('] ')[-1].split(' source: ', 1)
        loaded[name] = source
    expected = Path(build['overlay']['path']).resolve()
    target_classes = {entry.split('(', 1)[0].rsplit('.', 1)[0] for entry in trace}
    for name in target_classes:
        source = urlparse(loaded.get(name, ''))
        if source.scheme != 'file' or Path(unquote(source.path)).resolve() != expected:
            raise ValueError('Observed target method was loaded outside the pinned overlay: ' + name)
    return {name: loaded.get(name) for name in sorted(target_classes)}


def publish(verdict, receipt, work):
    """Pin every raw candidate/checker artifact used to reach this verdict."""
    paths = [work / 'Solution.scala', work / 'compile.stdout', work / 'compile.stderr']
    if (work / 'checks.json').exists():
        paths += [work / name for name in ('harness.stdout', 'harness.stderr', 'checks.json', 'backend_evidence.json')]
        paths += [work / 'program' / name for name in ('debugger.stdout', 'debugger.stderr', 'program.stdout',
                                                       'program.stderr', 'trace.txt', 'classload.log')]
    paths += sorted((work / 'classes').rglob('*.class'))
    verdict['adjudication_artifacts'] = [bind(path) for path in paths]
    verdict['backend_sha256'] = receipt
    print(json.dumps(verdict))


def main():
    request = json.load(sys.stdin)
    runtime, build, receipt = validate_backend(request, Path(sys.argv[1]).resolve())
    work = Path.cwd(); classes = work / 'classes'; classes.mkdir()
    cp = ':'.join([runtime['overlay'], runtime['helper'], *runtime['compiler_jars']])
    solution = 'object Solution { def solve(v: Array[Double]): Array[Double] = {\n' + request['code'] + '\n} }\n'
    (work / 'Solution.scala').write_text(solution)
    compiled = command([runtime['java'], '-cp', cp, 'scala.tools.nsc.Main', '-classpath', cp,
                        '-d', str(classes), str(work / 'Solution.scala')], 'compile')
    if compiled:
        publish({'execution_pass': False, 'oracle_pass': False, 'target_reached': False,
                 'public_feedback': (work / 'compile.stderr').read_text()}, receipt, work)
        return
    # Pinned library/helper classes precede generated classes, preventing a
    # candidate class with a trusted name from replacing a measured target.
    run_cp = ':'.join([runtime['overlay'], runtime['helper'], str(classes), *runtime['runtime_jars']])
    if command([runtime['javac'], '-cp', run_cp, '-d', str(classes), str(HERE / 'Harness.java'),
                str(HERE / 'TraceRunner.java')], 'harness'):
        raise RuntimeError('Trusted harness compilation failed; inspect harness.stderr')
    oracle = load(request['oracle_path'])
    target = work / 'program'; target.mkdir()
    with (target / 'debugger.stdout').open('w') as stdout, (target / 'debugger.stderr').open('w') as stderr:
        returncode = observed_program([runtime['java'], '-cp', str(classes), 'TraceRunner', run_cp,
                                      ';'.join(','.join(map(str, t['input'])) for t in oracle['tests'])],
                                     target, stdout, stderr)
    if not (target / 'trace.txt').exists():
        raise RuntimeError('JVM observer failed before producing a trace')
    trace = (target / 'trace.txt').read_text().splitlines()
    origins = verify_class_loading((target / 'classload.log').read_text(), build, trace)
    verdict, outcomes = check_outputs(oracle, (target / 'program.stdout').read_text(), trace,
                                     request['target_apis'], returncode)
    (work / 'checks.json').write_text(json.dumps(outcomes, indent=2) + '\n')
    (work / 'backend_evidence.json').write_text(json.dumps({'backend_sha256': receipt,
        'build_sha256': build['sha256'], 'class_origins': origins, 'raw_trace': trace}, indent=2) + '\n')
    if bind(runtime['overlay']) != build['overlay'] or bind(runtime['helper']) != build['helper']:
        raise ValueError('Measured binary changed during candidate execution')
    publish(verdict, receipt, work)


if __name__ == '__main__':
    main()
