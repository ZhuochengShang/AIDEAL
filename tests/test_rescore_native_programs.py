"""Exercise saved-program replay without provider access or measured-file writes."""
import importlib.util
import json
from pathlib import Path
import shlex
import sys
from unittest.mock import patch
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'vendor').exists():
    ROOT = Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow')
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor/aideal_engine/src')]
spec = importlib.util.spec_from_file_location('rescore', ROOT / 'scripts/rescore_native_programs.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
r.ROOT = ROOT


def setup_saved(tmp_path, snippets):
    old = tmp_path / 'original'
    (old / 'configs').mkdir(parents=True)
    raw = {'project': {'name': 'scope-fixture', 'language': 'Python'},
           'codebase': {'source_globs': ['source.py']},
           'files': {'original_readme': 'README.md'},
           'comprehension': {'execute': {'scaffold': 'scaffold.py', 'region': ['# TODO API_TEST_START', '# TODO API_TEST_END'],
              'preamble': '', 'output_dir': 'execution/output', 'local_uris': False,
              'sample_data': {}, 'success_marker': '__DONE__', 'error_marker': '__RUN_ERR__',
              'require_correctness': True}},
           'models': {'registry': {'fake': {'provider': 'fake', 'model': 'none'}}, 'roles': {'audience': 'fake', 'author': 'fake'}}}
    (old / 'configs/aideal.yaml').write_text(yaml.safe_dump(raw))
    (old / 'source.py').write_text('def f(): pass\n')
    (old / 'README.md').write_text('Synthetic test.\n')
    details = {}
    for api, snippet in snippets.items():
        work = old / 'execution' / ('run_' + api)
        attempt = work / 'attempt_0001'
        attempt.mkdir(parents=True)
        program = (f'def run():\n    x = 1\n    output_dir = {str(old / "execution/output")!r}\n'
                   '    def api_test():\n        # TODO API_TEST_START\n' +
                   '\n'.join('        '+s for s in snippet.splitlines()) +
                   '\n        # TODO API_TEST_END\n    api_test()\nrun()\nprint("__DONE__")\n')
        for p in [work/'api_test.py', attempt/'api_test.py']:p.write_text(program)
        (attempt/'execution.json').write_text(json.dumps({'command':shlex.join([sys.executable, str(work/'api_test.py')]), 'cwd':str(old/'execution'), 'timeout_s':10}))
        (attempt/'request.json').write_text(json.dumps({'system':'Generate body','user':api}))
        details[api]={'status':'fail','code':snippet,'scala_file':str(work/'api_test.py')}
    source = old/'result.json'
    source.write_text(json.dumps({'mode':'execute','doc_source':'original','run':{'complete':True,'max_fix_rounds':0},'details':details,'metrics':{k:{} for k in details}}))
    return source


def test_scope_replay_passes_without_model_and_preserves_saved_program(tmp_path):
    source=setup_saved(tmp_path,{'f':'x = x + 1\nassert x == 2\nprint("__CHECK__ f 2")'})
    old=json.loads(source.read_text())['details']['f']['scala_file']
    checksum=r.digest(old)
    with patch('aideal.llm.invoke_text',side_effect=AssertionError('must never call provider')):
        result=r.run_program_case(source,'f',tmp_path/'replay/f')
    assert result['status']=='pass'
    assert result['llm_calls']==0 and result['input_tokens']==0
    assert r.digest(old)==checksum
    assert r.run_program_case(source,'f',tmp_path/'replay/f')==result


def test_each_case_output_is_independent_and_completed_evidence_is_checked(tmp_path):
    source=setup_saved(tmp_path,{
        'mkdir':'from pathlib import Path\nPath(output_dir,"image.png").mkdir()\nprint("__CHECK__ mkdir directory")',
        'write':'from pathlib import Path\np=Path(output_dir,"image.png")\np.write_text("ok")\nassert p.read_text()=="ok"\nprint("__CHECK__ write ok")'})
    one=r.run_program_case(source,'mkdir',tmp_path/'replay/mkdir')
    two=r.run_program_case(source,'write',tmp_path/'replay/write')
    assert one['status']==two['status']=='pass'
    assert not (source.parent/'execution/output').exists()
    Path(two['scala_file']).parent.joinpath('stdout.txt').write_text('tampered')
    with pytest.raises(ValueError,match='evidence changed'):
        r.run_program_case(source,'write',tmp_path/'replay/write')


def test_interrupted_execution_gets_fresh_physical_attempt(tmp_path):
    source=setup_saved(tmp_path,{'f':'print("__CHECK__ f ok")'})
    destination=tmp_path/'replay/f'
    with patch('aideal.execution.run_command',side_effect=RuntimeError('interrupted')):
        with pytest.raises(RuntimeError):r.run_program_case(source,'f',destination)
    result=r.run_program_case(source,'f',destination)
    assert result['status']=='pass'
    assert (destination/'attempt_0001/api_test.py').is_file()
    assert 'attempt_0002' in result['scala_file']


def test_refuses_old_output_and_changed_sources(tmp_path):
    source=setup_saved(tmp_path,{'f':'print("__CHECK__ f ok")'})
    with pytest.raises(ValueError,match='separate'):r.run_program_case(source,'f',source.parent/'new')
    dest=tmp_path/'replay/f'
    r.run_program_case(source,'f',dest)
    row=json.loads(source.read_text())['details']['f']
    Path(row['scala_file']).parent.joinpath('attempt_0001/api_test.py').write_text('changed')
    with pytest.raises(ValueError,match='Prepared evidence changed'):r.run_program_case(source,'f',dest)


def test_development_override_is_labeled_not_a_replay(tmp_path):
    source=setup_saved(tmp_path,{'f':'assert False\nprint("__CHECK__ f wrong")'})
    result=r.run_program_case(source,'f',tmp_path/'development/f',code_override='assert 2+2 == 4\nprint("__CHECK__ f 4")')
    assert result['status']=='pass' and result['mode']=='development_example'


def test_source_cache_does_not_mix_changed_result_with_old_parsed_content(tmp_path):
    source=setup_saved(tmp_path,{'f':'print("__CHECK__ f ok")'})
    first=r.load_source(str(source))
    changed=json.loads(source.read_text())
    changed['details']['f']['status']='pass'
    source.write_text(json.dumps(changed))
    second=r.load_source(str(source))
    assert first[1]['details']['f']['status']=='fail'
    assert second[1]['details']['f']['status']=='pass'


def test_source_mutation_during_execution_withholds_completion(tmp_path):
    source=setup_saved(tmp_path,{'f':'print("__CHECK__ f ok")'})
    import aideal.execution
    execute=aideal.execution.run_command
    def mutate(*args,**kwargs):
        result=execute(*args,**kwargs)
        source.write_text(source.read_text()+'\n')
        return result
    with patch('aideal.execution.run_command',side_effect=mutate):
        with pytest.raises(ValueError,match='input changed during execution'):
            r.run_program_case(source,'f',tmp_path/'replay/f')
    assert not (tmp_path/'replay/f/completion.json').exists()
