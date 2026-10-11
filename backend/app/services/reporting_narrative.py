"""Packet-only drafting. Each accepted claim traces to reviewed canonical facts."""
import asyncio
import json
from pydantic import BaseModel,ConfigDict,Field
from app.core.config import get_settings
from app.services.ai_provider import get_provider


class NarrativeClaim(BaseModel):
    model_config=ConfigDict(extra='forbid')
    fact_id: str=Field(max_length=64)
    text: str=Field(min_length=1,max_length=10000)


class NarrativeClaims(BaseModel):
    model_config=ConfigDict(extra='forbid')
    claims: list[NarrativeClaim]=Field(min_length=1,max_length=32)


def alternatives(fact):
    return [fact.statement,fact.statement.replace('I reported ','The complainant reported ',1)]


def validate_claims(proposal,packet):
    parsed=NarrativeClaims.model_validate(proposal)
    facts={fact.id:fact for fact in packet.facts}
    if len(parsed.claims)!=len(facts) or {claim.fact_id for claim in parsed.claims}!=set(facts):
        raise ValueError('Claims must cover each reviewed fact once')
    for claim in parsed.claims:
        if claim.text not in alternatives(facts[claim.fact_id]):raise ValueError('Unsupported narrative claim')
    return parsed.model_dump()


def portal_text(text):
    # Preserve the original narrative separately. Explicit character names in
    # the transfer copy avoid silently changing identifiers or omitting facts.
    names={'#':'number sign','$':'dollar sign','@':'at sign','^':'caret','*':'asterisk',
        '`':'backtick','’':'apostrophe','‘':'apostrophe','~':'tilde','|':'vertical bar','!':'exclamation mark'}
    for character,name in names.items():text=text.replace(character,f' {name} ')
    return text


def generate(packet):
    from time import perf_counter
    started=perf_counter()
    fallback={'claims':[{'fact_id':fact.id,'text':fact.statement} for fact in packet.facts]}
    status,provider_name,reason='local_draft','local',None
    claims=fallback
    try:
        provider=get_provider()
        if provider is not None:
            # No transcript, legacy summary, OCR, knowledge or action instructions.
            encoded=packet.model_dump_json()
            if len(encoded)>24000:raise ValueError('Packet context limit')
            async def invoke():return await provider.draft(encoded)
            output=asyncio.run(asyncio.wait_for(invoke(),timeout=get_settings().UNDERSTANDING_TIMEOUT_SECONDS))
            if len(output)>get_settings().UNDERSTANDING_MAX_OUTPUT_CHARS:raise ValueError('Output limit')
            claims=validate_claims(json.loads(output),packet)
            status,provider_name='ai_draft',getattr(provider,'name',get_settings().UNDERSTANDING_PROVIDER)
    except Exception as exc:
        # Bounded diagnostics only; no raw sensitive provider error/content.
        from app.services.case_agent import failure_category
        reason=failure_category(exc)
        status='local_fallback'
    text=' '.join(claim['text'] for claim in claims['claims'])
    copy=portal_text(text)
    warnings=[]
    if len(copy)<200:warnings.append('The official public checklist requires at least 200 characters. Add only relevant true details in chat; CyberSOS has not padded the account.')
    if copy!=text:warnings.append('The transfer copy names restricted symbols in words; original facts and narrative remain below for review.')
    from app.core.diagnostics import log_event
    log_event('reporting_draft',duration_ms=round((perf_counter()-started)*1000,1),status=status,
        provider=provider_name,model=get_settings().UNDERSTANDING_MODEL if provider_name!='local' else None,
        failure=reason,claim_count=len(claims['claims']))
    return dict(claims,text=text,portal_text=copy,provider=provider_name,status=status,failure=reason,warnings=warnings)
