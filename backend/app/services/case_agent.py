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
    from app.services.case_memory import derive_memory, recall
    from app.services.knowledge import relevant_knowledge
    answered = set(answered)
    if answered & {'occurred_at','time_window'}: answered.update({'occurred_at','time_window'})
    try:
        knowledge = relevant_knowledge(message)
        retrieval_status = 'found' if knowledge else 'no_support'
    except Exception:
        knowledge, retrieval_status = [], 'unavailable'
    data = fact_context(facts)
    unknown = [field for field, value in data.items() if value in (None, 'unknown')
        and field not in {'occurred_at' if facts.time_window else ''} and field not in answered]
    if not facts.signals and 'signals' not in answered:
        unknown.append('signals')
    if facts.payment_method.value in {'upi','bank_transfer','net_banking','debit_card','credit_card'}:
        unknown = [field for field in unknown if field != 'bank_involved']
    transaction_established = facts.money_lost is True and (facts.authorization != 'unknown' or
        facts.payment_method.value != 'unknown' or facts.bank_involved is True or facts.transaction_id is not None)
    if not transaction_established:
        payment_details={'authorization','payment_method','payment_app','transaction_id','transaction_status','bank_involved','currency'}
        unknown=[field for field in unknown if field not in payment_details]
    context = dict(facts=data, unknown_fields=unknown, answered_fields=list(answered),
        conflicts=conflicts, candidates=[{'field': c['field'], 'value': c['value'],
            'status': c['status'], 'source_text': c['source_text'][:256],
            'uncertainty': c['uncertainty']} for c in understanding.get('candidates', [])],
        recent_conversation=recall(turns, message)['recent'],
        memory=derive_memory(facts, turns, conflicts, message),
        knowledge=knowledge, retrieval_status=retrieval_status,
        current_message=message[:8000], current_move=current_move,
        approved_actions=[{'id': a.id, 'title': a.title, 'instruction': a.instruction,
            'why': a.why, 'phase': a.phase.value, 'phone': a.phone} for a in plan.actions],
        evidence=evidence, evidence_restrictions=['no credentials', 'no identity documents',
            'no explicit intimate media', 'no child sexual abuse material'],
        capabilities={'safe_evidence_upload': True, 'ai_evidence_extraction': True},
        case_state={'has_applicable_actions': bool(plan.actions), 'intake_completion_required': False,
            'transaction_established':transaction_established})
    # Preserve canonical truth and the current message. Recall is expendable,
    # whereas truncating facts would change the meaning of the case.
    while len(json.dumps(context, ensure_ascii=False)) > MAX_CONTEXT_CHARS and context['memory']['older_recall']:
        context['memory']['older_recall'].pop(0)
    while len(json.dumps(context, ensure_ascii=False)) > MAX_CONTEXT_CHARS and context['recent_conversation']:
        context['recent_conversation'].pop(0)
    while len(json.dumps(context, ensure_ascii=False)) > MAX_CONTEXT_CHARS and context['evidence']:
        context['evidence'] = context['evidence'][:-1]
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
            if update['field'] in {'occurred_at','time_window'}: declined.difference_update({'occurred_at','time_window'})
        if turn.fact_changes.get('field') and turn.fact_changes.get('after') not in (None, 'unknown'):
            declined.discard(turn.fact_changes['field'])
    return declined


# A question can reference known facts without asking for them again. The
# field contract, grounding checks and retrospective inquiry grammar work together.
QUESTION_START = re.compile(r'^(what|when|how|did|do|does|have|has|is|are|was|were|can|could|would|which|who|where|about when)\b', re.I)
NUMBER = re.compile(r'(?<!\w)\d[\d,]*(?:\.\d+)?(?!\w)')
OUTCOME = re.compile(r'\b(guarantee\w*|refund|recover\w*|revers\w*|eligib\w*|liability|illegal|frozen|freez\w*)\b', re.I)
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
    'platform': r'platform|service|app|account|website',
    'immediate_danger': r'safe|danger|physical|hurt|threat',
    'blackmail': r'blackmail|demand|threat|pay',
    'private_image_threat': r'private|image|photo|threat',
    'message_text': r'message|text|said', 'threat_text': r'threat|message|text|said',
    'timestamp_text': r'when|time|date', 'recipient': r'recipient|sent|paid|who',
    'bank_involved': r'bank|account|payment|wallet',
}


def reject(code):
    raise MoveRejected(code)


