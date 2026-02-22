#!/usr/bin/env python3
"""
Manual CAPTCHA solver - opens browser to solve CAPTCHA manually
"""

import webbrowser
from simplemmo_bot import SimpleMMOBot

print("=" * 60)
print("Manual CAPTCHA Solver")
print("=" * 60)

bot = SimpleMMOBot()

print("\n[Logging in...]")
if bot.login():
    print("✓ Login successful\n")
    
    # Try a travel to see if CAPTCHA appears
    print("[Testing if CAPTCHA is active...]")
    result = bot.travel()
    
    if result.get("parsed", {}).get("captcha"):
        print("\n⚠️  CAPTCHA is active!")
        
        url = f"{bot.base_url}/i-am-not-a-bot"
        print(f"\nOpening CAPTCHA page in browser:")
        print(f"  {url}\n")
        
        print("Please complete the CAPTCHA verification manually.")
        print("Press Enter after you've completed it...")
        
        webbrowser.open(url)
        input()
        
        print("\n[Testing if CAPTCHA was solved...]")
        result2 = bot.travel()
        
        if not result2.get("parsed", {}).get("captcha"):
            print("✓ CAPTCHA solved! Bot can continue traveling")
        else:
            print("✗ CAPTCHA still active - try solving it again")
    else:
        print("\n✓ No CAPTCHA detected - bot can travel freely")
else:
    print("✗ Login failed")

print("\nPress Enter to exit...")
input()
