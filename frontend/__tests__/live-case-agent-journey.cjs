// Explicit live opt-in only; actual browser -> API -> Gemini -> validation -> UI.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
const cases = [
  ['B', '₹5,000 is gone from my account. I just got a message.'],
  ['A', '₹5,000 left my account without my approval.'],
  ['C', 'Someone claiming to be from SBI made me send ₹35,000 through GPay.'],
  ['D', 'They made me install AnyDesk and then money disappeared.'],
].filter(([label]) => !process.env.SMOKE_LIVE_CASES || process.env.SMOKE_LIVE_CASES.split(',').includes(label));
(async () => {
  assert.equal(process.env.SMOKE_LIVE_AI, '1', 'Live calls require explicit opt-in');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  page.setDefaultTimeout(70000);
  const results = [];
  try {
    for (const [label, story] of cases) {
      await page.goto(process.env.SMOKE_FRONTEND_URL + '/incident/start');
      await page.getByLabel('What happened?', { exact: true }).fill(story);
      await page.getByRole('button', { name: 'Continue with my story' }).click();
      await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
      const endpoint = process.env.SMOKE_API_URL + '/api/v1/incidents/' + page.url().split('/').at(-2) + '/conversation';
      const state = await (await context.request.get(endpoint)).json();
      const changes = state.turns.at(-1).fact_changes;
      const history = page.getByRole('list', { name: 'Saved message history' });
      await history.getByText(story, { exact: true }).waitFor();
      const interaction = state.next_move?.message || state.pending_question?.question;
      if (interaction) await history.getByText(interaction, { exact: true }).waitFor();
      await page.getByLabel('Add to your story or correct a detail').waitFor();
      const fields = ['kind', 'money_lost', 'amount', 'currency', 'authorization', 'payment_method',
        'payment_app', 'claimed_organization', 'transaction_id', 'occurred_at', 'signals'];
      const result = { case: label, story,
        extraction: Object.fromEntries(['status', 'provider', 'model', 'provider_initialized',
          'invocation_succeeded', 'parsing_succeeded', 'category', 'reason', 'http_status'].map(k => [k, changes.understanding[k] ?? null])),
        candidates: changes.understanding.candidates.map(({field, value, source_text, status}) => ({field, value, source_text, status})),
        facts: Object.fromEntries(fields.map(k => [k, state.facts[k]])), agent: changes.agent,
        next_move: state.next_move, fallback_question: state.pending_question,
        acknowledgement: changes.acknowledgement,
        action_ids: state.plan.plan.actions.map(a => a.id),
        rendered_once: !interaction || await history.getByText(interaction, { exact: true }).count() === 1,
        composer_enabled: await page.getByLabel('Add to your story or correct a detail').isEnabled(),
      };
      result.accepted_live_move = changes.understanding.status === 'understood' && changes.agent.status === 'decided' && !!state.next_move;
      if (label === 'A') result.explicit_facts_correct = state.facts.money_lost === true && state.facts.amount === '5000' && state.facts.currency === 'INR' && state.facts.authorization === 'unauthorized';
      if (label === 'C') {
        result.no_bank_or_rail_invention = !('victim_bank' in state.facts) && state.facts.payment_method === 'unknown';
        result.scam_facts_correct = state.facts.money_lost === true && state.facts.amount === '35000'
          && state.facts.currency === 'INR' && state.facts.authorization === 'authorized'
          && state.facts.claimed_organization === 'SBI' && state.facts.payment_app === 'GPay';
      }
      if (label === 'D') result.multiple_signals = ['financial', 'device_compromise'].every(s => state.facts.signals.includes(s));
      results.push(result);
      console.log(JSON.stringify(result));
      const directory = path.resolve('../backend/tmp');
      fs.mkdirSync(directory, { recursive: true });
      await page.screenshot({ path: path.join(directory, 'phase3r-live-' + label + '.png'), fullPage: true });
    }
    const directory = path.resolve('../backend/tmp');
    fs.writeFileSync(path.join(directory, 'phase3r-live-result.json'), JSON.stringify(results, null, 2));
    assert.ok(results.every(r => r.accepted_live_move && r.rendered_once && r.composer_enabled), 'Live extraction + next move + validation + rendering must all succeed');
    if (results.some(r => r.case === 'A')) assert.ok(results.find(r => r.case === 'A').explicit_facts_correct);
    if (results.some(r => r.case === 'C')) assert.ok(results.find(r => r.case === 'C').no_bank_or_rail_invention);
    if (results.some(r => r.case === 'C')) assert.ok(results.find(r => r.case === 'C').scam_facts_correct, 'Scam payment facts must survive source validation');
    if (results.some(r => r.case === 'D')) assert.ok(results.find(r => r.case === 'D').multiple_signals);
    console.log('LIVE GEMINI browser ' + results.map(r => r.case).join(',') + ' PASS');
  } finally { await browser.close(); }
})().catch(error => { console.error(error.name + ': ' + error.message); process.exitCode = 1; });
