// Actual development assets and click handlers; intercept turns before AI use.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const shortcut of [false, true]) {
      const context = await browser.newContext();
      const page = await context.newPage();
      const errors = [];
      const failedScripts = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('requestfailed', request => {
        if (request.resourceType() === 'script') failedScripts.push(request.url());
      });
      let resolveTurn;
      const turn = new Promise(resolve => { resolveTurn = resolve; });
      await page.route('**/conversation/turns', async route => {
        resolveTurn(route.request().postDataJSON());
        await route.abort('failed');
      });
      await page.goto('http://localhost:3000/incident/start', { waitUntil: 'networkidle' });
      const story = '\u20b95,000 gone + message';
      if (shortcut) {
        await page.getByRole('button', { name: 'Money is gone', exact: true }).click();
      } else {
        await page.getByLabel('What happened?', { exact: true }).fill(story);
        await page.getByRole('button', { name: 'Continue with my story', exact: true }).click();
      }
      const payload = await Promise.race([turn, new Promise((_, reject) => {
        const timeout = setTimeout(() => reject(new Error('Click did not reach conversation API')), 15000);
        timeout.unref();
      })]);
      assert.equal(payload.type, shortcut ? 'shortcut' : 'message');
      assert.equal(shortcut ? payload.value : payload.text, shortcut ? 'money_gone' : story);
      assert.deepEqual(errors, []);
      assert.deepEqual(failedScripts, []);
      console.log(shortcut ? 'PASS: shortcut click reaches API' : 'PASS: typing enables story submission and click reaches API');
      await context.close();
    }
    console.log('PASS: development JavaScript loads; no Gemini calls made');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
