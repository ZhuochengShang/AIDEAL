import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('admission', Path(__file__).with_name('admit_alias_banks.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.coverage = {'requested_definitions': 2, 'planned_definitions': 2,
                         'omitted_requested_definitions': 0}

    def test_order_does_not_change_identity_set(self):
        module.exact_ids(['one', 'two'], ['two', 'one'], self.coverage, 2)

    def test_same_count_wrong_api_rejected(self):
        with self.assertRaises(ValueError):
            module.exact_ids(['one', 'two'], ['one', 'other'], self.coverage, 2)

    def test_repeated_api_rejected(self):
        with self.assertRaises(ValueError):
            module.exact_ids(['one', 'two'], ['one', 'one'], self.coverage, 2)

    def test_unplanned_omission_rejected(self):
        with self.assertRaises(ValueError):
            module.exact_ids(['one', 'two'], ['one', 'two'],
                             {**self.coverage, 'omitted_requested_definitions': 1}, 2)


if __name__ == '__main__':
    unittest.main()
