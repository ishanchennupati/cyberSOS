const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
const id = '11111111-1111-4111-8111-111111111111';
const state = {
  incident_id: id, revision: 20, version: '1.0', answered: [], facts: {}, pending_question: null,
  next_move: null, completions: [], memory: {},
  turns: Array.from({length:20}, (_, i) => ({id: String(i), text: `Synthetic message ${i}.`,
    attachments: [], fact_changes: {acknowledgement: `Synthetic reply ${i}. ` + 'Conversation text. '.repeat(8)}})),
  plan: {plan: {actions: [{id: 'synthetic-action', phase: 'CONTAIN', priority:'high', order:1,
    critical:true, title:'Synthetic action for layout testing', instruction:'Synthetic layout text only.',
    why:'Synthetic reason.', can_mark_complete:true}]}},
  projection: {reference: 'SYNTHETIC', revision:20, status:'Draft', working_understanding:[],
    known_facts: Object.fromEntries(Array.from({length:30}, (_,i)=>[`synthetic_field_${i}`, {value:'Synthetic value', verified:true}])),
    evidence_count:0, completed_actions:0},
};

(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const width of [1280, 390]) {
      const page = await browser.newPage({viewport:{width,height:900}});
      await page.route('**/api/v1/incidents/*/conversation', route => route.fulfill({json: state}));
      await page.goto((process.env.SMOKE_FRONTEND_URL || 'http://localhost:3000') + `/incident/${id}/conversation`);
      const action = page.getByRole('heading',{name:'Synthetic action for layout testing', exact:true});
      await action.waitFor();
      const viewport = page.locator('section[aria-label="Incident conversation"] > div').first();
      await viewport.evaluate(el => el.scrollTop = el.scrollHeight);
      await page.waitForTimeout(300);
      const before = await viewport.evaluate(el => el.scrollTop);
      const rect = await action.boundingBox();
      await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2);
      await page.mouse.wheel(0,-350);
      await page.waitForTimeout(350);
      assert.ok(await viewport.evaluate(el=>el.scrollTop) < before - 100,
        `Wheel over the action card must scroll conversation at width ${width}`);
      const historyBefore = await viewport.evaluate(el=>el.scrollTop);
      const viewRect = await viewport.boundingBox();
      await page.mouse.move(viewRect.x + viewRect.width / 2, viewRect.y + 40);
      await page.mouse.wheel(0,-300);
      await page.waitForTimeout(350);
      assert.ok(await viewport.evaluate(el=>el.scrollTop) < historyBefore - 100, 'Wheel over messages must scroll');
      const composer = page.getByRole('textbox',{name:'Message CyberSOS'});
      await composer.fill('Preserved synthetic draft');
      await page.getByRole('button',{name:'View case',exact:true}).click();
      const details = page.getByRole('complementary',{name:'Current case details'});
      await details.waitFor();
      await details.evaluate(el => el.scrollTop = 0);
      const detailRect = await details.boundingBox();
      await page.mouse.move(detailRect.x + detailRect.width / 2, detailRect.y + detailRect.height / 2);
      await page.mouse.wheel(0,300);
      await page.waitForTimeout(350);
      assert.ok(await details.evaluate(el=>el.scrollTop) > 100, 'Case details must retain their own scrolling');
      assert.equal(await composer.inputValue(),'Preserved synthetic draft');
      const composerRect = await composer.boundingBox();
      assert.ok(composerRect.y >= 0 && composerRect.y + composerRect.height <= 900, 'Composer must stay visible');
      await page.close();
    }
    console.log('PASS: desktop/mobile wheel over messages and action cards; detail scrolling and visible draft preserved. Mock case data; no AI calls.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
