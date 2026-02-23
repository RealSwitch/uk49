"""
Migration script to add draw_type column to existing draws table.

This script:
1. Adds the draw_type column if it doesn't exist
2. Sets default values for existing rows
3. Handles the case where the column already exists

Usage:
  docker-compose exec api python scripts/migrate_draw_type.py

For local development:
  python scripts/migrate_draw_type.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import engine
from sqlalchemy import inspect, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_draw_type():
    """Add draw_type column to draws table if it doesn't exist."""
    inspector = inspect(engine)
    
    # Check if draws table exists
    if 'draws' not in inspector.get_table_names():
        logger.info('✗ Table "draws" does not exist. Nothing to migrate.')
        return
    
    # Check if draw_type column already exists
    columns = [col['name'] for col in inspector.get_columns('draws')]
    
    if 'draw_type' in columns:
        logger.info('✓ Column "draw_type" already exists. Nothing to migrate.')
        return
    
    logger.info('Adding "draw_type" column to draws table...')
    
    try:
        with engine.connect() as conn:
            # Add the column with default value 'lunchtime'
            conn.execute(text(
                "ALTER TABLE draws ADD COLUMN draw_type VARCHAR DEFAULT 'lunchtime' NOT NULL"
            ))
            conn.commit()
            logger.info('✓ Successfully added "draw_type" column')
            
            # List the table structure
            result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='draws' ORDER BY ordinal_position"))
            logger.info('Table structure:')
            for row in result:
                logger.info(f'  - {row[0]}: {row[1]}')
    except Exception as e:
        logger.exception(f'✗ Migration failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    migrate_draw_type()
    logger.info('\n✓ Migration complete. You can now regenerate data with:')
    logger.info('  docker-compose exec api python scripts/generate_sample_data.py 90')
