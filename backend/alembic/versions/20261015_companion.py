"""Optional identity, secure recovery and 90-day synthetic case lifecycle."""
from alembic import op
import sqlalchemy as sa

revision = '20261015_companion'
down_revision = '20261010_reporting'
branch_labels = depends_on = None


def upgrade():
    op.add_column('incidents', sa.Column('access_epoch', sa.String(80), nullable=False, server_default='1'))
    op.add_column('incidents', sa.Column('retention_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('incidents', sa.Column('deleting_at', sa.DateTime(timezone=True), nullable=True))
    from datetime import datetime, timedelta, timezone
    from app.core.config import get_settings
    op.get_bind().execute(sa.text('UPDATE incidents SET retention_expires_at = :expiry'),
        {'expiry': datetime.now(timezone.utc)+timedelta(days=get_settings().CASE_RETENTION_DAYS)})
    from app.models.return_access import Account, AccountSession, EmailChallenge, CaseOwner, CaseRecovery, AuthThrottle, DeletionJob
    for model in (Account, AccountSession, EmailChallenge, CaseOwner, CaseRecovery, AuthThrottle, DeletionJob):
        model.__table__.create(op.get_bind())


def downgrade():
    for name in ('case_deletions','auth_throttles','case_recovery','case_owners','email_challenges','account_sessions','accounts'):
        op.drop_table(name)
    for name in ('deleting_at','retention_expires_at','access_epoch'):
        op.drop_column('incidents', name)
