#!/usr/bin/env python3
"""Write an explicit all-library queue; never execute jobs or inspect credentials."""
import argparse
import json
from pathlib import Path
import yaml

LIBRARIES = ['rdpro', 'mdanalysis', 'tslearn', 'mir_eval', 'thumbnailator', 'sedonadb']


def build(root, release, python, catalog, install_directory=None, libraries=None,
          model='gemini-3.1-flash-lite'):
    root, release, catalog = map(lambda p: str(Path(p).resolve()), (root, release, catalog))
    python = str(Path(python).absolute())  # Preserve the venv interpreter symlink.
    jobs = []
    for library in libraries or LIBRARIES:
        r0 = Path(root) / 'runs/original' / library
        author = Path(root) / 'authoring' / library
        original_command = [python, release + '/scripts/run_original_micro.py', '--catalog', catalog,
                            '--output', str(r0), '--libraries', library, '--model', model, '--run']
        author_command = [python, release + '/scripts/run_readme_generation.py', '--catalog', catalog,
                          '--output', str(author), '--libraries', library, '--scope', 'surface',
                          '--model', model, '--run']
        artifact = author / library / 'completion.json'
        if install_directory is not None:
            manifest = Path(install_directory).resolve() / (library + '.json')
            if not manifest.is_file():
                raise ValueError('Missing explicit installation manifest: ' + str(manifest))
            value = json.loads(manifest.read_text())
            if (Path(value['readme']).resolve() != author / library / 'docs/LLM_readme.md' or
                    Path(value['completion']).resolve() != artifact):
                raise ValueError('Installation manifest uses a different authoring output: ' + library)
            artifact = author / 'installation.json'
            author_command = [python, release + '/scripts/install_generated_readme.py', '--manifest', str(manifest),
                              '--receipt', str(artifact), '--run-command', *author_command]
        jobs.extend([{'id': library + '-r0', 'library': library, 'stage': 'r0', 'command': original_command,
                      'output': str(r0), 'complete_artifact': str(r0 / library / 'result.json')},
                     {'id': library + '-readme', 'library': library, 'stage': 'readme', 'command': author_command,
                      'output': str(author), 'complete_artifact': str(artifact)}])
    return {'root': root, 'release': release, 'jobs': jobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'release', 'python', 'catalog', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--install-directory', type=Path)
    parser.add_argument('--libraries', nargs='+', help='Catalog keys, including language-specific RDPro banks')
    parser.add_argument('--model', default='gemini-3.1-flash-lite')
    args = parser.parse_args()
    catalog = yaml.safe_load(args.catalog.read_text())
    if not isinstance(catalog, dict) or not catalog:
        parser.error('The catalog must contain at least one library configuration')
    libraries = args.libraries if args.libraries is not None else list(catalog)
    if len(libraries) != len(set(libraries)) or set(libraries) - set(catalog):
        parser.error('Choose unique keys from the supplied catalog')
    plan = build(args.root, args.release, args.python, args.catalog, args.install_directory,
                 libraries, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(plan, indent=2) + '\n'
    if args.output.exists() and args.output.read_text() != content:
        raise ValueError('An existing queue plan would change; use a new plan/output root')
    args.output.write_text(content)
    print(json.dumps({'jobs': len(plan['jobs']), 'plan': str(args.output)}))


if __name__ == '__main__':
    main()
