// Optional local browser verification, using an already installed Playwright.
// No dependency install, fake API, external provider, or government submission.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || "playwright");
const apiUrl = process.env.SMOKE_API_URL || "http://localhost:8000";
const fixture = JSON.parse(fs.readFileSync(path.resolve("../backend/tests/fixtures/scenarios.yaml"), "utf8"))["0B_existing_journey"];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(15000);
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("dialog", dialog => dialog.accept());
  page.on("response", response => {
    if (response.url().includes("/api/v1/") && response.status() >= 400) errors.push(response.status() + " " + response.url());
  });
  try {
    await page.goto(process.env.SMOKE_FRONTEND_URL || "http://127.0.0.1:3001");
    await page.getByRole("link", { name: "Tell us what happened", exact: true }).click();
    await page.getByRole("button", { name: "Money is gone", exact: true }).click();
    const current = page.getByRole('region', { name: 'Current question' });
    await current.getByRole('button', { name: 'I approved it after deception', exact: true }).click();
    for (const prompt of [/Is money still moving/, /remote access/, /Can someone else/, /Were access credentials exposed/]) {
      await current.getByRole('heading', { name: prompt }).waitFor();
      await current.getByRole('button', { name: 'No', exact: true }).click();
    }
    await current.getByRole('heading', { name: /Approximately when/ }).waitFor();
    await page.getByLabel('Approximate time', { exact: true }).fill('2026-10-01T12:00');
    await current.getByRole('button', { name: 'Save answer', exact: true }).click();
    await current.getByRole('button', { name: 'UPI', exact: true }).click();
    await current.getByRole('button', { name: 'Completed', exact: true }).click();
    await page.getByLabel('Amount', { exact: true }).fill(String(fixture.amount));
    await current.getByRole('button', { name: 'Save answer', exact: true }).click();
    await current.getByRole('heading', { name: /transaction reference/ }).waitFor();
    await current.getByRole('button', { name: 'Not sure', exact: true }).click();
    await current.getByRole('heading', { name: /safe supporting records/ }).waitFor();
    await current.getByRole('button', { name: 'Not sure', exact: true }).click();
    await current.getByRole('heading', { name: /answered the available questions/ }).waitFor();
    await page.getByRole('link', { name: 'Review reporting draft', exact: true }).click();
    await page.waitForURL(/\/incident\/[^/]+\/result/);
    const ident = page.url().split("/").at(-2);
    const actionPlan = await (await page.request.get(`${apiUrl}/api/v1/incidents/${ident}/action-plan`)).json();
    assert.ok(!("recovery_window" in actionPlan));
    assert.equal(actionPlan.playbook_id, "financial_scam_transfer");
    assert.ok(!actionPlan.actions.some(action => action.id === "bank_fraud_desk"));
    assert.ok(!(await page.locator("body").innerText()).includes("Recovery window:"));
    await page.getByRole("link", { name: "Go to evidence vault" }).click();
    await page.waitForURL(/\/evidence$/);
    await page.getByText("Demo environment — use synthetic data only.").waitFor();
    await page.locator('input[type="file"]').setInputFiles({
      name: fixture.file_name, mimeType: "image/png", buffer: Buffer.from(fixture.png_base64, "base64"),
    });
    await page.getByRole("radio", { name: "Payment screenshot", exact: true }).click();
    const uploadResponse = page.waitForResponse(r => r.url().endsWith("/evidence") && r.request().method() === "POST");
    await page.getByRole("button", { name: "Add evidence", exact: true }).click();
    const uploaded = await uploadResponse;
    assert.equal(uploaded.status(), fixture.expected.upload_status);
    const proof = await uploaded.json();
    await page.getByText("Extraction unavailable. You can enter these details yourself instead.").waitFor();
    // The original file must be served by the backend, not the frontend origin.
    const image = page.getByAltText("Preview of " + fixture.file_name, { exact: true });
    await image.waitFor();
    assert.ok((await image.getAttribute("src")).startsWith(apiUrl + "/"));
    await page.waitForFunction((alt) => {
      const image = Array.from(document.images).find(image => image.alt === alt);
      return image && image.complete && image.naturalWidth > 0;
    }, "Preview of " + fixture.file_name);
    await page.getByLabel("Amount", { exact: true }).fill(String(fixture.amount));
    await page.getByLabel("Transaction ID", { exact: true }).fill(fixture.transaction_id);
    const verifyResponse = page.waitForResponse(r => r.url().endsWith("/verify"));
    await page.getByRole("button", { name: "Confirm details", exact: true }).click();
    const verified = await verifyResponse;
    assert.equal((await verified.json()).evidence.verification_status, fixture.expected.verification_status);
    await page.getByRole("button", { name: "Close evidence details" }).click();
    await page.getByPlaceholder("In your own words…", { exact: true }).fill(fixture.description);
    const saved = page.waitForResponse(r => r.url().endsWith("/description"));
    await page.getByRole("button", { name: "Save description", exact: true }).click();
    assert.equal((await (await saved).json()).description, fixture.description);
    await page.getByLabel("Value", { exact: true }).fill(fixture.suspect_phone);
    await page.getByRole("button", { name: "Add another identifier" }).click();
    await page.getByText(fixture.suspect_phone, { exact: true }).waitFor();
    await page.getByRole("button", { name: "Add event", exact: true }).click();
    await page.getByLabel("When", { exact: true }).fill("2026-09-30T12:00");
    await page.getByLabel("What happened", { exact: true }).fill(fixture.timeline_description);
    await page.getByRole("button", { name: "Save event", exact: true }).click();
    await page.getByText(fixture.timeline_description, { exact: true }).waitFor();
    const summaryResponse = page.waitForResponse(r => r.url().endsWith("/generate-summary"));
    await page.getByRole("button", { name: "Generate incident summary" }).click();
    const summary = await (await summaryResponse).json();
    assert.equal(summary.provider, fixture.expected.summary_provider);
    assert.ok(summary.draft.includes(fixture.description));
    await page.reload();
    await page.getByText(fixture.suspect_phone, { exact: true }).waitFor();
    await page.getByText(fixture.timeline_description, { exact: true }).waitFor();
    assert.equal(await page.getByPlaceholder("In your own words…", { exact: true }).inputValue(), fixture.description);
    // Exercise deletion through the actual frontend request boundary.
    await page.getByRole("button", { name: "Remove Phone number " + fixture.suspect_phone }).click();
    await page.getByText(fixture.suspect_phone, { exact: true }).waitFor({ state: "detached" });
    // Browser-side API fetch verifies private original and final delete semantics.
    const removed = await page.evaluate(async ({ id, apiUrl }) => {
      const original = await fetch(apiUrl + "/api/v1/evidence/" + id + "/file", { credentials: "include" });
      const deleted = await fetch(apiUrl + "/api/v1/evidence/" + id, { method: "DELETE", credentials: "include" });
      return { original: original.status, size: (await original.arrayBuffer()).byteLength, deleted: deleted.status };
    }, { id: proof.id, apiUrl });
    assert.equal(removed.original, 200);
    assert.equal(removed.deleted, fixture.expected.delete_status);
    assert.ok(removed.size > 0);
    await page.reload();
    await page.getByText(fixture.file_name, { exact: true }).waitFor({ state: "detached" });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByText("Demo environment — use synthetic data only.").waitFor();
    assert.deepEqual(errors, []);
    console.log("PASS existing browser journey: conversation create/replies/actions → vault upload/private file → honest extraction failure/manual verify → description/suspect/timeline/template summary → reload persistence → delete; mobile page loaded. Incident:", ident);
  } catch (error) {
    console.error("Browser URL:", page.url());
    console.error((await page.locator("body").innerText()).slice(-4500));
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
