"""Private reporting snapshots; canonical case state remains authoritative."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ReportingSnapshot(Base):
    __tablename__='reporting_snapshots'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True)
    incident_id: Mapped[uuid.UUID]=mapped_column(Uuid,ForeignKey('incidents.id',ondelete='CASCADE'),index=True)
    source_revision: Mapped[int]=mapped_column(nullable=False)
    source_digest: Mapped[str]=mapped_column(String(64),nullable=False)
    packet: Mapped[dict]=mapped_column(JSON,nullable=False)
    narrative: Mapped[dict]=mapped_column(JSON,nullable=False)
    reviewed_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
