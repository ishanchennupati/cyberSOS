"""Deny expired/deleting cases before retryable physical cleanup."""
from datetime import timedelta
import asyncio
import json
import os
import uuid
from pathlib import Path
from sqlalchemy import delete, select
from app.core.config import get_settings
from app.models.incident import Incident
from app.models.evidence import Evidence
from app.models.return_access import DeletionJob, CaseRecovery, CaseOwner, Account, AccountSession, EmailChallenge, AuthThrottle, FileCleanup
from app.services.return_access import now, utc


def available(incident):
    return bool(incident and not incident.deleting_at and incident.retention_expires_at and utc(incident.retention_expires_at) > now()
        and str(incident.id) not in deleted_ids())


def deleted_ids():
    """Independent revocation journal survives database restore; no content/secrets."""
    path = Path(get_settings().CASE_DELETION_JOURNAL)
    try:
        if not path.exists():
            return set()
        return {str(uuid.UUID(json.loads(line)['case_id'])) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()}
    except (OSError, ValueError, KeyError):
        from fastapi import HTTPException
        raise HTTPException(503, 'Private case availability could not be checked. Please try later.') from None


def journal_deletion(case_id):
    if str(case_id) in deleted_ids():
        return
    path = Path(get_settings().CASE_DELETION_JOURNAL)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, (json.dumps({'case_id':str(case_id)})+'\n').encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def touch(incident):
    incident.retention_expires_at = now()+timedelta(days=get_settings().CASE_RETENTION_DAYS)


def lock_active(db, case_id):
    from fastapi import HTTPException
    incident = db.scalar(select(Incident).where(Incident.id == case_id).with_for_update().execution_options(populate_existing=True))
    if not available(incident):
        raise HTTPException(404, 'Private resource not available')
    return incident


def request_deletion(db, incident):
    # Persist revocation and the file manifest BEFORE attempting storage removal.
    incident = db.scalar(select(Incident).where(Incident.id == incident.id).with_for_update().execution_options(populate_existing=True))
    if incident is None:
        return True
    job = db.get(DeletionJob, incident.id)
    if not job:
        job = DeletionJob(incident_id=incident.id, requested_at=now(), paths=list(db.scalars(
            select(Evidence.storage_path).where(Evidence.incident_id == incident.id))))
        db.add(job)
    incident.deleting_at = now()
    incident.case_secret_hash = None
    incident.case_secret_expires_at = None
    db.execute(delete(CaseRecovery).where(CaseRecovery.incident_id == incident.id))
    db.commit()
    return finish_deletion(db, job)


def finish_deletion(db, job):
    from app.services.storage_service import get_storage_backend
    try:
        journal_deletion(job.incident_id)
        backend = get_storage_backend()
        for path in job.paths:
            backend.delete(path)
    except Exception:
        # Manifest is private DB state, not a diagnostic containing filenames.
        db.rollback()
        return False
    # Cascades remove transcript, plans, completions, candidates, evidence, packet,
    # identifiers and timeline. No persistent private retrieval indexes exist.
    owner = db.get(CaseOwner, job.incident_id)
    owner_id = owner.account_id if owner else None
    db.execute(delete(Incident).where(Incident.id == job.incident_id))
    db.delete(job)
    db.commit()
    # Remove identities with no remaining owned cases and their credentials.
    empty = list(db.scalars(select(Account).where(Account.id == owner_id, ~select(CaseOwner.incident_id).where(
        CaseOwner.account_id == Account.id).exists(), ~select(AccountSession.secret_hash).where(
        AccountSession.account_id == Account.id, AccountSession.expires_at > now()).exists()))) if owner_id else []
    for account in empty:
        db.execute(delete(EmailChallenge).where(EmailChallenge.email == account.email))
        db.delete(account)
    db.commit()
    return True


def cleanup(db):
    reconcile_deletions(db)
    expired = list(db.scalars(select(Incident).where(Incident.retention_expires_at <= now(), Incident.deleting_at.is_(None))))
    for incident in expired:
        request_deletion(db, incident)
    pending = list(db.scalars(select(DeletionJob)))
    for job in pending:
        finish_deletion(db, job)
    from app.services.storage_service import get_storage_backend
    for job in list(db.scalars(select(FileCleanup))):
        try:
            get_storage_backend().delete(job.path)
        except Exception:
            continue
        db.delete(job)
    for model in (EmailChallenge, AccountSession, AuthThrottle):
        db.execute(delete(model).where(model.expires_at <= now()))
    # An active account is independent of any one case. Once its last session
    # expires, remove the identity if it has no owned cases left.
    db.execute(delete(Account).where(~select(CaseOwner.incident_id).where(
        CaseOwner.account_id == Account.id).exists(), ~select(AccountSession.secret_hash).where(
        AccountSession.account_id == Account.id).exists()))
    db.commit()
    return {'pending_deletions': len(list(db.scalars(select(DeletionJob.incident_id)))),
        'pending_files': len(list(db.scalars(select(FileCleanup.path))))}


def remove_uncommitted_file(db, backend, path):
    """Retain failed original cleanup independently of case/metadata rollback."""
    db.rollback()
    try:
        backend.delete(path)
    except Exception:
        if not db.get(FileCleanup, path):
            db.add(FileCleanup(path=path, requested_at=now()))
            db.commit()


def reconcile_deletions(db):
    count = 0
    for case_id in deleted_ids():
        incident = db.get(Incident, uuid.UUID(case_id))
        if incident:
            request_deletion(db, incident)
            count += 1
    return count


async def periodic_cleanup():
    from app.db.session import SessionLocal
    from app.core.diagnostics import log_event
    def run():
        with SessionLocal() as db:
            return cleanup(db)
    while True:
        await asyncio.sleep(get_settings().CASE_CLEANUP_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(run)
        except Exception:
            # No private paths, filenames, case ids or raw storage/DB errors.
            log_event('case_cleanup_unavailable', category='APPLICATION_ERROR')


if __name__ == '__main__':
    from app.db.session import SessionLocal
    with SessionLocal() as db:
        print(cleanup(db))
