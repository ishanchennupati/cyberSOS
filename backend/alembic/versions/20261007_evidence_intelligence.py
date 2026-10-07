"""Immutable private extraction attempts and revision-controlled partial reviews."""
from alembic import op
import sqlalchemy as sa

revision = '20261007_evidence_intelligence'
down_revision = '20261003_chat_attachments'
branch_labels = depends_on = None


def upgrade():
    op.create_table('evidence_attempts',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('evidence_id', sa.Uuid(), sa.ForeignKey('evidence.id', ondelete='CASCADE'), nullable=False),
        sa.Column('incident_id', sa.Uuid(), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('base_revision', sa.Integer(), nullable=False),
        sa.Column('base_facts', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(24), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('model', sa.String(128), nullable=False),
        sa.Column('candidates', sa.JSON(), nullable=False),
        sa.Column('failure', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    for column in ('evidence_id', 'incident_id'):
        op.create_index('ix_evidence_attempts_' + column, 'evidence_attempts', [column])
    op.create_index('uq_evidence_active_analysis', 'evidence_attempts', ['evidence_id'], unique=True,
        sqlite_where=sa.text("status = 'processing'"), postgresql_where=sa.text("status = 'processing'"))
    op.create_table('evidence_reviews',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('attempt_id', sa.Uuid(), sa.ForeignKey('evidence_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('turn_id', sa.Uuid(), sa.ForeignKey('conversation_turns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('decisions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    for column in ('attempt_id', 'turn_id'):
        op.create_index('ix_evidence_reviews_' + column, 'evidence_reviews', [column])


def downgrade():
    op.drop_table('evidence_reviews')
    op.drop_table('evidence_attempts')
