"""Compile source-bound RDPro overlays outside every attached Git checkout.

No dependency download, provider request, hook, or library checkout mutation.
The explicit dependency set is copied from an existing pinned runtime manifest.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
PACKAGE = 'cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/'
SOURCES = tuple(PACKAGE + name + '.scala' for name in ('Feature', 'RasterSchemaHelper', 'RasterMetadata'))
CLASSES = ('edu.ucr.cs.bdlab.beast.geolite.Feature$',
           'edu.ucr.cs.bdlab.beast.geolite.RasterSchemaHelper$',
           'edu.ucr.cs.bdlab.beast.geolite.RasterMetadata')
ARMS = ('original', 'readme_only', 'alias_only', 'error_hints_only', 'combined')


def load(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def bind(path):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as stream:
        h = hashlib.file_digest(stream, 'sha256') if hasattr(hashlib, 'file_digest') else None
        if h is None:
            h = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1048576), b''):
                h.update(chunk)
    return {'path': str(path), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def command(args, directory, name, timeout=120):
    with (directory / (name + '.stdout')).open('w') as out, (directory / (name + '.stderr')).open('w') as err:
        result = subprocess.run(args, stdout=out, stderr=err, cwd=directory, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{name} failed; inspect {directory / (name + ".stderr")}')
    return args


def jar(directory, target):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(directory.rglob('*.class')):
            info = zipfile.ZipInfo(p.relative_to(directory).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            archive.writestr(info, p.read_bytes())


def installed_treatments(study):
    """Require a real complete installation before building the five-arm study."""
    study = Path(study).resolve(strict=True)
    attachment = load(study / 'attachment.json')
    pointer_path = study / 'treatments/current.json'
    if not pointer_path.is_file():
        raise ValueError('Five-arm builds require installed README, Scala aliases and error hints')
    pointer = load(pointer_path)
    version = pointer.get('proposal_sha256', '')
    if len(version) != 64 or any(c not in '0123456789abcdef' for c in version):
        raise ValueError('Invalid treatment version identity')
    application = load(study / 'treatments' / version / 'application.json')
    if (digest(application) != pointer.get('application_sha256')
            or application.get('status') != 'applied_unvalidated'
            or application.get('baseline_revision') != attachment['revision']
            or application.get('proposal_sha256') != version):
        raise ValueError('Treatment application identity does not match the study')
    expected = {'original': set(), 'readme_only': {'readme'},
                'alias_only': {'alias', 'alias_interface'},
                'error_hints_only': {'error_hints'},
                'combined': {'readme', 'alias', 'alias_interface', 'error_hints'}}
    if set(application.get('arms', {})) != set(ARMS):
        raise ValueError('Treatment application must cover exactly the five attachment arms')
    for arm in ARMS:
        row, attached = application['arms'][arm], attachment['worktrees'][arm]
        root = Path(attached['path']).resolve(strict=True)
        if (str(root) != row['path'] or git(root, 'rev-parse', 'HEAD') != row['commit_revision']
                or git(root, 'branch', '--show-current') != attached['branch']):
            raise ValueError('Installed treatment checkout changed: ' + arm)
        if {r['role'] for r in row['files'].values()} != expected[arm]:
            raise ValueError('Missing or mixed treatment artifacts: ' + arm)
        for name, ref in row['files'].items():
            if ref['role'] == 'alias' and not name.endswith('.scala'):
                raise ValueError('This RDPro build recipe supports Scala alias modules only')
            observed = bind(root / name)
            if any(observed[k] != ref[k] for k in ('sha256', 'bytes')):
                raise ValueError('Installed treatment bytes changed: ' + arm + '/' + name)
    if application['arms']['original']['commit_revision'] != attachment['revision']:
        raise ValueError('Original must retain the attached baseline revision')
    return attachment, application


def overlay_class_names(directory):
    """Probe every emitted class, including newly compiled aliases, without initialization."""
    names = sorted(p.relative_to(directory).with_suffix('').as_posix().replace('/', '.')
                   for p in directory.rglob('*.class'))
    if not set(CLASSES) <= set(names):
        raise ValueError('Compiled overlay is missing measured RDPro classes')
    return names


def build_one(root, output, runtime=None, baseline=None):
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    if output == root or root in output.parents:
        raise ValueError('Build outside the source checkout')
    if output.exists():
        raise ValueError('Preserve existing build evidence; choose a new output')
    revision = git(root, 'rev-parse', 'HEAD')
    runtime = load(HERE / 'runtime.json') if runtime is None else runtime
    sources = [root / p for p in SOURCES]
    # Only new Scala files are eligible aliases. The caller's frozen controller
    # separately verifies that alias-only did not edit any original code file.
    if baseline:
        added = git(root, 'diff', '--name-only', '--diff-filter=A', baseline, revision).splitlines()
        sources += [root / p for p in added if p.endswith('.scala') and not p.startswith('.aideal/')]
    helper = HERE / 'public_helpers/StudySupport.scala'
    required = list(dict.fromkeys([runtime['java'], runtime['javac'], *runtime['jars']]))
    inputs = {'source': [bind(p) for p in sources], 'helper': bind(helper),
              'dependencies': [bind(p) for p in required], 'builder': bind(__file__)}
    output.mkdir(parents=True)
    classes, helpers = output / 'library_classes', output / 'helper_classes'
    classes.mkdir(); helpers.mkdir()
    cp = ':'.join(runtime['jars'])
    compile_prefix = [runtime['java'], '-cp', cp, 'scala.tools.nsc.Main']
    commands = [command(compile_prefix + ['-classpath', cp, '-d', str(classes), *map(str, sources)], output, 'library_compile')]
    overlay = output / 'library_overlay.jar'
    jar(classes, overlay)
    commands.append(command(compile_prefix + ['-classpath', str(overlay) + ':' + cp,
                                             '-d', str(helpers), str(helper)], output, 'helper_compile'))
    helper_jar = output / 'public_helpers.jar'
    jar(helpers, helper_jar)
    probe = output / 'probe_classes'; probe.mkdir()
    commands.append(command([runtime['javac'], '-d', str(probe), str(HERE / 'ClassOrigin.java')], output, 'origin_compile'))
    actual_cp = ':'.join([str(overlay), str(helper_jar), str(probe), *runtime['jars']])
    expected_classes = overlay_class_names(classes)
    commands.append(command([runtime['java'], '-cp', actual_cp, 'ClassOrigin', *expected_classes], output, 'class_origins'))
    origins = {}
    for line in (output / 'class_origins.stdout').read_text().splitlines():
        name, location = line.split('\t', 1)
        if Path(location).resolve() != overlay:
            raise ValueError('Pinned source was shadowed by another library: ' + line)
        origins[name] = location
    if set(origins) != set(expected_classes):
        raise ValueError('Incomplete classloader origin evidence')
    if git(root, 'rev-parse', 'HEAD') != revision or any(bind(r['path']) != r for r in inputs['source']):
        raise ValueError('Sources changed during build')
    identity = {'schema_version': 1, 'worktree': str(root), 'revision': revision,
                'tree': git(root, 'rev-parse', 'HEAD^{tree}'), 'inputs': inputs, 'commands': commands,
                'overlay': bind(overlay), 'helper': bind(helper_jar), 'class_origins': origins,
                'class_hashes': {p.relative_to(classes).as_posix(): bind(p)['sha256'] for p in sorted(classes.rglob('*.class'))}}
    identity['sha256'] = digest(identity)
    save(output / 'build_identity.json', identity)
    config = {'java': runtime['java'], 'javac': runtime['javac'], 'compiler_jars': runtime['jars'],
              'runtime_jars': runtime['jars'], 'overlay': str(overlay), 'helper': str(helper_jar),
              'build_identity': bind(output / 'build_identity.json'), 'worktree': str(root), 'revision': revision}
    save(output / 'runtime.json', config)
    artifacts = [str(output / 'runtime.json'), str(output / 'build_identity.json'), str(overlay), str(helper_jar),
                 *required, *(str(HERE / p) for p in ('execute.py', 'Harness.java', 'TraceRunner.java', 'ClassOrigin.java', 'build_backends.py')),
                 str(helper)]
    return {'runtime': str(output / 'runtime.json'), 'source_artifacts': list(dict.fromkeys(artifacts)),
            'worktree': str(root), 'revision': revision, 'build_sha256': identity['sha256']}


def build_backends(study, output):
    """Build only the five installed treatment arms; never include refactor_only."""
    study, output = Path(study).resolve(strict=True), Path(output).resolve()
    attachment, application = installed_treatments(study)
    conditions = {arm: attachment['worktrees'][arm]['path'] for arm in ARMS}
    output.mkdir(parents=True, exist_ok=False)
    results = {arm: build_one(root, output / arm, baseline=attachment['revision']) for arm, root in conditions.items()}
    if installed_treatments(study)[1] != application:
        raise ValueError('Treatment installation changed during builds; retain this build evidence')
    save(output / 'backends.json', results)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build_backends(args.study, args.output), indent=2))
