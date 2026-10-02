"""AI chooses investigation; policy actions are inputs, never model output."""
import asyncio
import json
import re
from decimal import Decimal
from pydantic import ValidationError
from app.core.config import get_settings
from app.domain.policy import check_values
from app.domain.facts import names_payment_verification_target, normalize_payment_method
from app.schemas.next_move import NextMove
from app.services.ai_provider import get_provider, transient_provider_error

MAX_CONTEXT_CHARS = 24000


class MoveRejected(ValueError):
    """Bounded public diagnostic code, never raw provider content."""


def failure_category(exc):
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return 'TIMEOUT'
    if isinstance(exc, MoveRejected):
        return 'VALIDATION_REJECTED'
    if isinstance(exc, ValidationError):
        return 'MALFORMED_OUTPUT'
    status = getattr(exc, 'code', None)
    if isinstance(status, int):
        if status == 429:
            return 'PROVIDER_QUOTA'
        if status in (401, 403):
            return 'PROVIDER_AUTH'
        if status == 404:
            return 'PROVIDER_MODEL_UNAVAILABLE'
        return 'PROVIDER_5XX' if status >= 500 else 'PROVIDER_UNAVAILABLE'
    if type(exc).__module__.startswith(('httpx', 'google.genai')):
        return 'PROVIDER_UNAVAILABLE'
    return 'APPLICATION_ERROR'


def failure_reason(exc):
    # Exception messages may contain credentials/input. Store only bounded categories.
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return 'timeout'
    if getattr(exc, 'code', None) == 429:
        return 'quota'
    if getattr(exc, 'code', None) in (400, 401, 403, 404):
        return 'provider_rejected'
    return 'invalid_output' if isinstance(exc, ValueError) else 'provider_error'


def fact_context(facts):
    data = facts.model_dump(mode='json')
    data['provenance'] = [{'field': p.field, 'origin': p.origin, 'verified': p.verified,
        'confidence': p.confidence, 'source_turn': str(p.source_turn) if p.source_turn else None}
        for p in facts.provenance]
    return data


def build_context(facts, understanding, conflicts, turns, message, plan, evidence, answered, current_move=None):
    data = fact_context(facts)
    unknown = [field for field, value in data.items() if value in (None, 'unknown')
        and field not in {'occurred_at' if facts.time_window else ''} and field not in answered]
    context = dict(facts=data, unknown_fields=unknown, answered_fields=list(answered),
        conflicts=conflicts, candidates=[{'field': c['field'], 'value': c['value'],
            'status': c['status'], 'source_text': c['source_text'][:256],
            'uncertainty': c['uncertainty']} for c in understanding.get('candidates', [])],
        recent_conversation=[{'user': t.text[:1000],
            'assistant': (t.fact_changes.get('next_move') or {}).get('message', '')}
            for t in turns[-4:]], current_message=message[:8000], current_move=current_move,
        approved_actions=[{'id': a.id, 'title': a.title, 'instruction': a.instruction,
            'why': a.why, 'phase': a.phase.value} for a in plan.actions],
        evidence=evidence, evidence_restrictions=['no credentials', 'no identity documents',
            'no explicit intimate media', 'no child sexual abuse material'],
        capabilities={'safe_evidence_upload': True, 'ai_evidence_extraction': False},
        case_state={'has_applicable_actions': bool(plan.actions), 'intake_completion_required': False})
    return context


def unresolved_candidates(turns, result, updates, answered=()):
    pending = {}
    for turn in turns:
        for candidate in turn.fact_changes.get('understanding', {}).get('candidates', []):
            if candidate['status'] in {'needs_review', 'conflict'}:
                pending[candidate['field']] = candidate
            elif candidate['status'] == 'accepted':
                pending.pop(candidate['field'], None)
        for update in turn.fact_changes.get('updates', []):
            pending.pop(update['field'], None)
        if turn.fact_changes.get('field'):
            pending.pop(turn.fact_changes['field'], None)
        for field in turn.fact_changes.get('understanding', {}).get('resolved_reviews', []):
            pending.pop(field, None)
    for update in updates:
        pending.pop(update['field'], None)
    for candidate in result.get('candidates', []):
        if candidate['status'] in {'needs_review', 'conflict'}:
            pending[candidate['field']] = candidate
        elif candidate['status'] == 'accepted':
            pending.pop(candidate['field'], None)
    for field in result.get('resolved_reviews', []):
        pending.pop(field, None)
    # Not sure is a completed answer, not an invitation to verify the same
    # uncertain inference again. Keep actual contradictions available for review.
    active = []
    for c in pending.values():
        if c['field'] in answered and c['status'] != 'conflict':
            continue
        if c['field'] == 'payment_method':
            normalized = normalize_payment_method(c['value'])
            if normalized in (None, 'unknown'):
                continue
            c = dict(c, value=normalized)  # Historical JSON remains unchanged.
        active.append(c)
    return active[-32:]


