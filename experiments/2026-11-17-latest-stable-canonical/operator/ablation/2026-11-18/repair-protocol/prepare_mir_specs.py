"""Freeze two small runtime-verified condition specs without model calls."""
from pathlib import Path
import ast,hashlib,json,shlex,subprocess,sys
root=Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
op=root/'operator/ablation/2026-11-18/repair-protocol'
def bind(p):
 p=Path(p).resolve(strict=True)
 return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def once(p,v):
 content=json.dumps(v,indent=2)+'\n'
 if p.exists():assert p.read_text()==content,p
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
prior=json.loads((root/'operator/ablation/2026-11-18/specs/mir_eval.json').read_text())
original=root/'sources/mir_eval';hinted=root/'runtime-conditions/native-hints-2026-11-18/mir_eval/error-hints-only'
python='/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/bin/python'
base='Reference intervals and pitches have different lengths.'
action=' [AIDEAL fix:interval_pitch_length_match] Ensure the number of rows in the interval array matches the number of elements in the pitch array.'
# Only the previously validated message line may differ in the Python package.
orig={str(p.relative_to(original)):p.read_bytes() for p in (original/'mir_eval').rglob('*.py')}
mods={str(p.relative_to(hinted)):p.read_bytes() for p in (hinted/'mir_eval').rglob('*.py')}
assert orig.keys()==mods.keys()
assert [n for n in orig if orig[n]!=mods[n]]==['mir_eval/transcription.py']
candidate_ast=ast.parse(mods['mir_eval/transcription.py']); matches=[n for n in ast.walk(candidate_ast) if isinstance(n,ast.Constant) and n.value==base+action]
assert len(matches)==1
matches[0].value=base
assert ast.dump(candidate_ast)==ast.dump(ast.parse(orig['mir_eval/transcription.py']))
for condition,source,message in [('original',original,base),('error_hints',hinted,base+action)]:
 files=[bind(p) for p in sorted((source/'mir_eval').rglob('*.py'))]
 runtime=op/f'runtime.{condition}.json'
 once(runtime,{'condition':condition,'source':str(source),'files':files,'trigger_message':message})
 command=[python,str(op/'mir_runtime.py'),'--binding',str(runtime)]
 result=subprocess.run(command+['--smoke'],capture_output=True,text=True,check=True)
 receipt=op/f'runtime.{condition}.smoke.json';once(receipt,json.loads(result.stdout))
 spec={k:prior[k] for k in ['release','release_binding','release_binding_sha256']}
 spec.update(schema=1,condition=condition,library='mir_eval',trials=1,api_ids=['python:mir_eval.transcription.validate'],
  output=str(root/'ablation-2026-11-18/repair-pilot/mir_eval'/condition),
  prepared_config=bind(root/'qualified/runs/original/mir_eval/mir_eval/configs/aideal.yaml'),
  engine_helper=bind(root/'operator/ablation/2026-11-18/generated_readme_r0.py'),
  runtime={'command':'env -u PYTHONPATH -u PYTHONHOME MPLBACKEND=Agg OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONHASHSEED=0 '+shlex.join(command)+' "{test_file}"',
   'status':'verified','files':[bind(op/'mir_runtime.py'),bind(runtime),*files],
   'receipt':bind(receipt),'aliases_installed':False,'native_hints_installed':condition=='error_hints'})
 if condition=='error_hints':spec['runtime'].update(native_hint_format='single-line-exception',native_hint_messages=[message])
 once(op/'specs'/f'mir_eval.{condition}.json',spec)
 print(json.dumps({'condition':condition,'status':'runtime_verified','source_files':len(files),'spec':str(op/'specs'/f'mir_eval.{condition}.json')}))
