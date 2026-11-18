"""Retain original documentation bytes; correct only source identity retrieval.

This creates a new scoped manifest, never rewrites the frozen full-Beast corpus.
Receiver/source proofs are review metadata, not text added to audience prompts.
"""
from pathlib import Path
from collections import defaultdict
from types import SimpleNamespace
import copy, hashlib, json, re, shutil, sys

ROOT = Path('/tmp/aideal-raptor-scope-2026-11-17')
STUDY = Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical')
BASE = STUDY / 'review/qualified-api/rdpro/original-docs'
OUT = ROOT / 'original-docs'
ENGINE = Path('/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src')
OUT.mkdir(exist_ok=True)
sha = lambda raw: hashlib.sha256(raw).hexdigest()
base_bytes = (BASE/'manifest.json').read_bytes()
base = json.loads(base_bytes)
audit = json.loads((ROOT/'document-audit/COUNTS.json').read_text())
version_check = json.loads((ROOT/'github-docs/VERSION_COMPARISON.json').read_text())
assert len(version_check) == 16 and all(r['same_bytes_as_linked_branch'] for r in version_check)
proofs = json.loads((ROOT/'consolidated/CONSOLIDATION.json').read_text())['proofs']
forward = {r['removed_api_id']:r for r in proofs}
selected = set()
for language in ('scala','java'):
    selected.update(json.loads((ROOT/f'consolidated/api_manifest.{language}.json').read_text())['apis'])
assert len(selected)==406
rows = [r for r in audit['rows'] if r['group']=='raster' and (r['api_id'] in selected or r['api_id'] in forward)]
assert len(rows)==19
manifest = {k: copy.deepcopy(v) for k,v in base.items() if k not in ('targets','documents')}
manifest['scope'] = ('Raster/Raptor source subset after 16 source-verified forwarding consolidations. '
    'Original published bytes are preserved. Reviewed receiver-to-owner mappings and verified forwarding '
    'proofs identify relevant original excerpts; they add no generated guidance. Documentation coverage '
    'means a reviewed interface or consolidated operation has an original example or description, not '
    'that examples compile, every overload is documented, or other targets have no prose anywhere.')
manifest['mapping_provenance'] = {'method':'reviewed_receiver_resolution_and_verified_forwarding',
    'frozen_base_manifest_sha256':sha(base_bytes),'linked_doc_commit':audit['doc_branch_commit'],
    'linked_16_markdown_files_byte_identical_to_pinned_source':True,
    'consolidation_sha256':sha((ROOT/'consolidated/CONSOLIDATION.json').read_bytes()),
    'changes_to_original_text':False, 'original_source_checks_executed':False}
# Preserve all 21 original document payloads for complete corpus provenance/full-doc mode.
manifest['documents'] = copy.deepcopy(base['documents'])
for d in manifest['documents']:
    src = BASE/d['path']; dst=OUT/d['path']; dst.parent.mkdir(parents=True,exist_ok=True)
    raw=src.read_bytes(); assert sha(raw)==d['sha256']; dst.write_bytes(raw)
    d.pop('source_path',None)
by_doc={d['id']:d for d in manifest['documents']}
manifest['targets']={}
for api in sorted(selected):
    prev=base['targets'][api]
    if prev['status']=='documented':
        manifest['targets'][api]=copy.deepcopy(prev)
    else:
        manifest['targets'][api]={'status':'undocumented','excerpts':[],
          'reason':'No reviewed defining-interface or verified consolidated-operation match was found in the pinned original corpus. This disposition is a retrieval-coverage result, not a claim that the source lacks comments or that no related prose exists.'}

def section_bounds(doc, line):
    """Whole original heading section containing the evidence, including fences."""
    text=(ROOT/'github-docs'/doc).read_text(); lines=text.splitlines(keepends=True)
    heads=[]
    for n,s in enumerate(lines,1):
        m=re.match(r'^(#{1,6})\s',s)
        if m:heads.append((n,len(m[1])))
    start,depth=max((n,level) for n,level in heads if n<=line)
    end=next((n-1 for n,level in heads if n>start and level<=depth),len(lines))
    return start,end

def excerpt(doc,start,end):
    doc_id='doc/'+doc; raw=(ROOT/'github-docs'/doc).read_bytes()
    assert sha(raw)==by_doc[doc_id]['sha256']
    body=b''.join(raw.splitlines(keepends=True)[start-1:end])
    path=f'excerpts/{Path(doc).stem}-L{start}-L{end}.md'
    (OUT/path).parent.mkdir(exist_ok=True); (OUT/path).write_bytes(body)
    return {'path':path,'sha256':sha(body),'document_id':doc_id,
      'origin_url':by_doc[doc_id]['origin_url'],'anchor':f'lines-{start}:{end}',
      'original_line_start':start,'original_line_end':end,'selection':'unaltered_contiguous_original_section'}

mapped=defaultdict(list)
for row in rows:
    target=forward.get(row['api_id'],{}).get('retained_api_id',row['api_id'])
    assert target in selected
    mapped[target].append(row)
