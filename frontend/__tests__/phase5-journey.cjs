const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
const base=process.env.SMOKE_FRONTEND_URL||'http://localhost:3001';
const api=process.env.SMOKE_API_URL||'http://localhost:8001';

(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage();
  page.setDefaultTimeout(30000);
  const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
  async function turn(click){
   const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
   await click();const result=await response;assert.equal(result.status(),200);return result.json();
  }
  async function send(text){await composer.fill(text);return turn(()=>page.getByRole('button',{name:'Send message',exact:true}).click());}
  await page.goto(base+'/incident/start');
  // First turn can be attachment-only; delayed analysis must follow navigation.
  await page.locator('input[type=file]').setInputFiles('../backend/tests/fixtures/phase5/financial.png');
  await page.getByText('Ready to send · not analyzed',{exact:true}).waitFor();
  await turn(()=>page.getByRole('button',{name:'Send message',exact:true}).click());
  await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
  await page.getByRole('button',{name:'Confirm detail',exact:true}).first().waitFor();
  await page.goto(base+'/incident/start');
  assert.equal(await composer.isVisible(),true);
  for(const label of ['Women/Children Related Crime','Financial Fraud','Other Cyber Crime','Not sure'])assert.equal(await page.getByRole('button',{name:label,exact:true}).isVisible(),true);
  let state=await send('I lost 5000');
  assert.equal(state.route_hint,null);assert.equal(state.plan.plan.actions.length,0);
  await page.getByRole('button',{name:'It was an online payment',exact:true}).waitFor();
  await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
  await page.reload();assert.equal((await(await context.request.get(api+`/api/v1/incidents/${state.incident_id}/conversation`)).json()).facts.amount,'5000');
  // Route hints persist and change without creating incident facts or clearing drafts.
  await page.goto(base+'/incident/start');
  await composer.fill('Preserved draft');
  assert.equal(await composer.inputValue(),'Preserved draft');
  state=await turn(()=>page.getByRole('button',{name:'Women/Children Related Crime',exact:true}).click());
  assert.equal(state.route_hint,'women_children');assert.equal(state.facts.signals.length,0);
  await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
  await page.waitForFunction(()=>document.querySelector('#chat-message')?.value==='Preserved draft');
  await page.getByText('Optional starting choice',{exact:false}).click();
  state=await turn(()=>page.getByRole('button',{name:'Financial Fraud',exact:true}).click());
  assert.equal(state.route_hint,'financial');
  await composer.fill('A scammer made me send INR 35000 via UPI today.');
  let response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Send message',exact:true}).click();
  await page.getByLabel('Pending message',{exact:true}).waitFor();
  assert.match(await page.getByLabel('Pending message',{exact:true}).innerText(),/35000/);
  state=await(await response).json();assert.equal(state.facts.amount,'35000');
  // Real upload/API/revision path with explicitly fake extraction.
  await composer.fill('Here is the synthetic receipt.');
  await page.locator('input[type=file]').setInputFiles('../backend/tests/fixtures/phase5/financial.png');
  await page.getByText('Ready to send · not analyzed',{exact:true}).waitFor();
  const analysis=page.waitForResponse(r=>r.url().endsWith('/analyze')&&r.request().method()==='POST');
  state=await turn(()=>page.getByRole('button',{name:'Send message',exact:true}).click());
  assert.equal((await analysis).status(),200);
  await page.getByRole('button',{name:'Use attachment value',exact:true}).waitFor();
  await composer.fill('Draft while reviewing');
  state=await turn(()=>page.getByRole('button',{name:'Use attachment value',exact:true}).click());
  assert.equal(state.facts.amount,'3500');assert.equal(state.facts.currency,'INR');
  assert.equal(await composer.inputValue(),'Draft while reviewing');
  state=await send('All details in this attachment are correct.');
  assert.equal(state.facts.identifiers[0].value,'sample-store@upi');
  assert.equal(state.evidence_reviews[0].candidates.every(c=>c.reviewed),true);
  await page.reload();await page.getByText('Review recorded · only accepted details update your case.').waitFor();
  await composer.fill('Multiline\ndraft\nstays available');
  await page.getByRole('button',{name:'Response plan',exact:true}).click();
  state=await turn(()=>page.getByRole('button',{name:'Looks right · show my plan',exact:true}).last().click());
  assert.equal(state.understanding_review.reviewed,true);
  const rect=await composer.boundingBox();assert.ok(rect.y>=0&&rect.y+rect.height<=844);
  assert.equal(await composer.inputValue(),'Multiline\ndraft\nstays available');
  await page.getByRole('button',{name:'Close details',exact:true}).click();
  await page.getByRole('button',{name:'Delete attachment',exact:true}).click();
  await page.getByText('Attachment deleted',{exact:true}).waitFor();
  assert.equal(await composer.inputValue(),'Multiline\ndraft\nstays available');
  // Nonfinancial choices use the same conversation and approved policy.
  for(const [label,text,signal] of [['Women/Children Related Crime','Someone on Instagram is threatening to share my private photos.','threats'],['Other Cyber Crime','Someone still has access to my Google account.','account_takeover']]){
   await page.goto(base+'/incident/start');await turn(()=>page.getByRole('button',{name:label,exact:true}).click());
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);state=await send(text);
   assert.ok(state.facts.signals.includes(signal));assert.ok(!state.plan.plan.actions.some(a=>a.id==='call_1930'||a.id.startsWith('contact_bank')));
  }
  console.log('PASS: Phase 5 hybrid -> pending -> upload -> partial/conflict/natural review -> canonical memory -> fuller plan -> mobile resume/deletion; three routes share one system (fake AI).');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
