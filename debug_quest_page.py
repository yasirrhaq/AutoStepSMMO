#!/usr/bin/env python3
"""
Debug script to fetch and analyze the quest page HTML
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from simplemmo_bot import SimpleMMOBot
import re
import json
from bs4 import BeautifulSoup

def main():
    print("="*60)
    print("Quest Page HTML Debug Tool")
    print("="*60)
    print()
    
    # Initialize bot
    bot = SimpleMMOBot()
    
    # Login
    print("Logging in...")
    if not bot.login():
        print("❌ Login failed!")
        return
    print("✓ Login successful")
    print()
    
    # Fetch quest page
    print("Fetching quest page...")
    response = bot.session.get('https://web.simple-mmo.com/quests')
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch quest page (status {response.status_code})")
        return
    
    print(f"✓ Page fetched successfully")
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"  Content-Encoding: {response.headers.get('Content-Encoding', 'None')}")
    print(f"  Content-Length: {len(response.content)} bytes (raw)")
    print(f"  Text Length: {len(response.text)} chars (decoded)")
    print()
    
    # Check if response is actually HTML
    if not response.text.strip().startswith('<'):
        print("❌ WARNING: Response doesn't look like HTML!")
        print(f"First 200 chars: {response.text[:200]}")
        print()
    
    # Save full HTML to file
    html_file = Path(__file__).parent / "debug_quest_page.html"
    html_file.write_text(response.text, encoding='utf-8')
    print(f"✓ Saved full HTML to: {html_file}")
    print()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Debug 1: Look for expedition data in JavaScript
    print("-"*60)
    print("DEBUG 1: Looking for expedition data in JavaScript...")
    print("-"*60)
    
    script_tags = soup.find_all('script')
    print(f"Found {len(script_tags)} script tags")
    
    expedition_found = False
    for i, script in enumerate(script_tags):
        script_text = script.string or ""
        if 'expedition' in script_text.lower():
            print(f"\nScript tag {i+1} contains 'expedition':")
            # Show first 500 chars
            preview = script_text[:500]
            print(preview)
            if len(script_text) > 500:
                print(f"... ({len(script_text) - 500} more characters)")
            expedition_found = True
    
    if not expedition_found:
        print("❌ No script tags contain 'expedition'")
    print()
    
    # Debug 2: Look for quest buttons with Alpine.js
    print("-"*60)
    print("DEBUG 2: Looking for quest buttons with Alpine.js...")
    print("-"*60)
    
    alpine_buttons = soup.find_all('button', {'x-on:click': True})
    print(f"Found {len(alpine_buttons)} buttons with x-on:click")
    
    quest_buttons = [b for b in alpine_buttons if 'expedition' in str(b.get('x-on:click', '')).lower()]
    print(f"Found {len(quest_buttons)} buttons with 'expedition' in x-on:click")
    
    if quest_buttons:
        print("\nFirst quest button HTML:")
        print(quest_buttons[0].prettify()[:800])
    else:
        print("❌ No quest buttons found")
    print()
    
    # Debug 3: Look for any buttons
    print("-"*60)
    print("DEBUG 3: All buttons on page...")
    print("-"*60)
    
    all_buttons = soup.find_all('button')
    print(f"Found {len(all_buttons)} total buttons")
    
    if all_buttons:
        print("\nFirst button:")
        print(all_buttons[0].prettify()[:400])
    print()
    
    # Debug 4: Look for common quest page elements
    print("-"*60)
    print("DEBUG 4: Looking for common quest page elements...")
    print("-"*60)
    
    # Look for page title
    title = soup.find('h1') or soup.find('h2')
    if title:
        print(f"Page title: {title.get_text(strip=True)}")
    
    # Look for any divs with "quest" in class name
    quest_divs = soup.find_all('div', class_=re.compile(r'quest', re.I))
    print(f"Found {len(quest_divs)} divs with 'quest' in class name")
    
    # Look for any elements with "expedition" in attributes
    expedition_elems = soup.find_all(attrs={'data-expedition': True})
    print(f"Found {len(expedition_elems)} elements with data-expedition attribute")
    print()
    
    # Debug 5: API parameter extraction
    print("-"*60)
    print("DEBUG 5: Looking for API parameters (expires/signature)...")
    print("-"*60)
    
    # Try to find expires parameter
    expires_pattern = r'expires["\'\s:=]+(\d+)'
    expires_match = re.search(expires_pattern, response.text)
    if expires_match:
        print(f"✓ Found 'expires' parameter: {expires_match.group(1)}")
    else:
        print("❌ Could not find 'expires' parameter")
    
    # Try to find signature parameter
    sig_pattern = r'signature["\'\s:=]+([a-fA-F0-9]+)'
    sig_match = re.search(sig_pattern, response.text)
    if sig_match:
        print(f"✓ Found 'signature' parameter: {sig_match.group(1)[:20]}...")
    else:
        print("❌ Could not find 'signature' parameter")
    print()
    
    # Debug 6: Check for Alpine.js
    print("-"*60)
    print("DEBUG 6: Checking for Alpine.js framework...")
    print("-"*60)
    
    alpine_divs = soup.find_all(attrs={'x-data': True})
    print(f"Found {len(alpine_divs)} elements with x-data (Alpine.js components)")
    
    if alpine_divs:
        print("\nFirst Alpine.js component:")
        print(f"x-data value: {alpine_divs[0].get('x-data', '')[:200]}")
    print()
    
    print("="*60)
    print("Debug complete! Check debug_quest_page.html for full HTML")
    print("="*60)

if __name__ == '__main__':
    main()
