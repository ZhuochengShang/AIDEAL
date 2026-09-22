"""Construct a budgeted five-arm Codex config from real treatments/builds.

This does not freeze controls, invoke a provider, or execute library code.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile

import yaml

from build_backends import ARMS, HERE, bind, digest, installed_treatments, load

COMMON = {'temperature': 0, 'max_output_tokens': 2048, 'max_snippet_fixes': 1,
          'provider_attempt_limit': 1, 'provider_timeout_s': 150, 'execution_timeout_s': 180,
          'trial_ids': ['trial_01'], 'ordering_seed': 20260921,
          'documentation_max_characters': 8000, 'alias_max_characters': 2500,
          'hint_max_characters': 1500, 'source_access': False}


def provider_settings(study, model_adapter, python):
    """Pin provider implementation and ledger location, never mutable ledger bytes."""
    study = Path(study).resolve(strict=True)
    adapter = Path(model_adapter).resolve(strict=True)
    budget = adapter.with_name('provider_budget.py').resolve(strict=True)
    python = Path(python).resolve(strict=True)
    ledger = study / 'development/codex_budget_v1.json'
    return {'name': 'gpt-5.3-codex',
            # Equals form keeps the controller from hashing an existing mutable
            # ledger as though it were an immutable standalone command artifact.
            'command': [str(python), str(adapter), '--budget-ledger=' + str(ledger), '--max-cost-usd=5'],
            'artifacts': [str(adapter), str(budget)],
            'parameter_policy': {'requested_temperature_placeholder': 0,
                                 'temperature_sent_to_provider': False,
                                 'effective_temperature': 'provider_default_unspecified',
                                 'reasoning_effort': 'low', 'sdk_timeout_s': 120,
                                 'service_tier': 'default', 'max_cost_usd': 5.0,
                                 'shared_mutable_budget_ledger': str(ledger)}}


def config_from_builds(study, backends_path, model_adapter, python):
    study = Path(study).resolve(strict=True)
    attachment, application = installed_treatments(study)
    backends_path = Path(backends_path).resolve(strict=True)
    rows = load(backends_path)
    if set(rows) != set(ARMS):
        raise ValueError('Build summary must contain exactly the five treatment arms')
    model = provider_settings(study, model_adapter, python)
    python = Path(python).resolve(strict=True)
    previous = yaml.safe_load((study / 'refactor_pair_v2.yaml').read_text())['condition_evaluation']
    old_original = previous['conditions']['original']['documents']
    original_docs = [str(Path(p).resolve(strict=True)) for p in old_original]
    reused_readme = bind(study / 'development/existing_readme/README.md')
    if reused_readme['sha256'] != load(study / 'development/existing_readme/provenance.json')['sha256']:
        raise ValueError('The selected existing Generated README changed')
    conditions = {}
    for arm in ARMS:
        built, installed = rows[arm], application['arms'][arm]
        root = Path(attachment['worktrees'][arm]['path']).resolve(strict=True)
        if built['worktree'] != str(root) or built['revision'] != installed['commit_revision']:
            raise ValueError('Build does not match installed treatment: ' + arm)
        runtime = load(built['runtime'])
        identity = load(runtime['build_identity']['path'])
        if (bind(runtime['build_identity']['path']) != runtime['build_identity']
                or identity['sha256'] != built['build_sha256']
                or identity['sha256'] != digest({k: v for k, v in identity.items() if k != 'sha256'})):
            raise ValueError('Build summary identity changed: ' + arm)
        artifacts = built['source_artifacts']
        # Check existence and bind the actual files, never manufacture a hash.
        for path in artifacts:
            bind(path)
        documents = original_docs
        if arm in ('readme_only', 'combined'):
            readme = root / '.aideal/treatments/README.md'
            if bind(readme)['sha256'] != reused_readme['sha256']:
                raise ValueError('README treatment differs from the chosen existing artifact')
            documents = [str(readme)]
        condition = {'documents': documents,
                     'source': {'worktree': str(root), 'revision': built['revision'],
                                'branch': attachment['worktrees'][arm]['branch'], 'artifacts': artifacts},
                     'adapter': {'command': [str(python), str(HERE / 'execute.py'), built['runtime']],
                                 'artifacts': [str(HERE / p) for p in
                                     ('execute.py', 'build_backends.py', 'Harness.java', 'TraceRunner.java',
                                      'ClassOrigin.java')] + [built['runtime']]}}
        if arm in ('alias_only', 'combined'):
            condition['alias_interface'] = str(root / '.aideal/treatments/ALIASES.md')
        if arm in ('error_hints_only', 'combined'):
            condition['error_hints'] = str(root / '.aideal/treatments/error_hints.json')
        conditions[arm] = condition
    return {'condition_evaluation': {
        'schema_version': 1, 'design': 'five_arm', 'bank': previous['bank'],
        'api_function_ids': previous['api_function_ids'],
        'model': model,
        'common': copy.deepcopy(COMMON), 'development_case_ids': previous['development_case_ids'],
        'holdout_review': (
            'Reuse the existing eight held-out cases and 24 private fixtures without changes. '
            'Four microtasks and four puzzles, one trial in each of five conditions. '
            'Development proposals use separate development failures, never this bank. '
            'Reference/wrong-output/no-target controls must validate all five actual backends. '
            'Original/alias/hints conditions receive the original documentation; README/combined '
            'reuse the exact existing Generated README, which lacks dedicated readType sections. '
            'Canonical target IDs, oracles, model, repair/output budgets and per-channel caps are shared. '
            'Actual input lengths differ with the treatment and are recorded. Hints arrive only after '
            'a checked failure and matching public diagnostic. Reachability includes transitive calls '
            'and does not prove causal use in each fixture. This is a separate GPT-5.3-Codex pilot; '
            'do not pool its scores with Gemini or the earlier Pro refactor protocol. '
            'The controller temperature=0 is a compatibility placeholder, not a provider parameter: '
            'the adapter omits it and records the unspecified provider default. '
            'Development and audience inference share one USD5 reservation ledger; budget denial '
            'can stop incomplete work and is not a failed semantic check.'),
        'conditions': conditions}}


def prepare(study, backends, adapter, python, workflow_root, output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Preserve an existing configuration; choose a new output')
    config = config_from_builds(study, backends, adapter, python)
    sys.path.insert(0, str(Path(workflow_root).resolve(strict=True)))
    from workflow.condition_setup import read_condition_config
    from execute import validate_backend
    output.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(config, sort_keys=False)
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', dir=output.parent) as temporary:
        temporary.write(text); temporary.flush()
        payload = read_condition_config(temporary.name)
        for arm, backend in payload['backends'].items():
            validate_backend({'protocol': 'condition_evaluation_v1', 'backend': backend,
                              'target_apis': payload['bank']['api_names']},
                             config['condition_evaluation']['conditions'][arm]['adapter']['command'][2])
    # Read-only preflight passed; controls and model execution remain separate.
    with output.open('x') as stream:
        stream.write(text)
    return {'status': 'configured_not_frozen', 'config': bind(output),
            'units': 40, 'trusted_controls_required': 120,
            'maximum_audience_provider_attempts': 80,
            'shared_development_and_audience_budget_usd': 5.0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True)
    parser.add_argument('--backends', required=True)
    parser.add_argument('--model-adapter', required=True)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--workflow-root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.study, args.backends, args.model_adapter, args.python,
                             args.workflow_root, args.output), indent=2))
