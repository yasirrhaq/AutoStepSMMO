#!/usr/bin/env python3
"""
Verify CAPTCHA dependencies are installed
"""

import sys

print("=" * 60)
print("Checking CAPTCHA Dependencies")
print("=" * 60)
print()

# Check Python version
print(f"Python version: {sys.version}")
print()

# Check Pillow
try:
    from PIL import Image
    import PIL
    print(f"✓ Pillow (PIL) version {PIL.__version__}")
except ImportError as e:
    print(f"✗ Pillow NOT installed")
    print(f"  Error: {e}")
    print(f"  Install with: pip install Pillow")

# Check pytesseract
try:
    import pytesseract
    print(f"✓ pytesseract installed")
    
    # Try to check Tesseract binary
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR version {version}")
    except Exception as e:
        print(f"⚠ pytesseract is installed but Tesseract binary not found")
        print(f"  Error: {e}")
        print(f"  Download from: https://github.com/UB-Mannheim/tesseract/wiki")
except ImportError as e:
    print(f"✗ pytesseract NOT installed")
    print(f"  Error: {e}")
    print(f"  Install with: pip install pytesseract")

print()
print("=" * 60)
print("Summary")
print("=" * 60)
print()

# Try importing in the bot
try:
    from simplemmo_bot import SimpleMMOBot
    bot = SimpleMMOBot()
    
    if bot.has_pil:
        print("✓ Bot can use PIL for image processing")
    else:
        print("✗ Bot cannot use PIL - install Pillow")
    
    print()
    print("Bot is ready to use CAPTCHA features!")
    
except Exception as e:
    print(f"⚠ Error loading bot: {e}")

print()
input("Press Enter to exit...")
