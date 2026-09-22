"""Portable offline contracts for README parsing, discovery, and mocked authoring.

No provider, compiler, library experiment, or archived baseline is required.
"""
import ast
from contextlib import contextmanager
from importlib import import_module
from importlib.util import find_spec
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'vendor/aideal_engine/src'
MODULES = (
    'readme_format', 'readme_evidence', 'readme_catalogue', 'api_visibility',
    'api_examples', 'scaffold_generation', 'api_intent', 'api_overloads',
    'api_signatures', 'api_discovery', 'readme_generation',
)


class ReadmeFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if find_spec('yaml') is None:
            raise unittest.SkipTest('README configuration requires the existing PyYAML dependency')
        sys.path.insert(0, str(ENGINE))
        cls.addClassCleanup(lambda: sys.path.remove(str(ENGINE)))
        cls.readme = import_module('aideal.readme_agent')
        cls.config_module = import_module('aideal.config')

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        (self.root / 'src').mkdir()
        (self.root / 'tests').mkdir()
        (self.root / 'docs').mkdir()
        (self.root / 'README.md').write_text('''# Offline library
```scala
Ops.scale(2)
```
''')
        (self.root / 'src/Ops.scala').write_text('''package demo
object Ops {
  /** Multiply the value by two. */
  def scale(value: Int): Int = value * 2
  def scale(value: Int, factor: Int): Int = value * factor
  def optional(value: Option[Int] = None): Int = value.getOrElse(0)
  private def hidden(value: Int): Int = value
}
private object Internal {
  def internalOnly(value: Int): Int = value
}
''')
        (self.root / 'tests/OpsTest.scala').write_text('''test("scales a value") {
  assert(Ops.scale(3) == 6)
}
''')
        self.cfg = self.config_module.AidealConfig(
            root=self.root, project_name='Offline', language='Scala',
            source_globs=['src/*.scala'], public_def_regex=r'\bdef\s+([A-Za-z][A-Za-z0-9_]*)',
            exclude_names=[], visibility={}, test_globs=['tests/*.scala'], surface_filter='all',
            llm_readme=self.root / 'docs/LLM_readme.md', original_readme=self.root / 'README.md',
            original_readme_files=[self.root / 'README.md'], notes_to_self=self.root / 'docs/notes.md',
            integration_tasks=self.root / 'tasks.yaml', aliases_file=self.root / 'aliases.json',
            error_log=self.root / 'error.jsonl',
            registry={'offline': self.config_module.ModelSpec(provider='offline', model='fixture')},
            roles={'author': 'offline'}, runtime_target='local', runtime={},
            required_sections=['Goal'], comprehension_apis_sampled=5, comprehension={}, puzzle={},
            raw={'codebase': {}},
        )

    def python_source(self):
        self.cfg.language = 'Python'
        self.cfg.source_globs = ['src/*.py']
        self.cfg.test_globs = ['tests/*.py']
        (self.root / 'src/api.py').write_text('''def scale(value: int, factor: int = 2) -> int:
    """Multiply a value."""
    def local_helper():
        return 0
    return value * factor

class Worker:
    def run(self, count: int = 1) -> int:
        """Run an operation."""
        return count

def _hidden():
    return 1
''')
        (self.root / 'tests/test_api.py').write_text('''def test_scale():
    assert scale(2, 3) == 6
''')

    @contextmanager
    def fake_models(self):
        """Substitute the only possible model boundary, recording its exact payloads."""
        calls = []
        fake_llm, fake_prompts, fake_profile, fake_checks = (
            ModuleType('aideal.' + name) for name in ('llm', 'prompts', 'profile', 'doc_checks'))

        def load_prompt(cfg, name, **fields):
            return name, json.dumps(fields, sort_keys=True, ensure_ascii=False)

        def invoke_text(spec, system, user):
            calls.append((spec.provider, spec.model, system, user))
            fields = json.loads(user)
            if system == 'aideal/readme_distill':
                return 'Offline distilled context.'
            if system == 'aideal/readme_entry':
                return fields['template'].replace('TODO', 'Offline fixture content')
            raise AssertionError('Unexpected prompt: ' + system)

        def unexpected(*args, **kwargs):
            raise AssertionError('Unexpected execution/harness operation')

        fake_llm.invoke_text = invoke_text
        fake_prompts.load = load_prompt
        fake_profile.require_profile = lambda cfg: None
        for name in ('_resolve_io_hints', '_resolve_preamble', '_execute_sample_data'):
            setattr(fake_checks, name, unexpected)
        with patch.dict(sys.modules, {m.__name__: m for m in
                                     (fake_llm, fake_prompts, fake_profile, fake_checks)}):
            yield calls


