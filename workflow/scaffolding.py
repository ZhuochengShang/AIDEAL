"""Generate evaluation instrumentation in an attached worktree, not in the tool."""
from copy import deepcopy
from pathlib import Path

from .ablation import bind, save
from .preparation import _engine_config_module


TEMPLATES = {
    'python': ('python.py.tmpl', 'api_test.py'),
    'java': ('java.java.tmpl', 'ApiTest.java'),
    'scala': ('scala.scala.tmpl', 'ApiTest.scala'),
    'rust': ('rust.rs.tmpl', 'api_test.rs'),
}


def scaffold_spec(config):
    """Read a configured harness or render a language-only, fail-closed skeleton."""
    config = Path(config).expanduser().resolve()
    engine = _engine_config_module()
    cfg = engine.load_config(config)
    execute = cfg.comprehension.get('execute', {}) or {}
    scaffold = execute.get('scaffold')
    if scaffold:
        path = (cfg.root / scaffold).resolve()
        if not path.is_file():
            raise ValueError(f'Configured scaffold is missing: {path}')
        return cfg, {'filename': path.name, 'text': path.read_text(encoding='utf-8'),
                     'origin': bind(path), 'method': 'configured_harness', 'imports_pending': False}
    frame = execute.get('scaffold_frame')
    imports = execute.get('imports', []) or []
    imports_pending = not isinstance(imports, list)
    if imports_pending:
        imports = []  # Automatic import mining belongs to validated adapter preparation.
    if frame:
        filename = execute.get('test_filename')
        if not filename:
            raise ValueError('A custom scaffold_frame requires comprehension.execute.test_filename')
        text = frame.replace('{imports}', '\n'.join(imports))
        origin = bind(config)
        method = 'configured_frame'
    else:
        language = cfg.language.lower()
        if language not in TEMPLATES:
            raise ValueError('Provide a scaffold or scaffold_frame for language: ' + cfg.language)
        template, filename = TEMPLATES[language]
        path = Path(__file__).resolve().parents[1] / 'templates/harness' / template
        text = path.read_text(encoding='utf-8').replace('{{imports}}', '\n'.join(imports))
        origin = bind(path)
        method = 'language_skeleton'
    if Path(filename).name != filename or filename in ('.', '..'):
        raise ValueError('Scaffold filename must be a filename, not a path')
    return cfg, {'filename': filename, 'text': text, 'origin': origin,
                 'method': method, 'imports_pending': imports_pending}


def write_scaffold(worktree, repository, study, cfg, spec):
    """Write the same instrumentation to every condition; never overwrite .aideal."""
    worktree, repository, study = (Path(p).resolve() for p in (worktree, repository, study))
    destination = worktree / '.aideal'
    # Exclusive creation also rejects a pre-existing file or symlink.
    destination.mkdir(exist_ok=False)
    harness = destination / 'harness' / spec['filename']
    harness.parent.mkdir()
    harness.write_text(spec['text'], encoding='utf-8')

    def relocate(value):
        path = (cfg.root / value).resolve()
        if path == repository or repository in path.parents:
            return str(worktree / path.relative_to(repository))
        return str(path)

    # A draft configuration is deliberately not auto-discovered as aideal.yaml.
    # Resolve discovery against THIS branch, and keep evaluation artifacts outside
    # the library API inventory. Full runtime/build path validation remains pending.
    raw = deepcopy(cfg.raw)
    raw.pop('extends', None)
    codebase = raw.setdefault('codebase', {})
    codebase['source_globs'] = [relocate(p) for p in cfg.source_globs]
    codebase['test_globs'] = [relocate(p) for p in cfg.test_globs]
    excluded = list(codebase.get('exclude_path_patterns', []) or [])
    excluded.append(r'(^|/)\.aideal(/|$)')
    codebase['exclude_path_patterns'] = excluded
    files = raw.setdefault('files', {})
    files.update(original_readme=str(study / 'original_documentation.txt'),
                 llm_readme='docs/LLM_readme.md', aliases='aliases/proposals.json',
                 error_log='evidence/errors.jsonl', notes_to_self='docs/notes.md',
                 integration_tasks='bank/puzzles.yaml')
    execution = raw.setdefault('comprehension', {}).setdefault('execute', {})
    execution['scaffold'] = str(harness)
    execution['test_filename'] = spec['filename']
    execution['work_dir'] = str(destination / 'runs')
    draft = destination / 'configs' / 'aideal.draft.yaml'
    draft.parent.mkdir()
    draft.write_text(_engine_config_module().yaml.safe_dump(raw, sort_keys=False), encoding='utf-8')
    for folder in ('docs', 'aliases', 'bank', 'evidence', 'runs'):
        (destination / folder).mkdir()
    record = {'state': 'scaffolded_not_validated', 'harness': bind(harness),
              'configuration': bind(draft), 'template_origin': spec['origin'],
              'method': spec['method'], 'imports_pending': spec['imports_pending'],
              'shared_plan': str(study / 'plan.draft.json'),
              'shared_bank': str(study / 'bank.draft.json'),
              'evaluation_ready': False, 'llm_calls': 0}
    save(destination / 'scaffold.json', record)
    (destination / 'README.md').write_text(
        '# AIDEAL evaluation workspace\n\n'
        'This instrumentation was generated inside the isolated codebase checkout.\n'
        'The harness is not yet validated. Complete its runtime/fixtures and independent\n'
        'checks before evaluation; an empty skeleton is not a pass.\n\n'
        '- configs/aideal.draft.yaml: resolved draft; audit runtime paths before use.\n'
        '- harness/: supplied harness or language-only skeleton.\n'
        '- scaffold.json: hashes and shared study/bank pointers.\n'
        '- evidence/ and runs/: future outputs, not preloaded example results.\n\n'
        'Keep the shared microtest/puzzle bank outside the model-visible checkout.\n'
        'All five conditions start with the same harness bytes. No model was called,\n'
        'no test was executed and no treatment was applied during scaffolding.\n',
        encoding='utf-8',
    )
    return record
