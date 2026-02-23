import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///uk49.db')

# Create an engine tuned for long-running container apps. `pool_pre_ping`
# helps avoid "connection already closed" errors when RDS closes idle
# connections. `future=True` uses SQLAlchemy 2.0 style.
engine = create_engine(
	DATABASE_URL,
	echo=False,
	future=True,
	pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_connection(timeout_seconds: int = 5) -> bool:
	"""Quick check that the engine can connect and run a simple query.

	Returns True on success, False otherwise.
	"""
	try:
		with engine.connect() as conn:
			# Execute a simple query using SQLAlchemy text(); avoid
			# unsupported execution_options like `timeout` which can
			# raise on some dialects (e.g. sqlite).
			conn.execute(text("SELECT 1"))
		return True
	except Exception:
		return False
