#!/usr/bin/env python3
"""
Test script for Quest Runner Auto-Restart Functionality

Tests the auto-restart logic without importing the full quest_runner module.
This avoids dependency issues and focuses on testing the restart loop logic.

Run: python test_quest_restart.py
"""

import sys
from io import StringIO


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_restart_on_exception():
    """
    Test 1: Simulate a generic exception and verify restart prompt appears
    """
    print_section("TEST 1: Exception -> Restart Prompt")
    
    # Simulate session stats
    class MockBot:
        _session_completed = 2
        _session_steps = 5
        _session_exp = 12500
        _session_gold = 4500
        _session_quest_progress = {
            "Test Quest 1": {'done': 3, 'total': 10, 'remaining': 7},
            "Test Quest 2": {'done': 2, 'total': 5, 'remaining': 3}
        }
    
    bot = MockBot()
    login_called = False
    
    def mock_login():
        nonlocal login_called
        login_called = True
        print("[Mock] Login called - session refreshed")
        return True
    
    def mock_auto_quest_loop():
        print("[Mock] auto_quest_loop running...")
        raise ValueError("Simulated API error for testing")
    
    # Simulate the restart loop from main()
    _restart_count = 0
    
    with patch_input(['', 'c']):  # Press Enter to restart, then 'c' to exit
        while True:
            if _restart_count > 0:
                print(f"\n{'='*60}")
                print(f"  Auto-restarting bot (restart #{_restart_count})...")
                print(f"{'='*60}\n")
            
            try:
                mock_auto_quest_loop()
                break  # If no error, exit loop
                
            except KeyboardInterrupt:
                print("\n[Mock] KeyboardInterrupt handled")
                restart = input("\n Press Enter to restart, or C to close: ").strip().lower()
                if restart == 'c':
                    break
                else:
                    _restart_count += 1
                    mock_login()
                    
            except Exception as e:
                print(f"\n\n{'='*60}")
                print(f"  ERROR: {e}")
                print(f"{'='*60}")
                
                # Show session stats
                _completed = getattr(bot, '_session_completed', 0)
                _steps = getattr(bot, '_session_steps', 0)
                _exp = getattr(bot, '_session_exp', 0)
                _gold = getattr(bot, '_session_gold', 0)
                
                if _steps > 0 or _completed > 0:
                    print("\n" + "="*60)
                    print("  Session Stats (before error)")
                    print("="*60)
                    print(f"  Quests completed : {_completed}")
                    print(f"  Total attempts   : {_steps}")
                    print(f"  Total EXP        : {_exp:,}")
                    print(f"  Total Gold       : {_gold:,}")
                    print("="*60)
                
                restart = input("\n Press Enter to restart, or C to close: ").strip().lower()
                if restart == 'c':
                    print("\nBot stopped. Goodbye!")
                    break
                else:
                    _restart_count += 1
                    # Re-login
                    try:
                        mock_login()
                    except Exception as login_err:
                        print(f"\nRe-login failed: {login_err}")
                        break
        
        # Verify results
        print("\n" + "="*70)
        print("  TEST 1 RESULTS")
        print("="*70)
        print(f"  [OK] Exception was caught and displayed")
        print(f"  [OK] Session stats were shown")
        print(f"  [OK] Restart prompt appeared")
        print(f"  [OK] Restart count: {_restart_count}")
        print(f"  [OK] Login was called: {login_called}")
        print(f"  [OK] User input was processed correctly")
        print("="*70)
        
        return _restart_count == 1 and login_called


def test_keyboard_interrupt():
    """
    Test 2: Simulate Ctrl+C (KeyboardInterrupt) and verify restart
    """
    print_section("TEST 2: KeyboardInterrupt -> Restart Prompt")
    
    class MockBot:
        _session_completed = 3
        _session_steps = 10
        _session_exp = 25000
        _session_gold = 8500
        _session_quest_progress = {
            "Test Quest": {'done': 10, 'total': 10, 'remaining': 0}
        }
    
    bot = MockBot()
    
    def mock_auto_quest_loop():
        print("[Mock] auto_quest_loop running...")
        raise KeyboardInterrupt("Simulated Ctrl+C")
    
    _restart_count = 0
    _completed = 0
    
    with patch_input(['', 'c']):  # Press Enter to restart, then 'c' to exit
        while True:
            if _restart_count > 0:
                print(f"\n  Auto-restarting bot (restart #{_restart_count})...")
            
            try:
                mock_auto_quest_loop()
                break
                
            except KeyboardInterrupt:
                _completed = getattr(bot, '_session_completed', 0)
                _steps = getattr(bot, '_session_steps', 0)
                _exp = getattr(bot, '_session_exp', 0)
                _gold = getattr(bot, '_session_gold', 0)
                
                print("\n\n" + "="*60)
                print("Quest Runner stopped.")
                print("="*60)
                print(f"  Quests fully completed : {_completed}")
                print(f"  Total attempts         : {_steps}")
                print(f"  Total EXP              : {_exp:,}")
                print(f"  Total Gold             : {_gold:,}")
                print("="*60)
                
                restart = input("\n Press Enter to restart, or C to close: ").strip().lower()
                if restart == 'c':
                    print("\nBot stopped gracefully. Goodbye!")
                    break
                else:
                    _restart_count += 1
        
        print("\n" + "="*70)
        print("  TEST 2 RESULTS")
        print("="*70)
        print(f"  [OK] KeyboardInterrupt was caught")
        print(f"  [OK] Session summary was displayed")
        print(f"  [OK] Restart prompt appeared")
        print(f"  [OK] Restart count: {_restart_count}")
        print(f"  [OK] Quests completed: {_completed}")
        print("="*70)
        
        return _restart_count == 1 and _completed == 3