class ReadmeContractTests(ReadmeFixtures):
    def test_parser_keeps_entries_and_sections(self):
        self.cfg.llm_readme.write_text('''# Catalog
## API Test: `scale`
### Goal
Scale a value.
### Prompt Snippet
scale(2)
### Valid Call Patterns
```scala
Ops.scale(2)
```
## API Test: `optional`
### Goal
Use an optional value.
''')
        entries = self.readme.parse_readme(self.cfg.llm_readme)
        self.assertEqual(['scale', 'optional'], [entry.name for entry in entries])
        self.assertEqual('Scale a value.', entries[0].goal)
        self.assertEqual('scale(2)', entries[0].snippet)
        self.assertTrue(self.readme._section_has_code(entries[0].body, 'Valid Call Patterns'))
        self.assertFalse(self.readme._section_has_code(entries[1].body, 'Valid Call Patterns'))
        self.assertEqual([], self.readme.parse_readme(self.root / 'absent.md'))

    def test_visibility_and_overloads_keep_the_same_public_surface(self):
        self.assertEqual({'scale', 'optional'}, self.readme.public_api_surface(self.cfg))
        details = self.readme.public_api_details(self.cfg)
        scale = [record for record in details if record['name'] == 'scale']
        self.assertEqual(2, len(scale))
        self.assertEqual([True, False, False], [
            next(r for r in details if r['name'] == name)['visibility'] == 'public'
            for name in ('scale', 'hidden', 'internalOnly')])
        maximal, subsumed = self.readme._subsume_overloads(scale)
        self.assertEqual(1, len(maximal))
        self.assertEqual(2, len(maximal[0]['params']))
        self.assertEqual(1, len(subsumed))
        self.assertIn('scale', self.readme.api_test_examples(self.cfg))

    def test_python_ast_rejects_nested_local_functions(self):
        self.python_source()
        self.assertEqual({'scale', 'run'}, self.readme.public_api_surface(self.cfg))
        details = {record['name']: record for record in self.readme.public_api_details(self.cfg)}
        self.assertNotIn('local_helper', details)
        self.assertTrue(details['run']['qualified_name'].endswith('Worker.run'))
        self.assertEqual('2', details['scale']['params'][1]['default'])
        self.assertIn('scale', self.readme.api_test_examples(self.cfg))

    def test_skeleton_existing_document_and_scope_filters(self):
        result = self.readme.find_or_create(self.cfg, generate=False)
        original = self.cfg.llm_readme.read_bytes()
        self.assertEqual('created_skeleton', result['action'])
        self.assertEqual(['optional', 'scale'], [e.name for e in self.readme.parse_readme(self.cfg.llm_readme)])
        self.assertEqual('found', self.readme.find_or_create(self.cfg)['action'])
        self.assertEqual(original, self.cfg.llm_readme.read_bytes())
        self.cfg.surface_filter = 'intent_score'
        self.cfg.raw['codebase']['intent'] = {'threshold': 5}
        self.assertEqual({'scale'}, self.readme.public_api_surface(self.cfg))
        coverage = self.readme.api_coverage(self.cfg)
        self.assertEqual(['scale'], coverage['shared_T'])

    def test_augmentation_does_not_promote_a_stale_verified_example(self):
        block = '## API Test: `scale`\n### Goal\nScale.\n'
        rows = [
            {'status': 'pass', 'code': 'stale()', 'library_version': 'old', 'run_id': '2'},
            {'status': 'pass', 'code': 'current()', 'library_version': 'current', 'run_id': '1'},
        ]
        updated, added = self.readme._augment_block(block, rows, current_version='current')
        self.assertIn('current()', updated)
        self.assertNotIn('stale()', updated)
        self.assertEqual(['example'], added)

    def test_generated_entries_resume_without_new_model_calls(self):
        with self.fake_models() as calls:
            result = self.readme.find_or_create(self.cfg, generate=True, max_generated=0)
            self.assertEqual(2, result['generated_ok'])
            self.assertEqual(0, result['fallback_to_skeleton'])
            self.assertEqual(3, len(calls))  # One distillation plus two API entries.
            before = self.cfg.llm_readme.read_bytes()
            resumed = self.readme.find_or_create(self.cfg, generate=True, max_generated=0, resume=True)
            self.assertEqual(2, resumed['resumed_entries'])
            self.assertEqual(0, resumed['newly_generated'])
            self.assertEqual(3, len(calls))
            self.assertEqual(before, self.cfg.llm_readme.read_bytes())

    def test_generation_identity_covers_the_moved_implementations(self):
        tree = ast.parse((ENGINE / 'aideal/readme_generation.py').read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == '_engine_files' for t in n.targets))
        files = {n.value for n in ast.walk(node) if isinstance(n, ast.Constant)
                 and isinstance(n.value, str) and n.value.endswith('.py')}
        self.assertTrue({name + '.py' for name in MODULES} <= files)
        self.assertTrue({'config.py', 'llm.py', 'profile.py', 'prompts.py', 'readme_agent.py'} <= files)




if __name__ == '__main__':
    unittest.main()
