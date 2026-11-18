"""Reject unfinished placeholders without rejecting grounded source-note labels."""
import unittest
from unittest.mock import patch

import test_readme_launcher as fixture
from aideal.readme_recording import ReadmeCallRecorder, ReadmeGenerationStopped
from aideal.readme_validation import validate_entry

SOURCE_DOC = ('Create the Topology object\n\nReturns\n-------\n'
              'MDAnalysis Topology object\n\nTodo\n----\n'
              'Could use the resnum and temp factor better')
REFERENCE = ('- **Attribute Limitations:** As noted in the `Todo`, the parser may not fully '
             'utilize `resnum` or `tempfactor` fields; if your analysis depends on these '
             'specific attributes, verify they are correctly populated in the resulting '
             '`Topology` object.')


def documented(name):
    return (f'## API Test: `{name}`\n\n### Signature\n```python\n{name}()\n```\n'
            f'_Source doc:_ {SOURCE_DOC}\n\n### Goal\nRead topology.\n\n'
            f'### Notes\n{REFERENCE}\n')


class SourceReferenceTests(unittest.TestCase):
    def test_recorded_crd_parser_reference_is_allowed_without_rewriting(self):
        text = documented('python:MDAnalysis.topology.CRDParser.CRDParser.parse')
        before = text
        validate_entry(text, 'python:MDAnalysis.topology.CRDParser.CRDParser.parse', [SOURCE_DOC])
        self.assertEqual(text, before)

    def test_reference_requires_todo_in_the_supplied_source_documentation(self):
        text = fixture.entry('beta') + '\n' + REFERENCE
        for docs in ([], ['Ordinary source description'], ['TODOish operation']):
            with self.subTest(docs=docs), self.assertRaises(ValueError):
                validate_entry(text, 'beta', docs)

    def test_real_placeholders_remain_rejected_after_a_valid_reference(self):
        for extra in ('TODO: complete example', '`TODO`', 'The example is TODO.',
                      'See the `TODO: finish this`', '_Source doc:_ TODO: invented'):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                validate_entry(documented('beta') + '\n' + extra, 'beta', [SOURCE_DOC])

    def test_fenced_indented_and_quoted_content_is_not_exempt(self):
        for extra in ('```python\n# See the `TODO`\n```',
                      '~~~text\nSee the `TODO`\n~~~',
                      '````python\nSee the `TODO`\n````',
                      '    See the `TODO`', '\tSee the `TODO`', '> See the `TODO`'):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                validate_entry(documented('beta') + '\n' + extra, 'beta', [SOURCE_DOC])

    def test_unclosed_code_fence_does_not_turn_into_exempt_prose(self):
        with self.assertRaises(ValueError):
            validate_entry(documented('beta') + '\n```text\nSee the `TODO`', 'beta', [SOURCE_DOC])


class SourceReferenceReplayTests(unittest.TestCase):
    setUp = fixture.ReadmeLauncherTests.setUp
    prepare = fixture.ReadmeLauncherTests.prepare
    generate = fixture.ReadmeLauncherTests.generate

    def test_returned_reference_revalidates_without_new_provider_call_or_old_edits(self):
        (self.source / 'api.py').write_text(
            'def alpha(x):\n    return x\n\ndef beta(x):\n'
            '    """' + SOURCE_DOC + '"""\n    return x+1\n')
        prepared = self.prepare()

        def old_validator(text, api, source_docs=()):
            if '`Todo`' in text:
                raise ValueError('old blanket TODO reference rejection')
            validate_entry(text, api, source_docs)

        with patch.object(ReadmeCallRecorder, '_validate', staticmethod(old_validator)), \
                patch('aideal.llm.usage_delta', return_value={'calls': 1, 'input_tokens': 100, 'output_tokens': 50}):
            with self.assertRaises(ReadmeGenerationStopped):
                # This small bare-name fixture flattens source descriptions;
                # the real qualified CRD response is tested verbatim above.
                response = documented('beta').replace(SOURCE_DOC, ' '.join(SOURCE_DOC.split()))
                self.generate(prepared, ['summary', fixture.entry('alpha'), response])
        (self.destination.parent / '.lock').touch()
        old_files = {p: p.read_bytes() for p in self.destination.rglob('*') if p.is_file()}
        destination = self.root / 'reference-revision/demo'
        current = fixture.launcher.prepare(self.library, destination, 'gemini-3.1-flash-lite',
                                           reuse_from=self.destination)
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('Must replay')) as provider:
            result = fixture.launcher.run_library(current[0], destination, current[1], current[2])
        self.assertEqual(0, provider.call_count)
        self.assertEqual((3, 1, 0), (result['imported_calls'], result['revalidated_calls'], result['new_calls']))
        self.assertEqual([], list(destination.rglob('provider.json')))
        self.assertTrue(all(p.read_bytes() == content for p, content in old_files.items()))


if __name__ == '__main__':
    unittest.main()
