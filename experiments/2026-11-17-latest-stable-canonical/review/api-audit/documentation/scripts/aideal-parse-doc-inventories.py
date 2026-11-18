from pathlib import Path
from urllib.parse import urljoin
from collections import Counter,defaultdict
import csv,json,re,zlib,hashlib
out=Path('/tmp/aideal-source-doc-recheck-2026-11-17')
review=Path('/tmp/aideal-current-review-package-2026-11-17/review')
source_html=(review/'API_SELECTION.html').read_text()
sources,_=json.JSONDecoder().raw_decode(source_html.split('const records=',1)[1])
downloads=json.loads((out/'OFFICIAL_DOWNLOADS.json').read_text())
selected_scopes={'mdanalysis':'mdanalysis-2.11.0-objects','tslearn':'tslearn-stable-objects','mir_eval':'mir_eval-stable-objects'}
callable_types={'py:function','py:method','py:class','py:exception'}
reports=[]
for lib,artifact in selected_scopes.items():
    receipt=next(x for x in downloads if x['id']==artifact)
    payload=Path(receipt['local_path']).read_bytes();headers=payload.split(b'\n',4)
    assert headers[0]==b'# Sphinx inventory version 2'
    text=zlib.decompress(headers[4]).decode()
    entries=[];continuations=[]
    for line in text.splitlines():
        match=re.match(r'^(.*?)\s+(\S+:\S+)\s+(-?\d+)\s+(\S+)\s+(.*)$',line)
        if not match:
            if line.strip():continuations.append(line)
            continue
        name,kind,priority,uri,display=match.groups()
        if uri.endswith('$'):uri=uri[:-1]+name
        entries.append({'qualified_name':name,'object_type':kind,'priority':priority,'url':urljoin(receipt['final_url'],uri),'display_name':name if display=='-' else display,'private_name_component':any(x.startswith('_') for x in name.split('.'))})
    with (out/f'{lib}-official-inventory.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
    typed=[x for x in entries if x['object_type'].startswith('py:')]
    by_exact=defaultdict(list);by_bare=defaultdict(list)
    for e in typed:by_exact[e['qualified_name']].append(e);by_bare[e['qualified_name'].rsplit('.',1)[-1]].append(e)
    bank=(review/'banks'/lib/'TASK_BANK.js').read_text();bankrows=json.loads(bank.split('] = ',1)[1].strip().removesuffix(';'))
    mentions={x['api']:x['original_documentation_code_mention'] for x in bankrows}
    cross=[]
    for src in sources:
        if src['library']!=lib:continue
        rel=src['path'].removeprefix('package/').removesuffix('.py').replace('/','.')
        if rel.endswith('.__init__'):rel=rel.removesuffix('.__init__')
        qual='.'.join(x for x in [rel,src['owner'],src['name']] if x)
        exact=by_exact.get(qual,[]);bare=by_bare.get(src['name'],[])
        cross.append({'name':src['name'],'source_qualified_name':qual,'source_owner':src['owner'],'source_path':src['path'],'source_line':src['line'],'source_kind':src['site_id'].split(':')[-2],'selection_status':src['status'],'selection_reason':src['reason'],'exact_qualified_match':bool(exact),'exact_object_types':' | '.join(x['object_type']for x in exact),'exact_urls':' | '.join(x['url']for x in exact),'bare_name_match':bool(bare),'bare_name_qualified_candidates':' | '.join(sorted(set(x['qualified_name']for x in bare))),'bare_name_urls':' | '.join(sorted(set(x['url']for x in bare))),'selected_name_code_mention':mentions.get(src['name'],'not_selected')})
    with (out/f'{lib}-source-inventory-crosswalk.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(cross[0]));w.writeheader();w.writerows(cross)
    picked=[x for x in cross if x['selection_status']=='selected']
    counts=lambda rows:{'sites':len(rows),'distinct_simple_names':len({x['name']for x in rows}),'exact_qualified_inventory_matches':sum(x['exact_qualified_match']for x in rows),'bare_name_inventory_matches':sum(x['bare_name_match']for x in rows),'bare_only_matches':sum(x['bare_name_match']and not x['exact_qualified_match']for x in rows),'no_lexical_inventory_match':sum(not x['bare_name_match']for x in rows)}
    reports.append({'library':lib,'inventory_url':receipt['final_url'],'inventory_sha256':receipt['sha256'],'inventory_headers':[x.decode()for x in headers[:4]],'inventory_entries':len(entries),'python_object_rows':len(typed),'python_distinct_qualified_names':len({x['qualified_name']for x in typed}),'python_simple_names':len({x['qualified_name'].rsplit('.',1)[-1]for x in typed}),'type_counts':dict(sorted(Counter(x['object_type']for x in entries).items())),'callable_rows_including_classes_exceptions':sum(x['object_type']in callable_types for x in entries),'private_component_python_rows':sum(x['private_name_component']for x in typed),'inventory_continuation_lines':continuations,'all_saved_source_rows':counts(cross),'selected_source_rows':counts(picked),'selected_code_mentions':sum(bool(x['selected_name_code_mention'])for x in picked),'selected_documentation_inventory_present_but_no_code_mention':sum(x['bare_name_match']and not x['selected_name_code_mention']for x in picked),'examples_documented_but_code_mention_false':[x for x in picked if x['exact_qualified_match']and not x['selected_name_code_mention']][:8],'examples_bare_only':[x for x in picked if x['bare_name_match']and not x['exact_qualified_match']][:5]})
result={'observed_at':downloads[0]['observed_at'],'method':'Read official Sphinx v2 inventories; zlib-decompress metadata only. Crosswalk lexical qualified identities and simple names to saved source rows. No imports, builds, model calls, or subject executions.','source_rows_artifact':str(review/'API_SELECTION.html'),'source_rows_artifact_sha256':hashlib.sha256((review/'API_SELECTION.html').read_bytes()).hexdigest(),'limitations':['Inventory objects include aliases, inherited members, private names, attributes and modules; counts are not a complete public callable API count.','Exact qualified source path may differ from documented public re-export path. Bare-name matching cannot certify owner/signature or overload identity.','Inventory presence means a documentation target exists, not adequate examples, correct behavior, or complete subject coverage.','Malformed/non-record continuation lines in MDAnalysis inventory are retained as evidence and not counted as additional object records.','Stable documentation URLs can advance; downloaded bytes/version headers are frozen by SHA256 and timestamp.'], 'libraries':reports}
for report in reports:
    entries=list(csv.DictReader((out/f'{report["library"]}-official-inventory.csv').open()))
    callable_entries=[entry for entry in entries if entry['object_type'] in callable_types]
    report['callable_distinct_qualified_names']=len({entry['qualified_name']for entry in callable_entries})
    report['callable_distinct_simple_names']=len({entry['qualified_name'].rsplit('.',1)[-1]for entry in callable_entries})
(out/'OFFICIAL_INVENTORY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
for report in reports:print(json.dumps({k:report[k]for k in ['library','type_counts','all_saved_source_rows','selected_source_rows','selected_code_mentions','selected_documentation_inventory_present_but_no_code_mention']}))
