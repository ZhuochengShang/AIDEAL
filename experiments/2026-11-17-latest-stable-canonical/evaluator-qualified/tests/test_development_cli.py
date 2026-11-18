"""Current treatment entry points remain clear without breaking saved workflows."""
from contextlib import redirect_stdout
from io import StringIO
import json
from unittest import TestCase
from unittest.mock import patch

from workflow.__main__ import main


class DevelopmentCommandTests(TestCase):
    def invoke(self, *arguments):
        output = StringIO()
        with patch('sys.argv', ['aideal', *arguments]), redirect_stdout(output):
            main()
        return json.loads(output.getvalue())

    def help_text(self, *arguments):
        output = StringIO()
        with patch('sys.argv', ['aideal', *arguments, '--help']), redirect_stdout(output):
            with self.assertRaises(SystemExit) as stopped:
                main()
        self.assertEqual(0, stopped.exception.code)
        return output.getvalue()

    def test_main_help_distinguishes_current_workflow_from_compatibility(self):
        current = self.help_text()
        for name in ('preview-native-hints', 'propose-native-hints', 'validate-native-hints',
                     'install-native-hints', 'preview-library', 'propose-library'):
            self.assertIn(name, current)
        for name in ('preview-source-hints', 'propose-source-hints', 'validate-source-hints',
                     'install-source-hints', 'preview-improvements', 'propose-improvements',
                     'show-fix-hints'):
            self.assertNotIn(name, current)
            self.assertIn('Compatibility', self.help_text(name))

    def test_current_and_earlier_preview_names_use_identical_evidence_intake(self):
        with patch('workflow.source_hint_development.build_development_preview',
                   return_value={'preview': 'saved/preview.json'}) as intake:
            for command in ('preview-native-hints', 'preview-source-hints'):
                self.assertEqual({'preview': 'saved/preview.json'}, self.invoke(
                    command, '--manifest', 'development.json', '--output', 'saved'))
                intake.assert_called_with('development.json', 'saved')
            self.assertEqual(2, intake.call_count)

    def test_compatibility_proposals_keep_old_dispatch_and_arguments(self):
        with patch('workflow.improvement_suggestions.propose_improvements',
                   return_value={'schema_version': 1}) as old_proposal, \
             patch('workflow.improvement_batches.propose_library_improvements',
                   side_effect=AssertionError('Do not reinterpret a saved single preview')):
            self.assertEqual({'schema_version': 1}, self.invoke(
                'propose-improvements', '--preview', 'old-preview.json',
                '--model-config', 'model.yaml', '--output', 'old-output', '--readme', 'README.md'))
            old_proposal.assert_called_once_with('old-preview.json', 'model.yaml',
                                                 'old-output', readme='README.md')
        with patch('workflow.source_hint_development.propose_source_hints',
                   return_value={'protocol': 'source-comments'}) as old_hints, \
             patch('workflow.native_hints.propose_native_hints',
                   side_effect=AssertionError('Do not reinterpret comment-hint proposals')):
            self.assertEqual({'protocol': 'source-comments'}, self.invoke(
                'propose-source-hints', '--preview', 'old-preview.json',
                '--model-config', 'model.yaml', '--output', 'comment-output'))
            old_hints.assert_called_once_with('old-preview.json', 'model.yaml', 'comment-output')

    def test_native_install_routes_to_validation_enforcing_installer(self):
        # The CLI must retain the installer that rejects invalid receipts.
        with patch('workflow.native_hints.install_native_hints',
                   side_effect=ValueError('Native validation receipt rejected')) as install:
            with self.assertRaisesRegex(ValueError, 'Native validation receipt rejected'):
                self.invoke('install-native-hints', '--validation', 'invalid.json',
                            '--target', 'target-checkout')
            install.assert_called_once_with('invalid.json', 'target-checkout')

    def test_bundle_requires_explicit_legacy_hint_opt_in(self):
        with patch('workflow.treatment_bundles.bundle_proposals',
                   return_value={'status': 'proposed_unvalidated'}) as bundle:
            for include in (False, True):
                args = ('--include-legacy-hints',) if include else ()
                self.invoke('bundle-proposals', '--proposal', 'batch/proposal.json',
                            '--output', 'fresh-bundle', *args)
                bundle.assert_called_with(['batch/proposal.json'], 'fresh-bundle',
                                          readme=None, include_legacy_hints=include)
