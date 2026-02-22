#!/usr/bin/env python3
"""
Quick auto-test script - automatically runs 3 travel iterations
"""

from simplemmo_bot import SimpleMMOBot
import sys

print("=" * 60)
print("SimpleMMO Bot - Quick Auto Test (3 travels)")
print("=" * 60)

bot = SimpleMMOBot()

print("\n[Logging in from config.json...]")
if bot.login():
    print("✓ Login successful!")
    print(f"  Session: Active")
    print(f"  API Token: {'Configured' if bot.api_token else 'Missing'}\n")
    
    print("[Running 3 travel iterations...]\n")
    try:
        bot.auto_travel_loop(iterations=3)
        print("\n✓ Test completed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        sys.exit(0)
else:
    print("✗ Login failed")
    print("\nTroubleshooting:")
    print("1. Check your session_token in config.json")
    print("2. Make sure the token is fresh (not expired)")
    print("3. Check simplemmo_bot.log for detailed errors")

input("\nPress Enter to exit...")
