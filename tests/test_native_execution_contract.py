"""Offline regression checks for native assertions and per-attempt outputs."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.native_execution_contract import assertion_environment, isolate_output_bindings, rebind_output_text, native_check_passed
from aideal.execution import run_command
from aideal.config import load_config
from aideal.doc_check_execution import _comprehension_execute
from aideal.readme_agent import ApiEntry


class NativeExecutionContractTests(unittest.TestCase):
    def test_outputs_are_isolated_and_input_paths_and_uris_are_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            samples = {'fixture': 'file:///old/output/fixed.csv', 'output_dir': 'file:///old/output'}
            first, placeholders, receipt = isolate_output_bindings(
                samples, root / 'one', {'OUTPUT_PATH': '/old/output/image.png', 'INPUT': '/data/fixed.csv'})
            second, _, _ = isolate_output_bindings(samples, root / 'two')
            self.assertEqual(first['fixture'], samples['fixture'])
            self.assertEqual(samples['output_dir'], 'file:///old/output')
            self.assertNotEqual(first['output_dir'], second['output_dir'])
            self.assertEqual(placeholders['INPUT'], '/data/fixed.csv')
            self.assertEqual(placeholders['OUTPUT_PATH'], str(root / 'one/output/image.png'))
            rebound = rebind_output_text('x="/old/output/image.png"; y="file:///old/output"; source="file:///old/output/fixed.csv"', receipt)
            self.assertIn(str(root / 'one/output/image.png'), rebound)
            self.assertIn('source="file:///old/output/fixed.csv"', rebound)
            self.assertNotIn('y="file:///old/output"', rebound)

    def test_correctness_requires_exact_api_witness_on_stdout(self):
        ex = {'success_marker': 'DONE', 'error_marker': 'RUN_ERROR', 'require_correctness': True}
        api = 'java:owner.method'
        self.assertTrue(native_check_passed('__CHECK__ java:owner.method 12\nDONE', '', 0, api, ex))
        for stdout, stderr in [
            ('__CHECK__ java:owner.other 12\nDONE', ''),
            ('__CHECK__ java:owner.methodExtra 12\nDONE', ''),
            ('DONE', '__CHECK__ java:owner.method 12'),
            ('__CHECK__ java:owner.method \nDONE', ''),
            ('prefix __CHECK__ java:owner.method 12\nDONE', ''),
            ('__CHECK__ java:owner.method 12', 'DONE'),
            ('__CHECK__ java:owner.method 12\nDONE', 'RUN_ERROR failed'),
        ]:
            with self.subTest(stdout=stdout, stderr=stderr):
                self.assertFalse(native_check_passed(stdout, stderr, 0, api, ex))
        self.assertFalse(native_check_passed('__CHECK__ java:owner.method 12\nDONE', '', 1, api, ex))
        self.assertTrue(native_check_passed('VALUE java:owner.method 0\nDONE', '', 0, api,
                                          dict(ex, check_marker='VALUE')))
        self.assertTrue(native_check_passed('DONE', '', 0, api, dict(ex, require_correctness=False)))

    def test_assertion_environment_is_private_and_rejects_disable_switches(self):
        original = {'JAVA_TOOL_OPTIONS': '-Xmx256m', 'OTHER': 'keep'}
        changed = assertion_environment(original, 'Scala')
        self.assertEqual(original['JAVA_TOOL_OPTIONS'], '-Xmx256m')
        self.assertEqual(changed['JAVA_TOOL_OPTIONS'], '-Xmx256m -ea')
        self.assertEqual(assertion_environment(original, 'Python'), original)
        for command in ['java -da ApiTest', 'spark-submit --conf spark.driver.extraJavaOptions=-disableassertions app.jar']:
            with self.assertRaisesRegex(ValueError, 'assertions'):
                assertion_environment({}, 'Java', command)
        with self.assertRaisesRegex(ValueError, 'assertions'):
            assertion_environment({'_JAVA_OPTIONS': '-da:my.package'}, 'Java')

    @unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'JDK is not installed')
    def test_real_java_false_assertion_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'AssertionProbe.java').write_text(
                'public class AssertionProbe { public static void main(String[] args) { assert false : "must fail"; } }')
            subprocess.run(['javac', str(root / 'AssertionProbe.java')], check=True, capture_output=True)
            result = run_command(shlex.join(['java', '-cp', str(root), 'AssertionProbe']),
                                 cwd=root, env=assertion_environment(os.environ, 'Java'), timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('AssertionError: must fail', result.stderr)

    def test_native_runner_separates_apis_and_repair_rounds(self):
        for local_uris in (False, True):
            with self.subTest(local_uris=local_uris):
                with tempfile.TemporaryDirectory() as folder:
                    root = Path(folder).resolve()
                    (root / 'fixture.csv').write_text('fixed-input\n')
                    (root / 'library.py').write_text('def f(): pass\ndef g(): pass\n')
                    (root / 'README.md').write_text('Synthetic library.')
                    (root / 'scaffold.py').write_text('def run():\n    # AIDEAL_DATA_BINDINGS\n    # START\n    # END\n    print("DONE")\nrun()\n')
                    (root / 'dummy.jar').write_bytes(b'fixture avoids importing Spark')
                    config = {
                        'project': {'name': 'isolation-regression', 'language': 'Python'},
                        'codebase': {'source_globs': ['library.py']},
                        'files': {'original_readme': 'README.md'},
                        'models': {'registry': {'fake': {'provider': 'synthetic', 'model': 'offline'}},
                                   'roles': {'audience': 'fake', 'author': 'fake'}},
                        'comprehension': {'execute': {
                            'command': shlex.quote(sys.executable) + ' "{test_file}"',
                            'scaffold': 'scaffold.py', 'region': ['# START', '# END'],
                            'work_dir': 'work', 'test_filename': 'ApiTest.py', 'success_marker': 'DONE',
                            'spark_jars': '*.jar', 'local_uris': local_uris,
                            'sample_data': {'csv_input': str(root / 'fixture.csv')}, 'output_dir': str(root / 'shared-output'),
                        }},
                    }
                    (root / 'configs').mkdir()
                    (root / 'configs/aideal.yaml').write_text(yaml.safe_dump(config))
                    cfg = load_config(root / 'configs/aideal.yaml')
                    snippets = [
                        'from pathlib import Path\nfrom urllib.parse import urlparse, unquote\noutput_dir = unquote(urlparse(output_dir).path) if output_dir.startswith("file://") else output_dir\nPath(output_dir, "image.png").mkdir()\nraise ValueError("first attempt")',
                        'from pathlib import Path\nfrom urllib.parse import urlparse, unquote\noutput_dir = unquote(urlparse(output_dir).path) if output_dir.startswith("file://") else output_dir\nPath(output_dir, "image.png").write_text("fixed")',
                        'from pathlib import Path\nfrom urllib.parse import urlparse, unquote\noutput_dir = unquote(urlparse(output_dir).path) if output_dir.startswith("file://") else output_dir\nPath(output_dir, "image.png").write_text("next API")',
                    ]
                    with ExitStack() as stack:
                        provider = stack.enter_context(patch('aideal.llm.invoke_text', side_effect=snippets))
                        stack.enter_context(patch('aideal.doc_check_execution.public_api_details', return_value=[]))
                        stack.enter_context(patch('aideal.doc_check_execution.public_api_surface', return_value={'f', 'g'}))
                        stack.enter_context(patch('aideal.readme_agent.public_api_details', return_value=[]))
                        result = _comprehension_execute(cfg, [ApiEntry(x, '', '', 'Use the function.') for x in ['f', 'g']],
                                                        0, 42, 'original', show_code=True, max_fix_rounds=1)
                    self.assertEqual(result['score'], 1)
                    self.assertEqual(result['metrics']['f']['pass_round'], 1)
                    self.assertEqual(result['metrics']['g']['pass_round'], 0)
                    evidence = [Path(p) for m in result['metrics'].values() for p in m['attempt_evidence']]
                    self.assertEqual(len(evidence), 3)
                    self.assertEqual(len({json.loads((p / 'execution.json').read_text())['cwd'] for p in evidence}), 3)
                    for p in evidence:
                        receipt = json.loads((p / 'execution_contract.json').read_text())
                        self.assertEqual(receipt['sample_data']['csv_input'], (root / 'fixture.csv').as_uri() if local_uris else str(root / 'fixture.csv'))
                        self.assertEqual(receipt['output_root'], str(p / 'output'))
                        prompt = json.loads((p / 'request.json').read_text())['user']
                        self.assertIn(str(p / 'output'), prompt)
                        self.assertIn('a file URI, not a filesystem path' if local_uris else 'a local filesystem path', prompt)
                        if local_uris:
                            self.assertIn("convert it with the language's URI/path utilities", prompt)
                    self.assertEqual((root / 'fixture.csv').read_text(), 'fixed-input\n')
                    self.assertFalse((root / 'shared-output').exists())
                    self.assertEqual(result['run']['execution_contract']['version'], 'native-execution-v3')


if __name__ == '__main__':
    unittest.main()
