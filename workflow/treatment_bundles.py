"""Combine bounded model proposals without concatenating executable source files."""
import json
from pathlib import Path
import shutil

from .ablation import bind, digest, load, verify_artifact
from .execution import atomic_json
from .treatment_versions import _artifact_role, _read_proposal


def bundle_proposals(proposals, output, *, readme=None, include_legacy_hints=False):
    """Produce a complete multi-file version; installation remains a separate step.

    Inputs are exact per-batch proposal paths. Earlier library versions are not
    implicitly included: provide every batch to retain in this complete bundle.
    README/aliases are installable by default. Legacy JSON hint candidates remain
    recorded but require explicit opt-in; native hints use separate validation.
    """
    # Check that the selected batches refer to one baseline. Write separate alias
    # source files, their combined interface, and any selected README or legacy hints.
    if not proposals:
        raise ValueError('Supply at least one per-batch proposal')
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise FileExistsError('Bundle output already exists')
    sources = [Path(p).expanduser().resolve(strict=True) for p in proposals]
    if len(set(sources)) != len(sources):
        raise ValueError('Duplicate proposal path')
    baseline = load(sources[0]).get('baseline_revision')
    if not baseline:
        raise ValueError('Missing baseline revision')
    checked, reviews = [], []
    for path in sources:
        proposal = load(path)
        refactors = proposal.get('refactor_suggestions')
        if refactors:
            if (not isinstance(refactors, dict) or not verify_artifact(refactors)
                    or not Path(refactors['path']).resolve().is_relative_to(path.parent)):
                raise ValueError('Refactor review evidence is missing, changed or outside its proposal')
            reviews.append(refactors)
        if proposal.get('artifacts') == {} and proposal.get('status') == 'review_candidates_only':
            if proposal.get('baseline_revision') != baseline or not refactors:
                raise ValueError('Refactor-only batch baseline or evidence is missing')
            checked.append((proposal, {}))
        else:
            checked.append(_read_proposal(path, baseline))
    source_refs = [bind(p) for p in sources]
    aliases, hints, interfaces, contents, targets, names = [], [], [], {}, set(), set()
    readmes, legacy_hint_sources = [], []
    # Collect the selected outputs in batch order and reject collisions before
    # creating the bundle directory.
    for number, (proposal, data) in enumerate(checked, 1):
        for row in proposal.get('aliases', []):
            name = row.get('name')
            if not isinstance(name, str) or not name or name.casefold() in names:
                raise ValueError('Duplicate or missing exported alias name across batches')
            names.add(name.casefold())
            aliases.append(row)
        for key, binding in proposal['artifacts'].items():
            role = _artifact_role(key)
            if role == 'alias':
                target = binding['target']
                if any(target.casefold() == old or target.casefold().startswith(old + '/')
                       or old.startswith(target.casefold() + '/') for old in targets):
                    raise ValueError('Duplicate alias source destination or path prefix across batches')
                targets.add(target.casefold())
                contents[f'alias_{len(contents) + 1:04d}'] = (target, data[key])
            elif role == 'alias_interface':
                interfaces.append(f'## Proposal batch {number}\n\n' + data[key].decode())
            elif role == 'readme':
                readmes.append(data[key])
            elif role == 'error_hints':
                legacy_hint_sources.append(binding)
                payload = json.loads(data[key])
                if not isinstance(payload.get('hints'), list):
                    raise ValueError('Error-hint artifact must contain a hints list')
                for hint in payload['hints']:
                    if not isinstance(hint, dict):
                        raise ValueError('Error hints must be objects')
                    marked = {**hint, 'status': 'unverified'}
                    if marked not in hints:
                        hints.append(marked)
    if readme:
        readme = Path(readme).expanduser().resolve(strict=True)
        readmes.append(readme.read_bytes())
        source_refs.append(bind(readme))
    if readmes and any(text != readmes[0] for text in readmes):
        raise ValueError('Conflicting improved README versions; select identical bytes')
    if not contents and not (hints and include_legacy_hints) and not readmes:
        raise ValueError('No installable README or alias treatments; keep review candidates separate. '
                         'Legacy JSON hints require explicit include_legacy_hints=True.')
    output.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for key, (target, content) in contents.items():
        path = output / (key + Path(target).suffix)
        path.write_bytes(content)
        artifacts[key] = {**bind(path), 'target': target}
    if contents:
        path = output / 'ALIASES.md'
        path.write_text('# Alias interfaces\n\n' + '\n\n'.join(interfaces))
        artifacts['alias_interface'] = bind(path)
    if hints and include_legacy_hints:
        path = output / 'error_hints.json'
        atomic_json(path, {'schema_version': 1, 'status': 'unverified',
                          'source': 'development evidence only', 'hints': hints})
        artifacts['error_hints'] = bind(path)
    if readmes:
        path = output / 'README.md'
        path.write_bytes(readmes[0])
        artifacts['readme'] = bind(path)
    if not artifacts:
        raise ValueError('No installable artifacts in supplied proposals')
    # Keep exact original proposals as provenance, not additional owned source.
    for index, path in enumerate(sources, 1):
        shutil.copyfile(path, output / f'batch_{index:04d}.json')
    review_bindings = []
    for index, ref in enumerate(reviews, 1):
        path = output / f'refactor_review_{index:04d}.json'
        shutil.copyfile(ref['path'], path)
        review_bindings.append(bind(path))
    # This receipt is evidence only; the installer reads only `artifacts` above.
    selection = output / 'legacy_hint_selection.json'
    installed_hints = len(hints) if include_legacy_hints else 0
    atomic_json(selection, {
        'include_legacy_hints': include_legacy_hints,
        'candidate_count': len(hints), 'installed_count': installed_hints,
        'omitted_count': len(hints) - installed_hints,
        'source_artifacts': legacy_hint_sources, 'candidates': hints,
        'note': ('Legacy JSON hints explicitly included for their original evaluation protocol.'
                 if include_legacy_hints else
                 'Legacy JSON candidates are retained as evidence, not installed. '
                 'Native exception guidance requires separate proposal, validation and installation.'),
    })
    result = {'schema_version': 2, 'baseline_revision': baseline,
              'status': 'proposed_unvalidated', 'artifacts': artifacts,
              'aliases': aliases, 'source_proposals': source_refs,
              'refactor_reviews': review_bindings, 'legacy_hint_selection': bind(selection),
              'source_proposals_sha256': digest(source_refs), 'requires_validation': True,
              'bundle_semantics': 'complete_replace_owned', 'llm_calls': 0}
    atomic_json(output / 'proposal.json', result)
    return {'proposal': str(output / 'proposal.json'), 'status': result['status'],
            'alias_source_files': len(contents), 'aliases': len(aliases),
            'hints': installed_hints, 'omitted_legacy_hints': len(hints) - installed_hints,
            'legacy_hint_selection': str(selection), 'llm_calls': 0}
