#!/usr/bin/env python3
"""Extract API token from travel page"""
from simplemmo_bot import SimpleMMOBot
import re

print("=" * 60)
print("Testing API token extraction")
print("=" * 60)

bot = SimpleMMOBot()

if bot.login():
    print("✓ Logged in\n")
    
    # Get the travel page
    response = bot.session.get(f"{bot.base_url}/travel")
    html = response.text
    
    print("Searching for api_token in page HTML...")
    print()
    
    # Search patterns
    patterns = [
        (r'api_token["\']?\s*[:=]\s*["\']([^"\']+)["\']', "api_token assignment"),
        (r'data-api-token["\']?\s*[:=]\s*["\']([^"\']+)["\']', "data attribute"),
        (r'window\.api_token\s*=\s*["\']([^"\']+)["\']', "window variable"),
        (r'"api_token"\s*:\s*"([^"]+)"', "JSON api_token"),
    ]
    
    for pattern, desc in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"✓ Found via {desc}:")
            for match in matches[:2]:  # Show first 2
                print(f"  - {match[:50]}... (length: {len(match)})")
    
    # Check if bot extracted it
    print(f"\nBot's api_token: {bot.api_token}")
    
    if bot.api_token:
        print("\n✓ API token successfully extracted!")
    else:
        print("\n✗ API token NOT found - need to search HTML manually")
        # Save HTML to file for manual inspection
        with open('travel_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved HTML to travel_page.html for manual inspection")
else:
    print("✗ Login failed")
