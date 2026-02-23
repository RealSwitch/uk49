"""
Extract and display raw script content from saved HTML
"""

import re

with open('lunchtime_page.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f'Found {len(scripts)} script tags')

# Look for the one that likely contains data (usually contains "data" or "props" or is large)
for i, script in enumerate(scripts):
    if len(script) > 1000:  # Data-bearing scripts are usually large
        print(f'\n--- Script {i} (length: {len(script)}) ---')
        # Show first 1000 chars
        preview = script[:1000]
        print(preview)
        
        # Check what it contains
        if 'window' in script:
            print('\n✓ Contains window object')
        if '__NEXT' in script:
            print('✓ Contains Next.js data')
        if 'props' in script:
            print('✓ Contains props')
        if 'data' in script[:200]:
            print('✓ Contains data in first 200 chars')
        
        # Try to find JSON-like start
        json_start = script.find('{')
        json_end = script.rfind('}')
        if json_start != -1:
            print(f'\n✓ JSON found from position {json_start} to {json_end}')
            print(f'JSON preview: {script[json_start:json_start+200]}...')
        
        break
