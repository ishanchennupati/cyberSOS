const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
const base=process.env.SMOKE_FRONTEND_URL||'http://localhost:3001';
const live=process.env.SMOKE_LIVE_AI==='1';
const results=[];
const routes=[
 {label:'Women/Children Related Crime',story:live?'Someone harassed me on Instagram. They sent repeated insulting messages yesterday evening.':'Someone on Instagram is threatening to share my private photos.',correction:'Correction: this happened on Facebook, not Instagram.'},
 {label:'Financial Fraud',story:live?'A scammer made me send INR 35000 via UPI ten minutes ago.':'A scammer made me send INR 35000 via UPI today.',correction:'Correction: the amount was INR 3500.'},
 {label:'Other Cyber Crime',story:live?'Someone else still has access to my Google account and sent messages pretending to be me.':'Someone still has access to my Google account.',correction:'Correction: this was my Microsoft account, not Google.'}
];
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage();
  page.setDefaultTimeout(75000);
  const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
  async function send(text){
   await composer.fill(text); const start=Date.now();
   const [res]=await Promise.all([
    page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST'),
    page.getByRole('button',{name:'Send message',exact:true}).click()]);
   assert.equal(res.status(),200);const state=await res.json();
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
   await page.waitForFunction(()=>document.querySelector('#chat-message')?.value==='');
   const change=state.turns.at(-1).fact_changes;
   const result={text,duration_ms:Date.now()-start,state};results.push(result);
   if(live&&state.facts.money_lost===null){
    const reply=state.next_move?.message||change.acknowledgement||'';
    assert.ok(!/no (?:payment or )?financial loss was involved|no money (?:was )?lost/i.test(reply),'Unreported money loss must remain unknown in the rendered reply');
   }
   console.log(JSON.stringify({text,duration_ms:result.duration_ms,understanding:change.understanding?.status,agent:change.agent?.status,rejection:change.agent?.rejection_reason,reply:state.next_move?.message||change.acknowledgement,pending:state.pending_question}));
   if(live) await page.waitForTimeout(8000);
   return state;
  }
  const failures=[];
  for(const route of routes){
   await page.goto(base+'/incident/start');
   const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
   await page.getByRole('button',{name:route.label,exact:true}).click();assert.equal((await response).status(),200);
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
   await page.getByRole('button',{name:'View case',exact:true}).waitFor();
   let state=await send(route.story);
   if(live&&route.label==='Financial Fraud')assert.ok(!state.facts.signals.includes('impersonation'),'A generic scam does not establish an impersonated identity');
   if(route.label!=='Financial Fraud')assert.ok(!state.plan.plan.actions.some(a=>a.id==='call_1930'||a.id.startsWith('contact_bank')));
   if(live){
    for(const text of [route.label==='Women/Children Related Crime'?'Why are you asking about money?':'Why are you asking that?', 'I am scared. Please explain what CyberSOS can help me with.', 'I do not know. Please skip that question.',route.correction]) state=await send(text);
    if(route.label==='Financial Fraud')assert.equal(state.facts.amount,'3500');
    if(route.label==='Women/Children Related Crime')assert.equal(state.facts.platform,'Facebook');
    if(route.label==='Other Cyber Crime')assert.match(state.facts.platform,/^Microsoft(?: account)?$/i);
   }
   state=await send('Enough questions. Tell me what to do now.');
   assert.equal(state.pending_question,null);assert.equal(state.memory.questions_paused,true);
   assert.ok(state.turns.at(-1).fact_changes.help_view.action_ids.length);
   assert.equal(state.understanding_review.reviewed,false);
   await page.getByText('Current understanding and help',{exact:true}).last().waitFor();
   const panel=page.getByRole('list',{name:'Saved message history'}).locator(':scope > li').last();
   await panel.locator('details[data-action-group="PRESERVE"] > summary').click();
   assert.ok(await panel.getByRole('heading').count()>0);
   fs.mkdirSync('../backend/tmp',{recursive:true});
   await page.screenshot({path:`../backend/tmp/phase6-help-${live?'live':'fake'}-${routes.indexOf(route)}.png`,fullPage:true});
   state=await send('Summarize and conclude.');assert.equal(state.memory.questions_paused,true);assert.equal(state.pending_question,null);
   await composer.fill('A draft that must survive opening details.');
   await page.getByRole('button',{name:'View case',exact:true}).click();
   assert.equal(await composer.inputValue(),'A draft that must survive opening details.');
   const rect=await composer.boundingBox();assert.ok(rect.y>=0&&rect.y+rect.height<=844);
   await page.reload();await composer.waitFor();assert.equal(await composer.inputValue(),'A draft that must survive opening details.');
   const restored=new URL(page.url()).pathname.split('/')[2];
   const saved=await context.request.get(`${process.env.SMOKE_API_URL}/api/v1/incidents/${restored}/conversation`);assert.equal(saved.status(),200);assert.equal((await saved.json()).memory.questions_paused,true);
  }
  if(live){
   await page.goto(base+'/incident/start');
   let state=await send('Someone just got harassed in front of me; what should I do?');
   assert.equal(state.facts.immediate_danger,null);assert.equal(state.memory.incident_scope_pending,true);
   state=await send('This is a separate incident affecting someone else, physically in front of me.');
   assert.equal(state.facts.immediate_danger,null);assert.equal(state.memory.incident_scope_pending,true);
   for(const {text,state} of results){const change=state.turns.at(-1).fact_changes;
    const applicationControl=change.agent?.status==='not_requested'&&change.agent?.reason==='citizen_control'&&
      ['help','plan','summary','conclude','pause','witness','separate_incident'].includes(change.conversation_control?.request);
    if(change.understanding?.status!=='understood'||change.agent?.status!=='decided'&&!applicationControl) failures.push({text,understanding:change.understanding,agent:change.agent});
   }
   assert.deepEqual(failures,[],'Live understanding and requested follow-up must succeed; application control is explicitly distinguished.');
  }
  console.log(`PASS: ${live?'live':'fake'} conversation repair, three routes, help, conclusion, mobile draft and reload.`);
 }finally{
  fs.mkdirSync('../backend/tmp',{recursive:true});fs.writeFileSync(`../backend/tmp/phase6-repair-${live?'live':'fake'}-${Date.now()}.json`,JSON.stringify(results,null,2));
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
