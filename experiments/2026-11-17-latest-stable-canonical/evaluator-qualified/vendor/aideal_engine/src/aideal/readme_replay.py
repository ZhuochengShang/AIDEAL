"""Explicit, hash-bound replay across a validation-only authoring revision.

No historical receipt is rewritten. A replay receipt contains references, not a
second provider usage record. The actual newly rendered request must match.
"""
from __future__ import annotations

import ast
import fcntl
import json
from pathlib import Path

from .readme_recording import atomic_json, digest
from .readme_validation import POLICY, validate_entry

_REVISED = {'readme_generation.py', 'readme_recording.py', 'doc_check_sources.py', 'doc_check_provenance.py',
            'readme_validation.py', 'readme_replay.py'}
_FIELDS = ('schema', 'model', 'scope', 'sample', 'manifest_sha256', 'source',
           'revision', 'effective_config_sha256', 'interpreter',
           'provider_settings', 'packages', 'authoring')


def _documentation_ast(data):
    class StripDocs(ast.NodeTransformer):
        def generic_visit(self, node):
            node = super().generic_visit(node)
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                    node.body = node.body[1:]
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                    node.func.attr in ('add_parser', 'add_argument')):
                for keyword in node.keywords:
                    if keyword.arg == 'help' and isinstance(keyword.value, ast.Constant):
                        keyword.value = ast.Constant(value='[help text]')
            return node
    return ast.dump(StripDocs().visit(ast.parse(data)), include_attributes=False)


def _label(path):
    marker = '/vendor/aideal_engine/src/aideal/'
    if marker in path:
        return 'engine/' + path.split(marker, 1)[1]
    if path.endswith('/scripts/run_readme_generation.py'):
        return 'launcher'
    return path


def compatible(previous, current):
    """Only validation/recording code may change; semantic inputs remain bound."""
    for field in _FIELDS:
        if previous.get(field) != current.get(field):
            raise ValueError('README replay incompatible: ' + field)
    maps, paths = [], []
    for identity in (previous, current):
        values, originals = {}, {}
        for row in identity['inputs']:
            label = _label(row['path'])
            if label in values and values[label] != row['sha256']:
                raise ValueError('Ambiguous README replay input binding')
            values[label] = row['sha256']
            originals[label] = row['path']
        maps.append(values)
        paths.append(originals)
    changed = []
    for label in sorted(set(maps[0]) | set(maps[1])):
        if maps[0].get(label) == maps[1].get(label):
            continue
        if label != 'launcher' and label not in {'engine/' + name for name in _REVISED}:
            if (label not in ('engine/api_discovery.py', 'engine/cli.py') or
                    label not in maps[0] or label not in maps[1] or
                    _documentation_ast(_checked(paths[0][label], maps[0][label])) !=
                    _documentation_ast(_checked(paths[1][label], maps[1][label]))):
                raise ValueError('README replay incompatible input: ' + label)
        changed.append({'path': label, 'previous_sha256': maps[0].get(label),
                        'current_sha256': maps[1].get(label)})
    return changed


def normalized(request):
    return {key: value for key, value in request.items() if key != 'binding'}


def _checked(path, expected):
    data = Path(path).read_bytes()
    if digest(data) != expected:
        raise ValueError('README replay evidence changed: ' + str(path))
    return data


def verify_replay_receipts(directory):
    for path in Path(directory).glob('*/replay_receipt.json'):
        for source, sha in json.loads(path.read_text())['files'].items():
            _checked(source, sha)


def prepare_replay(previous_root, destination, current):
    previous_root, destination = Path(previous_root).resolve(), Path(destination).resolve()
    if previous_root == destination:
        raise ValueError('A validation revision requires a new output namespace')
    old_path = previous_root / 'launch.json'
    old_bytes = old_path.read_bytes()
    old = json.loads(old_bytes)
    old_id = old['identity_sha256']
    if digest({k: v for k, v in old.items() if k != 'identity_sha256'}) != old_id:
        raise ValueError('Previous README launch identity changed')
    changes = compatible(old, current)
    plan_path = destination / 'inputs/replay_plan.json'
    # Do not even take a snapshot while the old namespace has a live author.
    with (previous_root.parent / '.lock').open('r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Previous README output still has an active worker') from exc
        if plan_path.exists():
            plan = json.loads(plan_path.read_text())
            if (plan['previous_launch'] != str(old_path) or
                    plan['previous_launch_sha256'] != digest(old_bytes) or
                    plan['revised_inputs'] != changes or plan['validation_policy'] != POLICY):
                raise ValueError('Prepared README replay plan changed')
        else:
            candidates = []
            for request_path in sorted((previous_root / 'author_calls').glob('*/attempt_*/request.json')):
                provider_path = request_path.with_name('provider.json')
                response_path = request_path.with_name('response.txt')
                if not provider_path.is_file() or not response_path.is_file():
                    continue
                request = json.loads(request_path.read_text())
                state = json.loads(provider_path.read_text())
                if request.get('binding') != old_id or state.get('request_sha256') != digest(request):
                    raise ValueError('Previous README request identity changed')
                action = ('replayed_complete' if state.get('status') == 'complete' else
                          'revalidated_returned_response' if
                          state.get('status') == 'failed_or_interrupted' and
                          state.get('error_type') == 'ValueError' and
                          (state.get('usage') or {}).get('calls', 0) >= 1 else None)
                if action is None:
                    continue
                response = response_path.read_bytes()
                if digest(response) != state.get('response_sha256'):
                    raise ValueError('Previous README response changed')
                candidates.append({'request_sha256': digest(normalized(request)), 'action': action,
                                   'files': {str(p): digest(p.read_bytes()) for p in
                                             (request_path, provider_path, response_path)}})
            plan = {'schema': 1, 'previous_launch': str(old_path),
                    'previous_launch_sha256': digest(old_bytes), 'previous_identity': old_id,
                    'validation_policy': POLICY, 'revised_inputs': changes, 'candidates': candidates}
            atomic_json(plan_path, plan)
    return plan_path, digest(plan_path.read_bytes())


class ReplayStore:
    def __init__(self, plan_path, plan_sha256, binding, output):
        self.plan = json.loads(_checked(plan_path, plan_sha256))
        _checked(self.plan['previous_launch'], self.plan['previous_launch_sha256'])
        self.binding, self.output = binding, Path(output)
        self.imported_calls = self.revalidated_calls = 0
        self.candidates = {}
        for candidate in self.plan['candidates']:
            self.candidates.setdefault(candidate['request_sha256'], []).append(candidate)

    def lookup(self, request, source_docs=()):
        identity = digest(normalized(request))
        for candidate in self.candidates.get(identity, []):
            files = {Path(path).name: _checked(path, sha) for path, sha in candidate['files'].items()}
            old = json.loads(files['request.json'])
            if normalized(old) != normalized(request):
                raise ValueError('README replay request changed')
            text = files['response.txt'].decode()
            try:
                validate_entry(text, request.get('api'), source_docs)
            except ValueError:
                continue  # A returned but still unfinished response is not reusable.
            receipt = {'schema': 1, 'binding': self.binding,
                       'previous_identity': self.plan['previous_identity'],
                       'validation_policy': POLICY, **candidate}
            path = self.output / identity / 'replay_receipt.json'
            if path.exists() and json.loads(path.read_text()) != receipt:
                raise ValueError('README replay receipt changed')
            if not path.exists():
                atomic_json(path, receipt)
            self.imported_calls += 1
            self.revalidated_calls += candidate['action'] == 'revalidated_returned_response'
            return text
        return None
