"""Real native execution controls in temporary synthetic inputs, no providers."""
from pathlib import Path
import importlib.util
import unittest
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parent
if ROOT.name == 'tests':
    ROOT = ROOT.parent
TOOLKIT = ROOT if (ROOT / 'vendor/aideal_engine').is_dir() else Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow')
def imported(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

helper = imported('cluster_preflight', ROOT / 'scripts/preflight_cluster_libraries.py')
fixture_module = imported('native_launcher_fixture', TOOLKIT / 'tests/test_original_micro_launcher.py')


class NativePreflightTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.OriginalMicroLauncherTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        config = yaml.safe_load(self.fixture.config.read_text())
        config['comprehension']['execute']['require_correctness'] = True
        config['comprehension']['execute']['check_marker'] = '__CHECK__'
        self.fixture.config.write_text(yaml.safe_dump(config))
        self.launcher = helper.load_launcher(TOOLKIT)

    @staticmethod
    def response(name, spec, case):
        code = 'assert f(1) == 1\nprint("__IDENTITY__ temporary synthetic source")\n'
        if case != 'witness_omitted':
            code += 'print("__CHECK__ f value=1")\n'
        if case == 'assertion_failure':
            code += f'assert False, "{helper.SENTINEL}"\n'
        return code

    def test_three_controls_exercise_native_pass_failure_and_witness_gate(self):
        with patch.dict(helper.APIS, {'demo': 'f'}), patch.object(helper, 'snippet', side_effect=self.response):
            for case in helper.CASES:
                with self.subTest(case=case):
                    row = helper.check_case('demo', self.fixture.library, case, self.fixture.root / case, self.launcher)
                    self.assertEqual('verified', row['status'])
                    self.assertEqual(0, row['actual_model_calls'])

    def test_unrelated_execution_failure_cannot_be_counted_as_expected_assertion(self):
        with patch.dict(helper.APIS, {'demo': 'f'}), patch.object(helper, 'snippet', return_value='raise ImportError("broken environment")'):
            with self.assertRaisesRegex(AssertionError, 'identity check'):
                helper.check_case('demo', self.fixture.library, 'assertion_failure', self.fixture.root / 'wrong', self.launcher)


if __name__ == '__main__':
    unittest.main()
