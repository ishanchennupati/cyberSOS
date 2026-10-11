"""Owned, revision-bound reporting review snapshots."""
from alembic import op
import sqlalchemy as sa
revision='20261010_reporting'
down_revision='20261007_evidence_intelligence'
branch_labels=depends_on=None


def upgrade():
    op.create_table('reporting_snapshots',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('incident_id',sa.Uuid(),sa.ForeignKey('incidents.id',ondelete='CASCADE'),nullable=False),
        sa.Column('source_revision',sa.Integer(),nullable=False),
        sa.Column('source_digest',sa.String(64),nullable=False),
        sa.Column('packet',sa.JSON(),nullable=False),
        sa.Column('narrative',sa.JSON(),nullable=False),
        sa.Column('reviewed_at',sa.DateTime(timezone=True)),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_reporting_snapshots_incident_id','reporting_snapshots',['incident_id'])


def downgrade():
    op.drop_table('reporting_snapshots')