def declined_fields(turns):
    declined = set()
    for turn in turns:
        if turn.fact_changes.get('answered_unknown'):
            declined.add(turn.fact_changes['answered_unknown'])
        for update in turn.fact_changes.get('updates', []):
            declined.discard(update['field'])
        if turn.fact_changes.get('field') and turn.fact_changes.get('after') not in (None, 'unknown'):
            declined.discard(turn.fact_changes['field'])
    return declined


# A question can reference known facts without asking for them again. The
# field contract, grounding checks and retrospective inquiry grammar work together.
QUESTION_START = re.compile(r'^(what|when|how|did|do|does|have|has|is|are|was|were|can|could|would|which|who|where|about when)\b', re.I)
NUMBER = re.compile(r'(?<!\w)\d[\d,]*(?:\.\d+)?(?!\w)')
OUTCOME = re.compile(r'\b(guarantee\w*|refund|recover\w*|revers\w*|eligib\w*|police|legal|fir|government|frozen|freez\w*)\b', re.I)
ACTION_VERB = r'call|contact|dial|pay|transfer|send|install|disconnect|disable|delete|block|change|reset|uninstall|submit|open|visit|click|report|withdraw|move|turn off|wipe|erase|reboot'
KNOWN_QUESTION_TERMS = {
    'money_lost': r'^(?:has|have|did|is)\b.*\b(money|funds|payment)\b.*\b(left|leave|gone|lost|sent|moved)\b',
    'amount': r'how much|what (?:was|is) the amount',
    'authorization': r'^(?:did|have|do|was|were)\b.*\b(approv\w*|authoriz\w*|authoris\w*|permission|consent)\b',
    'occurred_at': r'^(?:about when|when|how long|what time)\b',
    'payment_method': r'^(?:how.*(?:pay|sent|transfer)|what.*payment (?:method|rail))\b',
    'payment_app': r'\b(which|what) (app|payment app)\b',
    'transaction_id': r'^(?:what|do you have)\b.*\b(transaction reference|utr|transaction id)\b',
    'remote_access': r'^(?:can|does|is|has)\b.*\b(still|currently|now)\b.*\b(access|control|connected)\b',
    'account_compromised': r'^(?:can|does)\b.*\b(access|log in|login)\b.*\b(account)\b',
    'ongoing_loss': r'^(?:is|are)\b.*\b(still|continuing|ongoing|further)\b.*\b(money|loss|transactions|payments)\b',
    'evidence_available': r'^(?:do you have|have you saved)\b.*\b(evidence|screenshot|message|receipt|record)\b',
}
INQUIRY_TOPIC = {
    'money_lost': r'money|funds|payment|lost|loss', 'amount': r'amount|how much|sum|total',
    'authorization': r'approv|authoriz|authoris|permission|consent|you (?:send|sent|transfer|pay|paid|make|initiate)',
    'occurred_at': r'when|time|long|recent|ago', 'time_window': r'when|time|long|recent|ago',
    'payment_method': r'upi|card|bank|wallet|rail|method|neft|imps|rtgs|how.*(?:pay|sent|transfer)',
    'payment_app': r'app|gpay|phonepe|paytm', 'currency': r'currency|rupees|inr|usd',
    'transaction_id': r'reference|utr|transaction id', 'transaction_status': r'pending|completed|status',
    'remote_access': r'access|control|connect', 'account_compromised': r'access|log.?in|sign.?in',
    'credentials_exposed': r'access details|credentials|password|pin|otp|shared|exposed',
    'ongoing_loss': r'money|loss|transactions|payments|pay more',
    'evidence_available': r'evidence|screenshot|message|receipt|records',
    'evidence_mentioned': r'evidence|screenshot|message|receipt|records',
    'claimed_organization': r'organization|organisation|company|claim|represent',
    'claimed_person': r'who|claim|person', 'identifiers': r'contact|profile|phone|email|upi|url|account|identifier',
    'signals': r'what else|happened|incident',
}


