"""
Analyze the structure of saved HTML files from star49s.com
"""

import json
import re

def analyze_html(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f'\n=== Analyzing {filename} ===')
    print(f'Total length: {len(content)} bytes')
    
    # Find all script tags
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    print(f'Found {len(scripts)} script tags')
    
    # Try to find JSON-like content
    json_patterns = re.findall(r'\{[^}]*"(results|draw|date|number)[^}]*\}', content)
    print(f'Found {len(json_patterns)} JSON-like objects with draw-related keys')
    
    # Look for the word "results" and extract context
    results_matches = list(re.finditer(r'"results"', content))
    print(f'Found {len(results_matches)} instances of "results"')
    
    if results_matches:
        # Get the first match and show context
        match = results_matches[0]
        start = max(0, match.start() - 100)
        end = min(len(content), match.end() + 500)
        
        print(f'\nFirst "results" context (chars {start}-{end}):')
        context = content[start:end]
        print(repr(context[:300]))
    
    # Search for numbers patterns (1-2 digits)
    number_sequences = re.findall(r'\[\s*[0-9]{1,2}(?:,\s*[0-9]{1,2}){4,}\s*\]', content)
    print(f'\nFound {len(number_sequences)} number sequences (possible draw results)')
    
    if number_sequences:
        print(f'Sample number sequences:')
        for seq in number_sequences[:3]:
            print(f'  {seq}')
    
    # Look for specific patterns
    if 'window.__INITIAL_STATE__' in content:
        print('\n✓ Found window.__INITIAL_STATE__ (Next.js)')
        idx = content.find('window.__INITIAL_STATE__')
        print(content[idx:idx+200])
    
    if '__NEXT_DATA__' in content:
        print('\n✓ Found __NEXT_DATA__ (Next.js SSR)')
        idx = content.find('__NEXT_DATA__')
        print(content[idx:idx+200])
    
    # Look for common result field names
    fields = ['date', 'draw_date', 'drawDate', 'resultDate', 'date_drawn', 
              'numbers', 'winning_numbers', 'balls', 'result']
    found_fields = []
    for field in fields:
        if f'"{field}"' in content:
            found_fields.append(field) 
    
    if found_fields:
        print(f'\n✓ Found potential data fields: {", ".join(found_fields)}')

if __name__ == '__main__':
    analyze_html('lunchtime_page.html')
    analyze_html('teatime_page.html')
