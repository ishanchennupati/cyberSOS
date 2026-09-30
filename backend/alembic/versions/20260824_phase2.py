"""Frozen historical incident/legacy-evidence baseline.

Revision ID: 20260824_phase2
Revises:
Existing startup-created schemas are adopted without discarding rows.
This revision deliberately contains no imports of mutable application models.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260824_phase2"
down_revision = None
branch_labels = None
depends_on = None

INCIDENT_TYPES = ("women_children", "financial_fraud", "other_cyber_crime",
                  "phishing", "identity_theft", "social_media", "job_scam", "other")
PAYMENT_METHODS = ("upi", "debit_card", "credit_card", "net_banking", "wallet",
                   "unknown", "bank_transfer", "card")
URGENCIES = ("critical", "high", "medium", "medium_low", "standard", "low")
SUBCATEGORIES = ("online_social_media", "ransomware", "hacking", "cryptocurrency",
                 "online_trafficking", "online_gambling", "any_other")
STATUSES = ("draft", "triage_started", "action_required", "report_prepared", "submitted", "closed")


def incident_columns():
    json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incident_type", sa.Enum(*INCIDENT_TYPES, name="incident_type_enum"), nullable=False),
        sa.Column("payment_method", sa.Enum(*PAYMENT_METHODS, name="payment_method_enum"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2)),
        sa.Column("incident_time", sa.DateTime(timezone=True)),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        sa.Column("transaction_id", sa.String(128)),
        sa.Column("transaction_status", sa.String(32)),
        *[sa.Column(name, sa.Boolean()) for name in (
            "is_fraud_ongoing", "is_account_compromised", "is_credentials_exposed",
            "is_otp_shared", "is_pin_shared", "is_password_shared", "is_remote_access_granted",
            "unauthorized_activity_continuing", "potential_additional_loss",
            "account_secured", "evidence_available")],
        sa.Column("incident_subtype", sa.String(128)),
        *[sa.Column(name, sa.String(64)) for name in ("affected_person_type", "platform", "account_type")],
        *[sa.Column(name, sa.Boolean()) for name in ("immediate_danger", "threat_or_blackmail", "content_still_online")],
        sa.Column("account_access", sa.String(32)),
        sa.Column("attacker_active", sa.Boolean()),
        sa.Column("sensitive_information_exposed", sa.Boolean()),
        sa.Column("evidence_types", json_type),
        sa.Column("urgency_score", sa.Integer()),
        sa.Column("other_crime_sub_category", sa.Enum(*SUBCATEGORIES, name="other_crime_sub_category_enum")),
        sa.Column("details", json_type),
        sa.Column("urgency", sa.Enum(*URGENCIES, name="urgency_enum"), nullable=False),
        sa.Column("urgency_computed_at", sa.DateTime(timezone=True)),
        sa.Column("severity", sa.Enum(*URGENCIES, name="urgency")),
        sa.Column("ongoing_risk", sa.Enum(*URGENCIES, name="urgency")),
        sa.Column("recovery_window", sa.String(32)),
        sa.Column("urgency_reasons", json_type),
        sa.Column("status", sa.Enum(*STATUSES, name="incident_status_enum"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "incidents" not in inspector.get_table_names():
        op.create_table("incidents", *incident_columns())
    else:
        existing = {c["name"] for c in inspector.get_columns("incidents")}
        # Deliberate support for Phase 0 startup-created incident tables.
        if bind.dialect.name == "postgresql":
            for enum_name, values in (("incident_type_enum", INCIDENT_TYPES), ("payment_method_enum", PAYMENT_METHODS), ("urgency_enum", URGENCIES)):
                for value in values:
                    with op.get_context().autocommit_block():
                        op.execute(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")
        for column in incident_columns():
            if column.name not in existing:
                if isinstance(column.type, sa.Enum):
                    column.type.create(bind, checkfirst=True)
                op.add_column("incidents", column)
        if "occurred_at" not in existing:
            op.execute("UPDATE incidents SET occurred_at = incident_time WHERE occurred_at IS NULL")
    if "evidence" not in inspector.get_table_names():
        op.create_table(
            "evidence",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("incident_id", sa.Uuid(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("original_filename", sa.String(255), nullable=False),
            sa.Column("stored_filename", sa.String(255), nullable=False, unique=True),
            sa.Column("content_type", sa.String(128)),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_evidence_incident_id", "evidence", ["incident_id"])


def downgrade():
    # Baseline downgrade is intentionally destructive; back up before invoking.
    op.drop_table("evidence")
    op.drop_table("incidents")
