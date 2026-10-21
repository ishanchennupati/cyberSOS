"""Retain cleanup for upload originals whose metadata could not be committed."""
from alembic import op

revision = '20261016_file_cleanup'
down_revision = '20261015_companion'
branch_labels = depends_on = None


def upgrade():
    from app.models.return_access import FileCleanup
    FileCleanup.__table__.create(op.get_bind())


def downgrade():
    op.drop_table('file_cleanup_jobs')