def reject(code):
    raise MoveRejected(code)


def grounded_text(text, context):
    facts = context['facts']
    # Numbers may come from canonical facts or the candidates under review,
    # never merely from arbitrary provider output or an instruction in a story.
    sources = [str(value) for key, value in facts.items() if key not in {'provenance', 'fact_schema_version'} and value is not None]
    sources += [str(c['value']) for c in context['candidates'] if c['status'] in {'needs_review', 'conflict'}]
    allowed = {Decimal(n.replace(',', '')) for source in sources for n in NUMBER.findall(source)}
    for number in NUMBER.findall(text):
        if Decimal(number.replace(',', '')) not in allowed:
            reject('UNGROUNDED_NUMBER')
    currencies = {'\u20b9': 'INR', '$': 'USD', '\u20ac': 'EUR'}
    if any(symbol in text and facts.get('currency') != currency for symbol, currency in currencies.items()):
        reject('UNGROUNDED_CURRENCY')
    amount_values = {Decimal(facts['amount'])} if facts.get('amount') is not None else set()
    amount_values.update(Decimal(c['value']) for c in context['candidates']
        if c['field'] == 'amount' and c['status'] in {'needs_review', 'conflict'}
        and isinstance(c['value'], str) and re.fullmatch(r'\d+(?:\.\d+)?', c['value']))
    for number in re.findall(r'[\u20b9$\u20ac]\s*(\d[\d,]*(?:\.\d+)?)', text):
        if Decimal(number.replace(',', '')) not in amount_values:
            reject('UNGROUNDED_AMOUNT')
    for identifier in re.findall(r'\b[\w.+-]+@[\w.-]+', text):
        if not any(identifier == item['value'] for item in facts['identifiers']):
            reject('UNGROUNDED_IDENTIFIER')
    # Caller organization is never evidence of ownership of a named bank account.
    if re.search(r'\byour\s+(?!(?:bank|account)\b)[\w-]+(?:\s+bank)?\s+account\b|\byour\s+[\w-]+\s+bank\b', text, re.I):
        reject('UNSUPPORTED_ACCOUNT_OWNERSHIP')
    for url in re.findall(r'https?://[^\s?]+|www\.[^\s?]+', text):
        if not any(url.rstrip('.,') == item['value'] for item in facts['identifiers']):
            reject('UNSUPPORTED_URL')
    if OUTCOME.search(text):
        reject('AUTHORITATIVE_OUTCOME')
    # Exposure is a valid investigative topic; requesting the secret itself is not.
    if re.search(r'\b(?:what(?: is| was)?|tell|give|enter|type|share|upload|send|provide)\b.{0,60}\b(?:otp|pin|password|credentials|card number|cvv|aadhaar|passport|intimate|nude|explicit)\b', text, re.I):
        reject('RESTRICTED_INFORMATION_REQUEST')
    if re.search(r'\b(?:you (?:should|must|need to|have to|can|could)|please|then|and)\s+(?:' + ACTION_VERB + r')\b', text, re.I):
        reject('ACTION_IN_INVESTIGATION')
    if re.search(r'^(?:' + ACTION_VERB + r')\b', text, re.I):
        reject('ACTION_IN_INVESTIGATION')
    check_values(text)


def valid_reply(reply, field):
    normalized = reply.lower().strip().rstrip('.')
    if normalized in {'not sure', "i don't know", 'unsure'}:
        return True
    if field in SAFE_REPLIES:
        if normalized in {'yes', 'no'} and field != 'authorization':
            return True
        if field == 'authorization':
            return bool(re.fullmatch(r'i (?:did not approve (?:it|the payment|the transaction)|approved (?:it|the payment|the transaction)(?: after deception)?)', normalized))
    return False


