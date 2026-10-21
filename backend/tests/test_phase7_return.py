"""Owned secure-return flows; no real emails or citizen data."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.models.incident import Incident


def create(client):
    return client.post('/api/v1/incidents', json={'conversation_first': True}).json()['id']


def test_email_link_requires_guest_authority_and_verification(client, monkeypatch):
    from app.services import return_access
    mail = []
    monkeypatch.setattr(return_access, 'send_sign_in', lambda email, token: mail.append((email, token)))
    case_id = create(client)
    result = client.post('/api/v1/auth/email', json={'email': 'synthetic@example.test'})
    assert result.status_code == 202
    assert 'token' not in result.json()
    token = mail[0][1]
    verified = client.post('/api/v1/auth/confirm', json={'token': token})
    assert verified.status_code == 200
    assert client.get('/api/v1/auth/cases').json()['cases'] == []
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code == 200
    assert client.get('/api/v1/auth/cases').json()['cases'][0]['id'] == case_id
    assert client.post('/api/v1/auth/confirm', json={'token': token}).status_code == 404
    with TestClient(app, base_url='https://testserver') as stranger:
        assert stranger.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404
        assert stranger.post(f'/api/v1/incidents/{case_id}/save').status_code == 404


def test_recovery_after_expiry_rotates_code_and_case_secret(client, db):
    case_id = create(client)
    result = client.post(f'/api/v1/incidents/{case_id}/recovery-code')
    assert result.status_code == 200
    code = result.json()['code']
    incident = db.get(Incident, uuid.UUID(case_id))
    incident.case_secret_expires_at = datetime.now(timezone.utc)-timedelta(seconds=1)
    db.commit()
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404
    recovered = client.post('/api/v1/auth/recover', json={'case_id': case_id, 'code': code})
    assert recovered.status_code == 200
    assert recovered.json()['code'] != code
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 200
    assert client.post('/api/v1/auth/recover', json={'case_id': case_id, 'code': code}).status_code == 404


def test_deleted_case_denies_every_old_credential(client, db):
    case_id = create(client)
    code = client.post(f'/api/v1/incidents/{case_id}/recovery-code').json()['code']
    removed = client.request('DELETE', f'/api/v1/incidents/{case_id}', json={'confirmation': 'DELETE'})
    assert removed.status_code == 200
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404
    assert client.post('/api/v1/auth/recover', json={'case_id': case_id, 'code': code}).status_code == 404
    db.expire_all()
    assert db.get(Incident, uuid.UUID(case_id)) is None


def test_inactive_case_expiry_is_not_recoverable(client, db):
    case_id = create(client)
    incident = db.get(Incident, uuid.UUID(case_id))
    incident.retention_expires_at = datetime.now(timezone.utc)-timedelta(seconds=1)
    db.commit()
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404


def login(client, monkeypatch, email='synthetic@example.test'):
    from app.services import return_access
    delivered = []
    monkeypatch.setattr(return_access, 'send_sign_in', lambda email, token: delivered.append(token))
    assert client.post('/api/v1/auth/email', json={'email': email}).status_code == 202
    assert client.post('/api/v1/auth/confirm', json={'token': delivered[-1]}).status_code == 200


def test_expired_guest_resumes_through_owned_email_session(client, monkeypatch, db):
    case_id = create(client)
    login(client, monkeypatch)
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code == 200
    incident = db.get(Incident, uuid.UUID(case_id))
    incident.case_secret_expires_at = datetime.now(timezone.utc)-timedelta(seconds=1)
    db.commit()
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 200
    assert client.post('/api/v1/auth/logout').status_code == 200
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404


def test_email_link_cannot_sign_in_another_browser(client, monkeypatch):
    from app.services import return_access
    delivered = []
    monkeypatch.setattr(return_access, 'send_sign_in', lambda email, token: delivered.append(token))
    assert client.post('/api/v1/auth/email', json={'email': 'synthetic@example.test'}).status_code == 202
    with TestClient(app, base_url='https://testserver') as other:
        assert other.post('/api/v1/auth/confirm', json={'token':delivered[0]}).status_code == 404
    assert client.post('/api/v1/auth/confirm', json={'token':delivered[0]}).status_code == 200


def test_email_request_is_rate_limited_without_exposing_token(client, monkeypatch):
    from app.services import return_access
    monkeypatch.setattr(return_access, 'send_sign_in', lambda email, token: None)
    body = {'email': 'synthetic@example.test'}
    assert client.post('/api/v1/auth/email', json=body).status_code == 202
    assert client.post('/api/v1/auth/email', json=body).status_code == 429


def test_cross_origin_auth_and_case_mutation_rejected(client):
    case_id = create(client)
    assert client.post('/api/v1/auth/email', json={'email':'synthetic@example.test'}, headers={'Origin':'https://attacker.test'}).status_code == 404
    assert client.post(f'/api/v1/incidents/{case_id}/recovery-code', headers={'Origin':'https://attacker.test'}).status_code == 404


def test_retention_cleanup_removes_originals_and_all_case_derivatives(client, db):
    from app.models.return_access import DeletionJob
    from app.services.lifecycle import cleanup
    from app.models.evidence import Evidence
    from app.services.storage_service import get_storage_backend
    from sqlalchemy import select
    case_id = create(client)
    evidence = client.post(f'/api/v1/incidents/{case_id}/evidence',files={'file':('synthetic.txt',b'Synthetic record','text/plain')}).json()
    stored = db.get(Evidence, uuid.UUID(evidence['id']))
    path = stored.storage_path
    incident = db.get(Incident, uuid.UUID(case_id))
    incident.retention_expires_at = datetime.now(timezone.utc)-timedelta(seconds=1)
    db.commit()
    assert cleanup(db)['pending_deletions'] == 0
    assert not list(db.scalars(select(DeletionJob)))
    assert client.get(f"/api/v1/evidence/{evidence['id']}/file").status_code == 404
    import pytest
    from app.services.storage_service import StorageError
    with pytest.raises(StorageError):
        get_storage_backend().download(path)


def test_storage_failure_revokes_access_and_keeps_retry_manifest(client, monkeypatch, db):
    from app.services import storage_service
    from app.services.lifecycle import cleanup
    from app.models.return_access import DeletionJob
    case_id = create(client)
    client.post(f'/api/v1/incidents/{case_id}/evidence',files={'file':('synthetic.txt',b'Synthetic','text/plain')})
    original = storage_service.LocalDiskStorageBackend.delete
    def fail(self, path):
        raise storage_service.StorageError('Synthetic storage outage')
    monkeypatch.setattr(storage_service.LocalDiskStorageBackend, 'delete', fail)
    result = client.request('DELETE',f'/api/v1/incidents/{case_id}',json={'confirmation':'DELETE'})
    assert result.status_code == 202 and result.json()['access_revoked'] is True
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404
    assert db.get(DeletionJob,uuid.UUID(case_id)).paths
    monkeypatch.setattr(storage_service.LocalDiskStorageBackend, 'delete', original)
    assert cleanup(db)['pending_deletions'] == 0


def test_restore_epoch_denies_old_guest_and_recovery_credentials(client, db, monkeypatch):
    from app.core.config import get_settings
    case_id = create(client)
    code = client.post(f'/api/v1/incidents/{case_id}/recovery-code').json()['code']
    monkeypatch.setenv('AUTH_EPOCH', 'post-restore-synthetic-2')
    get_settings.cache_clear()
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404
    assert client.post('/api/v1/auth/recover',json={'case_id':case_id,'code':code}).status_code == 404


def test_owner_case_cannot_be_claimed_by_another_account(client, monkeypatch):
    case_id = create(client)
    login(client, monkeypatch)
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code == 200
    login(client, monkeypatch, 'second@example.test')
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code == 409
    assert client.get('/api/v1/auth/cases').json()['cases'] == []


def test_deletion_journal_blocks_a_restored_case_before_cleanup(client, db, monkeypatch, tmp_path):
    from app.core.config import get_settings
    from app.services.lifecycle import reconcile_deletions
    journal = tmp_path/'private-deletions.jsonl'
    monkeypatch.setenv('CASE_DELETION_JOURNAL', str(journal))
    get_settings.cache_clear()
    case_id=create(client)
    # A deletion recorded outside the database must deny a restored DB row,
    # including for newly authenticated owners, before physical cleanup runs.
    journal.write_text('{"case_id":"'+case_id+'"}\n',encoding='utf-8')
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code == 404
    assert reconcile_deletions(db) == 1
    db.expire_all()
    assert db.get(Incident,uuid.UUID(case_id)) is None


def test_expired_email_challenge_cannot_create_session(client, monkeypatch, db):
    from app.services import return_access
    from app.models.return_access import EmailChallenge
    delivered=[]
    monkeypatch.setattr(return_access,'send_sign_in',lambda email,token:delivered.append(token))
    assert client.post('/api/v1/auth/email',json={'email':'synthetic@example.test'}).status_code==202
    row=db.get(EmailChallenge,return_access.digest(delivered[0]));row.expires_at=return_access.now()-timedelta(seconds=1);db.commit()
    assert client.post('/api/v1/auth/confirm',json={'token':delivered[0]}).status_code==404
    assert client.get('/api/v1/auth/session').json()['signed_in'] is False


def test_revoked_account_session_and_guest_secret_cannot_resume(client, monkeypatch):
    case_id=create(client)
    login(client,monkeypatch)
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code==200
    assert client.post('/api/v1/auth/revoke-sessions').status_code==200
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code==404
    assert client.get('/api/v1/auth/cases').status_code==401


def test_recovery_code_concurrent_redemption_has_one_winner(client):
    from concurrent.futures import ThreadPoolExecutor
    case_id=create(client)
    code=client.post(f'/api/v1/incidents/{case_id}/recovery-code').json()['code']
    def redeem(_):
        with TestClient(app,base_url='https://testserver') as browser:
            return browser.post('/api/v1/auth/recover',json={'case_id':case_id,'code':code}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(redeem,range(2)))==[200,404]


def test_deletion_during_provider_turn_does_not_resurrect_case(client, monkeypatch, db):
    from app.services import case_agent
    from tests.test_phase3r_case_agent import install, move, send
    from tests.test_phase3_understanding import candidate
    from app.services.lifecycle import request_deletion
    install(monkeypatch,[candidate('signals',['harassment'],'harassed')],move())
    case_id=create(client)
    state=client.get(f'/api/v1/incidents/{case_id}/conversation').json()
    original=case_agent.decide
    def delete_then_reply(context):
        from app.db.session import SessionLocal
        with SessionLocal() as other:
            request_deletion(other,other.get(Incident,uuid.UUID(case_id)))
        return original(context)
    monkeypatch.setattr(case_agent,'decide',delete_then_reply)
    result=client.post(f'/api/v1/incidents/{case_id}/conversation/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'message','text':'I was harassed.'})
    assert result.status_code==404
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code==404


def test_fresh_verification_can_save_guest_without_logout_or_lost_authority(client, monkeypatch):
    from app.services import return_access
    case_id=create(client)
    login(client,monkeypatch)
    future=return_access.now()+timedelta(minutes=16)
    monkeypatch.setattr(return_access,'now',lambda:future)
    assert client.get('/api/v1/auth/session').json()['recently_verified'] is False
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code==401
    # Requesting/confirming another email link must retain guest case access.
    login(client,monkeypatch)
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code==200
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code==200


def test_failed_upload_cleanup_is_durable_without_deleting_active_case(client, monkeypatch, db):
    from app.services import storage_service
    from app.services.lifecycle import cleanup
    from app.models.return_access import FileCleanup
    from sqlalchemy import select
    case_id=create(client)
    original_upload=storage_service.LocalDiskStorageBackend.upload
    original_delete=storage_service.LocalDiskStorageBackend.delete
    def failed_upload(self,path,data,content_type):
        original_upload(self,path,data,content_type)
        raise storage_service.StorageError('Synthetic storage response lost after upload')
    def failed_delete(self,path):
        raise storage_service.StorageError('Synthetic cleanup outage')
    monkeypatch.setattr(storage_service.LocalDiskStorageBackend,'upload',failed_upload)
    monkeypatch.setattr(storage_service.LocalDiskStorageBackend,'delete',failed_delete)
    result=client.post(f'/api/v1/incidents/{case_id}/evidence',files={'file':('synthetic.txt',b'Synthetic record','text/plain')})
    assert result.status_code in {500,503}
    db.expire_all()
    queued=list(db.scalars(select(FileCleanup)))
    assert len(queued)==1
    path=queued[0].path
    assert storage_service.LocalDiskStorageBackend().download(path)==b'Synthetic record'
    monkeypatch.setattr(storage_service.LocalDiskStorageBackend,'delete',original_delete)
    cleanup(db)
    assert not list(db.scalars(select(FileCleanup)))
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code==200
    import pytest
    with pytest.raises(storage_service.StorageError):
        storage_service.LocalDiskStorageBackend().download(path)


def test_periodic_cleanup_retires_an_expired_case(client, monkeypatch, db):
    import asyncio
    from app.services import lifecycle
    case_id=create(client)
    row=db.get(Incident,uuid.UUID(case_id));row.retention_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db.commit()
    sleeps=0
    async def advance(_):
        nonlocal sleeps
        sleeps+=1
        if sleeps>1:raise asyncio.CancelledError
    monkeypatch.setattr(lifecycle.asyncio,'sleep',advance)
    import pytest
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(lifecycle.periodic_cleanup())
    db.expire_all()
    assert db.get(Incident,uuid.UUID(case_id)) is None


def test_deleting_last_case_keeps_current_account_usable_for_another_case(client, monkeypatch):
    case_id=create(client)
    login(client,monkeypatch)
    assert client.post(f'/api/v1/incidents/{case_id}/save').status_code==200
    assert client.request('DELETE',f'/api/v1/incidents/{case_id}',json={'confirmation':'DELETE'}).status_code==200
    assert client.get('/api/v1/auth/session').json()['signed_in'] is True
    assert client.get('/api/v1/auth/cases').json()['cases']==[]
    another=create(client)
    assert client.post(f'/api/v1/incidents/{another}/save').status_code==200


def test_relative_deletion_journal_has_stable_backend_root(monkeypatch, tmp_path):
    from app.core.config import get_settings
    from pathlib import Path
    monkeypatch.setenv('CASE_DELETION_JOURNAL','./tmp/private/synthetic-journal.jsonl')
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    actual=Path(get_settings().CASE_DELETION_JOURNAL)
    assert actual.is_absolute()
    assert actual==Path(__file__).resolve().parents[1]/'tmp/private/synthetic-journal.jsonl'


def test_explicit_resume_extends_retention_but_background_read_does_not(client, db):
    from app.services.return_access import utc
    case_id=create(client)
    row=db.get(Incident,uuid.UUID(case_id));old=datetime.now(timezone.utc)+timedelta(days=1);row.retention_expires_at=old;db.commit()
    assert client.get(f'/api/v1/incidents/{case_id}/conversation').status_code==200
    db.refresh(row);assert utc(row.retention_expires_at)==old
    assert client.post(f'/api/v1/incidents/{case_id}/resume').status_code==200
    db.refresh(row);assert utc(row.retention_expires_at)>old+timedelta(days=80)
