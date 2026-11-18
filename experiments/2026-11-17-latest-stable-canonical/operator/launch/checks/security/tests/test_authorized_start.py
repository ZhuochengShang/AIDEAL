"""Exercise the launch operator with synthetic files and a mocked provider only."""
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

WRAPPER = Path(os.environ.get('AIDEAL_OPERATOR_UNDER_TEST', '/tmp/aideal-launch-2026-11-17/package/start_authorized.py'))
spec = importlib.util.spec_from_file_location('authorized_operator_under_test', WRAPPER)
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)
DUMMY = 'dummy-provider-credential-only-for-offline-tests'
sha_bytes = lambda raw: hashlib.sha256(raw).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

class AuthorizedLaunchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.study = self.base/'study'
        self.root = self.study/'operator'/'launch'
        self.root.mkdir(parents=True)
        self.qualified = self.study/'qualified'
        self.qualified.mkdir()
        self.review = self.study/'review_snapshot'
        self.review.mkdir()
        self.release = self.base/'releases'/'synthetic-frozen-release'
        (self.release/'scripts').mkdir(parents=True)
        queue = self.release/'scripts'/'run_cluster_experiment.py'
        queue.write_text('import json\nfrom pathlib import Path\ndef supervise(plan, key_file, workers=2):\n'
            ' root=Path(plan["root"])\n'
            ' assert not (root/"REVIEW_HOLD.json").exists()\n'
            ' assert not (root.parent/"REVIEW_HOLD.json").exists()\n'
            ' (root/"queue_called.json").write_text(json.dumps({"workers":workers,"key_file_argument":str(key_file)}))\n'
            ' return {"complete":True,"jobs":{"synthetic-r0":{"status":"complete"}}}\n')
        self.plan = {'root':str(self.qualified),'release':str(self.release),
                     'jobs':[{'id':'synthetic-r0','command':['python','unused.py','--model','synthetic-model']} ]}
        dump(self.root/'QUEUE.json', self.plan)
        files = {'scripts/run_cluster_experiment.py':sha_bytes(queue.read_bytes())}
        binding = {'release':self.release.name,'content_sha256':'synthetic-release-hash','files':files}
        dump(self.review/'EVALUATOR_RELEASE.json',binding)
        manifest_files={'EVALUATOR_RELEASE.json':sha_bytes((self.review/'EVALUATOR_RELEASE.json').read_bytes())}
        bundle=sha_bytes(json.dumps(manifest_files,sort_keys=True,separators=(',',':')).encode())
        dump(self.review/'SYNC_MANIFEST.json', {'bundle_sha256':bundle,'files':manifest_files})
        plan_hash=sha_bytes((self.root/'QUEUE.json').read_bytes())
        dump(self.root/'USER_AUTHORIZATION.json',{'authorized':True,'plan_sha256':plan_hash,'base_review_bundle_sha256':bundle})
        dump(self.root/'PRELAUNCH_CHECKS.json',{'status':'PASS','plan_sha256':plan_hash,'base_bundle_sha256':bundle,'release_sha256':'synthetic-release-hash','source_bindings':[]})
        dump(self.root/'RUNTIME_ENV.json',{'AIDEAL_SYNTHETIC_TEST':'safe'})
        self.key=self.base/'dummy-key.txt';self.key.write_text(DUMMY)
        for directory in (self.base,self.study,self.qualified):
            dump(directory/'REVIEW_HOLD.json',{'must_remain_unless_this_study_is_released':str(directory)})
        self.before={str(p):p.read_bytes() for p in (self.base/'REVIEW_HOLD.json',self.study/'REVIEW_HOLD.json',self.qualified/'REVIEW_HOLD.json')}
        self.stack=ExitStack();self.stack.enter_context(mock.patch.dict(os.environ,{},clear=False))
        self.stack.enter_context(mock.patch.object(sys,'path',list(sys.path)))

    def tearDown(self):
        self.stack.close();self.tmp.cleanup()

    @contextmanager
    def fake_provider(self, text='AIDEAL_READY', error=None):
        package=types.ModuleType('aideal');package.__path__=[]
        cfg=types.ModuleType('aideal.config');cfg.ModelSpec=lambda **kw:types.SimpleNamespace(**kw)
        llm=types.ModuleType('aideal.llm')
        def invoke(*args):
            if error is not None:raise error
            return text
        llm.invoke_text=mock.Mock(side_effect=invoke)
        llm.reset_usage=lambda:None
        llm.usage_snapshot=lambda:{'calls':1,'input_tokens':5,'output_tokens':2,'usage_complete':True}
        with mock.patch.dict(sys.modules,{'aideal':package,'aideal.config':cfg,'aideal.llm':llm}):yield llm.invoke_text

    @contextmanager
    def detect_key_reads(self):
        original=Path.read_text;reads=[]
        def read(path,*args,**kwargs):
            if path==self.key:reads.append(path)
            return original(path,*args,**kwargs)
        with mock.patch.object(Path,'read_text',read):yield reads

    def saved_states_contain_no_key(self):
        for path in self.root.rglob('*'):
            if path.is_file():self.assertNotIn(DUMMY,path.read_text(),str(path))

    def assert_holds_intact(self):
        for raw_path,raw in self.before.items():self.assertEqual(Path(raw_path).read_bytes(),raw)

    def test_failed_verification_never_reads_key(self):
        with (self.root/'QUEUE.json').open('a') as stream:stream.write('\n')
        with self.fake_provider() as invoke,self.detect_key_reads() as reads:
            self.assertEqual(operator.worker(self.root,self.key),2)
        self.assertEqual(reads,[]);invoke.assert_not_called();self.assert_holds_intact()
        self.assertEqual(json.loads((self.root/'LAUNCH_STATE.json').read_text())['status'],'BLOCKED')
        self.saved_states_contain_no_key()

    def test_tampered_manifest_cannot_keep_old_bundle_label(self):
        manifest=json.loads((self.review/'SYNC_MANIFEST.json').read_text())
        (self.review/'extra.txt').write_text('tampered addition')
        manifest['files']['extra.txt']=sha_bytes((self.review/'extra.txt').read_bytes())
        dump(self.review/'SYNC_MANIFEST.json',manifest)
        with self.fake_provider() as invoke,self.detect_key_reads() as reads:
            self.assertEqual(operator.worker(self.root,self.key),2)
        self.assertEqual(reads,[]);invoke.assert_not_called();self.assert_holds_intact()

    def test_provider_failure_preserves_holds_and_never_starts_queue(self):
        with self.fake_provider(error=RuntimeError('simulated denial '+DUMMY)) as invoke:
            self.assertEqual(operator.worker(self.root,self.key),2)
        invoke.assert_called_once();self.assert_holds_intact();self.assertFalse((self.qualified/'queue_called.json').exists())
        self.assertEqual(json.loads((self.root/'LAUNCH_STATE.json').read_text())['status'],'PROVIDER_BLOCKED')
        self.saved_states_contain_no_key()

    def test_success_releases_only_study_holds_and_delegates(self):
        with self.fake_provider() as invoke:
            self.assertEqual(operator.worker(self.root,self.key),0)
        invoke.assert_called_once()
        self.assertEqual((self.base/'REVIEW_HOLD.json').read_bytes(),self.before[str(self.base/'REVIEW_HOLD.json')])
        for scope,directory in [('study',self.study),('qualified',self.qualified)]:
            self.assertFalse((directory/'REVIEW_HOLD.json').exists())
            self.assertEqual((self.root/(scope+'-')/'REVIEW_HOLD.released.json').read_bytes(),self.before[str(directory/'REVIEW_HOLD.json')])
        called=json.loads((self.qualified/'queue_called.json').read_text())
        self.assertEqual(called,{'workers':2,'key_file_argument':str(self.key)})
        self.assertEqual(json.loads((self.root/'LAUNCH_STATE.json').read_text())['status'],'COMPLETE')
        self.saved_states_contain_no_key()

    def test_existing_queue_owner_is_rejected_before_key_read(self):
        supervisor=self.qualified/'supervisor';supervisor.mkdir()
        with (supervisor/'queue.lock').open('a') as held:
            fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.fake_provider() as invoke,self.detect_key_reads() as reads:
                self.assertEqual(operator.worker(self.root,self.key),2)
        self.assertEqual(reads,[]);invoke.assert_not_called();self.assert_holds_intact()
        self.assertFalse((self.qualified/'queue_called.json').exists())
        self.saved_states_contain_no_key()

    def test_unexpected_provider_text_is_redacted_in_saved_artifacts(self):
        with self.fake_provider(text='unexpected response '+DUMMY):
            self.assertEqual(operator.worker(self.root,self.key),2)
        self.assert_holds_intact();self.saved_states_contain_no_key()
        result=json.loads(next((self.root/'provider_checks').glob('check_*/result.json')).read_text())
        self.assertTrue(result['response_redacted'])

    def test_archive_collision_never_partially_releases_holds(self):
        dump(self.root/'qualified-'/'REVIEW_HOLD.released.json',{'existing_receipt':True})
        with self.fake_provider():self.assertEqual(operator.worker(self.root,self.key),2)
        self.assert_holds_intact();self.assertFalse((self.qualified/'queue_called.json').exists())
        self.assertFalse((self.root/'study-'/'REVIEW_HOLD.released.json').exists())

    def test_hold_rename_failure_rolls_back_previous_release(self):
        original=Path.rename
        def rename(path,target):
            if path==self.qualified/'REVIEW_HOLD.json':raise OSError('synthetic rename failure')
            return original(path,target)
        with self.fake_provider(),mock.patch.object(Path,'rename',rename):
            self.assertEqual(operator.worker(self.root,self.key),2)
        self.assert_holds_intact();self.assertFalse((self.qualified/'queue_called.json').exists())
        self.saved_states_contain_no_key()

if __name__=='__main__':unittest.main(verbosity=2)