def validate_move(move, context):
    facts, field = context['facts'], move.related_field
    if move.type == 'EXPLAIN_APPROVED_ACTION':
        action = next((a for a in context['approved_actions'] if a['id'] == move.action_id), None)
        if action is None:
            reject('ACTION_NOT_APPLICABLE')
        # The authoritative instruction always comes from the versioned playbook.
        return move.model_copy(update={'message': action['instruction'] + ' ' + action['why']})
    text = move.message.strip()
    grounded_text(text, context)
    if move.type == 'ACKNOWLEDGE_AND_WAIT':
        # Accept complete supportive sentences and checkable canonical financial
        # statements. A friendly prefix cannot authorize the rest of a sentence.
        sentences = [s.strip() for s in re.split(r'[.!](?=\s|$)', text) if s.strip()]
        support = r"(?:ready when you are|take your time|i(?:'m| am) here(?: when you are ready)?|you can (?:keep typing here|keep telling me what happened(?: when you are ready)?|continue (?:your story|when you are ready)|add to your story(?: or correct a detail)?(?: whenever you are ready)?|correct a detail(?: whenever you are ready)?))"
        grounded = r'(?!)'
        if facts['money_lost'] is True:
            amount = Decimal(facts['amount']) if facts['amount'] is not None else None
            formatted = f'{amount:,.2f}'.rstrip('0').rstrip('.') if amount is not None else 'Money'
            if amount is not None:
                formatted = ('\u20b9' + formatted) if facts['currency'] == 'INR' else formatted + (f" {facts['currency']}" if facts['currency'] else '')
            approval = {'unauthorized': r' and you did not approve (?:it|the payment|the transaction)',
                'authorized': r' and you approved (?:it|the payment|the transaction)', 'unknown': r'(?!)'}[facts['authorization']]
            grounded = r'(?:i understand(?: that)?[,:]? )?' + re.escape(formatted) + r' (?:left|was lost|is gone)(?:' + approval + r')?'
        if text.count('?') or not all(re.fullmatch(support, sentence, re.I) or re.fullmatch(grounded, sentence, re.I) or sentence.lower() == 'i understand' for sentence in sentences):
            reject('UNSUPPORTED_ACKNOWLEDGEMENT_CLAIM')
        return move.model_copy(update={'message': text})
    if move.type == 'REQUEST_EVIDENCE':
        if context['evidence'] or facts['evidence_available'] is False:
            reject('EVIDENCE_PRESENT_OR_UNAVAILABLE')
        relevant = bool(facts['evidence_mentioned']) or any(c['field'] == 'evidence_available' for c in context['candidates'])
        relevant |= bool(facts['money_lost'] and move.evidence_kind in {'transaction_message', 'transaction_receipt'})
        relevant |= bool(facts['identifiers'] and move.evidence_kind == 'profile_identifier')
        relevant |= bool(set(facts['signals']) & {'threats', 'harassment', 'impersonation'} and move.evidence_kind == 'non_explicit_conversation')
        if not relevant:
            reject('EVIDENCE_NOT_RELEVANT')
        if re.search(r'\b(extract|ocr|read|analyse|analyze|identify)\b', text, re.I):
            reject('UNAVAILABLE_EVIDENCE_CAPABILITY')
        if text.count('?') > 1:
            reject('MULTIPLE_QUESTIONS')
        # Validate the evidence invitation as a whole. An invitation prefix cannot
        # smuggle identity-document requests, invented capabilities or advice.
        record = r'(?:the |that |a |an )?(?:transaction |sms |safe |non-explicit )?(?:message|receipt|screenshot|conversation|profile details)'
        invitation = (
            r'(?:could|would|can) you (?:optionally )?(?:share|save|upload) ' + record + r'\?'
            r'|do you (?:still )?have ' + record + r'\?'
            r'|if you (?:still )?have ' + record + r',? you can (?:optionally )?(?:save|upload) (?:a |the )?(?:safe |non-explicit )?screenshot(?: with this case| here)?[.]?'
        )
        if not re.fullmatch(invitation, text, re.I):
            reject('UNSUPPORTED_EVIDENCE_INVITATION')
        return move.model_copy(update={'message': text, 'related_field': 'evidence_available', 'quick_replies': []})
    if move.type == 'RESOLVE_CONFLICT':
        if field not in context['conflicts']:
            reject('NO_CONFLICT')
    elif move.type == 'VERIFY_INFORMATION':
        if field in context['answered_fields']:
            reject('ALREADY_ANSWERED')
        if not any(c['field'] == field and c['status'] == 'needs_review' for c in context['candidates']):
            reject('NO_UNRESOLVED_CANDIDATE')
    elif move.type == 'ASK_CLARIFICATION':
        if field not in context['unknown_fields']:
            reject('FACT_ESTABLISHED_OR_ANSWERED')
    if not QUESTION_START.search(text) or text.count('?') != 1 or not text.endswith('?'):
        reject('ONE_INVESTIGATIVE_QUESTION_REQUIRED')
    if field != 'story' and not re.search(INQUIRY_TOPIC[field], text, re.I):
        reject('QUESTION_FIELD_MISMATCH')
    if re.search(r'[!;\n]|\.(?!\d)', text):
        reject('EXTRA_SENTENCE_OR_INSTRUCTION')
    if re.search(r'\b(?:how (?:can|do|could|should|would)|how to|steps to|instructions to|should you|must you)\b', text, re.I):
        reject('PROCEDURE_IS_NOT_INVESTIGATION')
    # Can/Could/Would you requests must investigate capability or invite a story,
    # rather than issue a protective/financial instruction disguised as a question.
    if re.match(r'^(can|could|would) you\b', text, re.I) and not re.match(
        r'^(can|could|would) you (still )?(tell|describe|remember|recall|access|log in|sign in)\b', text, re.I):
        reject('PROSPECTIVE_INSTRUCTION')
    if re.search(r'\b(?:' + ACTION_VERB + r')\b', text, re.I):
        verbs = re.findall(r'\b(?:' + ACTION_VERB + r')\b', text, re.I)
        past_payment = field in {'authorization', 'payment_method'} and re.match(r'^(did you|have you|how did you)\b', text, re.I)
        ongoing_inquiry = field == 'ongoing_loss' and re.match(r'^is money\b', text, re.I)
        if not (past_payment or ongoing_inquiry) or any(v.lower() not in {'send', 'pay', 'transfer', 'move'} for v in verbs):
            reject('ACTION_IN_INVESTIGATION')
    for known, pattern in KNOWN_QUESTION_TERMS.items():
        established = facts.get(known) not in (None, 'unknown', []) or known in context['answered_fields']
        if known == 'occurred_at' and facts['time_window']:
            established = True
        if established and re.search(pattern, text, re.I) and not (known == field and move.type == 'RESOLVE_CONFLICT'):
            reject('REPEATED_ESTABLISHED_FACT')
    # Bind every payment confirmation to the displayed target, even without buttons.
    targets = [c for c in context['candidates'] if c['field'] == 'payment_method' and c['status'] == 'needs_review']
    confirmation_replies = (move.type == 'VERIFY_INFORMATION' and field == 'payment_method'
        and len(targets) == 1 and normalize_payment_method(targets[0]['value']) not in (None, 'unknown')
        and names_payment_verification_target(text, targets[0]['value']))
    if move.type == 'VERIFY_INFORMATION' and field == 'payment_method' and not confirmation_replies:
        reject('VERIFICATION_TARGET_MISMATCH')
    if any(not (valid_reply(reply, field) or (confirmation_replies and reply.strip().casefold() in {'yes', 'no'})) for reply in move.quick_replies):
        reject('UNSUPPORTED_QUICK_REPLY')
    check_values(move.model_dump(mode='json'))
    return move.model_copy(update={'message': text})


