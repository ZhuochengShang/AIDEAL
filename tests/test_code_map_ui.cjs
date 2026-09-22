/* Navigation state checks with a minimal DOM double; no browser or network. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');

class Element {
  constructor(tag = 'div') {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.dataset = {};
    this.attributes = {};
    this.value = '';
    this.className = '';
    this.classList = {
      contains: name => this.className.split(' ').includes(name),
      toggle: (name, enable) => {
        const names = new Set(this.className.split(' ').filter(Boolean));
        if (enable) names.add(name); else names.delete(name);
        this.className = [...names].join(' ');
      }
    };
  }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return (this.text || '') + this.children.map(c => c.textContent).join(''); }
  append(...nodes) { for (const node of nodes) { node.parentElement = this; this.children.push(node); } }
  replaceChildren(...nodes) { this.text = ''; this.children = []; this.append(...nodes); }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  scrollIntoView() { this.scrolled = true; }
}
function walk(node) { return [node, ...node.children.flatMap(walk)]; }
function app() {
  const html = fs.readFileSync(path.join(root, 'templates/code_map.html'), 'utf8');
  const elements = Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(m => [m[1], new Element()]));
  elements['map-data'].textContent = fs.readFileSync(path.join(root, 'docs/function_map.json'), 'utf8');
  const hooks = {};
  const context = {
    document: {
      getElementById: id => elements[id],
      createElement: tag => new Element(tag),
      createTextNode: text => { const node = new Element('#text'); node.textContent = text; return node; },
      querySelectorAll: selector => {
        assert.equal(selector, '[data-stage]');
        return Object.values(elements).flatMap(walk).filter(n => n.dataset.stage);
      }
    },
    location: {hash: ''},
    window: {addEventListener: (name, callback) => { hooks[name] = callback; }}
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, 'templates/code_map.js'), 'utf8'), context);
  return {elements, go: hash => { context.location.hash = hash; hooks.hashchange(); }};
}

test('guided review starts with three entry points and collapsed helpers', () => {
  const {elements: e} = app();
  assert.equal(e.paths.children.length, 4);
  assert.equal(e.entries.children.length, 3);
  assert.equal(e.functions.classList.contains('hidden'), true);
  assert.equal(e.guide.classList.contains('hidden'), false);
  const details = walk(e.entries).filter(n => n.tagName === 'DETAILS');
  assert.ok(details.length > 3);
  assert.ok(details.every(n => !n.open));
});

test('published function view links to the exact GitHub source line', () => {
  const {elements: e, go} = app();
  go('#workflow.evaluation%3Arun_evaluation');
  const source = walk(e.detail).find(n => n.tagName === 'A' && n.textContent === 'Open this definition on GitHub');
  assert.ok(source);
  assert.match(source.href, /^https:\/\/github\.com\/ZhuochengShang\/AIDEAL\/blob\/main\/workflow\/evaluation\.py#L\d+$/);
});

test('development and library preparation link the implemented condition runner', () => {
  const {elements: e, go} = app();
  go('#path-development');
  assert.equal(e.entries.children.length, 4);
  assert.match(e['other-tools'].textContent, /Other development tools/);
  for (const id of ['treatment_preview', 'treatment_proposal', 'treatment_versions', 'source_refactors']) {
    go('#stage-' + id);
    const panel = walk(e['other-tools']).find(n => n.dataset.stage === id);
    assert.equal(panel.open, true);
    assert.ok(walk(panel).some(n => n.tagName === 'A' && n.href.startsWith('#workflow.')));
    if (id === 'treatment_proposal' || id === 'treatment_versions') {
      assert.equal(panel.children[1].textContent, 'implemented unvalidated');
      assert.ok(panel.children[1].classList.contains('pending'));
    }
  }
  go('#path-unfinished');
  assert.equal(e.entries.children.length, 4);
  const runner = e.entries.children.at(-1);
  assert.match(runner.textContent, /run_conditions/);
  assert.ok(walk(runner).some(n => n.tagName === 'A' && n.href.includes('condition_evaluation')));
  go('#path-conditions');
  assert.equal(e.entries.children.length, 3);
  assert.match(e.entries.textContent, /freeze_conditions/);
  assert.match(e.entries.textContent, /report_conditions/);
});

test('old function aliases work and stage history restores the correct workflow', () => {
  const {elements: e, go} = app();
  go('#aideal.readme_agent%3Afind_or_create');
  assert.equal(e.functions.classList.contains('hidden'), false);
  assert.equal(e.detail.children[0].textContent, 'find_or_create');
  go('#stage-legacy_author');
  assert.equal(e.functions.classList.contains('hidden'), true);
  assert.match(e['path-intro'].textContent, /separate development workflow/);
  const panel = walk(e.entries).find(n => n.dataset.stage === 'legacy_author');
  assert.equal(panel.open, true);
  assert.equal(panel.parentElement.open, true);
  go('#path-evaluation');
  assert.equal(e.entries.children.length, 3);
});

test('full reference searches helpers and explains stale removed-function links', () => {
  const {elements: e, go} = app();
  go('#functions');
  e.query.value = 'workflow.evaluation:run_evaluation';
  e.query.oninput();
  assert.equal(e.results.children.length, 1);
  assert.match(e.results.textContent, /run_evaluation/);
  go('#aideal.missing%3Aold_private_helper');
  assert.equal(e.detail.children[0].textContent, 'Function not found');
});
