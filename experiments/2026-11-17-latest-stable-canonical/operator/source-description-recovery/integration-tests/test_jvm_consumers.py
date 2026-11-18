"""Offline integration of the patched registry's JVM records with actual loops.

Model responses, original-document mapping, and execution are synthetic. The
actual R0 loop, authoring loop, prompt assembly, and artifact writes run.
"""
from contextlib import ExitStack
import importlib.util
import json
import hashlib
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import pytest

FROZEN=Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/evaluator-qualified')
STAGE=Path('/tmp/aideal-launch-2026-11-17/fix-source-description')
sys.path.insert(0,str(FROZEN/'vendor/aideal_engine/src'))

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

reader_tests=load('staged_reader_tests',STAGE/'tests/test_public_api_inventory.py')
readme_tests=load('frozen_readme_fixture',FROZEN/'tests/test_readme_modules.py')
execution_tests=load('frozen_execution_fixture',FROZEN/'tests/test_doc_check_modules.py')
from aideal import doc_check_execution,readme_generation
from aideal.readme_format import ApiEntry

@pytest.fixture(params=[('Java','java','package pkg; public class C { public int run(int x) { return x + 1; } }','public int run(int x)'),('Scala','scala','package pkg\nclass C { def run(x: Int): Int = x + 1 }','def run(x: Int): Int')])
def jvm_details(request,tmp_path,monkeypatch):
    bound=reader_tests.bound_reader.__wrapped__(tmp_path,monkeypatch)
    reader_tests.test_compiler_record_without_comment_reaches_existing_overload_consumer(bound,monkeypatch,*request.param)
    module,cfg,manifest,ledger,selection=bound
    details=module.qualified_inventory_details(cfg,manifest)
    return request.param[0],details

def test_actual_r0_loop_consumes_normalized_jvm_record(jvm_details):
    language,details=jvm_details
    case=execution_tests.DocCheckModuleTests();case.setUp()
    try:
        cfg=case.cfg;cfg.language=language
        key=details[0]['api_id']
        manifest={'kind':'qualified_source_api_inventory','canonical_selection':'fixture-selection.json',
                  'canonical_selection_policy_version':'owner_qualified_max_arity_v2',
                  'canonical_selection_sha256':'fixture-selection','source_inventory_sha256':'fixture-source',
                  'source_commit':'fixture-commit','source_tree':'fixture-tree','source_version':'fixture'}
        inventory_path=cfg.root/'fixture-inventory.json'
        inventory_path.write_text(json.dumps(manifest))
        cfg.raw['codebase'].update(identity_mode='qualified',api_inventory='fixture-inventory.json',
                                   api_inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest())
        document={'schema':'aideal.original-documents/v1','library':'fixture','source_version':'fixture',
                  'source_commit':'fixture-commit','source_tree':'fixture-tree','scope':'fixture',
                  'documents':[{'id':'readme','path':'README.md','kind':'original_markdown',
                                'sha256':hashlib.sha256((cfg.root/'README.md').read_bytes()).hexdigest()}],
                  'targets':{key:{'status':'undocumented','reason':'Synthetic fixture has no API excerpt','excerpts':[]}}}
        document_path=cfg.root/'fixture-original.json';document_path.write_text(json.dumps(document))
        cfg.raw.setdefault('files',{}).update(original_doc_manifest='fixture-original.json',
            original_doc_manifest_sha256=hashlib.sha256(document_path.read_bytes()).hexdigest())
        with ExitStack() as stack:
            stack.enter_context(patch('aideal.api_registry.configured_api_details',return_value=details))
            model=stack.enter_context(patch('aideal.llm.invoke_text',return_value='println("DONE")'))
            executor=stack.enter_context(patch('aideal.execution.run_command',return_value=subprocess.CompletedProcess('synthetic',0,'DONE','')))
            stack.enter_context(patch('subprocess.run',side_effect=AssertionError('No subprocess is allowed')))
            stack.enter_context(patch.object(doc_check_execution,'public_api_details',return_value=details))
            stack.enter_context(patch.object(doc_check_execution,'public_api_surface',return_value={key}))
            stack.enter_context(patch('aideal.readme_agent.public_api_details',return_value=details))
            result=doc_check_execution._comprehension_execute(cfg,[ApiEntry(key,'Return input','','Original docs')],0,42,'original',show_code=True,max_fix_rounds=0)
        assert result['passed']
        assert model.call_count==1
        assert executor.call_count==1
        assert result['metrics'][key]['status']=='pass'
        checkpoint=Path(result['run']['checkpoint'])
        assert checkpoint.is_file()
        assert details[0]['file'] in checkpoint.read_text()
    finally:case.doCleanups()

def test_actual_authoring_loop_consumes_normalized_jvm_record(jvm_details):
    language,details=jvm_details
    case=readme_tests.ReadmeFixtures();case.setUpClass();case.setUp()
    try:
        cfg=case.cfg;cfg.language=language
        key=details[0]['api_id']
        manifest={'kind':'qualified_source_api_inventory','canonical_selection':'fixture-selection.json',
                  'canonical_selection_policy_version':'owner_qualified_max_arity_v2',
                  'canonical_selection_sha256':'fixture-selection','source_inventory_sha256':'fixture-source',
                  'source_commit':'fixture-commit','source_tree':'fixture-tree','source_version':'fixture'}
        inventory_path=cfg.root/'fixture-inventory.json'
        inventory_path.write_text(json.dumps(manifest))
        cfg.raw['codebase'].update(identity_mode='qualified',api_inventory='fixture-inventory.json',
                                   api_inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest())
        document={'schema':'aideal.original-documents/v1','library':'fixture','source_version':'fixture',
                  'source_commit':'fixture-commit','source_tree':'fixture-tree','scope':'fixture',
                  'documents':[{'id':'readme','path':'README.md','kind':'original_markdown',
                                'sha256':hashlib.sha256((cfg.root/'README.md').read_bytes()).hexdigest()}],
                  'targets':{key:{'status':'undocumented','reason':'Synthetic fixture has no API excerpt','excerpts':[]}}}
        document_path=cfg.root/'fixture-original.json';document_path.write_text(json.dumps(document))
        cfg.raw.setdefault('files',{}).update(original_doc_manifest='fixture-original.json',
            original_doc_manifest_sha256=hashlib.sha256(document_path.read_bytes()).hexdigest())
        with ExitStack() as stack:
            stack.enter_context(patch('aideal.api_registry.configured_api_details',return_value=details))
            stack.enter_context(patch.object(readme_generation,'public_api_details',return_value=details))
            stack.enter_context(patch.object(readme_generation,'public_api_surface',return_value={key}))
            stack.enter_context(patch.object(readme_generation,'original_target_texts',return_value={key:'Original docs'}))
            stack.enter_context(patch('subprocess.run',side_effect=AssertionError('No subprocess is allowed')))
            calls=stack.enter_context(case.fake_models())
            result=readme_generation.find_or_create(cfg,generate=True,max_generated=0)
        assert result['generated_ok']==1
        assert result['fallback_to_skeleton']==0
        assert len(calls)==2
        entry=next(c for c in calls if c[2]=='aideal/readme_entry')
        facts=json.loads(json.loads(entry[3])['api_facts'])
        assert facts['api_id']==key
        assert facts['source_doc'] is None
        assert facts['signature']==details[0]['signature']
        assert cfg.llm_readme.is_file()
        assert key in cfg.llm_readme.read_text()
    finally:
        case.doCleanups();case.doClassCleanups()
