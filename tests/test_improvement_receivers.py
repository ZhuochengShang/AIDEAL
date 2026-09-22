"""Scala preview identity stays stable while receiver facts remain source-backed."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from workflow.ablation import load
from workflow.improvement_context import _library_inputs, _scala_receiver_facts, preview_improvements
from workflow.improvement_batches import _implementation_bindings, preview_library_improvements
from workflow.worktrees import attach


class ScalaPreviewReceiversTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / 'library'
        (self.repo / 'src').mkdir(parents=True)
        # The two same-name RDPro APIs really belong to distinct objects.
        # A local same-name definition exercises the conservative failure case.
        self.source = ('/* package wrong; object Wrong { } */\n'
                       'package edu.ucr.cs.bdlab.beast.geolite\n'
                       'object Feature {\n'
                       '  val label = "package false; object Fake { }"\n'
                       '  def readType(in: ObjectInput): DataType = read(in)\n'
                       '}\n'
                       'object RasterSchemaHelper {\n'
                       '  def readType(in: ObjectInput): DataType = read(in)\n'
                       '  def outer(): Unit = {\n'
                       '    def readType(in: ObjectInput): DataType = read(in)\n'
                       '  }\n'
                       '}\n')
        (self.repo / 'src/Types.scala').write_text(self.source)
        (self.repo / 'README.md').write_text('Original documentation')
        config = self.repo / 'configs/aideal.yaml'
        config.parent.mkdir()
        config.write_text('extends: [scala-spark]\nproject: {name: Example, language: Scala}\n'
                          'codebase: {source_globs: [src/**/*.scala]}\n'
                          'files: {original_readme: README.md}\n')
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL)
        git('init', '-q')
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.invalid')
        git('add', '.')
        git('commit', '-qm', 'Fixture')
        self.study = self.root / 'study'
        attach(self.repo, config, self.study)

    def test_same_name_receivers_keep_original_ids_and_filter_scope(self):
        rows = _library_inputs(self.study)[4]
        expected = ['src/Types.scala:5:readType', 'src/Types.scala:8:readType',
                    'src/Types.scala:9:outer', 'src/Types.scala:10:readType']
        self.assertEqual(expected, [row['id'] for row in rows])
        self.assertEqual(['readType', 'readType', 'outer', 'readType'],
                         [row['qualified_name'] for row in rows])
        selected = _library_inputs(self.study, ['readType'])[4]
        self.assertEqual([expected[i] for i in (0, 1, 3)], [row['id'] for row in selected])
        for row, receiver in zip(rows[:2], ('Feature', 'RasterSchemaHelper')):
            self.assertEqual(receiver, row['receiver'])
            self.assertEqual('object', row['owner_kind'])
            self.assertEqual('edu.ucr.cs.bdlab.beast.geolite.' + receiver, row['qualified_receiver'])
            self.assertEqual(row['qualified_receiver'] + '.readType', row['source_qualified_name'])
            self.assertEqual('resolved_lexical', row['qualification_status'])
            self.assertIn('object ' + receiver, row['owner_declaration']['text'])
        local = rows[-1]
        self.assertEqual('unresolved', local['qualification_status'])
        for key in ('receiver', 'owner_kind', 'owner_path', 'qualified_receiver', 'source_qualified_name'):
            self.assertIsNone(local[key])

    def test_both_preview_routes_deliver_facts_without_changing_ids(self):
        small = load(preview_improvements(self.study, self.root / 'small', apis=['readType'])['preview'])
        plan = load(preview_library_improvements(self.study, self.root / 'library-preview',
                                                apis=['readType'], batch_size=1)['manifest'])
        self.assertEqual(3, plan['coverage']['planned_definitions'])
        batched = [row for batch in plan['batches']
                   for row in load(batch['preview']['path'])['context']['apis']]
        self.assertEqual(small['context']['apis'], batched)
        self.assertEqual(['Feature', 'RasterSchemaHelper', None], [row['receiver'] for row in batched])
        self.assertTrue(any(ref['path'].endswith('/workflow/scala_owners.py')
                            for ref in _implementation_bindings()))
        self.assertEqual(0, plan['llm_calls'])

    def test_nested_and_companion_owners_and_unsupported_sites(self):
        source = 'package a\npackage b\nobject A {\n class B {\n def readType = 1\n }\n}\nclass A {\n def readType = 2\n}'
        nested = _scala_receiver_facts(source, 5, 'readType')
        self.assertEqual(('B', 'class', 'A.B', 'a.b.A.B'),
                         tuple(nested[k] for k in ('receiver', 'owner_kind', 'owner_path', 'qualified_receiver')))
        self.assertEqual('class', _scala_receiver_facts(source, 9, 'readType')['owner_kind'])
        for text, line in [('package a {\n object A {\n def f = 1\n }\n}', 3),
                           ('object A {\n def f = {\n new B {\n def g = 1\n }\n }\n}', 4),
                           ('object A:\n def f = 1', 2)]:
            with self.subTest(source=text):
                result = _scala_receiver_facts(text, line, 'g' if line == 4 else 'f')
                self.assertEqual('unresolved', result['qualification_status'])
                self.assertIsNone(result['qualified_receiver'])


if __name__ == '__main__':
    unittest.main()
