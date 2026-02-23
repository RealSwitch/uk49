"""
Diagnostic script to inspect the actual HTML from star49s.com history page.

Run with:
  docker-compose exec api python scripts/inspect_page.py
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)


draw_urls = {
    'teatime': 'https://star49s.com/results/teatime/history',
    'lunchtime': 'https://star49s.com/results/lunchtime/history',
}

headers = {'User-Agent': USER_AGENT}

for draw, url in draw_urls.items():
    logger.info(f'Fetching {draw} draw: {url}...')
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        logger.info(f'Status: {resp.status_code} for {draw}')

        # Save raw HTML for inspection
        out_path = f'/tmp/page_{draw}.html'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(resp.text)
        logger.info(f'Saved to {out_path}')

        # Show first 3000 chars
        print(f'\n--- {draw.upper()} PAGE CONTENT (first 3000 chars) ---')
        print(resp.text[:3000])
        print('--- END ---\n')

        # Parse and show structure
        soup = BeautifulSoup(resp.text, 'lxml')

        # Find all text
        text = soup.get_text(' ', strip=True)[:1000]
        print(f'Text content (first 1000 chars): {text}\n')

        # Find all tables
        tables = soup.find_all('table')
        print(f'Found {len(tables)} tables')
        for i, t in enumerate(tables[:3]):
            print(f'  Table {i}: {len(t.find_all("tr"))} rows')

        # Find all divs with class containing "result"
        result_divs = soup.find_all('div', class_=lambda x: x and 'result' in x.lower())
        print(f'Found {len(result_divs)} divs with "result" in class')

        # Find all elements with data
        scripts = soup.find_all('script')
        print(f'Found {len(scripts)} script tags')

        # Look for JSON data in scripts
        for i, script in enumerate(scripts[:5]):
            content = script.string
            if content and ('data' in content.lower() or 'result' in content.lower() or '[' in content):
                print(f'Script {i} (first 500 chars): {content[:500]}...')

    except Exception as e:
        logger.exception(f'Error fetching {draw}: {e}')
