import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ConversationState(Base):
    __tablename__ = 'conversation_states'
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('incidents.id', ondelete='CASCADE'), primary_key=True)
    revision: Mapped[int] = mapped_column(default=0)
    version: Mapped[str] = mapped_column(String(16), default='1.0')
    answered: Mapped[list] = mapped_column(JSON, default=list)
    pending_question: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ConversationTurn(Base):
    __tablename__ = 'conversation_turns'
    __table_args__ = (UniqueConstraint('incident_id', 'revision', name='uq_conversation_revision'),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('incidents.id', ondelete='CASCADE'), index=True)
    role: Mapped[str] = mapped_column(String(16), default='user')
    type: Mapped[str] = mapped_column(String(16))
    text: Mapped[str] = mapped_column(String(256))
    structured_reply: Mapped[dict] = mapped_column(JSON)
    fact_changes: Mapped[dict] = mapped_column(JSON)
    pending_question: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    revision: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
