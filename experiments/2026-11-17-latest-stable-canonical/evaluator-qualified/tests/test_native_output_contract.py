"""Output caps and provider-stopped text: offline provider/process doubles only."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace, ModuleType
import unittest
from unittest.mock import patch, Mock
from contextlib import ExitStack
import yaml
from aideal.config import ModelSpec, load_config
from aideal import llm, doc_check_execution
from aideal.readme_format import ApiEntry
from aideal.readme_recording import ReadmeCallRecorder, ReadmeGenerationStopped
import test_doc_check_modules as native_fixtures


def response(text='valid text', metadata=None, additional=None):
    return SimpleNamespace(content=text, response_metadata=metadata or {},
        additional_kwargs=additional or {}, usage_metadata={'input_tokens': 5, 'output_tokens': 2})


class OutputContractTests(unittest.TestCase):
    def setUp(self):
        llm.reset_usage()
        self.spec=ModelSpec('google','synthetic',8192)

    def test_config_cap_validates_and_loads_without_changing_legacy_default(self):
        self.assertIsNone(ModelSpec('google','synthetic').max_output_tokens)
        for invalid in (True,False,0,-1,1.5,'8192'):
            with self.subTest(invalid=invalid),self.assertRaisesRegex(ValueError,'positive integer'):
                ModelSpec('google','synthetic',invalid)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'configs/aideal.yaml';p.parent.mkdir()
            p.write_text(yaml.safe_dump({'models':{'registry':{'selected':{
                'provider':'google','model':'synthetic','max_output_tokens':8192}}}}))
            self.assertEqual(8192,load_config(p).registry['selected'].max_output_tokens)

    def test_provider_specific_cap_parameters_and_legacy_omission(self):
        mapping={'google':('langchain_google_genai','ChatGoogleGenerativeAI','max_output_tokens'),
            'openai':('langchain_openai','ChatOpenAI','max_tokens'),
            'codex':('langchain_openai','ChatOpenAI','max_tokens'),
            'openai-responses':('langchain_openai','ChatOpenAI','max_tokens'),
            'anthropic':('langchain_anthropic','ChatAnthropic','max_tokens'),
            'ollama':('langchain_ollama','ChatOllama','num_predict')}
        for provider,(module_name,class_name,argument) in mapping.items():
            with self.subTest(provider=provider):
                module=ModuleType(module_name);constructor=Mock();setattr(module,class_name,constructor)
                with patch.dict(sys.modules,{module_name:module}):
                    llm.get_chat_model(ModelSpec(provider,'synthetic',8192))
                    self.assertEqual(8192,constructor.call_args.kwargs[argument])
                    llm.get_chat_model(ModelSpec(provider,'synthetic'))
                    self.assertNotIn(argument,constructor.call_args.kwargs)
        with self.assertRaisesRegex(ValueError,'Output cap is unsupported'):
            llm.get_chat_model(ModelSpec('unknown','synthetic',8192))

    def test_known_truncated_outputs_keep_raw_text_metadata_and_usage(self):
        examples=[{'finish_reason':'MAX_TOKENS'},{'finish_reason':'length'},
            {'stop_reason':'max_tokens'},{'done_reason':'length'},
            {'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'}}]
        for metadata in examples:
            with self.subTest(metadata=metadata),patch.object(llm,'get_chat_model',return_value=SimpleNamespace(invoke=lambda _:response('partial(',metadata))),patch.object(llm,'_wait_for_provider_slot'):
                with self.assertRaises(llm.ProviderOutputError) as caught:
                    llm.invoke_text(self.spec,'system','user')
                exc=caught.exception
                self.assertEqual('provider-incomplete-output',exc.category)
                self.assertEqual('partial(',exc.response_text)
                self.assertEqual(metadata,exc.provider_evidence['response_metadata'])
                self.assertEqual(2,exc.provider_evidence['usage_metadata']['output_tokens'])
        self.assertEqual(len(examples),llm.usage_snapshot()['calls'])

    def test_refused_and_empty_responses_are_not_accepted(self):
        cases=[(response('refused',{'finish_reason':'SAFETY'}),'provider-refused-output'),
            (response('refused',additional={'refusal':'cannot comply'}),'provider-refused-output'),
            (response([{'type':'refusal','refusal':'cannot comply'}]),'provider-refused-output'),
            (response('',{'status':'incomplete','incomplete_details':{'reason':'content_filter'}}),'provider-refused-output'),
            (response('   '),'provider-empty-output'),(response(None),'provider-empty-output')]
        for returned,category in cases:
            with self.subTest(category=category),self.assertRaises(llm.ProviderOutputError) as caught:
                llm._checked_response_text(returned,self.spec)
            self.assertEqual(category,caught.exception.category)

    def test_missing_usage_is_distinct_from_reported_zero_and_failed_request(self):
        before=llm.usage_snapshot()
        self.assertEqual(0,before['calls'])
        returned=response();returned.usage_metadata=None
        with patch.object(llm,'get_chat_model',return_value=SimpleNamespace(invoke=lambda _:returned)),patch.object(llm,'_wait_for_provider_slot'):
            llm.invoke_text(self.spec,'s','u')
        missing=llm.usage_delta(before)
        self.assertEqual(1,missing['calls'])
        self.assertEqual(1,missing['missing_usage_calls'])
        self.assertFalse(missing['usage_complete'])
        self.assertFalse(missing['by_model']['google:synthetic']['usage_complete'])
        before=llm.usage_snapshot();returned.usage_metadata={'input_tokens':0,'output_tokens':0}
        with patch.object(llm,'get_chat_model',return_value=SimpleNamespace(invoke=lambda _:returned)),patch.object(llm,'_wait_for_provider_slot'):
            llm.invoke_text(self.spec,'s','u')
        knownzero=llm.usage_delta(before)
        self.assertTrue(knownzero['usage_complete'])
        self.assertEqual(0,knownzero['missing_usage_calls'])
        self.assertEqual(0,knownzero['output_tokens'])
        before=llm.usage_snapshot()
        with patch.object(llm,'get_chat_model',return_value=SimpleNamespace(invoke=Mock(side_effect=RuntimeError('synthetic unavailable')))),patch.object(llm,'_wait_for_provider_slot'):
            with self.assertRaises(RuntimeError):llm.invoke_text(self.spec,'s','u')
        self.assertEqual(0,llm.usage_delta(before)['calls'])
        returned.usage_metadata=None;returned.response_metadata={'finish_reason':'MAX_TOKENS'}
        with self.assertRaises(llm.ProviderOutputError) as caught:llm._checked_response_text(returned,self.spec)
        self.assertIsNone(caught.exception.provider_evidence['usage_metadata'])

    def test_unknown_finish_and_text_blocks_remain_supported(self):
        self.assertEqual('valid text',llm._checked_response_text(response(metadata={'finish_reason':'NEW_UNKNOWN'}),self.spec))
        self.assertEqual('xy',llm._checked_response_text(response([{'type':'text','text':'x'},'y']),self.spec))
        self.assertEqual('valid text',llm._checked_response_text(response(),self.spec))

    def test_author_failure_saves_partial_response_and_never_reuses_it(self):
        exc=llm.ProviderOutputError('provider-incomplete-output','partial',{
            'finish_reason':'MAX_TOKENS','response_metadata':{'finish_reason':'MAX_TOKENS'},
            'usage_metadata':{'input_tokens':5,'output_tokens':2},'max_output_tokens':8192})
        with tempfile.TemporaryDirectory() as directory:
            recorder=ReadmeCallRecorder(directory,{'source':'synthetic'})
            with patch.object(llm,'invoke_text',side_effect=exc),patch.object(recorder,'_validate') as validate:
                for _ in range(2):
                    with self.assertRaises(ReadmeGenerationStopped):recorder.invoke(self.spec,'s','u',phase='entry',api='python:pkg.f')
                validate.assert_not_called()
            attempts=list(Path(directory).glob('*/attempt_*'));self.assertEqual(2,len(attempts))
            for attempt in attempts:
                self.assertEqual('partial',(attempt/'response.txt').read_text())
                state=json.loads((attempt/'provider.json').read_text())
                self.assertEqual('provider-incomplete-output',state['category'])
                self.assertNotEqual('complete',state['status'])
                self.assertEqual(8192,json.loads((attempt/'request.json').read_text())['max_output_tokens'])

    def test_author_request_identity_includes_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder=ReadmeCallRecorder(directory,{'source':'synthetic'})
            with patch.object(llm,'invoke_text',return_value='synthetic'),patch.object(recorder,'_validate'):
                recorder.invoke(self.spec,'s','u',phase='entry')
                recorder.invoke(ModelSpec('google','synthetic',4096),'s','u',phase='entry')
            self.assertEqual(2,recorder.new_calls)
            self.assertEqual(2,len(list(Path(directory).iterdir())))


class NativeIncompleteTests(unittest.TestCase):
    setUp=native_fixtures.DocCheckModuleTests.setUp
    fingerprint_arguments=native_fixtures.DocCheckModuleTests.fingerprint_arguments

    def test_max_tokens_cannot_fill_or_execute_scaffold_and_keeps_evidence(self):
        self.cfg.registry['fake'].max_output_tokens=8192
        self.cfg.comprehension['execute']['stop_on_provider_error']=True
        returned=response('print("PARTIAL")',{'finish_reason':'MAX_TOKENS'})
        with ExitStack() as stack:
            stack.enter_context(patch.object(llm,'get_chat_model',return_value=SimpleNamespace(invoke=lambda _:returned)))
            fill=stack.enter_context(patch.object(doc_check_execution,'_fill_scaffold',side_effect=AssertionError('must not fill scaffold')))
            execute=stack.enter_context(patch('aideal.execution.run_command',side_effect=AssertionError('must not execute')))
            stack.enter_context(patch('subprocess.run',side_effect=AssertionError('must not start process')))
            stack.enter_context(patch.object(doc_check_execution,'public_api_details',return_value=[]))
            stack.enter_context(patch.object(doc_check_execution,'public_api_surface',return_value={'f'}))
            stack.enter_context(patch('aideal.readme_agent.public_api_details',return_value=[]))
            result=doc_check_execution._comprehension_execute(self.cfg,[ApiEntry('f','Goal','','docs')],0,42,'aideal',max_fix_rounds=0)
            fill.assert_not_called();execute.assert_not_called()
        self.assertEqual('provider-incomplete-output',result['metrics']['f']['error_category'])
        self.assertTrue(result['run']['stopped_on_provider_error'])
        self.assertFalse(result['run']['complete'])
        attempts=list((self.root/'work').glob('**/attempt_*'));self.assertEqual(1,len(attempts))
        attempt=attempts[0]
        self.assertEqual('print("PARTIAL")',(attempt/'response.txt').read_text())
        state=json.loads((attempt/'provider.json').read_text())
        self.assertEqual('MAX_TOKENS',state['provider_response']['finish_reason'])
        self.assertEqual('provider-incomplete-output',state['category'])
        self.assertFalse((attempt/'execution.json').exists())
        self.assertEqual(8192,json.loads((attempt/'request.json').read_text())['max_output_tokens'])

    def test_runtime_cap_changes_native_fingerprint(self):
        from aideal.doc_check_provenance import _comprehension_fingerprint_components
        before=_comprehension_fingerprint_components(self.cfg,**self.fingerprint_arguments())
        self.cfg.registry['fake'].max_output_tokens=8192
        after=_comprehension_fingerprint_components(self.cfg,**self.fingerprint_arguments())
        self.assertNotEqual(before['models'],after['models'])
        self.assertEqual(8192,after['models']['audience_max_output_tokens'])


if __name__=='__main__':unittest.main()
