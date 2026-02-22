#!/usr/bin/env python3
"""Debug API call to see exactly what's being sent"""
import requests
import json
from urllib.parse import unquote

print("=" * 60)
print("DEBUG: API Authentication Test")
print("=" * 60)

# Load config
with open('config.json') as f:
    config = json.load(f)

# URL decode
session_token = unquote(config['session_token'])
xsrf_token = unquote(config['xsrf_token'])

print(f"\nSession token length: {len(session_token)}")
print(f"XSRF token length: {len(xsrf_token)}")

# Create session
s = requests.Session()

# Set cookies with dot prefix for all subdomains
print("\nSetting cookies for .simple-mmo.com...")
s.cookies.set('laravelsession', session_token, domain='.simple-mmo.com', path='/', secure=True)
s.cookies.set('XSRF-TOKEN', xsrf_token, domain='.simple-mmo.com', path='/', secure=True)

# Check what cookies are set
print(f"Total cookies in jar: {len(s.cookies)}")
for cookie in s.cookies:
    print(f"  - {cookie.name}: domain={cookie.domain}, secure={cookie.secure}")

# Prepare headers
headers = {
    'X-XSRF-TOKEN': xsrf_token,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'https://web.simple-mmo.com',
    'Referer': 'https://web.simple-mmo.com/travel',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("\nHeaders being sent:")
for k, v in headers.items():
    print(f"  - {k}: {v[:50]}..." if len(str(v)) > 50 else f"  - {k}: {v}")

# Make API call
print("\n" + "=" * 60)
print("Making API call...")
print("=" * 60)

try:
    response = s.post('https://api.simple-mmo.com/api/action/travel/4', headers=headers, json={})
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text[:300]}")
    
    if response.status_code == 200:
        print("\n✓ SUCCESS!")
    elif response.status_code == 401:
        print("\n✗ HTTP 401 - Authentication failed")
        print("\nPossible issues:")
        print("1. Cookies not being sent to api.simple-mmo.com")
        print("2. Session token expired")
        print("3. Missing required header")
    else:
        print(f"\n✗ HTTP {response.status_code}")
        
except Exception as e:
    print(f"\n✗ Error: {e}")

print("=" * 60)
