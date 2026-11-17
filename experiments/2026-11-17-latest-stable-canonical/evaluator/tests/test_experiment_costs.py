"""Cost reports count saved receipts once and keep unknown spend explicit."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('experiment_costs', ROOT / 'scripts/report_experiment_costs.py')
costs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(costs)


class ExperimentCostTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='aideal-costs-offline-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.r0, self.readme = self.root / 'original', self.root / 'authoring'
        self.r0.mkdir()
        self.readme.mkdir()
        self.plan = {'libraries': {'demo': {'r0_apis': 4, 'readme_entries': 3}}}

    def receipt(self, root, name, *, phase=None, api='f', status='returned', usage=None, model=costs.MODEL):
        directory = root / 'demo' / name
        directory.mkdir(parents=True)
        request = {'api': api, 'model': model, 'system': 'DO NOT INCLUDE PROMPTS',
                   'user': 'private fixture description', 'round': 0}
        if phase:
            request['phase'] = phase
        (directory / 'request.json').write_text(json.dumps(request))
        (directory / 'provider.json').write_text(json.dumps({'status': status, 'usage': usage}))
        return directory

    def test_partial_progress_counts_billable_attempts_once_and_not_by_model(self):
        usage = {'calls': 1, 'input_tokens': 1000, 'output_tokens': 100,
                 'by_model': {'google:' + costs.MODEL: {'calls': 1, 'input_tokens': 1000, 'output_tokens': 100}}}
        self.receipt(self.r0, 'execution/run_f/attempt_0001', usage=usage)
        self.receipt(self.r0, 'execution/run_f/attempt_0002', usage=usage)
        self.receipt(self.r0, 'execution/run_g/attempt_0001', api='g', status='error',
                     usage={'calls': 0, 'input_tokens': 0, 'output_tokens': 0})
        self.receipt(self.readme, 'author_calls/hash_a/attempt_0001', phase='entry',
                     status='complete', usage={'calls': 1, 'input_tokens': 800, 'output_tokens': 200})
        self.receipt(self.readme, 'author_calls/hash_b/attempt_0001', phase='distill', api=None,
                     status='complete', usage={'calls': 1, 'input_tokens': 2000, 'output_tokens': 300})
        report = costs.build_report(self.r0, self.readme, self.plan)
        total = report['totals']
        self.assertEqual((4800, 700, 5), (total['input_tokens'], total['output_tokens'], total['requests']))
        self.assertEqual(1, total['unknown_usage_requests'])
        self.assertEqual(1, total['failed_unknown_usage_requests'])
        self.assertAlmostEqual(.00225, total['known_cost_usd'])
        stages = report['libraries']['demo']
        self.assertEqual((1, 3), (stages['r0']['unique_completed_units'], stages['r0']['remaining_units']))
        self.assertEqual(2, stages['r0']['mean_sample_requests'])
        self.assertEqual(2, stages['readme_entry']['remaining_units'])
        self.assertEqual(0, stages['readme_distill']['remaining_units'])
        self.assertAlmostEqual(.00445, total['known_plus_projected_cost_usd'])
        text = costs.markdown(report)
        self.assertNotIn('DO NOT INCLUDE PROMPTS', text)
        self.assertNotIn('private fixture', json.dumps(report))
        self.assertIn('excludes unknown costs', text)

    def test_failed_author_response_with_usage_is_priced_but_not_completed(self):
        self.receipt(self.readme, 'author_calls/hash/attempt_0001', phase='entry', status='failed_or_interrupted',
                     usage={'calls': 1, 'input_tokens': 400, 'output_tokens': 100})
        report = costs.build_report(self.r0, self.readme, self.plan)
        row = report['libraries']['demo']['readme_entry']
        self.assertEqual(0, row['unique_completed_units'])
        self.assertEqual(0, row['unknown_usage_requests'])
        self.assertAlmostEqual(.00025, row['known_cost_usd'])
        self.assertEqual('explicit scenario; not measured', row['projection_basis'])

    def test_other_models_are_unpriced_and_do_not_seed_projection_means(self):
        self.receipt(self.r0, 'run/attempt_0001', usage={'calls': 1, 'input_tokens': 40, 'output_tokens': 10}, model='other-model')
        report = costs.build_report(self.r0, self.readme, self.plan)
        self.assertEqual(1, report['totals']['unpriced_known_usage_requests'])
        self.assertEqual(0, report['totals']['known_cost_usd'])
        self.assertEqual(0, report['libraries']['demo']['r0']['mean_sample_requests'])

    def test_overlapping_roots_do_not_count_same_receipt_twice(self):
        self.receipt(self.r0, 'run/attempt_0001', usage={'calls': 1, 'input_tokens': 100, 'output_tokens': 10})
        rows = costs.scan(self.r0, self.r0)
        self.assertEqual(1, len(rows))

    def test_unfinished_and_malformed_receipts_remain_unknown(self):
        path = self.receipt(self.r0, 'run/a', status='started', usage=None)
        (path / 'provider.json').write_text('{unfinished')
        self.receipt(self.r0, 'run/b', status='returned', usage={'calls': 'one', 'input_tokens': 10, 'output_tokens': 20})
        report = costs.build_report(self.r0, self.readme)
        self.assertEqual(2, report['totals']['unknown_usage_requests'])
        self.assertIsNone(report['totals']['estimated_remaining_cost_usd'])
        self.assertIsNone(report['libraries']['demo']['readme_distill']['planned_units'])

    def test_explicit_scenario_and_plan_can_project_before_calls(self):
        scenario = {stage: {'input_tokens': 100, 'output_tokens': 10} for stage in costs.SCENARIO}
        report = costs.build_report(self.r0, self.readme, self.plan, scenario)
        self.assertEqual(0, report['totals']['requests'])
        self.assertAlmostEqual(8 * costs.price(100, 10), report['totals']['known_plus_projected_cost_usd'])
        self.assertIn('explicit scenario; not measured', costs.markdown(report))

    def test_revalidated_response_finishes_unit_without_double_billing(self):
        old = self.receipt(self.readme, 'author_calls/hash/attempt_0001', phase='entry',
                           status='failed_or_interrupted', usage={'calls': 1, 'input_tokens': 400, 'output_tokens': 100})
        (old / 'response.txt').write_text('completed entry containing a source note')
        path = self.readme / 'demo/revisions/new/author_replay/hash/replay_receipt.json'
        path.parent.mkdir(parents=True)
        receipt = {'action': 'revalidated_returned_response', 'files': {
            str(old / name): hashlib.sha256((old / name).read_bytes()).hexdigest()
            for name in ('request.json', 'response.txt', 'provider.json')}}
        path.write_text(json.dumps(receipt))
        report = costs.build_report(self.r0, self.readme, self.plan)
        row = report['libraries']['demo']['readme_entry']
        self.assertEqual((1, 2, 1), (row['unique_completed_units'], row['remaining_units'], row['requests']))
        self.assertEqual((400, 100), (report['totals']['input_tokens'], report['totals']['output_tokens']))
        self.assertEqual(1, report['totals']['replayed_units'])
        self.assertAlmostEqual(.00025, row['known_cost_usd'])
        (old / 'response.txt').write_text('changed historical response')
        with self.assertRaisesRegex(ValueError, 'replay evidence changed'):
            costs.build_report(self.r0, self.readme, self.plan)

    def test_missing_roots_and_bad_counts_fail_clearly(self):
        with self.assertRaisesRegex(ValueError, 'not a directory'):
            costs.build_report(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'nonnegative integers'):
            costs.build_report(self.r0, self.readme, {'libraries': {'demo': {'r0_apis': -1}}})


if __name__ == '__main__':
    unittest.main()
