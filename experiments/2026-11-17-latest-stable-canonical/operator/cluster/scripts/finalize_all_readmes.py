from pathlib import Path
import json,hashlib,subprocess,sys
root=Path(sys.argv[1]).resolve();plan=json.loads((root/'plan.json').read_text());post=plan['protocol']['postprocess']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
script=root/'scripts/finalize_library_readmes.py'
assert sha(script)==post['library_finalizer_sha256']
results=[]
for group in post['groups']:
 directory=Path(group['directory']);assert sha(directory/'readme_installation_intent.json')==group['intent_sha256']
 done=subprocess.run([sys.executable,str(script),str(directory)],capture_output=True,text=True)
 log=directory/'finalize_console.log';log.write_text(done.stdout+'\n'+done.stderr)
 receipt=directory/'installations/completion.json'
 results.append({'library':group['library'],'returncode':done.returncode,'installed':done.returncode==0 and receipt.is_file(),'receipt':str(receipt) if receipt.is_file() else None})
result={'status':'installed' if all(r['installed'] for r in results) else 'pending_or_failed','libraries':results,'github_push':'not_performed; publish verified resulting commits separately'}
(root/'INSTALLATION_STATUS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
raise SystemExit(0 if result['status']=='installed' else 2)
