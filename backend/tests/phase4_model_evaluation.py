"""Explicit, quota-bounded free-tier synthetic comparison; no configured model change."""
import asyncio, json, os, time
from pathlib import Path
from datetime import datetime, timezone
from app.core.config import get_settings
from app.domain.facts import FACTS_ADAPTER
from app.domain.playbooks import evaluate
from app.services import understanding, case_agent

STORIES=[
    'Someone claiming SBI made me send ₹5,000 via UPI. They also made me install AnyDesk.',
    'SBI ani cheppi nannu ₹5,000 UPI lo pampincharu. AnyDesk install cheyincharu.',
    'SBI se bolkar mujhe ₹5,000 UPI se bhejne ko kaha aur maine bhej diya. AnyDesk bhi install karwaya.',
]

def main():
    if os.environ.get('PHASE4_LIVE')!='1':raise SystemExit('Explicit synthetic live opt-in required')
    settings=get_settings()
    from google import genai
    with genai.Client(api_key=settings.GEMINI_API_KEY) as client:
        names={model.name.removeprefix('models/') for model in client.models.list()}
    models=os.environ.get('PHASE4_MODELS',settings.UNDERSTANDING_MODEL+',gemini-3.8-flash').split(',')
    print(json.dumps({'configured_model':models[0],'available_candidates':[name for name in models if name in names],
        'tier':'No billing or fallback enabled; pricing documents reviewed for free standard tier'}))
    results=[]
    previous=os.environ.get('UNDERSTANDING_MODEL')
    try:
        for model in models:
            if model not in names:
                results.append({'model':model,'status':'not_listed'});continue
            os.environ['UNDERSTANDING_MODEL']=model;get_settings.cache_clear()
            for story in STORIES:
                from uuid import uuid4
                started=time.perf_counter()
                facts,updates,result=understanding.interpret(story,FACTS_ADAPTER.validate_python({'kind':'incident_understanding'}),uuid4(),datetime.now(timezone.utc),'Asia/Kolkata')
                extraction_ms=round((time.perf_counter()-started)*1000)
                # Exactly identical canonical context/retrieval per model for reasoning.
                fixed=FACTS_ADAPTER.validate_python({'kind':'financial_scam_transfer','money_lost':True,'authorization':'authorized',
                    'amount':'5000','currency':'INR','payment_method':'upi','signals':['financial','device_compromise']})
                context=case_agent.build_context(fixed,{},[],[],'What is the National Cybercrime Reporting Portal?',evaluate(fixed,as_of=datetime(2026,10,3,tzinfo=timezone.utc)),[],[])
                started=time.perf_counter();move,agent=case_agent.decide(context)
                row={'model':model,'story':story,'extraction_status':result['status'],'extraction_category':result.get('category'),
                    'extraction_ms':extraction_ms,'facts':{key:facts.model_dump(mode='json')[key] for key in ['amount','currency','authorization','payment_method','signals']},
                    'agent':agent,'reasoning_ms':round((time.perf_counter()-started)*1000),'reply':move.model_dump(mode='json') if move else None}
                results.append(row);print(json.dumps(row),flush=True)
                if result.get('http_status')==429 or agent.get('http_status')==429:break
                time.sleep(10)
    finally:
        if previous is None:os.environ.pop('UNDERSTANDING_MODEL',None)
        else:os.environ['UNDERSTANDING_MODEL']=previous
        get_settings.cache_clear()
    target=Path(__file__).parents[1]/'tmp/phase4-model-evaluation.json';target.parent.mkdir(exist_ok=True)
    if target.exists():
        previous_results=json.loads(target.read_text(encoding='utf-8'))
        (target.parent/'phase4-model-evaluation-before-schema-repair.json').write_text(json.dumps(previous_results,ensure_ascii=False,indent=2),encoding='utf-8')
    target.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
