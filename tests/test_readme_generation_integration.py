"""New generation accounting composes with the published README comparison designs."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_evaluation as fixtures
from workflow.ablation import load
from workflow.evaluation import run_evaluation
from workflow.evaluation_setup import CONDITIONS


REFRESH = ('Unchanged generated README', 'Selected API refresh', 'Full README refresh')


class ReadmeGenerationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.EvaluationTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        cfg = self.fixture.config['readme_evaluation']
        cfg['design'] = 'selective_refresh'
        cfg['documents'] = {new: cfg['documents'][old] for new, old in zip(REFRESH, CONDITIONS)}
        cfg['common'].update(
            max_snippet_fixes=1, repair_max_output_tokens=250, repair_context='distilled',
            documentation_selection={'policy': 'qualified_sections', 'api_headings': {'f': 'f [object]'}})
        for paths in cfg['documents'].values():
            Path(paths[0]).write_text('## API Test: `f [object]`\nRELEVANT_CONTRACT\n'
                                      '## Other\nUNRELATED_CONTRACT\n')

    def test_selective_retrieval_distilled_repair_caps_and_replay_work_together(self):
        fixture = self.fixture
        fixture.adapter.write_text(fixture.adapter.read_text().replace(
            "public_feedback='Independent checks failed'",
            "public_feedback='exact diagnostic\\n\\nexact diagnostic'"))
        fixture.model.write_text("""import json,sys
r=json.load(sys.stdin)
assert 'RELEVANT_CONTRACT' in r['prompt'] and 'UNRELATED_CONTRACT' not in r['prompt']
repair='COMPLETE PREVIOUS SOLUTION' in r['prompt']
assert r['max_output_tokens']==(250 if repair else 100)
if repair:
    assert r['prompt'].count('exact diagnostic')==1
print(json.dumps({'code':'correct' if repair else 'wrong',
 'response_status':'completed', 'usage':{'input_tokens':5,'output_tokens':2}}))
""")
        fixture.write_config()
        study, out = fixture.freeze(), fixture.root / 'run'
        summary = run_evaluation(study, out, condition=REFRESH[1])
        for kind in ('micro', 'puzzle'):
            self.assertEqual(0, summary['metrics'][REFRESH[1]][kind]['first_attempt_correct'])
            self.assertEqual(1, summary['metrics'][REFRESH[1]][kind]['correct_within_budget'])
        rows = list(out.glob('*/*/result.json'))
        self.assertEqual(2, len(rows))
        for path in rows:
            row = load(path)
            self.assertEqual(1, row['first_pass_round'])
            self.assertEqual(2, row['resources']['provider_calls'])
            self.assertEqual('qualified_sections', load(path.parent / 'documentation_exposure.json')['policy'])
            receipt = load(path.parent / 'round_01/repair_context.json')
            self.assertEqual(1, receipt['repeated_paragraphs_removed'])
            self.assertFalse(receipt['code_truncated'])
        with patch('workflow.evaluation.invoke', side_effect=AssertionError('Unexpected provider repeat')):
            self.assertEqual(summary, run_evaluation(study, out, condition=REFRESH[1]))

    def test_stopped_generations_report_selective_names_and_keep_fixed_denominators(self):
        fixture = self.fixture
        fixture.model.write_text("""import json,sys
json.load(sys.stdin)
print(json.dumps({'code':'partial', 'response_status':'incomplete',
 'incomplete_reason':'max_output_tokens', 'usage':{'input_tokens':5,'output_tokens':2}}))
""")
        fixture.write_config()
        study, out = fixture.freeze(), fixture.root / 'run'
        with patch('workflow.evaluation._checked_execution') as checker:
            summary = run_evaluation(study, out, condition=REFRESH[0])
            checker.assert_not_called()
        self.assertEqual(set(REFRESH), set(summary['generation_classifications']))
        self.assertEqual(2, summary['generation_classifications'][REFRESH[0]]['generation_incomplete'])
        for kind in ('micro', 'puzzle'):
            self.assertEqual(1, summary['metrics'][REFRESH[0]][kind]['selected'])
            self.assertEqual(1, summary['metrics'][REFRESH[0]][kind]['unresolved'])
            self.assertEqual(0, summary['metrics'][REFRESH[0]][kind]['completed'])
        self.assertIn('| ' + REFRESH[0] + ' | 2 | 0 | 0 | 0 |', (out / 'REPORT.md').read_text())
        with patch('workflow.evaluation.invoke', side_effect=AssertionError('Unexpected provider repeat')):
            self.assertEqual(summary, run_evaluation(study, out, condition=REFRESH[0], retry_provider=True))


if __name__ == '__main__':
    unittest.main()
