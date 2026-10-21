from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import get_settings
from app.models.incident import Incident
from app.models.return_access import Account, AccountSession, CaseOwner
from app.schemas.return_access import EmailRequest, ConfirmRequest, RecoverRequest
from app.services import return_access as access
from app.services.lifecycle import available

router = APIRouter(prefix='/auth', tags=['secure return'])


def boundary(request: Request, response: Response):
    access.origin_check(request, response)


router.dependencies.append(Depends(boundary))


@router.post('/email', status_code=202)
def email(payload: EmailRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    return access.request_email(db, request, response, payload.email)


@router.post('/confirm')
def confirm(payload: ConfirmRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    return access.confirm_email(db, request, response, payload.token)


@router.get('/session')
def status(request: Request, db: Session = Depends(get_db)):
    current = access.session(db, request)
    account = db.get(Account, current.account_id) if current else None
    settings = get_settings()
    return {'signed_in': bool(current), 'email': account.email if account else None,
        'recently_verified': bool(current and access.utc(current.verified_at) > access.now()-timedelta(minutes=15)),
        'email_available': settings.EMAIL_PROVIDER == 'resend' and bool(settings.RESEND_API_KEY),
        'test_delivery_only': not settings.RESEND_VERIFIED_DOMAIN}


@router.get('/cases')
def cases(request: Request, db: Session = Depends(get_db)):
    current = access.session(db, request, required=True)
    rows = db.scalars(select(Incident).join(CaseOwner, CaseOwner.incident_id == Incident.id).where(
        CaseOwner.account_id == current.account_id).order_by(Incident.updated_at.desc()))
    return {'cases': [{'id': str(row.id), 'signals': (row.facts or {}).get('signals', []),
        'updated_at': row.updated_at, 'expires_at': row.retention_expires_at} for row in rows if available(row)]}


@router.post('/logout')
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    db.execute(delete(AccountSession).where(AccountSession.secret_hash == access.digest(request.cookies.get('cybersos_account', ''))))
    db.commit()
    # Guest cookies in this browser must not silently preserve access after logout.
    for name in request.cookies:
        if name.startswith('cybersos_case_') or name in {'cybersos_account', 'cybersos_login_nonce'}:
            access.cookie(response, name, '', 0)
    return {'signed_in': False}


@router.post('/revoke-sessions')
def revoke(request: Request, response: Response, db: Session = Depends(get_db)):
    current = access.session(db, request, required=True, fresh=True)
    db.execute(delete(AccountSession).where(AccountSession.account_id == current.account_id))
    # Also revoke legacy guest secrets for the account's cases.
    for row in db.scalars(select(Incident).join(CaseOwner).where(CaseOwner.account_id == current.account_id)):
        row.case_secret_hash = None
    db.commit()
    access.cookie(response, 'cybersos_account', '', 0)
    return {'signed_in': False}


@router.post('/recover')
def recover(payload: RecoverRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    return access.recover(db, request, response, payload.case_id, payload.code)
