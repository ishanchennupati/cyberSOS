"""Validate grounded candidates; never evaluate or manufacture response actions."""
import asyncio
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
from pydantic import ValidationError
from app.core.config import get_settings
from app.domain.facts import ApproximateTime, FACTS_ADAPTER, FactProvenance, names_payment_verification_target, normalize_payment_method
from app.domain.policy import check_values
from app.schemas.understanding import Understanding
from app.services.ai_provider import get_provider, transient_provider_error

KINDS = {'authorized': 'financial_scam_transfer', 'unauthorized': 'unauthorized_financial_transaction', 'unknown': 'financial_authorization_unknown'}


def resolve_time(phrase: str, timestamp: datetime, zone: str) -> ApproximateTime | None:
    local = timestamp.astimezone(ZoneInfo(zone))
    phrase_lower = phrase.lower().strip()
    phrase_lower = re.sub(r'^(about|approximately|around)\s+', '', phrase_lower)
    phrase_lower = re.sub(r'^(a|an)\s+(hour|minute)\b', r'one \2', phrase_lower)
    aliases = {'నిన్న సాయంత్రం': 'yesterday evening', 'ninna sayantram': 'yesterday evening',
        'कल शाम': 'yesterday evening', 'kal shaam': 'yesterday evening',
        'ఈ ఉదయం': 'this morning', 'ee roju udayam': 'this morning',
        'आज सुबह': 'this morning', 'aaj subah': 'this morning',
        'నిన్న రాత్రి': 'last night', 'ninna ratri': 'last night',
        'कल रात': 'last night', 'kal raat': 'last night',
        'పది నిమిషాల క్రితం': 'ten minutes ago', 'padi nimishala kritam': 'ten minutes ago',
        'दस मिनट पहले': 'ten minutes ago', 'dus minute pehle': 'ten minutes ago'}
    phrase_lower = aliases.get(phrase_lower, phrase_lower)
    words = {'one': 1, 'two': 2, 'five': 5, 'ten': 10, 'twenty': 20, 'thirty': 30}
    match = re.fullmatch(r'(\d+|one|two|five|ten|twenty|thirty)\s+(minutes?|hours?)\s+ago', phrase_lower)
    if match:
        quantity = int(match[1]) if match[1].isdigit() else words[match[1]]
        # Longer relative intervals need review; prevent datetime arithmetic overflow.
        if quantity > (525600 if match[2].startswith('minute') else 8760):
            return None
        delta = timedelta(minutes=quantity) if match[2].startswith('minute') else timedelta(hours=quantity)
        point = local - delta
        margin = timedelta(minutes=1 if match[2].startswith('minute') else 15)
        start, end = point - margin, min(point + margin, local)
    elif phrase_lower in {'yesterday evening', 'this morning', 'last night'}:
        day = local.replace(hour=0, minute=0, second=0, microsecond=0)
        if phrase_lower == 'this morning':
            start, end = day + timedelta(hours=5), min(day + timedelta(hours=12), local)
        elif phrase_lower == 'yesterday evening':
            start, end = day - timedelta(hours=6), day - timedelta(hours=2)
        else:
            start, end = day - timedelta(hours=6), min(day + timedelta(hours=5), local)
        if start > end:
            return None
    else:
        return None  # Keep unsupported/multilingual phrases as candidates, never guess.
    return ApproximateTime(start=start.astimezone(timezone.utc), end=end.astimezone(timezone.utc), original=phrase, timezone=zone)


async def _extract(provider, message, context, settings):
    async def attempts():
        for attempt in range(settings.UNDERSTANDING_RETRIES + 1):
            try:
                return await provider.extract(message, context)
            except Exception as exc:
                if attempt == settings.UNDERSTANDING_RETRIES or not transient_provider_error(exc):
                    raise
                from app.core.diagnostics import log_event
                log_event('ai_retry', stage='extraction', attempt=attempt + 1,
                          error_type=type(exc).__name__, http_status=getattr(exc, 'code', None))
                await asyncio.sleep(0.25)
    return await asyncio.wait_for(attempts(), timeout=settings.UNDERSTANDING_TIMEOUT_SECONDS)


