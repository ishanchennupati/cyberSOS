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
