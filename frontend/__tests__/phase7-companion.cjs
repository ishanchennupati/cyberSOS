const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
const fs=require('node:fs');
const base=process.env.SMOKE_FRONTEND_URL||'http://localhost:3001',api=process.env.SMOKE_API_URL||'http://localhost:8001';
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const desktop of [false,true]){
   const context=await browser.newContext({viewport:desktop?{width:1280,height:900}:{width:390,height:844}});
   const page=await context.newPage();page.setDefaultTimeout(30000);
   for(const [index,fixture] of [
    {route:'Women/Children Related Crime',story:'Someone on Instagram is threatening to share my private photos.'},
    {route:'Financial Fraud',story:'A scammer made me send INR 35000 via UPI today.'},
    {route:'Other Cyber Crime',story:'Someone still has access to my Google account.'},
   ].entries()){
    await page.goto(base+'/incident/start');
    await page.getByRole('button',{name:fixture.route,exact:true}).click();
    await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
    const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
    async function send(text){await composer.fill(text);const done=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');await page.getByRole('button',{name:'Send message',exact:true}).click();const response=await done;assert.equal(response.status(),200);await page.waitForFunction(()=>document.querySelector('#chat-message')?.value==='');return response.json();}
    let state=await send(fixture.story),id=state.incident_id;
    assert.equal(state.next_move.type,'REQUEST_EVIDENCE');
    state=await send('Yes');assert.equal(state.projection.companion.evidence_offer,'accepted');assert.equal(state.facts.evidence_available,null);
    state=await send('I have no more useful details.');assert.equal(state.projection.companion.presented,true);assert.equal(state.understanding_review.reviewed,false);
    const outcome=page.getByRole('region',{name:'Current personalized outcome'});await outcome.waitFor();
    await outcome.getByRole('heading',{name:'Draft CyberSOS case sheet',exact:true}).waitFor();
    const previous=state;state=await send('Thanks.');assert.equal(state.pending_question,null);assert.equal(state.next_move?.message.includes('?'),false);
    await composer.fill('A draft that survives opening my case.');await page.getByRole('button',{name:'View case',exact:true}).click();
    const panel=page.getByRole('complementary',{name:'Current case details'});
    await panel.getByRole('heading',{name:'Your continuing case'}).waitFor();assert.equal(await composer.inputValue(),'A draft that survives opening my case.');
    const box=await composer.boundingBox();assert.ok(box&&box.y>=0&&box.y+box.height<=(desktop?900:844));
    await panel.getByText('Add a note or external reference',{exact:true}).click();
    await panel.getByLabel('Record type').selectOption('reference');await panel.getByLabel('Note or reference').fill('SYNTHETIC-REF-123');await panel.getByLabel('Organization, if relevant').fill('Platform');
    const saved=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Save record',exact:true}).click();assert.equal((await saved).status(),200);
    await panel.getByRole('button',{name:'Generate private recovery code'}).click();
    let code=await panel.getByLabel('New recovery code').innerText();assert.ok(code.length>30);
    // The same guest must prove both case authority and email ownership before linking.
    await panel.getByLabel('Email you securely control').fill(`synthetic-${desktop}-${index}@example.test`);
    const mailed=page.waitForResponse(r=>r.url().endsWith('/auth/email'));await panel.getByRole('button',{name:'Send sign-in link',exact:true}).click();assert.equal((await mailed).status(),202);
    const token=(await (await context.request.get(api+'/__phase7/mail')).json()).token;
    const tab=await context.newPage();await tab.goto(base+'/return#token='+token);await tab.getByRole('button',{name:'Confirm email sign-in'}).click();await tab.getByText('Signed in as',{exact:false}).waitFor();
    assert.equal(await tab.getByRole('link',{name:new RegExp(id.slice(0,8))}).count(),0);
    await panel.getByRole('button',{name:'I verified my email · refresh'}).click();
    if(index===0){
      assert.equal((await context.request.post(api+`/api/v1/__phase7/${id}/age-verification`)).status(),200);
      await panel.getByRole('button',{name:'I verified my email · refresh'}).click();
      await panel.getByText('Verify your safe email again to save another case or change recovery access. Your chat and draft stay here.',{exact:true}).waitFor();
      await panel.getByRole('button',{name:'Verify my email again',exact:true}).click();
      await panel.getByRole('status').filter({hasText:'If delivery is available'}).waitFor();
      const fresh=(await (await context.request.get(api+'/__phase7/mail')).json()).token;
      await tab.goto(base+'/return#token='+fresh);await tab.getByRole('button',{name:'Confirm email sign-in'}).click();
      await tab.getByText('Signed in as',{exact:false}).waitFor();
      await panel.getByRole('button',{name:'I verified my email · refresh'}).click();
      assert.equal(await composer.inputValue(),'A draft that survives opening my case.');
    }
    await panel.getByRole('button',{name:'Save this case',exact:true}).click();await panel.getByText('This case is saved to your verified email.',{exact:true}).waitFor();
    await tab.reload();await tab.getByRole('link',{name:new RegExp(id.slice(0,8))}).waitFor();await tab.close();
    const expected=await (await context.request.get(api+`/api/v1/incidents/${id}/conversation`)).json();
    assert.equal((await context.request.post(api+`/api/v1/__phase7/${id}/expire`)).status(),200);
    assert.equal((await context.request.get(api+`/api/v1/incidents/${id}/conversation`)).status(),404);
    if(index===0){
      await page.reload();const expired=page.getByRole('alert');await expired.getByText('Return using a saved recovery code',{exact:true}).click();
      await expired.getByLabel('Private recovery code',{exact:true}).fill(code);await expired.getByRole('button',{name:'Recover this case',exact:true}).click();
      await expired.getByLabel('New recovery code').waitFor();code=await expired.getByLabel('New recovery code').innerText();
      assert.equal(await composer.inputValue(),'A draft that survives opening my case.');
      await expired.getByRole('button',{name:'Continue conversation',exact:true}).click();await page.getByRole('button',{name:'View case',exact:true}).waitFor();
    }
    const other=await browser.newContext({viewport:{width:390,height:844}}),returnPage=await other.newPage();
    await returnPage.goto(base+'/return');await returnPage.getByText('Return using a saved recovery code',{exact:true}).click();
    await returnPage.getByLabel('Case reference',{exact:true}).fill(id);await returnPage.getByLabel('Private recovery code',{exact:true}).fill(code);
    await returnPage.getByRole('button',{name:'Recover this case',exact:true}).click();await returnPage.getByLabel('New recovery code').waitFor();
    assert.notEqual(await returnPage.getByLabel('New recovery code').innerText(),code);
    await returnPage.getByRole('link',{name:'Continue this case'}).click();await returnPage.getByRole('button',{name:'View case',exact:true}).click();
    const restored=await (await other.request.get(api+`/api/v1/incidents/${id}/conversation`)).json();assert.deepEqual(restored.facts,expected.facts);assert.deepEqual(restored.memory,expected.memory);assert.deepEqual(restored.turns,expected.turns);assert.ok(restored.projection.records.some(r=>r.text==='SYNTHETIC-REF-123'));assert.equal(restored.projection.companion.presented,true);
    await returnPage.reload();await returnPage.getByRole('button',{name:'View case',exact:true}).click();
    const restoredPanel=returnPage.getByRole('complementary',{name:'Current case details'});await restoredPanel.getByText('Delete this case',{exact:true}).click();await restoredPanel.getByLabel('I want to permanently delete this case.').check();await restoredPanel.getByRole('button',{name:'Permanently delete case',exact:true}).click();await returnPage.waitForURL(/\/return\?deleted=1/);
    assert.equal((await other.request.get(api+`/api/v1/incidents/${id}/conversation`)).status(),404);
    await other.close();
    const layout=await page.evaluate(()=>({viewport:innerHeight,document:document.documentElement.scrollHeight,body:document.body.scrollHeight,overflow:getComputedStyle(document.querySelector('main')).overflow,rect:document.querySelector('main').getBoundingClientRect().toJSON(),scrollY,positioned:[...document.querySelectorAll('body *')].filter(el=>['absolute','fixed'].includes(getComputedStyle(el).position)).map(el=>({tag:el.tagName,cls:el.className,bottom:el.getBoundingClientRect().bottom}))}));
    console.log('LAYOUT',layout);
    if(layout.document>layout.viewport+2)await page.screenshot({path:'../tmp/phase7-overflow.png',fullPage:true});
    assert.ok(layout.document<=layout.viewport+2,'The chat and open companion must stay within the viewport');
    await page.screenshot({path:`../tmp/phase7-${desktop?'desktop':'mobile'}-${index}.png`,fullPage:true});
    console.log('PASS',desktop?'desktop':'mobile',fixture.route,'consent/readiness/notes/email/save/expiry/cross-device/recovery/delete');
   }
   await context.close();
  }
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
