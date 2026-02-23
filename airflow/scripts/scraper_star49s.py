"""
Scraper for UK49 results from star49s.com

This scraper:
1. Fetches both lunchtime and teatime draw history pages using Playwright (JavaScript rendering)
2. Extracts draw dates and winning numbers from the rendered page
3. Returns a DataFrame with columns: draw_date, draw_type, numbers (comma-separated)

Note: Uses Playwright for headless browser automation since star49s.com uses Next.js with client-side rendering.
"""

import logging
import pandas as pd
from datetime import datetime
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

LUNCHTIME_URL = 'https://star49s.com/results/lunchtime/history'
TEATIME_URL = 'https://star49s.com/results/teatime/history'


def scrape_url_with_playwright(url: str, draw_type: str) -> pd.DataFrame:
    """Scrape UK49 results using Playwright (handles JavaScript rendering).

    Args:
        url: The history page URL (lunchtime or teatime)
        draw_type: 'lunchtime' or 'teatime'

    Returns a DataFrame with columns: draw_date, draw_type, numbers (comma-separated).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error('Playwright not installed. Install with: pip install playwright')
        logger.error('Then run: playwright install chromium')
        return pd.DataFrame()

    logger.info(f'Fetching {url} with Playwright (draw_type={draw_type})')

    rows = []

    try:
        with sync_playwright() as p:
            # Use chromium browser for better performance
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 720})
            
            # Set timeout and navigate
            page.set_default_timeout(30000)
            logger.info(f'Navigating to {url}...')
            page.goto(url, wait_until='networkidle')
            
            # Wait for results to load (look for result rows)
            logger.info('Waiting for results to load...')
            try:
                page.wait_for_selector('[data-testid="result"], .result, tr[data-result]', timeout=10000)
            except:
                logger.warning('Timeout waiting for result elements, continuing anyway')
            
            # Extract all visible text content
            content = page.content()
            
            # Try multiple selectors for rows
            result_rows = []
            for selector in [
                '[data-testid="result"]',
                '.result',
                'tr[data-result]',
                '[class*="result"]',
                'div[class*="DrawRow"]',
                'article',
            ]:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        logger.info(f'Found {len(elements)} elements with selector: {selector}')
                        result_rows = elements
                        break
                except:
                    pass
            
            # Extract text from each row
            for row in result_rows:
                try:
                    text = row.text_content()
                    # Look for date and number patterns
                    # Pattern: DD/MM or similar date format followed by 6 numbers
                    matches = re.findall(r'(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)[^\d]*(\d{1,2})[^\d]*(\d{1,2})[^\d]*(\d{1,2})[^\d]*(\d{1,2})[^\d]*(\d{1,2})[^\d]*(\d{1,2})?', text)
                    
                    for match in matches:
                        date_str = match[0]
                        numbers = [int(n) for n in match[1:7] if n]
                        
                        # Validate: 6 unique numbers between 1-49
                        if len(numbers) >= 6 and 1 <= min(numbers) and max(numbers) <= 49:
                            numbers = sorted(set(numbers))[:6]
                            if len(numbers) == 6:
                                rows.append({
                                    'draw_date': date_str,
                                    'draw_type': draw_type,
                                    'numbers': ','.join(map(str, numbers))
                                })
                
                except Exception as e:
                    logger.debug(f'Error extracting row: {e}')
            
            browser.close()
            
    except Exception as e:
        logger.exception(f'Error scraping {url}: {e}')
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    logger.info(f'Scraped {len(df)} draws from {draw_type}')
    return df


def scrape_star49s_history():
    """Scrape UK49 lunchtime and teatime results from star49s.com.

    Returns a DataFrame with columns: draw_date, draw_type, numbers (comma-separated).
    """
    # Fetch both lunchtime and teatime draws
    lunchtime_df = scrape_url_with_playwright(LUNCHTIME_URL, 'lunchtime')
    teatime_df = scrape_url_with_playwright(TEATIME_URL, 'teatime')
    
    # Combine results
    if not lunchtime_df.empty and not teatime_df.empty:
        combined_df = pd.concat([lunchtime_df, teatime_df], ignore_index=True)
    elif not lunchtime_df.empty:
        combined_df = lunchtime_df
    elif not teatime_df.empty:
        combined_df = teatime_df
    else:
        combined_df = pd.DataFrame()
    
    logger.info(f'Total: Scraped {len(combined_df)} draws from star49s.com (lunchtime + teatime)')
    return combined_df


if __name__ == '__main__':
    # Quick test
    logging.basicConfig(level=logging.INFO)
    df = scrape_star49s_history()
    print(df.head(10))
    print(f'\nTotal draws: {len(df)}')
    if not df.empty:
        print(f'Draw types: {df["draw_type"].value_counts().to_dict()}')
