const assert = require('node:assert/strict');
const { test } = require('node:test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

// Use existing golden scenarios and the canonical ResponseAction contract.
// The frontend tests do not decide which safety actions should apply.
const python = path.resolve('../.venv/Scripts/python.exe');
const scenarios = JSON.parse(execFileSync(python, ['-c', `
import json
from pathlib import Path
from datetime import datetime, timezone
from app.domain.facts import FACTS_ADAPTER
from app.domain.playbooks import evaluate
scenarios = json.loads(Path('tests/fixtures/scenarios.yaml').read_text())['phase1_playbooks']
print(json.dumps([evaluate(FACTS_ADAPTER.validate_python(s['facts']), as_of=datetime(2026,10,1,12,tzinfo=timezone.utc)).model_dump(mode='json')['actions'] for s in scenarios]))
`], { cwd: path.resolve('../backend'), encoding: 'utf8' }));

function loadPanel() {
  const filename = path.resolve('components/conversation-action-panel.tsx');
  const source = fs.readFileSync(filename, 'utf8');
  const module = new Module(filename);
  module.filename = filename;
  module.paths = require('node:module')._nodeModulePaths(path.dirname(filename));
  module._compile(ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  } }).outputText, filename);
  return module.exports;
}

test('distinct ACT NOW area uses backend critical flags and numbered deterministic order', () => {
  const { ConversationActionPanel } = loadPanel();
  for (const actions of scenarios) {
    const html = renderToStaticMarkup(React.createElement(ConversationActionPanel, {
      actions, completed: new Map(), disabled: false, onComplete() {},
    }));
    assert.ok(html.includes('aria-label="Applicable actions"'));
    const urgent = html.match(/<section[^>]*aria-labelledby="act-now-heading"[\s\S]*?<\/section>/)?.[0];
    const expected = actions.filter(a => a.phase === 'CONTAIN' || (a.phase === 'REPORT' && a.critical));
    if (expected.length) {
      assert.ok(urgent?.includes('ACT NOW'));
      assert.deepEqual([...urgent.matchAll(/data-action-id="([^"]+)"/g)].map(m => m[1]), expected.map(a => a.id));
      assert.deepEqual([...urgent.matchAll(/data-action-order="(\d+)"/g)].map(m => Number(m[1])), expected.map(a => a.order));
    } else assert.equal(urgent, undefined);
    assert.deepEqual([...html.matchAll(/data-action-id="([^"]+)"/g)].map(m => m[1]).sort(), actions.map(a => a.id).sort());
    assert.ok(!html.includes('chat bubble'));
  }
});

test('completion is accessible self-report and explanation/source remain available', () => {
  const { ConversationActionPanel } = loadPanel();
  const actions = scenarios[0];
  const action = actions.find(a => a.can_mark_complete);
  const html = renderToStaticMarkup(React.createElement(ConversationActionPanel, {
    actions, completed: new Map([[action.id, true]]), disabled: false, onComplete() {},
  }));
  assert.ok(html.includes(`aria-label="Mark not done: ${action.title}"`));
  assert.ok(html.includes('aria-pressed="true"'));
  assert.ok(html.includes('You say you took this step'));
  assert.ok(html.includes('Why this step / official source'));
  for (const item of actions.filter(a => a.url)) assert.ok(html.includes(item.url.replaceAll('&', '&amp;')));
});

test('only applicable supported groups appear progressively and retain completed actions', () => {
  const { ConversationActionPanel } = loadPanel();
  const actions = scenarios[0];
  const groups = [
    ['ACT NOW', a => a.phase === 'CONTAIN' || (a.phase === 'REPORT' && a.critical)],
    ['PRESERVE', a => a.phase === 'PRESERVE'],
    ['REPORT', a => a.phase === 'REPORT' && !a.critical],
    ['FOLLOW THROUGH', a => a.phase === 'FOLLOW_UP'],
  ];
  let applicable = [];
  for (let index = -1; index < groups.length; index++) {
    if (index >= 0) applicable = applicable.concat(actions.filter(groups[index][1]));
    const html = renderToStaticMarkup(React.createElement(ConversationActionPanel, {
      actions: [...applicable].reverse(), completed: new Map(applicable.map(a => [a.id, true])),
      disabled: false, onComplete() {},
    }));
    const sections = [...html.matchAll(/data-action-group="([^"]+)"/g)].map(m => m[1]);
    assert.deepEqual(sections, groups.slice(0, index + 1).filter(([, select]) => applicable.some(select)).map(([title]) => title));
    assert.ok(!html.includes('data-action-group="UNDERSTAND"'));
    assert.ok(!html.includes('data-action-group="CONTAIN"'));
    for (const [title, select] of groups.slice(0, index + 1)) {
      const start = html.indexOf(`data-action-group="${title}"`);
      const list = start < 0 ? '' : html.slice(start).split('</ol>')[0];
      assert.ok(start >= 0);
      const expected = applicable.filter(select).sort((a, b) => a.order - b.order);
      assert.deepEqual([...list.matchAll(/data-action-id="([^"]+)"/g)].map(m => m[1]), expected.map(a => a.id));
    }
    assert.equal([...html.matchAll(/data-action-id="/g)].length, applicable.length);
    assert.equal([...html.matchAll(/aria-pressed="true"/g)].length, applicable.filter(a => a.can_mark_complete).length);
  }
});
