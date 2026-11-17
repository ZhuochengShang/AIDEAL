from pathlib import Path
from collections import Counter
import csv,json,re
root=Path('/tmp/aideal-source-doc-recheck-2026-11-17')
imports=json.loads((root/'TSLEARN_AST_REEXPORTS.json').read_text())
explicit=[x for x in imports if not x['star_import'] and x['direct_top_level']]
inventory=list(csv.DictReader((root/'tslearn-official-inventory.csv').open()))
by_name={x['qualified_name']:x for x in inventory if x['object_type'].startswith('py:')}
cross=list(csv.DictReader((root/'tslearn-source-inventory-crosswalk.csv').open()))
result=[]
for row in cross:
    origin=row['source_qualified_name'];visited={origin:[]};queue=[origin]
    while queue:
        current=queue.pop(0)
        for imp in explicit:
            target=imp['imported_target']
            if current==target or current.startswith(target+'.'):
                alias=imp['public_binding']+current[len(target):]
                if alias not in visited:
                    visited[alias]=visited[current]+[{'path':imp['path'],'line':imp['line'],'binding':imp['public_binding'],'target':target}]
                    queue.append(alias)
    matches=[name for name in visited if name in by_name]
    result.append({**row,'ast_resolved_doc_match':bool(matches),'ast_resolved_doc_names':' | '.join(sorted(matches)),'ast_resolved_urls':' | '.join(by_name[x]['url']for x in sorted(matches)),'ast_proof':json.dumps({name:visited[name]for name in matches},separators=(',',':')),'unresolved_bare_only':not bool(matches) and row['bare_name_match']=='True'})
with(root/'tslearn-source-inventory-crosswalk-with-aliases.csv').open('w',newline='')as f:
    writer=csv.DictWriter(f,fieldnames=list(result[0]));writer.writeheader();writer.writerows(result)
count=lambda rows:{'source_sites':len(rows),'direct_qualified_matches':sum(x['exact_qualified_match']=='True'for x in rows),'direct_or_ast_export_matches':sum(x['ast_resolved_doc_match']for x in rows),'unresolved_bare_name_only':sum(x['unresolved_bare_only']for x in rows),'no_bare_name_match':sum(x['bare_name_match']=='False'for x in rows)}
aliases={'library':'tslearn','method':'Static ImportFrom graph in pinned tslearn/**/__init__.py. Only unconditional top-level explicit imports prove aliases; star/conditional imports are separately recorded and do not prove a match. Attribute suffixes retain class method identity. No module imports or execution.','import_rows':len(imports),'explicit_unconditional_imports':len(explicit),'conditional_or_star_rows':[x for x in imports if x not in explicit],'all_source_rows':count(result),'selected_source_rows':count([x for x in result if x['selection_status']=='selected']),'still_ambiguous_selected':[x for x in result if x['selection_status']=='selected'and x['unresolved_bare_only']]}
(root/'TSLEARN_ALIAS_AUDIT.json').write_text(json.dumps(aliases,indent=2)+'\n')
readback=json.loads((root/'PINNED_SOURCE_AND_DOC_READBACK.json').read_text())
cython=readback['libraries']['mdanalysis']['cython_pyx_files']
entries=list(csv.DictReader((root/'mdanalysis-official-inventory.csv').open()))
sourcequals={x['source_qualified_name']for x in csv.DictReader((root/'mdanalysis-source-inventory-crosswalk.csv').open())}
linked=[]
for entry in entries:
    if not entry['object_type'].startswith('py:'):continue
    candidates=[x for x in cython if entry['qualified_name']==x['module']or entry['qualified_name'].startswith(x['module']+'.')]
    if not candidates:continue
    src=max(candidates,key=lambda x:len(x['module']));name=entry['qualified_name'].rsplit('.',1)[-1]
    declared=[x for x in src['declaration_lines']if re.search(r'\b'+re.escape(name)+r'\s*(?:\(|:)',x['text'])]
    linked.append({**entry,'source_pyx_path':src['path'],'source_pyx_sha256':src['sha256'],'absent_from_saved_python_rows':entry['qualified_name']not in sourcequals,'same_token_declaration_lines':' | '.join(str(x['line'])+':'+x['text']for x in declared)})
with(root/'mdanalysis-cython-documented-objects.csv').open('w',newline='')as f:
    writer=csv.DictWriter(f,fieldnames=list(linked[0]));writer.writeheader();writer.writerows(linked)
cython_summary={'library':'mdanalysis','pinned_pyx_files':len(cython),'documented_cython_module_objects':len(linked),'types':dict(Counter(x['object_type']for x in linked)),'all_absent_from_saved_python_rows':all(x['absent_from_saved_python_rows']for x in linked),'private_name_component_rows':sum(x['private_name_component']=='True'for x in linked),'scope_note':'Inventory objects linked by exact module prefix to tracked .pyx files, not a newly parsed public Cython-callable count. May include inherited objects/properties/data. Saved source rows are Python-only and therefore not the complete package API.','examples':[x for x in linked if x['same_token_declaration_lines']and x['object_type']in ['py:function','py:class']][:12]}
(root/'MDANALYSIS_CYTHON_SCOPE.json').write_text(json.dumps(cython_summary,indent=2)+'\n')
print(json.dumps({'tslearn':{k:aliases[k]for k in ['all_source_rows','selected_source_rows']},'mdanalysis_cython':{k:cython_summary[k]for k in ['pinned_pyx_files','documented_cython_module_objects','types','all_absent_from_saved_python_rows']}}))
