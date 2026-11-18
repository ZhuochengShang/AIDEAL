from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urldefrag,urlparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import csv,json,hashlib,re,html,time
root=Path('/tmp/aideal-source-doc-recheck-2026-11-17')
callable_types={'py:function','py:method','py:class','py:exception'}
versions={'mdanalysis':'2.11.0','tslearn':'0.10.0','mir_eval':'0.8.2'}
jobs=[];targets=[]
for lib,version in versions.items():
    entries=list(csv.DictReader((root/f'{lib}-official-inventory.csv').open()))
    sources=list(csv.DictReader((root/f'{lib}-source-inventory-crosswalk.csv').open()))
    source_names={x['source_qualified_name']for x in sources}
    for entry in entries:
        if entry['object_type'] not in callable_types and not(entry['object_type']=='py:property' and entry['qualified_name']in source_names):continue
        url,anchor=urldefrag(entry['url'])
        if not urlparse(url).path.endswith('.html'):continue
        item={**entry,'library':lib,'expected_version':version,'page_url':url,'anchor':anchor,'source_qualified_match':entry['qualified_name']in source_names}
        targets.append(item)
    for url in sorted({x['page_url']for x in targets if x['library']==lib}):jobs.append((lib,version,url))
def fetch(job):
    lib,version,url=job;relative=Path(urlparse(url).path.lstrip('/'))
    # Preserve site-relative paths under each library for portable linking.
    destination=root/'raw-docs'/lib/relative
    record={'library':lib,'expected_version':version,'requested_url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'local_path':str(destination.relative_to(root))}
    try:
        with urlopen(Request(url,headers={'User-Agent':'AIDEAL-source-documentation-audit/1.0'}),timeout=30) as response:
            payload=response.read();record.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'),etag=response.headers.get('ETag'),last_modified=response.headers.get('Last-Modified'))
        text=payload.decode('utf-8',errors='replace');match=re.search(r'<title[^>]*>(.*?)</title>',text,re.S|re.I);title=html.unescape(re.sub('<[^>]+>','',match.group(1))).strip()if match else ''
        version_match=bool(re.search(r'(?<![\w.])'+re.escape(version)+r'(?![\w.])',title)) and 'dev' not in title
        record.update(html_title=title,version_check='PASS' if version_match else 'REVIEW_REQUIRED',bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),status='downloaded')
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(payload)
    except Exception as error:record.update(status='ERROR',error=type(error).__name__+': '+str(error),version_check='UNAVAILABLE')
    return record
records=[]
with ThreadPoolExecutor(max_workers=4)as pool:
    future_jobs={pool.submit(fetch,job):job for job in jobs}
    for future in as_completed(future_jobs):
        records.append(future.result())
        if len(records)%40==0:print(json.dumps({'completed':len(records),'total':len(jobs)}),flush=True)
records.sort(key=lambda x:(x['library'],x['requested_url']))
by_url={x['requested_url']:x for x in records}
for target in targets:
    record=by_url[target['page_url']]
    target['local_page']=record.get('local_path','');target['page_sha256']=record.get('sha256','');target['version_check']=record['version_check']
with(root/'RENDERED_DOC_TARGETS.csv').open('w',newline='')as f:
    w=csv.DictWriter(f,fieldnames=list(targets[0]));w.writeheader();w.writerows(targets)
summary={'status':'READY_FOR_DOCUMENT_INPUT_REVIEW'if all(x['version_check']=='PASS'for x in records)else'REQUIRES_REVIEW','scope':'Official HTML pages targeted by inventory functions/methods/classes/exceptions, plus properties with exact saved-source identity. Every HTML URL fetched once; anchors retained separately. Configurations, source trees and releases unchanged.','model_calls':0,'subject_executions':0,'concurrency':4,'target_rows':len(targets),'unique_pages':len(jobs),'libraries':{lib:{'target_rows':sum(x['library']==lib for x in targets),'unique_pages':sum(x['library']==lib for x in records),'version_pass_pages':sum(x['library']==lib and x['version_check']=='PASS'for x in records),'errors':sum(x['library']==lib and x['status']=='ERROR'for x in records),'bytes':sum(x.get('bytes',0)for x in records if x['library']==lib)}for lib in versions},'pages':records,'note':'Rendered HTML is staged as evidence/replacement input material only. A future config/retrieval policy must normalize markup and bind exact API owners/aliases; no treatment has been changed.'}
(root/'RENDERED_DOC_BUNDLE.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k]for k in ['status','target_rows','unique_pages','libraries']}),flush=True)
