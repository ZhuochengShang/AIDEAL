import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

MODULE=Path(__file__).parents[1]/'vendor/aideal_engine/src/aideal/api_public_inventory.py'
spec=importlib.util.spec_from_file_location('api_public_inventory_test',MODULE)
inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)

def scan(tmp_path,files):
    for name,text in files.items():
        path=tmp_path/'pkg'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    (tmp_path/'pkg/__init__.py').touch(exist_ok=True)
    return inventory.scan_python_surface(tmp_path,{'pkg':'pkg'},'fixture')

def row(data,qualified):
    return next(x for x in data['records'] if x['qualified_name']==qualified)

def test_defining_identity_and_inherited_override(tmp_path):
    data=scan(tmp_path,{'base.py':'class Base:\n def run(self,x): return x\n','child.py':'from .base import Base\nclass Child(Base):\n pass\nclass Own(Base):\n def run(self,x,y=1): return x+y\n'})
    inherited=[x for x in data['exposures'] if x['qualified_name']=='pkg.child.Child.run']
    assert {x['defining_api_id'] for x in inherited}=={'python:pkg.base.Base.run'}
    own=[x for x in data['exposures'] if x['qualified_name']=='pkg.child.Own.run']
    assert {x['defining_api_id'] for x in own}=={'python:pkg.child.Own.run'}

def test_private_implementation_public_reexport(tmp_path):
    data=scan(tmp_path,{'__init__.py':'from ._impl import _run as run\n','_impl.py':'def _run(x): return x+1\n'})
    record=row(data,'pkg._impl._run')
    assert record['declared_visibility']=='non-public'
    assert record['public_exposure_established']
    assert record['inventory_status']=='candidate'
    assert record['preferred_public_path']=='pkg.run'

def test_external_import_not_owned(tmp_path):
    data=scan(tmp_path,{'__init__.py':'from math import sqrt\ndef mapPixels(x): return x.map(lambda y:y+1)\n'})
    assert row(data,'pkg.mapPixels')['inventory_status']=='candidate'
    assert not any(x['name']=='sqrt' for x in data['records'])
    assert next(x for x in data['exposures'] if x['qualified_name']=='pkg.sqrt')['status']=='external'

def test_no_subject_execution(tmp_path):
    data=scan(tmp_path,{'__init__.py':'raise RuntimeError("must not execute")\ndef safe(x): return x\n'})
    assert row(data,'pkg.safe')['parameter_count']==1

def test_property_is_mapped_not_callable(tmp_path):
    data=scan(tmp_path,{'__init__.py':'class C:\n @property\n def value(self): return 1\n'})
    record=row(data,'pkg.C.value')
    assert record['callable'] is False
    assert record['inventory_reason']=='noncallable_property'

def test_cython_complete_public_and_c_only(tmp_path):
    data=scan(tmp_path,{'native.pyx':'cdef int helper(int x):\n return x\ncpdef double public(double x, y=1):\n return x+y\ncdef class Box:\n def __cinit__(self,n):\n  pass\n @property\n def value(self):\n  return 2\n def run(self,x):\n  return x\n'})
    assert data['counts']['cython_files']==1
    assert row(data,'pkg.native.helper')['inventory_reason']=='c_only_cython_declaration'
    assert row(data,'pkg.native.public')['parameter_count']==2
    assert row(data,'pkg.native.Box')['parameter_count']==1
    assert row(data,'pkg.native.Box.run')['parameter_count']==1
    assert row(data,'pkg.native.Box.value')['callable'] is False

def test_unknown_external_constructor_not_zero(tmp_path):
    data=scan(tmp_path,{'__init__.py':'from other import External\nclass C(External):\n pass\n'})
    assert row(data,'pkg.C')['parameter_count'] is None
    assert data['issues'][-1]['reason']=='external_or_dynamic_base_members_not_enumerated'

def test_decorated_constructor_not_invented(tmp_path):
    data=scan(tmp_path,{'__init__.py':'from dataclasses import dataclass\n@dataclass\nclass C:\n value: int\n'})
    assert row(data,'pkg.C')['parameter_count'] is None

def test_rebound_class_name_base_resolves_import(tmp_path):
    data=scan(tmp_path,{'base.py':'class C:\n def run(self): return 1\n','__init__.py':'from .base import C\nclass C(C):\n pass\n'})
    assert row(data,'pkg.C')['static_mro']==['pkg.C','pkg.base.C']
    assert not any(x['reason']=='inconsistent_or_cyclic_static_mro' for x in data['issues'])

