"""Optional, source-attested alias removal for an existing complete SQL registry."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess

POLICY_VERSION = 'registered_sql_explicit_aliases_v1'


def canonical_sql_details(cfg, data, details):
    fields = ('canonical_selection', 'canonical_selection_sha256',
              'canonical_selection_policy_version', 'canonical_registered_names')
    if not any(field in data for field in fields):
        return details
    if not all(field in data for field in fields) or data['canonical_selection_policy_version'] != POLICY_VERSION:
        raise ValueError('SQL canonical selection requires a complete supported binding')
    from .api_registry import _bound_json
    receipt = _bound_json(cfg, data, 'canonical_selection')
    names = sorted(row['name'].lower() for row in details)
    names_sha = hashlib.sha256(json.dumps(names, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if (receipt.get('schema') != 1 or receipt.get('kind') != 'registered_sql_canonical_selection'
            or receipt.get('policy_version') != POLICY_VERSION or receipt.get('source_revision') != data.get('source_revision')
            or receipt.get('registered_names') != names or receipt.get('registered_names_sha256') != names_sha):
        raise ValueError('SQL alias receipt differs from the complete registered surface')
    def relative(value):
        path = Path(value)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Invalid SQL alias source path')
        return path
    root = (cfg.root / relative(receipt['source_root'])).resolve()
    def git(*args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError('Cannot verify SQL source identity')
        return result.stdout.strip()
    if (git('rev-parse', 'HEAD') != receipt['source_revision']
            or git('rev-parse', 'HEAD^{tree}') != receipt.get('source_tree')
            or git('status', '--porcelain', '--untracked-files=no')):
        raise ValueError('SQL alias source checkout differs from its pinned clean revision')
    texts, hashes = {}, {}
    for binding in receipt.get('source_evidence', []):
        path = root / relative(binding['path'])
        if not path.resolve().is_relative_to(root) or binding['path'] in texts:
            raise ValueError('Invalid or duplicate SQL source evidence')
        raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
        if digest != binding.get('sha256'):
            raise ValueError('SQL alias source evidence changed')
        texts[binding['path']] = raw.decode('utf-8'); hashes[binding['path']] = digest
    aliases = {}
    for edge in receipt.get('aliases', []):
        alias, canonical = edge.get('alias'), edge.get('canonical')
        if (alias not in names or canonical not in names or alias == canonical or alias in aliases
                or edge.get('relationship') != 'explicit_udf_with_aliases'
                or edge.get('path') not in texts or edge.get('file_sha256') != hashes[edge['path']]):
            raise ValueError('Invalid explicit SQL alias edge')
        text = texts[edge['path']]; start, end = edge.get('start'), edge.get('end')
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
            raise ValueError('Invalid SQL alias proof span')
        proof = text[start:end]
        groups = re.findall(r'\.with_aliases\(vec!\[(.*?)\]\)', proof, re.S)
        if (hashlib.sha256(proof.encode()).hexdigest() != edge.get('source_span_sha256')
                or '"' + canonical + '"' not in proof
                or not any('"' + alias + '"' in group for group in groups)):
            raise ValueError('SQL alias proof does not match its source span')
        aliases[alias] = canonical
    if any(canonical in aliases for canonical in aliases.values()):
        raise ValueError('SQL alias targets must be direct retained canonical operations')
    expected = sorted(set(names) - set(aliases))
    selected = data['canonical_registered_names']
    if (receipt.get('selected_names') != expected or not isinstance(selected, list)
            or len(selected) != len(set(selected)) or sorted(selected) != expected):
        raise ValueError('Selected SQL names must exactly equal the registry minus proven aliases')
    unbounded = receipt.get('unbounded_names', [])
    if not set(unbounded) <= set(expected):
        raise ValueError('Unbounded SQL operation is outside the selected registry')
    by_name = {row['name'].lower(): row for row in details}
    result = []
    for name in expected:
        row = deepcopy(by_name[name])
        row.update(site_id='SQL:' + name, target_kind='registered_sql',
                   parameter_count_status='unbounded_variadic' if name in unbounded else 'user_defined_runtime_signature')
        result.append(row)
    return result
