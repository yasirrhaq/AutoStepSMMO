#!/usr/bin/env python3
"""
Test CAPTCHA auto-solve functionality
WARNING: Use only on test accounts!
"""

from simplemmo_bot import SimpleMMOBot
import json

print("=" * 60)
print("SimpleMMO Bot - CAPTCHA Solver Test")
print("=" * 60)
print()
print("⚠️  WARNING: This test is for DEVELOPMENT ONLY")
print("   Only use on test accounts you own!")
print()
print("=" * 60)

# Check if OCR dependencies are available
try:
    from PIL import Image
    print("\u2713 Pillow (PIL) is installed")
except ImportError:
    print("\u2717 Pillow (PIL) NOT installed")
    print("   Install: pip install Pillow")

try:
    import pytesseract
    print("\u2713 pytesseract is installed")
    
    # Try to run tesseract
    try:
        pytesseract.get_tesseract_version()
        print("\u2713 Tesseract binary is accessible")
    except:
        print("\u2717 Tesseract binary NOT found")
        print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
except ImportError:
    print("\u2717 pytesseract NOT installed")
    print("   Install: pip install pytesseract")

print("=" * 60)
print()

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

if not config.get('auto_solve_captcha'):
    print("⚠️  auto_solve_captcha is DISABLED in config.json")
    print()
    response = input("Enable it for this test? (y/n): ")
    if response.lower() == 'y':
        config['auto_solve_captcha'] = True
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("\u2713 Enabled auto_solve_captcha")
    else:
        print("\nTest cancelled. To enable manually:")
        print('  Set "auto_solve_captcha": true in config.json')
        exit()

print()
print("=" * 60)
print("Starting CAPTCHA Test")
print("=" * 60)
print()

bot = SimpleMMOBot()

print("[Logging in...]")
if bot.login():
    print("\u2713 Login successful")
    print()
    
    # Fetch the CAPTCHA page directly
    print("[Fetching CAPTCHA page...]")
    response = bot.session.get(f"{bot.base_url}/i-am-not-a-bot")
    
    if response.status_code == 200:
        print("\u2713 CAPTCHA page loaded")
        print()
        
        # Check if there's actually a CAPTCHA
        if "Please press on the following item" in response.text:
            print("[Attempting to solve CAPTCHA...]")
            print()
            
            success = bot._solve_captcha(response.text)
            
            if success:
                print()
                print("=" * 60)
                print("\u2713 CAPTCHA SOLVED SUCCESSFULLY!")
                print("=" * 60)
            else:
                print()
                print("=" * 60)
                print("\u2717 CAPTCHA solving failed")
                print("=" * 60)
                print()
                print("Check captcha_images/ folder for saved images")
                print("This helps diagnose why OCR couldn't read them")
        else:
            print("No CAPTCHA currently active")
            print("(This might mean you recently solved one)")
            print()
            print("To trigger a CAPTCHA:")
            print("1. Make many rapid travel actions")
            print("2. Or wait for the game to show one naturally")
    else:
        print(f"\u2717 Failed to load CAPTCHA page (HTTP {response.status_code})")
else:
    print("\u2717 Login failed")

print()
input("Press Enter to exit...")
