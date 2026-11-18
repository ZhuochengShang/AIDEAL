"""Reproduce source-bound strict raster selection without model/library execution."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
import hashlib,json,re,sys
OUT=Path(__file__).resolve().parent
BASE=Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/review/qualified-api/rdpro')
SOURCE=Path('/private/tmp/aideal-readiness-rebuild-2026-11-17/inventory/sources/rdpro')
RELEASE=Path('/tmp/aideal-launch-2026-11-17/recovery-release')
sys.path.insert(0,str(RELEASE/'vendor/aideal_engine/src'))
from aideal.api_canonical_selection import select_canonical_implementations,QUALIFIED_POLICY_VERSION

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def span(row):
    raw=(SOURCE/row['path']).read_bytes()
    assert sha(raw)==row['source_sha256'],row['site_id']
    text=raw.decode('utf-8')
    value=text.encode('utf-16-le')[2*row['start']:2*row['end']].decode('utf-16-le')
    assert sha(value.encode())==row['source_span_sha256'],row['site_id']
    return value

ledger_raw=(BASE/'ledger.json').read_bytes();ledger=json.loads(ledger_raw)
rows=ledger['records'];by_site={r['site_id']:r for r in rows}
previous=json.loads((OUT.parent/'consolidated/SELECTED_APIS.json').read_text())
previous_sites={r['site_id'] for r in previous}
support={r['path'] for r in previous if r['path'].startswith('cg/')}
def in_scope(r):return r['path'].startswith('raptor/src/main/') or r['path'] in support
scoped=[r for r in rows if r.get('inventory_status')=='candidate' and in_scope(r)]
assert len(scoped)==452
source_spans={r['site_id']:span(r) for r in scoped}
manual=json.loads((OUT/'MANUAL_DECISIONS.json').read_text())
prior=json.loads((OUT.parent/'consolidated/CONSOLIDATION.json').read_text())
excluded={}
def exclude(row,reason,evidence,category):
    excluded[row['site_id']]={'site_id':row['site_id'],'source_span_sha256':row['source_span_sha256'],
      'source_sha256':row['source_sha256'],'reason':reason,'evidence':evidence}
    decisions[row['site_id']]={'action':'exclude','category':category,'reason':evidence}
decisions={}
# Manual decisions refer to previous selected sites; they do not accidentally
# exclude a genuine implementation overload with the same owner-qualified ID.
for row in scoped:
    if row['site_id'] in previous_sites and row['api_id'] in manual:
        d=manual[row['api_id']]
        evidence=d['reason'].replace('an equal-arity core overload exists but cannot replace the hash-bound canonical site silently.','the equal-arity core overload is selected after this exclusion.').replace('equal-arity core site requires an explicit canonical selection revision.','the core overload is selected after this source-bound exclusion.')
        exclude(row,'wrapper',evidence,d['category'])
# The earlier16 collapsed source-proven call forms remain excluded.
for proof in prior['proofs']:
    row=by_site[proof['removed_site_id']]
    exclude(row,'wrapper','Single-expression delegation to '+proof['retained_api_id']+' with the source-bound argument mapping in the prior consolidation receipt.','previous_verified_forwarder')
# Check every candidate overload, not only the former winner. ??? means an
# unconditional unimplemented body, and cannot be a runnable success target.
for row in scoped:
    if row['kind']=='method' and re.search(r'=\s*\?\?\?\s*$',source_spans[row['site_id']]):
        exclude(row,'unimplemented','Complete method body is Scala ???, which raises NotImplementedError unconditionally.','unimplemented_stub')
# These are valid public types but not independently constructible runnable
# targets. Constructor-AST modifiers alone do not describe enclosing classes.
abstract_types={'scala:edu.ucr.cs.bdlab.beast.geolite.ITile',
                'scala:edu.ucr.cs.bdlab.raptor.AbstractGeoTiffTile',
                'scala:edu.ucr.cs.bdlab.raptor.AbstractConvolutionTile'}
for row in scoped:
    if row['api_id'] in abstract_types:
        text=(SOURCE/row['path']).read_bytes().decode('utf-8')
        declaration=re.search(r'^\s*abstract\s+class\s+'+re.escape(row['name'])+r'\b[^\n]*',text,re.M)
        assert declaration,row['api_id']
        exclude(row,'abstract_type',
            'Enclosing source declaration is '+declaration.group().strip()+
            '; retain this abstract type as documentation/context, not an independently executable constructor target.',
            'abstract_type_context_only')
additional={
 'Scala:raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/MemoryTileWindow.scala:3725:method:create':'Thin factory forwards existing tile metadata and the supplied array to the MemoryTileWindow constructor.',
 'Scala:raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorJoin.scala:15436:method:raptorJoinLocalJ':'Unselected Java iterator facade calls raptorJoinLocal then asJava; exclude before overload selection.',
 'Scala:raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/RaptorMixin.scala:6715:method:reproject':'Unselected extension-method adapter converts SRID through CRSServer.sridToCRS then forwards to RasterOperationsFocal.reproject.',
 'Scala:raptor/src/main/scala/edu/ucr/cs/bdlab/raptor/ZonalStatistics.scala:9305:method:zonalStatsLocal':'Unselected feature-array adapter extracts geometries then forwards to the core zonalStatsLocal overload.',
 'Java:raptor/src/main/java/edu/ucr/cs/bdlab/raptor/Intersections.java:4570:method:compute':'Lower-arity convenience overload generates sequential IDs and delegates to the core intersections implementation.'}
for site,evidence in additional.items():
    assert site in source_spans;exclude(by_site[site],'wrapper',evidence,'unselected_overload_adapter')
review={'schema':'source_bound_selection_exclusions/v1','review_version':'rdpro-raptor-no-wrappers-2026-11-17',
 'source_inventory_sha256':sha(ledger_raw),'records':[excluded[k] for k in sorted(excluded)]}
dump('selection_exclusions.json',review)
review_hash=sha((OUT/'selection_exclusions.json').read_bytes())
# Re-elect from all source candidate definitions, preserving full-ledger coverage
# and the established owner-aware maximum-arity selection policy.
filtered=[r for r in rows if r.get('inventory_status')=='candidate' and r['site_id'] not in excluded]
selection=select_canonical_implementations(filtered,policy_version=QUALIFIED_POLICY_VERSION)
assert selection['counts']['unresolved_sites']==0
selection['selection_exclusions_sha256']=review_hash
# The qualified reader recomputes full records from the frozen source ledger.
# Its receipt check needs policy, review binding and selected site/language IDs,
# so avoid publishing the same source bodies repeatedly in a 35 MB receipt.
compact={k:selection[k] for k in ('schema_version','policy_version','identity_version',
                                 'policy','counts','selection_resolved','selection_exclusions_sha256')}
compact.update(source_inventory_sha256=sha(ledger_raw),
    winners=[{k:r[k] for k in ('site_id','api_id','language')} for r in selection['winners']],
    full_selection_reconstruction_sha256=sha(json.dumps(selection,sort_keys=True,separators=(',',':')).encode()),
    representation='identity-only receipt; full declarations reconstructed from the bound source ledger')
dump('canonical-selection.json',compact)
kept=[r for r in selection['winners'] if in_scope(r)]
assert not {r['site_id'] for r in kept}&set(excluded)
assert len(kept)==len({r['api_id'] for r in kept})==len({r['site_id'] for r in kept})
for language in ('Java','Scala'):
    names=sorted(r['api_id'] for r in kept if r['language']==language)
    dump('api_manifest.'+language.lower()+'.json',{'schema':2,'identity_mode':'qualified','apis':names,'api_names':names})
    inventory=json.loads((BASE/('api_inventory.'+language.lower()+'.json')).read_text())
    inventory.update(selection_exclusions='selection_exclusions.json',selection_exclusions_sha256=review_hash,
        canonical_selection='canonical-selection.json',canonical_selection_sha256=sha((OUT/'canonical-selection.json').read_bytes()),
        canonical_declaration_ids=[r['site_id'] for r in selection['winners'] if r['language']==language],
        api_ids=[r['api_id'] for r in selection['winners'] if r['language']==language])
    if 'api_names' in inventory:
        inventory['api_names']=[r['name'] for r in selection['winners'] if r['language']==language]
    # Keep complete source bindings/declaration IDs. The operator relocates this
    # relative source-inventory locator to the unchanged hash-bound ledger.
    dump('api_inventory.'+language.lower()+'.json',inventory)
kept_sites={r['site_id'] for r in kept}
by_decision={r['site_id']:r for r in selection['site_decisions']}
audit=[]
for row in scoped:
    outcome=decisions.get(row['site_id'])
    if outcome is None:
        d=by_decision[row['site_id']]
        outcome={'action':'retain' if row['site_id'] in kept_sites else d['status'],
                 'category':'owned_implementation_or_type' if row['site_id'] in kept_sites else d['reason'],
                 'reason':'Custom domain/state implementation or distinct class/type. Same-owner overload policy applies after explicit wrapper and stub exclusions.' if row['site_id'] in kept_sites else d['reason']}
    audit.append({**{k:row[k] for k in ('site_id','api_id','language','path','line','kind','name','owner','signature','parameter_count','source_sha256','source_span_sha256')},
                  **outcome,'source':source_spans[row['site_id']]})
dump('ALL_CANDIDATE_DECISIONS.json',audit)
dump('REMOVED.json',[r for r in audit if r['action']=='exclude'])
dump('SELECTED_APIS.json',[{k:r[k] for k in ('api_id','site_id','language','path','line','kind','signature','parameter_count')} for r in kept])
old_by_api={r['api_id']:r for r in previous}
replacements=[{'api_id':r['api_id'],'old_site_id':old_by_api[r['api_id']]['site_id'],'new_site_id':r['site_id'],'new_signature':r['signature']} for r in kept if r['api_id'] in old_by_api and r['site_id']!=old_by_api[r['api_id']]['site_id']]
summary={'selected_targets':len(kept),'by_language':dict(Counter(r['language'] for r in kept)),
 'by_kind':dict(Counter(r['kind'] for r in kept)),
 'by_language_kind':{l:dict(Counter(r['kind'] for r in kept if r['language']==l)) for l in ('Java','Scala')},
 'before_scope':422,'previous_consolidated':406,'reviewed_candidate_sites':len(scoped),
 'excluded_source_sites':len(excluded),'exclusions_by_reason':dict(Counter(r['reason'] for r in excluded.values())),
 'removed_previous_target_ids':len(set(old_by_api)-{r['api_id'] for r in kept}),
 'replacement_core_overloads':replacements,'source_module_counts':dict(Counter(r['module'] for r in kept)),
 'selection_exclusions_sha256':review_hash,'source_inventory_sha256':sha(ledger_raw),
 'model_calls':0,'subject_executions':0,'scope_limits':['No proof of universal semantic independence.','Distinct owners remain separate even when their short names or small bodies match.','Original source and runtime dependencies are unchanged.','Wrapper exclusion removes evaluation targets, not callable public paths from the installed library.','Canonical receipt covers the full source ledger; language manifests select only the strict raster subset.']}
dump('SUMMARY.json',summary)
print(json.dumps(summary,indent=2))
