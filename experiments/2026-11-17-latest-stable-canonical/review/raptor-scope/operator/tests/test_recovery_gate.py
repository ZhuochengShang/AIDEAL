"""Offline recovery-launcher checks. No provider or cluster access."""
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,subprocess,sys,tempfile,threading,time,types,unittest
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'start_after_queue.py'
spec=importlib.util.spec_from_file_location('recovery_gate',SCRIPT)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data))
class RecoveryGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.base=Path(self.tmp.name)
        self.root=self.base/'recovery'/'launch';self.root.mkdir(parents=True)
        self.old=self.base/'original'/'launch';self.old.mkdir(parents=True)
        self.release=self.base/'release';self.release.mkdir()
        (self.release/'implementation.py').write_text('value = 1\n')
        files={'implementation.py':gate.sha(self.release/'implementation.py')}
        content=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.plan={'root':str(self.root.parent),'release':str(self.release),'jobs':[{'id':'java-r0'}]}
        write(self.root/'QUEUE.json',self.plan)
        self.checks={'status':'PASS','plan_sha256':gate.sha(self.root/'QUEUE.json'),'release_sha256':content,'original_launch':str(self.old),'replaces_jobs':['java-r0']}
        write(self.root/'RECOVERY_CHECKS.json',self.checks)
        write(self.root/'EVALUATOR_RELEASE.json',{'release':'release','files':files,'content_sha256':content})
        (self.old/'start_authorized.py').write_text('def verified_inputs(root):\n    return True\n')
        write(self.old/'RUNTIME_ENV.json',{})
        write(self.old/'QUEUE.json',{'root':str(self.old.parent),'jobs':[{'id':'java-r0'},{'id':'python-r0'}]})
        self.summary={'jobs':{'java-r0':{'status':'failed'},'python-r0':{'status':'complete'}}}
        write(self.old.parent/'supervisor/summary.json',self.summary)
        self.secret=self.base/'credential-not-read.txt'
    def verified(self,*_args):return self.plan,self.release,self.old,self.checks
    def state(self):return json.loads((self.root/'STATE.json').read_text())
    def finish(self, *_a, **kwargs):
        self.assertEqual(kwargs['workers'],2)
        return {'complete':True,'jobs':{'java-r0':{'status':'complete'}}}
    def test_valid_manifest(self):
        self.assertEqual(gate.verify(self.root)[0],self.plan)
    def test_modified_scoped_input_rejected(self):
        source=self.base/'scoped-manifest.json';source.write_text('["raster.api"]')
        self.checks['scope_files']={str(source):gate.sha(source)};write(self.root/'RECOVERY_CHECKS.json',self.checks)
        gate.verify(self.root)
        source.write_text('["unrelated.api"]')
        with self.assertRaisesRegex(ValueError,'scope or original-document inputs changed'):gate.verify(self.root)
    def test_modified_queue_rejected(self):
        (self.root/'QUEUE.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'queue identity'):gate.verify(self.root)
    def test_modified_release_file_rejected(self):
        (self.release/'implementation.py').write_text('value = 2')
        with self.assertRaisesRegex(ValueError,'bytes changed'):gate.verify(self.root)
    def test_false_manifest_digest_rejected(self):
        p=self.root/'EVALUATOR_RELEASE.json';b=json.loads(p.read_text());b['content_sha256']='fake';write(p,b)
        self.checks['release_sha256']='fake';write(self.root/'RECOVERY_CHECKS.json',self.checks)
        with self.assertRaisesRegex(ValueError,'identity changed'):gate.verify(self.root)
    def test_unsafe_release_path_rejected(self):
        p=self.root/'EVALUATOR_RELEASE.json';b=json.loads(p.read_text());b['files']={'../outside':'x'};write(p,b)
        with self.assertRaisesRegex(ValueError,'Unsafe'):gate.verify(self.root)
    def test_duplicate_worker_preserves_owner_state(self):
        write(self.root/'STATE.json',{'status':'RUNNING','pid':123});before=(self.root/'STATE.json').read_bytes()
        with (self.root/'worker.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.assertEqual(gate.worker(self.root,self.secret),2)
        self.assertEqual((self.root/'STATE.json').read_bytes(),before)
    def test_duplicate_parent_preserves_process_receipt(self):
        write(self.root/'PROCESS.json',{'pid':123});before=(self.root/'PROCESS.json').read_bytes()
        with (self.root/'worker.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with patch.object(gate,'__file__',str(self.root/'start_after_queue.py')),patch.object(sys,'argv',['gate','--key-file',str(self.secret)]),patch.object(gate,'verify') as verify:
                self.assertEqual(gate.main(),2);verify.assert_not_called()
        self.assertEqual((self.root/'PROCESS.json').read_bytes(),before)
    def test_waits_for_upstream_and_holds_it_during_supervision(self):
        called=threading.Event();returns=[]
        def supervise(*args,**kw):
            with (self.old.parent/'supervisor/queue.lock').open('a') as lock:
                with self.assertRaises(BlockingIOError):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            called.set();return self.finish(*args,**kw)
        with (self.old.parent/'supervisor/queue.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with patch.object(gate,'verify',side_effect=self.verified),patch.object(gate,'load_module',return_value=types.SimpleNamespace(supervise=supervise)):
                thread=threading.Thread(target=lambda:returns.append(gate.worker(self.root,self.secret)));thread.start()
                for _ in range(100):
                    if (self.root/'STATE.json').exists() and self.state()['status']=='WAITING_FOR_ORIGINAL_QUEUE':break
                    time.sleep(.01)
                self.assertEqual(self.state()['status'],'WAITING_FOR_ORIGINAL_QUEUE');self.assertFalse(called.is_set())
                fcntl.flock(lock,fcntl.LOCK_UN);thread.join(3)
                self.assertFalse(thread.is_alive());self.assertEqual(returns,[0]);self.assertTrue(called.is_set())
        self.assertEqual(self.state()['status'],'COMPLETE')
    def test_missing_or_nonterminal_upstream_jobs_block(self):
        for summary in ({'jobs':{'java-r0':{'status':'failed'}}},{'jobs':{'java-r0':{'status':'failed'},'python-r0':{'status':'running'}}},{'jobs':{'java-r0':{'status':'complete'},'python-r0':{'status':'complete'}}}):
            with self.subTest(summary=summary):
                write(self.old.parent/'supervisor/summary.json',summary)
                with patch.object(gate,'verify',side_effect=self.verified),patch.object(gate,'load_module') as load:
                    self.assertEqual(gate.worker(self.root,self.secret),2);load.assert_not_called()
                self.assertEqual(self.state()['status'],'BLOCKED')
    def test_provider_exception_message_never_recorded(self):
        def fail(*_a,**_kw):raise RuntimeError('sensitive-provider-value')
        with patch.object(gate,'verify',side_effect=self.verified),patch.object(gate,'load_module',return_value=types.SimpleNamespace(supervise=fail)):
            self.assertEqual(gate.worker(self.root,self.secret),2)
        self.assertNotIn('sensitive-provider-value',(self.root/'STATE.json').read_text());self.assertEqual(self.state()['error_type'],'RuntimeError')
    def test_parent_passes_held_lock_to_child(self):
        def spawn(command,**kw):
            self.assertIn('--lock-fd',command);self.assertEqual(kw['pass_fds'],(int(command[command.index('--lock-fd')+1]),))
            with (self.root/'worker.lock').open('a') as other:
                with self.assertRaises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
            return types.SimpleNamespace(pid=456)
        with patch.object(gate,'__file__',str(self.root/'start_after_queue.py')),patch.object(sys,'argv',['gate','--key-file',str(self.secret)]),patch.object(gate,'verify',side_effect=self.verified),patch.object(gate.subprocess,'Popen',side_effect=spawn):
            self.assertEqual(gate.main(),0)
        self.assertEqual(json.loads((self.root/'PROCESS.json').read_text())['pid'],456)
    def test_actual_detached_lock_handoff_and_duplicate_start(self):
        script=self.root/'start_after_queue.py';script.write_bytes(SCRIPT.read_bytes())
        fake=self.release/'scripts/run_cluster_experiment.py';fake.parent.mkdir()
        fake.write_text("def supervise(plan, key_file, workers=2):\n    assert workers == 2\n    return {'complete': True, 'jobs': {'java-r0': {'status':'complete'}}}\n")
        binding=json.loads((self.root/'EVALUATOR_RELEASE.json').read_text());binding['files']['scripts/run_cluster_experiment.py']=gate.sha(fake)
        content=hashlib.sha256(json.dumps(binding['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest();binding['content_sha256']=content;write(self.root/'EVALUATOR_RELEASE.json',binding)
        self.checks['release_sha256']=content;write(self.root/'RECOVERY_CHECKS.json',self.checks)
        command=[sys.executable,str(script),'--key-file',str(self.secret)]
        with (self.old.parent/'supervisor/queue.lock').open('a') as upstream:
            fcntl.flock(upstream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            started=subprocess.run(command,capture_output=True,text=True,timeout=3)
            self.assertEqual(started.returncode,0,started.stderr)
            for _ in range(100):
                if (self.root/'STATE.json').exists() and self.state()['status']=='WAITING_FOR_ORIGINAL_QUEUE':break
                time.sleep(.01)
            self.assertEqual(self.state()['status'],'WAITING_FOR_ORIGINAL_QUEUE')
            process_before=(self.root/'PROCESS.json').read_bytes();state_before=(self.root/'STATE.json').read_bytes()
            duplicate=subprocess.run(command,capture_output=True,text=True,timeout=3)
            self.assertEqual(duplicate.returncode,2,duplicate.stderr);self.assertIn('ALREADY_RUNNING',duplicate.stdout)
            self.assertEqual((self.root/'PROCESS.json').read_bytes(),process_before);self.assertEqual((self.root/'STATE.json').read_bytes(),state_before)
            fcntl.flock(upstream,fcntl.LOCK_UN)
            for _ in range(100):
                if self.state()['status']=='COMPLETE':break
                time.sleep(.01)
            self.assertEqual(self.state()['status'],'COMPLETE')
if __name__=='__main__':unittest.main()
