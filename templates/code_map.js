'use strict';
const data = JSON.parse(document.getElementById('map-data').textContent);
const records = new Map(data.functions.map(f => [f.id, f]));
for (const [alias, target] of Object.entries(data.aliases || {})) {
  records.set(alias, records.get(target));
}
const stages = new Map((data.pipeline.stages || []).map(s => [s.id, s]));
const paths = data.review_paths || [];
let activePath = paths[0]?.id;
let selectedFunction = null;
const el = id => document.getElementById(id);
const make = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
};
const values = value => value == null ? [] : Array.isArray(value) ? value : [value];
const human = value => String(value).replaceAll('_', ' ');
const needsReview = status => /pending|unfinished|partial|wip|planned|not_implemented|review|example_only|guidance_only|preparation|helper|validation|unvalidated/i.test(status);

function badge(status) {
  return make('span', human(status), 'badge' + (needsReview(status) ? ' pending' : ''));
}
function functionLink(id, compact = false) {
  const link = make('a', compact ? (records.get(id)?.name || id) : id);
  link.href = '#' + encodeURIComponent(id);
  return link;
}
function links(container, ids) {
  if (!ids.length) container.append(make('span', 'None resolved', 'path'));
  for (const id of ids) container.append(functionLink(id));
}
function show(view) {
  el('guide').classList.toggle('hidden', view !== 'guide');
  el('functions').classList.toggle('hidden', view !== 'functions');
  el('guide-link').classList.toggle('active', view === 'guide');
  el('reference-link').classList.toggle('active', view === 'functions');
}
function stagePanel(id) {
  const stage = stages.get(id);
  const panel = make('details', undefined, 'stage-details');
  panel.dataset.stage = id;
  panel.append(make('summary', stage.title), badge(stage.status));
  for (const [key, label] of [['entry_points', 'Related functions'], ['prompts', 'Prompts'],
    ['harness', 'Harness / checker'], ['role', 'Model role'], ['outputs', 'Outputs'],
    ['limitations', 'Limits / work remaining']]) {
    const items = values(stage[key]);
    if (!items.length) continue;
    panel.append(make('div', label, 'label'));
    if (key === 'entry_points') {
      const group = make('div', undefined, 'links');
      for (const item of items) {
        group.append(records.has(item) ? functionLink(item) : make('span', item, 'path'));
      }
      panel.append(group);
    } else {
      for (const item of items) panel.append(make('p', String(item)));
    }
  }
  const downstream = (data.pipeline.relationships || []).filter(r => r.from === id);
  if (downstream.length) {
    panel.append(make('div', 'Related stages', 'label'));
    const group = make('div', undefined, 'links');
    for (const relation of downstream) {
      const link = make('a', stages.get(relation.to).title + ' · ' + human(relation.kind));
      link.href = '#stage-' + relation.to;
      group.append(link);
    }
    panel.append(group);
  }
  return panel;
}
function entryCard(entry) {
  const card = make('li', undefined, 'card entry');
  card.id = 'entry-' + entry.id;
  const heading = make('div', undefined, 'entry-main');
  const description = make('div');
  description.append(make('h3', entry.title), make('p', entry.summary));
  heading.append(description);
  if (entry.function) {
    const link = functionLink(entry.function, true);
    link.className = 'function-link';
    link.title = entry.function;
    heading.append(link);
  }
  card.append(heading);
  if (entry.status !== 'implemented') card.append(badge(entry.status));
  const io = make('div', undefined, 'io');
  for (const [label, text] of [['Input', entry.inputs], ['Output', entry.outputs]]) {
    const box = make('div');
    box.append(make('span', label, 'label'), make('p', text));
    io.append(box);
  }
  card.append(io);
  if (entry.function) {
    const helpers = make('details');
    helpers.append(make('summary', 'Helpers underneath · ' + entry.helper_ids.length + ' direct calls'));
    helpers.append(make('p', 'Resolved Python calls. Open a helper to follow its own dependencies.', 'path'));
    const list = make('ul', undefined, 'helper-list');
    for (const id of entry.helper_ids) {
      const row = make('li');
      const f = records.get(id);
      row.append(functionLink(id, true), make('small', f.summary || f.module));
      list.append(row);
    }
    helpers.append(list);
    card.append(helpers);
  }
  const evidence = make('details');
  evidence.append(make('summary', 'Prompts, harness and implementation status'));
  for (const id of entry.stage_ids) evidence.append(stagePanel(id));
  card.append(evidence);
  return card;
}
function renderPath(id) {
  const path = paths.find(p => p.id === id) || paths[0];
  if (!path) return;
  activePath = path.id;
  for (const link of el('paths').children) {
    if (link.dataset.path === path.id) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  el('guide-link').href = '#path-' + path.id;
  el('path-intro').replaceChildren(badge(path.status), make('h2', path.subtitle),
    make('p', path.summary, 'intro'), make('p', path.note, 'notice'));
  el('entries').replaceChildren(...path.entries.map(entryCard));
  el('other-tools').replaceChildren();
  if (path.extra_stage_ids.length) {
    const extra = make('details', undefined, 'card');
    extra.append(make('summary', 'Other development tools and examples'));
    for (const stage of path.extra_stage_ids) extra.append(stagePanel(stage));
    el('other-tools').append(extra);
  }
}
function filter() {
  const query = el('query').value.trim().toLowerCase();
  const module = el('module').value;
  const matches = data.functions.filter(f => (!module || f.module === module) &&
    (!query || [f.id, ...(f.aliases || []), f.summary, ...f.prompts].join(' ').toLowerCase().includes(query)));
  el('count').textContent = matches.length + ' of ' + data.functions.length + ' definitions in the full reference';
  el('results').replaceChildren();
  for (const f of matches) {
    const button = make('button', f.name);
    button.dataset.id = f.id;
    button.classList.toggle('selected', f.id === selectedFunction);
    button.append(make('small', f.module + ' · line ' + f.line));
    button.onclick = () => { location.hash = encodeURIComponent(f.id); };
    el('results').append(button);
  }
  if (!matches.length) el('results').append(make('p', 'No matching definitions.', 'intro'));
}
function selectFunction(id) {
  const f = records.get(id);
  if (!f) {
    show('functions');
    el('detail').replaceChildren(make('h2', 'Function not found'),
      make('p', 'This link may refer to a removed private helper or an older map. Search the current reference or return to the guided workflow.'));
    return;
  }
  selectedFunction = f.id;
  show('functions');
  el('detail').replaceChildren(make('h2', f.name),
    make('div', f.path + ':' + f.line + ' · ' + f.kind, 'path'),
    make('p', f.summary || 'Inspect its source, callers and dependencies below.'),
    make('div', f.signature, 'signature'));
  if (f.source_url) {
    const sourceLink = make('a', 'Open this definition on GitHub');
    sourceLink.href = f.source_url;
    el('detail').append(sourceLink);
  }
  const columns = make('div', undefined, 'cols');
  for (const [label, ids] of [['Calls / helpers', f.calls], ['Called by', f.called_by]]) {
    const box = make('div');
    box.append(make('h3', label));
    const group = make('div', undefined, 'links');
    links(group, ids);
    box.append(group);
    columns.append(box);
  }
  el('detail').append(columns);
  if (f.prompts.length) {
    el('detail').append(make('div', 'Prompt keys', 'label'), make('p', f.prompts.join(', ')),
      make('p', 'Lookup: configured prompts directory / <key>.md, then packaged default_prompts / <key>.md.', 'path'));
  }
  if (f.unresolved_calls.length) {
    const unresolved = make('details');
    unresolved.append(make('summary', 'External or dynamic calls · ' + f.unresolved_calls.length),
      make('p', f.unresolved_calls.join(' · '), 'unresolved'));
    el('detail').append(unresolved);
  }
  const source = make('details');
  source.open = true;
  source.append(make('summary', 'Source · lines ' + f.line + '–' + f.end_line));
  const pre = make('pre', undefined, 'source');
  f.source.split('\n').forEach((line, index) => {
    const row = make('span');
    row.append(make('span', String(f.line + index), 'line-no'), document.createTextNode(line));
    pre.append(row);
  });
  source.append(pre);
  el('detail').append(source);
  for (const button of el('results').children) {
    button.classList.toggle('selected', button.dataset.id === f.id);
  }
}
function revealStage(id) {
  const owns = p => p.extra_stage_ids.includes(id) || p.entries.some(e => e.stage_ids.includes(id));
  const path = paths.find(p => p.id === activePath && owns(p)) || paths.find(owns);
  if (path) renderPath(path.id);
  show('guide');
  const panel = [...document.querySelectorAll('[data-stage]')].find(p => p.dataset.stage === id);
  if (panel) {
    for (let node = panel; node; node = node.parentElement) {
      if (node.tagName === 'DETAILS') node.open = true;
    }
    panel.scrollIntoView({block: 'start'});
  }
}
function routeHash() {
  let id;
  try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
  if (!id || id.startsWith('path-')) {
    renderPath(id ? id.slice(5) : paths[0]?.id);
    show('guide');
  } else if (id === 'functions') show('functions');
  else if (id.startsWith('stage-')) revealStage(id.slice(6));
  else selectFunction(id);
}
for (const path of paths) {
  const link = make('a');
  link.href = '#path-' + path.id;
  link.dataset.path = path.id;
  link.append(make('strong', path.title), make('span', path.subtitle));
  el('paths').append(link);
}
for (const module of data.modules) {
  const option = make('option', module.name + ' · ' + module.lines + ' lines');
  option.value = module.name;
  el('module').append(option);
}
if (stages.has('operator_guidance')) el('operator-details').append(stagePanel('operator_guidance'));
el('limitations').textContent = data.limitations;
el('query').oninput = filter;
el('module').onchange = filter;
window.addEventListener('hashchange', routeHash);
renderPath(activePath);
filter();
routeHash();
