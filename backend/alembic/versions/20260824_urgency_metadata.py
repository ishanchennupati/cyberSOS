"""Add multi-factor urgency inputs and explanations.

Revision ID: 20260824_urgency_metadata
Revises: 20260824_phase2
"""
from alembic import op
import sqlalchemy as sa

revision = "20260824_urgency_metadata"
down_revision = "20260824_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("incidents")}
    columns = (
        ("transaction_status", sa.String(length=32)),
        ("is_fraud_ongoing", sa.Boolean()),
        ("is_account_compromised", sa.Boolean()),
        ("is_credentials_exposed", sa.Boolean()),
        ("is_otp_shared", sa.Boolean()),
        ("is_pin_shared", sa.Boolean()),
        ("is_password_shared", sa.Boolean()),
        ("is_remote_access_granted", sa.Boolean()),
        ("unauthorized_activity_continuing", sa.Boolean()),
        ("potential_additional_loss", sa.Boolean()),
        ("account_secured", sa.Boolean()),
        ("evidence_available", sa.Boolean()),
        ("severity", sa.String(length=32)),
        ("ongoing_risk", sa.String(length=32)),
        ("recovery_window", sa.String(length=32)),
        ("urgency_reasons", sa.JSON()),
    )
    for name, column in columns:
        if name not in existing:
            op.add_column("incidents", sa.Column(name, column, nullable=True))


def downgrade() -> None:
    for name in (
        "urgency_reasons", "recovery_window", "ongoing_risk", "severity",
        "evidence_available", "account_secured", "potential_additional_loss",
        "unauthorized_activity_continuing", "is_remote_access_granted",
        "is_password_shared", "is_pin_shared", "is_otp_shared",
        "is_credentials_exposed", "is_account_compromised", "is_fraud_ongoing",
        "transaction_status",
    ):
        op.drop_column("incidents", name)