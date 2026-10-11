const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
const base=process.env.SMOKE_FRONTEND_URL||'http://localhost:3001',api=process.env.SMOKE_API_URL||'http://localhost:8001';
const live=process.env.SMOKE_LIVE_AI==='1';
const desktop=process.env.SMOKE_REPORT_DESKTOP==='1';
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:desktop?{width:1280,height:800}:{width:390,height:844},permissions:['clipboard-read','clipboard-write']}),page=await context.newPage();
  page.setDefaultTimeout(75000);
  for(const fixture of [
   {route:'Women/Children Related Crime',story:'Someone on Instagram is threatening to share my private photos.'},
   {route:'Financial Fraud',story:'A scammer made me send INR 35000 via UPI today.'},
   {route:'Other Cyber Crime',story:live?'Someone still has access to my Google account.':'Someone still has access to my Google account. They used user_name@example.test.'}]){
   await page.goto(base+'/incident/start');
   const created=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
   await page.getByRole('button',{name:fixture.route,exact:true}).click();assert.equal((await created).status(),200);
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
   await page.getByRole('button',{name:'View case',exact:true}).waitFor();
   const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
   async function send(text){await composer.fill(text);const reply=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');await page.getByRole('button',{name:'Send message',exact:true}).click();const response=await reply;assert.equal(response.status(),200);await page.waitForFunction(()=>document.querySelector('#chat-message')?.value==='');return response.json();}
   let state=await send(fixture.story),id=state.incident_id;
   assert.ok(state.facts.signals.length,'Synthetic story must establish supported context');
   await composer.fill('A draft preserved while reviewing the reporting packet.');
   await page.getByRole('button',{name:'Prepare report',exact:true}).click();
   const panel=page.getByRole('complementary',{name:'Reporting packet'});
   await panel.getByRole('button',{name:'Facts look right · prepare reporting draft',exact:true}).click();
   await panel.getByRole('heading',{name:'Citizen account',exact:true}).waitFor();
   assert.equal(await composer.inputValue(),'A draft preserved while reviewing the reporting packet.');
   assert.equal(await panel.getByRole('button',{name:'Copy narrative',exact:true}).count(),0);
   await panel.getByRole('button',{name:'I reviewed this packet · ready to transfer',exact:true}).click();
   await panel.getByRole('button',{name:'Copy narrative',exact:true}).waitFor();
   await panel.getByRole('button',{name:'Copy narrative',exact:true}).click();
   await panel.getByText('Narrative copied.',{exact:true}).waitFor();
   const view=await (await context.request.get(api+`/api/v1/incidents/${id}/reporting`)).json(),old=view.draft;
   assert.equal(view.state,'ready_for_handoff');assert.equal(old.reviewed,true);
   const copied=await page.evaluate(()=>navigator.clipboard.readText());assert.equal(copied,old.narrative.portal_text);
   const field=fixture.route==='Financial Fraud'?{label:'Amount',value:'35000'}:{label:'Affected service',value:fixture.route==='Other Cyber Crime'?'Google':'Instagram'};
   await panel.getByRole('button',{name:`Copy ${field.label}`,exact:true}).click();
   await panel.getByText(`${field.label} copied.`,{exact:true}).waitFor();
   assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),field.value);
   await panel.getByRole('button',{name:'Copy narrative',exact:true}).click();
   await panel.getByText('Narrative copied.',{exact:true}).waitFor();
   await panel.locator('summary').filter({hasText:'Official portal fields and requirements'}).click();
   await panel.getByRole('link',{name:'Official reporting FAQ',exact:true}).waitFor();
   await panel.getByRole('heading',{name:'Women/children anonymous content report',exact:true}).waitFor();
   assert.equal(view.mapping.narrative.maximum_characters,null,'Anonymous limits must not be asserted for registered routes');
   assert.equal(view.mapping.route_requirements[0].narrative.maximum_characters,1500);
   assert.equal(view.mapping.route_requirements[0].eligibility_established,false);
   assert.equal(view.mapping.fields.some(field=>field.id==='transaction_id'),fixture.route==='Financial Fraud');
   const expandedComposer=await composer.boundingBox();
   assert.ok(expandedComposer.y>=0&&expandedComposer.y+expandedComposer.height<=(desktop?800:844),'Expanded requirements must preserve the composer');
   await panel.locator('summary').filter({hasText:'Official portal fields and requirements'}).click();
   if(!live&&fixture.route==='Other Cyber Crime'){
    await panel.getByRole('button',{name:'Copy email identifier',exact:true}).click();
    await panel.getByText('email identifier copied.',{exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'user_name@example.test');
   }
   const download=page.waitForEvent('download');await panel.getByRole('button',{name:'Download reviewed PDF',exact:true}).click();
   const artifact=await download;fs.mkdirSync('../backend/tmp',{recursive:true});await artifact.saveAs(`../backend/tmp/phase6-report-${live?'live':'fake'}-${id}.pdf`);
   const bytes=fs.readFileSync(`../backend/tmp/phase6-report-${live?'live':'fake'}-${id}.pdf`);assert.equal(bytes.subarray(0,5).toString(),'%PDF-');
   assert.match(await panel.getByRole('link',{name:'Open official reporting portal',exact:true}).getAttribute('href'),/^https:\/\/cybercrime\.gov\.in\//);
   const rect=await composer.boundingBox();assert.ok(rect.y>=0&&rect.y+rect.height<=(desktop?800:844));
   await page.screenshot({path:`../backend/tmp/phase6-report-${live?'live':'fake'}-${fixture.route.split(' ')[0]}-${desktop?'desktop':'mobile'}.png`,fullPage:true});
   await page.reload();await page.getByRole('button',{name:'Prepare report',exact:true}).click();await panel.getByRole('button',{name:'Copy narrative',exact:true}).waitFor();
   assert.equal(await composer.inputValue(),'A draft preserved while reviewing the reporting packet.');
   const correction=fixture.route==='Financial Fraud'?'Correction: the amount was INR 3500.':'Correction: this happened on Facebook.';
   if(fixture.route==='Women/Children Related Crime'){
    const remote=await context.request.post(api+`/api/v1/incidents/${id}/conversation/turns`,{data:{turn_id:require('node:crypto').randomUUID(),expected_revision:old.source_revision,type:'message',text:correction}});
    assert.equal(remote.status(),200);state=await remote.json();
    const rejected=page.waitForResponse(r=>r.url().endsWith(`/reporting/drafts/${old.id}/export`)&&r.status()===409);
    await panel.getByRole('button',{name:'Copy narrative',exact:true}).click();await rejected;
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),copied,'Stale copy must not modify the clipboard');
   }else state=await send(correction);
   await panel.getByText('Your case changed. The earlier packet needs a new review and draft.',{exact:true}).waitFor();
   assert.equal(await panel.getByRole('button',{name:'Copy narrative',exact:true}).count(),0);
   assert.equal((await context.request.get(api+`/api/v1/incidents/${id}/reporting/drafts/${old.id}/export?format=pdf`)).status(),409);
   assert.equal(state.understanding_review.reviewed,false);
   await panel.getByRole('button',{name:'Facts look right · prepare reporting draft',exact:true}).click();
   await panel.getByRole('button',{name:'I reviewed this packet · ready to transfer',exact:true}).click();
   await panel.getByRole('button',{name:'Copy narrative',exact:true}).waitFor();
   const fresh=await (await context.request.get(api+`/api/v1/incidents/${id}/reporting`)).json();assert.notEqual(fresh.draft.id,old.id);
   const correctedFact=fresh.draft.packet.facts.find(f=>f.id===(fixture.route==='Financial Fraud'?'amount':'platform'));
   assert.equal(correctedFact.value,fixture.route==='Financial Fraud'?'3500':'Facebook');
   const freshPdf=await context.request.get(api+`/api/v1/incidents/${id}/reporting/drafts/${fresh.draft.id}/export?format=pdf`);
   assert.equal(freshPdf.status(),200);const freshBytes=await freshPdf.body();assert.equal(freshBytes.subarray(0,5).toString(),'%PDF-');
   fs.writeFileSync(`../backend/tmp/phase6-report-${live?'live':'fake'}-${id}-corrected.pdf`,freshBytes);
   const outsider=await browser.newContext();assert.equal((await outsider.request.get(api+`/api/v1/incidents/${id}/reporting`)).status(),404);await outsider.close();
   if(live)await page.waitForTimeout(8000);
  }
  console.log(`PASS: ${live?'live':'fake'} Phase6 reporting: three routes, review separation, copy/PDF, correction/stale export, resume, mobile composer and ownership.`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
