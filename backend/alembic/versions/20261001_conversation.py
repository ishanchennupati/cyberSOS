"""Durable structured conversation state and idempotent turns."""
from alembic import op
import sqlalchemy as sa

revision = '20261001_conversation'
down_revision = '20261001_response_foundation'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('conversation_states',
        sa.Column('incident_id', sa.Uuid(), sa.ForeignKey('incidents.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(16), nullable=False),
        sa.Column('answered', sa.JSON(), nullable=False),
        sa.Column('pending_question', sa.JSON(), nullable=True))
    op.create_table('conversation_turns',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('incident_id', sa.Uuid(), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('type', sa.String(16), nullable=False),
        sa.Column('text', sa.String(256), nullable=False),
        sa.Column('structured_reply', sa.JSON(), nullable=False),
        sa.Column('fact_changes', sa.JSON(), nullable=False),
        sa.Column('pending_question', sa.JSON(), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('incident_id', 'revision', name='uq_conversation_revision'))
    op.create_index('ix_conversation_turns_incident_id', 'conversation_turns', ['incident_id'])


def downgrade():
    op.drop_table('conversation_turns')
    op.drop_table('conversation_states')
