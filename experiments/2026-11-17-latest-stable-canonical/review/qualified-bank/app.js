(function () {
  'use strict';
  const bank = globalThis.QUALIFIED_BANK;
  if (!bank || bank.rows.length !== 5307) throw new Error('Qualified bank data missing or incomplete');
  const labels = {rdpro:'Beast / RDPro',mdanalysis:'MDAnalysis',tslearn:'tslearn',mir_eval:'mir_eval',thumbnailator:'Thumbnailator',sedonadb:'SedonaDB SQL'};
  const flagLabels = {prior_forwarding_label:'Prior forwarding label',body_unresolved:'Body unresolved',arity_unknown:'Arity unknown',source_registration_unresolved:'Source registration unresolved'};
  const sourceURL = row => row.source_file ? 'https://github.com/' + bank.meta.banks[row.bank].github_repository + '/blob/' + row.public_snapshot_commit + '/' + row.source_file.split('/').map(encodeURIComponent).join('/') + (row.source_line ? '#L' + row.source_line : '') : null;
  const rows = bank.rows.map(row => {
    const full = Object.assign({}, bank.meta.banks[row.bank], row);
    full.source_url = sourceURL(full);
    full.search_text = [full.api_id,full.display_name,full.qualified_name,full.owner,full.module,full.signature,full.preferred_public_path,...full.public_access_paths].join('\n').toLowerCase();
    return full;
  });
  function filterRows(values, filters) {
    const query = (filters.query || '').toLowerCase().trim();
    return values.filter(row => (!filters.library || row.library===filters.library) && (!filters.module || row.module===filters.module) && (!filters.language || row.source_language===filters.language) && (!filters.doc || row.doc_status===filters.doc) && (!filters.flag || row.review_flags.includes(filters.flag)) && (!query || row.search_text.includes(query)));
  }
  function options(values, key) { return [...new Set(values.map(row=>row[key]))].sort((a,b)=>a.localeCompare(b)); }
  globalThis.QualifiedBankUI = {rows,filterRows,options,sourceURL};
  if (typeof document==='undefined') return;
  const byId = id=>document.getElementById(id);
  const nodes = Object.fromEntries(['query','library','module','language','doc','flag','reset','rows','detail','match-count','page-count','previous','next'].map(id=>[id,byId(id)]));
  let page = 0, selected = '', filtered = rows;
  const pageSize = 50;
  function el(tag,text,cls) { const node=document.createElement(tag); if(text!==undefined) node.textContent=text; if(cls) node.className=cls; return node; }
  function link(text,href) { const node=el('a',text); if(!href || !/^(?:https?:\/\/|\.\.?\/)/.test(href)) throw new Error('Unexpected evidence URL'); node.href=href; if(/^https?:/.test(href)){node.target='_blank';node.rel='noopener noreferrer';} return node; }
  function addOptions(node,values,allLabel,nameMap) { const previous=node.value; node.replaceChildren(el('option',allLabel)); node.firstChild.value=''; values.forEach(value=>{const option=el('option',nameMap ? nameMap[value] : value); option.value=value; node.append(option);}); node.value=values.includes(previous)?previous:''; }
  function filters() { return Object.fromEntries(['query','library','module','language','doc','flag'].map(key=>[key,nodes[key].value])); }
  addOptions(nodes.library,options(rows,'library'),'All libraries',labels);
  addOptions(nodes.language,options(rows,'source_language'),'All languages');
  addOptions(nodes.module,options(rows,'module'),'All modules');
  function metadata(parent,items) { const dl=el('dl'); items.forEach(([key,value])=>{dl.append(el('dt',key),el('dd',value===null||value===undefined||value===''?'Not established':String(value)));}); parent.append(dl); }
  function evidenceLinks(parent,values) { const list=el('div',undefined,'asset-links');values.forEach(([text,href])=>list.append(link(text,href))); parent.append(list); }
  function show(row,writeHash) {
    selected=row.api_id; const pane=nodes.detail;pane.replaceChildren();
    pane.append(el('h2',row.display_name),el('p',row.api_id,'identity'));
    const copyRow=el('div',undefined,'copy-row'),copy=el('button','Copy API ID'),copyStatus=el('span','');copy.type='button';
    copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(row.api_id);copyStatus.textContent='Copied';}catch(_){copyStatus.textContent='Select the API ID above to copy it.';}});copyRow.append(copy,copyStatus);pane.append(copyRow);
    metadata(pane,[['Library / bank',labels[row.library]+' · '+row.bank],['Module',row.module],['Language',row.source_language+(row.source_language!==row.language?' (API identity: '+row.language+')':'')],['Kind',row.kind],['Defining owner',row.owner],['Owner kind',row.owner_kind]]);
    pane.append(el('h3','Selected declaration'),el('pre',row.signature||'No verified signature recorded'));
    const arity=row.language==='SQL'?'Registered SQL signature; no finite host arity asserted':row.parameter_count===null?'Unknown arity; not a verified zero-argument callable':row.parameter_count+' explicit parameter'+(row.parameter_count===1?'':'s');
    pane.append(el('p',arity+' · '+row.parameter_count_status));
    if(row.preferred_public_path) pane.append(el('p','Preferred public access: '+row.preferred_public_path));
    if(row.public_access_paths.length){const detail=el('details');detail.append(el('summary','Verified public access paths ('+row.public_access_paths.length+')'),el('pre',row.public_access_paths.join('\n')));pane.append(detail);}
    pane.append(el('h3','Source and selection evidence'));
    if(row.source_url)pane.append(link(row.source_file+(row.source_line?':'+row.source_line:''),row.source_url));else pane.append(el('p','Source registration binding remains unresolved. See the origin ledger.','notice'));
    pane.append(el('p','Selection: '+row.selection_reason.replaceAll('_',' ')));
    if(row.review_flags.length)pane.append(el('p',row.review_flags.map(flag=>flagLabels[flag]).join(' · '),'callout'));
    pane.append(el('p','Body category: '+row.body_category+'. Structural labels do not establish semantic duplication or certify wrapper-free selection.','sub'));
    if(row.review_notes.length){const list=el('ul');row.review_notes.forEach(note=>list.append(el('li',note)));pane.append(list);}
    if(row.related_sites.length){const detail=el('details');detail.append(el('summary','Other recorded sites for this identity ('+row.related_sites.length+')'));const list=el('ul');row.related_sites.forEach(site=>list.append(el('li',site.status+': '+site.reason.replaceAll('_',' ')+' · arity '+(site.parameter_count===null?'unknown':site.parameter_count)+' · '+site.file+':'+site.line)));detail.append(list);pane.append(detail);}
    if(row.collapsed_sql_aliases.length)pane.append(el('p','Explicit SQL aliases collapsed into this registered operation: '+row.collapsed_sql_aliases.join(', ')));
    evidenceLinks(pane,[['Full selection receipt',row.links.selection_receipt],['Source / origin ledger',row.links.source_ledger],['Selected API manifest',row.links.api_manifest]]);
    const provenance=el('details');provenance.append(el('summary','Pinned source and publication identities'));metadata(provenance,[['Official commit',row.source_commit],['Source tree',row.source_tree],['Public snapshot',row.public_snapshot_commit],['Source file SHA256',row.source_sha256],['Selected site ID',row.site_id],['Policy',row.selection_policy],['Origin status',row.origin_status]]);provenance.append(el('p','The public snapshot commit differs from the official commit; its source tree is recorded as identical.'));pane.append(provenance);
    pane.append(el('h3','Original documentation input'));
    pane.append(el('p',row.doc_status==='documented'?'Exact reviewed excerpt mapped':'No exact excerpt mapped; this does not establish that useful original documentation is absent.'));
    pane.append(el('p',row.doc_reason,'sub'));
    const shared=el('ul');row.shared_readme.forEach(doc=>{const li=el('li');li.append(link('Shared pinned README · '+doc.id,doc.href));shared.append(li);});pane.append(shared);
    if(row.excerpts.length){const list=el('ul');row.excerpts.forEach((doc,index)=>{const li=el('li');li.append(link('Exact excerpt '+(index+1)+(doc.anchor?' · '+doc.anchor:''),doc.href));if(doc.origin_url)li.append(document.createTextNode(' · '),link('original page',doc.origin_url+(doc.anchor?'#'+encodeURIComponent(doc.anchor):'')));list.append(li);});pane.append(list);}
    pane.append(el('p','Shared README text is supplied verbatim to every Original target and earns no exact-match coverage credit. Exact content budgets are checked; no silent slicing.','sub'));
    evidenceLinks(pane,[['Documentation manifest and hashes',row.links.documentation_manifest]]);
    pane.append(el('h3','Prepared micro task inputs'));
    pane.append(el('p',bank.meta.micro_contract));
    evidenceLinks(pane,[['Configuration',row.links.config],['Project profile',row.links.profile],['Scaffold',row.links.scaffold],['Prepared target manifest',row.links.prepared_manifest]]);
    pane.append(el('h3','Program and result status'));
    pane.append(el('p','Pending an approved model call. No generated program, delivered prompt/response, task-specific expected value, stdout/stderr or benchmark verdict is claimed here.','pending'));
    if(writeHash && typeof history!=='undefined')history.replaceState(null,'','#api='+encodeURIComponent(row.api_id));
    renderTable();
  }
  function renderTable(){
    nodes.rows.replaceChildren();
    if(!filtered.length){const tr=el('tr'),td=el('td','No targets match these filters.','empty');td.colSpan=3;tr.append(td);nodes.rows.append(tr);}
    filtered.slice(page*pageSize,(page+1)*pageSize).forEach(row=>{const tr=el('tr');if(row.api_id===selected)tr.className='selected';const first=el('td'),choose=el('button',row.qualified_name,'api-button');choose.type='button';choose.title=row.api_id;choose.addEventListener('click',()=>show(row,true));first.append(choose,el('span',row.api_id,'sub'));const second=el('td',labels[row.library]+' · '+row.source_language);second.append(el('span',row.module,'sub'));const third=el('td');third.append(el('span',row.doc_status==='documented'?'Exact excerpt':'No exact excerpt','badge'+(row.doc_status==='documented'?'':' no')));row.review_flags.forEach(flag=>third.append(el('span',flagLabels[flag],'badge review')));tr.append(first,second,third);nodes.rows.append(tr);});
    const pages=Math.max(1,Math.ceil(filtered.length/pageSize));nodes['page-count'].textContent='Page '+(page+1)+' / '+pages;nodes.previous.disabled=page===0;nodes.next.disabled=page+1>=pages;
    nodes['match-count'].textContent=filtered.length.toLocaleString()+' of '+rows.length.toLocaleString()+' targets'+(filtered.length?' · showing '+(page*pageSize+1)+'–'+Math.min((page+1)*pageSize,filtered.length):'');
  }
  function apply(){page=0;filtered=filterRows(rows,filters());const choice=filtered.find(row=>row.api_id===selected)||filtered[0];if(choice)show(choice,false);else{selected='';nodes.detail.replaceChildren(el('p','No targets match the current filters.'));renderTable();}}
  nodes.query.addEventListener('input',apply);
  ['module','language','doc','flag'].forEach(key=>nodes[key].addEventListener('change',apply));
  nodes.library.addEventListener('change',()=>{const subset=rows.filter(row=>!nodes.library.value||row.library===nodes.library.value);addOptions(nodes.module,options(subset,'module'),'All modules');apply();});
  nodes.reset.addEventListener('click',()=>{['query','library','module','language','doc','flag'].forEach(key=>nodes[key].value='');addOptions(nodes.module,options(rows,'module'),'All modules');apply();});
  nodes.previous.addEventListener('click',()=>{if(page>0){page--;renderTable();}});nodes.next.addEventListener('click',()=>{if((page+1)*pageSize<filtered.length){page++;renderTable();}});
  const selectedId=new URLSearchParams(location.hash.slice(1)).get('api');const initial=rows.find(row=>row.api_id===selectedId)||rows[0];renderTable();show(initial,false);
  globalThis.QualifiedBankUI.show=show;
})();
