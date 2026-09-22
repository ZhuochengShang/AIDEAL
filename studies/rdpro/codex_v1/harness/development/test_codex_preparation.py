"""Offline build-contract tests: no JVM, library or provider is executed."""
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import yaml

sys.path.insert(0, str(Path(__file__).parent / 'evaluation_assets_codex_v1'))
import build_backends as builder
from prepare_conditions import COMMON, config_from_builds
import prepare_conditions as preparation


class CodexBuildTests(unittest.TestCase):
    def build_fixture(self, directory, missing_alias=False, shadow_alias=False):
        root = directory / 'source'; root.mkdir()
        alias = 'cg/src/main/scala/example/Convenience.scala'
        for name in [*builder.SOURCES, alias]:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic Scala source')
        dependency = directory / 'dependency'; dependency.write_text('synthetic dependency')
        runtime = {'java': str(dependency), 'javac': str(dependency), 'jars': [str(dependency)]}
        names = [*builder.CLASSES, 'example.Convenience$', 'example.Convenience']
        seen = {}

        def fake_git(checkout, *arguments):
            if arguments[:1] == ('diff',):
                return alias + '\n.aideal/treatments/README.md'
            return 'synthetic-tree' if arguments[-1] == 'HEAD^{tree}' else 'synthetic-revision'

        def fake_command(arguments, output, label, timeout=120):
            seen[label] = arguments
            (output / (label + '.stdout')).write_text('')
            (output / (label + '.stderr')).write_text('')
            if label == 'library_compile':
                for name in names:
                    path = output / 'library_classes' / (name.replace('.', '/') + '.class')
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_text('synthetic class bytes')
            if label == 'class_origins':
                origins = []
                for name in names:
                    if missing_alias and name == 'example.Convenience$':
                        continue
                    source = output / ('dependency.jar' if shadow_alias and name == 'example.Convenience$'
                                       else 'library_overlay.jar')
                    origins.append(name + '\t' + str(source))
                (output / (label + '.stdout')).write_text('\n'.join(origins))
            return arguments

        with patch.object(builder, 'git', side_effect=fake_git), patch.object(builder, 'command', side_effect=fake_command):
            row = builder.build_one(root, directory / 'build', runtime=runtime, baseline='baseline')
        return row, seen, root / alias

    def test_new_scala_alias_is_compiled_and_every_class_origin_is_probed(self):
        with tempfile.TemporaryDirectory() as temporary:
            row, commands, alias = self.build_fixture(Path(temporary))
            self.assertIn(str(alias.resolve()), commands['library_compile'])
            self.assertIn('example.Convenience$', commands['class_origins'])
            self.assertIn('example.Convenience', commands['class_origins'])
            identity = builder.load(Path(row['runtime']).with_name('build_identity.json'))
            self.assertIn(builder.bind(alias), identity['inputs']['source'])
            self.assertEqual(5, len(identity['class_origins']))
            self.assertIn('example/Convenience$.class', identity['class_hashes'])

    def test_missing_alias_origin_cannot_produce_runtime_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, 'Incomplete classloader'):
                self.build_fixture(root, missing_alias=True)
            self.assertFalse((root / 'build/runtime.json').exists())

    def test_shadowed_alias_origin_cannot_produce_runtime_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, 'shadowed'):
                self.build_fixture(root, shadow_alias=True)
            self.assertFalse((root / 'build/runtime.json').exists())

    def test_no_installed_treatment_fails_before_any_build_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'attachment.json').write_text(json.dumps({'revision': 'baseline'}))
            with self.assertRaisesRegex(ValueError, 'require installed'):
                builder.build_backends(root, root / 'builds')
            self.assertFalse((root / 'builds').exists())

    def test_five_arm_build_never_reads_or_adds_a_refactor_pointer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'refactors').mkdir()
            (root / 'refactors/current.json').write_text('invalid synthetic old refactor pointer')
            attachment = {'revision': 'baseline', 'worktrees': {
                arm: {'path': str(root / arm)} for arm in builder.ARMS}}
            with patch.object(builder, 'installed_treatments', return_value=(attachment, {'version': 'same'})), \
                    patch.object(builder, 'build_one', side_effect=lambda source, output, baseline:
                                 {'worktree': source, 'revision': baseline}) as build:
                rows = builder.build_backends(root, root / 'builds')
            self.assertEqual(list(builder.ARMS), list(rows))
            self.assertEqual(5, build.call_count)
            self.assertNotIn('refactor_only', rows)

    def test_shared_low_token_caps_and_single_provider_attempt_are_explicit(self):
        self.assertEqual(2048, COMMON['max_output_tokens'])
        self.assertEqual(1, COMMON['max_snippet_fixes'])
        self.assertEqual(1, COMMON['provider_attempt_limit'])
        self.assertEqual(['trial_01'], COMMON['trial_ids'])
        self.assertEqual((8000, 2500, 1500), tuple(COMMON[k] for k in
            ('documentation_max_characters', 'alias_max_characters', 'hint_max_characters')))

    def test_config_refuses_uninstalled_treatments_before_reading_builds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'attachment.json').write_text(json.dumps({'revision': 'baseline'}))
            with self.assertRaisesRegex(ValueError, 'require installed'):
                config_from_builds(root, root / 'missing_backends.json', root / 'adapter.py', sys.executable)

    def config_fixture(self, root):
        docs = root / 'original.txt'; docs.write_text('original synthetic documentation')
        old = {'bank': str(root / 'existing_bank.json'), 'api_function_ids': {'api': 'source:1:api'},
               'development_case_ids': ['separate_development'],
               'conditions': {'original': {'documents': [str(docs)]}}}
        (root / 'refactor_pair_v2.yaml').write_text(yaml.safe_dump({'condition_evaluation': old}))
        selected = root / 'development/existing_readme/README.md'
        selected.parent.mkdir(parents=True); selected.write_text('selected synthetic Generated README')
        selected.with_name('provenance.json').write_text(json.dumps({'sha256': builder.bind(selected)['sha256']}))
        adapter = root / 'openai_codex_adapter.py'; adapter.write_text('synthetic adapter')
        adapter.with_name('provider_budget.py').write_text('synthetic response helper')
        rows, attachment, application = {}, {'worktrees': {}}, {'arms': {}}
        for arm in builder.ARMS:
            worktree = root / arm; worktree.mkdir()
            attachment['worktrees'][arm] = {'path': str(worktree), 'branch': 'branch/' + arm}
            application['arms'][arm] = {'commit_revision': 'revision/' + arm}
            if arm in ('readme_only', 'combined'):
                readme = worktree / '.aideal/treatments/README.md'
                readme.parent.mkdir(parents=True); readme.write_bytes(selected.read_bytes())
            identity = {'worktree': str(worktree), 'revision': 'revision/' + arm}
            identity['sha256'] = builder.digest(identity)
            path = worktree / 'build_identity.json'; builder.save(path, identity)
            runtime = worktree / 'runtime.json'; builder.save(runtime, {'build_identity': builder.bind(path)})
            rows[arm] = {'worktree': str(worktree), 'revision': 'revision/' + arm,
                         'runtime': str(runtime), 'build_sha256': identity['sha256'],
                         'source_artifacts': [str(path), str(runtime)]}
        summary = root / 'backends.json'; builder.save(summary, rows)
        return attachment, application, summary, adapter, docs

    def test_config_routes_matched_artifacts_and_binds_both_provider_modules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            attachment, application, summary, adapter, docs = self.config_fixture(root)
            with patch.object(preparation, 'installed_treatments', return_value=(attachment, application)):
                cfg = config_from_builds(root, summary, adapter, sys.executable)['condition_evaluation']
            self.assertEqual('five_arm', cfg['design'])
            self.assertEqual(list(builder.ARMS), list(cfg['conditions']))
            self.assertEqual([str(adapter), str(adapter.with_name('provider_budget.py'))], cfg['model']['artifacts'])
            for arm, row in cfg['conditions'].items():
                self.assertEqual(arm in ('alias_only', 'combined'), 'alias_interface' in row)
                self.assertEqual(arm in ('error_hints_only', 'combined'), 'error_hints' in row)
                if arm not in ('readme_only', 'combined'):
                    self.assertEqual([str(docs)], row['documents'])
                self.assertEqual('revision/' + arm, row['source']['revision'])
            self.assertEqual(0, cfg['common']['temperature'])
            self.assertEqual('gpt-5.3-codex', cfg['model']['name'])
            policy = cfg['model']['parameter_policy']
            self.assertFalse(policy['temperature_sent_to_provider'])
            self.assertEqual('provider_default_unspecified', policy['effective_temperature'])
            self.assertEqual('low', policy['reasoning_effort'])
            self.assertIn('--budget-ledger=' + str(root / 'development/codex_budget_v1.json'),
                          cfg['model']['command'])

    def test_config_refuses_silent_replacement_of_the_selected_generated_readme(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            attachment, application, summary, adapter, _ = self.config_fixture(root)
            (root / 'readme_only/.aideal/treatments/README.md').write_text('different synthetic treatment')
            with patch.object(preparation, 'installed_treatments', return_value=(attachment, application)):
                with self.assertRaisesRegex(ValueError, 'README treatment differs'):
                    config_from_builds(root, summary, adapter, sys.executable)

    def test_mutable_budget_ledger_is_not_bound_as_a_command_file(self):
        from workflow.condition_inputs import bind_command
        from workflow.ablation import bind
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            adapter = root / 'openai_codex_adapter.py'; adapter.write_text('synthetic adapter')
            adapter.with_name('provider_budget.py').write_text('synthetic budget helper')
            ledger = root / 'development/codex_budget_v1.json'
            ledger.parent.mkdir(); ledger.write_text('{"reserved_usd":0}')
            settings = preparation.provider_settings(root, adapter, sys.executable)
            refs = []
            bind_command(settings, 'model', root, refs)
            ledger.write_text('{"reserved_usd":1}')
            self.assertNotIn(str(ledger), [ref['path'] for ref in refs])
            self.assertTrue(all(bind(ref['path']) == ref for ref in refs))
            self.assertIn('--budget-ledger=' + str(ledger), settings['command'])
            self.assertNotIn(str(ledger), settings['command'])

    def installation_fixture(self, root):
        def git(repo, *args):
            return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                           stderr=subprocess.DEVNULL).strip()
        source = root / 'baseline'; source.mkdir()
        git(source, 'init', '-q')
        (source / 'source.scala').write_text('baseline source')
        git(source, 'add', 'source.scala')
        identity = ('-c', 'user.name=Synthetic Test', '-c', 'user.email=test@example.invalid',
                    '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null')
        git(source, *identity, 'commit', '-qm', 'baseline')
        baseline = git(source, 'rev-parse', 'HEAD')
        role_paths = {'readme': '.aideal/treatments/README.md',
                      'alias': 'src/Aliases.scala', 'alias_interface': '.aideal/treatments/ALIASES.md',
                      'error_hints': '.aideal/treatments/error_hints.json'}
        roles = {'original': [], 'readme_only': ['readme'],
                 'alias_only': ['alias', 'alias_interface'], 'error_hints_only': ['error_hints'],
                 'combined': list(role_paths)}
        attachment = {'revision': baseline, 'worktrees': {}}
        application = {'proposal_sha256': 'a' * 64, 'baseline_revision': baseline,
                       'status': 'applied_unvalidated', 'arms': {}}
        for arm in builder.ARMS:
            checkout = root / arm
            subprocess.run(['git', 'clone', '-q', str(source), str(checkout)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            branch = 'aideal/test/' + arm
            git(checkout, 'checkout', '-qb', branch)
            files = {}
            for role in roles[arm]:
                name = role_paths[role]; path = checkout / name
                path.parent.mkdir(parents=True, exist_ok=True); path.write_text(role + ' synthetic bytes')
                files[name] = {**builder.bind(path), 'role': role}
                git(checkout, 'add', name)
            if files:
                git(checkout, *identity, 'commit', '-qm', 'synthetic treatment')
            attachment['worktrees'][arm] = {'path': str(checkout), 'branch': branch}
            application['arms'][arm] = {'path': str(checkout),
                                        'commit_revision': git(checkout, 'rev-parse', 'HEAD'), 'files': files}
        builder.save(root / 'attachment.json', attachment)
        folder = root / 'treatments' / ('a' * 64); folder.mkdir(parents=True)
        builder.save(folder / 'application.json', application)
        builder.save(root / 'treatments/current.json',
                     {'proposal_sha256': 'a' * 64, 'application_sha256': builder.digest(application)})
        return attachment, application, git

    def test_real_git_installation_passes_and_tampered_alias_prevents_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            expected = self.installation_fixture(root)
            self.assertEqual(expected[:2], builder.installed_treatments(root))
            (root / 'alias_only/src/Aliases.scala').write_text('unrecorded bytes')
            with self.assertRaisesRegex(ValueError, 'Installed treatment bytes changed'):
                builder.build_backends(root, root / 'builds')
            self.assertFalse((root / 'builds').exists())

    def test_real_git_branch_change_prevents_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            _, _, git = self.installation_fixture(root)
            git(root / 'combined', 'checkout', '-qb', 'unexpected')
            with self.assertRaisesRegex(ValueError, 'Installed treatment checkout changed'):
                builder.build_backends(root, root / 'builds')
            self.assertFalse((root / 'builds').exists())


if __name__ == '__main__':
    unittest.main()
