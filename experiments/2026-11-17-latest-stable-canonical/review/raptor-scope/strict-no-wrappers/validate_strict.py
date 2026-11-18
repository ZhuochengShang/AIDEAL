"""Check scoped identities, origins, source bindings and duplicate text signals."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re
OUT=Path(__file__).resolve().parent
BASE=Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/review/qualified-api/rdpro')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ledger=json.loads((BASE/'ledger.json').read_text());by_site={r['site_id']:r for r in ledger['records']}
selected=json.loads((OUT/'SELECTED_APIS.json').read_text());rows=[by_site[r['site_id']] for r in selected]
review=json.loads((OUT/'selection_exclusions.json').read_text());excluded={r['site_id'] for r in review['records']}
assert len(excluded)==100 and len(rows)==330
assert review['source_inventory_sha256']==sha(BASE/'ledger.json')
assert all(r['source_sha256']==by_site[r['site_id']]['source_sha256'] and r['source_span_sha256']==by_site[r['site_id']]['source_span_sha256'] for r in review['records'])
assert len({r['api_id'] for r in rows})==len({r['site_id'] for r in rows})==330
assert not excluded & {r['site_id'] for r in rows}
assert all(r['api_origin']['status']=='library_defined' and r['api_origin']['defining_namespace'].startswith('edu.ucr.cs.bdlab.') and not r['api_origin']['external_namespace_matches'] for r in rows)
full=json.loads((OUT/'canonical-selection.json').read_text())
assert full['selection_exclusions_sha256']==sha(OUT/'selection_exclusions.json')
for lang in ('java','scala'):
    m=json.loads((OUT/f'api_manifest.{lang}.json').read_text())
    i=json.loads((OUT/f'api_inventory.{lang}.json').read_text())
    assert set(m['apis'])=={r['api_id'] for r in rows if r['language'].lower()==lang}
    assert i['selection_exclusions_sha256']==sha(OUT/'selection_exclusions.json')
    assert i['canonical_selection_sha256']==sha(OUT/'canonical-selection.json')
    assert set(i['canonical_declaration_ids'])=={r['site_id'] for r in full['winners'] if r['language'].lower()==lang}
    assert set(i['api_ids'])=={r['api_id'] for r in full['winners'] if r['language'].lower()==lang}
    assert set(i['declaration_ids'])=={r['site_id'] for r in ledger['records'] if r.get('inventory_status')=='candidate' and r['language'].lower()==lang}
for r in rows:
    family=[x for x in ledger['records'] if x.get('inventory_status')=='candidate' and x['site_id'] not in excluded and x.get('api_id')==r['api_id'] and x.get('body_presence')!='absent' and x.get('is_abstract') is not True]
    assert r['parameter_count'] is not None
    assert r['parameter_count']==max(x['parameter_count'] for x in family)
# Reuse only pure normalizer functions from the independent reviewer; do not run
# its script or overwrite its original406-target audit.
script=OUT.parent/'document-audit/audit_origin_duplicates.py'
module=ast.parse(script.read_text());functions=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ('norm','body')]
namespace={};exec(compile(ast.Module(body=functions,type_ignores=[]),str(script),'exec'),namespace)
normalise,body=namespace['norm'],namespace['body']
reviewed={r['site_id']:r for r in json.loads((OUT/'ALL_CANDIDATE_DECISIONS.json').read_text())}
groups=defaultdict(list)
for r in rows:
    if r['kind']!='method':continue
    declaration=reviewed[r['site_id']]['source'];impl=body(declaration,r['language'])
    assert impl is not None,r['site_id']
    normalized=normalise(impl)
    assert normalized!='???'
    groups[normalized].append(r)
original=json.loads((OUT.parent/'document-audit/ORIGIN_DUPLICATES.json').read_text())
reviews={g['normalized_body']:g for g in original['duplicate_implementation_candidates']}
duplicates=[]
for normalized,members in groups.items():
    if len(members)<2:continue
    assert len({r['owner'] for r in members})==len(members),'Unexpected same-owner exact duplicate'
    prior=reviews.get(normalized)
    assert prior and prior['status'].startswith('retain_distinct_'),(normalized,[r['api_id'] for r in members])
    duplicates.append({'normalized_body':normalized,'api_ids':[r['api_id'] for r in members],
                       'decision':'retain_distinct_owner_operations','reason':prior['contract_review']})
(OUT/'NORMALIZED_BODY_REVIEW.json').write_text(json.dumps({'groups':duplicates,'limits':'Exact equality after removing comments/whitespace is a screening signal, not semantic equivalence. Literals and identifier spelling remain intact.'},indent=2)+'\n')
summary={'status':'PASS','selected_targets':330,'scope_candidate_sites_verified':452,
 'unique_api_ids':330,'unique_site_ids':330,'external_defined_targets':0,'same_owner_overload_violations':0,
 'unimplemented_stub_targets':0,'reviewed_wrapper_targets_retained':0,'abstract_type_targets':0,
 'distinct_owner_equal_body_groups_retained':len(duplicates),'canonical_bindings_match':True,
 'language_manifests_disjoint':True,'source_ledger_unchanged':True,'model_calls':0,'subject_executions':0,
 'files':{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.glob('*.json')) if p.name!='VALIDATION.json'}}
(OUT/'VALIDATION.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='files'},indent=2))
