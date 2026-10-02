// Explicit live opt-in: multiple natural turns through browser/API/Gemini/storage.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
(async () => {
  assert.equal(process.env.SMOKE_LIVE_AI, '1');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  page.setDefaultTimeout(70000);
  const errors = [];
  page.on('pageerror', e => errors.push(e.name));
  try {
    const story = 'Someone deceived me. I sent ₹5,000 using net banking.';
    await page.goto(process.env.SMOKE_FRONTEND_URL + '/incident/start');
    await page.getByLabel('What happened?', { exact: true }).fill(story);
    await page.getByRole('button', { name: 'Continue with my story' }).click();
    await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
    const endpoint = process.env.SMOKE_API_URL + '/api/v1/incidents/' + page.url().split('/').at(-2) + '/conversation';
    const snapshot = async () => (await context.request.get(endpoint)).json();
    const composer = page.getByLabel('Add to your story or correct a detail');
    async function check(state) {
      const changes = state.turns.at(-1).fact_changes;
      assert.equal(changes.understanding.status, 'understood');
      assert.equal(changes.agent.status, 'decided', JSON.stringify(changes.agent));
      assert.equal(state.facts.payment_method, 'net_banking');
      assert.ok(state.next_move);
      assert.notEqual(state.next_move.related_field, 'payment_method');
      assert.ok(!changes.unresolved_candidates.some(c => c.field === 'payment_method'));
      const history = page.getByRole('list', { name: 'Saved message history' });
      // Each turn owns one assistant move; repeated supportive copy may be historical.
      await history.locator(':scope > li').last().getByText(state.next_move.message, { exact: true }).waitFor();
      assert.equal(await history.locator(':scope > li').last().getByText(state.next_move.message, { exact: true }).count(), 1);
      assert.ok(await composer.isEnabled());
      console.log(JSON.stringify({ revision: state.revision, extraction: changes.understanding.status,
        agent: changes.agent.status, move: state.next_move.type, field: state.next_move.related_field,
        payment_method: state.facts.payment_method, amount: state.facts.amount }));
    }
    let state = await snapshot();
    await check(state);
    assert.equal(state.facts.authorization, 'authorized');
    for (const text of [
      'No more money has left my account since then.',
      'Nobody else currently has access to my device or account.',
      'I have saved the transaction receipt.',
      'Sorry, the amount was ₹4,500.',
      'I need a moment to check my records.',
    ]) {
      await composer.fill(text);
      const response = page.waitForResponse(r => r.url() === endpoint + '/turns' && r.request().method() === 'POST');
      await page.getByRole('button', { name: 'Send message', exact: true }).click();
      const saved = await response;
      assert.equal(saved.status(), 200);
      state = await saved.json();
      await check(state);
    }
    assert.equal(state.facts.amount, '4500');
    assert.equal(state.turns[0].text, story);
    await page.reload();
    await composer.waitFor();
    assert.deepEqual(await snapshot(), state);
    assert.deepEqual(errors, []);
    console.log('LIVE GEMINI six-turn payment browser PASS');
  } finally { await browser.close(); }
})().catch(e => { console.error(e.name + ': ' + e.message); process.exitCode = 1; });
