#!/usr/bin/env python3
"""
Analyze the CAPTCHA page structure
"""

from bs4 import BeautifulSoup

with open('captcha_page_debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=" * 60)
print("CAPTCHA Page Structure Analysis")
print("=" * 60)

# Look for text indicators
if "Please press on the following item" in html:
    print("\n✓ Contains: 'Please press on the following item'")
else:
    print("\n✗ No 'Please press on the following item'")

# Find all divs with size/weight classes
print("\n1. Looking for large/bold text divs:")
for cls in ['font-semibold', 'font-bold', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl']:
    divs = soup.find_all('div', class_=lambda x: x and cls in str(x))
    if divs:
        print(f"\n  {cls}: Found {len(divs)} divs")
        for i, div in enumerate(divs[:3]):
            text = div.text.strip()[:80]
            print(f"    [{i}] {text}")

# Look for the actual item name in a specific structure
print("\n2. Looking for specific structures:")

# Pattern 1: Text in span with specific classes
spans = soup.find_all('span', class_=lambda x: x and 'text-' in str(x))
if spans:
    print(f"\n  Text spans: Found {len(spans)}")
    for span in spans[:5]:
        text = span.text.strip()
        if len(text) < 50 and len(text) > 2:
            print(f"    - {span.get('class')}: '{text}'")

# Pattern 2: Look for verification-related text
verify_section = soup.find(string=lambda text: text and 'verify' in text.lower())
if verify_section:
    parent = verify_section.find_parent()
    print(f"\n  Verify section found: {parent.name}")
    # Look for bold/large text nearby
    sibling = parent.find_next_sibling()
    if sibling:
        print(f"    Next sibling: {sibling.text.strip()[:60]}")

# Pattern 3: Look in the threat-level div
threat_div = soup.find('div', id='threat-level')
if threat_div:
    print(f"\n  Threat-level div found")
    # Find all child divs
    child_divs = threat_div.find_all('div', recursive=False)
    print(f"    Direct children: {len(child_divs)}")
    for i, child in enumerate(child_divs[:5]):
        if child.text.strip():
            print(f"    [{i}] {child.text.strip()[:80]}")

print("\n" + "=" * 60)
