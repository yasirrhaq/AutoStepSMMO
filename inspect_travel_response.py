#!/usr/bin/env python3
"""
Inspect what /travel returns to help find the real API endpoint
"""
from simplemmo_bot import SimpleMMOBot
import re

print("=" * 60)
print("Inspecting /travel response...")
print("=" * 60)

bot = SimpleMMOBot()

if bot.login():
    print("✓ Logged in\n")
    
    # Get the travel page
    response = bot.session.get(f"{bot.base_url}/travel")
    html = response.text
    
    # Look for Alpine.js function names
    alpine_functions = re.findall(r'x-on:click="([^"]+)"', html)
    if alpine_functions:
        print(f"Found {len(set(alpine_functions))} Alpine.js click handlers:")
        for func in set(alpine_functions):
            print(f"  - {func}")
    
    # Look for API endpoints in the HTML
    api_patterns = [
        r'["\']/(api/[^"\']+)["\']',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.[a-z]+\(["\']([^"\']+)["\']',
    ]
    
    print("\nSearching for API endpoints in HTML...")
    for pattern in api_patterns:
        matches = re.findall(pattern, html)
        if matches:
            print(f"Found {len(set(matches))} potential endpoints:")
            for match in set(matches):
                print(f"  - {match}")
    
    # Look for window.livewire or Alpine data
    if 'window.livewire' in html.lower():
        print("\n⚠ Page uses Livewire (Laravel framework)")
    if 'alpine.start()' in html.lower() or 'x-data' in html:
        print("⚠ Page uses Alpine.js for interactivity")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Open your browser and go to https://web.simple-mmo.com/travel")
    print("2. Press F12 → Network tab → Clear")
    print("3. Click 'Take a Step' button")
    print("4. Look for XHR/Fetch requests in Network tab")
    print("5. Share the URL, method, and payload of the request")
    print("=" * 60)
else:
    print("✗ Login failed")
