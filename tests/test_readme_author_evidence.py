"""No models or subject imports: exact owner/comment source evidence contracts."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from aideal.readme_author_evidence import qualified_author_evidence, source_comment, verify_author_evidence
from test_readme_modules import ReadmeFixtures


def setup(tmp_path, language='Java'):
    (tmp_path/'src').mkdir(); (tmp_path/'tests').mkdir()
    return SimpleNamespace(root=tmp_path, language=language, test_globs=['tests/*'])


def definition(cfg, owner='Reader', name='run', comment='Reads the input.'):
    path = cfg.root/'src'/f'{owner}.java'
    path.write_text(f'package demo;\nclass {owner} {{\n /** {comment} */\n public static int {name}(int value) {{return value;}}\n}}\n')
    return {'api_id':f'java:demo.{owner}.{name}', 'name':name,
            'qualified_name':f'demo.{owner}.{name}', 'file':str(path.relative_to(cfg.root)),
            'line':4, 'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def test_javadoc_is_attached_to_selected_source_and_bound(tmp_path):
    cfg=setup(tmp_path);row=definition(cfg)
    result=source_comment(cfg,row)
    assert result['text']=='Reads the input.'
    assert result['evidence']['start_line']==3
    assert result['evidence']['text']=='/** Reads the input. */'
    assert result['evidence']['file_sha256']==row['source_sha256']


def test_does_not_borrow_comment_from_previous_overload(tmp_path):
    cfg=setup(tmp_path);row=definition(cfg)
    path=cfg.root/row['file'];path.write_text(path.read_text().replace('\n}', '\n public static int other(int x) {return x;}\n}'))
    row.update(name='other',line=5,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert source_comment(cfg,row)['status']=='not_supplied'


def test_annotation_and_multiline_comment_preserve_exact_span(tmp_path):
    cfg=setup(tmp_path,'Scala');path=cfg.root/'src/Ops.scala'
    path.write_text('object Ops {\n /** A comment.\n  * Second line.\n  */\n @deprecated("old")\n def run(x: Int): Int = x\n}\n')
    row={'name':'run','file':'src/Ops.scala','line':6,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    value=source_comment(cfg,row)
    assert 'Second line.' in value['text']
    assert value['evidence']['start_line']==2 and value['evidence']['end_line']==4


def test_python_docstring_span_and_source_change(tmp_path):
    cfg=setup(tmp_path,'Python');path=cfg.root/'src/api.py'
    path.write_text('def run(x):\n    """Preserve café.\n    More."""\n    return x\n')
    row={'api_id':'python:pkg.run','qualified_name':'pkg.run','name':'run','file':'src/api.py','line':1,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    evidence=qualified_author_evidence(cfg,[row])['python:pkg.run']
    assert 'café' in evidence['source_comment']['text']
    verify_author_evidence(evidence)
    path.write_text(path.read_text().replace('café','tea'))
    with pytest.raises(ValueError,match='source changed'):source_comment(cfg,row)
    with pytest.raises(ValueError,match='evidence changed'):verify_author_evidence(evidence)


def test_exact_import_owners_do_not_share_same_name_examples(tmp_path):
    cfg=setup(tmp_path);a=definition(cfg);b=definition(cfg,'Writer')
    (cfg.root/'tests/Test.java').write_text('import demo.Reader;\nimport demo.Writer;\n@Test public void first() {Reader.run(1);}\n@Test public void second() {Writer.run(2);}\n')
    result=qualified_author_evidence(cfg,[a,b])
    assert 'Reader.run' in result[a['api_id']]['test_examples'][0]['code']
    assert 'Writer.run' not in result[a['api_id']]['test_examples'][0]['code']
    assert result[b['api_id']]['test_examples'][0]['test']=='second'
    assert result[a['api_id']]['test_examples'][0]['execution_status']=='not_run'


@pytest.mark.parametrize('code', ['run(1);','other.run(1);','String s = "demo.Reader.run(1)";',
                                   '/* demo.Reader.run(1); */','Reader.run(1);'])
def test_bare_ambiguous_or_quoted_calls_do_not_count(tmp_path,code):
    cfg=setup(tmp_path);row=definition(cfg)
    (cfg.root/'tests/Test.java').write_text('import demo.*;\n@Test public void test() {'+code+'}\n')
    assert qualified_author_evidence(cfg,[row])[row['api_id']]['test_examples']==[]


def test_qualified_constructor_in_scala_package(tmp_path):
    cfg=setup(tmp_path,'Scala');path=cfg.root/'src/Grid.scala'
    path.write_text('package demo\n/** Grid dimensions. */\nclass Grid(val width: Int)\n')
    row={'api_id':'scala:demo.Grid','qualified_name':'demo.Grid','name':'Grid','file':'src/Grid.scala','line':3,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (cfg.root/'tests/GridTest.scala').write_text('package demo\ntest("grid") {\n val grid = new Grid(4)\n assert(grid.width == 4)\n}\n')
    value=qualified_author_evidence(cfg,[row])[row['api_id']]
    assert value['test_examples'][0]['matched_calls'][0]['public_path']=='demo.Grid'
    assert value['source_comment']['text']=='Grid dimensions.'


def test_import_shadowing_and_duplicate_owner_imports_are_rejected(tmp_path):
    cfg=setup(tmp_path);row=definition(cfg)
    test=cfg.root/'tests/Test.java'
    for prefix,body in [('import demo.Reader;\nimport other.Reader;','Reader.run(1);'),
                        ('import demo.Reader;','Reader = other; Reader.run(1);')]:
        test.write_text(prefix+'\n@Test public void test() {'+body+'}\n')
        assert qualified_author_evidence(cfg,[row])[row['api_id']]['test_examples']==[]


def test_python_import_alias_resolves_but_local_receiver_does_not(tmp_path):
    cfg=setup(tmp_path,'Python');path=cfg.root/'src/api.py';path.write_text('def run(x):\n return x\n')
    row={'api_id':'python:pkg.run','qualified_name':'pkg.run','name':'run','file':'src/api.py','line':1,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    test=cfg.root/'tests/test_api.py'
    test.write_text('from pkg import run as operation\ndef test_ok():\n assert operation(1) == 1\ndef test_shadow(operation):\n assert operation(2) == 2\n')
    examples=qualified_author_evidence(cfg,[row])[row['api_id']]['test_examples']
    assert [e['test'] for e in examples]==['test_ok']
    test.write_text('from pkg import run as operation\noperation=other\ndef test_shadow():\n operation(1)\n')
    assert qualified_author_evidence(cfg,[row])[row['api_id']]['test_examples']==[]


def test_changed_test_fails_and_overlong_examples_are_not_truncated(tmp_path):
    cfg=setup(tmp_path);row=definition(cfg);test=cfg.root/'tests/Test.java'
    test.write_text('@Test public void test() {demo.Reader.run(1);}\n')
    evidence=qualified_author_evidence(cfg,[row])[row['api_id']]
    verify_author_evidence(evidence)
    test.write_text(test.read_text().replace('(1)','(2)'))
    with pytest.raises(ValueError,match='evidence changed'):verify_author_evidence(evidence)
    result=qualified_author_evidence(cfg,[row],max_chars=5)[row['api_id']]
    assert result['test_examples']==[]
    assert result['test_selection']['scan']['omitted_oversized_or_ambiguous_blocks']==1


def test_unbound_discovery_stub_does_not_invent_source_context(tmp_path):
    cfg=setup(tmp_path);row=definition(cfg);row.pop('source_sha256')
    value=source_comment(cfg,row)
    assert value['status']=='not_supplied' and value['text']==''


def test_private_or_external_bank_cannot_enter_repository_test_context(tmp_path):
    cfg=setup(tmp_path);row=definition(cfg)
    inventory=cfg.root/'inventory.json';inventory.write_text(json.dumps({'source_root':'src'}))
    cfg.raw={'codebase':{'api_inventory':'inventory.json','api_inventory_sha256':hashlib.sha256(inventory.read_bytes()).hexdigest()}}
    (cfg.root/'tests/held_out.java').write_text('@Test public void oracle() {demo.Reader.run(1);}\n')
    with pytest.raises(ValueError,match='inside the pinned source repository'):
        qualified_author_evidence(cfg,[row])


class AuthoringIntegrationTests(ReadmeFixtures):
    def setUp(self):
        super().setUp()
        from aideal import readme_generation
        self.generation=readme_generation
        self.key='scala:demo.Ops.scale'
        self.cfg.raw['codebase']['identity_mode']='qualified'
        self.test=self.root/'tests/OpsTest.scala'
        self.test.write_text('import demo.Ops\n'+self.test.read_text())
        self.row={'api_id':self.key,'name':'scale','qualified_name':'demo.Ops.scale',
                  'owner':'demo.Ops','owner_kind':'object','visibility':'public',
                  'file':'src/Ops.scala','line':4,'source_sha256':hashlib.sha256((self.root/'src/Ops.scala').read_bytes()).hexdigest(),
                  'signature':'def scale(value: Int): Int','params':[{'name':'value','type':'Int','default':None}],
                  'returns':'Int','description':''}

    def discover(self):
        from contextlib import ExitStack
        stack=ExitStack()
        stack.enter_context(patch.object(self.generation,'public_api_surface',return_value={self.key}))
        stack.enter_context(patch.object(self.generation,'public_api_details',return_value=[self.row]))
        stack.enter_context(patch.object(self.generation,'original_target_texts',return_value={self.key:'Original description'}))
        stack.enter_context(patch.object(self.generation,'_original_readme_snippets',return_value={self.key:['Original description']}))
        return stack

    def test_saved_author_context_and_request_contain_bound_exact_evidence(self):
        with self.discover(), self.fake_models() as calls:
            result=self.generation.find_or_create(self.cfg,generate=True,max_generated=0)
        request=json.loads(next(c[3] for c in calls if c[2]=='aideal/readme_entry'))
        facts=json.loads(request['api_facts'])
        self.assertEqual('Multiply the value by two.',facts['source_doc'])
        self.assertIn('Ops.scale(3)',request['test_examples'])
        self.assertNotIn('text',facts['authoring_evidence']['test_examples'][0]['span'])
        state=json.loads(Path(result['generation_state']).read_text())
        folder=self.root/'.aideal_exec/readme_authoring'/state['generation_fingerprint']
        receipt=json.loads((folder/'index.json').read_text())['apis'][self.key]
        content=Path(receipt['path']).read_bytes()
        self.assertEqual(receipt['sha256'],hashlib.sha256(content).hexdigest())
        record=json.loads(content)
        self.assertIn('Ops.scale(3)',record['test_examples'][0]['code'])
        self.assertEqual('',self.row['description'])  # discovery is not rewritten

    def test_changed_test_invalidates_resume_before_author_request(self):
        with self.discover(), self.fake_models():
            self.generation.find_or_create(self.cfg,generate=True,max_generated=0)
        self.test.write_text(self.test.read_text().replace('scale(3)','scale(4)'))
        with self.discover(),self.fake_models() as calls:
            with self.assertRaisesRegex(ValueError,'fingerprint changed'):
                self.generation.find_or_create(self.cfg,generate=True,resume=True,max_generated=0)
        self.assertEqual([],calls)

    def test_source_change_during_author_call_is_rejected(self):
        import sys
        with self.discover(),self.fake_models():
            model=sys.modules['aideal.llm'];invoke=model.invoke_text
            def mutate(spec,system,user):
                answer=invoke(spec,system,user)
                if system=='aideal/readme_entry':self.test.write_text(self.test.read_text()+'// mutation\n')
                return answer
            with patch.object(model,'invoke_text',side_effect=mutate):
                with self.assertRaisesRegex(ValueError,'evidence changed'):
                    self.generation.find_or_create(self.cfg,generate=True,max_generated=0)
