#!/usr/bin/env python3
"""Direct test of travel GET request"""

import sys
import importlib.util

# Force reload the module
if 'simplemmo_bot' in sys.modules:
    del sys.modules['simplemmo_bot']

# Load fresh
spec = importlib.util.spec_from_file_location("simplemmo_bot", "simplemmo_bot.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SimpleMMOBot = module.SimpleMMOBot

print("Testing travel with fresh module import...")
bot = SimpleMMOBot()

if bot.login():
    print("✓ Logged in")
    print("\nAttempting single travel...")
    result = bot.travel()
    print(f"Result: {result}")
else:
    print("✗ Login failed")
