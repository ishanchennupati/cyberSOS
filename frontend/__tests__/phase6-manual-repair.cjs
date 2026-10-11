const assert=require('node:assert/strict'),fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true}),results=[];
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});page.setDefaultTimeout(60000);
  await page.goto(process.env.SMOKE_FRONTEND_URL+'/incident/start');
  const created=page.waitForResponse(r=>r.url().endsWith('/conversation/turns'));
  await page.getByRole('button',{name:'Women/Children Related Crime',exact:true}).click();await created;
  await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
  const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
  let previousReply='';
  for(const text of ['ok','Someone harassed me on Instagram with repeated insulting messages yesterday evening',
   'i dont remember','no','yes the guy threatened me by saying he will leak stories about me online',
   'no','No','no','yes','hi']){
   await composer.fill(text);
   const response=page.waitForResponse(r=>r.url().endsWith('/conversation/turns')&&r.request().method()==='POST');
   await composer.press('Enter');await page.getByLabel('Pending message').waitFor();
   assert.equal(await composer.inputValue(),'');
   const res=await response;assert.equal(res.status(),200);const state=await res.json(),c=state.turns.at(-1).fact_changes;
   const reply=state.next_move?.message||c.acknowledgement||'';
   results.push({text,state});console.log(JSON.stringify({text,reply,field:state.next_move?.related_field,understanding:c.understanding?.status,agent:c.agent?.status,rejection:c.agent?.rejection_reason}));
   assert.equal(c.understanding.status,'understood');
   assert.ok(c.agent.status==='decided'||c.agent.rejection_reason==='REPEATED_CASE_RECAP','Unexpected live follow-up failure');
   assert.ok(!['claimed_person','claimed_organization'].includes(state.next_move?.related_field),'Harassment must not become claimed-identity intake');
   assert.notEqual(state.next_move?.related_field,'recipient','Ordinary harassment must not become recipient intake');
   if(text==='i dont remember'&&/identif|username|profile|handle/i.test(previousReply))
    assert.notEqual(state.next_move?.related_field,'identifiers','A declined identifier request must not repeat');
   assert.ok(!reply||reply.length<80||reply!==previousReply,'The same case recap must not repeat');
   if(text.includes('leak stories'))assert.notEqual(state.facts.blackmail,true,'An unconditional threat is not a reported coercive demand');
   if(['yes','hi'].includes(text))assert.equal(state.understanding_review.reviewed,false);
   previousReply=reply;
   await page.waitForTimeout(8000);
  }
  await page.getByRole('button',{name:'Looks right · show my plan',exact:true}).waitFor({state:'visible'});
  const reviewed=page.waitForResponse(r=>r.url().endsWith('/conversation/turns'));
  await page.getByRole('button',{name:'Looks right · show my plan',exact:true}).click();
  assert.equal((await reviewed).status(),200);
  await page.getByRole('complementary',{name:'Response plan'}).waitFor();
  assert.equal(await composer.inputValue(),'');
  console.log('PASS: live manual-test sequence, relevant fields, no repeated recap, greetings, existing review and explicit plan confirmation.');
 }finally{
  fs.writeFileSync(`../backend/tmp/phase6-manual-repair-${Date.now()}.json`,JSON.stringify(results,null,2));
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
