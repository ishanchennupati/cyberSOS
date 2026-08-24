"""Add Phase 2 cyber crime fields and evidence metadata.

Revision ID: 20260824_phase2
Revises:
"""
from alembic import op
import sqlalchemy as sa

from app.db.base import Base
from app.models import incident  # noqa: F401

revision = "20260824_phase2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "incidents" not in sa.inspect(bind).get_table_names():
        Base.metadata.create_all(bind=bind)
        return
    if bind.dialect.name == "postgresql":
        op.execute("DO $$ BEGIN CREATE TYPE other_crime_sub_category_enum AS ENUM ('online_social_media', 'ransomware', 'hacking', 'cryptocurrency', 'online_trafficking', 'online_gambling', 'any_other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
        for value in ("other_cyber_crime", "women_children"):
            op.execute(f"ALTER TYPE incident_type_enum ADD VALUE IF NOT EXISTS '{value}'")

    inspector = sa.inspect(bind)
    incident_columns = {column["name"] for column in inspector.get_columns("incidents")}
    if "occurred_at" not in incident_columns:
        op.add_column("incidents", sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True))
    if "transaction_id" not in incident_columns:
        op.add_column("incidents", sa.Column("transaction_id", sa.String(length=128), nullable=True))
    if "other_crime_sub_category" not in incident_columns:
        column_type = sa.Enum("online_social_media", "ransomware", "hacking", "cryptocurrency", "online_trafficking", "online_gambling", "any_other", name="other_crime_sub_category_enum") if bind.dialect.name == "postgresql" else sa.String(length=64)
        op.add_column("incidents", sa.Column("other_crime_sub_category", column_type, nullable=True))
    if "details" not in incident_columns:
        op.add_column("incidents", sa.Column("details", sa.JSON(), nullable=True))
    if "urgency_computed_at" not in incident_columns:
        op.add_column("incidents", sa.Column("urgency_computed_at", sa.DateTime(timezone=True), nullable=True))
    for name, column in (
        ("incident_subtype", sa.String(length=128)),
        ("affected_person_type", sa.String(length=64)),
        ("platform", sa.String(length=64)),
        ("account_type", sa.String(length=64)),
        ("immediate_danger", sa.Boolean()),
        ("threat_or_blackmail", sa.Boolean()),
        ("content_still_online", sa.Boolean()),
        ("account_access", sa.String(length=32)),
        ("attacker_active", sa.Boolean()),
        ("sensitive_information_exposed", sa.Boolean()),
        ("evidence_types", sa.JSON()),
        ("urgency_score", sa.Integer()),
    ):
        if name not in incident_columns:
            op.add_column("incidents", sa.Column(name, column, nullable=True))

    if "evidence" not in inspector.get_table_names():
        op.create_table(
            "evidence",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("incident_id", sa.Uuid(), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("stored_filename", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=128), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stored_filename"),
        )
        op.create_index("ix_evidence_incident_id", "evidence", ["incident_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_incident_id", table_name="evidence")
    op.drop_table("evidence")
    for name in ("urgency_score", "evidence_types", "sensitive_information_exposed", "attacker_active", "account_access", "content_still_online", "threat_or_blackmail", "immediate_danger", "account_type", "platform", "affected_person_type", "incident_subtype", "urgency_computed_at", "details", "other_crime_sub_category", "transaction_id", "occurred_at"):
        op.drop_column("incidents", name)
