"""
Diagnostic tool to inspect HTML structure of star49s.com pages.

This script fetches the raw HTML from the lunchtime/teatime history pages
and saves them to files so you can inspect the structure.

Usage:
  docker-compose exec api python scripts/inspect_star49s.py

This will create:
  - lunchtime_page.html
  - teatime_page.html
"""

import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)

URLS = {
    'lunchtime': 'https://star49s.com/results/lunchtime/history',
    'teatime': 'https://star49s.com/results/teatime/history'
}


def inspect_page(url: str, draw_type: str):
    """Fetch and save the HTML from a page."""
    logger.info(f'Fetching {url}...')
    
    headers = {'User-Agent': USER_AGENT}
    
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        
        # Save to file
        filename = f'{draw_type}_page.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(resp.text)
        
        logger.info(f'✓ Saved {len(resp.text)} bytes to {filename}')
        
        # Print some basic info
        logger.info(f'\nHTML Analysis for {draw_type}:')
        logger.info(f'  - Content length: {len(resp.text)} bytes')
        logger.info(f'  - Status code: {resp.status_code}')
        
        # Look for common table indicators
        if '<table' in resp.text.lower():
            logger.info('  ✓ Found <table> tags')
        else:
            logger.info('  ✗ No <table> tags found')
        
        if 'tbody' in resp.text.lower():
            logger.info('  ✓ Found <tbody>')
        else:
            logger.info('  ✗ No <tbody>')
        
        if 'javascript' in resp.text.lower() or 'fetch' in resp.text.lower():
            logger.info('  ⚠ Page likely uses JavaScript/AJAX for content loading')
        
        # Look for common data patterns
        if '/results/' in resp.text:
            logger.info('  ✓ Found "/results/" references')
        
        if 'data' in resp.text.lower() and 'json' in resp.text.lower():
            logger.info('  ⚠ Potential JSON data embedded in page')
        
        # Check for common class/id indicators
        if 'result' in resp.text.lower():
            logger.info('  ✓ Found "result" keyword')
        if 'history' in resp.text.lower():
            logger.info('  ✓ Found "history" keyword')
        if 'draw' in resp.text.lower():
            logger.info('  ✓ Found "draw" keyword')
        
        return True
        
    except Exception as e:
        logger.exception(f'Error fetching {url}: {e}')
        return False


if __name__ == '__main__':
    logger.info('Star49s.com HTML Inspector')
    logger.info('=' * 50)
    
    for draw_type, url in URLS.items():
        inspect_page(url, draw_type)
        logger.info('')
    
    logger.info('=' * 50)
    logger.info('HTML files saved. Open them in a text editor to inspect the structure.')
    logger.info('Look for data in: <div>, <span>, <script> tags, or embedded JSON.')
