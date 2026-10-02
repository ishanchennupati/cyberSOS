// Real browser error events and the shared API boundary; synthetic input only.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const captured = [];
    page.on('console', message => {
      if (message.text().startsWith('[CyberSOS diagnostic]')) {
        captured.push(Promise.all(message.args().map(arg => arg.jsonValue())));
      }
    });
    await page.goto(process.env.SMOKE_FRONTEND_URL + '/incident/start');
    await page.getByLabel('What happened?', { exact: true }).fill('Synthetic private story');
    await page.route('**/api/v1/incidents', async route => {
      const requestId = route.request().headers()['x-request-id'];
      assert.match(requestId, /^[a-f0-9-]{36}$/);
      await route.fulfill({ status: 503, contentType: 'application/json',
        headers: { 'X-Request-ID': requestId, 'Access-Control-Expose-Headers': 'X-Request-ID' },
        body: JSON.stringify({ detail: 'Temporary synthetic failure' }) });
    });
    await page.getByRole('button', { name: 'Continue with my story' }).click();
    await page.getByRole('alert').waitFor();
    await page.evaluate(() => {
      window.dispatchEvent(new ErrorEvent('error', { message: 'synthetic-private-secret', lineno: 42 }));
      window.dispatchEvent(new PromiseRejectionEvent('unhandledrejection', {
        promise: Promise.resolve(), reason: 'synthetic-private-secret' }));
    });
    const entries = (await Promise.all(captured)).map(args => args[1]);
    assert.ok(entries.some(e => e.category === 'HTTP_ERROR' && e.status === 503 && e.requestId));
    assert.ok(entries.some(e => e.category === 'RUNTIME_ERROR' && e.line === 42));
    assert.ok(entries.some(e => e.category === 'UNHANDLED_REJECTION'));
    assert.ok(!JSON.stringify(entries).includes('synthetic-private'));
    console.log('Browser HTTP/runtime/rejection diagnostics PASS');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
