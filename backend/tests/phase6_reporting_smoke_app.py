"""Synthetic reporting browser provider; never imported by production."""
import json
from tests.phase5_smoke_app import BrowserProvider,app
from tests.test_phase3_understanding import candidate
from app.services import understanding,case_agent,reporting_narrative


class ReportingBrowserProvider(BrowserProvider):
    name='fake'
    async def extract(self,message,context):
        if message=='Someone still has access to my Google account. They used user_name@example.test.':
            data=json.loads(await super().extract('Someone still has access to my Google account.',context))
            data['candidates'].append(candidate('identifiers',[{'type':'email','value':'user_name@example.test'}],'user_name@example.test'))
            return json.dumps(data)
        fields={'Correction: this happened on Facebook.':('platform','Facebook','Facebook'),
            'Correction: the amount was INR 3500.':('amount','3500','3500')}
        if message in fields:
            field,value,quote=fields[message];item=candidate(field,value,quote);item['correction_source']='Correction'
            return json.dumps({'language':'en','candidates':[item]})
        return await super().extract(message,context)
    async def draft(self,packet):
        data=json.loads(packet)
        return json.dumps({'claims':[{'fact_id':f['id'],'text':f['statement']} for f in data['facts']]})


provider=ReportingBrowserProvider()
understanding.get_provider=case_agent.get_provider=reporting_narrative.get_provider=lambda:provider
