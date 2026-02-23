"""
Test different API endpoints for star49s.com data
"""

import requests
import json

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)

headers = {'User-Agent': USER_AGENT}

# Common API endpoint patterns
endpoints = [
    'https://star49s.com/api/results/lunchtime/history',
    'https://star49s.com/api/results/teatime/history',
    'https://star49s.com/api/lunchtime/history',
    'https://star49s.com/api/teatime/history',
    'https://api.star49s.com/results/lunchtime',
    'https://api.star49s.com/results/teatime',
    'https://star49s.com/results/lunchtime/history.json',
    'https://star49s.com/results/teatime/history.json',
    'https://star49s.com/api/results',
    'https://star49s.com/api/draws',
]

print('Testing API endpoints...\n')

for url in endpoints:
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f'{resp.status_code} - {url}')
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f'  ✓ Valid JSON response')
                print(f'  Keys: {list(data.keys()) if isinstance(data, dict) else "Array"}')
                if isinstance(data, dict):
                    print(f'  First 200 chars: {str(data)[:200]}')
            except:
                print(f'  ✗ Not JSON')
                print(f'  Content preview: {resp.text[:100]}')
    except requests.exceptions.Timeout:
        print(f'⏱ TIMEOUT - {url}')
    except Exception as e:
        print(f'✗ ERROR - {url}: {str(e)[:50]}')
