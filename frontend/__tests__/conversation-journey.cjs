// Synthetic Phase 2 journey against disposable real API/database/browser servers.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
const api = process.env.SMOKE_API_URL || 'http://localhost:8000';
const web = process.env.SMOKE_FRONTEND_URL || 'http://localhost:3001';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    await page.goto(web);
    await page.getByRole('link', { name: 'Tell us what happened' }).click();
    // Creation succeeds but the shortcut save fails. Recovery must yield a resumable URL.
    await page.route('**/conversation/turns', route => route.abort('failed'));
    await page.getByRole('button', { name: 'Money is gone', exact: true }).click();
    await page.getByRole('button', { name: 'Retry unsaved reply' }).waitFor();
    await page.unroute('**/conversation/turns');
    await page.getByRole('button', { name: 'Retry unsaved reply' }).click();
    await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
    const id = page.url().split('/').at(-2);
    const endpoint = `${api}/api/v1/incidents/${id}/conversation`;
    const question = page.getByRole('region', { name: 'Current question' });
    const snapshot = async () => (await context.request.get(endpoint)).json();
    await page.getByRole('link', { name: 'Call 1930', exact: true }).waitFor();
    let state = await snapshot();
    assert.equal(state.facts.amount, null);
    assert.equal(state.facts.transaction_id, null);
    assert.equal(state.turns[0].type, 'shortcut');
    assert.equal(state.pending_question.field, 'authorization');
    assert.equal(await question.getByRole('heading').count(), 1);
    const panel = page.getByRole('region', { name: 'Applicable actions' });
    const actNow = panel.getByRole('region', { name: 'ACT NOW', exact: true });
    const assertActions = async (state) => {
      const ordered = [...state.plan.plan.actions].sort((a, b) => a.order - b.order);
      const urgent = ordered.filter(a => a.phase === 'CONTAIN' || (a.phase === 'REPORT' && a.critical));
      const groups = [
        ['ACT NOW', urgent],
        ['PRESERVE', ordered.filter(a => a.phase === 'PRESERVE')],
        ['REPORT', ordered.filter(a => a.phase === 'REPORT' && !a.critical)],
        ['FOLLOW THROUGH', ordered.filter(a => a.phase === 'FOLLOW_UP')],
      ].filter(([, items]) => items.length);
      assert.deepEqual(await panel.locator('[data-action-group]').evaluateAll(nodes => nodes.map(node => node.dataset.actionGroup)), groups.map(([title]) => title));
      for (const [title, items] of groups) {
        assert.deepEqual(await panel.locator(`[data-action-group="${title}"] [data-action-id]`).evaluateAll(nodes => nodes.map(node => node.dataset.actionId)), items.map(a => a.id));
      }
      if (state.pending_question) assert.equal(await question.evaluate(node => node.classList.contains('bg-calm-soft') || node.classList.contains('border-calm')), false, 'Unanswered question does not use success styling');
      assert.deepEqual(await actNow.locator('[data-action-id]').evaluateAll(nodes => nodes.map(node => node.dataset.actionId)), urgent.map(a => a.id));
      assert.deepEqual(await panel.locator('[data-action-id]').evaluateAll(nodes => nodes.map(node => node.dataset.actionId).sort()), ordered.map(a => a.id).sort());
      assert.deepEqual(await actNow.locator('[data-action-order]').evaluateAll(nodes => nodes.map(node => Number(node.dataset.actionOrder))), urgent.map(a => a.order));
      assert.equal(await page.getByRole('region', { name: 'Incident conversation' }).locator('[data-action-id]').count(), 0);
    };
    await assertActions(state);
    const banner = await actNow.getByRole('heading', { name: 'ACT NOW', exact: true }).boundingBox();
    assert.ok(banner && banner.y >= 0 && banner.y < 844, 'ACT NOW is visible on initial mobile screen');
    assert.ok((await page.getByRole('status', { name: 'Action updates' }).innerText()).includes('ACT NOW'));
    if (process.env.SMOKE_SCREENSHOT_DIR) {
      require('node:fs').mkdirSync(process.env.SMOKE_SCREENSHOT_DIR, { recursive: true });
      await page.screenshot({ path: require('node:path').join(process.env.SMOKE_SCREENSHOT_DIR, 'phase2-mobile-actions.png') });
      await page.setViewportSize({ width: 1280, height: 900 });
      await page.screenshot({ path: require('node:path').join(process.env.SMOKE_SCREENSHOT_DIR, 'phase2-desktop-question.png') });
      await page.setViewportSize({ width: 390, height: 844 });
    }
    // Mobile actions precede the question and remain reachable by sticky keyboard links.
    assert.equal(await panel.evaluate(node => !!(node.compareDocumentPosition(document.getElementById('current-question')) & Node.DOCUMENT_POSITION_FOLLOWING)), true);
    // Keyboard quick reply and focus move to the next question.
    await question.getByRole('button', { name: 'I approved it after deception', exact: true }).focus();
    await page.keyboard.press('Enter');
    await question.getByRole('heading', { name: /Is money still moving/ }).waitFor();
    assert.equal(await page.evaluate(() => document.activeElement.tagName), 'H2');
    await question.getByRole('button', { name: 'Not sure', exact: true }).click();
    await question.getByRole('heading', { name: /remote access/ }).waitFor();
    state = await snapshot();
    assert.equal(state.facts.ongoing_loss, null);
    await assertActions(state);
    const mobileActions = page.getByRole('navigation', { name: 'Conversation shortcuts' });

    await mobileActions.getByRole('link', { name: /actions? to take now/ }).focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'act-now-heading');
    await mobileActions.getByRole('link', { name: 'Continue conversation', exact: true }).click();
    assert.equal(await page.evaluate(() => document.activeElement.closest('section')?.id), 'current-question');
    await page.waitForFunction(() => {
      const question = document.querySelector('#current-question h2').getBoundingClientRect();
      const nav = document.querySelector('[aria-label="Conversation shortcuts"]').getBoundingClientRect();
      return question.top >= nav.bottom && question.top < innerHeight;
    });
    if (process.env.SMOKE_SCREENSHOT_DIR) await page.screenshot({ path: require('node:path').join(process.env.SMOKE_SCREENSHOT_DIR, 'phase2-mobile-question.png') });

    // Failure is visible; retry retains the exact turn ID.
    let rejected;
    await page.route('**/conversation/turns', async route => {
      rejected = route.request().postDataJSON();
      await route.abort('failed');
    });
    await question.getByRole('button', { name: 'No', exact: true }).click();
    await page.getByRole('button', { name: 'Retry unsaved reply' }).waitFor();
    assert.ok((await page.getByRole('alert').filter({ hasText: /not been confirmed saved/ }).innerText()).includes('not been confirmed saved'));
    assert.equal((await snapshot()).revision, state.revision);
    await page.unroute('**/conversation/turns');
    const retried = page.waitForRequest(r => r.url().endsWith('/conversation/turns'));
    await page.getByRole('button', { name: 'Retry unsaved reply' }).click();
    assert.equal((await retried).postDataJSON().turn_id, rejected.turn_id);
    await question.getByRole('heading', { name: /Can someone else/ }).waitFor();
    // Reply accepted but response lost: retry must not append another turn.
    let committed;
    await page.route('**/conversation/turns', async route => {
      committed = route.request().postDataJSON();
      await route.fetch();
      await route.abort('failed');
    });
    await question.getByRole('button', { name: 'No', exact: true }).click();
    await page.getByRole('button', { name: 'Retry unsaved reply' }).waitFor();
    const afterCommit = await snapshot();
    await page.unroute('**/conversation/turns');
    await page.getByRole('button', { name: 'Retry unsaved reply' }).click();
    await question.getByRole('heading', { name: /Were access credentials exposed/ }).waitFor();
    assert.equal((await snapshot()).turns.length, afterCommit.turns.length);
    assert.equal(afterCommit.turns.at(-1).id, committed.turn_id);
    // Another tab advances the state. This tab must reject its stale reply.
    const other = await context.newPage();
    await other.goto(page.url());
    await other.getByRole('region', { name: 'Current question' }).getByRole('button', { name: 'No', exact: true }).click();
    await other.getByRole('region', { name: 'Current question' }).getByRole('heading', { name: /Approximately when/ }).waitFor();
    await question.getByRole('button', { name: 'Yes', exact: true }).click();
    await page.getByText(/Review the latest conversation before sending/).waitFor();
    assert.equal((await snapshot()).facts.credentials_exposed, false);
    await page.getByRole('button', { name: 'Discard unsaved reply and review' }).click();
    await question.getByRole('button', { name: 'Not sure', exact: true }).click();
    await question.getByRole('heading', { name: /How was the payment made/ }).waitFor();
    await question.getByRole('button', { name: 'UPI', exact: true }).click();
    await question.getByRole('heading', { name: /pending or completed/ }).waitFor();
    await question.getByRole('button', { name: 'Completed', exact: true }).click();
    await question.getByRole('heading', { name: /What amount/ }).waitFor();
    await assertActions(await snapshot());
    await question.getByText('Answer with an optional field', { exact: true }).click();
    await page.getByLabel('Amount', { exact: true }).fill('2500');
    const beforeStaleAmount = await snapshot();
    const savedElsewhere = await context.request.post(endpoint + '/turns', { data: {
      turn_id: require('node:crypto').randomUUID(), expected_revision: beforeStaleAmount.revision,
      type: 'answer', field: beforeStaleAmount.pending_question.field, value: '2500',
    } });
    assert.equal(savedElsewhere.status(), 200);
    // Stale text must never carry over from amount to transaction reference.
    await question.getByRole('button', { name: 'Save answer' }).click();
    await page.getByText(/Review the latest conversation before sending/).waitFor();
    await page.getByRole('button', { name: 'Discard unsaved reply and review' }).click();
    await question.getByRole('heading', { name: /transaction reference/ }).waitFor();
    assert.equal(await page.getByLabel('Transaction reference', { exact: true }).inputValue(), '');
    await question.getByRole('button', { name: 'Not sure', exact: true }).click();
    await question.getByRole('heading', { name: /safe supporting records/ }).waitFor();
    await question.getByRole('button', { name: 'Not sure', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('[aria-label="Current question"]'));
    await page.getByLabel('Add to your story or correct a detail').waitFor();
    const completionSaved = page.waitForResponse(r => r.url().endsWith('/conversation/turns') && r.request().method() === 'POST');
    const completionButton = page.getByRole('button', { name: 'Mark done: Call 1930 to report financial cyber fraud', exact: true });
    await completionButton.focus();
    await page.keyboard.press('Enter');
    assert.equal((await completionSaved).status(), 200);
    await page.getByRole('status').filter({ hasText: /Saved/ }).waitFor();
    assert.equal(await page.evaluate(() => document.activeElement.getAttribute('aria-pressed')), 'true', 'Completion retains focus on its control');
    await page.locator('summary').filter({ hasText: 'Review or correct your answers' }).click();
    await page.getByRole('button', { name: 'Edit payment approval', exact: true }).click();
    await question.getByRole('button', { name: 'I did not approve it', exact: true }).click();
    await page.getByRole('heading', { name: 'Report the unauthorized transaction to your bank', exact: true }).waitFor();
    state = await snapshot();
    assert.equal(state.pending_question, null);
    assert.equal(state.completions[0].completed, true);
    assert.equal(state.facts.amount, '2500');
    assert.equal(state.turns.at(-1).fact_changes.before, 'authorized');
    await assertActions(state);
    await page.reload();
    await page.getByLabel('Add to your story or correct a detail').waitFor();
    assert.equal(await page.getByRole('button', { name: 'Mark not done: Call 1930 to report financial cyber fraud', exact: true }).getAttribute('aria-pressed'), 'true');
    assert.deepEqual(await snapshot(), state);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await assertActions(state);
    // A 320px viewport still has one usable column and an accessible active question.
    await page.setViewportSize({ width: 320, height: 740 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await mobileActions.getByRole('link', { name: 'Continue conversation', exact: true }).click();
    const questionBox = await page.getByRole('region', { name: 'Incident conversation' }).boundingBox();
    assert.ok(questionBox && questionBox.width <= 320);
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    const panelBox = await panel.boundingBox();
    const desktopQuestion = await page.getByRole('region', { name: 'Incident conversation' }).boundingBox();
    assert.ok(panelBox.x > desktopQuestion.x && Math.abs(panelBox.y - desktopQuestion.y) < 4);
    assert.equal(await panel.evaluate(node => getComputedStyle(node).position), 'sticky');
    if (process.env.SMOKE_SCREENSHOT_DIR) await page.screenshot({ path: require('node:path').join(process.env.SMOKE_SCREENSHOT_DIR, 'phase2-desktop-actions.png') });
    await page.getByRole('link', { name: 'Review reporting draft', exact: true }).click();
    await page.getByRole('link', { name: 'Edit answers', exact: true }).click();
    await page.waitForURL(new RegExp(`/incident/${id}/conversation$`));
    await page.getByLabel('Add to your story or correct a detail').waitFor();
    const outsider = await browser.newContext();
    assert.equal((await outsider.request.get(endpoint)).status(), 404);
    assert.equal((await outsider.request.post(endpoint + '/turns', { data: rejected })).status(), 404);
    await outsider.close();
    assert.deepEqual(errors, []);
    console.log('PASS Phase 2: ACT NOW / server action order / distinct question / sticky mobile controls / action announcements / completion focus / early actions / keyboard / unknown / disconnect / retry / lost response / stale tab / progression / correction / refresh / 320px mobile / desktop panel / authority');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
