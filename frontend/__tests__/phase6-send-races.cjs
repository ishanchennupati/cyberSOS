// UI race test: controlled turn responses, no model calls.
const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});let release;const errors=[];
 try{
  for(const scenario of ['identical','cleared']){
   const page=await browser.newPage({viewport:{width:390,height:844}});
   await page.goto(process.env.SMOKE_FRONTEND_URL+'/incident/start');
   const created=page.waitForResponse(r=>r.url().endsWith('/conversation/turns'));
   await page.getByRole('button',{name:'Other Cyber Crime',exact:true}).click();let state=await (await created).json();
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
   const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
   await page.route('**/conversation/turns',async route=>{
    const request=route.request().postDataJSON();await new Promise(resolve=>{release=resolve;});
    if(scenario==='cleared')return route.abort();
    state={...state,revision:state.revision+1,turns:[...state.turns,{id:request.turn_id,revision:state.revision+1,type:'message',role:'user',text:request.text,structured_reply:request,fact_changes:{acknowledgement:'Saved.'},pending_question:null,attachments:[]}]};
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(state)});
   });
   await composer.fill('yes');await composer.press('Enter');await page.getByLabel('Pending message').waitFor();
   await composer.fill(scenario==='identical'?'yes':'A newer draft.');
   if(scenario==='cleared')await composer.fill('');
   release();
   if(scenario==='cleared')await page.getByRole('button',{name:'Retry message',exact:true}).waitFor();
   else await page.getByLabel('Pending message').waitFor({state:'hidden'});
   const expected=scenario==='identical'?'yes':'';
   if(await composer.inputValue()!==expected)errors.push(`${scenario}: got ${JSON.stringify(await composer.inputValue())}, expected ${JSON.stringify(expected)}`);
   if(scenario==='cleared'){
    await page.reload();await page.getByRole('button',{name:'Retry message',exact:true}).waitFor();
    assert.equal(await composer.inputValue(),'','Reload must preserve the deliberate empty draft');
   }
   await page.close();
  }
  assert.deepEqual(errors,[]);
  console.log('PASS: identical newer draft survives success; deliberate empty draft survives failed send.');
 }finally{release?.();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
