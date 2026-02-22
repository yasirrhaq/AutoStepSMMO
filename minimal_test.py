#!/usr/bin/env python3
import requests
import json

# Load config
with open('config.json') as f:
    config = json.load(f)

# Create session
s = requests.Session()

# URL decode tokens
from urllib.parse import unquote
session_token = unquote(config['session_token'])
xsrf_token = unquote(config['xsrf_token'])

# Set cookies
s.cookies.set('laravelsession', session_token, domain='web.simple-mmo.com')
s.cookies.set('XSRF-TOKEN', xsrf_token, domain='web.simple-mmo.com')

# Set headers
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://web.simple-mmo.com/',
})

# Test GET request to /travel
print("Testing GET request to https://web.simple-mmo.com/travel...")
response = s.get('https://web.simple-mmo.com/travel')
print(f"Status: {response.status_code}")
print(f"URL after redirects: {response.url}")
print(f"Response preview: {response.text[:300]}")
