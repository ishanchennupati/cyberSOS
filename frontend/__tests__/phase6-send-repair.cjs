const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});let release;
 try{
  for(const width of [390,1280]){
   const page=await browser.newPage({viewport:{width,height:844}});
   await page.goto(process.env.SMOKE_FRONTEND_URL+'/incident/start');
   const created=page.waitForResponse(r=>r.url().endsWith('/conversation/turns'));
   await page.getByRole('button',{name:'Women/Children Related Crime',exact:true}).click();await created;
   await page.waitForURL(/\/incident\/[^/]+\/conversation$/);
   const composer=page.getByRole('textbox',{name:'Message CyberSOS'});
   let mode='hold',failAfterHold=false;const sent=[];
   await page.route('**/conversation/turns',async route=>{
    sent.push(route.request().postDataJSON());
    if(mode==='fail')return route.abort();
    if(mode==='hold')await new Promise(resolve=>{release=resolve;});
    return failAfterHold?route.abort():route.continue();
   });
   await composer.fill('Someone on Instagram is threatening to share my private photos.');
   await composer.press('Enter');
   await page.getByLabel('Pending message').waitFor();
   assert.equal(await composer.inputValue(),'','Sent text must move out of the composer before the server finishes');
   await composer.fill('A newer unsent draft.');
   const saved=page.waitForResponse(r=>r.url().endsWith('/conversation/turns'));release();await saved;
   await page.getByRole('button',{name:'Send message',exact:true}).waitFor();
   await page.waitForFunction(()=>!document.querySelector('button[aria-label="Send message"]')?.disabled);
   assert.equal(await composer.inputValue(),'A newer unsent draft.');
   mode='fail';await composer.press('Enter');await page.getByRole('button',{name:'Retry message',exact:true}).waitFor();
   assert.equal(await composer.inputValue(),'A newer unsent draft.','Failed text must be recoverable');
   const failedId=sent.at(-1).turn_id;
   mode='continue';
   const retried=page.waitForResponse(r=>r.url().endsWith('/conversation/turns'));
   await page.getByRole('button',{name:'Retry message',exact:true}).click();await retried;
   await page.waitForFunction(()=>document.querySelector('#chat-message')?.value==='');
   assert.equal(sent.at(-1).turn_id,failedId,'Retry must preserve the original key');
   mode='hold';failAfterHold=true;
   await composer.fill('A second failed message.');await composer.press('Enter');
   await page.getByLabel('Pending message').waitFor();await composer.fill('Keep this newer draft.');release();
   await page.getByRole('button',{name:'Retry message',exact:true}).waitFor();
   assert.equal(await composer.inputValue(),'Keep this newer draft.','Recovery must not overwrite new typing');
   const rect=await composer.boundingBox();assert.ok(rect.y+rect.height<=844);
   await page.close();
  }
  console.log('PASS: Enter/send clears pending text immediately; newer typing, failures and same-key retry preserved on mobile/desktop.');
 }finally{release?.();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
