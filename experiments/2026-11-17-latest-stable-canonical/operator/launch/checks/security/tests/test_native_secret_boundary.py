"""No credentials or subject libraries: synthetic child-process boundary checks."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audited_execution', ROOT / 'vendor/aideal_engine/src/aideal/execution.py')
execution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(execution)

KEYS = ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
        'AZURE_OPENAI_API_KEY', 'DUMMY_API_TOKEN', 'DUMMY_ACCESS_TOKEN', 'AWS_SECRET_ACCESS_KEY')
SAFE = 'AIDEAL_SYNTHETIC_SAFE_OPTION'

class NativeSecretBoundaryTests(unittest.TestCase):
    def environment(self, root):
        # An explicitly constructed environment avoids reading real credentials.
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(root),
               SAFE: 'preserved', 'JAVA_HOME': '/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home'}
        env.update({name: 'dummy-secret-for-test' for name in KEYS})
        return env

    def probe(self):
        return ('import json, os; '
                f'assert all(key not in os.environ for key in {KEYS!r}); '
                f'assert os.environ[{SAFE!r}] == "preserved"; '
                'print(json.dumps({"secret_variables_absent": True, "safe_variable_preserved": True}))')

    def test_native_python_child_and_nested_subprocess(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            child = root / 'child.py'
            child.write_text(self.probe() + '\nimport subprocess, sys\nsubprocess.run([sys.executable, "-c", '+repr(self.probe())+'], check=True)\n')
            env = self.environment(root); before = dict(env)
            result = execution.run_command(shlex.join([sys.executable, str(child)]), cwd=root, env=env, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(env, before, 'Controller environment must remain untouched')
            rows=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row['secret_variables_absent'] and row['safe_variable_preserved'] for row in rows))

    def test_shell_build_then_real_scala_jvm(self):
        scalac = shutil.which('scalac'); scala = shutil.which('scala')
        self.assertIsNotNone(scalac, 'Scala compiler required for this concrete boundary check')
        self.assertIsNotNone(scala, 'Scala runner required for this concrete boundary check')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td);source=root/'SyntheticEnvironment.scala'
            quoted=', '.join(json.dumps(key) for key in KEYS)
            source.write_text('object SyntheticEnvironment { def main(args: Array[String]): Unit = {\n'
                              f'val names = Array({quoted})\n'
                              'require(names.forall(name => System.getenv(name) == null))\n'
                              f'require(System.getenv({json.dumps(SAFE)}) == "preserved")\n'
                              'println("SCALA_JVM_ENVIRONMENT_OK")\n} }\n')
            env=self.environment(root);before=dict(env)
            command=' && '.join([shlex.join([sys.executable,'-c',self.probe()]),
                                  shlex.join([scalac,'-d',str(root),str(source)]),
                                  shlex.join([scala,'-cp',str(root),'SyntheticEnvironment'])])
            result=execution.run_command(command,cwd=root,env=env,timeout=50)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('SCALA_JVM_ENVIRONMENT_OK',result.stdout)
            self.assertEqual(env,before)

    def test_actual_sedona_adapter_runpy_and_nested_child(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);program=root/'api_test.py'
            (root/'requested_target.json').write_text(json.dumps({'api_id':'sql:ST_Point','display_name':'ST_Point'}))
            program.write_text('# TODO API_TEST_START\n'+self.probe()+'\n'
                'import subprocess, sys\n'
                'subprocess.run([sys.executable, "-c", '+repr(self.probe())+'], check=True)\n'
                'print(\'__CHECK__ sql:ST_Point {"synthetic_environment_check": true}\')\n'
                '# TODO API_TEST_END\n')
            env=self.environment(root);before=dict(env)
            result=execution.run_command(shlex.join([sys.executable,str(ROOT/'scripts/sedonadb/run_snippet.py'),str(program)]),cwd=root,env=env,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('__CHECK__ sql:ST_Point',result.stdout)
            self.assertEqual(env,before)

if __name__ == '__main__':
    unittest.main(verbosity=2)
