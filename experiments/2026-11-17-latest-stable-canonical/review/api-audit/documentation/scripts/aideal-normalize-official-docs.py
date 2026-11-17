from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
from collections import Counter
import csv,json,re,hashlib
root=Path('/tmp/aideal-source-doc-recheck-2026-11-17')
bundle=json.loads((root/'RENDERED_DOC_BUNDLE.json').read_text())
targets=list(csv.DictReader((root/'RENDERED_DOC_TARGETS.csv').open()))
blocked={'script','style','noscript','nav','header','footer','aside','form','iframe','object','svg','button','input'}
void={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
blocks={'p','div','section','article','main','pre','dt','dd','dl','li','ul','ol','table','tr','blockquote','h1','h2','h3','h4','h5','h6','br','hr'}
class Node:
    def __init__(self,tag='',attrs=None,parent=None):self.tag=tag;self.attrs=attrs or {};self.parent=parent;self.children=[]
class Tree(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root];self.nodes=[];self.ids={}
    def handle_starttag(self,tag,attrs):
        node=Node(tag,dict(attrs),self.stack[-1]);node.parent.children.append(node);self.nodes.append(node)
        if node.attrs.get('id'):self.ids[node.attrs['id']]=node
        if tag not in void:self.stack.append(node)
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)
def text_of(node,pre=False):
    if isinstance(node,str):return node if pre else re.sub(r'\s+',' ',node)
    if node.tag in blocked or 'headerlink' in node.attrs.get('class','').split():return ''
    inside_pre=pre or node.tag=='pre'
    text=''.join(text_of(x,inside_pre) for x in node.children)
    if node.tag in {'td','th'}:text+=' | '
    return ('\n'+text+'\n')if node.tag in blocks else text
def normalize(node):
    raw=text_of(node);lines=[x.rstrip()for x in raw.splitlines()];return re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n','\n'.join(lines)).strip()+'\n'
def write_text(path,text):
    payload=text.encode();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload);return hashlib.sha256(payload).hexdigest()
page_cache={};pages=[]
for row in bundle['pages']:
    if row['status']!='downloaded' or row['version_check']!='PASS':continue
    path=root/row['local_path'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
    tree=Tree();tree.feed(raw.decode('utf-8',errors='replace'))
    candidates=[n for n in tree.nodes if n.tag=='article'] or [n for n in tree.nodes if n.attrs.get('role')=='main'] or [n for n in tree.nodes if n.tag=='main']
    assert candidates,(row['library'],row['requested_url'])
    main=max(candidates,key=lambda x:len(normalize(x)));text=normalize(main)
    dest=root/'derived-docs'/Path(row['local_path']).relative_to('raw-docs').with_suffix('.txt')
    digest=write_text(dest,text)
    meta={'library':row['library'],'url':row['requested_url'],'version':row['expected_version'],'version_check':row['version_check'],'retrieved_at':row['retrieved_at'],'raw_html_path':row['local_path'],'raw_html_sha256':row['sha256'],'main_text_path':str(dest.relative_to(root)),'main_text_sha256':digest,'main_text_characters':len(text),'main_element':main.tag,'main_element_attributes':main.attrs}
    pages.append(meta);page_cache[row['requested_url']]=(tree,meta)
excerpts=[]
for target in targets:
    tree,meta=page_cache[target['page_url']];anchor=unquote(target['anchor']);node=tree.ids.get(anchor)
    record={**target,'anchor_present':bool(node),'raw_html_sha256':meta['raw_html_sha256'],'main_text_path':meta['main_text_path'],'main_text_sha256':meta['main_text_sha256'],'retrieved_at':meta['retrieved_at']}
    if node:
        container=node
        while container.parent and container.tag not in {'dl','section','article','main'}:container=container.parent
        excerpt=normalize(container);digest=hashlib.sha256(excerpt.encode()).hexdigest();dest=root/'derived-docs/excerpts'/f'{digest}.txt'
        if not dest.exists():write_text(dest,excerpt)
        nested=[]
        stack=[container]
        while stack:
            n=stack.pop()
            if isinstance(n,str):continue
            ident=n.attrs.get('id','')
            if ident.startswith(target['qualified_name']+'.'):nested.append(ident)
            stack.extend(n.children)
        record.update(excerpt_path=str(dest.relative_to(root)),excerpt_sha256=digest,excerpt_characters=len(excerpt),excerpt_container=container.tag,nested_api_anchor_count=len(nested),nested_api_anchors=' | '.join(sorted(nested)),scope_note='Class/exception excerpt includes nested member documentation where present.'if target['object_type']in{'py:class','py:exception'}and nested else 'Exact anchor’s nearest definition-list/section documentation; no implementation-source page appended.')
    else:record.update(excerpt_path='',excerpt_sha256='',excerpt_characters=0,excerpt_container='',nested_api_anchor_count=0,nested_api_anchors='',scope_note='Anchor absent: no API excerpt manufactured.')
    excerpts.append(record)
with(root/'RENDERED_DOC_API_EXCERPTS.csv').open('w',newline='')as file:
    writer=csv.DictWriter(file,fieldnames=list(excerpts[0]));writer.writeheader();writer.writerows(excerpts)
summary={'status':'READY_FOR_DOCUMENT_INPUT_REVIEW'if all(x['anchor_present']for x in excerpts)else'ANCHOR_REVIEW_REQUIRED','method':'Saved official HTML only; extract article/main text after removing scripts/styles/navigation/forms. Per-target exact anchor selects nearest definition list or section. Deduplicate excerpt bytes by SHA256. No source-code implementation page fetched or appended.','network_requests':0,'model_calls':0,'subject_executions':0,'pages':pages,'target_count':len(excerpts),'present_anchors':sum(x['anchor_present']for x in excerpts),'absent_anchors':[{'name':x['qualified_name'],'url':x['url']}for x in excerpts if not x['anchor_present']],'unique_excerpt_files':len({x['excerpt_path']for x in excerpts if x['excerpt_path']}),'class_targets_with_nested_members':sum(x['object_type']in{'py:class','py:exception'}and x['nested_api_anchor_count']>0 for x in excerpts),'libraries':{lib:{'pages':sum(x['library']==lib for x in pages),'targets':sum(x['library']==lib for x in excerpts),'present_anchors':sum(x['library']==lib and x['anchor_present']for x in excerpts),'main_text_characters':sum(x['main_text_characters']for x in pages if x['library']==lib)}for lib in ['mdanalysis','tslearn','mir_eval']},'limitations':['Documentation anchor existence is not an assessment of example correctness or completeness.','Class excerpts can include nested methods; this is explicitly recorded per target.','Inventory aliases and source declaration identities remain separate; the AST crosswalk is supplied independently.','New bundles are staged for review; no frozen experiment config or generated prompt was replaced.']}
(root/'NORMALIZED_DOC_BUNDLE.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k]for k in ['status','target_count','present_anchors','unique_excerpt_files','class_targets_with_nested_members','libraries']}))
