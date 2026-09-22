"""Attach a Git codebase using an isolated local clone and five real branches."""
from pathlib import Path
import subprocess

from .ablation import load, save
from .preparation import CONDITION_FOLDERS, prepare_study
from .scaffolding import scaffold_spec, write_scaffold


def _git(directory, *arguments):
    result = subprocess.run(
        ['git', '-C', str(directory), *arguments], capture_output=True, text=True,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Git command failed')
    return result.stdout.strip()


def attach(repository, config, output):
    """Pin a clean local Git checkout; never switch or patch the user's checkout.

    Study records and branch worktrees are distinct: records share one protocol;
    each worktree contains the library source for one condition. All five begin
    at the same commit. Treatment preparation/evaluation are subsequent stages.
    """
    repository = Path(repository).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    root = Path(_git(repository, 'rev-parse', '--show-toplevel')).resolve()
    if repository != root:
        raise ValueError(f'Pass the Git repository root: {root}')
    if repository == output or repository in output.parents:
        raise ValueError('Use an output directory outside the target repository')
    if _git(repository, 'status', '--porcelain'):
        raise ValueError('Target has uncommitted changes; select a clean checkout to pin the baseline')
    revision = _git(repository, 'rev-parse', '--verify', 'HEAD')
    if (repository / '.aideal').exists() or (repository / '.aideal').is_symlink():
        raise ValueError('Target already contains .aideal; preserve it and choose an explicit migration before attachment')
    cfg, spec = scaffold_spec(config)
    # No Git state is changed until YAML paths and study creation pass.
    prepared = prepare_study(config, output)
    workspace_root = Path(prepared['source']['workspace_root'])
    for pattern in prepared['source']['source_globs']:
        resolved = (workspace_root / pattern).resolve()
        if resolved != repository and repository not in resolved.parents:
            raise ValueError('YAML source_globs must point inside the attached repository: ' + pattern)
    plan_path = output / 'plan.draft.json'
    plan = load(plan_path)
    plan['source_revision'] = revision
    save(plan_path, plan)
    state = {'status': 'attaching', 'repository': str(repository), 'revision': revision,
             'worktrees': {}, 'evaluated': False, 'treatments_applied': False}
    state_path = output / 'attachment.json'
    save(state_path, state)
    clone = output / 'repository.git'
    try:
        # A bare local clone isolates refs and objects from the user's checkout.
        _git(output, 'clone', '--bare', '--no-hardlinks', '--single-branch', str(repository), str(clone))
        if _git(clone, 'rev-parse', 'HEAD') != revision:
            raise ValueError('Target revision changed during attachment; retain this output and start a new study')
        for arm, folder in CONDITION_FOLDERS.items():
            branch = 'aideal/' + arm.replace('_', '-')
            path = output / folder / 'source'
            _git(clone, 'worktree', 'add', '-b', branch, str(path), revision)
            state['worktrees'][arm] = {'branch': branch, 'path': str(path), 'base_revision': revision}
            condition_path = output / folder / 'condition.json'
            condition = load(condition_path)
            condition['backend_path'] = str(path)
            condition['scaffold'] = write_scaffold(path, repository, output, cfg, spec)
            save(condition_path, condition)
            (output / folder / 'README.md').write_text(
                f'# {folder}\n\n'
                'source/ is the isolated library checkout. source/.aideal/ contains its generated harness and configuration.\n'
                'The harness is unvalidated; no treatment has been applied or evaluation run.\n', encoding='utf-8')
            save(state_path, state)
        state['status'] = 'attached_scaffolded_pending_validation'
        save(state_path, state)
        (output / 'README.md').write_text(
            '# Attached AIDEAL study\n\n'
            'Each condition/source directory is a real Git worktree at the recorded base commit.\n'
            'Each source/.aideal directory contains generated, uncommitted evaluation instrumentation.\n'
            'The shared plan and bank are still drafts. No treatment or evaluation has run.\n'
            'See attachment.json and each condition.json for source and scaffold locations.\n', encoding='utf-8')
    except Exception:
        state['status'] = 'attachment_incomplete'
        save(state_path, state)
        raise
    return {'attachment': state, 'preparation': prepared,
            'next': 'Validate the library adapter and shared bank, prepare/review treatments, then freeze and evaluate.'}
