"""
Test DB connectivity using the shared `api.database` engine.

Run inside the `api` container:

  docker-compose exec api python scripts/test_db.py

Or locally (after installing requirements):

  python scripts/test_db.py

This script prints DB URL, tries to connect and lists a sample query result.
"""
import sys
import os

# Make sure project package imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import DATABASE_URL, engine, test_connection
from sqlalchemy import text

print('DATABASE_URL:', DATABASE_URL)
print('Testing connection...')

ok = test_connection()
if not ok:
    print('✗ Connection test failed. Please verify DATABASE_URL and network access.')
    sys.exit(2)

print('✓ Connection test succeeded')

# Run a small query to show tables or sample draws
try:
    with engine.connect() as conn:
        # Try select count
        res = conn.execute(text("SELECT count(*) FROM draws"))
        cnt = res.scalar()
        print('draws table count:', cnt)
except Exception as e:
    print('Note: could not query draws table (may not exist yet):', e)

print('Done')
