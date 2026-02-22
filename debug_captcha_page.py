#!/usr/bin/env python3
"""
Debug script to see what the CAPTCHA page actually contains
"""

from simplemmo_bot import SimpleMMOBot
import json

print("=" * 60)
print("CAPTCHA Page Inspector")
print("=" * 60)

bot = SimpleMMOBot()

print("\n[Logging in...]")
if bot.login():
    print("✓ Login successful\n")
    
    # Try a travel to see if CAPTCHA appears
    print("[Attempting travel to trigger CAPTCHA...]")
    result = bot.travel()
    
    if result.get("parsed", {}).get("captcha"):
        print("\n✓ CAPTCHA detected in travel response!\n")
        
        # Now fetch the CAPTCHA page
        print("[Fetching CAPTCHA page...]")
        response = bot.session.get(f"{bot.base_url}/i-am-not-a-bot")
        
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        print(f"Length: {len(response.text)} chars\n")
        
        # Save to file for inspection
        with open("captcha_page_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print("✓ Saved full page to: captcha_page_debug.html")
        
        # Show key portions
        if "Please press on the following item" in response.text:
            print("\n✓ Contains: 'Please press on the following item'")
        
        if "text-2xl" in response.text:
            print("✓ Contains: 'text-2xl' class")
        else:
            print("✗ Does NOT contain 'text-2xl' class")
        
        # Try to find what classes are used
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for any div with size-related classes
        large_divs = soup.find_all('div', class_=lambda x: x and ('xl' in str(x) or 'semibold' in str(x) or '2xl' in str(x)))
        if large_divs:
            print(f"\n✓ Found {len(large_divs)} divs with size/weight classes:")
            for div in large_divs[:5]:  # Show first 5
                print(f"  - {div.get('class')}: {div.text.strip()[:50]}")
        
        print(f"\n{'='*60}")
        print("Check captcha_page_debug.html for full HTML")
        print(f"{'='*60}")
    else:
        print("\n✗ No CAPTCHA detected")
        print("Try making a few more travel actions to trigger one")
else:
    print("✗ Login failed")

print("\nPress Enter to exit...")
input()
