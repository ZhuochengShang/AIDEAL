"""No-install runtime override checks, including dependency-file drift."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from workflow.runtime_profile import (load_runtime_profile, remap_runtime_command,
    runtime_profile_receipts, verify_runtime_profile, require_runtime_ready)


class RuntimeProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / 'base-python'
        self.binary.write_text('#!/bin/sh\nexit 0\n')
        self.binary.chmod(0o755)
        self.old = self.root / 'old/bin/python'
        self.new = self.root / 'overlay/bin/python'
        for path in (self.old, self.new):
            path.parent.mkdir(parents=True)
            path.symlink_to(self.binary)
        self.package = self.root / 'overlay/site-packages/example.py'
        self.package.parent.mkdir(parents=True)
        self.package.write_text('VERSION = 1\n')
        self.manifest = self.root / 'environment.json'
        self.manifest.write_text(json.dumps({'file_bindings': [self.receipt(self.package)]}))
        self.report = self.root / 'setup.json'
        self.report.write_text('{"imports_checked": true}')
        self.path = self.root / 'profile.json'
        self.raw = {'schema': 1, 'command_replacements': {str(self.old): str(self.new)},
                    'environment_manifest': self.receipt(self.manifest),
                    'setup_report': self.receipt(self.report)}
        self.path.write_text(json.dumps(self.raw))

    def receipt(self, path):
        return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_virtual_environment_command_path_is_not_resolved(self):
        profile = load_runtime_profile(self.path)
        command = f'env -u PYTHONPATH "{self.old}" "{{test_file}}" && echo done'
        changed = remap_runtime_command(command, profile)
        self.assertIn(str(self.new), changed)
        self.assertNotIn(str(self.binary), changed)
        self.assertIn('&& echo done', changed)
        self.assertIn('"{test_file}"', changed)
        self.assertEqual(profile['identity_sha256'], load_runtime_profile(self.path)['identity_sha256'])

    def test_installed_module_drift_is_detected_without_manifest_change(self):
        profile = load_runtime_profile(self.path)
        before = self.package.stat()
        self.package.write_text('VERSION = 2\n')
        os.utime(self.package, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, 'Runtime evidence changed'):
            verify_runtime_profile(profile)

    def test_profile_and_setup_mutation_are_rejected(self):
        profile = load_runtime_profile(self.path)
        self.report.write_text('{"imports_checked": false}')
        with self.assertRaisesRegex(ValueError, 'Runtime evidence changed'):
            verify_runtime_profile(profile)
        with self.assertRaisesRegex(ValueError, 'Runtime evidence changed'):
            load_runtime_profile(self.path)

    def test_interpreter_symlink_retarget_is_rejected(self):
        profile = load_runtime_profile(self.path)
        other = self.root / 'other-python'
        other.write_bytes(self.binary.read_bytes())
        other.chmod(0o755)
        self.new.unlink()
        self.new.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'interpreter link changed'):
            verify_runtime_profile(profile)

    def test_substrings_are_not_command_replacements(self):
        profile = load_runtime_profile(self.path)
        with self.assertRaisesRegex(ValueError, 'did not match'):
            remap_runtime_command(str(self.old) + '-unrelated test.py', profile)

    def test_missing_executable_or_unbound_installed_files_are_rejected(self):
        self.raw['command_replacements'][str(self.old)] = str(self.root / 'missing/python')
        self.path.write_text(json.dumps(self.raw))
        with self.assertRaisesRegex(ValueError, 'missing or not executable'):
            load_runtime_profile(self.path)
        self.raw['command_replacements'][str(self.old)] = str(self.new)
        self.manifest.write_text('{}')
        self.raw['environment_manifest'] = self.receipt(self.manifest)
        self.path.write_text(json.dumps(self.raw))
        with self.assertRaisesRegex(ValueError, 'actual installed files'):
            load_runtime_profile(self.path)

    def test_compact_receipts_bind_manifest_that_checks_actual_packages(self):
        profile = load_runtime_profile(self.path)
        self.assertIn(self.receipt(self.manifest), runtime_profile_receipts(profile))
        self.assertNotIn(self.receipt(self.package), runtime_profile_receipts(profile))
        verify_runtime_profile(profile)
        self.assertEqual(runtime_profile_receipts(None), [])
        self.assertEqual(remap_runtime_command('python test.py', None), 'python test.py')

    def test_execution_command_must_use_the_declared_environment(self):
        profile = load_runtime_profile(self.path)
        verify_runtime_profile(profile, command=f'{self.new} test.py')
        with self.assertRaisesRegex(ValueError, 'has not applied'):
            verify_runtime_profile(profile, command=f'{self.old} test.py')

    def test_unresolved_setup_can_be_inspected_but_blocks_paid_work(self):
        self.report.write_text(json.dumps({'unresolved_setup': ['external fixture not available']}))
        self.raw['setup_report'] = self.receipt(self.report)
        self.path.write_text(json.dumps(self.raw))
        profile = load_runtime_profile(self.path)
        verify_runtime_profile(profile)
        with self.assertRaisesRegex(ValueError, 'paid generation is blocked'):
            require_runtime_ready(profile)


if __name__ == '__main__':
    unittest.main()
