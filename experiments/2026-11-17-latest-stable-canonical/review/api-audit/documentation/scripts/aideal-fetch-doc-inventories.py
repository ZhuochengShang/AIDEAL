from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,re

root=Path('/tmp/aideal-source-doc-recheck-2026-11-17');root.mkdir(exist_ok=True)
requests=[
 ('mdanalysis-2.11.0-index','https://docs.mdanalysis.org/2.11.0/index.html'),
 ('mdanalysis-2.11.0-objects','https://docs.mdanalysis.org/2.11.0/objects.inv'),
 ('tslearn-stable-index','https://tslearn.readthedocs.io/en/stable/'),
 ('tslearn-stable-objects','https://tslearn.readthedocs.io/en/stable/objects.inv'),
 ('tslearn-0.10.0-index','https://tslearn.readthedocs.io/en/0.10.0/'),
 ('tslearn-0.10.0-objects','https://tslearn.readthedocs.io/en/0.10.0/objects.inv'),
 ('mir_eval-stable-index','https://mir-eval.readthedocs.io/stable/'),
 ('mir_eval-stable-objects','https://mir-eval.readthedocs.io/stable/objects.inv'),
 ('mir_eval-0.8.2-index','https://mir-eval.readthedocs.io/0.8.2/'),
 ('mir_eval-0.8.2-objects','https://mir-eval.readthedocs.io/0.8.2/objects.inv')]
def get(item):
 name,url=item; record={'id':name,'requested_url':url,'observed_at':datetime.now(timezone.utc).isoformat()}
 try:
  with urlopen(Request(url,headers={'User-Agent':'AIDEAL-source-documentation-audit/1.0'}),timeout=25) as response:
   payload=response.read();record.update(status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),etag=response.headers.get('ETag'),last_modified=response.headers.get('Last-Modified'))
  suffix='.inv' if 'objects' in name else '.html';dest=root/'official-downloads'/(name+suffix);dest.parent.mkdir(exist_ok=True);dest.write_bytes(payload);record['local_path']=str(dest)
  if suffix=='.html':
   text=payload.decode(errors='replace');match=re.search(r'<title[^>]*>(.*?)</title>',text,re.S|re.I);record['html_title']=match.group(1).strip() if match else None
 except Exception as error:record.update(status='ERROR',error=type(error).__name__+': '+str(error))
 return record
with ThreadPoolExecutor(max_workers=5) as pool:records=list(pool.map(get,requests))
(root/'OFFICIAL_DOWNLOADS.json').write_text(json.dumps(records,indent=2)+'\n')
for record in records:print(json.dumps({k:record[k] for k in ['id','status','final_url','bytes','html_title','error'] if k in record}))
