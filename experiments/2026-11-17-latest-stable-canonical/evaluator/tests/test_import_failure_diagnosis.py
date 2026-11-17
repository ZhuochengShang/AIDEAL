"""Import-failure attribution requires actual, unambiguous candidate API use."""
import unittest

from workflow.failure_diagnosis import diagnose_failure


OWNER = 'edu.ucr.cs.bdlab.beast.geolite.RasterMetadata'
WRONG = 'edu.ucr.cs.bdlab.raptor.RasterMetadata'
IDENTITY = 'RasterMetadata.scala:219:rescale'


class ImportFailureDiagnosisTests(unittest.TestCase):
    def setUp(self):
        self.index = {'records': [], 'api_function_ids': {OWNER + '.rescale': IDENTITY}}
        self.code = f'import {WRONG}\nval metadata = new RasterMetadata(0, 0, 8, 4)\nmetadata.rescale(4, 2)\n'
        self.feedback = (f'DevelopmentProbe.scala:4: error: object RasterMetadata is not a member of package edu.ucr.cs.bdlab.raptor\n'
                         f'import {WRONG}\n                                ^\n')

    def diagnose(self, code=None, feedback=None):
        return diagnose_failure(self.index, {'code': code or self.code, 'feedback': feedback or self.feedback,
                                           'target_apis': ['a.deliberately.wrong.task.target']})

    def test_exact_bad_import_with_constructed_receiver_identifies_called_method(self):
        result = self.diagnose()
        self.assertEqual(result['status'], 'identified')
        self.assertEqual(result['function_id'], IDENTITY)
        self.assertEqual(result['evidence'][0]['kind'], 'compiler_import_and_explicit_call')
        self.assertEqual(result['evidence'][0]['canonical_owner'], OWNER)

    def test_direct_owner_call_is_supported(self):
        code = f'import {WRONG}\nRasterMetadata.rescale(4, 2)\n'
        self.assertEqual(self.diagnose(code)['function_id'], IDENTITY)

    def test_import_without_actual_known_call_does_not_attribute_from_task(self):
        for code in (f'import {WRONG}\nval metadata = new RasterMetadata(0, 0, 8, 4)\n',
                     self.code.replace('metadata.rescale', 'somethingElse.rescale')):
            self.assertEqual(self.diagnose(code)['status'], 'unresolved_function')

    def test_factory_return_type_is_not_guessed(self):
        code = self.code.replace('new RasterMetadata(0, 0, 8, 4)', 'makeMetadata()')
        self.assertEqual(self.diagnose(code)['status'], 'unresolved_function')

    def test_homonymous_owner_is_ambiguous_and_receives_no_attribution(self):
        self.index['api_function_ids']['another.package.RasterMetadata.rescale'] = 'Other.scala:1:rescale'
        self.assertEqual(self.diagnose()['status'], 'unresolved_function')

    def test_multiple_called_api_functions_are_ambiguous(self):
        self.index['api_function_ids'][OWNER + '.gridToModel'] = 'RasterMetadata.scala:150:gridToModel'
        result = self.diagnose(self.code + 'metadata.gridToModel(1, 2)\n')
        self.assertEqual(result['status'], 'ambiguous_function')
        self.assertEqual(set(result['candidate_function_ids']), {IDENTITY, 'RasterMetadata.scala:150:gridToModel'})

    def test_comments_and_strings_cannot_supply_constructor_or_method_use(self):
        cases = [self.code.replace('val metadata', '// val metadata'),
                 self.code.replace('metadata.rescale(4, 2)', '// metadata.rescale(4, 2)'),
                 f'import {WRONG}\nval text = "val metadata = new RasterMetadata(1); metadata.rescale(4, 2)"\n',
                 '// ' + self.code]
        for code in cases:
            self.assertEqual(self.diagnose(code)['status'], 'unresolved_function')

    def test_wrong_import_echo_or_unrelated_owner_is_not_accepted(self):
        self.assertEqual(self.diagnose(feedback=self.feedback.replace(f'import {WRONG}', 'import unrelated.Other'))['status'], 'unresolved_function')
        self.assertEqual(self.diagnose(feedback=self.feedback.replace('object RasterMetadata', 'object Different'))['status'], 'unresolved_function')

    def test_correct_canonical_import_failure_is_dependency_issue_not_namespace_guess(self):
        code = self.code.replace(WRONG, OWNER)
        feedback = self.feedback.replace(WRONG, OWNER).replace('package edu.ucr.cs.bdlab.raptor', 'package edu.ucr.cs.bdlab.beast.geolite')
        self.assertEqual(self.diagnose(code, feedback)['status'], 'unresolved_function')

    def test_reassigned_or_shadowed_receiver_does_not_supply_attribution(self):
        code = self.code.replace('metadata.rescale', 'metadata = anotherObject\nmetadata.rescale')
        self.assertEqual(self.diagnose(code)['status'], 'unresolved_function')

    def test_local_class_with_same_name_does_not_inherit_catalog_identity(self):
        code = self.code + 'class RasterMetadata { def rescale(x: Int, y: Int) = x }\n'
        self.assertEqual(self.diagnose(code)['status'], 'unresolved_function')

    def test_java_plain_import_and_explicit_constructor(self):
        code = f'import {WRONG};\nRasterMetadata metadata = new RasterMetadata(0, 0, 8, 4);\nmetadata.rescale(4, 2);\n'
        feedback = (f'Candidate.java:1: error: package edu.ucr.cs.bdlab.raptor does not exist\n'
                    f'import {WRONG};\n                                ^\n')
        self.assertEqual(self.diagnose(code, feedback)['function_id'], IDENTITY)

    def test_duplicate_short_imports_are_not_resolved_by_guessing(self):
        code = self.code + f'import {OWNER}\n'
        self.assertEqual(self.diagnose(code)['status'], 'unresolved_function')


if __name__ == '__main__':
    unittest.main()
