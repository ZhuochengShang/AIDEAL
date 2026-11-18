"""Versioned, content-based inputs omitted by historical native fingerprints."""
import hashlib
import json
import os
from pathlib import Path

from .prompts import DEFAULT_PROMPTS, prompts_dir
from .profile import profile_path


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def prompt_contract(cfg):
    result = {}
    for name in ('comprehension_write_exec',):
        path = prompts_dir(cfg) / f'aideal/{name}.md'
        if not path.exists():
            path = DEFAULT_PROMPTS / f'aideal/{name}.md'
        result[name] = digest(path.read_bytes())
    profile = profile_path(cfg)
    return {'templates': result,
            'profile_sha256': digest(profile.read_bytes()) if profile.exists() else None}


def transport_contract():
    timeout = float(os.environ.get('AIDEAL_GOOGLE_REQUEST_TIMEOUT_S', '300'))
    attempts = int(os.environ.get('AIDEAL_GOOGLE_MAX_RETRIES', '2'))
    if timeout <= 0 or attempts < 1:
        raise ValueError('Invalid provider deadline or SDK-attempt count')
    return {'temperature': 0.0, 'google_request_timeout_s': timeout,
            'google_sdk_attempts': attempts, 'google_outer_deadline_s': timeout * attempts + 30,
            'adapter_sha256': os.environ.get('AIDEAL_TRANSPORT_ADAPTER_SHA256'),
            'policy_sha256': os.environ.get('AIDEAL_TRANSPORT_POLICY_SHA256'),
            'setup_policy_sha256': os.environ.get('AIDEAL_SETUP_POLICY_SHA256')}


def extra_components(cfg):
    return {'prompt_contract': prompt_contract(cfg), 'transport_contract': transport_contract()}


def write_run_identity(path, components):
    """Publish active identity before the first API; readers need no legacy alias."""
    record = {'schema': 1, 'experiment_fingerprint': digest_native(components),
              'fingerprint_components': components}
    path = Path(path)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(record, indent=2) + '\n')
    temporary.replace(path)


def digest_native(components):
    return hashlib.sha256(json.dumps(components, sort_keys=True, separators=(',', ':'),
                                     default=str).encode()).hexdigest()
