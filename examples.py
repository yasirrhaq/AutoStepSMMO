#!/usr/bin/env python3
"""
Example usage scripts for SimpleMMO Bot
"""

from simplemmo_bot import SimpleMMOBot
import time


def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===\n")
    
    # Initialize bot with config file
    bot = SimpleMMOBot("config.json")
    
    # Login using credentials from config
    if bot.login():
        print("✓ Logged in successfully\n")
        
        # Perform single travel
        print("Performing single travel...")
        result = bot.travel()
        print(f"Result: {result}\n")
        
        time.sleep(2)
        
        # Perform another travel
        print("Performing another travel...")
        result = bot.travel()
        print(f"Result: {result}\n")
    else:
        print("✗ Login failed - check config.json")


def example_auto_travel():
    """Auto travel example"""
    print("=== Auto Travel Example ===\n")
    
    bot = SimpleMMOBot("config.json")
    
    if bot.login():
        print("Starting auto-travel for 10 iterations...\n")
        bot.auto_travel_loop(iterations=10)
        print("\n✓ Auto-travel completed")
    else:
        print("✗ Login failed - check config.json")


def example_continuous_travel():
    """Continuous travel example"""
    print("=== Continuous Travel Example ===\n")
    
    bot = SimpleMMOBot("config.json")
    
    if bot.login():
        print("Starting continuous travel...")
        print("Press Ctrl+C to stop\n")
        try:
            bot.auto_travel_loop()  # Infinite loop
        except KeyboardInterrupt:
            print("\n✓ Travel stopped")
    else:
        print("✗ Login failed - check config.json")


def example_with_custom_config():
    """Example using email/password from config"""
    print("=== Auto Login Example ===\n")
    
    bot = SimpleMMOBot("config.json")
    
    if bot.login():
        print("✓ Logged in from config.json\n")
        
        # Run some travels
        print("Running 5 travel iterations...\n")
        bot.auto_travel_loop(iterations=5)
        print("\n✓ Completed")
    else:
        print("✗ Login failed - check config.json")


def example_custom_delays():
    """Example with custom configuration"""
    print("=== Custom Delays Example ===\n")
    
    # Create custom config
    custom_config = {
        "base_url": "https://web.simple-mmo.com",
        "email": "your_email@example.com",
        "password": "yourpassword",
        "travel_delay_min": 1,
        "travel_delay_max": 3,
        "enable_random_delays": True
    }
    
    # Save custom config
    import json
    with open("custom_config.json", "w") as f:
        json.dump(custom_config, f, indent=2)
    
    # Use custom config
    bot = SimpleMMOBot("custom_config.json")
    
    if bot.login():
        print("✓ Using custom delay settings (1-3 seconds)\n")
        bot.auto_travel_loop(iterations=5)
    else:
        print("✗ Login failed - check custom_config.json")


def example_scheduled_travel():
    """Example of scheduled travel"""
    print("=== Scheduled Travel Example ===\n")
    
    bot = SimpleMMOBot("config.json")
    
    if bot.login():
        print("Running scheduled travel:")
        print("- 10 travels")
        print("- Wait 60 seconds")
        print("- Repeat\n")
        
        try:
            while True:
                # Travel phase
                print("=== Starting Travel Batch ===")
                bot.auto_travel_loop(iterations=10)
                
                print("\n⏸ Waiting 60 seconds before next batch...\n")
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n✓ Scheduled travel stopped")
    else:
        print("✗ Login failed - check config.json")


if __name__ == "__main__":
    print("SimpleMMO Bot - Usage Examples\n")
    print("Choose an example to run:")
    print("1. Basic Usage (2 travels)")
    print("2. Auto Travel (10 iterations)")
    print("3. Continuous Travel (infinite)")
    print("4. Auto Login Example")
    print("5. Custom Delays")
    print("6. Scheduled Travel")
    
    choice = input("\nSelect example (1-6): ").strip()
    print()
    
    examples = {
        "1": example_basic_usage,
        "2": example_auto_travel,
        "3": example_continuous_travel,
        "4": example_with_custom_config,
        "5": example_custom_delays,
        "6": example_scheduled_travel
    }
    
    if choice in examples:
        examples[choice]()
    else:
        print("Invalid choice")