def test_source_hash_and_unicode_span(tmp_path):
    data=scan(tmp_path,{'__init__.py':'# café\ndef run(x="é"):\n return x\n'})
    record=row(data,'pkg.run');text=(tmp_path/'pkg/__init__.py').read_text()
    assert hashlib.sha256(text[record['start']:record['end']].encode()).hexdigest()==record['source_span_sha256']

def test_star_exports_and_unresolved_dynamic_all(tmp_path):
    data=scan(tmp_path,{'base.py':'__all__=["run"]\ndef run(x): return x\ndef other(x): return x\n','__init__.py':'from .base import *\n__all__=get_names()\n'})
    assert any(x['qualified_name']=='pkg.run' and x['defining_api_id']=='python:pkg.base.run' for x in data['exposures'])
    assert any(x['reason']=='dynamic___all__' for x in data['issues'])

def test_generated_owned_factory_is_custom_api(tmp_path):
    data=scan(tmp_path,{'__init__.py':'from external import foreign\ndef adapt(fn):\n def wrapper(*args, **kwargs):\n  kwargs["library_option"]=True\n  return fn(*args,**kwargs)\n return wrapper\ncustom=adapt(foreign)\n'})
    record=row(data,'pkg.custom')
    assert record['inventory_status']=='candidate'
    assert record['generated_callable']['factory']=='pkg.adapt'
    assert record['parameter_count']==2

def test_symlink_escape_rejected(tmp_path):
    outside=tmp_path/'outside.py';outside.write_text('def nope(): pass\n')
    package=tmp_path/'source/pkg';package.mkdir(parents=True);(package/'__init__.py').write_text('')
    (package/'escape.py').symlink_to(outside)
    with pytest.raises(ValueError,match='escapes'):inventory.scan_python_surface(tmp_path/'source',{'pkg':'pkg'},'fixture')

def test_documentation_exact_identity_not_bare_name(tmp_path):
    data=scan(tmp_path,{'__init__.py':'class First:\n def run(self): return 1\nclass Second:\n def run(self): return 2\n'})
    mapped=inventory.reconcile_documentation(data,[{'qualified_name':'pkg.First.run','object_type':'py:method','url':'https://official.example/api#pkg.First.run','sha256':'test'}])
    assert mapped['python:pkg.First.run']['status']=='documented'
    assert mapped['python:pkg.Second.run']['status']=='undocumented'

def test_documentation_resolved_reexport(tmp_path):
    data=scan(tmp_path,{'__init__.py':'from .impl import run\n','impl.py':'def run(x): return x\n'})
    mapped=inventory.reconcile_documentation(data,[{'qualified_name':'pkg.run','object_type':'py:function','url':'https://official.example/api#pkg.run'}])
    assert mapped['python:pkg.impl.run']['evidence'][0]['match_type']=='resolved_public_exposure'

def test_abstract_evidence_is_explicit(tmp_path):
    data=scan(tmp_path,{'__init__.py':'from abc import abstractmethod\nclass C:\n @abstractmethod\n def run(self): ...\n def empty(self): pass\n'})
    assert row(data,'pkg.C.run')['is_abstract'] is True
    assert row(data,'pkg.C.empty')['body_presence']=='absent'

def test_condition_records_both_arms_and_bound_active_variant(tmp_path):
    scan(tmp_path,{'__init__.py':'if AVAILABLE:\n class Model:\n  def run(self,x): return x\nelse:\n class Model:\n  def run(self,x,y): return y\n'})
    data=inventory.scan_python_surface(tmp_path,{'pkg':'pkg'},'fixture',binding_environment={'facts':{'pkg.AVAILABLE':{'value':True}}})
    models=[r for r in data['records'] if r['qualified_name']=='pkg.Model']
    assert len(models)==2
    assert {r['conditional_context'][0]['expected'] for r in models}=={True,False}
    assert sum(r['inventory_status']=='candidate' for r in models)==1
    assert next(r for r in models if r['conditional_context'][0]['expected'] is False)['inventory_reason']=='inactive_recorded_runtime_variant'

def test_companion_doc_match_is_defining_identity():
    data={'records':[{'api_id':'scala:class:pkg.C.run','qualified_name':'pkg.C.run'}]}
    mapped=inventory.reconcile_documentation(data,[{'qualified_name':'pkg.C.run','object_type':'method'}])
    assert mapped['scala:class:pkg.C.run']['evidence'][0]['match_type']=='exact_defining_identity'

