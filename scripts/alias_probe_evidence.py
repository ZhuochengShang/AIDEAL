"""Small immutable-file/Git checks used by the independent development probes."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile


def load(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def bind(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file(): raise ValueError('Expected regular file')
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return {'path': str(path), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def verified(ref):
    if (not isinstance(ref, dict) or set(ref) != {'path', 'sha256', 'bytes'}
            or not isinstance(ref['path'], str) or not Path(ref['path']).is_absolute()
            or type(ref['bytes']) is not int or ref['bytes'] < 0
            or str(Path(ref['path']).resolve()) != ref['path'] or bind(ref['path']) != ref):
        raise ValueError('Changed or malformed evidence binding')
    return Path(ref['path'])


def core_ref(value):
    return {k: value[k] for k in ('path', 'sha256', 'bytes')}


def relative_path(root, name):
    if (not isinstance(name, str) or '\\' in name or PurePosixPath(name).is_absolute()
            or any(p in ('', '.', '..', '.git') for p in name.split('/'))):
        raise ValueError('Unsafe relative source path')
    root = Path(root).resolve(strict=True); result = root / name
    cursor = root
    for part in name.split('/'):
        cursor /= part
        if cursor.is_symlink(): raise ValueError('Symlink in source path')
    return result


def save(path, value):
    path = Path(path)
    data = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary,path)  # Exclusive publication: never replace old evidence.
    finally:
        os.unlink(temporary)
    return bind(path)


def git(root, *args, binary=False):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS='0')
    value = subprocess.check_output(['git', '-C', str(root), '-c', 'core.hooksPath=/dev/null',
        '-c', 'core.fsmonitor=false', '-c', 'gc.auto=0', '--literal-pathspecs', *args], env=env)
    return value if binary else value.decode().strip()


def verify_checkout(receipt):
    """Read raw files and Git objects; no clean filters, hooks or index mutations."""
    if digest({k:v for k,v in receipt.items() if k != 'sha256'}) != receipt['sha256']:
        raise ValueError('Backend receipt digest differs')
    root = Path(receipt['worktree']).resolve(strict=True)
    if (git(root, 'rev-parse', 'HEAD') != receipt['revision']
            or git(root, 'rev-parse', 'HEAD^{tree}') != receipt['tree']
            or git(root, 'branch', '--show-current') != receipt['branch']):
        raise ValueError('Backend checkout identity changed')
    code = {}
    for row in git(root, 'ls-tree', '-rz', 'HEAD', binary=True).split(b'\0'):
        if not row: continue
        fields, name = row.decode().split('\t', 1)
        mode, kind, blob = fields.split()
        if name.startswith('.aideal/treatments/'): continue
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Unsupported linked/submodule source entry')
        path = relative_path(root, name); data = path.read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != blob or ('100755' if path.stat().st_mode & 0o111 else '100644') != mode:
            raise ValueError('Raw backend source changed: ' + name)
        code[name] = [mode, blob]
    if code != receipt['code_files'] or digest(code) != receipt['code_tree_sha256']:
        raise ValueError('Backend tracked code identity differs')
    for ref in receipt['source_artifacts'] + receipt['adapter_artifacts']: verified(ref)
    return root


def verify_runtime(backend, receipt, aliases, trace_runner):
    root = verify_checkout(receipt)
    runtime = load(backend['runtime']); build = load(verified(runtime['build_identity']))
    if digest({k:v for k,v in build.items() if k != 'sha256'}) != build['sha256']:
        raise ValueError('Build digest differs')
    for value in (backend, runtime, build):
        if value['worktree'] != str(root) or value['revision'] != receipt['revision']:
            raise ValueError('Runtime source identity differs')
    if build['tree'] != receipt['tree'] or build['sha256'] != backend['build_sha256']:
        raise ValueError('Runtime build identity differs')
    inputs = build['inputs']
    refs = [*inputs['source'], inputs['helper'], inputs['builder'], *inputs['dependencies'],
            build['overlay'], build['helper'], runtime['build_identity']]
    for ref in refs: verified(ref)
    permitted = {r['path']: r for r in inputs['dependencies']}
    for path in [runtime['java'], runtime['javac'], *runtime['compiler_jars'], *runtime['runtime_jars']]:
        if bind(path) != permitted.get(str(Path(path).resolve())):
            raise ValueError('Unbound compiler/runtime dependency')
    for name in ('overlay', 'helper'):
        if bind(runtime[name]) != build[name]: raise ValueError('Runtime classpath differs')
    source_inputs = {r['path']:r for r in inputs['source']}
    for ref in aliases:
        installed = bind(relative_path(root, ref['target']))
        if any(installed[k] != ref[k] for k in ('sha256', 'bytes')) or source_inputs.get(installed['path']) != installed:
            raise ValueError('Installed/compiled aliases differ from proposal')
    if bind(trace_runner) not in receipt['source_artifacts'] + receipt['adapter_artifacts']:
        raise ValueError('TraceRunner is not bound by configured backend')
    return runtime, build