for target,evidence_rows in mapped.items():
    # Every RDPro page example assumes the original import/setup, preserved verbatim.
    snippets=[excerpt('rdpro.md',1,13)]
    evidence=[]
    for r in evidence_rows:
        start,end=section_bounds(r['doc_file'],r['doc_line'])
        snippets.append(excerpt(r['doc_file'],start,end))
        if r['family']=='saveAsGeoTiff':
            snippets.append(excerpt('rdpro.md',246,len((ROOT/'github-docs/rdpro.md').read_text().splitlines())))
        evidence.append({'match_type':'reviewed_original_receiver_to_source_owner',
          'documented_interface':r['api_id'],'documented_call':r['call_path'],
          'document_id':'doc/'+r['doc_file'],'doc_line':r['doc_line'],'doc_text':r['doc_text'],
          'source_path':r['source_file'],'source_line':r['source_line'],
          'source_signature':r['source_signature'],'evidence_kind':r['evidence'],
          'consolidation_proof':forward.get(r['api_id']),
          'version_status':'All 16 linked Markdown documents equal the pinned source documents byte-for-byte.',
          'execution_status':'Name/receiver/forwarding mapping checked; original example execution not certified.'})
    snippets=list({s['path']:s for s in snippets}.values())
    manifest['targets'][target]={'status':'documented','excerpts':snippets,
      'reason':'Original example or explicit description matched to its defining interface, then to a retained operation only when a reviewed forwarding proof exists.',
      'evidence':evidence}
assert len(mapped)==18
documented_total=sum(r['status']=='documented' for r in manifest['targets'].values())
assert documented_total==19 # 18 operations plus previously matched ITile type identity
raw=(json.dumps(manifest,indent=2)+'\n').encode(); (OUT/'manifest.json').write_bytes(raw)
# Exercise the exact real reader used by Original evaluation and README authoring.
sys.path.insert(0,str(ENGINE))
from aideal.original_documentation import load_original_documents, original_target_texts
cfg=SimpleNamespace(root=OUT,raw={'files':{'original_doc_manifest':'manifest.json','original_doc_manifest_sha256':sha(raw)}})
bundle=load_original_documents(cfg.root,cfg.raw['files'])
texts=original_target_texts(cfg, sorted(selected),limit=22119)
checks=[]
for api,rs in mapped.items():
    body=texts[api]
    for r in rs:
        assert r['doc_text'] in body, (api,r['doc_text'])
    assert 'import edu.ucr.cs.bdlab.beast._' in body
    assert all('consolidation_proof' not in body and 'source_signature' not in body for r in rs)
    checks.append({'api':api,'prompt_document_chars':len(body),'original_evidence_lines_present':True,'setup_present':True})
for api,row in manifest['targets'].items():
    for ex in row['excerpts']:
        if 'original_line_start' in ex:
            doc=(OUT/by_doc[ex['document_id']]['path']).read_bytes()
            expected=b''.join(doc.splitlines(keepends=True)[ex['original_line_start']-1:ex['original_line_end']])
            assert (OUT/ex['path']).read_bytes()==expected
sample='scala:edu.ucr.cs.bdlab.raptor.RasterOperationsLocal.mapPixels'
(OUT/'EXAMPLE_ORIGINAL_CONTEXT_mapPixels.txt').write_text(texts[sample])
report={'status':'passed','real_reader':'aideal.original_documentation.original_target_texts',
 'manifest_sha256':sha(raw),'selected_targets':len(selected),'documented_interfaces_before_consolidation':len(rows),
 'documented_retained_targets':documented_total,'documented_operation_targets':len(mapped),
 'preexisting_documented_type_targets':documented_total-len(mapped),'no_reviewed_api_specific_match':len(selected)-documented_total,
 'source_documents':len(manifest['documents']),'shared_document_ids':manifest['shared_document_ids'],
 'maximum_prompt_document_chars':max(map(len,texts.values())),'configured_limit_checked':22119,
 'all_406_targets_resolved':len(texts)==406,'original_excerpt_bytes_unchanged':True,
 'proof_metadata_not_added_to_audience':True,'no_model_or_library_execution':True,
 'frozen_base_manifest_unchanged':sha((BASE/'manifest.json').read_bytes())==sha(base_bytes),
 'documented_target_checks':checks}
# Also traverse the audience inventory layer that places these texts in entries.
from aideal.doc_check_sources import _relevant_doc_inventory
cfg.comprehension={'relevant_doc_chars':22119}
cfg.llm_readme=OUT/'nonexistent-generated-readme.md'
entries=_relevant_doc_inventory(cfg,'original',sorted(selected))
assert len(entries)==406
assert next(e.body for e in entries if e.name==sample)==texts[sample]
try:
    load_original_documents(OUT,{**cfg.raw['files'],'original_doc_manifest_sha256':'0'*64})
except ValueError as err:
    assert 'checksum mismatch' in str(err)
else:
    raise AssertionError('Invalid manifest hash accepted')
report.update(real_audience_inventory_builder='aideal.doc_check_sources._relevant_doc_inventory',
              audience_inventory_entries=len(entries),audience_mapPixels_matches_saved_context=True,
              invalid_manifest_hash_rejected=True)
(OUT/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'CONFIG_FIELDS.json').write_text(json.dumps(cfg.raw['files'],indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='documented_target_checks'},indent=2))
