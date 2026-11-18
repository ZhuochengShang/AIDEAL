"""Execution regressions for preloaded Python inputs and nested snippet scopes."""
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.evaluation_scope import bind_python_scaffold_inputs


class PythonInputScopeTests(unittest.TestCase):
    def execute(self, source):
        namespace = {}
        exec(compile(source, '<scope regression>', 'exec'), namespace)
        return namespace

    def test_mir_eval_read_then_rebind_outer_fixtures(self):
        source = '''
result = []
def adjust_intervals(intervals, labels):
    return intervals[1:], labels[1:]
def run():
    ref_intervals = [[0., 1.], [1., 2.]]
    ref_labels = ['a', 'b']
    def api_test():
        # TODO API_TEST_START
        ref_intervals, ref_labels = adjust_intervals(ref_intervals, ref_labels)
        assert ref_intervals == [[1., 2.]]
        assert ref_labels == ['b']
        result.append((ref_intervals, ref_labels))
        # TODO API_TEST_END
        pass
    api_test()
    assert ref_labels == ['a', 'b']
run()
'''
        with self.assertRaises(UnboundLocalError):
            self.execute(source)
        fixed = bind_python_scaffold_inputs(source)
        self.assertEqual(self.execute(fixed)['result'], [([[1., 2.]], ['b'])])
        self.assertIn('ref_intervals, ref_labels = adjust_intervals(ref_intervals, ref_labels)', fixed)
        self.assertEqual(bind_python_scaffold_inputs(fixed), fixed)

    def test_import_and_reassignment_have_initialized_locals(self):
        source = '''
import math
result = []
def run():
    values = [4]
    def api_test():
        # TODO API_TEST_START
        value = math.sqrt(values[0])
        import math
        values = [value]
        result.append(values[0])
        # TODO API_TEST_END
        pass
    api_test()
run()
'''
        self.assertEqual(self.execute(bind_python_scaffold_inputs(source))['result'], [2.0])

    def test_existing_parameters_and_nested_candidate_function(self):
        source = '''
result = []
def run():
    inputs = [3]
    def api_test(flag=True, *, scale=2):
        # TODO API_TEST_START
        inputs = [inputs[0] * scale]
        def read():
            return inputs[0]
        result.append(read())
        # TODO API_TEST_END
        pass
    api_test()
run()
'''
        self.assertEqual(self.execute(bind_python_scaffold_inputs(source))['result'], [6])

    def test_candidate_assignments_do_not_become_scaffold_bindings(self):
        source = '''
def run():
    inputs = [1]
    def api_test():
        # TODO API_TEST_START
        missing = missing + 1
        # TODO API_TEST_END
        pass
    api_test()
run()
'''
        fixed = bind_python_scaffold_inputs(source)
        self.assertNotIn('missing=missing', fixed)
        with self.assertRaises(UnboundLocalError):
            self.execute(fixed)

    def test_global_and_nonlocal_are_not_converted_to_arguments(self):
        source = '''
result = 0
def run():
    count = 1
    def api_test():
        # TODO API_TEST_START
        global result
        nonlocal count
        count += 1
        result = count
        # TODO API_TEST_END
        pass
    api_test()
run()
'''
        fixed = bind_python_scaffold_inputs(source)
        self.assertEqual(self.execute(fixed)['result'], 2)
        self.assertNotIn('count=count', fixed)
        self.assertNotIn('result=result', fixed)

    def test_conditional_and_future_outer_locals_not_eagerly_read(self):
        source = '''
value = 5
def run():
    if False:
        unavailable = 2
    def api_test():
        # TODO API_TEST_START
        assert True
        # TODO API_TEST_END
        pass
    value = 9
    api_test()
run()
'''
        fixed = bind_python_scaffold_inputs(source)
        self.assertNotIn('unavailable=unavailable', fixed)
        self.assertNotIn('value=value', fixed)
        self.execute(fixed)

    def test_malformed_candidate_is_left_for_execution_checker(self):
        source = 'def run():\n    # TODO API_TEST_START\n    if ???\n    # TODO API_TEST_END\n'
        self.assertEqual(bind_python_scaffold_inputs(source), source)

    def test_explicit_scaffold_matches_saved_program_path(self):
        scaffold = '''
def run():
    values = [1]
    def api_test():
        # TODO API_TEST_START
        pass
        # TODO API_TEST_END
    api_test()
run()
'''
        source = scaffold.replace('        pass\n', '        values = values + [2]\n        assert values == [1, 2]\n')
        a = bind_python_scaffold_inputs(source, scaffold)
        self.assertEqual(a, bind_python_scaffold_inputs(source))
        self.execute(a)

    def test_class_namespace_is_not_treated_as_lexical_method_input(self):
        source = '''
class Example:
    value = 1
    def method(self):
        # TODO API_TEST_START
        assert self.value == 1
        # TODO API_TEST_END
        pass
'''
        self.assertEqual(bind_python_scaffold_inputs(source), source)


if __name__ == '__main__':
    unittest.main()
