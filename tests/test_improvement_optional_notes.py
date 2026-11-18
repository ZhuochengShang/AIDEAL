"""Omitted narrative notes must not relax executable proposal validation."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workflow.improvement_suggestions import validate_suggestions


class OptionalNotesTests(unittest.TestCase):
    def setUp(self):
        self.context = {'apis': [{'id': 'python:lib.validate', 'name': 'validate'}],
                        'development_errors': [], 'alias_destination': 'lib/aliases.py'}
        self.proposal = {'aliases': [{'name': 'validate_beats', 'target_function': 'python:lib.validate',
                                     'rationale': 'Names the input domain.'}],
                         'alias_code': 'from lib import validate\ndef validate_beats(x):\n    return validate(x)\n',
                         'alias_interface': 'validate_beats(x) forwards to lib.validate(x).', 'hints': []}

    def test_absent_notes_normalized_without_mutating_raw_response(self):
        original = copy.deepcopy(self.proposal)
        accepted = validate_suggestions(self.proposal, self.context)
        self.assertEqual('', accepted['notes'])
        self.assertEqual(original, self.proposal)
        self.assertNotIn('notes', self.proposal)

    def test_explicit_null_and_nontext_notes_rejected(self):
        for value in [None, 0, [], {}]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'notes'):
                validate_suggestions({**self.proposal, 'notes': value}, self.context)

    def test_missing_functional_fields_and_unknown_keys_rejected(self):
        for field in ['aliases', 'alias_code', 'alias_interface', 'hints']:
            changed = copy.deepcopy(self.proposal)
            del changed[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_suggestions(changed, self.context)
        with self.assertRaises(ValueError):
            validate_suggestions({**self.proposal, 'invented': ''}, self.context)

    def test_missing_rationale_and_undefined_wrapper_still_rejected(self):
        changed = copy.deepcopy(self.proposal)
        del changed['aliases'][0]['rationale']
        with self.assertRaises(ValueError):
            validate_suggestions(changed, self.context)
        changed = {**self.proposal, 'alias_code': 'from lib import validate as validate_beats\n'}
        with self.assertRaisesRegex(ValueError, 'does not define each proposed name'):
            validate_suggestions(changed, self.context)


if __name__ == '__main__':
    unittest.main()
