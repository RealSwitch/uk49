"""
Scraper for UK49 Drivetime results from star49s.com/results/drivetime/history

This scraper:
1. Fetches the history page with a user-agent
2. Parses the HTML table for draw dates and numbers
3. Returns a DataFrame with columns: draw_date, numbers
"""

import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# User-Agent to avoid bot blocking
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)

HISTORY_URL = 'https://star49s.com/results/drivetime/history'


def scrape_star49s_history():
    """Scrape UK49 Drivetime draw results from star49s.com history page.

    Returns a DataFrame with columns: draw_date, numbers (comma-separated).
    """
    logger.info(f'Fetching {HISTORY_URL}')

    headers = {'User-Agent': USER_AGENT}

    try:
        resp = requests.get(HISTORY_URL, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.exception(f'Error fetching {HISTORY_URL}: {e}')
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, 'lxml')

    # Look for a table containing results
    rows = []
    
    # Try to find result tables (multiple tables possible)
    tables = soup.find_all('table')
    logger.info(f'Found {len(tables)} table(s)')

    for table in tables:
        for tr in table.find_all('tr'):
            cols = [td.get_text(separator=' ', strip=True) for td in tr.find_all(['td', 'th'])]
            
            if not cols or len(cols) < 2:
                continue

            # Skip header rows
            if any(h in cols[0].lower() for h in ['date', 'draw', 'time']):
                continue

            # Heuristic: first column is date-like, rest are numbers
            date_str = cols[0]
            # Check if it starts with a date pattern (DD/MM, DD-MM, or similar)
            if not re.match(r'\d{1,2}[-/]\d{1,2}', date_str):
                continue

            # Remaining cols should contain numbers
            num_str = ' '.join(cols[1:])
            # Extract all 1-2 digit numbers
            nums = re.findall(r'\d{1,2}', num_str)
            
            # UK49 draws 6 numbers; filter by that
            if len(nums) >= 6:
                # Take first 6 unique numbers
                nums = sorted(set([int(n) for n in nums[:6]]))
                if 1 <= min(nums) and max(nums) <= 49:
                    rows.append({
                        'draw_date': date_str,
                        'numbers': ','.join(map(str, nums))
                    })

    if not rows:
        logger.warning('No result rows found in tables')
        # Try alternative: look for any div/span blocks with date + numbers pattern
        text_blocks = soup.find_all(['div', 'span', 'p'])
        for block in text_blocks:
            text = block.get_text(' ', strip=True)
            # Look for patterns like "15/02 12 34 45 02 33 22"
            matches = re.findall(r'(\d{1,2}[-/]\d{1,2}).*?(\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2})', text)
            for date_str, nums_str in matches:
                nums = [int(x) for x in re.findall(r'\d{1,2}', nums_str)]
                if len(nums) >= 6 and 1 <= min(nums) and max(nums) <= 49:
                    rows.append({
                        'draw_date': date_str,
                        'numbers': ','.join(map(str, sorted(nums[:6])))
                    })

    df = pd.DataFrame(rows)
    logger.info(f'Scraped {len(df)} draws from star49s.com')
    return df


if __name__ == '__main__':
    # Quick test
    logging.basicConfig(level=logging.INFO)
    df = scrape_star49s_history()
    print(df.head())
