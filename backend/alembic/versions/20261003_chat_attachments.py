"""Durable owned turn/evidence linkage, reusing originals and turn snapshots."""
from alembic import op
import sqlalchemy as sa

revision = '20261003_chat_attachments'
down_revision = '20261001_understanding'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('evidence', sa.Column('staged_for_chat', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table('conversation_attachments',
        sa.Column('evidence_id', sa.Uuid(), sa.ForeignKey('evidence.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('turn_id', sa.Uuid(), sa.ForeignKey('conversation_turns.id', ondelete='CASCADE'), nullable=False))
    op.create_index('ix_conversation_attachments_turn_id', 'conversation_attachments', ['turn_id'])


def downgrade():
    op.drop_table('conversation_attachments')
    op.drop_column('evidence', 'staged_for_chat')
