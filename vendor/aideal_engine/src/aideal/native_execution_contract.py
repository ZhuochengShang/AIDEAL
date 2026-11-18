"""Versioned execution rules for independent native snippet attempts.

Output isolation prevents an earlier program from changing a later program's
fixtures. This is process/output hygiene, not containment of arbitrary code.
"""
from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import unquote, urlparse

NATIVE_EXECUTION_CONTRACT_VERSION = 'native-execution-v2'


def execution_contract(language: str) -> dict:
    """Publish the rules that distinguish corrected runs from historical scores."""
    return {
        'version': NATIVE_EXECUTION_CONTRACT_VERSION,
        'working_directory': 'per_attempt',
        'output_bindings': 'per_attempt',
        'correctness_witness': 'exact_target_stdout',
        'jvm_assertions': language.lower() in {'java', 'scala'},
        'python_fixture_scope': 'explicit_function_bindings' if language.lower() == 'python' else None,
    }


def assertion_environment(environment: dict, language: str, command: str = '') -> dict:
    """Enable assertions for child JVMs, including locally launched Spark JVMs.

    Keep the caller's environment untouched. Reject explicit disable switches
    instead of silently reporting correctness under a contradictory command.
    Remote Spark executors must receive their own -ea configuration; environment
    inheritance alone only certifies JVMs launched by this local process tree.
    """
    copied = dict(environment)
    if language.lower() not in {'java', 'scala'}:
        return copied
    switches = ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS',
                'SPARK_SUBMIT_OPTS', 'SPARK_JAVA_OPTS')
    disabled = re.compile(r'(?:^|[\s\"\'=])-(?:da|dsa|disableassertions|disablesystemassertions)(?=$|[\s\"\':])')
    if any(disabled.search(str(value)) for value in [command, *(copied.get(k, '') for k in switches)]):
        raise ValueError('Native execution requires JVM assertions; remove assertion-disabling options')
    copied['JAVA_TOOL_OPTIONS'] = (copied.get('JAVA_TOOL_OPTIONS', '').strip() + ' -ea').strip()
    # Preserve user-selected JVM options without changing the controller's env.
    return copied


def isolate_output_bindings(sample_data: dict, evidence_dir: Path,
                            placeholders: dict | None = None,
                            output_names: list[str] | None = None) -> tuple[dict, dict, dict]:
    """Rebind only declared outputs; source input paths retain exact identities.

    output_dir is the established native output binding. Additional writable
    sample-data names must be explicit in execute.output_bindings. Legacy
    OUTPUT_DIR / OUTPUT_PATH placeholders beneath that output root are rebased.
    """
    if output_names is not None and not isinstance(output_names, list):
        raise ValueError('execute.output_bindings must be a list of sample-data names')
    root = evidence_dir.resolve() / 'output'
    root.mkdir(parents=True, exist_ok=True)
    names = list(dict.fromkeys(['output_dir', *(output_names or [])]))
    sample = dict(sample_data)
    legacy = dict(placeholders or {})
    changes = []
    old_root = str(sample.get('output_dir', ''))
    old_local = unquote(urlparse(old_root).path) if old_root.startswith('file://') else old_root
    for name in names:
        if name not in sample:
            raise ValueError(f'Configured output binding is absent: {name}')
        old = str(sample[name])
        if name == 'output_dir':
            path = root
        else:
            local = unquote(urlparse(old).path) if old.startswith('file://') else old
            path = root / name / Path(local).name
            path.parent.mkdir(parents=True, exist_ok=True)
        new = path.as_uri() if old.startswith('file://') else str(path)
        sample[name] = new
        changes.append({'name': name, 'original': old, 'isolated': new})
    for key, value in legacy.items():
        if key.upper() not in {'OUTPUT_DIR', 'OUTPUT_PATH', 'OUTPUT_FILE'}:
            continue
        old = str(value)
        local = unquote(urlparse(old).path) if old.startswith('file://') else old
        try:
            relative = Path(local).relative_to(old_local) if old_local else None
        except ValueError:
            relative = None
        if relative is None:
            raise ValueError(f'Output placeholder {key} must be beneath the configured output_dir')
        path = root / relative
        new = path.as_uri() if old.startswith('file://') else str(path)
        legacy[key] = new
        changes.append({'name': key, 'original': old, 'isolated': new})
    receipt = {'version': NATIVE_EXECUTION_CONTRACT_VERSION, 'output_root': str(root),
               'bindings': changes, 'source_inputs_unchanged': True,
               'input_bindings': {key: str(value) for key, value in sample_data.items() if key not in names}}
    return sample, legacy, receipt


def rebind_output_text(text: str, receipt: dict) -> str:
    """Update configured output literals in the prompt and scaffold consistently."""
    # Protect source paths even when a historical fixture sits beneath the
    # old shared output directory. Only output references may be relocated.
    protected = []
    for value in sorted(set(receipt.get('input_bindings', {}).values()), key=len, reverse=True):
        variants = [value]
        if value.startswith('file://'):
            variants.append(unquote(urlparse(value).path))
        for original in variants:
            if original and original in text:
                token = f'__AIDEAL_PRESERVED_INPUT_{len(protected)}__'
                while token in text:
                    token += '_'
                text = text.replace(original, token)
                protected.append((token, original))
    # Longest first avoids swallowing an OUTPUT_PATH under OUTPUT_DIR.
    changes = sorted(receipt['bindings'], key=lambda row: len(row['original']), reverse=True)
    for row in changes:
        old, new = row['original'], row['isolated']
        if old:
            text = text.replace(old, new)
            if old.startswith('file://'):
                text = text.replace(unquote(urlparse(old).path), unquote(urlparse(new).path))
    for token, original in protected:
        text = text.replace(token, original)
    return text


def native_witness_present(stdout: str, api: str, marker: str = '__CHECK__') -> bool:
    """Require a nonempty witness for this exact API on its own stdout line.

    This proves only that the requested witness was emitted. Independent task
    checks are still necessary to establish that its claimed value is correct.
    """
    prefix = f'{marker} {api} '
    return any(line.startswith(prefix) and line[len(prefix):].strip()
               for line in (stdout or '').splitlines())


def native_check_passed(stdout: str, stderr: str, rc: int, api: str, ex: dict) -> bool:
    """Apply one native verdict consistently in fresh runs and saved replays."""
    out, err = stdout or '', stderr or ''
    success = ex.get('success_marker') or ''
    failure = ex.get('error_marker') or ''
    if rc != 0 or (success and success not in out) or (failure and failure in out + '\n' + err):
        return False
    return not ex.get('require_correctness') or native_witness_present(
        out, api, str(ex.get('check_marker') or '__CHECK__'))