QUESTIONS = {
    'money_lost': 'Has any money left your account or been sent because of this incident?',
    'authorization': 'Did you approve the payment, or did it happen without your approval?',
    'amount': 'What amount was sent or lost?', 'currency': 'Which currency was the payment in?',
    'occurred_at': 'About when did this happen?', 'time_window': 'About when did this happen?',
    'payment_app': 'Which app was involved?', 'payment_method': 'How was the payment made?',
    'transaction_id': 'Do you have a transaction reference?', 'transaction_status': 'Does the transaction show as pending or completed?',
    'claimed_organization': 'Which organization did the person claim to represent?',
    'claimed_person': 'Who did the person claim to be?', 'identifiers': 'Which contact or profile was involved?',
    'signals': 'What else happened during this incident?',
    'remote_access': 'Can someone else still access or control your device?',
    'account_compromised': 'Can someone else access your account?',
    'credentials_exposed': 'Were any access details exposed? Please do not type the details themselves.',
    'ongoing_loss': 'Is money still moving or are you being asked to pay more?',
    'evidence_available': 'Do you have safe records of what happened?',
    'evidence_mentioned': 'What safe records of this incident do you have?',
}
SAFE_REPLIES = {field: {'Yes', 'No', 'Not sure'} for field in
    ('money_lost','remote_access','account_compromised','credentials_exposed','ongoing_loss','evidence_available')}
