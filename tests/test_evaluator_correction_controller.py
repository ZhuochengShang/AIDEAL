"""The launch gate must reject unsupported setups before any paid stage."""
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'vendor/aideal_engine/src')]
spec = importlib.util.spec_from_file_location('correction_controller', ROOT / 'scripts/run_evaluator_correction.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def launch(tmp_path, *, expected='pass', actual='pass', unresolved=None, phases=('rescore','d2','matched'), tamper=False):
    output = tmp_path / 'corrected'
    (output / 'operator').mkdir(parents=True)
    proof = tmp_path / 'proof.json'
    proof.write_text(json.dumps({'status': actual, 'exit_code':1 if actual=='fail' else 0,
                                 'stderr_tail':'AssertionError: deliberate' if actual=='fail' else ''}))
    ready = {'status':'passed', 'evaluator':{'sha256':'frozen'},
             'banks':{'mdanalysis':{'status':'passed','unresolved_setup':unresolved or []}},
             'checks':[{'bank':'mdanalysis','role':'negative' if expected=='fail' else 'positive', 'required_diagnostic':'AssertionError: deliberate',
                        'result':c.binding(proof),'expected':expected}]}
    other = tmp_path / 'other.json'
    other.write_text(json.dumps({'status':'fail' if expected=='pass' else 'pass',
                                 'exit_code':1 if expected=='pass' else 0,
                                 'stderr_tail':'AssertionError: deliberate' if expected=='pass' else ''}))
    ready['checks'].append({'bank':'mdanalysis','result':c.binding(other),
                            'role':'negative' if expected=='pass' else 'positive',
                            'required_diagnostic':'AssertionError: deliberate',
                            'expected': 'fail' if expected == 'pass' else 'pass'})
    (output / 'operator/READINESS.json').write_text(json.dumps(ready))
    if tamper:proof.write_text(json.dumps({'status':actual,'tampered':True}))
    plans={p:{'jobs':[]} for p in ('rescore','d2','matched')}
    argv=['controller','--study',str(tmp_path),'--output',str(output),'--key-file',str(tmp_path/'credential-path-only'),
          '--banks','mdanalysis','--phases',*phases,'--run']
    with patch.object(sys,'argv',argv), patch.object(c,'prepare',return_value=plans), \
         patch.object(c,'verify_release',return_value=ready['evaluator']), \
         patch.object(c.supervisor,'supervise',return_value={'complete':True}) as supervise:
        try:
            c.main()
        except (ValueError, SystemExit):
            assert not supervise.called
            raise
        return supervise.call_count, json.loads((output/'operator/STATE.json').read_text())


def test_setup_blocker_prevents_paid_stages(tmp_path):
    with pytest.raises(ValueError,match='setup blockers'):
        launch(tmp_path,unresolved=['IMD live stream fixture unavailable'])


def test_wrong_control_verdict_blocks_launch(tmp_path):
    with pytest.raises(ValueError,match='expected verdict'):
        launch(tmp_path,expected='fail',actual='pass')


def test_changed_control_evidence_blocks_launch(tmp_path):
    with pytest.raises(ValueError,match='evidence changed'):
        launch(tmp_path,tamper=True)


def test_replay_only_does_not_sneak_into_model_stages(tmp_path):
    calls, state=launch(tmp_path,unresolved=['external tool unavailable'],phases=('rescore',))
    assert calls==1 and state['phases']==['rescore']


def test_negative_control_is_a_required_failure_not_a_setup_failure(tmp_path):
    calls, state=launch(tmp_path,expected='fail',actual='fail')
    assert calls==3 and state['status']=='complete'


def test_setup_error_cannot_satisfy_a_negative_control(tmp_path):
    output=tmp_path/'corrected'
    (output/'operator').mkdir(parents=True)
    proofs=[]
    for role,status,rc,stderr in [('positive','pass',0,''),('negative','fail',1,'ModuleNotFoundError: fixture')]:
        path=tmp_path/(role+'.json')
        path.write_text(json.dumps({'status':status,'exit_code':rc,'stderr_tail':stderr}))
        proofs.append({'bank':'mdanalysis','role':role,'expected':status,
                       'required_diagnostic':'AssertionError: deliberate','result':c.binding(path)})
    (output/'operator/READINESS.json').write_text(json.dumps({'status':'passed',
        'evaluator':{'sha256':'frozen'},'banks':{'mdanalysis':{'status':'passed'}},'checks':proofs}))
    with patch.object(c,'verify_release',return_value={'sha256':'frozen'}):
        with pytest.raises(ValueError,match='deliberate assertion'):
            c.verify_readiness(output,['mdanalysis'],['rescore'],{})
