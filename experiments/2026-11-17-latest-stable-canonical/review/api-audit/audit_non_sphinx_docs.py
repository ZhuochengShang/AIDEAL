from pathlib import Path
import collections,json,re,sys,hashlib,subprocess
from html.parser import HTMLParser
S=Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
sys.path.insert(0,'/home/zshan011/apps/aideal/releases/2026-11-17-canonical-api-a6e8bb84fe32/vendor/aideal_engine/src')
from aideal.api_intent import _doc_code_mentions
r=S/'review_snapshot/review'
s=(r/'API_SELECTION.html').read_text();rows,_=json.JSONDecoder().raw_decode(s.split('const records=',1)[1])
result={'method':'Read-only pinned source/doc text audit; no imports of subject packages, model calls or subject executions','libraries':{}}
a=[x for x in rows if x['library']=='rdpro']; names=set(x['name'] for x in a)
inputs=json.loads((r/'banks/rdpro_scala/INPUTS.json').read_text());paths=[Path(x) for x in inputs['original_document_files']]
extra=[S/'sources/rdpro'/p for p in ['dataExplorer/README.md','distribution/README.txt','dynoviz/README.md','satex/README.md']]
docs=[]
for p in paths+extra:
 text=p.read_text(); hits=_doc_code_mentions(text,names)
 docs.append({'path':str(p),'source_relative':str(p.relative_to(S/'sources/rdpro')),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'in_old_bundle':p in paths,'code_context_names':sorted(hits),'mention_count':len(hits),'headings':re.findall(r'^#{1,4} (.+)',text,re.M),'evidence':[{'name':n,'lines':[i for i,l in enumerate(text.splitlines(),1) if re.search(r'\b'+re.escape(n)+r'\b',l)][:10],'candidate_sites':len([x for x in a if x['name']==n])} for n in sorted(hits)]})
result['libraries']['rdpro']={'source_names':len(names),'old_bundle_files':len(paths),'whole_repository_additional_module_readmes':4,'old_bundle_code_context_names':len(set().union(*(set(x['code_context_names']) for x in docs if x['in_old_bundle']))),'expanded_bundle_code_context_names':len(set().union(*(set(x['code_context_names']) for x in docs))),'documents':docs,'interpretation':'Simple-name code mentions, not qualified API or complete documentation coverage. Full original Markdown retained upstream; no invented rendered API inventory.'}
class MemberParser(HTMLParser):
 def __init__(self):super().__init__();self.h=False;self.pre=False;self.hh=[];self.pp=[];self.title='';self.members=[];self.ready=False
 def handle_starttag(self,t,a):
  if t in ('h3','h4'):self.h=True;self.hh=[]
  if t=='pre':self.pre=self.ready;self.pp=[]
 def handle_data(self,t):
  if self.h:self.hh.append(t)
  if self.pre:self.pp.append(t)
 def handle_endtag(self,t):
  if t in ('h3','h4') and self.h:self.title=''.join(self.hh).strip();self.h=False;self.ready=True
  if t=='pre' and self.pre:
   text=' '.join(''.join(self.pp).split());self.pre=False;self.ready=False
   if self.title and '(' in text and ')' in text and re.search(r'\b'+re.escape(self.title)+r'\s*\(',text):self.members.append({'name':self.title,'signature':text})
root=S/'extras/thumbnailator/original_docs';members=[]
for p in sorted(root.rglob('*.html')):
 if not str(p.relative_to(root)).startswith('net/coobird/thumbnailator/'):continue
 parser=MemberParser();parser.feed(p.read_text(errors='replace'));owner=str(p.relative_to(root))[:-5].replace('/','.')
 for m in parser.members:
  m.update(owner=owner,path=str(p),kind='constructor' if m['name']==owner.rsplit('.',1)[-1] else 'method',access='public' if re.search(r'\bpublic\b',m['signature']) else 'protected' if re.search(r'\bprotected\b',m['signature']) else 'unspecified',page_sha256=hashlib.sha256(p.read_bytes()).hexdigest());members.append(m)
for m in members:
 if m['access']=='unspecified':
  source=S/'sources/thumbnailator/src/main/java'/(m['owner'].replace('.','/')+'.java')
  if source.is_file() and re.search(r'public\s+interface\s+'+re.escape(m['owner'].rsplit('.',1)[-1])+r'\b',source.read_text()):
   m['access']='public';m['access_basis']='implicit_public_interface_member';m['owner_source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
  else:m['access_basis']='not_resolved';m['owner_source_sha256']=''
 else:m['access_basis']='explicit_public_modifier';m['owner_source_sha256']=''
result['libraries']['thumbnailator']={'javadoc_root':str(root),'parsed_signature_entries':len(members),'public_signature_entries':sum(m['access']=='public' for m in members),'public_distinct_simple_names':len({m['name'] for m in members if m['access']=='public'}),'kind_access_counts':dict(collections.Counter(m['kind']+':'+m['access'] for m in members)),'members':members,'interpretation':'Declared member detail signatures parsed from official 0.4.21 Javadoc; inherited-only links are excluded; protected declarations separated.'}
inputs=json.loads((r/'banks/sedonadb/INPUTS.json').read_text());paths=[Path(x) for x in inputs['original_document_files']];names={x['name'].lower():x['name'] for x in rows if x['library']=='sedonadb'};docs=[]
for p in paths:
 if p.suffix!='.qmd' or p.stem=='index':continue
 text=p.read_text();docs.append({'path':str(p),'name_from_filename':p.stem,'registered_name':names.get(p.stem.lower()),'title':re.findall(r'^title:\s*(.+)',text,re.M)[:1],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
found={x['registered_name'] for x in docs if x['registered_name']}
result['libraries']['sedonadb']={'registered_names':len(names),'function_pages':len(docs),'exact_filename_matches':len(found),'registered_names_without_exact_page':sorted(set(names.values())-found),'documents':docs,'interpretation':'Version-bound SQL reference page filenames matched case-insensitively to registered SQL names; aliases need separate mapping, no bare prose counting.'}
print(json.dumps(result))
