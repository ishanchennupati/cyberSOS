// Phase 3 real browser/API journey, intentionally without a provider key.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
const api = process.env.SMOKE_API_URL;
const web = process.env.SMOKE_FRONTEND_URL;

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.setDefaultTimeout(15000);
  try {
    await page.goto(web + '/incident/start');
    assert.equal(await page.getByRole('button', { name: 'Money is gone', exact: true }).count(), 1);
    const text = 'SBI nunchi call ani cheppi 35k GPay lo send cheyincharu. ' + 'Synthetic story. '.repeat(25);
    await page.getByLabel('What happened?', { exact: true }).fill(text);
    // Lost submission retains the original UUID/text for a safe retry.
    await page.route('**/conversation/turns', route => route.abort('failed'));
    await page.getByRole('button', { name: 'Continue with my story', exact: true }).click();
    await page.getByRole('button', { name: 'Retry unsaved reply' }).waitFor();
    await page.unroute('**/conversation/turns');
    await page.getByRole('button', { name: 'Retry unsaved reply' }).click();
    await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
    const id = page.url().split('/').at(-2);
    const endpoint = `${api}/api/v1/incidents/${id}/conversation`;
    const snapshot = async () => (await context.request.get(endpoint)).json();
    let state = await snapshot();
    assert.equal(state.turns[0].text, text);
    assert.equal(state.facts.kind, 'incident_understanding');
    assert.equal(state.facts.amount, null);
    assert.equal(state.turns[0].fact_changes.understanding.status, 'fallback');
    assert.equal(state.plan.plan.actions.length, 0);
    const current = page.getByRole('region', { name: 'Current question' });
    await page.getByRole('region', { name: 'Working understanding' }).getByText(/Automatic understanding is unavailable/).waitFor();
    assert.equal(await current.getByRole('heading').count(), 1);
    assert.equal(await page.getByText(state.pending_question.question, { exact: true }).count(), 1);
    assert.equal(await page.getByText(state.turns.at(-1).fact_changes.acknowledgement, { exact: true }).count(), 1);
    await current.getByRole('button', { name: 'Yes', exact: true }).click();
    await page.getByRole('link', { name: 'Call 1930', exact: true }).waitFor();
    state = await snapshot();
    assert.equal(state.facts.money_lost, true);
    assert.equal(state.facts.amount, null);
    await current.getByRole('button', { name: 'I approved it after deception' }).click();
    await current.getByRole('heading').getByText('Is money still moving or are you being asked to pay more?').waitFor();
    await page.getByLabel('Add to your story or correct a detail').fill('Sorry, it was ₹3,500.');
    await page.getByRole('button', { name: 'Send message', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('#incident-story')?.value === '');
    state = await snapshot();
    assert.equal(state.turns.at(-1).text, 'Sorry, it was ₹3,500.');
    assert.equal(state.facts.amount, null); // Failure never fakes a corrected amount.
    await page.reload();
    await current.getByRole('heading').waitFor();
    assert.deepEqual(await snapshot(), state);
    await page.setViewportSize({ width: 320, height: 760 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    // New no-money case can continue without financial-bank/1930 advice.
    await page.goto(web + '/incident/start');
    await page.getByLabel('What happened?', { exact: true }).fill('నా ఖాతాలోకి ఎవరో వచ్చారు. డబ్బు పోలేదు.');
    await page.getByRole('button', { name: 'Continue with my story', exact: true }).click();
    await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
    await current.getByRole('button', { name: 'No', exact: true }).click();
    await page.getByRole('region', { name: 'Applicable actions' }).locator('[data-action-group="PRESERVE"]').waitFor();
    assert.equal(await page.getByRole('link', { name: 'Call 1930', exact: true }).count(), 0);
    assert.deepEqual(errors, []);
    console.log('PASS Phase 3 story-first, multilingual input, honest fallback, retry, actions, reload and mobile');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
