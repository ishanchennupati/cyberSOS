"""Consolidate the existing evidence contract, preserving incident/evidence rows.

Revision ID: 20260930_evidence_contract
Revises: 20260824_urgency_metadata
"""
import hashlib
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260930_evidence_contract"
down_revision = "20260824_urgency_metadata"
branch_labels = None
depends_on = None


def enum_type(bind, name, values):
    value = sa.Enum(*values, name=name)
    value.create(bind, checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False) if bind.dialect.name == "postgresql" else value


def upgrade():
    bind = op.get_bind()
    for name, length in (("bank", 128), ("wallet", 128), ("merchant", 255), ("description", 4000)):
        op.add_column("incidents", sa.Column(name, sa.String(length)))

    evidence_type = enum_type(bind, "evidence_type_enum", (
        "bank_statement", "transaction_receipt", "payment_screenshot", "sms_message",
        "email", "chat_conversation", "website_url", "suspect_information", "photo_video", "other_document"))
    extraction = enum_type(bind, "extraction_status_enum", ("pending", "processing", "completed", "failed"))
    verification = enum_type(bind, "verification_status_enum", ("unverified", "verified", "needs_review"))
    suspect_type = enum_type(bind, "suspect_identifier_type_enum", (
        "phone", "email", "upi_id", "bank_account", "website", "social_media", "other"))

    with op.batch_alter_table("evidence") as batch:
        batch.alter_column("original_filename", type_=sa.String(512), existing_type=sa.String(255), existing_nullable=False)
        batch.alter_column("stored_filename", new_column_name="storage_path", type_=sa.String(1024), existing_type=sa.String(255), existing_nullable=False)
        batch.alter_column("content_type", new_column_name="mime_type", existing_type=sa.String(128), existing_nullable=True)
        batch.alter_column("size_bytes", new_column_name="file_size", type_=sa.BigInteger(), existing_type=sa.Integer(), existing_nullable=False)
        batch.add_column(sa.Column("sha256_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("evidence_type", evidence_type, nullable=False, server_default="other_document"))
        batch.add_column(sa.Column("description", sa.String(2000)))
        batch.add_column(sa.Column("extraction_status", extraction, nullable=False, server_default="pending"))
        batch.add_column(sa.Column("extracted_data", sa.JSON().with_variant(postgresql.JSONB(), "postgresql")))
        batch.add_column(sa.Column("verification_status", verification, nullable=False, server_default="unverified"))
        batch.add_column(sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE evidence SET uploaded_at = created_at, updated_at = created_at")

    # Only local original bytes can establish a legacy hash. Never invent it.
    # Resolve paths within the explicitly configured previous evidence directory.
    from app.core.config import get_settings
    settings = get_settings()
    root = Path(settings.LOCAL_STORAGE_ROOT or settings.EVIDENCE_STORAGE_DIR).resolve()
    rows = bind.execute(sa.text("SELECT id, storage_path FROM evidence")).all()
    for ident, storage_path in rows:
        path = (root / storage_path).resolve()
        if root not in path.parents or not path.is_file():
            continue
        try:
            digest = hashlib.sha256()
            with path.open("rb") as original:
                for chunk in iter(lambda: original.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError:
            continue
        bind.execute(sa.text("UPDATE evidence SET sha256_hash=:hash WHERE id=:id"), {"hash": digest.hexdigest(), "id": ident})

    with op.batch_alter_table("evidence") as batch:
        batch.alter_column("uploaded_at", existing_type=sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        batch.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    op.create_index("ix_evidence_sha256_hash", "evidence", ["sha256_hash"])

    op.create_table(
        "suspect_identifiers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incident_id", sa.Uuid(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", suspect_type, nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.Column("source_evidence_id", sa.Uuid(), sa.ForeignKey("evidence.id", ondelete="SET NULL")),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_suspect_identifiers_incident_id", "suspect_identifiers", ["incident_id"])
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incident_id", sa.Uuid(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("source_evidence_id", sa.Uuid(), sa.ForeignKey("evidence.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_timeline_events_incident_id", "timeline_events", ["incident_id"])


def downgrade():
    # Rich verification/extraction metadata cannot be represented by the old
    # contract. Do not silently discard it on an accidental downgrade.
    raise RuntimeError("Evidence consolidation is forward-only; restore a database backup to roll back.")
