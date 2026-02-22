#!/usr/bin/env python3
"""
Quick test script to verify bot functionality
"""

from simplemmo_bot import SimpleMMOBot
import sys

def test_login():
    """Test login functionality"""
    print("=" * 60)
    print("SimpleMMO Bot - Login Test")
    print("=" * 60)
    
    bot = SimpleMMOBot()
    
    print("\n[Testing login...]")
    if bot.login():
        print("✓ Login successful!")
        print(f"✓ CSRF Token obtained: {bot.csrf_token[:20]}..." if bot.csrf_token else "✗ No CSRF token")
        
        # Test single travel
        print("\n[Testing single travel action...]")
        result = bot.travel()
        
        if result.get("success"):
            print("✓ Travel action successful!")
            print(f"Response data: {result.get('data')}")
        else:
            print(f"✗ Travel action failed: {result.get('error')}")
        
        return True
    else:
        print("✗ Login failed - check config.json")
        return False

def test_auto_travel():
    """Test auto-travel with 3 iterations"""
    print("=" * 60)
    print("SimpleMMO Bot - Auto Travel Test (3 steps)")
    print("=" * 60)
    
    bot = SimpleMMOBot()
    
    print("\n[Logging in...]")
    if bot.login():
        print("✓ Login successful!")
        print("\n[Running 3 travel iterations...]")
        bot.auto_travel_loop(iterations=3)
        print("\n✓ Test completed")
    else:
        print("✗ Login failed - check config.json")

if __name__ == "__main__":
    print("Select test:")
    print("1. Login + Single Travel")
    print("2. Auto Travel (3 iterations)")
    
    choice = input("\nChoice (1-2): ").strip()
    
    if choice == "1":
        test_login()
    elif choice == "2":
        test_auto_travel()
    else:
        print("Invalid choice")
        sys.exit(1)
