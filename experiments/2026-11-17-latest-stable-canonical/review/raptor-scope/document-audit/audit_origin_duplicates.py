from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,re
ROOT=Path('/tmp/aideal-raptor-scope-2026-11-17')
BASE=Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/review/qualified-api/rdpro')
SRC=Path('/private/tmp/aideal-readiness-rebuild-2026-11-17/inventory/sources/rdpro')
selected=json.loads((ROOT/'consolidated/SELECTED_APIS.json').read_text())
ledger=json.loads((BASE/'ledger.json').read_text())
records={r['site_id']:r for r in ledger['records']}

def norm(s):
    # Remove comments/whitespace only outside literals, retaining exact literals.
    out=[];i=0
    while i<len(s):
        if s.startswith('//',i):
            i=s.find('\n',i);i=len(s) if i<0 else i;continue
        if s.startswith('/*',i):
            end=s.find('*/',i+2);i=len(s) if end<0 else end+2;continue
        if s.startswith('"""',i):
            end=s.find('"""',i+3);end=len(s)-3 if end<0 else end;out.append(s[i:end+3]);i=end+3;continue
        if s[i] in ('"',"'"):
            mark=s[i];j=i+1
            while j<len(s):
                if s[j]=='\\':j+=2;continue
                if s[j]==mark:j+=1;break
                j+=1
            out.append(s[i:j]);i=j;continue
        if not s[i].isspace():out.append(s[i])
        i+=1
    return ''.join(out)

def body(span,lang):
    # Source spans are compiler-defined declaration windows. Seek top-level body
    # marker after balanced formal parameters/type parameters, ignoring literals.
    depth=0;quote=None;i=0
    while i<len(span):
        c=span[i]
        if quote:
            if c=='\\':i+=2;continue
            if c==quote:quote=None
        elif c in ('"',"'"):quote=c
        elif c in '([':depth+=1
        elif c in ')]':depth-=1
        elif depth==0 and (c=='{' or lang=='Scala' and c=='='):
            return span[i+1:-1] if c=='{' and span.rstrip().endswith('}') else span[i+1:]
        i+=1
    return None

rows=[];groups=defaultdict(list);declarations=defaultdict(list)
for s in selected:
    r=records[s['site_id']];raw=(SRC/r['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['source_sha256']
    span=raw.decode().encode('utf-16-le')[2*r['start']:2*r['end']].decode('utf-16-le')
    assert hashlib.sha256(span.encode()).hexdigest()==r['source_span_sha256']
    impl=body(span,r['language'])
    row={'api_id':r['api_id'],'site_id':r['site_id'],'owner':r['owner'],'name':r['name'],'kind':r['kind'],
      'path':r['path'],'line':r['line'],'signature':r['signature'],
      'api_origin_status':r['api_origin']['status'],'api_origin_reason':r['api_origin']['reason'],
      'defining_namespace':r['api_origin']['defining_namespace'],
      'external_namespace_matches':r['api_origin']['external_namespace_matches'],
      'overrides_framework_or_parent':r['kind']=='method' and bool(re.match(r'\s*(override\b|@Override\b)',span)),
      'declaration':span,'body_normalized':norm(impl) if impl is not None else None}
    rows.append(row)
    declarations[r['api_id'].split(':',1)[1]].append(row)
    if impl is not None and r['kind'] in ('method','function'):
        groups[norm(impl)].append(row)

duplicates=[]
for impl,group in groups.items():
    if len(group)<2:continue
    duplicates.append({'normalized_body':impl,'count':len(group),
      'same_owner':len(set(r['owner'] for r in group))==1,
      'same_name':len(set(r['name'] for r in group))==1,
      'members':[{k:v for k,v in r.items() if k not in ('body_normalized','declaration')} for r in group],
      'declarations':[r['declaration'] for r in group],
      'status':'candidate_only_distinct_owner_or_contract_requires_review'})
result={'scope':406,'all_frozen_source_file_and_span_hashes_match':True,
  'unique_api_ids':len(set(r['api_id'] for r in rows)),'unique_site_ids':len(set(r['site_id'] for r in rows)),
  'origin_status_counts':dict(Counter(r['api_origin_status'] for r in rows)),
  'unqualified_external_origins':[r for r in rows if r['external_namespace_matches'] or not r['defining_namespace'].startswith('edu.ucr.cs.bdlab.')],
  'same_qualified_name_multiple_language_targets':[[r['api_id'] for r in g] for g in declarations.values() if len(g)>1],
  'override_definition_count':sum(r['overrides_framework_or_parent'] for r in rows),
  'duplicate_implementation_candidates':duplicates,
  'policy':'Same body text is only a review signal. Preserve distinct owner operations and library-owned implementations of framework interfaces. Imported or inherited-only members are not eligible targets.',
  'rows':rows}
(ROOT/'document-audit/ORIGIN_DUPLICATES.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','duplicate_implementation_candidates')},indent=2))
for g in duplicates:
 print('\nDUP',g['normalized_body'][:450],[(r['api_id'],r['path'],r['line']) for r in g['members']])
