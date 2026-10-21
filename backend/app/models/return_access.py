"""Optional identity and case-scoped recovery; no conversation data in identity."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Account(Base):
    __tablename__ = 'accounts'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True)


class AccountSession(Base):
    __tablename__ = 'account_sessions'
    secret_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('accounts.id', ondelete='CASCADE'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    epoch: Mapped[str] = mapped_column(String(80))


class EmailChallenge(Base):
    __tablename__ = 'email_challenges'
    secret_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    nonce_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    epoch: Mapped[str] = mapped_column(String(80))


class CaseOwner(Base):
    __tablename__ = 'case_owners'
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('incidents.id', ondelete='CASCADE'), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('accounts.id', ondelete='CASCADE'), index=True)


class CaseRecovery(Base):
    __tablename__ = 'case_recovery'
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('incidents.id', ondelete='CASCADE'), primary_key=True)
    secret_hash: Mapped[str] = mapped_column(String(64))
    epoch: Mapped[str] = mapped_column(String(80))


class AuthThrottle(Base):
    __tablename__ = 'auth_throttles'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(default=1)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DeletionJob(Base):
    __tablename__ = 'case_deletions'
    # Independent of the case cascade, retained until storage removal succeeds.
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    paths: Mapped[list] = mapped_column(JSON, default=list)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FileCleanup(Base):
    __tablename__ = 'file_cleanup_jobs'
    # No case FK: failed/racing uploads may outlive the case's DB row.
    path: Mapped[str] = mapped_column(String(1024), primary_key=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
