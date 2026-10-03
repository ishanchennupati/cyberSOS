"""Bounded synthetic provider-schema diagnostic. Never print keys or request data."""
import asyncio, json
from app.services.ai_provider import GeminiProvider
from app.core.config import get_settings

async def main():
    try:
        from app.domain.facts import FACTS_ADAPTER
        from app.domain.playbooks import evaluate
        from app.services.case_agent import build_context
        from datetime import datetime, timezone
        facts=FACTS_ADAPTER.validate_python({'kind':'financial_scam_transfer','money_lost':True,'authorization':'authorized',
            'amount':'5000','currency':'INR','payment_method':'upi','signals':['financial','device_compromise']})
        context=build_context(facts,{},[],[],'What is the National Cybercrime Reporting Portal?',evaluate(facts,as_of=datetime.now(timezone.utc)),[],[])
        output = await GeminiProvider().decide(json.dumps(context))
        print(json.dumps({'ok':bool(output)}))
    except Exception as exc:
        message = str(exc).replace(get_settings().GEMINI_API_KEY or '<none>', '<redacted>')
        print(json.dumps({'error_type':type(exc).__name__,'status':getattr(exc,'code',None),'synthetic_schema_diagnostic':message[:1600]}))

if __name__=='__main__':asyncio.run(main())