@pytest.fixture
def bound_reader(tmp_path,monkeypatch):
    import json,types,copy
    pkg=types.ModuleType('inventory_test_package');pkg.__path__=[str(MODULE.parent)];monkeypatch.setitem(sys.modules,pkg.__name__,pkg)
    selector=MODULE.parent/'api_canonical_selection.py'
    if not selector.exists():selector=MODULE.parents[6]/'selection/files/vendor/aideal_engine/src/aideal/api_canonical_selection.py'
    for name,path in [('api_origin',MODULE.parent/'api_origin.py'),('api_canonical_selection',selector),('api_public_inventory',MODULE)]:
        spec=importlib.util.spec_from_file_location(pkg.__name__+'.'+name,path);mod=importlib.util.module_from_spec(spec);monkeypatch.setitem(sys.modules,spec.name,mod);spec.loader.exec_module(mod);setattr(pkg,name,mod)
    root=tmp_path/'source';root.mkdir();ledger=scan(root,{'__init__.py':'def run(x): return x+1\n'})
    ledger.update(source_snapshot={'commit':'commit','tree':'tree'},source_version='1',origin_policy={'source_roots':['pkg'],'library_namespaces':['pkg'],'external_namespaces':['math']})
    cfg=types.SimpleNamespace(root=tmp_path,language='Python',raw={'codebase':{'api_origin':{'source_roots':['source/pkg'],'library_namespaces':['pkg'],'external_namespaces':['math']}}})
    for r in ledger['records']:r.update(defining_file='source/'+r['path'],file='source/'+r['path'])
    decisions=pkg.api_origin.audit_api_origins(cfg,ledger['records'])['decisions']
    for r,d in zip(ledger['records'],decisions):r['api_origin']=d
    candidates=[r for r in ledger['records'] if r['inventory_status']=='candidate']
    selection=pkg.api_canonical_selection.select_canonical_implementations(candidates,policy_version=pkg.api_canonical_selection.QUALIFIED_POLICY_VERSION)
    manifest={'schema':2,'kind':'qualified_source_api_inventory','source_root':'source','source_commit':'commit','source_tree':'tree','source_version':'1','declaration_ids':[r['site_id'] for r in candidates],'canonical_declaration_ids':selection['winner_site_ids'],'canonical_selection_policy_version':pkg.api_canonical_selection.QUALIFIED_POLICY_VERSION}
    registry=types.ModuleType(pkg.__name__+'.api_registry');registry._bound_json=lambda c,d,k:ledger if k=='source_inventory' else selection;monkeypatch.setitem(sys.modules,registry.__name__,registry)
    monkeypatch.setattr(pkg.api_public_inventory.subprocess,'run',lambda args,**kw:types.SimpleNamespace(stdout='commit' if args[-1]=='HEAD' else 'tree' if args[-1]=='HEAD^{tree}' else ''))
    return pkg.api_public_inventory,cfg,manifest,ledger,selection

def test_reader_verifies_relocated_owned_source(bound_reader):
    module,cfg,manifest,ledger,selection=bound_reader
    result=module.qualified_inventory_details(cfg,manifest)
    assert result[0]['api_id']=='python:pkg.run'
    assert result[0]['api_origin']['status']=='library_defined'

def test_reader_rejects_source_bytes_with_old_ledger(bound_reader):
    module,cfg,manifest,ledger,selection=bound_reader
    (cfg.root/'source/pkg/__init__.py').write_text('def run(x): return x+2\n')
    with pytest.raises(ValueError,match='source file changed'):module.qualified_inventory_details(cfg,manifest)

@pytest.mark.parametrize('field,value',[('parameter_count',55),('public_owner_chain',False),('callable',False),('forwarding',{'relation':'direct_forwarder'}),('params',[]),('preferred_public_path','external.wrong')])
def test_reader_rejects_self_consistent_selection_fact_rewrite(bound_reader,field,value):
    module,cfg,manifest,ledger,selection=bound_reader
    ledger['records'][0][field]=value
    with pytest.raises(ValueError,match='fresh static parse'):module.qualified_inventory_details(cfg,manifest)

def test_reader_rejects_policy_drift(bound_reader):
    module,cfg,manifest,ledger,selection=bound_reader
    cfg.raw['codebase']['api_origin']['external_namespaces']=[]
    with pytest.raises(ValueError,match='namespace policy'):module.qualified_inventory_details(cfg,manifest)


