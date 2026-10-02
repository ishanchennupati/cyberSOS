// Phase 3R: real browser/API/storage, scripted provider, no real key or user data.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    await page.goto(process.env.SMOKE_FRONTEND_URL + '/incident/start');
    await page.getByLabel('What happened?', { exact: true }).fill('₹5,000 left my account without my approval.');
    await page.getByRole('button', { name: 'Continue with my story' }).click();
    await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
    const endpoint = process.env.SMOKE_API_URL + '/api/v1/incidents/' + page.url().split('/').at(-2) + '/conversation';
    const snapshot = async () => (await context.request.get(endpoint)).json();
    let state = await snapshot();
    assert.equal(state.facts.authorization, 'unauthorized');
    assert.equal(state.facts.amount, '5000');
    assert.equal(state.pending_question, null);
    await page.getByRole('list', { name: 'Saved message history' }).getByText(/₹5,000 left and you did not approve/).waitFor();
    await page.getByText('Was the ₹5,000 debit shown as UPI, card, or something else?', { exact: true }).waitFor();
    assert.equal(await page.getByText(state.next_move.message, { exact: true }).count(), 1);
    assert.equal(await page.getByRole('region', { name: 'Current question' }).count(), 0);
    await page.getByRole('link', { name: 'Call 1930', exact: true }).waitFor();
    const composer = page.getByLabel('Add to your story or correct a detail');
    const send = async text => {
      await composer.fill(text);
      await page.getByRole('button', { name: 'Send message', exact: true }).click();
      await page.waitForFunction(() => document.querySelector('#incident-story')?.value === '');
      return snapshot();
    };
    state = await send('It happened about an hour ago.');
    assert.ok(state.facts.time_window.approximate);
    assert.equal(state.next_move.type, 'ACKNOWLEDGE_AND_WAIT');
    state = await send('Sorry, it was ₹4,500.');
    assert.equal(state.facts.amount, '4500');
    assert.equal(state.turns.at(-1).fact_changes.updates[0].before, '5000');
    state = await send('I also installed AnyDesk.');
    assert.ok(state.facts.signals.includes('device_compromise'));
    assert.equal(state.next_move.related_field, 'remote_access');
    await page.getByRole('button', { name: 'Not sure', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('button[disabled]') || [...document.querySelectorAll('[role="status"]')].some(el => el.textContent.includes('Saved.')));
    state = await snapshot();
    assert.equal(state.turns.at(-1).type, 'message');
    assert.equal(state.turns.at(-1).text, 'Not sure');
    state = await send('I have an SMS screenshot.');
    assert.equal(state.next_move.type, 'REQUEST_EVIDENCE');
    await page.getByRole('link', { name: 'Save optional safe evidence', exact: true }).waitFor();
    assert.ok(!state.next_move.message.includes('extract'));
    await page.reload();
    await composer.waitFor();
    assert.deepEqual(await snapshot(), state);
    await page.setViewportSize({ width: 320, height: 740 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.deepEqual(errors, []);
    for (const story of ['₹5,000 is gone from my account. I just got a message.', '5000 gone']) {
      await page.goto(process.env.SMOKE_FRONTEND_URL + '/incident/start');
      await page.getByLabel('What happened?', { exact: true }).fill(story);
      await page.getByRole('button', { name: 'Continue with my story' }).click();
      await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
      const url = process.env.SMOKE_API_URL + '/api/v1/incidents/' + page.url().split('/').at(-2) + '/conversation';
      const response = await (await context.request.get(url)).json();
      assert.equal(response.turns.at(-1).fact_changes.agent.status, 'decided');
      await page.getByText(response.next_move.message, { exact: true }).waitFor();
      assert.equal(await page.getByText(response.next_move.message, { exact: true }).count(), 1);
      await composer.waitFor();
      if (story === '5000 gone') {
        await page.getByRole('button', { name: 'I approved it after deception', exact: true }).waitFor();
        assert.equal(response.facts.currency, null);
        assert.ok(!response.turns.at(-1).fact_changes.acknowledgement.includes('account'));
      }
    }
    console.log('PASS FAKE PROVIDER browser: exact reproduction, visible conversation, persistent composer, actions, relative time, correction, device signal, natural quick reply, optional evidence, reload, 320px');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
