"""Explicit offline test allowlist. Never discover or execute a real study."""
from pathlib import Path
import contextlib, hashlib, importlib, io, json, os, sys, time, unittest

ROOT = Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow')
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ.pop('AIDEAL_TEST_TRACE', None)
sys.path[:0] = [str(ROOT/'tests'), str(ROOT), str(ROOT/'vendor/aideal_engine/src')]

# Block accidental live network use and any write to the shared source tree.
# Synthetic adapters are inspected fixture programs confined to TemporaryDirectory.
blocked_events = []
def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo'):
        blocked_events.append(event)
        raise RuntimeError('Offline audit prohibits network access')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0]))
        if path.name in ('quickrun.py', 'gemini-apikey-aideal.txt'):
            blocked_events.append('forbidden_file')
            raise RuntimeError('Forbidden scratch/credential file')
        mode, flags = args[1], args[2]
        write = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if write:
            absolute = path.absolute()
            if absolute == ROOT or ROOT in absolute.parents:
                blocked_events.append('source_tree_write')
                raise RuntimeError('Offline audit prohibits source-tree writes')
sys.addaudithook(audit)

MODULES = [
    'test_api_origin', 'test_api_canonical_selection',
    'test_compiler_api_registry', 'test_compiler_canonical_selection',
    'test_source_audit_registry', 'test_sql_canonical_aliases',
    'test_canonical_prompt_targets', 'test_canonical_launch_relocation',
    'test_readme_modules', 'test_readme_launcher', 'test_readme_replay',
    'test_original_micro_launcher', 'test_evaluation',
    'test_condition_evaluation', 'test_shared_evaluation',
    'test_evaluation_recovery', 'test_incomplete_evaluation',
]
EXCLUDED = {
    'test_evaluation.EvaluationTests.test_identical_copied_controller_accepts_frozen_identity': 'Copies the entire workflow folder, which can include the forbidden scratch file.',
    'test_evaluation.EvaluationTests.test_changed_copied_controller_is_rejected_before_any_command': 'Copies the entire workflow folder, which can include the forbidden scratch file.',
    'test_shared_evaluation.SharedEvaluationTests.test_changed_shared_runner_rejects_both_protocols_before_commands': 'Copies the entire workflow folder, which can include the forbidden scratch file.',
}
def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):yield from flatten(test)
        else:yield test

selection=[]
for name in MODULES:
    module=importlib.import_module(name)
    selection.extend(t for t in flatten(unittest.defaultTestLoader.loadTestsFromModule(module)) if t.id() not in EXCLUDED)
identities={str(ROOT/'tests'/f'{name}.py'):hashlib.sha256((ROOT/'tests'/f'{name}.py').read_bytes()).hexdigest() for name in MODULES}
(OUT/'TEST_SELECTION.json').write_text(json.dumps({'modules':MODULES,'included_ids':[t.id() for t in selection],'excluded':EXCLUDED,'test_file_sha256':identities},indent=2)+'\n')

class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.rows=[]
    def startTest(self,test):super().startTest(test);self.started=time.monotonic()
    def stopTest(self,test):
        status='pass'
        if any(t is test for t,_ in self.failures):status='failure'
        if any(t is test for t,_ in self.errors):status='error'
        if any(t is test for t,_ in self.skipped):status='skipped'
        self.rows.append({'test':test.id(),'status':status,'seconds':round(time.monotonic()-self.started,4)})
        super().stopTest(test)

started=time.monotonic()
with (OUT/'TEST_LOG.txt').open('w') as log, (OUT/'PROGRAM_OUTPUT.txt').open('w') as output:
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Result).run(unittest.TestSuite(selection))
receipt={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'intentionally_excluded':EXCLUDED,'elapsed_seconds':round(time.monotonic()-started,3),'python':sys.version,'source_root':str(ROOT),'test_files_unchanged':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in identities.items()),'network_guard_events':blocked_events,'real_model_calls':0,'real_library_experiments':0,'synthetic_local_adapter_processes':'permitted by inspected fixture tests','limitations':['Tests of the existing global bare-name canonical policy verify historical compatibility; they do not implement the newly agreed owner-qualified selection.','No dependency installation, real library build, model API access, or full experiment was attempted.','Three recursive controller-copy tests were intentionally excluded to protect the scratch file.'],'results':result.rows,'failure_details':[{'test':t.id(),'traceback':s} for t,s in result.failures+result.errors]}
(OUT/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('results','failure_details','intentionally_excluded','limitations')}))
if not result.wasSuccessful():
    print(json.dumps(receipt['failure_details'],indent=2))
    raise SystemExit(1)
