"""Guarded additive Phase 5 development migration. Never print secrets or row bodies."""
import json
import os
from pathlib import Path
from sqlalchemy import create_engine,inspect,text
from alembic import command
from alembic.config import Config
from app.core.config import get_settings


def main():
    settings=get_settings()
    engine=create_engine(settings.DATABASE_URL)
    backend=Path(__file__).parents[1]
    config=Config(str(backend/'alembic.ini'))
    config.set_main_option('script_location',str(backend/'alembic'))
    tables=('incidents','evidence','conversation_states','conversation_turns','response_plans','suspect_identifiers','timeline_events')
    with engine.begin() as connection:
        revision=connection.scalar(text('select version_num from alembic_version'))
        if revision not in {'20261003_chat_attachments','20261007_evidence_intelligence'}:
            raise RuntimeError('Unexpected migration revision; refusing to modify this database')
        before={name:connection.scalar(text('select count(*) from '+name)) for name in tables}
        if revision!='20261007_evidence_intelligence' and os.environ.get('PHASE5_APPLY_DEV_MIGRATION')=='1':
            config.attributes['connection']=connection
            command.upgrade(config,'20261007_evidence_intelligence')
        after={name:connection.scalar(text('select count(*) from '+name)) for name in tables}
        if before!=after:
            raise RuntimeError('Existing row counts changed; rolling back')
        current=connection.scalar(text('select version_num from alembic_version'))
        present=set(inspect(connection).get_table_names())
        print(json.dumps({'migration_before':revision,'migration_after':current,'existing_row_counts_unchanged':before==after,
            'attempts_present':'evidence_attempts' in present,'reviews_present':'evidence_reviews' in present,
            'applied':revision!=current}),flush=True)
    engine.dispose()


if __name__=='__main__':main()
