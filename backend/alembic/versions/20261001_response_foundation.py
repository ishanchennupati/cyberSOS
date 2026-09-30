"""Add typed response snapshots, versions and hashed private case capabilities."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261001_response_foundation"
down_revision = "20260930_evidence_contract"
branch_labels = None
depends_on = None


def upgrade():
    data = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
    for name, length in (("playbook_id", 64), ("playbook_version", 32), ("fact_schema_version", 32), ("case_secret_hash", 64)):
        op.add_column("incidents", sa.Column(name, sa.String(length), nullable=True))
    op.add_column("incidents", sa.Column("facts", data, nullable=True))
    op.add_column("incidents", sa.Column("plan_revision", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("incidents", sa.Column("case_secret_expires_at", sa.DateTime(timezone=True), nullable=True))
    # Historical unversioned rules cannot honestly be assigned a invented version.
    # Preserve all prior fields and keep cases locked until an offline owner process exists.
    op.execute("UPDATE incidents SET playbook_id='legacy_unversioned'")
    op.create_table("response_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incident_id", sa.Uuid(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("plan", data, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("incident_id", "revision", name="uq_response_plan_revision"))
    op.create_index("ix_response_plans_incident_id", "response_plans", ["incident_id"])
    op.create_table("action_completions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incident_id", sa.Uuid(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Uuid(), sa.ForeignKey("response_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_id", sa.String(64), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("user_note", sa.String(512), nullable=True),
        sa.Column("user_recorded_reference", sa.String(128), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plan_id", "action_id", name="uq_completion_plan_action"))
    op.create_index("ix_action_completions_incident_id", "action_completions", ["incident_id"])


def downgrade():
    raise RuntimeError("Response/capability history is forward-only; restore a database backup.")
