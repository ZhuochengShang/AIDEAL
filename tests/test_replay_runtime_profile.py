"""Real subprocess integration for recorded interpreter overrides, without LLMs."""
import hashlib
import json
from pathlib import Path
import shlex
import sys
from unittest.mock import patch

import pytest
from test_rescore_native_programs import setup_saved, r
from workflow.runtime_profile import load_runtime_profile, runtime_profile_receipts


def receipt(path):
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def runtime_fixture(tmp_path):
    wrapper = tmp_path / 'isolated-wrapper-python'
    wrapper.write_text('#!/bin/sh\nprintf "RUNTIME_PROFILE_EXECUTED\\n"\nexec ' + shlex.quote(sys.executable) + ' "$@"\n')
    wrapper.chmod(0o755)
    dependency = tmp_path / 'dependency.py'
    dependency.write_text('VERSION = 1\n')
    environment = tmp_path / 'environment.json'
    environment.write_text(json.dumps({'file_bindings': [receipt(wrapper), receipt(dependency)]}))
    setup = tmp_path / 'setup.json'
    # Offline rescoring must remain available even when new paid work is blocked.
    setup.write_text(json.dumps({'unresolved_setup': ['integration-only missing external fixture']}))
    profile = tmp_path / 'runtime-profile.json'
    profile.write_text(json.dumps({'schema': 1,
        'command_replacements': {sys.executable: str(wrapper)},
        'environment_manifest': receipt(environment), 'setup_report': receipt(setup)}))
    return profile, wrapper, dependency


def test_replay_executes_selected_runtime_and_retains_verified_receipts(tmp_path):
    source = setup_saved(tmp_path, {'f': 'x = x + 1\nassert x == 2\nprint("__CHECK__ f 2")'})
    profile, wrapper, _ = runtime_fixture(tmp_path)
    destination = tmp_path / 'replay/f'
    with patch('aideal.llm.invoke_text', side_effect=AssertionError('Provider access forbidden')):
        result = r.run_program_case(source, 'f', destination, runtime_profile=str(profile))
    assert result['status'] == 'pass'
    assert result['llm_calls'] == 0
    assert 'RUNTIME_PROFILE_EXECUTED' in result['stdout_tail']
    identity = json.loads((destination / 'replay_identity.json').read_text())
    assert identity['runtime_profile'] == runtime_profile_receipts(load_runtime_profile(profile))
    execution = json.loads((Path(result['scala_file']).parent / 'execution.json').read_text())
    assert str(wrapper) in execution['command']
    assert r.run_program_case(source, 'f', destination, runtime_profile=str(profile)) == result


def test_replay_rejects_changed_profile_and_dependency_before_reuse(tmp_path):
    source = setup_saved(tmp_path, {'f': 'print("__CHECK__ f ok")'})
    profile, _, dependency = runtime_fixture(tmp_path)
    destination = tmp_path / 'replay/f'
    r.run_program_case(source, 'f', destination, runtime_profile=str(profile))
    raw = profile.read_text()
    profile.write_text(raw + '\n')
    with pytest.raises(ValueError, match='Prepared evidence changed'):
        r.run_program_case(source, 'f', destination, runtime_profile=str(profile))
    profile.write_text(raw)
    dependency.write_text('VERSION = 2\n')
    with pytest.raises(ValueError, match='Runtime evidence changed'):
        r.run_program_case(source, 'f', destination, runtime_profile=str(profile))
