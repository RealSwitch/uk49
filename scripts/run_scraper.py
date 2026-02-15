"""
Standalone script to run the UK49 scraper and populate PostgreSQL with real data.

Usage:
  python scripts/run_scraper.py

With Docker:
  docker-compose exec api python scripts/run_scraper.py

This script:
1. Fetches real UK49 results from https://uk49s.net/
2. Transforms the data
3. Loads into PostgreSQL database
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_etl_from_path():
  """Dynamically load the etl function from airflow/scripts/etl_tasks.py by file path.

  This avoids importing the installed `airflow` package which can trigger
  heavy initialization (and version conflicts)."""
  import importlib.util
  repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
  etl_path = os.path.join(repo_root, 'airflow', 'scripts', 'etl_tasks.py')
  if not os.path.exists(etl_path):
    raise FileNotFoundError(f"etl_tasks.py not found at {etl_path}")
  spec = importlib.util.spec_from_file_location('uk49_etl_tasks', etl_path)
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod.etl


def main():
  """Run the ETL pipeline to scrape and load real UK49 data."""
  logger.info("Starting UK49 scraper...")
  logger.info("Fetching real data from https://uk49s.net/...")
  try:
    etl = load_etl_from_path()
    etl()
    logger.info("✓ Scraper completed successfully!")
  except Exception as e:
    logger.exception(f"✗ Scraper failed: {e}")
    sys.exit(1)

if __name__ == '__main__':
    main()
