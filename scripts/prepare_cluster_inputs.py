#!/usr/bin/env python3
"""Inventory and export pinned native R0 inputs; never call a model or read keys.

Default: inventory only. --export writes a portable payload with exact HEAD source
archives and resolved input files. Runtime paths are supplied via --runtime-json.
No local source changes are silently included: changed tracked files are recorded,
and inputs that require a changed tracked file fail unless explicitly allowed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import sys
import tarfile

import yaml


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args])


def source_inventory(name, source):
    source = source.resolve()
    top = Path(git(source, 'rev-parse', '--show-toplevel').decode().strip())
    if top != source:
        raise ValueError(f'{name}: expected independent source repository, got {top}')
    head = git(source, 'rev-parse', 'HEAD').decode().strip()
    entries = {}
    for row in git(source, 'ls-tree', '-rlz', head).split(b'\0'):
        if not row:
            continue
        metadata, raw_path = row.split(b'\t', 1)
        mode, kind, blob, size = metadata.decode().split()
        rel = raw_path.decode()
        if kind != 'blob':
            raise ValueError(f'Unsupported submodule/tree entry: {name}/{rel}')
        if any(p in ('.git', '__pycache__', '.venv', 'build') for p in PurePosixPath(rel).parts) or rel.endswith(('.pyc', '.so', '.dylib')):
            raise ValueError(f'Unexpected generated binary/build file tracked by HEAD: {name}/{rel}')
        entries[rel] = {'mode': mode, 'git_blob': blob, 'bytes': int(size)}
    changed = git(source, 'diff', '--name-only', '-z', head).decode().strip('\0').split('\0')
    changed = sorted(p for p in changed if p)
    return {'library': name, 'local_source': str(source), 'upstream_revision': head,
            'git_branch': git(source, 'branch', '--show-current').decode().strip(),
            'archive_policy': 'exact_git_HEAD_no_working_tree_overlays',
            'excluded_working_tree_changes': changed,
            'tracked_files': len(entries), 'tracked_bytes': sum(r['bytes'] for r in entries.values()),
            'entries': entries}


class Exporter:
    def __init__(self, args):
        self.args = args
        self.remote = args.remote_study.rstrip('/')
        self.payload = args.output / 'payload'
        self.sources = {}
        self.copies = {}
        self.transformed = {}
        self.references = []
        self.jar_by_hash = {}
        self.library_records = {}
        self.configs = {}
        self.catalog = {}
        self.excluded_input_caches = []
        self.runtime = json.loads(args.runtime_json.read_text()) if args.runtime_json else {}

    def copied(self, path, rel, *, category, library, content=None):
        path = Path(path).resolve()
        if not path.is_file():
            raise ValueError(f'Missing input {path}')
        record = {'local': str(path), 'relative': rel, 'remote': self.remote + '/' + rel,
                  'sha256': sha256(path), 'bytes': path.stat().st_size,
                  'category': category, 'library': library}
        old = self.copies.get(rel)
        if old and old['sha256'] != record['sha256']:
            raise ValueError(f'Input destination collision: {rel}')
        self.copies[rel] = record
        if content is not None:
            record['original_sha256'] = record['sha256']
            record['sha256'] = hashlib.sha256(content).hexdigest()
            record['bytes'] = len(content)
            record['transformation'] = 'Replace runtime paths in copied project profile; preserve original identity separately'
            self.transformed[rel] = content
        self.references.append(record)
        return record['remote']

    def reference(self, path, *, library, category):
        path = Path(path).resolve()
        source = self.sources[library]
        source_path = Path(source['local_source'])
        try:
            relative = path.relative_to(source_path).as_posix()
        except ValueError:
            relative = None
        if path.is_dir():
            files = []
            for candidate in sorted(p for p in path.rglob('*') if p.is_file()):
                candidate_relative = candidate.relative_to(source_path).as_posix() if candidate.is_relative_to(source_path) else None
                if candidate_relative not in source['entries'] and (
                    '__pycache__' in candidate.parts or candidate.suffix == '.pyc'
                    or candidate.name.endswith(('_offsets.npz', '_offsets.lock'))):
                    self.excluded_input_caches.append(str(candidate))
                else:
                    files.append(candidate)
            if not files:
                raise ValueError(f'Empty input directory: {path}')
            tracked_directory = relative is not None and all(
                p.relative_to(source_path).as_posix() in source['entries'] and
                p.relative_to(source_path).as_posix() not in source['excluded_working_tree_changes']
                for p in files)
            if tracked_directory:
                for p in files:
                    self.reference(p, library=library, category=category)
                return self.remote + '/sources/' + library + '/' + relative
            destination = 'extras/' + library + '/' + category + '/' + path.name
            for p in files:
                self.copied(p, destination + '/' + p.relative_to(path).as_posix(), category=category, library=library)
            return self.remote + '/' + destination
        if relative in source['entries']:
            if relative in source['excluded_working_tree_changes']:
                raise ValueError(f'Required {category} differs from pinned HEAD: {path}')
            remote = self.remote + '/sources/' + library + '/' + relative
            self.references.append({'local': str(path), 'remote': remote, 'category': category,
                                    'library': library, 'storage': 'git_HEAD_archive',
                                    'sha256': sha256(path), 'bytes': path.stat().st_size})
            return remote
        digest = sha256(path)
        return self.copied(path, f'extras/{library}/{category}/{digest[:12]}-{path.name}', category=category, library=library)

    def jar(self, path, library):
        digest = sha256(path)
        if digest not in self.jar_by_hash:
            remote = self.copied(path, f'runtime/jars/{digest[:12]}-{Path(path).name}', category='portable_jar', library=library)
            self.jar_by_hash[digest] = remote
        return self.jar_by_hash[digest]

    def collect_library(self, name, spec, load_config, load_manifest):
        cfg = load_config(spec['base_config'])
        raw = deepcopy(cfg.raw)
        # This historical exporter rewrites runtime/source layouts. It cannot
        # rewrite qualified provenance receipts without invalidating their hashes.
        # Current studies synchronize their frozen review/evaluator bundle instead.
        if (raw.get('codebase', {}).get('identity_mode') == 'qualified'
                or raw.get('files', {}).get('original_doc_manifest')):
            raise ValueError('Qualified API/document bundles must use the current frozen-study '
                             'synchronization path; this legacy exporter cannot preserve their provenance')
        raw.pop('extends', None)
        source = Path(spec['source_link']['target']).resolve()
        self.sources[name] = source_inventory(name, source)
        library_root = self.remote + '/libraries/' + name
        runtime = self.runtime.get(name, {})
        python = runtime.get('python', '/home/zshan011/apps/aideal/envs/' + name + '/bin/python')
        java = runtime.get('java', '/usr/bin/java')
        javac = runtime.get('javac', '/usr/bin/javac')
        files = raw['files']
        files['original_readme'] = [self.reference(p, library=name, category='original_docs') for p in cfg.original_readme_files]
        profile = cfg.root / files['project_profile']
        def profile_paths(value):
            if isinstance(value, dict):
                return {k: profile_paths(v) for k, v in value.items()}
            if isinstance(value, list):
                return [profile_paths(v) for v in value]
            if isinstance(value, str) and ('/Users/' in value or '/Library/' in value):
                if value.startswith('/Users/') and value.endswith('/bin/python'):
                    return python
                if value.startswith(str(source)):
                    return value.replace(str(source), self.remote + '/sources/' + name, 1)
                if value.startswith(str(cfg.root)):
                    return value.replace(str(cfg.root), library_root, 1)
                raise ValueError(f'Unmapped project profile path for {name}: {value}')
            return value
        profile_original = yaml.safe_load(profile.read_text())
        profile_portable = profile_paths(profile_original)
        self.copied(profile, f'libraries/{name}/configs/project_profile.yaml', category='project_profile', library=name,
                    content=yaml.safe_dump(profile_portable, sort_keys=False).encode() if profile_portable != profile_original else None)
        files['project_profile'] = 'configs/project_profile.yaml'
        for field in ('prompts_dir', 'integration_tasks', 'aliases'):
            original = cfg.root / files[field] if files.get(field) else None
            if original and original.exists():
                files[field] = self.reference(original, library=name, category=field)
            elif field == 'prompts_dir':
                files[field] = 'prompts'
            else:
                files.pop(field, None)
        # All original docs are resolved above. No archive download/cache refresh is
        # needed or allowed while installing this exact source-document snapshot.
        for field in ('original_doc_archives', 'original_doc_snapshot', 'original_doc_manifest'):
            files.pop(field, None)
        files.update(llm_readme='docs/LLM_readme.md', notes_to_self='docs/notes_to_self.md', error_log='logs/error_log.jsonl')
        ex = raw['comprehension']['execute']
        scaffold = cfg.root / ex['scaffold']
        scaffold_dest = f'libraries/{name}/inputs/{scaffold.name}'
        self.copied(scaffold, scaffold_dest, category='scaffold', library=name)
        ex.update(scaffold='inputs/' + scaffold.name, work_dir='execution', output_dir='execution/output',
                  max_fix_rounds=0, stop_on_provider_error=True, auto_report=False, build='')
        for key, value in ex.get('sample_data', {}).items():
            if isinstance(value, str):
                ex['sample_data'][key] = self.reference(cfg.root / value, library=name, category='fixtures')
            elif isinstance(value, dict) and value.get('path'):
                value['path'] = self.reference(cfg.root / value['path'], library=name, category='fixtures')
        jars = list(dict.fromkeys(self.jar(p, name) for p in spec.get('runtime_artifacts', []) if p.endswith('.jar')))
        if name == 'rdpro':
            classpath = ':'.join(jars)
            ex['command'] = ('mkdir -p "{work}/classes" && ' + shlex.quote(java) + ' -cp ' + shlex.quote(classpath)
                + ' scala.tools.nsc.Main -classpath ' + shlex.quote(classpath) + ' -d "{work}/classes" "{scala_file}" && '
                + shlex.quote(java) + ' -cp "{work}/classes:' + classpath + '" GeoJobMain')
            ex['uberjar'] = next(p for p in jars if p.endswith('-library_overlay.jar'))
            ex.update(jars='', spark_jars='', build_cwd='.')
        elif name == 'thumbnailator':
            ex['command'] = ('mkdir -p "{work}/classes" && ' + shlex.quote(javac)
                + ' -cp "{classpath}" -d "{work}/classes" "{test_file}" && ' + shlex.quote(java)
                + ' -Djava.awt.headless=true -cp "{work}/classes:{classpath}" ApiTest')
            ex.update(uberjar=jars[0], jars='', spark_jars='', build_cwd='source')
        else:
            environment = ['MPLBACKEND=Agg', 'OPENBLAS_NUM_THREADS=1', 'OMP_NUM_THREADS=1']
            if name == 'mdanalysis':
                environment.append('PYTHONPATH={root}/mdanalysis/package')
            elif name == 'tslearn':
                environment += ['PYTHONPATH={root}/tslearn', 'PYTHONHASHSEED=0', 'NUMBA_THREADING_LAYER=workqueue', 'NUMBA_NUM_THREADS=1', 'MKL_NUM_THREADS=1']
            elif name == 'mir_eval':
                environment.append('PYTHONPATH={root}/source')
            ex['command'] = 'env ' + ' '.join(environment) + ' ' + shlex.quote(python) + ' "{test_file}"'
        raw['comprehension'].update(class_context=False, relevant_doc_chars=12000)
        raw['models'] = {'registry': {'selected': {'provider': 'google', 'model': self.args.model}},
                         'roles': {role: 'selected' for role in ('author', 'audience', 'fixer')}}
        prior_provenance = raw.pop('provenance', None)
        raw['provenance'] = {'source_revision': self.sources[name]['upstream_revision'],
                             'source_export': 'exact Git HEAD; local generated changes excluded and recorded in export.json',
                             'runtime_validation': 'pending Linux preflight', 'packaging_manifest': self.remote + '/export.json'}
        # Remaining absolute Mac paths are an error, never an implicit fallback.
        serialized = yaml.safe_dump(raw, sort_keys=False)
        if '/Users/' in serialized or '/Library/Java/' in serialized or '-darwin' in serialized:
            raise ValueError(f'{name}: unconverted platform-specific value in effective config')
        self.configs[name] = serialized
        self.copied(spec['manifest'], f'libraries/{name}/inputs/api_manifest.json', category='manifest', library=name)
        artifacts = jars + list(runtime.get('runtime_artifacts', []))
        if name in ('rdpro', 'thumbnailator'):
            artifacts += [java] + ([javac] if name == 'thumbnailator' else [])
        else:
            artifacts.append(python)
        self.catalog[name] = {'base_config': library_root + '/configs/aideal.yaml',
                              'manifest': library_root + '/inputs/api_manifest.json',
                              'source_link': {'name': spec['source_link']['name'], 'target': self.remote + '/sources/' + name},
                              'runtime_artifacts': list(dict.fromkeys(artifacts)),
                              'scope_note': spec.get('scope_note', '').replace('Original source uses locally rebuilt Cython extensions; the extension binaries are hash-bound.', 'Linux extensions must be built and added to the runtime manifest before execution.')}
        self.library_records[name] = {'api_names': len(load_manifest(cfg, spec['manifest'])),
                                     'source_link_name': spec['source_link']['name'], 'local_base_config': spec['base_config'],
                                     'effective_config_extends': cfg.raw.get('extends'), 'runtime_settings': runtime,
                                     'prior_config_provenance': prior_provenance,
                                     'python': python, 'java': java if name in ('rdpro', 'thumbnailator') else None,
                                     'resolved_original_documents': len(cfg.original_readme_files),
                                     'portable_jar_references': len(jars)}

    def finish(self):
        self.args.output.mkdir(parents=True, exist_ok=True)
        metadata = {'schema_version': 1, 'remote_study': self.remote, 'model': self.args.model,
                    'protocol': 'Original docs; native microbenchmarks; one trial; R0 only; relevant docs; no repairs',
                    'libraries': self.library_records,
                    'source_trees': [{k:v for k,v in source.items() if k != 'entries'} for source in self.sources.values()],
                    'file_mapping': self.references,
                    'excluded_input_caches': self.excluded_input_caches,
                    'summary': {'source_files': sum(s['tracked_files'] for s in self.sources.values()),
                                'source_uncompressed_bytes': sum(s['tracked_bytes'] for s in self.sources.values()),
                                'additional_unique_files': len(self.copies), 'additional_unique_bytes': sum(c['bytes'] for c in self.copies.values()),
                                'unique_jars': len(self.jar_by_hash),
                                'api_names': sum(r['api_names'] for r in self.library_records.values())},
                    'readiness': 'requires Linux runtime provisioning and offline validation; no model calls made',
                    'excluded_library': {'sedonadb': 'No configured native audience execution command/scaffold'},
                    'local_working_tree_policy': 'HEAD-only source; excluded generated changes recorded; required modified input would fail'}
        (self.args.output / 'inventory.json').write_text(json.dumps(metadata, indent=2) + '\n')
        if not self.args.export:
            print(json.dumps(metadata['summary'], indent=2))
            return
        if self.payload.exists() and any(self.payload.iterdir()) and not self.args.resume_export:
            raise ValueError('Payload already exists; select a fresh output or inspect existing files')
        self.payload.mkdir(parents=True, exist_ok=True)
        for relative, record in self.copies.items():
            destination = self.payload / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Read once, check planned identity before committing an exported input.
            data = Path(record['local']).read_bytes()
            if hashlib.sha256(data).hexdigest() != record.get('original_sha256', record['sha256']):
                raise ValueError(f'Input changed after inventory: {record["local"]}')
            data = self.transformed.get(relative, data)
            if destination.exists():
                if destination.read_bytes() != data:
                    raise ValueError(f'Existing payload input differs: {destination}')
            else:
                destination.write_bytes(data)
        for name, source in self.sources.items():
            destination = self.payload / 'source_archives' / (name + '.tar.gz')
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                subprocess.run(['git', '-C', source['local_source'], 'archive', '--format=tar.gz',
                                '--output=' + str(destination), source['upstream_revision']], check=True)
            with tarfile.open(destination, 'r:gz') as archive:
                if archive.pax_headers.get('comment') != source['upstream_revision']:
                    raise ValueError(f'Existing archive does not identify pinned revision: {destination}')
                names = set()
                substituted = set()
                for member in archive.getmembers():
                    if member.isfile() or member.issym():
                        relative = member.name.rstrip('/')
                        names.add(relative)
                        data = member.linkname.encode() if member.issym() else archive.extractfile(member).read()
                        git_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                        if git_blob != source['entries'][relative]['git_blob']:
                            substituted.add(relative)
            missing = set(source['entries']) - names
            supplements = []
            for relative in sorted(missing | substituted):
                entry = source['entries'][relative]
                if entry['mode'] not in ('100644', '100755'):
                    raise ValueError(f'Cannot supplement nonregular export-ignored entry: {name}/{relative}')
                data = git(source['local_source'], 'show', source['upstream_revision'] + ':' + relative)
                supplement_rel = 'source_supplements/' + name + '/' + relative
                supplement = self.payload / supplement_rel
                supplement.parent.mkdir(parents=True, exist_ok=True)
                supplement.write_bytes(data)
                supplements.append({'relative': relative, 'payload': supplement_rel, 'sha256': hashlib.sha256(data).hexdigest(),
                                    'bytes': len(data), 'mode': entry['mode'],
                                    'reason': 'Restore exact HEAD bytes after Git archive export-subst' if relative in substituted else 'Tracked HEAD blob excluded by Git archive attributes'})
            for row in metadata['source_trees']:
                if row['library'] == name:
                    row.update(archive='source_archives/' + name + '.tar.gz', archive_sha256=sha256(destination),
                               archive_bytes=destination.stat().st_size, head_archive_supplements=supplements)
        for name, content in self.configs.items():
            destination = self.payload / 'libraries' / name / 'configs/aideal.yaml'
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
        (self.payload / 'original_micro_linux.yaml').write_text(yaml.safe_dump(self.catalog, sort_keys=False))
        (self.payload / 'export.json').write_text(json.dumps(metadata, indent=2) + '\n')
        (self.payload / 'materialize_sources.py').write_text(MATERIALIZE)
        print(json.dumps({**metadata['summary'], 'payload': str(self.payload),
                          'source_archives_bytes': sum(s['archive_bytes'] for s in metadata['source_trees'])}, indent=2))


MATERIALIZE = '''#!/usr/bin/env python3
"""Extract verified HEAD snapshots and make native config source links. No calls."""
from pathlib import Path, PurePosixPath
import hashlib, json, os, tarfile
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'export.json').read_text())
if str(root) != manifest['remote_study']:
    raise SystemExit('Install payload at exact remote_study path before materializing')
for source in manifest['source_trees']:
    archive = root / source['archive']
    if hashlib.sha256(archive.read_bytes()).hexdigest() != source['archive_sha256']:
        raise SystemExit('Source archive hash mismatch: ' + str(archive))
    target = root / 'sources' / source['library']
    if target.exists():
        raise SystemExit('Refusing to replace existing source: ' + str(target))
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream.getmembers():
            p = PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or member.isdev() or member.islnk():
                raise SystemExit('Unsafe tar member')
            if member.issym():
                link = PurePosixPath(member.linkname)
                if link.is_absolute() or '..' in link.parts:
                    raise SystemExit('Unsafe symlink')
        target.mkdir(parents=True)
        stream.extractall(target)
    for supplement in source.get('head_archive_supplements', []):
        data = (root / supplement['payload']).read_bytes()
        if hashlib.sha256(data).hexdigest() != supplement['sha256']:
            raise SystemExit('HEAD supplement hash mismatch')
        destination = target / supplement['relative']
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        destination.chmod(int(supplement['mode'], 8) & 0o777)
    name = source['library']
    link = root / 'libraries' / name / manifest['libraries'][name]['source_link_name']
    link.symlink_to(Path('../../sources') / name, target_is_directory=True)
print('Verified and materialized five source snapshots. Runtime preflight remains required.')
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toolkit', type=Path, required=True)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--output', type=Path, default=Path('/tmp/aideal-cluster-preparation'))
    parser.add_argument('--remote-study', default='/home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite')
    parser.add_argument('--model', default='gemini-3.1-flash-lite')
    parser.add_argument('--runtime-json', type=Path, help='Library keyed python/java/javac/runtime_artifacts settings')
    parser.add_argument('--export', action='store_true')
    parser.add_argument('--resume-export', action='store_true', help='Reuse byte-identical exported inputs after an interrupted export')
    args = parser.parse_args()
    args.output = args.output.resolve()
    sys.path.insert(0, str(args.toolkit / 'vendor/aideal_engine/src'))
    from aideal.config import load_config
    from aideal.doc_check_sources import _load_manifest
    catalog = yaml.safe_load((args.catalog or args.toolkit / 'configs/original_micro_libraries.yaml').read_text())
    exporter = Exporter(args)
    for name, spec in catalog.items():
        if 'blocked' not in spec:
            exporter.collect_library(name, spec, load_config, _load_manifest)
    exporter.finish()


if __name__ == '__main__':
    main()
