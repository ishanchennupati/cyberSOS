const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
const base=process.env.SMOKE_FRONTEND_URL||'http://localhost:3001';
const results=[];
const stageFailures=[];
const delay=()=>new Promise(resolve=>setTimeout(resolve,10000));

(async()=>{
 assert.equal(process.env.SMOKE_LIVE_AI,'1');
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage();
  page.setDefaultTimeout(75000);
  const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
  async function send(text){
   await composer.fill(text);const start=Date.now();
   const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
   await page.getByRole('button',{name:'Send message',exact:true}).click();
   const result=await response;assert.equal(result.status(),200);const state=await result.json();
   const change=state.turns.at(-1).fact_changes;
   results.push({kind:'conversation',duration_ms:Date.now()-start,text,understanding:change.understanding?.status,
     agent:change.agent,reply:state.next_move,facts:state.facts,actions:state.plan.plan.actions.map(a=>a.id)});
   console.log(JSON.stringify({text,duration_ms:results.at(-1).duration_ms,understanding:change.understanding?.status,
      agent:change.agent?.status,rejection:change.agent?.rejection_reason,reply:state.next_move?.message}));
   if(change.understanding?.status!=='understood'||change.agent?.status!=='decided')
     stageFailures.push({text,understanding:change.understanding?.status,agent:change.agent});
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);await page.waitForFunction(()=>document.querySelector('#chat-message')?.value==='');
   await delay();return state;
  }
  async function attach(file){
   await page.locator('input[type=file]').setInputFiles('../backend/tests/fixtures/phase5/'+file);
   await page.getByText('Ready to send · not analyzed',{exact:true}).waitFor();
   const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
   const analyzed=page.waitForResponse(r=>r.url().endsWith('/analyze')&&r.request().method()==='POST');
   const start=Date.now();await page.getByRole('button',{name:'Send message',exact:true}).click();
   const state=await(await response).json();const analysisResponse=await analyzed;assert.equal(analysisResponse.status(),200);
   const analysis=await analysisResponse.json();results.push({kind:'evidence',file,duration_ms:Date.now()-start,analysis});
   console.log(JSON.stringify({file,status:analysis.status,fields:analysis.candidates.map(c=>c.field),duration_ms:results.at(-1).duration_ms}));
   assert.equal(analysis.status,'review_needed');assert.ok(analysis.candidates.length>0);
   await page.getByText('Details to review',{exact:false}).last().waitFor();await delay();return {state,analysis};
  }
  await page.goto(base+'/incident/start');
  let state=await send('I lost 5000');assert.ok(!state.plan.plan.actions.some(a=>a.id==='call_1930'||a.id.startsWith('contact_bank')));
  assert.equal(state.facts.currency,null);assert.equal(state.facts.payment_method,'unknown');
  const routes=[
    {label:'Financial Fraud',story:'Someone pretending to be my bank made me send INR 35000 via UPI ten minutes ago.',files:['financial.png','financial.jpg','financial.pdf']},
    {label:'Women/Children Related Crime',story:'Someone on Instagram is threatening to share my private photos if I do not pay. I am scared.',files:['threat.png']},
    {label:'Other Cyber Crime',story:'Someone else still has access to my Google account and sent messages pretending to be me.',files:['account.png']},
  ];
  const selectedRoutes=process.env.PHASE5_LIVE_ROUTE ? routes.filter(r=>r.label===process.env.PHASE5_LIVE_ROUTE) : routes;
  assert.ok(selectedRoutes.length);
  for(const route of selectedRoutes){
   await page.goto(base+'/incident/start');
   const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
   await page.getByRole('button',{name:route.label,exact:true}).click();assert.equal((await response).status(),200);
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);state=await send(route.story);
   if(route.label==='Financial Fraud')assert.ok(state.plan.plan.actions.some(a=>a.id==='call_1930'&&a.critical));
   else assert.ok(!state.plan.plan.actions.some(a=>a.id==='call_1930'||a.id.startsWith('contact_bank')));
   state=await send('Why are you asking that?');
   for(const file of route.files){
    const {analysis}=await attach(file);
    if(file==='financial.png'){
     const amount=analysis.candidates.find(c=>c.field==='amount');assert.ok(amount&&amount.conflict);
     const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
     await page.getByRole('button',{name:'Use attachment value',exact:true}).first().click();
     const result=await response;assert.equal(result.status(),200);state=await result.json();
     assert.equal(Number(state.facts.amount),3500);await delay();
     state=await send('All remaining details in this attachment are correct.');
     assert.ok(state.facts.transaction_id);assert.equal(state.evidence_reviews[0].candidates.every(c=>c.reviewed),true);
    }
   }
   await page.reload();await composer.waitFor();const rect=await composer.boundingBox();assert.ok(rect.y>=0&&rect.y+rect.height<=844);
  }
  assert.deepEqual(stageFailures,[], 'Every typed turn must pass both live AI stages; saved fallback alone is not acceptance.');
  console.log(`PASS: live typed understanding/follow-up and native-file extraction through the browser across ${selectedRoutes.length} selected supported routes.`);
 }finally{
  fs.mkdirSync('../backend/tmp',{recursive:true});fs.writeFileSync('../backend/tmp/phase5-live-results.json',JSON.stringify(results,null,2));
  fs.writeFileSync(`../backend/tmp/phase5-live-results-${Date.now()}.json`,JSON.stringify(results,null,2));
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
