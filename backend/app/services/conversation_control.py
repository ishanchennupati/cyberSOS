"""Citizen control and presentation, never extraction or action authorization."""
import re


def explicit_controls(text):
    """Small failure safety net for direct commands; multilingual meaning stays AI-led.

    Quoted examples/questions about commands do not change case control. This
    parser cannot establish facts, confirm evidence, or authorize an action.
    """
    text = re.sub(r'"[^"\n]*"|“[^”\n]*”', '', text).casefold().strip()
    intents = set()
    for sentence in re.split(r'[.!;\n]+', text):
        sentence = re.sub(r'^\s*(?:please\s+)?', '', sentence).strip()
        if re.match(r'^(?:stop|pause)(?:$|\s+(?:asking|questions|questioning|the questions|for now)\b)|^enough questions\b|^no more questions\b', sentence):
            intents.add('pause')
        if re.match(r'^(?:summari[sz]e|conclude|wrap up)\b', sentence):
            intents.add('summary')
            if re.search(r'conclude|wrap up', sentence): intents.add('conclude')
        if re.match(r'^(?:give|show|tell)\s+me\b.*\b(?:plan|steps|what to do)\b|^what (?:should|can) i do\b|^help me\b', sentence):
            intents.add('help')
        if re.fullmatch(r'(?:resume|continue)(?: (?:asking )?questions)?', sentence):
            intents.add('resume')
        if re.match(r'^skip(?:$|\s+(?:this|that|the) question\b)', sentence):
            intents.add('skip')
        if re.match(r'^why (?:are|were) you asking\b', sentence):
            intents.add('question')
    return intents


def control(intents, memory):
    intents = set(intents)
    paused = memory.get('questions_paused', False)
    if 'resume' in intents: paused = False
    if intents & {'pause', 'conclude', 'summary', 'help', 'plan'}: paused = True
    request = next((i for i in ('witness','separate_incident','conclude','summary','plan','help','pause','resume','question','feedback') if i in intents), 'investigate')
    scope_pending = memory.get('incident_scope_pending', False)
    if intents & {'witness','separate_incident'}: scope_pending = True
    elif 'same_incident' in intents: scope_pending = False
    if scope_pending:
        request = 'separate_incident'
        paused = True
    return {'request': request, 'questions_paused': paused, 'incident_scope_pending':scope_pending}


def question_context(facts, field):
    values = facts.model_dump(mode='json')
    related = {
        'story': ['signals','platform','threat_text','money_lost','payment_app','payment_method','authorization'],
        'remote_access': ['remote_access','signals'], 'account_compromised': ['account_compromised','signals','platform'],
        'money_lost': ['money_lost','signals'], 'immediate_danger': ['immediate_danger','signals','threat_text'],
        'evidence_available': ['evidence_available','evidence_mentioned'],
        'identifiers': ['identifiers','platform'],
    }.get(field, [field, 'signals', 'money_lost', 'authorization', 'payment_method'])
    return {key: values.get(key) for key in related}


def dispositions(facts, turns):
    result = {}
    for turn in turns:
        item = turn.fact_changes.get('question_disposition')
        if item:
            for entry in [item, *item.get('also_declined', [])]:
                result[entry['field']] = entry
        for update in turn.fact_changes.get('updates', []):
            if update['field'] in result: result[update['field']] = dict(result[update['field']], status='answered')
    return result


def suppressed_fields(facts, history):
    return {field for field, item in history.items() if item['status'] in {'declined','nonanswer'}
        and item.get('context') == question_context(facts, field)}


def help_view(facts, plan, conflicts):
    from app.services.case_memory import derive_memory
    known = derive_memory(facts, [], conflicts)['facts']
    # Explicit unknowns stay separate from the citizen's account, never defaults.
    unknowns = list(conflicts)
    if 'financial' in facts.signals:
        for field in ['authorization', 'payment_method', 'amount', 'currency', 'time_window']:
            if getattr(facts, field) in (None, 'unknown'): unknowns.append(field)
    if 'threats' in facts.signals and facts.immediate_danger is None: unknowns.append('immediate_danger')
    return {'known_facts': known, 'unknowns': list(dict.fromkeys(unknowns)),
        'action_ids': [a.id for a in plan.actions], 'meaning': 'Current help; facts have not been marked reviewed.'}
