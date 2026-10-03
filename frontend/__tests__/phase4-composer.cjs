const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || 'playwright');
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const width of [390, 1280]) {
      const page = await browser.newPage({viewport:{width,height:844}});
      await page.goto('http://localhost:3000/incident/start');
      const composer = page.getByRole('textbox', {name:'Message CyberSOS'});
      await composer.waitFor();
      assert.equal(await page.getByRole('button',{name:'Send message',exact:true}).isEnabled(),false);
      await composer.fill('A synthetic story');
      let first;
      await page.route('**/conversation/turns', route => { first=route.request().postDataJSON(); return route.abort(); });
      await page.getByRole('button',{name:'Send message',exact:true}).click();
      await page.getByRole('button',{name:'Retry message'}).waitFor();
      assert.equal(first.text,'A synthetic story');
      assert.equal(await composer.inputValue(),'A synthetic story');
      const rect = await composer.boundingBox();
      assert.ok(rect.y + rect.height < 844);
      assert.equal(await page.getByRole('button',{name:/microphone|voice/i}).count(),0);
      await page.close();
    }
    console.log('PASS: desktop/mobile direct composer, single first Send, failure draft retention; no AI calls');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode=1;});
