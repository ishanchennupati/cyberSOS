// Two small real-browser code-mixed journeys; no model or billing changes.
const {spawnSync}=require('node:child_process');
for(const language of ['te-Latn','hi-Latn']){
  const result=spawnSync(process.execPath,['__tests__/phase4-live.cjs'],{
    env:{...process.env,LIVE_LANGUAGE:language,LIVE_TURNS:'2',LIVE_DELAY_MS:'10000'},stdio:'inherit'});
  if(result.status!==0)process.exit(result.status||1);
}
