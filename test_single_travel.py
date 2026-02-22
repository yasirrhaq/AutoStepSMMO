#!/usr/bin/env python3
"""
Test a single travel to see the API response structure
"""

from simplemmo_bot import SimpleMMOBot
import json

print("=" * 60)
print("SimpleMMO Bot - Single Travel Test")
print("=" * 60)

bot = SimpleMMOBot()

print("\n[Logging in...]")
if bot.login():
    print("✓ Login successful!\n")
    
    print("[Performing single travel...]")
    result = bot.travel()
    
    if result.get("success"):
        print("\n✓ Travel successful!\n")
        
        # Show raw API response
        print("Raw API Response:")
        print(json.dumps(result.get("data", {}), indent=2))
        
        # Show parsed results
        parsed = result.get("parsed", {})
        if parsed:
            print("\n" + "=" * 60)
            print("Parsed Results:")
            print(f"  EXP: {parsed.get('exp', 0)}")
            print(f"  Gold: {parsed.get('gold', 0)}")
            print(f"  Items: {parsed.get('items', [])}")
            print(f"  Message: {parsed.get('message', 'N/A')}")
            print("=" * 60)
    else:
        print(f"\n✗ Travel failed: {result.get('error')}")
else:
    print("✗ Login failed")

print("\nPress Enter to exit...")
input()