SAFE_REPLIES['authorization'] = {'I approved the payment', 'I did not approve the payment', 'Not sure'}


async def _decide(provider, context, settings):
    async def attempts():
        for attempt in range(settings.UNDERSTANDING_RETRIES + 1):
            try:
                return await provider.decide(context)
            except Exception as exc:
                if attempt == settings.UNDERSTANDING_RETRIES or not transient_provider_error(exc):
                    raise
                from app.core.diagnostics import log_event
                log_event('ai_retry', stage='follow_up', attempt=attempt + 1,
                          error_type=type(exc).__name__, http_status=getattr(exc, 'code', None))
                await asyncio.sleep(0.25)
    return await asyncio.wait_for(attempts(), timeout=settings.UNDERSTANDING_TIMEOUT_SECONDS)


def decide(context):
    settings = get_settings()
    diagnostics = {'status': 'fallback', 'reason': 'unavailable', 'category': 'PROVIDER_UNAVAILABLE',
        'provider': settings.UNDERSTANDING_PROVIDER, 'model': settings.UNDERSTANDING_MODEL,
        'provider_initialized': False, 'invocation_succeeded': False, 'parsing_succeeded': False,
        'validation_succeeded': False, 'proposed_type': None, 'rejection_reason': None}
    try:
        provider = get_provider()
        if provider is None:
            return None, diagnostics
        diagnostics['provider_initialized'] = True
        encoded = json.dumps(context, ensure_ascii=False)
        if len(encoded) > MAX_CONTEXT_CHARS:
            return None, dict(diagnostics, reason='context_limit', category='VALIDATION_REJECTED')
        check_values(context)
        output = asyncio.run(_decide(provider, encoded, settings))
        diagnostics['invocation_succeeded'] = True
        if len(output) > settings.UNDERSTANDING_MAX_OUTPUT_CHARS:
            reject('OUTPUT_LIMIT')
        proposed = NextMove.model_validate_json(output)
        diagnostics.update(parsing_succeeded=True, proposed_type=proposed.type)
        move = validate_move(proposed, context)
        return move, dict(diagnostics, status='decided', reason=None, category=None, validation_succeeded=True)
    except Exception as exc:
        return None, dict(diagnostics, reason=failure_reason(exc), category=failure_category(exc),
            validation_errors=[{'loc': list(e['loc']), 'type': e['type']} for e in exc.errors()[:8]] if isinstance(exc, ValidationError) else [],
            rejection_reason=str(exc) if isinstance(exc, MoveRejected) else None,
            error_type=type(exc).__name__,
            http_status=getattr(exc, 'code', None) if isinstance(getattr(exc, 'code', None), int) else None)


def acknowledge(facts, updates):
    fields = {u['field'] for u in updates}
    if fields & {'money_lost', 'amount', 'authorization'} and facts.money_lost:
        amount = ('₹' + f'{facts.amount:,.2f}'.rstrip('0').rstrip('.')) if facts.amount is not None and facts.currency == 'INR' else (
            f'{facts.amount:,.2f}'.rstrip('0').rstrip('.') + (f' {facts.currency}' if facts.currency else '') if facts.amount is not None else 'Money')
        approval = {'unauthorized': ' and you did not approve the transaction',
            'authorized': ' and you approved the payment', 'unknown': ''}[facts.authorization]
        prefix = 'I’ve updated the amount. ' if any(u['field'] == 'amount' and u['correction'] for u in updates) else 'I understand. '
        return prefix + amount + ' left' + approval + '.'
    if fields & {'signals', 'remote_access', 'account_compromised'}:
        return 'I’ve added those details to the working understanding of your case.'
    if updates:
        return 'I’ve updated the working understanding from what you told me. You can correct it at any time.'
    return 'Your message is saved with this case.'