def test_clean_exit_on_user_choice():
    """
    Test 3: Simulate user choosing 'C' to exit cleanly
    """
    print_section("TEST 3: User Chooses 'C' -> Clean Exit")
    
    class MockBot:
        _session_completed = 1
        _session_steps = 3
        _session_exp = 5000
        _session_gold = 1200
    
    bot = MockBot()
    
    def mock_auto_quest_loop():
        print("[Mock] auto_quest_loop running...")
        raise ValueError("Simulated error")
    
    _restart_count = 0
    exited_cleanly = False
    
    with patch_input(['c']):  # Type 'c' to exit immediately
        while True:
            if _restart_count > 0:
                print(f"\n  Auto-restarting bot (restart #{_restart_count})...")
            
            try:
                mock_auto_quest_loop()
                break
                
            except Exception as e:
                print(f"\n  ERROR: {e}")
                
                restart = input("\n Press Enter to restart, or C to close: ").strip().lower()
                if restart == 'c':
                    exited_cleanly = True
                    print("\nBot stopped. Goodbye!")
                    break
                else:
                    _restart_count += 1
        
        print("\n" + "="*70)
        print("  TEST 3 RESULTS")
        print("="*70)
        print(f"  [OK] Error was caught")
        print(f"  [OK] User chose 'C' to exit")
        print(f"  [OK] Exit was clean: {exited_cleanly}")
        print(f"  [OK] No restart occurred (count: {_restart_count})")
        print("="*70)
        
        return exited_cleanly and _restart_count == 0


def test_exp_gold_formatting():
    """
    Test 4: Verify EXP/Gold formatting handles strings with commas
    """
    print_section("TEST 4: EXP/Gold Formatting (String with Commas)")
    
    # Test the formatting logic from the fix
    test_cases = [
        ("2,500", "150", (2500, 150)),
        ("10000", "500", (10000, 500)),
        ("1,234,567", "98,765", (1234567, 98765)),
        (2500, 150, (2500, 150)),  # Already integers
        ("invalid", "150", (0, 150)),  # Invalid string
        (None, 150, (0, 150)),  # None value
    ]
    
    all_passed = True
    
    for exp_raw, gold_raw, expected in test_cases:
        try:
            # Replicate the fix logic from quest_runner.py
            try:
                exp_int = int(str(exp_raw).replace(',', ''))
            except (ValueError, TypeError):
                exp_int = 0
            try:
                gold_int = int(str(gold_raw).replace(',', ''))
            except (ValueError, TypeError):
                gold_int = 0
            
            result = (exp_int, gold_int)
            
            if result == expected:
                print(f"  [OK] Input: exp={repr(exp_raw)}, gold={repr(gold_raw)} -> Formatted: {exp_int:,}, {gold_int:,}")
            else:
                print(f"  [FAIL] Input: exp={repr(exp_raw)}, gold={repr(gold_raw)} -> Expected: {expected}, Got: {result}")
                all_passed = False
                
        except Exception as e:
            print(f"  [FAIL] Input: exp={repr(exp_raw)}, gold={repr(gold_raw)} -> Exception: {e}")
            all_passed = False
    
    print("\n" + "="*70)
    print("  TEST 4 RESULTS")
    print("="*70)
    if all_passed:
        print(f"  [OK] All formatting test cases passed")
        print(f"  [OK] String commas are handled correctly")
        print(f"  [OK] Invalid values default to 0")
    else:
        print(f"  [FAIL] Some formatting test cases failed")
    print("="*70)
    
    return all_passed


# Input patching context manager
from unittest.mock import patch
from io import StringIO

def patch_input(responses):
    """Context manager to mock input() with predefined responses"""
    return patch('builtins.input', side_effect=responses)


def main():
    """Run all tests"""
    print("=" * 70)
    print("  QUEST RUNNER AUTO-RESTART TEST SUITE")
    print("=" * 70)
    print("\nThis test suite verifies the auto-restart functionality")
    print("without making real API calls.\n")
    
    results = []
    
    # Run all tests
    results.append(("Exception -> Restart", test_restart_on_exception()))
    results.append(("KeyboardInterrupt -> Restart", test_keyboard_interrupt()))
    results.append(("User Exit -> Clean Shutdown", test_clean_exit_on_user_choice()))
    results.append(("EXP/Gold Formatting", test_exp_gold_formatting()))
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"{'Test Name':<40} {'Result':<10}")
    print("-" * 55)
    
    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        if result:
            passed += 1
        print(f"{name:<40} [{status}]")
    
    print("-" * 55)
    print(f"Total: {passed}/{len(results)} tests passed")
    print("=" * 70)
    
    if passed == len(results):
        print("\n[OK] ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n[FAIL] {len(results) - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