@pytest.mark.parametrize('missing', [True, False])
def test_reader_normalizes_absent_or_null_source_comment_without_mutating_ledger(bound_reader,missing):
    """Compiler-produced ledgers omit this optional field; consumers need a string."""
    import copy
    module,cfg,manifest,ledger,selection=bound_reader
    record=ledger['records'][0]
    if missing:record.pop('description',None)
    else:record['description']=None
    before=copy.deepcopy(ledger)
    result=module.qualified_inventory_details(cfg,manifest)
    assert result[0]['description']==''
    assert ledger==before
    assert [r['site_id'] for r in result]==selection['winner_site_ids']
    assert result[0]['signature']==record['signature']
    assert result[0]['source_sha256']==record['source_sha256']
    assert result[0]['source_span_sha256']==record['source_span_sha256']


def test_reader_preserves_existing_source_comment_verbatim(bound_reader):
    module,cfg,manifest,ledger,selection=bound_reader
    text='Exact source comment.\nDo not replace this with generated guidance.'
    ledger['records'][0]['description']=text
    result=module.qualified_inventory_details(cfg,manifest)
    assert result[0]['description']==text


@pytest.mark.parametrize('invalid', [42, False, {'unexpected':'object'}, ['unexpected']])
def test_reader_rejects_nontext_source_comment(bound_reader,invalid):
    module,cfg,manifest,ledger,selection=bound_reader
    ledger['records'][0]['description']=invalid
    with pytest.raises(ValueError,match='description must be text or absent'):
        module.qualified_inventory_details(cfg,manifest)


@pytest.mark.parametrize('language,extension,source_text,signature', [
    ('Java', 'java', 'package pkg; public class C { public int run(int x) { return x + 1; } }', 'public int run(int x)'),
    ('Scala', 'scala', 'package pkg\nclass C { def run(x: Int): Int = x + 1 }', 'def run(x: Int): Int'),
])
def test_compiler_record_without_comment_reaches_existing_overload_consumer(
        bound_reader, monkeypatch, language, extension, source_text, signature):
    """A JVM ledger must reach the shared R0/README overload consumer safely."""
    import copy, types
    module,cfg,manifest,ledger,selection=bound_reader
    package=sys.modules[module.__package__]
    path='pkg/C.'+extension
    source_file=cfg.root/'source'/path
    source_file.write_text(source_text)
    sha=hashlib.sha256(source_text.encode()).hexdigest()
    record=ledger['records'][0]
    record.update(language=language,source_language=language,name='run',
        owner='pkg.C',defining_owner='pkg.C',defining_owner_kind='class',
        qualified_name='pkg.C.run',api_id=language.lower()+':pkg.C.run',
        site_id=language.lower()+':fixture:C.run',kind='method',definition_kind='method',
        path=path,file='source/'+path,defining_file='source/'+path,line=1,
        start=0,end=len(source_text),source_sha256=sha,source_span_sha256=sha,
        signature=signature,params=[{'name':'x','type':'int' if language=='Java' else 'Int'}],
        parameter_count=1,parameter_count_status='compiler_declared',
        offset_unit='UTF-16 code units in decoded UTF-8 source',
        public_access_paths=['pkg.C.run'],preferred_public_path='pkg.C.run')
    record.pop('description',None)
    ledger.pop('package_roots',None)
    ledger['source_files']=[{'path':path,'sha256':sha,'bytes':len(source_text.encode()),'encoding':'utf-8'}]
    ledger['source_file_binding_sha256']=module.digest(ledger['source_files'])
    cfg.language=language
    record['api_origin']=package.api_origin.audit_api_origins(cfg,[record])['decisions'][0]
    updated_selection=package.api_canonical_selection.select_canonical_implementations(
        [record],policy_version=package.api_canonical_selection.QUALIFIED_POLICY_VERSION)
    selection.clear();selection.update(updated_selection)
    manifest.update(declaration_ids=[record['site_id']],canonical_declaration_ids=selection['winner_site_ids'])
    before=copy.deepcopy(ledger)
    normalized=module.qualified_inventory_details(cfg,manifest)
    assert ledger==before
    assert len(normalized)==1
    assert normalized[0]['description']==''
    assert normalized[0]['signature']==signature
    assert normalized[0]['site_id']==record['site_id']
    # Load the unchanged consumer with its unrelated imports stubbed; no LLM,
    # subject import, compiler, or generated-program execution is involved.
    for name,attribute in [('config','AidealConfig'),('api_discovery','public_api_details'),('api_intent','intent_scores')]:
        stub=types.ModuleType(package.__name__+'.'+name)
        setattr(stub,attribute,object)
        monkeypatch.setitem(sys.modules,stub.__name__,stub)
    spec=importlib.util.spec_from_file_location(package.__name__+'.api_overloads',MODULE.parent/'api_overloads.py')
    consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
    maximals,subsumed=consumer._subsume_overloads(normalized)
    assert maximals==normalized
    assert subsumed==[]
