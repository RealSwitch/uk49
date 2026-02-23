import logging
import pandas as pd
from sqlalchemy import create_engine
import os
import importlib.util

logger = logging.getLogger(__name__)


def load_scraper():
    """Load the star49s scraper from the local script."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    scraper_path = os.path.join(repo_root, 'airflow', 'scripts', 'scraper_star49s.py')
    if not os.path.exists(scraper_path):
        raise FileNotFoundError(f"scraper_star49s.py not found at {scraper_path}")
    spec = importlib.util.spec_from_file_location('scraper_star49s', scraper_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch_draws():
    """Scrape UK49 Drivetime results from star49s.com/results/drivetime/history."""
    try:
        scraper_mod = load_scraper()
        df = scraper_mod.scrape_star49s_history()
        return df
    except Exception as e:
        logger.exception(f'fetch_draws failed: {e}')
        return pd.DataFrame()


def transform(df: pd.DataFrame) -> pd.DataFrame:
    logger.info('Transforming draws')
    if df.empty:
        return df
    # normalize fields
    df = df.copy()
    # ensure draw_date exists; otherwise use local date
    if 'draw_date' not in df.columns:
        df['draw_date'] = datetime.utcnow().date().isoformat()
    df['numbers'] = df['numbers'].astype(str)
    # create a numeric list column for convenience
    def to_list(s):
        try:
            return [int(x) for x in s.split(',') if x.strip()]
        except Exception:
            return []

    df['numbers_list'] = df['numbers'].apply(to_list)
    return df


def load_to_db(df: pd.DataFrame):
    if df.empty:
        logger.info('No data to load to DB')
        return

    # Prefer the shared engine from the API module if available so all
    # components use the same DB connection configuration.
    try:
        from api.database import engine
        logger.info('Using engine from api.database')
    except Exception:
        url = os.environ.get('DATABASE_URL') or 'sqlite:///uk49.db'
        logger.info('Falling back to DATABASE_URL: %s', url)
        engine = create_engine(url)

    logger.info('Loading %d rows to DB', len(df))
    # write only selected columns
    if 'draw_type' in df.columns:
        to_save = df[['draw_date', 'draw_type', 'numbers']].copy()
    else:
        to_save = df[['draw_date', 'numbers']].copy()
        to_save['draw_type'] = 'drivetime'
    # ensure table exists or let pandas create it
    try:
        to_save.to_sql('draws', engine, if_exists='append', index=False)
    except Exception:
        logger.exception('Failed to write draws to DB')


def etl():
    df = fetch_draws()
    df = transform(df)
    load_to_db(df)

