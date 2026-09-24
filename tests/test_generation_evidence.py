"""Completion classification must retain the published invocation/audit evidence."""
from pathlib import Path
import sys
import tempfile
import unittest

from workflow.ablation import verify_artifact
from workflow.execution import invoke
from workflow.generation import rounds


class GenerationEvidenceTests(unittest.TestCase):
    def test_incomplete_response_keeps_bound_invocation_and_provider_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = root / 'round_00/provider_001'
            script = (
                'import json; from pathlib import Path; '
                'p=Path("provider_audit"); p.mkdir(); '
                '(p/"request.json").write_text(json.dumps({"max_output_tokens": 128})); '
                '(p/"response.json").write_text(json.dumps({"status": "incomplete"})); '
                'print(json.dumps({"code":"partial", "response_status":"incomplete"}))'
            )
            result = invoke([sys.executable, '-c', script], {'prompt': 'synthetic'}, attempt, 5)
            self.assertEqual(result['status'], 'ok')
            record = rounds(root)[0]['providers'][0]['files']
            expected = {'request.json', 'process.json', 'stdout.txt', 'stderr.txt',
                        'invocation.json', 'provider_audit/request.json', 'provider_audit/response.json'}
            self.assertEqual(set(record), expected)
            self.assertTrue(all(verify_artifact(value) for value in record.values()))
            (attempt / 'provider_audit/response.json').write_text('{"status":"completed"}')
            self.assertFalse(verify_artifact(record['provider_audit/response.json']))
            self.assertNotEqual(record, rounds(root)[0]['providers'][0]['files'])


if __name__ == '__main__':
    unittest.main()
