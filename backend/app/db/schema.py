"""
Bring the incidents table in line with the current model.

Phase 0 used create_all only, which will not add columns or enum values to
an existing database. This runs after create_all and is a no-op on a fresh
schema.
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.base import Base

PG_ENUM_VALUES: dict[str, tuple[str, ...]] = {
    "incident_type_enum": (
        "financial_fraud",
        "phishing",
        "identity_theft",
        "social_media",
        "job_scam",
        "other",
    ),
    "payment_method_enum": (
        "upi",
        "bank_transfer",
        "card",
        "wallet",
        "unknown",
        "debit_card",
        "credit_card",
        "net_banking",
    ),
    "urgency_enum": (
        "critical",
        "high",
        "medium",
        "low",
        "medium_low",
        "standard",
    ),
}

NEW_COLUMNS: tuple[tuple[str, str, str], ...] = (
    # (name, postgres type, sqlite type)
    ("occurred_at", "TIMESTAMP WITH TIME ZONE", "TIMESTAMP"),
    ("transaction_id", "VARCHAR(128)", "VARCHAR(128)"),
    ("urgency_computed_at", "TIMESTAMP WITH TIME ZONE", "TIMESTAMP"),
)


def ensure_schema(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "incidents" not in inspector.get_table_names():
        return

    dialect = engine.dialect.name
    existing = {col["name"] for col in inspector.get_columns("incidents")}

    if dialect == "postgresql":
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            for enum_name, values in PG_ENUM_VALUES.items():
                for value in values:
                    conn.execute(
                        text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")
                    )

    missing_sql: list[str] = []
    for name, pg_type, sqlite_type in NEW_COLUMNS:
        if name in existing:
            continue
        col_type = sqlite_type if dialect == "sqlite" else pg_type
        missing_sql.append(f"ALTER TABLE incidents ADD COLUMN {name} {col_type}")

    if not missing_sql:
        return

    with engine.begin() as conn:
        for stmt in missing_sql:
            conn.execute(text(stmt))
        if "occurred_at" not in existing:
            conn.execute(
                text(
                    "UPDATE incidents SET occurred_at = incident_time "
                    "WHERE occurred_at IS NULL AND incident_time IS NOT NULL"
                )
            )
