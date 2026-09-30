"""Private case capability checks. Secrets are never stored or logged in plaintext."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import uuid

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.models.incident import Incident
from app.models.evidence import Evidence, SuspectIdentifier, TimelineEvent


def issue(incident: Incident) -> str:
    token = secrets.token_urlsafe(32)
    incident.case_secret_hash = hashlib.sha256(token.encode()).hexdigest()
    incident.case_secret_expires_at = datetime.now(timezone.utc) + timedelta(seconds=get_settings().CASE_ACCESS_TTL_SECONDS)
    return token


def set_cookie(response: Response, incident: Incident, token: str) -> None:
    response.set_cookie("cybersos_case_" + str(incident.id), token, httponly=True,
        secure=get_settings().CASE_COOKIE_SECURE, samesite="strict",
        path=get_settings().API_V1_PREFIX, max_age=get_settings().CASE_ACCESS_TTL_SECONDS)
    response.headers["Cache-Control"] = "no-store"


def authorize_case_resource(request: Request, response: Response, db: Session = Depends(get_db)) -> Incident | None:
    # The anonymous create route has no existing private resource.
    ident = request.path_params.get("incident_id")
    try:
        if ident is None:
            for key, model in (("evidence_id", Evidence), ("suspect_id", SuspectIdentifier), ("event_id", TimelineEvent)):
                if key in request.path_params:
                    resource = db.get(model, uuid.UUID(str(request.path_params[key])))
                    ident = resource.incident_id if resource else None
                    break
        if ident is None:
            if request.method == "POST" and request.url.path.rstrip("/") == get_settings().API_V1_PREFIX + "/incidents":
                return None
            raise ValueError()
        incident = db.get(Incident, uuid.UUID(str(ident)))
    except (ValueError, TypeError):
        incident = None
    token = request.headers.get("X-Case-Secret") or (request.cookies.get("cybersos_case_" + str(incident.id)) if incident else None)
    expected = incident.case_secret_hash if incident else None
    expires = incident.case_secret_expires_at if incident else None
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    valid = bool(token and len(token) <= 256 and expected and expires and expires > datetime.now(timezone.utc))
    if valid:
        valid = hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), expected)
    if not valid:
        raise HTTPException(status_code=404, detail="Private resource not available")
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin not in get_settings().cors_origins_list:
        raise HTTPException(status_code=404, detail="Private resource not available")
    response.headers["Cache-Control"] = "no-store"
    return incident
