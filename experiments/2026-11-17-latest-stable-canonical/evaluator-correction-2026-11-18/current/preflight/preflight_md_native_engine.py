"""Real native execution with a stubbed model; never an experiment score."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
from unittest.mock import patch

p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--bank',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
manifest=json.loads((args.engine/'EVALUATOR_RELEASE.json').read_text())
for rel,sha in manifest['files'].items():
 assert hashlib.sha256((args.engine/rel).read_bytes()).hexdigest()==sha,rel
assert(args.bank/'continuation.json').is_file(),'Wait for prepared configs'
sys.path[:0]=[str(args.engine),str(args.engine/'vendor/aideal_engine/src')]
from aideal.config import load_config
from aideal.doc_check_comprehension import comprehension_check
from aideal.llm import reset_usage

API='python:MDAnalysis.lib.distances.calc_bonds'
CALC='''from MDAnalysis.lib.distances import calc_bonds
import numpy as np
first = atoms[:2].positions.copy()
second = atoms[1:3].positions.copy()
observed = calc_bonds(first, second, backend="serial")
expected = np.linalg.norm(first.astype(float) - second.astype(float), axis=1)
assert np.allclose(observed, expected + EXPECTED_SHIFT, rtol=1e-6, atol=1e-6)
print(f"__CHECK__ python:MDAnalysis.lib.distances.calc_bonds {observed.tolist()}")
'''
IMD_API='python:MDAnalysis.coordinates.IMD.IMDReader'
IMD='''from MDAnalysis.coordinates.IMD import IMDReader
assert imd_url.startswith('imd://127.0.0.1:')
with IMDReader(imd_url,n_atoms=imd_n_atoms) as reader:
 count=1
 while True:
  try:next(reader);count+=1
  except (StopIteration,EOFError):break
assert count == EXPECTED_COUNT
print(f"__CHECK__ python:MDAnalysis.coordinates.IMD.IMDReader {count}")
'''
def binding(path):
 path=Path(path).resolve();return{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
summary={'schema':1,'kind':'native_engine_with_mocked_model_and_real_execution','not_an_experiment_result':True,'paid_model_calls':0,'driver':binding(__file__),'release':binding(args.engine/'EVALUATOR_RELEASE.json'),'prepared_identity':binding(args.bank/'continuation.json'),'checks':[]}
args.output.mkdir(parents=True,exist_ok=False)
for arm in ['original','generated_d1']:
 config=args.bank/arm/'configs/continuation.yaml'
 cases=[('calc_positive',API,CALC.replace('EXPECTED_SHIFT','0.0'),'pass'),('calc_negative',API,CALC.replace('EXPECTED_SHIFT','1.0'),'fail')]
 if arm=='original':cases.extend([('imd_positive',IMD_API,IMD.replace('EXPECTED_COUNT','5'),'pass'),('imd_negative',IMD_API,IMD.replace('EXPECTED_COUNT','6'),'fail')])
 for name,api,code,expected in cases:
  directory=args.output/arm/name;directory.mkdir(parents=True)
  cfg=load_config(config)
  cfg.comprehension['execute']['work_dir']=str(directory/'execution')
  cfg.comprehension['execute']['output_dir']=str(directory/'output')
  cfg.error_log=directory/'error_log.jsonl';cfg.notes_to_self=directory/'notes.json'
  cfg.raw.setdefault('files',{})['error_log']=str(cfg.error_log)
  calls=[]
  def mock_model(model,system,user):
   calls.append({'system':system,'user':user,'provider_stubbed':True})
   return code
  reset_usage();started=time.monotonic()
  with patch('aideal.llm.invoke_text',side_effect=mock_model):
   result=comprehension_check(cfg,doc_source='original'if arm=='original'else'aideal',execute=True,show_code=True,class_context=False,max_fix_rounds=0,resume=False,doc_scope='relevant',sample=None,manifest=str(args.bank/arm/'inputs/pending_manifest.json'),api=api)
  result['not_an_experiment_result']=True;result['provider_was_mocked']=True
  (directory/'native_result.json').write_text(json.dumps(result,indent=2)+'\n')
  (directory/'mock_provider_prompts.json').write_text(json.dumps(calls,indent=2)+'\n')
  row=result.get('details',{}).get(api,{})
  observed=row.get('status')if isinstance(row,dict)else row
  check={'arm':arm,'name':name,'api':api,'expected_status':expected,'observed_status':observed,'mock_requests':len(calls),'paid_model_calls':0,'passed':observed==expected and len(calls)==1,'elapsed_s':time.monotonic()-started,'source_config':binding(config),'result':binding(directory/'native_result.json'),'prompts':binding(directory/'mock_provider_prompts.json')}
  summary['checks'].append(check)
  (args.output/'NATIVE_ENGINE_CONTROLS.json').write_text(json.dumps(summary,indent=2)+'\n')
  print(json.dumps(check),flush=True)
summary['passed']=all(r['passed']for r in summary['checks'])
(args.output/'NATIVE_ENGINE_CONTROLS.json').write_text(json.dumps(summary,indent=2)+'\n')
raise SystemExit(0 if summary['passed']else 2)
