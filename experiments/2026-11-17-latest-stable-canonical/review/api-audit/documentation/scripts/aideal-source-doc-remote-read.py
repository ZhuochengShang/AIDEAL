from pathlib import Path
import json,subprocess,hashlib,collections,os,ast,re,sys

payload=json.loads(sys.stdin.readline())
study=Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
release=Path('/home/zshan011/apps/aideal/releases/2026-11-17-canonical-api-a6e8bb84fe32')
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}
out={'study':str(study),'release':str(release),'mode':'read-only metadata/text audit; no subject imports or model calls','libraries':{},'helpers':{}}
for lib,inp in payload['inputs'].items():
    src=study/'sources'/lib
    tree=subprocess.check_output(['git','-C',str(src),'ls-tree','-r','-z','HEAD'],env=env)
    entries={}
    for rec in tree.split(b'\0'):
        if not rec:continue
        meta,rel=rec.split(b'\t',1);mode,kind,obj=meta.decode().split();entries[rel.decode()]={'mode':mode,'kind':kind,'object_id':obj}
    docs=[];parts=[];directives=collections.Counter();examples=[];offset=0
    for pathstr in inp['original_document_files']:
        path=Path(pathstr);data=path.read_bytes();text=data.decode('utf-8',errors='ignore')
        sha=hashlib.sha256(data).hexdigest();rel=None
        try:rel=str(path.relative_to(src))
        except ValueError:pass
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        matches=(entries.get(rel,{}).get('object_id')==blob) if rel else None
        block=f'===== {path} =====\n{text}';start=offset+(2 if parts else 0);end=start+len(block);offset=end;parts.append(block)
        cats='dataset' if '/datasets/' in pathstr else ('example' if '/examples/' in pathstr else ('configuration' if path.name in ['conf.py','requirements_rtd.txt'] else ('template' if '/_templates/' in pathstr else 'documentation')))
        lines=[(n,line)for n,line in enumerate(text.splitlines(),1) if re.match(r'^\s*\.\.\s+(auto\w+)::',line)]
        for n,line in lines:
            kind=re.search(r'(auto\w+)::',line).group(1);directives[kind]+=1
            if len(examples)<8:examples.append({'path':str(path),'line':n,'text':line.strip()})
        docs.append({'path':str(path),'relative_source_path':rel,'bytes':len(data),'characters':len(text),'sha256':sha,'tracked_upstream_blob_match':matches,'receipt_hash_match':sha==payload['expected_hashes'].get(pathstr) if pathstr in payload['expected_hashes'] else None,'category':cats,'bundle_start_character':start,'bundle_end_character':end,'characters_in_first_150000':max(0,min(end,150000)-min(start,150000))})
    bundle='\n\n'.join(parts)
    pyx=[rel for rel in entries if rel.endswith('.pyx')]
    doc_candidates=[]
    for rel in pyx:
        path=src/rel
        text=path.read_text(errors='replace')
        module=rel.removeprefix('package/').removesuffix('.pyx').replace('/','.')
        doc_candidates.append({'path':rel,'module':module,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'declaration_lines':[{'line':n,'text':line.strip()}for n,line in enumerate(text.splitlines(),1) if re.match(r'^\s*(?:cdef\s+class\s+|(?:cpdef|def)\s+)',line)][:150]})
    samplepaths={'mdanalysis':'package/doc/sphinx/source/documentation_pages/analysis/rms.rst','mir_eval':'docs/api/beat.rst','tslearn':'docs/gen_modules/tslearn.metrics.rst'}
    out['libraries'][lib]={'source_path':str(src),'head':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],env=env,text=True).strip(),'tree':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD^{tree}'],env=env,text=True).strip(),'tracked_status':subprocess.check_output(['git','-C',str(src),'status','--porcelain=v1','--untracked-files=no'],env=env,text=True),'tracked_entries':len(entries),'gitlinks':[dict(path=rel,**v) for rel,v in entries.items()if v['mode']=='160000'],'documents':docs,'bundle_characters':len(bundle),'bundle_sha256':hashlib.sha256(bundle.encode()).hexdigest(),'document_category_count':dict(collections.Counter(x['category']for x in docs)),'document_category_bytes':{c:sum(x['bytes']for x in docs if x['category']==c)for c in set(x['category']for x in docs)},'raw_rst_auto_directive_counts':dict(directives),'raw_rst_auto_directive_examples':examples,'cap150000_fully_excluded_files':sum(x['bundle_start_character']>=150000 for x in docs),'cap150000_boundary_file':next((x['path']for x in docs if x['bundle_start_character']<150000<x['bundle_end_character']),None),'cython_pyx_files':doc_candidates,'sample_raw_rst':{'path':samplepaths[lib],'text':(src/samplepaths[lib]).read_text()}if lib in samplepaths else None}
for filename,functions in {'api_intent.py':['_doc_code_mentions'],'doc_check_sources.py':['_relevant_original_texts','_relevant_doc_inventory'],'readme_generation.py':['distilled_readme_context'],'config.py':[]}.items():
    p=release/'vendor/aideal_engine/src/aideal'/filename;text=p.read_text();module=ast.parse(text);snippets=[]
    for node in ast.walk(module):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in functions:
            snippets.append({'name':node.name,'line':node.lineno,'end_line':node.end_lineno,'text':'\n'.join(text.splitlines()[node.lineno-1:node.end_lineno])})
    out['helpers'][filename]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'functions':snippets}
print(json.dumps(out))
