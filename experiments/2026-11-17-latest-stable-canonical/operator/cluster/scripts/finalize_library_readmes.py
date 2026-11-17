#!/usr/bin/env python3
"""Install the completed documents sequentially on the same condition refs.

The saved intent pins the initial refs. The second edit derives expected refs
only from the first verified installation receipt. No active checkout changes.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
intent_path=root/'readme_installation_intent.json'
intent=json.loads(intent_path.read_text())
plan_path=root/'plan.json'
if plan_path.is_file():
 expected=json.loads(plan_path.read_text())['protocol']['postprocess']['installation_intent_sha256']
 if hashlib.sha256(intent_path.read_bytes()).hexdigest()!=expected:
  raise ValueError('Frozen README installation intent changed')
release=Path(intent['release'])
module_path=release/'scripts/install_generated_readme.py'
if hashlib.sha256(module_path.read_bytes()).hexdigest()!=intent['installer_sha256']:
 raise ValueError('Pinned README installer changed')
spec=importlib.util.spec_from_file_location('pinned_installer',module_path)
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
missing=[r['completion'] for r in intent['documents'] if not Path(r['completion']).is_file()]
if missing:
 print(json.dumps({'status':'pending_authoring','missing':missing}));raise SystemExit(0)
branches=intent['branches']
receipts=[]
for row in intent['documents']:
 manifest={k:row[k] for k in ('readme','completion','destination')}
 manifest.update(repository=intent['repository'],branches=branches)
 path=root/'installations'/row['language']/'manifest.json';path.parent.mkdir(parents=True,exist_ok=True)
 content=json.dumps(manifest,indent=2)+'\n'
 if path.exists() and path.read_text()!=content:raise ValueError('Installation manifest changed')
 if not path.exists():path.write_text(content)
 receipt=path.with_name('installation.json')
 if receipt.exists():
  result=json.loads(receipt.read_text())
  expected={'manifest_sha256':installer.sha(path.read_bytes()),
            'readme_sha256':installer.sha(Path(manifest['readme']).read_bytes()),
            'completion_sha256':installer.sha(Path(manifest['completion']).read_bytes()),
            'repository':str(Path(manifest['repository']).resolve()),
            'destination':manifest['destination'],
            'original':installer.original_identity(Path(manifest['repository']))}
  if result.get('status')!='installed' or result.get('identity')!=expected:
   raise ValueError('Saved installation evidence changed')
  if {ref.removeprefix('refs/heads/'):r['old'] for ref,r in result['branches'].items()}!=branches:
   raise ValueError('Saved installation parent commits changed')
 else:
  result=installer.install(path,receipt)
 branches={ref.removeprefix('refs/heads/'):value['new'] for ref,value in result['branches'].items()}
 receipts.append(str(receipt))
# The final refs must contain both exact documents, including on resume.
for branch,commit in branches.items():
 if installer.git(intent['repository'],'rev-parse','refs/heads/'+branch).decode().strip()!=commit:
  raise ValueError('Final branch changed after installation')
 for row in intent['documents']:
  if installer.git(intent['repository'],'show',commit+':'+row['destination'])!=Path(row['readme']).read_bytes():
   raise ValueError('Final branch document differs from authored output')
final={'status' :'installed_all_documents','branches':branches,'receipts':receipts,'intent_sha256':hashlib.sha256(intent_path.read_bytes()).hexdigest()}
path=root/'installations/completion.json';data=json.dumps(final,indent=2)+'\n'
if path.exists() and path.read_text()!=data:raise ValueError('Installation completion changed')
if not path.exists():path.write_text(data)
print(json.dumps(final))
