const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
const prompts=[
  'Someone claiming to be SBI made me send ₹5,000 via UPI. They also made me install AnyDesk. The caller used a blue profile picture.',
  'Why are you asking that?',
  'What is the National Cybercrime Reporting Portal?',
  'Sorry, the amount was ₹4,500. Why does the time matter?',
  'I do not know. Please skip that question.',
  'I feel really worried about this.',
  'Please pause the questions for now.',
  'Can you write a birthday poem?',
  'What profile picture did I describe earlier?',
];
if(process.env.LIVE_LANGUAGE==='te-Latn')prompts[0]='SBI ani cheppi nannu ₹5,000 UPI lo pampincharu. AnyDesk install cheyincharu. The caller used a blue profile picture.';
if(process.env.LIVE_LANGUAGE==='hi-Latn')prompts[0]='SBI se bolkar mujhe ₹5,000 UPI se bhejne ko kaha aur maine bhej diya. AnyDesk bhi install karwaya. The caller used a blue profile picture.';
(async()=>{
  assert.equal(process.env.SMOKE_LIVE_AI,'1','Explicit synthetic live opt-in required');
  const browser=await chromium.launch({headless:true});const results=[];
  try{
    const context=await browser.newContext({viewport:{width:390,height:844}});const page=await context.newPage();
    page.setDefaultTimeout(70000);
    page.on('pageerror',error=>console.log('Browser error: '+error.message));
    page.on('response',response=>{if(response.url().includes('/api/v1/incidents')&&!response.url().includes('/turns'))console.log('Case API '+response.status()+' '+response.url().replace(/[a-f0-9-]{36}/g,'{case}'));});
    await page.goto((process.env.SMOKE_FRONTEND_URL||'http://localhost:3000')+'/incident/start',{waitUntil:'networkidle'});
    for(const prompt of prompts.slice(0,Number(process.env.LIVE_TURNS||prompts.length))){
      await page.getByRole('textbox',{name:'Message CyberSOS'}).fill(prompt);
      const started=Date.now();const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'Send message',exact:true}).click();
      const api=await response;assert.equal(api.status(),200);const state=await api.json();
      fs.mkdirSync('../backend/tmp',{recursive:true});fs.writeFileSync('../backend/tmp/phase4-live-state.json',JSON.stringify(state,null,2));
      const change=state.turns.at(-1).fact_changes;
      if(results.length===0){
        assert.equal(state.facts.amount,'5000');assert.equal(state.facts.currency,'INR');
        assert.equal(state.facts.payment_method,'upi');assert.equal(state.facts.authorization,'authorized');
        assert.ok(state.facts.signals.includes('financial')&&state.facts.signals.includes('device_compromise'));
      }
      results.push({prompt,duration_ms:Date.now()-started,extraction:change.understanding,agent:change.agent,
        reply:state.next_move,actions:state.plan.plan.actions.map(a=>a.id),amount:state.facts.amount,sources:change.knowledge_sources});
      console.log(JSON.stringify({prompt,duration_ms:results.at(-1).duration_ms,extraction:change.understanding?.status,agent:change.agent,reply:state.next_move}));
      if(!state.next_move){console.log('Live reply fell back; stopping quota-bounded run.');break;}
      await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
      await page.getByRole('button',{name:'Send message',exact:true}).waitFor();
      await page.waitForFunction(()=>document.querySelector('#chat-message')?.value==='');
      if(process.env.LIVE_DELAY_MS)await new Promise(resolve=>setTimeout(resolve,Number(process.env.LIVE_DELAY_MS)));
    }
    fs.mkdirSync('../backend/tmp',{recursive:true});fs.writeFileSync('../backend/tmp/phase4-live'+(process.env.LIVE_LANGUAGE?'-'+process.env.LIVE_LANGUAGE:'')+'.json',JSON.stringify(results,null,2));
    await page.screenshot({path:'../backend/tmp/phase4-mobile.png',fullPage:true});
    assert.ok(results.every(r=>r.extraction?.status==='understood'&&r.agent?.status==='decided'),'Both live AI stages must pass');
    assert.equal(results.length,Number(process.env.LIVE_TURNS||prompts.length));
    if(results.length>=3)assert.ok(results[2].sources?.some(s=>s.source_id==='NCRP-REPORT'),'Actual retrieved citation required');
    if(results.length>=4)assert.equal(results[3].amount,'4500');
    if(results.length>=9)assert.match(results[8].reply.message,/blue/i);
    console.log('PASS: live browser -> both AI stages -> validation -> rendering');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
