#!/usr/bin/env python3
"""
Quick installer for CAPTCHA solving dependencies
"""

import subprocess
import sys
import os

print("=" * 60)
print("CAPTCHA Solver - Dependency Installer")
print("=" * 60)
print()

def install_package(package):
    """Install a Python package using pip"""
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")
        return False

print("Step 1: Installing Python packages...")
print()

# Install Pillow
success_pillow = install_package("Pillow")
print()

# Install pytesseract
success_pytesseract = install_package("pytesseract")
print()

print("=" * 60)
print("Installation Summary")
print("=" * 60)
print()

if success_pillow:
    print("✓ Pillow (PIL) - Image processing")
else:
    print("✗ Pillow (PIL) - FAILED")

if success_pytesseract:
    print("✓ pytesseract - Python OCR wrapper")
else:
    print("✗ pytesseract - FAILED")

print()
print("=" * 60)
print("Step 2: Tesseract OCR Binary")
print("=" * 60)
print()

if os.name == 'nt':  # Windows
    print("⚠️  You still need to install Tesseract OCR binary:")
    print()
    print("1. Download from:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("2. Run the installer (tesseract-ocr-w64-setup-*.exe)")
    print()
    print("3. Install to default location:")
    print("   C:\\Program Files\\Tesseract-OCR\\")
    print()
    print("4. The installer should add it to PATH automatically")
    print()
else:  # Linux/Mac
    print("⚠️  You still need to install Tesseract OCR:")
    print()
    if sys.platform == 'darwin':  # Mac
        print("Mac:")
        print("  brew install tesseract")
    else:  # Linux
        print("Ubuntu/Debian:")
        print("  sudo apt-get install tesseract-ocr")
        print()
        print("Fedora:")
        print("  sudo dnf install tesseract")
    print()

print("=" * 60)
print("Next Steps")
print("=" * 60)
print()
print("1. Install Tesseract binary (see above)")
print("2. Restart your terminal/IDE")
print("3. Run: python test_captcha.py")
print("4. Enable in config.json:")
print('   "auto_solve_captcha": true')
print()
print("=" * 60)

input("\nPress Enter to exit...")
