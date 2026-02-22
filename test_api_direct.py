#!/usr/bin/env python3
"""Direct API endpoint test"""
import requests
import json
from urllib.parse import unquote

# Load config
with open('config.json') as f:
    config = json.load(f)

# Create session
s = requests.Session()

# URL decode and set cookies
session_token = unquote(config['session_token'])
xsrf_token = unquote(config['xsrf_token'])

s.cookies.set('laravelsession', session_token, domain='api.simple-mmo.com')
s.cookies.set('XSRF-TOKEN', xsrf_token, domain='api.simple-mmo.com')
s.cookies.set('laravelsession', session_token, domain='.simple-mmo.com')
s.cookies.set('XSRF-TOKEN', xsrf_token, domain='.simple-mmo.com')

# Prepare headers
headers = {
    'X-CSRF-Token': xsrf_token,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'https://web.simple-mmo.com',
    'Referer': 'https://web.simple-mmo.com/travel',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Test API call
print("Testing: POST https://api.simple-mmo.com/api/action/travel/4")
print("=" * 60)

response = s.post('https://api.simple-mmo.com/api/action/travel/4', headers=headers, json={})

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
print("=" * 60)

if response.status_code == 200:
    print("✓ SUCCESS! Travel action triggered!")
    try:
        data = response.json()
        print(f"Response data: {json.dumps(data, indent=2)[:500]}")
    except:
        pass
else:
    print(f"✗ Failed with HTTP {response.status_code}")
