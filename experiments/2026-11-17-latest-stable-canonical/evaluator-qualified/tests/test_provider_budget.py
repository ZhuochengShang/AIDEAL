"""Budget arithmetic, durable ambiguity, and cross-process overspend prevention."""
import json
import multiprocessing
from pathlib import Path
import tempfile
import unittest

from workflow.provider_budget import BudgetError, BudgetLedger, FRAMING_TOKENS, PRICES, digest


def reserve_parallel(path, queue):
    try:
        BudgetLedger(path, '0.05').reserve('system', 'prompt', 2048, digest('request'), digest('settings'))
        queue.put('reserved')
    except BudgetError:
        queue.put('blocked')


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'budget.json'
        self.ledger = BudgetLedger(self.path)

    def reserve(self, ledger=None, system='system', prompt='prompt', cap=2048):
        return (ledger or self.ledger).reserve(system, prompt, cap, digest('request'), digest('settings'))

    def read(self):
        return json.loads(self.path.read_text())

    def test_utf8_reservation_contains_no_prompt(self):
        self.reserve(system='秘密', prompt='private prompt body')
        row = self.read()['records'][0]
        bound = len('秘密private prompt body'.encode()) + FRAMING_TOKENS
        self.assertEqual(row['reserved_nanousd'], bound * PRICES['input'] + 2048 * PRICES['output'])
        self.assertEqual(row['charged_nanousd'], row['reserved_nanousd'])
        self.assertNotIn('private prompt body', self.path.read_text())
        self.assertNotIn('秘密', self.path.read_text())

    def test_known_usage_releases_to_actual_cached_price(self):
        key = self.reserve()
        receipt = self.ledger.finish(key, usage={'input_tokens': 100, 'cached_input_tokens': 80,
            'output_tokens': 30}, status='completed', response_id='resp_test')
        self.assertEqual(receipt['state'], 'settled')
        self.assertEqual(receipt['charged_nanousd'], 20 * 1750 + 80 * 175 + 30 * 14000)
        self.assertLess(receipt['charged_nanousd'], receipt['reserved_nanousd'])
        self.reserve()  # Resume validates settled arithmetic.

    def test_ambiguous_error_retains_full_reservation(self):
        key = self.reserve()
        receipt = self.ledger.finish(key, failure={'type': 'TimeoutError'})
        self.assertEqual(receipt['state'], 'uncertain')
        self.assertEqual(receipt['charged_nanousd'], receipt['reserved_nanousd'])
        self.assertEqual(self.read()['records'][0]['failure'], {'type': 'TimeoutError'})

    def test_missing_invalid_and_nonfinal_usage_never_releases(self):
        examples = [(None, 'completed'), ({'input_tokens': 1, 'output_tokens': 1}, 'completed'),
            ({'input_tokens': 1, 'cached_input_tokens': 2, 'output_tokens': 1}, 'completed'),
            ({'input_tokens': -1, 'cached_input_tokens': 0, 'output_tokens': 1}, 'completed'),
            ({'input_tokens': 1, 'cached_input_tokens': False, 'output_tokens': 1}, 'completed'),
            ({'input_tokens': 1, 'cached_input_tokens': 0, 'output_tokens': 1}, 'in_progress')]
        for usage, status in examples:
            with self.subTest(usage=usage, status=status):
                receipt = self.ledger.finish(self.reserve(), usage=usage, status=status)
                self.assertEqual(receipt['state'], 'uncertain')
                self.assertEqual(receipt['charged_nanousd'], receipt['reserved_nanousd'])

    def test_shared_budget_blocks_second_reservation(self):
        ledger = BudgetLedger(self.path, '0.05')
        self.reserve(ledger)
        with self.assertRaisesRegex(BudgetError, 'cannot cover'):
            self.reserve(BudgetLedger(self.path, '0.05'))
        self.assertEqual(len(self.read()['records']), 1)

    def test_simultaneous_processes_cannot_spend_same_capacity(self):
        context = multiprocessing.get_context('fork')
        queue = context.Queue()
        workers = [context.Process(target=reserve_parallel, args=(str(self.path), queue)) for _ in range(6)]
        for worker in workers:
            worker.start()
        outcomes = [queue.get(timeout=10) for _ in workers]
        for worker in workers:
            worker.join(timeout=10)
            self.assertEqual(worker.exitcode, 0)
        self.assertEqual(outcomes.count('reserved'), 1)
        self.assertEqual(outcomes.count('blocked'), 5)
        self.assertEqual(len(self.read()['records']), 1)

    def test_missing_ledger_cannot_be_recreated(self):
        self.reserve()
        self.path.unlink()
        with self.assertRaisesRegex(BudgetError, 'recreation is forbidden'):
            self.reserve()

    def test_missing_lock_or_corrupt_ledger_fails_closed(self):
        self.reserve()
        Path(str(self.path) + '.lock').unlink()
        with self.assertRaisesRegex(BudgetError, 'identity'):
            self.reserve()
        self.path.write_text('{bad json')
        with self.assertRaisesRegex(BudgetError, 'refusing to reset'):
            self.reserve()

    def test_model_prices_and_cap_cannot_change_on_resume(self):
        self.reserve()
        original = self.read()
        for field, value in [('model', 'gpt-other'), ('prices_nanousd_per_token', {'input': 1}),
                             ('max_cost_nanousd', 1)]:
            with self.subTest(field=field):
                self.path.write_text(json.dumps({**original, field: value}))
                with self.assertRaisesRegex(BudgetError, 'automatic reset'):
                    self.reserve()
        self.path.write_text(json.dumps(original))
        with self.assertRaisesRegex(BudgetError, 'cap'):
            self.reserve(BudgetLedger(self.path, '4'))

    def test_invalid_cap_and_negative_record_rejected(self):
        for cap in ('5.0001', '0', '-1', 'NaN', 'Infinity', 'abc', '0.0000000001'):
            with self.subTest(cap=cap), self.assertRaises(BudgetError):
                BudgetLedger(self.path, cap)
        self.reserve()
        data = self.read()
        data['records'][0]['charged_nanousd'] = -1
        self.path.write_text(json.dumps(data))
        with self.assertRaisesRegex(BudgetError, 'Invalid ledger record'):
            self.reserve()

    def test_reservation_overrun_is_saved_and_blocks_future_calls(self):
        key = self.reserve(cap=1)
        with self.assertRaisesRegex(BudgetError, 'ledger is blocked'):
            self.ledger.finish(key, status='completed', usage={
                'input_tokens': 1, 'cached_input_tokens': 0, 'output_tokens': 100000})
        self.assertEqual(self.read()['records'][0]['charged_nanousd'], 1750 + 100000 * 14000)
        with self.assertRaisesRegex(BudgetError, 'cannot cover'):
            self.reserve()

    def test_double_settlement_and_duplicate_record_rejected(self):
        key = self.reserve()
        self.ledger.finish(key)
        with self.assertRaisesRegex(BudgetError, 'already finalized'):
            self.ledger.finish(key)
        data = self.read()
        data['records'].append(data['records'][0])
        self.path.write_text(json.dumps(data))
        with self.assertRaisesRegex(BudgetError, 'Invalid ledger record'):
            self.reserve()


if __name__ == '__main__':
    unittest.main()
