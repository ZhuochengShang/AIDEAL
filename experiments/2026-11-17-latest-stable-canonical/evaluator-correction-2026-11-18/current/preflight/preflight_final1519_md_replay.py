import hashlib,importlib.util,json,sys,time
from pathlib import Path
from unittest.mock import patch
RELEASE=Path('/home/zshan011/apps/aideal/releases/2026-11-18-corrected-r0-d8ba3815cf95')
release_manifest=json.loads((RELEASE/'EVALUATOR_RELEASE.json').read_text())
for rel,sha in release_manifest['files'].items():
 if hashlib.sha256((RELEASE/rel).read_bytes()).hexdigest()!=sha:raise ValueError('Release drift: '+rel)
sys.path[:0]=[str(RELEASE),str(RELEASE/'vendor/aideal_engine/src')]
spec=importlib.util.spec_from_file_location('final_replay',RELEASE/'scripts/rescore_native_programs.py')
replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
from workflow.runtime_profile import load_runtime_profile,verify_runtime_profile,_cached_digest
STUDY=Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
OUT=STUDY/'evaluator-correction-2026-11-18/current/preflight/runtime-controls/mdanalysis/final1519-d8ba3815cf95'
PROFILE=STUDY/'evaluator-correction-2026-11-18/runtime-mdanalysis-final-2026-11-18/runtime_profile.json'
_cached_digest.cache_clear()
t=time.monotonic();profile=load_runtime_profile(PROFILE);cold=time.monotonic()-t
warm=[]
for _ in range(3):
 t=time.monotonic();verify_runtime_profile(profile);warm.append(time.monotonic()-t)
print(json.dumps({'profile_cold_s':cold,'profile_warm_verification_s':warm,'file_bindings':len(profile['installed_file_bindings'])}),flush=True)
source=STUDY/'qualified/runs/original/mdanalysis/mdanalysis/result.json'
api='python:MDAnalysis.lib.distances.calc_bonds'
code='''from MDAnalysis.lib.distances import calc_bonds
import numpy as np
first = atoms[:2].positions.copy()
second = atoms[1:3].positions.copy()
observed = calc_bonds(first, second, backend="serial")
expected = np.linalg.norm(first.astype(float) - second.astype(float), axis=1)
assert np.allclose(observed, expected + EXPECTED_SHIFT, rtol=1e-6, atol=1e-6)
print(f"__CHECK__ python:MDAnalysis.lib.distances.calc_bonds {observed.tolist()}")
'''
cfg=replay.load_source(str(source))[2]
before=replay.frozen_input_state(cfg)
rows=[]
with patch('aideal.llm.invoke_text',side_effect=AssertionError('No model calls in offline controls')):
 for variant,shift in [('positive','0.0'),('negative','1.0')]:
  start=time.monotonic()
  result=replay.run_program_case(source,api,OUT/variant,code_override=code.replace('EXPECTED_SHIFT',shift),runtime_profile=PROFILE)
  row={'variant':variant,'expected':'pass'if variant=='positive'else'fail','observed':result['status'],'error':result.get('error'),'exit_code':result['exit_code'],'execution_s':result['wall_s'],'total_case_s':time.monotonic()-start,'result':replay.binding(OUT/variant/'result.json')}
  row['passed']=row['expected']==row['observed'];rows.append(row)
  print(json.dumps(row),flush=True)
after=replay.frozen_input_state(cfg)
summary={'schema':1,'kind':'offline_positive_negative_runtime_controls','not_an_experiment_result':True,'model_calls':0,'release_manifest':replay.binding(RELEASE/'EVALUATOR_RELEASE.json'),'runtime_profile':replay.binding(PROFILE),'profile_load_cold_s':cold,'profile_verify_warm_s':warm,'checks':rows,'source_inputs_unchanged':before==after,'passed':before==after and all(r['passed']for r in rows)}
replay.atomic(OUT/'FINAL_REPLAY_CONTROLS.json',summary)
print(json.dumps({'passed':summary['passed'],'summary':str(OUT/'FINAL_REPLAY_CONTROLS.json')}),flush=True)
