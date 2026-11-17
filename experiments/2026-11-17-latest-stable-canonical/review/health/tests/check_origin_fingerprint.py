"""Prove direct README resume binds the new ownership module, without writes to it."""
from pathlib import Path
import importlib, json, sys, types
from unittest.mock import patch

ROOT=Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow')
OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'vendor/aideal_engine/src')]
import test_readme_modules as fixtures
from aideal import readme_generation as original
target=ROOT/'vendor/aideal_engine/src/aideal/api_origin.py'
source=Path(original.__file__).read_text()
needle='"api_discovery.py", "api_registry.py",'
assert source.count(needle)==1
candidate_source=source.replace(needle,'"api_discovery.py", "api_origin.py", "api_registry.py",')
candidate=types.ModuleType('aideal._origin_fingerprint_candidate')
candidate.__package__='aideal';candidate.__file__=original.__file__
exec(compile(candidate_source,original.__file__,'exec'),candidate.__dict__)

def check(module):
    cls=fixtures.ReadmeContractTests;cls.setUpClass();f=cls('runTest');f.setUp()
    try:
        f.python_source()
        f.cfg.raw['codebase']['api_origin']={'source_roots':['src'],'library_namespaces':['api'],'external_namespaces':['builtins','math']}
        with f.fake_models() as calls:
            initial=module.find_or_create(f.cfg,generate=True,max_generated=0)
            count=len(calls);reads=[];actual_read=Path.read_bytes
            def changed_bytes(path):
                data=actual_read(path)
                if path==target:
                    reads.append(str(path));return data+b'\n# Synthetic implementation revision.\n'
                return data
            with patch.object(Path,'read_bytes',changed_bytes):
                try:result=module.find_or_create(f.cfg,generate=True,max_generated=0,resume=True)
                except ValueError as e:
                    result={'rejected':True,'message':str(e)}
                else:result={'rejected':False,'resumed_entries':result.get('resumed_entries')}
            result.update(origin_hash_reads=len(reads),new_mock_calls=len(calls)-count,initial_generated=initial.get('generated_ok'))
            return result
    finally:f.doCleanups();cls.doClassCleanups()

report={'baseline':check(original),'candidate':check(candidate),'actual_source_modified':False,'real_model_calls':0,'subject_executions':0}
assert report['baseline']['rejected'] is False,report
assert report['baseline']['origin_hash_reads']==0,report
assert report['candidate']['rejected'] is True and 'fingerprint changed' in report['candidate']['message'],report
assert report['candidate']['origin_hash_reads']>0 and report['candidate']['new_mock_calls']==0,report
(OUT/'ORIGIN_FINGERPRINT_REGRESSION.json').write_text(json.dumps(report,indent=2)+'\n')
stage=OUT/'patch';stage.mkdir(exist_ok=True)
(stage/'readme_generation.py').write_text(candidate_source)
import difflib
(stage/'origin_fingerprint.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),candidate_source.splitlines(True),fromfile='a/vendor/aideal_engine/src/aideal/readme_generation.py',tofile='b/vendor/aideal_engine/src/aideal/readme_generation.py')))
print(json.dumps(report))
