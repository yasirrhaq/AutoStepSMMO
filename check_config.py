#!/usr/bin/env python3
"""
Simple diagnostic to check bot configuration
"""

import json

print("=" * 60)
print("SimpleMMO Bot - Configuration Diagnostic")
print("=" * 60)

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

print("\nConfiguration Status:")
print(f"  Session Token: {'✓ Present' if config.get('session_token') else '✗ Missing'}")
print(f"  XSRF Token: {'✓ Present' if config.get('xsrf_token') else '✗ Missing'}")
print(f"  API Token: {'✓ Present' if config.get('api_token') else '✗ Missing'}")

if config.get('api_token'):
    print(f"\n  API Token (first 20 chars): {config['api_token'][:20]}")
    print(f"  API Token length: {len(config['api_token'])}")

print("\n" + "=" * 60)
