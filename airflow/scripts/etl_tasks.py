import logging
import requests
import pandas as pd
from sqlalchemy import create_engine
import os
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)


def fetch_draws():
    """Scrape recent UK49 draw results from https://uk49s.net/.

    This function uses heuristics to locate a results table on the
    homepage. The exact selectors may need adjustment if the site
    structure changes.
    """
    url = 'https://uk49s.net/'
    logger.info('Fetching draws from %s', url)
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.exception('Error fetching %s: %s', url, e)
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, 'lxml')

    # Try to find a table that contains draw rows
    table = (
        soup.find('table', {'id': 'results'})
        or soup.find('table', {'class': 'results'})
        or soup.find('table')
    )

    rows = []
    if table:
        for tr in table.find_all('tr'):
            cols = [td.get_text(separator=' ', strip=True) for td in tr.find_all('td')]
            # Heuristic: date + 6 numbers (or more)
            if len(cols) >= 7:
                draw_date = cols[0]
                numbers = cols[1:7]
                # normalize date to ISO-ish if possible
                rows.append({'draw_date': draw_date, 'numbers': ','.join(numbers)})
    else:
        logger.warning('No table found when scraping %s', url)

    # As a safety: attempt to find any blocks that look like draws
    if not rows:
        # find any occurrence of 6 numbers in text nodes
        text = soup.get_text(' ', strip=True)
        import re

        matches = re.findall(r'(\d{1,2}[,\s])+\d{1,2}', text)
        for m in matches[:20]:
            nums = re.findall(r'\d{1,2}', m)
            if len(nums) >= 6:
                rows.append({'draw_date': datetime.utcnow().date().isoformat(), 'numbers': ','.join(nums[:6])})

    df = pd.DataFrame(rows)
    logger.info('Scraped %d draw rows', len(df))
    return df


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
    to_save = df[['draw_date', 'numbers']].copy()
    # ensure table exists or let pandas create it
    try:
        to_save.to_sql('draws', engine, if_exists='append', index=False)
    except Exception:
        logger.exception('Failed to write draws to DB')


def etl():
    df = fetch_draws()
    df = transform(df)
    load_to_db(df)

