import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ResponsePlanRecord(Base):
    __tablename__ = "response_plans"
    __table_args__ = (UniqueConstraint("incident_id", "revision", name="uq_response_plan_revision"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    revision: Mapped[int] = mapped_column(nullable=False)
    plan: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActionCompletionRecord(Base):
    __tablename__ = "action_completions"
    __table_args__ = (UniqueConstraint("plan_id", "action_id", name="uq_completion_plan_action"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("response_plans.id", ondelete="CASCADE"), nullable=False)
    action_id: Mapped[str] = mapped_column(String(64), nullable=False)
    completed: Mapped[bool] = mapped_column(nullable=False)
    user_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    user_recorded_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
