"""Portable checker tests; no Java, RDPro or provider execution."""
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import json
import tempfile

from execute import TARGET_EVENTS, check_outputs, publish, verify_class_loading
from build_backends import bind


class CheckerTests(unittest.TestCase):
    def test_numeric_oracle_and_qualified_target_are_independent(self):
        target = 'edu.ucr.cs.bdlab.beast.geolite.Feature.readType'
        oracle = {'tests': [{'input': [2], 'expected': [2, 1]}]}
        trace = [TARGET_EVENTS[target]]
        right, _ = check_outputs(oracle, 'AIDEAL_RESULT=[2,1]', trace, [target], 0)
        self.assertTrue(all(right[k] for k in ('execution_pass', 'oracle_pass', 'target_reached')))
        wrong, _ = check_outputs(oracle, 'AIDEAL_RESULT=[9,1]', trace, [target], 0)
        self.assertFalse(wrong['oracle_pass']); self.assertTrue(wrong['target_reached'])
        no_target, _ = check_outputs(oracle, 'AIDEAL_RESULT=[2,1]', [], [target], 0)
        self.assertTrue(no_target['oracle_pass']); self.assertFalse(no_target['target_reached'])
        wrong_receiver, _ = check_outputs(oracle, 'AIDEAL_RESULT=[2,1]',
            ['edu.ucr.cs.bdlab.beast.geolite.RasterSchemaHelper$.readType'], [target], 0)
        self.assertFalse(wrong_receiver['target_reached'])
        rescale = 'edu.ucr.cs.bdlab.beast.geolite.RasterMetadata.rescale'
        wrong_overload, _ = check_outputs(oracle, 'AIDEAL_RESULT=[2,1]',
            [rescale + '([Ledu/ucr/cs/bdlab/beast/geolite/RasterMetadata;II)Ledu/ucr/cs/bdlab/beast/geolite/RasterMetadata;'], [rescale], 0)
        self.assertFalse(wrong_overload['target_reached'])

    def test_missing_extra_nonfinite_boolean_outputs_never_pass(self):
        oracle = {'tests': [{'input': [1], 'expected': [1]}]}
        for text in ('', 'AIDEAL_RESULT=[NaN]', 'AIDEAL_RESULT=[true]',
                     'AIDEAL_RESULT=[1]\nAIDEAL_RESULT=[1]'):
            with self.subTest(text=text):
                result, _ = check_outputs(oracle, text, ['a.b'], ['a.b'], 0)
                self.assertFalse(result['oracle_pass'])

    def test_actual_classloader_origin_must_be_the_pinned_overlay(self):
        path = Path('/tmp/aideal space/library.jar')
        name = 'edu.ucr.cs.bdlab.beast.geolite.Feature$'
        trace = [name + '.readType']
        build = {'overlay': {'path': str(path)}}
        log = '[0.3s][info][class,load] ' + name + ' source: ' + path.as_uri()
        self.assertEqual({name: path.as_uri()}, verify_class_loading(log, build, trace))
        with self.assertRaisesRegex(ValueError, 'outside the pinned overlay'):
            verify_class_loading(log.replace('library.jar', 'old.jar'), build, trace)
        with self.assertRaisesRegex(ValueError, 'outside the pinned overlay'):
            verify_class_loading('', build, trace)

    def test_compile_failure_receipt_binds_source_logs_and_emitted_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'classes').mkdir()
            for name, value in (('Solution.scala', 'bad body'), ('compile.stdout', ''),
                                ('compile.stderr', 'compiler diagnostic'), ('classes/Partial.class', 'bytes')):
                (root / name).write_text(value)
            output = StringIO()
            with redirect_stdout(output):
                publish({'execution_pass': False, 'oracle_pass': False, 'target_reached': False}, 'backend', root)
            payload = json.loads(output.getvalue())
            self.assertEqual('backend', payload['backend_sha256'])
            self.assertEqual(4, len(payload['adjudication_artifacts']))
            self.assertTrue(all(bind(r['path']) == r for r in payload['adjudication_artifacts']))


if __name__ == '__main__':
    unittest.main()
