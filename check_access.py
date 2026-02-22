#!/usr/bin/env python3
"""
Quick script to check if you can access SimpleMMO
Helps diagnose 403 Forbidden errors
"""

import requests
import time

print("=" * 60)
print("SimpleMMO Access Checker")
print("=" * 60)

base_url = "https://web.simple-mmo.com"

print(f"\n[1/3] Testing access to home page...")
try:
    response = requests.get(base_url, timeout=10)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Home page accessible")
    elif response.status_code == 403:
        print("  ✗ 403 Forbidden - You are blocked!")
        print("\n  Possible causes:")
        print("    - IP address temporarily banned")
        print("    - Cloudflare bot protection")
        print("    - Rate limit exceeded")
    else:
        print(f"  ⚠ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print(f"\n[2/3] Testing access to login page...")
time.sleep(1)
try:
    response = requests.get(f"{base_url}/login", timeout=10)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Login page accessible")
    elif response.status_code == 403:
        print("  ✗ 403 Forbidden - Login blocked!")
        print("\n  This is why your bot can't login.")
    else:
        print(f"  ⚠ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print(f"\n[3/3] Testing with browser-like headers...")
time.sleep(1)
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    response = requests.get(f"{base_url}/login", headers=headers, timeout=10)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Working with browser headers")
    elif response.status_code == 403:
        print("  ✗ Still blocked (not a headers issue)")
    else:
        print(f"  ⚠ Status: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
print("Diagnosis Complete")
print("=" * 60)

print("\n📊 Results:")
print("  If all tests show 403: You are temporarily IP banned")
print("  If only login is 403: Account may be locked")
print("  If all tests pass: Bot configuration issue")

print("\n🔧 Solutions:")
print("  1. Wait 10-30 minutes and try again")
print("  2. Try accessing the site in your browser")
print("  3. Check if your IP is banned (try different network)")
print("  4. Use session token instead of email/password")
print("     (See SESSION_TOKEN_GUIDE.md)")
print("  5. Contact SimpleMMO support if issue persists")

input("\nPress Enter to exit...")
