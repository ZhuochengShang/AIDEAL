"""A prompt preview must not imply that its SQL was executed."""
from pathlib import Path
import tempfile
import unittest

from workflow.ablation import save
from studies.sedonadb.trace import trace


class TraceTests(unittest.TestCase):
    def test_preview_is_labeled_and_writes_only_inside_the_selected_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / 'studies/sedonadb/evidence/sql_reference_inventory.json', [{
                'api': 'ST_Test', 'kind': 'function_reference',
                'source': 'some/source.qmd', 'examples': ['SELECT ST_Test();'],
            }])
            docs = root / 'studies/sedonadb/evidence/reference/source.qmd'
            docs.parent.mkdir(parents=True)
            docs.write_text('A documented example, not an execution result.')
            template = root / 'prompts/comprehension_write_exec.md'
            template.parent.mkdir()
            template.write_text('{language}: {api_name}\n{api_body}\n{receiver}')
            result = trace(root, 'ST_Test')
            self.assertFalse(result['model_called'])
            self.assertTrue(result['preview_is_not_a_historical_delivered_prompt'])
            self.assertEqual([], result['recorded_examples'])
            out = root / '.runs/traces/ST_Test'
            self.assertEqual('SELECT ST_Test();', (out / 'documented_example_001.sql').read_text())
            self.assertFalse((out / 'executed_example_001.sql').exists())
            self.assertIn('ST_Test', Path(result['prompt_preview']).read_text())

    def test_unknown_api_does_not_create_a_trace_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / 'studies/sedonadb/evidence/sql_reference_inventory.json', [])
            with self.assertRaisesRegex(ValueError, 'Unknown SQL documentation API'):
                trace(root, '../unknown')
            self.assertFalse((root / '.runs').exists())


if __name__ == '__main__':
    unittest.main()