def interpret(message, facts, turn_id, timestamp, zone, pending_question=None, recent_turns=()):
    settings = get_settings()
    fallback = {'status': 'fallback', 'message': 'Automatic understanding is unavailable. Please answer one focused question; you can still continue.', 'candidates': [], 'conflicts': [],
        'provider_initialized': False, 'invocation_succeeded': False, 'parsing_succeeded': False,
        'category': 'PROVIDER_UNAVAILABLE', 'reason': 'unavailable', 'provider': settings.UNDERSTANDING_PROVIDER,
        'model': settings.UNDERSTANDING_MODEL}
    check_values(message)
    if len(message) > settings.UNDERSTANDING_MAX_INPUT_CHARS:
        return facts, [], fallback
    provider = get_provider()
    if provider is None:
        return facts, [], fallback
    fallback['provider_initialized'] = True
    try:
        from app.services.case_agent import fact_context, failure_reason, MAX_CONTEXT_CHARS, unresolved_candidates
        verification_candidate = None
        if pending_question and pending_question.get('type') == 'VERIFY_INFORMATION' and pending_question.get('related_field') == 'payment_method':
            targets = [c for c in unresolved_candidates(recent_turns, {}, [])
                if c['field'] == 'payment_method' and c['status'] == 'needs_review' and c['value'] != 'unknown']
            if len(targets) == 1 and names_payment_verification_target(pending_question.get('message', ''), targets[0]['value']):
                verification_candidate = {'field': 'payment_method', 'value': targets[0]['value']}
        context = json.dumps({'facts': fact_context(facts), 'question': pending_question,
            'verification_candidate': verification_candidate,
            'recent_conversation': [{'user': turn.text[:500]} for turn in recent_turns[-4:]],
            'timestamp': timestamp.isoformat(), 'timezone': zone})
        if len(context) > MAX_CONTEXT_CHARS:
            return facts, [], dict(fallback, reason='context_limit', category='VALIDATION_REJECTED')
        output = asyncio.run(_extract(provider, message, context, settings))
        fallback['invocation_succeeded'] = True
        if len(output) > settings.UNDERSTANDING_MAX_OUTPUT_CHARS:
            return facts, [], dict(fallback, reason='output_limit', category='MALFORMED_OUTPUT')
        parsed = Understanding.model_validate_json(output)
        check_values(parsed.model_dump(mode='json'))
    except Exception as exc:
        # Provider errors may include user input/key; never log or expose them.
        from app.services.case_agent import failure_reason, failure_category
        # Pydantic locations/types help diagnose malformed structured responses;
        # never include its input, error message or raw provider response.
        errors = [{'loc': list(e['loc']), 'type': e['type']} for e in exc.errors()[:8]] if isinstance(exc, ValidationError) else []
        return facts, [], dict(fallback, reason=failure_reason(exc), category=failure_category(exc), validation_errors=errors, error_type=type(exc).__name__,
            http_status=getattr(exc, 'code', None) if isinstance(getattr(exc, 'code', None), int) else None)
    data = facts.model_dump(mode='json')
    if parsed.language != 'unknown':
        data['detected_language'] = parsed.language
        language_source = message[:160]
        language_provenance = FactProvenance(field='detected_language', origin='ai_extraction',
            source_turn=turn_id, source_text=language_source, source_start=0, source_end=len(language_source),
            uncertainty='Language detection is provisional.')
        data['provenance'] = [p for p in data['provenance'] if p['field'] != 'detected_language'] + [language_provenance.model_dump(mode='json')]
    updates, conflicts, reviewed, resolved_reviews = [], [], [], []
    duplicates = {c.field for c in parsed.candidates if sum(other.field == c.field for other in parsed.candidates) > 1}
    # Loss must be established before authorization can select a financial branch.
    for candidate in sorted(parsed.candidates, key=lambda c: c.field != 'money_lost'):
        item = candidate.model_dump(mode='json')
        item['source_turn'] = str(turn_id)
        item['status'] = 'rejected'
        start = message.find(candidate.source_text)
        if start < 0:
            reviewed.append(item)
            continue
        item.update(source_start=start, source_end=start + len(candidate.source_text))
        field, value = candidate.field, item['value']
        if field == 'payment_method':
            value = normalize_payment_method(value)
            if value is None:
                reviewed.append(item)
                continue
            item['value'] = value
        if field in duplicates:
            item['status'] = 'conflict'
            conflicts.append(field)
            reviewed.append(item)
            continue
        # Uncertain/inferred candidates remain visible, but cannot drive playbooks.
        if candidate.extraction != 'explicit' or candidate.uncertainty or candidate.confidence < 0.8:
            item['status'] = 'needs_review'
            reviewed.append(item)
            continue
        source = candidate.source_text
        confirmed = False
        if candidate.confirms_pending is not None:
            if not verification_candidate or value != verification_candidate['value']:
                reviewed.append(item)
                continue
            if not candidate.confirms_pending:
                resolved_reviews.append(field)
                reviewed.append(item)
                continue
            confirmed = True
        if field in {'payment_app', 'claimed_organization', 'claimed_person', 'transaction_id'} and value.casefold() not in source.casefold():
            reviewed.append(item)
            continue
        if field == 'identifiers' and not all(v['value'] in source for v in value):
            reviewed.append(item)
            continue
        if field == 'amount':
            numbers = []
            for m in re.finditer(r'(?<!\w)(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|lakh)?\b', source, re.I):
                multiplier = {'k': 1000, 'thousand': 1000, 'lakh': 100000}.get((m[2] or '').lower(), 1)
                numbers.append(Decimal(m[1].replace(',', '')) * multiplier)
            try:
                if Decimal(value) not in numbers:
                    reviewed.append(item)
                    continue
            except Exception:
                reviewed.append(item)
                continue
        if field == 'payment_method' and value != 'unknown' and not confirmed:
            rail_terms = {'upi': ['upi'], 'bank_transfer': ['bank transfer', 'neft', 'imps', 'rtgs'],
                'debit_card': ['debit card'], 'credit_card': ['credit card'],
                'net_banking': ['net banking', 'internet banking', 'online banking'], 'wallet': ['wallet']}
            source_words = re.sub(r'[_-]+', ' ', source.casefold())
            if not any(re.search(r'\b' + re.escape(term) + r'\b', source_words) for term in rail_terms.get(value, [])):
                reviewed.append(item)
                continue
        current_access_answer = bool(pending_question and
            (pending_question.get('related_field') or pending_question.get('field')) == 'remote_access' and
            source.strip().casefold() in {'yes', 'avunu', 'haan', 'అవును', 'हाँ', 'हां'})
        if field == 'remote_access' and value is True and not current_access_answer and not re.search(r'\b(still|currently|ongoing|now|inka|abhi)\b|ఇంకా|అప్పటికీ|अभी|अब भी', source, re.I):
            item['status'] = 'needs_review'
            reviewed.append(item)
            continue
        if field == 'currency' and value not in source.upper() and not (value == 'INR' and ('₹' in source or re.search(r'rupees?|rs\.?', source, re.I))):
            reviewed.append(item)
            continue
        if field == 'time_window':
            if value not in source:
                reviewed.append(item)
                continue
            resolved = resolve_time(value, timestamp, zone)
            if resolved is None:
                item['status'] = 'needs_review'
                reviewed.append(item)
                continue
            value = resolved.model_dump(mode='json')
        before = data[field]
        # Compare canonical serialization, including decimal normalization.
        if field == 'amount' and before is not None and Decimal(before) == Decimal(value):
            value = before
        correction = bool(candidate.correction_source and candidate.correction_source in message and
            re.search(r'\b(sorry|correction|correct|actually|instead|galti|maaf|kaadu|kadu)\b|సారీ|క్షమించ|తప్పు|కాదు|माफ|गलती|सुधार', candidate.correction_source, re.I))
        # A complete, explicit amount correction remains citizen authority even
        # if the provider omitted its optional correction_source metadata. This
        # runs only after the candidate's confidence and numeric grounding checks.
        # An apology elsewhere in a story cannot authorize an overwrite.
        if field == 'amount' and not correction:
            amount_correction = re.fullmatch(
                r'\s*(?:sorry\s*,?\s*(?:the amount (?:was|is)\s+)|'
                r'correction\s*:\s*(?:the amount (?:was|is)\s+)?)'
                r'(?:₹\s*|INR\s*|Rs\.?\s*)?(\d[\d,]*(?:\.\d+)?)\s*[.!]?\s*',
                message, re.I)
            correction = bool(amount_correction and
                Decimal(amount_correction[1].replace(',', '')) == Decimal(value))
        if pending_question and pending_question.get('type') == 'RESOLVE_CONFLICT' and pending_question.get('related_field') == field:
            # A grounded answer to an explicit conflict prompt is a resolution;
            # citizens need not prepend a magic correction word.
            correction = True
        if before not in (None, 'unknown', [], ()) and before != value and field not in {'signals', 'identifiers', 'evidence_mentioned'} and not correction:
            item['status'] = 'conflict'
            conflicts.append(field)
            reviewed.append(item)
            continue
        if field in {'signals', 'identifiers', 'evidence_mentioned'}:
            value = before + [v for v in value if v not in before]
        proposed = dict(data)
        proposed[field] = value
        if field == 'authorization' and data['kind'] == 'incident_understanding' and proposed['money_lost'] is not True:
            item['status'] = 'needs_review'
            reviewed.append(item)
            continue
        if field == 'authorization' and proposed['money_lost'] is not False:
            proposed['kind'] = KINDS.get(value, 'invalid')
        if field == 'money_lost':
            proposed['kind'] = KINDS[proposed['authorization']] if value else 'incident_understanding'
            if value is False:
                proposed['authorization'] = 'unknown'
        p = FactProvenance(field=field, origin='user_verification' if confirmed else 'ai_extraction',
            verified=confirmed, source_turn=turn_id,
            source_text=source, source_start=start, source_end=start + len(source), confidence=candidate.confidence)
        proposed['provenance'] = [p for p in data['provenance'] if p['field'] != field] + [p.model_dump(mode='json')]
        try:
            validated = FACTS_ADAPTER.validate_python(proposed)
        except (ValidationError, ValueError):
            reviewed.append(item)
            continue
        data = validated.model_dump(mode='json')
        updates.append({'field': field, 'before': before, 'after': data[field], 'correction': correction})
        item['status'] = 'accepted'
        reviewed.append(item)
    return FACTS_ADAPTER.validate_python(data), updates, {'status': 'understood', 'language': parsed.language,
        'provider': settings.UNDERSTANDING_PROVIDER, 'model': settings.UNDERSTANDING_MODEL, 'category': None,
        'provider_initialized': True, 'invocation_succeeded': True, 'parsing_succeeded': True,
        'message': 'Working understanding from your words. You can review or correct it.',
        'candidates': reviewed, 'conflicts': conflicts, 'resolved_reviews': resolved_reviews}
