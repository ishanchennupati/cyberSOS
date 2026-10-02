"""Retain complete bounded natural-language turns; JSON snapshots need no new columns."""
from alembic import op
import sqlalchemy as sa

revision = '20261001_understanding'
down_revision = '20261001_conversation'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('conversation_turns') as batch:
        batch.alter_column('text', existing_type=sa.String(256), type_=sa.Text(), existing_nullable=False)


def downgrade():
    # Do not truncate citizens' saved stories during rollback.
    pass
