const assert = require("node:assert/strict");
const { test, afterEach } = require("node:test");
const fs = require("node:fs");
const Module = require("node:module");
const ts = require("typescript");

process.env.NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000";
const apiModule = new Module("api-contract", module);
apiModule.filename = require("node:path").resolve("lib/api.ts");
apiModule.paths = module.paths;
apiModule._compile(ts.transpileModule(fs.readFileSync("lib/api.ts", "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, apiModule.filename);
const api = apiModule.exports;
const originalFetch = global.fetch;
afterEach(() => { global.fetch = originalFetch; });

test('Diagnostics correlate HTTP errors without logging case data', async () => {
  const captured = [];
  const original = console.error;
  console.error = (...args) => captured.push(args);
  try {
    global.fetch = async (_url, options) => {
      assert.match(options.headers['X-Request-ID'], /^[a-f0-9-]{36}$/);
      return Response.json({ detail: 'synthetic-private-server-detail' }, {
        status: 500, headers: { 'X-Request-ID': options.headers['X-Request-ID'] },
      });
    };
    await assert.rejects(api.sendConversationTurn('synthetic-case-id', { text: 'synthetic-private-story' }),
      error => error.status === 500 && !!error.requestId);
    const serialized = JSON.stringify(captured);
    assert.ok(serialized.includes('HTTP_ERROR'));
    assert.ok(serialized.includes('/api/v1/incidents/{incident_id}/conversation/turns'));
    assert.ok(!serialized.includes('synthetic-private'));
    assert.ok(!serialized.includes('synthetic-case-id'));
  } finally { console.error = original; }
});

test('Diagnostics distinguish timeouts and malformed success responses', async () => {
  const captured = [];
  const original = console.error;
  console.error = (...args) => captured.push(args);
  try {
    global.fetch = async () => { throw new DOMException('synthetic-private', 'TimeoutError'); };
    await assert.rejects(api.getApiHealth(), error => error.category === 'TIMEOUT');
    global.fetch = async () => new Response('synthetic-private-invalid-json');
    await assert.rejects(api.getApiHealth(), error => error.category === 'RESPONSE_ERROR');
    assert.ok(JSON.stringify(captured).includes('RESPONSE_ERROR'));
    assert.ok(!JSON.stringify(captured).includes('synthetic-private'));
  } finally { console.error = original; }
});

test('AI fallback is diagnosed even when the API successfully saves the turn', async () => {
  const captured = [];
  const original = console.error;
  console.error = (...args) => captured.push(args);
  try {
    global.fetch = async () => Response.json({ turns: [{ text: 'synthetic-private-story', fact_changes: {
      understanding: { status: 'understood' }, agent: { status: 'fallback', http_status: 503 },
    } }] });
    const state = await api.sendConversationTurn('synthetic-private-case', {});
    assert.equal(state.turns.length, 1);
    assert.ok(JSON.stringify(captured).includes('AI_FOLLOW_UP_UNAVAILABLE'));
    assert.ok(!JSON.stringify(captured).includes('synthetic-private'));
  } finally { console.error = original; }
});

test("R4 private requests carry cookies without exposing secrets in URLs", async () => {
  global.fetch = async (url, options) => {
    assert.equal(options.credentials, "include");
    assert.equal(String(url).includes("secret"), false);
    return new Response(JSON.stringify([]));
  };
  await api.listEvidence("synthetic");
});

test("R2 DELETE handles an actual empty 204 response", async () => {
  global.fetch = async () => new Response(null, { status: 204 });
  await api.deleteEvidence("synthetic");
  await api.deleteSuspect("synthetic");
  await api.deleteTimelineEvent("synthetic");
});

test("R2 evidence preview paths resolve to the API origin", async () => {
  global.fetch = async () => Response.json({ id: "synthetic", preview_url: "/api/v1/evidence/synthetic/file" });
  const evidence = await api.getEvidence("synthetic");
  assert.equal(evidence.preview_url, "http://127.0.0.1:8000/api/v1/evidence/synthetic/file");
});

test("R2 lists and verification also resolve private preview paths", async () => {
  const evidence = { id: "synthetic", preview_url: "/api/v1/evidence/synthetic/file" };
  global.fetch = async () => Response.json([evidence]);
  assert.equal((await api.listEvidence("synthetic"))[0].preview_url, api.evidenceFileUrl("synthetic"));
  global.fetch = async () => Response.json({ evidence, comparison: { all_match: true } });
  assert.equal((await api.verifyEvidence("synthetic", {})).evidence.preview_url, api.evidenceFileUrl("synthetic"));
});

test("R2 rejected deletion remains an error", async () => {
  global.fetch = async () => Response.json({ detail: "Evidence not found" }, { status: 404 });
  await assert.rejects(api.deleteEvidence("missing"), { message: "Evidence not found", status: 404 });
});

test('Phase 2 turns preserve IDs, revision, unknown values and private authority', async () => {
  const payload = { turn_id: 'synthetic-request', expected_revision: 3, type: 'answer', field: 'ongoing_loss', value: null };
  global.fetch = async (url, options) => {
    assert.equal(options.credentials, 'include');
    assert.ok(options.signal instanceof AbortSignal);
    assert.deepEqual(JSON.parse(options.body), payload);
    assert.ok(String(url).endsWith('/conversation/turns'));
    return Response.json({ revision: 4 });
  };
  assert.equal((await api.sendConversationTurn('synthetic', payload)).revision, 4);
});

test('Phase 2 disconnect, timeout, failed save and stale state remain errors', async () => {
  for (const error of [new TypeError('offline'), new DOMException('timeout', 'TimeoutError')]) {
    global.fetch = async () => { throw error; };
    await assert.rejects(api.sendConversationTurn('synthetic', {}), api.ApiError);
  }
  for (const status of [409, 500]) {
    global.fetch = async () => Response.json({ detail: 'Save failed' }, { status });
    await assert.rejects(api.sendConversationTurn('synthetic', {}), { status });
  }
});
