"""Real subprocess tests for binary diagnostics and process-group timeout recovery."""
import hashlib
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from aideal.execution import run_command
from aideal.native_execution_contract import native_check_passed


class BinaryProcessOutputTests(unittest.TestCase):
    def command(self, source):
        return shlex.join([sys.executable, '-c', source])

    def assert_raw(self, result, stream, expected):
        receipt = result.output_decoding['raw_streams'][stream]
        self.assertEqual(Path(receipt['path']).read_bytes(), expected)
        self.assertEqual(receipt['sha256'], hashlib.sha256(expected).hexdigest())
        self.assertEqual(receipt['bytes'], len(expected))

    def test_invalid_stderr_preserves_success_and_exact_raw_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            result = run_command(self.command('import os; os.write(1,b"__CHECK__ api 3\\nDONE\\n"); os.write(2,b"native \\x88 error\\n")'), cwd=root, env=os.environ, timeout=5)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, 'native \\x88 error\n')
            self.assert_raw(result, 'stderr', b'native \x88 error\n')
            self.assertNotIn('stdout', result.output_decoding['raw_streams'])
            self.assertTrue(native_check_passed(result.stdout, result.stderr, result.returncode, 'api', {'require_correctness':True,'success_marker':'DONE'}))

    def test_invalid_stdout_does_not_turn_failed_program_into_success(self):
        with tempfile.TemporaryDirectory() as root:
            result = run_command(self.command('import os; os.write(1,b"\\xff\\n__CHECK__ api 3\\nDONE\\n"); raise SystemExit(7)'), cwd=root, env=os.environ, timeout=5)
            self.assertEqual(result.returncode, 7)
            self.assert_raw(result, 'stdout', b'\xff\n__CHECK__ api 3\nDONE\n')
            self.assertFalse(native_check_passed(result.stdout, result.stderr, result.returncode, 'api', {'require_correctness':True,'success_marker':'DONE'}))

    def test_timeout_retains_binary_output_and_reaps_process(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                run_command(self.command('import os,time; os.write(1,b"start\\xff"); os.write(2,b"error\\x88"); time.sleep(10)'), cwd=root, env=os.environ, timeout=.15)
            result=caught.exception
            self.assertEqual(result.stdout,'start\\xff')
            self.assertEqual(result.stderr,'error\\x88')
            self.assert_raw(result, 'stdout', b'start\xff')
            self.assert_raw(result, 'stderr', b'error\x88')
            self.assertTrue(result.cleanup['shell_reaped'])
            self.assertFalse((Path(root)/'.aideal_unreconciled_process.json').exists())

    def test_valid_utf8_preserves_universal_newlines_without_duplicate_raw_files(self):
        with tempfile.TemporaryDirectory() as root:
            result=run_command(self.command('import os; os.write(1,"héllo\\r\\nnext\\rlast".encode()); os.write(2,b"normal\\r\\n")'),cwd=root,env=os.environ,timeout=5)
            self.assertEqual(result.stdout,'héllo\nnext\nlast')
            self.assertEqual(result.stderr,'normal\n')
            self.assertEqual(result.output_decoding['raw_streams'],{})
            self.assertEqual(list(Path(root).iterdir()),[])

if __name__=='__main__':unittest.main()

# Exercise the actual replay writer, including verification on resume.
import json
from unittest.mock import patch
import pytest
from test_rescore_native_programs import setup_saved, r

@pytest.mark.parametrize('exit_code', [0, 7])
def test_replay_binds_raw_diagnostic_and_rejects_tampering(tmp_path, exit_code):
    snippet='import os\nos.write(2, b"bad \\x88 stderr")\nprint("__CHECK__ f ok")'
    if exit_code:snippet+='\nraise SystemExit(7)'
    source=setup_saved(tmp_path, {'f':snippet})
    originals={p:p.read_bytes() for p in source.parent.rglob('*') if p.is_file()}
    with patch('aideal.llm.invoke_text', side_effect=AssertionError('no model calls')):
        result=r.run_program_case(source,'f',tmp_path/'replay/f')
    assert result['status']==('fail' if exit_code else 'pass')
    assert result['llm_calls']==0
    execution=json.loads(Path(result['scala_file']).with_name('execution.json').read_text())
    raw=execution['output_decoding']['raw_streams']['stderr']
    assert Path(raw['path']).read_bytes()==b'bad \x88 stderr'
    assert raw in result['evidence_bindings']
    assert all(p.read_bytes()==data for p,data in originals.items())
    assert r.run_program_case(source,'f',tmp_path/'replay/f')==result
    Path(raw['path']).write_bytes(b'edited')
    with pytest.raises(ValueError, match='evidence changed'):
        r.run_program_case(source,'f',tmp_path/'replay/f')
