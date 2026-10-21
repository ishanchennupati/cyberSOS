"""Passwordless access without a gate before urgent help. No model authority."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import uuid
import httpx
from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from app.core.config import get_settings
from app.models.return_access import Account, AccountSession, EmailChallenge, CaseOwner, CaseRecovery, AuthThrottle


def now():
    return datetime.now(timezone.utc)


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def origin_check(request, response):
    response.headers['Cache-Control'] = 'private, no-store'
    origin = request.headers.get('origin')
    if request.method not in {'GET', 'HEAD', 'OPTIONS'} and origin and origin not in get_settings().cors_origins_list:
        raise HTTPException(404, 'Private resource not available')


def cookie(response, name, value, ttl):
    response.set_cookie(name, value, httponly=True, secure=get_settings().CASE_COOKIE_SECURE,
        samesite='strict', path=get_settings().API_V1_PREFIX, max_age=ttl)
    response.headers['Cache-Control'] = 'private, no-store'


def throttle(db, scope, value, limit, seconds):
    """Database-backed fixed-window limits, atomic across API workers."""
    stamp = now()
    key = digest(f'{scope}:{int(stamp.timestamp())//seconds}:{value}')
    changed = db.execute(update(AuthThrottle).where(AuthThrottle.key == key,
        AuthThrottle.count < limit).values(count=AuthThrottle.count+1))
    if changed.rowcount:
        db.commit()
        return
    if db.get(AuthThrottle, key):
        db.rollback()
        raise HTTPException(429, 'Please wait before trying again.')
    db.add(AuthThrottle(key=key, count=1, expires_at=stamp+timedelta(seconds=seconds)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        throttle(db, scope, value, limit, seconds)


def send_sign_in(email, token):
    settings = get_settings()
    if settings.EMAIL_PROVIDER != 'resend' or not settings.RESEND_API_KEY:
        raise HTTPException(503, 'Email sign-in is not configured. You can keep chatting and save a recovery code.')
    if not settings.RESEND_VERIFIED_DOMAIN and email != (settings.RESEND_TEST_RECIPIENT or '').strip().casefold():
        # Same observable result for all recipients in the restricted local mode.
        return
    link = settings.PUBLIC_APP_URL.rstrip('/')+'/return#token='+token
    try:
        result = httpx.post('https://api.resend.com/emails', headers={
            'Authorization': 'Bearer '+settings.RESEND_API_KEY}, json={
            'from': settings.RESEND_FROM_EMAIL, 'to': [email], 'subject': 'Your CyberSOS sign-in link',
            'text': 'You requested a CyberSOS sign-in. Open this link in the browser where you requested it, then confirm. '
                'It expires in 15 minutes and works once. If you did not request it, ignore it.\n\n'+link}, timeout=10)
        if result.status_code >= 400:
            raise HTTPException(503, 'Email delivery is unavailable. Keep chatting or use your recovery code.')
    except httpx.HTTPError:
        raise HTTPException(503, 'Email delivery is unavailable. Keep chatting or use your recovery code.') from None


def request_email(db, request, response, email):
    email = email.strip().casefold()
    throttle(db, 'email-ip', request.client.host if request.client else 'unknown', 10, 900)
    throttle(db, 'email-address', email, 1, 60)
    throttle(db, 'email-global-day', 'all', 90, 86400)
    throttle(db, 'email-global-month', 'all', 2700, 2678400)
    token, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.execute(delete(EmailChallenge).where(EmailChallenge.email == email))
    db.add(EmailChallenge(secret_hash=digest(token), email=email, nonce_hash=digest(nonce),
        expires_at=now()+timedelta(minutes=15), epoch=get_settings().AUTH_EPOCH))
    db.commit()
    try:
        send_sign_in(email, token)
    except Exception:
        db.execute(delete(EmailChallenge).where(EmailChallenge.secret_hash == digest(token)))
        db.commit()
        raise
    cookie(response, 'cybersos_login_nonce', nonce, 900)
    return {'message': 'If delivery is available, a sign-in link will arrive. Check your safe inbox; you can keep chatting.'}


def confirm_email(db, request, response, token):
    throttle(db, 'confirm-ip', request.client.host if request.client else 'unknown', 30, 900)
    challenge = db.get(EmailChallenge, digest(token))
    nonce = request.cookies.get('cybersos_login_nonce', '')
    if not challenge or utc(challenge.expires_at) <= now() or challenge.epoch != get_settings().AUTH_EPOCH or not hmac.compare_digest(challenge.nonce_hash, digest(nonce)):
        raise HTTPException(404, 'Sign-in link is unavailable. Request another link in this browser.')
    consumed = db.execute(delete(EmailChallenge).where(EmailChallenge.secret_hash == digest(token)))
    if consumed.rowcount != 1:
        db.rollback()
        raise HTTPException(404, 'Sign-in link is unavailable. Request another link.')
    account = db.scalar(select(Account).where(Account.email == challenge.email))
    if not account:
        account = Account(email=challenge.email)
        db.add(account)
        db.flush()
    secret = secrets.token_urlsafe(32)
    ttl = get_settings().CASE_ACCESS_TTL_SECONDS
    db.add(AccountSession(secret_hash=digest(secret), account_id=account.id,
        expires_at=now()+timedelta(seconds=ttl), verified_at=now(), epoch=get_settings().AUTH_EPOCH))
    db.execute(delete(AccountSession).where(AccountSession.secret_hash == digest(request.cookies.get('cybersos_account', ''))))
    db.commit()
    cookie(response, 'cybersos_account', secret, ttl)
    cookie(response, 'cybersos_login_nonce', '', 0)
    return {'signed_in': True}


def session(db, request, required=False, fresh=False):
    secret = request.cookies.get('cybersos_account', '')
    row = db.get(AccountSession, digest(secret)) if 0 < len(secret) <= 256 else None
    valid = row and utc(row.expires_at) > now() and row.epoch == get_settings().AUTH_EPOCH
    if valid and fresh:
        valid = utc(row.verified_at) > now()-timedelta(minutes=15)
    if valid:
        return row
    if required:
        raise HTTPException(401, 'Verify your safe email again to continue.')
    return None


def account_owns(db, request, incident_id):
    current = session(db, request)
    owner = db.get(CaseOwner, incident_id) if current else None
    return bool(owner and owner.account_id == current.account_id)


def set_recovery(db, incident):
    from app.services.lifecycle import lock_active
    incident = lock_active(db, incident.id)
    code = secrets.token_urlsafe(32)
    row = db.get(CaseRecovery, incident.id)
    if not row:
        row = CaseRecovery(incident_id=incident.id)
        db.add(row)
    row.secret_hash, row.epoch = digest(code), get_settings().AUTH_EPOCH
    db.commit()
    return {'case_id': str(incident.id), 'code': code}


def recover(db, request, response, case_id, code):
    from app.models.incident import Incident
    from app.services.case_access import issue, set_cookie
    from app.services.lifecycle import available, lock_active
    throttle(db, 'recovery-ip', request.client.host if request.client else 'unknown', 20, 900)
    row = db.get(CaseRecovery, case_id)
    incident = db.get(Incident, case_id)
    expected = row.secret_hash if row else digest('unavailable')
    valid = hmac.compare_digest(digest(code), expected)
    if not valid or not row or row.epoch != get_settings().AUTH_EPOCH or not available(incident):
        raise HTTPException(404, 'Private resource not available')
    # Match deletion's lock order: case first, recovery credential second.
    # Recheck lifecycle after waiting so expiry/deletion cannot be overwritten.
    incident = lock_active(db, case_id)
    replacement = secrets.token_urlsafe(32)
    changed = db.execute(update(CaseRecovery).where(CaseRecovery.incident_id == case_id,
        CaseRecovery.secret_hash == expected).values(secret_hash=digest(replacement)))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(404, 'Private resource not available')
    secret = issue(incident)
    db.commit()
    set_cookie(response, incident, secret)
    return {'case_id': str(case_id), 'code': replacement}
