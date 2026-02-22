#!/usr/bin/env python3
"""
Debug script to test the travel API call directly
"""

from simplemmo_bot import SimpleMMOBot

print("=" * 60)
print("Debug: Travel API Test")
print("=" * 60)

bot = SimpleMMOBot()

if bot.login():
    print("\n✓ Login successful")
    print(f"  Logged in: {bot.logged_in}")
    print(f"  CSRF Token: {bot.csrf_token[:20]}...")
    print(f"  API Token: {bot.api_token[:20] if bot.api_token else 'None'}...")
    
    print("\n[Calling travel()...]")
    result = bot.travel()
    
    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Error: {result.get('error')}")
    print(f"  Data: {result.get('data', 'N/A')}")
else:
    print("\n✗ Login failed")