def grounded_text(text, context):
    facts = context['facts']
    # Numbers may come from canonical facts or the candidates under review,
    # never merely from arbitrary provider output or an instruction in a story.
    sources = [str(value) for key, value in facts.items() if key not in {'provenance', 'fact_schema_version'} and value is not None]
    sources += [str(c['value']) for c in context['candidates'] if c['status'] in {'needs_review', 'conflict'}]
    sources += [item['text'] for item in context.get('knowledge', [])]
    sources += [item['phone'] for item in context.get('approved_actions', []) if item.get('phone')]
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
    for ownership in re.finditer(r'\byour\s+(?!(?:bank|account)\b)([\w-]+)(?:\s+bank)?\s+account\b|\byour\s+([\w-]+)\s+bank\b', text, re.I):
        named = ownership.group(1) or ownership.group(2)
        if ownership.group(2) or ' bank ' in ownership.group(0).casefold() or named.casefold() != (facts.get('platform') or '').casefold():
            reject('UNSUPPORTED_ACCOUNT_OWNERSHIP')
    for url in re.findall(r'https?://[^\s?]+|www\.[^\s?]+', text):
        if not any(url.rstrip('.,') == item['value'] for item in facts['identifiers']) and not any(
            url.rstrip('.,/') == item['url'].rstrip('/') for item in context.get('knowledge', [])):
            reject('UNSUPPORTED_URL')
    if OUTCOME.search(text):
        reject('AUTHORITATIVE_OUTCOME')
    # Exposure is a valid investigative topic; requesting the secret itself is not.
    if re.search(r'\b(?:what(?: is| was)?|tell|give|enter|type|share|upload|send|provide|attach|report)\b.{0,60}\b(?:otp|pin|password|credentials|card number|cvv|aadhaar|passport|intimate|nude|explicit)\b', text, re.I):
        reject('RESTRICTED_INFORMATION_REQUEST')
    # Explaining why a question improves an already approved report adds no
    # procedure. Other verbs/targets and secret requests remain prohibited.
    instruction_text = re.sub(r'\bso you can report\b','so reporting',text,flags=re.I) if re.match(r'^I ask\b',text,re.I) and context.get('approved_actions') else text
    if re.search(r'\b(?:you (?:should|must|need to|have to|can|could)|please)\s+(?:' + ACTION_VERB + r')\b', instruction_text, re.I):
        reject('ACTION_IN_INVESTIGATION')
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        for conjunction in re.finditer(r'\b(?:and|then)\s+(?:now\s+)?(?:'+ACTION_VERB+r')\b',sentence,re.I):
            history=sentence[:conjunction.start()]
            if not re.search(r'\b(?:had you|made you|asked you|told you|you reported|you said|you were|led you)\b',history,re.I):
                reject('ACTION_IN_INVESTIGATION')
    if re.search(r'(?:^|[.!?]\s+)(?:' + ACTION_VERB + r')\b', text, re.I):
        reject('ACTION_IN_INVESTIGATION')
    if re.search(r'(?:[,;:]\s*|\b(?:should|must|need to|have to)\s+)(?:' + ACTION_VERB + r')\b', text, re.I):
        reject('ACTION_IN_INVESTIGATION')
    if re.search(r'\b(?:you (?:should|must|need to|have to|can|could)|please)\s+(?:\w+\s+){0,3}(?:'+ACTION_VERB+r')\b',instruction_text,re.I):
        reject('ACTION_IN_INVESTIGATION')
    if re.search(r'\b(?:can|could|would) you\s+(?:\w+\s+){0,2}(?:'+ACTION_VERB+r')\b',text,re.I):
        reject('PROSPECTIVE_INSTRUCTION')
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
    """Validate references, applicability, grounding and safety, not sentence grammar."""
    facts, field = context['facts'], move.related_field
    text = move.message.strip()
    if move.type in {'ASK_CLARIFICATION', 'CONTINUE_OPEN_CONVERSATION', 'ANSWER_RELEVANT_QUESTION'} and context.get('case_state',{}).get('transaction_established') is False and '?' in text and re.search(
        r'what payment method|which payment|how did you pay|(?:this|the) (?:transaction|payment)|did you approve',text,re.I):
        reject('UNSUPPORTED_TRANSACTION_PREMISE')
    if context.get('memory', {}).get('questions_paused') and ('?' in text or move.type == 'REQUEST_EVIDENCE'):
        reject('QUESTIONS_PAUSED')
    for reference in move.fact_refs:
        if facts.get(reference.field) != reference.value:
            reject('FACT_REFERENCE_MISMATCH')
    # Claims of compromise/exposure require current affirmative facts. A
    # question about a possibility or an explicitly hypothetical explanation
    # must remain distinguishable from an assertion about this citizen.
    asserted = ' '.join(sentence for sentence in re.split(r'(?<=[.!?])\s+',text)
        if not sentence.endswith('?') and not re.search(r'\b(?:if|whether|may|might|possible)\b',sentence,re.I))
    claim_fields = {
        'account_compromised': r'\byour (?:bank )?account\b.{0,30}\b(?:hacked|compromised|taken over)\b',
        'credentials_exposed': r'\byour (?:password|credentials|pin|otp)\b.{0,30}\b(?:exposed|shared|stolen|leaked)\b',
        'remote_access': r'\b(?:they|someone|the caller)\b.{0,20}\b(?:can|still)\b.{0,20}\b(?:access|control)\b.{0,20}\byour (?:device|phone|computer)\b',
    }
    for claim_field, pattern in claim_fields.items():
        if re.search(pattern, asserted, re.I) and facts.get(claim_field) is not True:
            reject('UNSUPPORTED_INCIDENT_CLAIM')
    for pattern, expected in [
        (r'\byou (?:approved|authorized|authorised)\b', 'authorized'),
        (r'\b(?:you (?:did not|didn.t) approve|without your (?:approval|permission|consent))\b', 'unauthorized'),
    ]:
        if re.search(pattern, asserted, re.I) and facts.get('authorization') != expected:
            reject('UNSUPPORTED_AUTHORIZATION_CLAIM')
    for method in ['upi','card','neft','imps','rtgs']:
        if re.search(r'\b(?:you (?:paid|sent|transferred)|payment (?:was|went|made))\b.{0,30}\b'+method+r'\b', asserted,re.I) and facts.get('payment_method')!=method:
            reject('UNSUPPORTED_PAYMENT_METHOD_CLAIM')
    knowledge = {item['id']: item for item in context.get('knowledge', [])}
    for reference in move.knowledge_refs:
        document = knowledge.get(reference.id)
        if document is None or reference.claim != document['text']:
            reject('UNSUPPORTED_KNOWLEDGE_REFERENCE')
    if '1930' in text and (not re.search(r'\b(?:financial|fraud|money)\b',text,re.I)
            or re.search(r'\b(?:every|all|harassment|stalking|emergency|threats|blackmail)\b',text,re.I)):
        reject('UNSUPPORTED_HELPLINE_SCOPE')
    if re.search(r'\b(?:government|official portal|police|legal|fir)\b', text, re.I) and not move.knowledge_refs:
        reject('UNSUPPORTED_EXTERNAL_CLAIM')
    # Retrieved descriptions do not establish external processing, automatic
    # submission or official status. Those capabilities are not implemented.
    if re.search(r'\b(?:portal|police|bank|government|complaint)\b.{0,100}\b(?:automatically|investigat\w*|processes|forwards|submits|sends your|begins|will)\b', text, re.I):
        reject('UNSUPPORTED_EXTERNAL_PROCESS')
    if re.search(r'\b(?:reporting|complaint)\s+(?:deadline|timeframe|time limit)|\b(?:must|only)\b.{0,30}\b(?:within|hours|days)\b', text, re.I):
        reject('UNSUPPORTED_REPORTING_DEADLINE')
    if text.count('?') > 1:
        reject('MULTIPLE_QUESTIONS')
    if re.search(r'\b(?:bank|police|government|complaint|funds)\b.{0,35}\b(?:frozen|accepted|investigating|reviewing|approved|recovered)\b', text, re.I):
        reject('FAKE_EXTERNAL_STATUS')
    action = None
    if move.action_id:
        action = next((item for item in context['approved_actions'] if item['id'] == move.action_id), None)
        if action is None:
            reject('ACTION_NOT_APPLICABLE')
    # An explanation is prose about a reviewed action. Procedures stay in the
    # independently rendered policy card and cannot be expanded in model prose.
    grounded_text(text, context)
    if move.type == 'ANSWER_RELEVANT_QUESTION' and '?' in text:
        if field is None or field not in context['unknown_fields']:
            reject('ANSWER_FOLLOW_UP_MUST_TARGET_UNKNOWN_FACT')
    if move.type in {'ASK_CLARIFICATION', 'VERIFY_INFORMATION', 'RESOLVE_CONFLICT'} or move.type == 'ANSWER_RELEVANT_QUESTION' and '?' in text:
        if move.type in {'ASK_CLARIFICATION','ANSWER_RELEVANT_QUESTION'} and field not in context['unknown_fields']:
            reject('FACT_ESTABLISHED_OR_ANSWERED')
        if move.type == 'VERIFY_INFORMATION' and (field in context['answered_fields'] or not any(
            c['field'] == field and c['status'] == 'needs_review' for c in context['candidates'])):
            reject('NO_UNRESOLVED_CANDIDATE')
        if move.type == 'RESOLVE_CONFLICT' and field not in context['conflicts']:
            reject('NO_CONFLICT')
        if text.count('?') != 1:
            reject('ONE_INVESTIGATIVE_QUESTION_REQUIRED')
        question_text = re.split(r'(?<=[.!])\s+', text)[-1]
        if not re.search(INQUIRY_TOPIC.get(field, r'(?!)'), question_text, re.I):
            reject('QUESTION_FIELD_MISMATCH')
        if field == 'remote_access' and re.search(r'\b(?:software|app|application|installed|installation)\b', question_text, re.I):
            reject('SOFTWARE_PRESENCE_IS_NOT_REMOTE_ACCESS')
        if re.search(r'\b(?:how (?:can|do|could|should|would)|how to|steps to|instructions to)\b', question_text, re.I):
            reject('PROCEDURE_IS_NOT_INVESTIGATION')
        if re.match(r'^(?:can|could|would) you\b', question_text, re.I) and re.search(r'\b(?:' + ACTION_VERB + r')\b', question_text, re.I):
            reject('PROSPECTIVE_INSTRUCTION')
        if field == 'payment_method' and move.type == 'VERIFY_INFORMATION':
            targets = [c for c in context['candidates'] if c['field'] == field and c['status'] == 'needs_review']
            if len(targets) != 1 or not names_payment_verification_target(question_text, targets[0]['value']):
                reject('VERIFICATION_TARGET_MISMATCH')
    elif move.type == 'REQUEST_EVIDENCE':
        if context['evidence'] or facts['evidence_available'] is False:
            reject('EVIDENCE_PRESENT_OR_UNAVAILABLE')
        if not (facts['money_lost'] or facts['evidence_mentioned'] or facts['identifiers'] or set(facts['signals']) & {'threats','harassment','impersonation'}):
            reject('EVIDENCE_NOT_RELEVANT')
        if not context.get('capabilities', {}).get('ai_evidence_extraction') and re.search(r'\b(?:extract|ocr|analyse|analyze|identify)\b', text, re.I):
            reject('UNAVAILABLE_EVIDENCE_CAPABILITY')
    elif move.type in {'ACKNOWLEDGE_AND_WAIT', 'EXPLAIN_APPROVED_ACTION'} and '?' in text:
        reject('WAITING_MOVE_CANNOT_ASK')
    for known, pattern in KNOWN_QUESTION_TERMS.items():
        established = facts.get(known) not in (None, 'unknown', []) or known in context['answered_fields']
        if known == 'occurred_at' and facts['time_window']:
            established = True
        question_text = re.split(r'(?<=[.!])\s+', text)[-1]
        if '?' in question_text and established and re.search(pattern, question_text, re.I) and not (known == field and move.type == 'RESOLVE_CONFLICT'):
            reject('REPEATED_ESTABLISHED_FACT')
    confirmation = field == 'payment_method' and move.type == 'VERIFY_INFORMATION'
    for reply in move.quick_replies:
        if valid_reply(reply, field) or reply.casefold().strip() in {'skip', 'skip for now', 'not sure', 'yes', 'no'}:
            continue
        # A citizen may choose an already approved phone handoff. This does not
        # authorize model-created instructions or an unapproved destination.
        handoff = re.fullmatch(r'(?:call|report to)\s+(\d{3,6})', reply.strip(), re.I)
        if handoff and any(item.get('phone') == handoff.group(1) for item in context['approved_actions']):
            continue
        # Options propose citizen answers, not authoritative instructions or facts.
        # Validate safety and unsupported identifiers/numbers instead of a wording allowlist.
        grounded_text(reply, context)
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
