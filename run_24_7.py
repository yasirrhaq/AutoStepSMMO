#!/usr/bin/env python3
"""
SimpleMMO 24/7 AFK Mode
Runs the bot continuously with best practices for unattended operation
"""

import time
import random
from datetime import datetime, timedelta
from simplemmo_bot import SimpleMMOBot
import logging

class AFK24x7Bot:
    """Wrapper for 24/7 continuous operation with best practices"""
    
    def __init__(self):
        self.bot = None
        self.stats = {
            'travels_completed': 0,
            'captchas_solved': 0,
            'errors': 0,
            'restarts': 0,
            'start_time': datetime.now(),
            'total_exp': 0,
            'total_gold': 0,
            'total_items': 0
        }
        
        # Uptime segment tracking (every 10 travels)
        self.uptime_segments = []  # List of completed segment durations in seconds
        self.current_segment_number = 1
        self.segment_start_time = datetime.now()
        
        # Best practice settings
        self.travels_before_break = random.randint(50, 100)  # Random break every 50-100 travels
        self.break_duration_min = 5  # 5-10 minute breaks
        self.break_duration_max = 10
        
        # Session refresh interval (every 2-4 hours)
        self.session_refresh_hours = random.uniform(2, 4)
        self.last_session_refresh = datetime.now()
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('afk_24x7.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def print_stats(self):
        """Print current session statistics"""
        # Calculate current segment uptime
        current_segment_uptime = (datetime.now() - self.segment_start_time).total_seconds()
        current_segment_minutes = int(current_segment_uptime / 60)
        
        # Calculate total uptime (all completed segments + current segment)
        total_uptime_seconds = sum(self.uptime_segments) + current_segment_uptime
        total_uptime_minutes = int(total_uptime_seconds / 60)
        
        # Format total uptime as hours/minutes if > 60 minutes
        if total_uptime_minutes >= 60:
            total_hours = total_uptime_minutes // 60
            total_mins = total_uptime_minutes % 60
            total_uptime_str = f"{total_hours} h {total_mins}m"
        else:
            total_uptime_str = f"{total_uptime_minutes}m"
        
        print(f"\n{'='*60}")
        print(f"📊 24/7 AFK MODE - SESSION STATS")
        print(f"{'='*60}")
        print(f"⏱️  Uptime #{self.current_segment_number}: {current_segment_minutes}m")
        print(f"⏱️  Total Uptime: {total_uptime_str}")
        print(f"✅ Travels: {self.stats['travels_completed']}")
        print(f"💫 Total EXP: {self.stats['total_exp']:,}")
        print(f"💰 Total Gold: {self.stats['total_gold']:,}")
        print(f"🎁 Total Items: {self.stats['total_items']}")
        print(f"🤖 CAPTCHAs Solved: {self.stats['captchas_solved']}")
        print(f"⚠️  Errors Recovered: {self.stats['errors']}")
        print(f"🔄 Bot Restarts: {self.stats['restarts']}")
        
        # Calculate rates using total uptime in hours
        total_uptime_hours = total_uptime_seconds / 3600
        if total_uptime_hours > 0:
            travels_per_hour = self.stats['travels_completed'] / total_uptime_hours
            exp_per_hour = self.stats['total_exp'] / total_uptime_hours
            gold_per_hour = self.stats['total_gold'] / total_uptime_hours
            print(f"📈 Rate: {travels_per_hour:.1f} travels/hour")
            print(f"📈 Rate: {exp_per_hour:.0f} EXP/hour, {gold_per_hour:.0f} gold/hour")
        
        print(f"{'='*60}\n")
    
    def take_break(self):
        """Take a human-like break"""
        duration = random.randint(
            self.break_duration_min * 60,
            self.break_duration_max * 60
        )
        
        print(f"\n{'='*60}")
        print(f"☕ TAKING A BREAK")
        print(f"{'='*60}")
        print(f"Completed {self.stats['travels_completed']} travels")
        print(f"Taking a {duration // 60} minute break to look more human-like...")
        print(f"Bot will resume automatically\n")
        
        self.logger.info(f"Taking {duration // 60}m break after {self.stats['travels_completed']} travels")
        
        # Countdown for the break
        for remaining in range(duration, 0, -30):
            mins, secs = divmod(remaining, 60)
            print(f"\rBreak time remaining: {mins:02d}:{secs:02d}  ", end='', flush=True)
            time.sleep(min(30, remaining))
        
        print("\r" + " " * 50 + "\r", end='', flush=True)
        print("✓ Break over, resuming travels...\n")
        
        # Reset counter for next break
        self.travels_before_break = random.randint(50, 100)
    
    def refresh_session(self):
        """Refresh session periodically to prevent expiration"""
        time_since_refresh = datetime.now() - self.last_session_refresh
        
        if time_since_refresh.total_seconds() / 3600 >= self.session_refresh_hours:
            print("\n🔄 Refreshing session (preventive maintenance)...")
            self.logger.info("Refreshing session to prevent expiration")
            
            try:
                # Re-login to get fresh session
                if self.bot.login():
                    print("✓ Session refreshed successfully")
                    self.last_session_refresh = datetime.now()
                    self.session_refresh_hours = random.uniform(2, 4)
                else:
                    print("⚠️  Session refresh failed, but continuing with existing session")
            except Exception as e:
                self.logger.warning(f"Session refresh error: {e}")
                print("⚠️  Session refresh error, continuing...")
    
    def run_forever(self):
        """Main 24/7 loop with error recovery"""
        print("="*60)
        print("🌙 SimpleMMO 24/7 AFK MODE")
        print("="*60)
        print("Bot will run continuously with best practices:")
        print("  ✓ Random breaks every 50-100 travels (5-10 mins)")
        print("  ✓ Session refresh every 2-4 hours")
        print("  ✓ Automatic error recovery")
        print("  ✓ CAPTCHA auto-solve enabled")
        print("  ✓ 15-20 second delays between travels")
        print("\nPress Ctrl+C to stop gracefully")
        print("="*60 + "\n")
        
        consecutive_errors = 0
        
        while True:
            try:
                # Initialize or reinitialize bot
                if self.bot is None or consecutive_errors >= 3:
                    if consecutive_errors >= 3:
                        print(f"\n⚠️  Too many consecutive errors ({consecutive_errors})")
                        print("Reinitializing bot from scratch...")
                        self.stats['restarts'] += 1
                    
                    self.bot = SimpleMMOBot()
                    
                    print("\n[Logging in...]")
                    if not self.bot.login():
                        print("✗ Login failed. Retrying in 60 seconds...")
                        time.sleep(60)
                        continue
                    
                    print("✓ Login successful!")
                    consecutive_errors = 0
                
                # Refresh session periodically
                self.refresh_session()
                
                # Perform a single travel
                result = self.bot.travel()
                
                if result.get("success"):
                    self.stats['travels_completed'] += 1
                    consecutive_errors = 0  # Reset error counter on success
                    
                    # Check if we completed a 10-travel segment
                    if self.stats['travels_completed'] % 10 == 0:
                        # Save current segment duration
                        segment_duration = (datetime.now() - self.segment_start_time).total_seconds()
                        self.uptime_segments.append(segment_duration)
                        # Start new segment
                        self.current_segment_number += 1
                        self.segment_start_time = datetime.now()
                    
                    parsed = result.get("parsed", {})
                    
                    # Check for CAPTCHA
                    if parsed.get("captcha"):
                        print(f"\n{'='*60}")
                        print("🤖 CAPTCHA DETECTED - Auto-solving...")
                        print(f"{'='*60}\n")
                        
                        if self.bot._solve_captcha():
                            print("✓ CAPTCHA solved! Continuing...\n")
                            self.stats['captchas_solved'] += 1
                            continue
                        else:
                            print("✗ CAPTCHA auto-solve reported failure")
                            print("Note: AI might have selected wrong answer.")
                            print("- Wrong attempts saved to captcha_learning/ for improvement")
                            print("- Bot will automatically retry if question changes")
                            print("- Checking verification status on next travel...")
                            print("Waiting 1 minute before continuing...\n")
                            # Shorter wait - might be solved or question may change
                            for i in range(60, 0, -5):
                                mins, secs = divmod(i, 60)
                                print(f"\rCooldown: {mins:02d}:{secs:02d}  ", end='', flush=True)
                                time.sleep(5)
                            print("\r" + " "*50 + "\r", end='', flush=True)
                        
                        continue
                    
                    # Check if NPC battle occurred before travel
                    npc_battle_data = result.get("npc_battle")
                    if npc_battle_data:
                        print(f"\n{'='*60}")
                        print(f"⚔️  NPC BATTLE COMPLETED")
                        print(f"{'='*60}")
                        
                        # Track battle rewards
                        if isinstance(npc_battle_data, dict):
                            battle_exp = npc_battle_data.get("exp", npc_battle_data.get("experience", 0))
                            battle_gold = npc_battle_data.get("gold", npc_battle_data.get("coins", 0))
                            battle_msg = npc_battle_data.get("message", "")
                            battle_attacks = npc_battle_data.get("attacks", 0)
                            battle_damage = npc_battle_data.get("damage", 0)
                            
                            if battle_msg:
                                print(f"  💬 {battle_msg}")
                            if battle_attacks > 0:
                                print(f"  ⚔️  Attacks: {battle_attacks}")
                            if battle_damage > 0:
                                print(f"  💥 Total Damage: {battle_damage}")
                            
                            # Add to cumulative stats
                            if battle_exp > 0:
                                self.stats['total_exp'] += battle_exp
                                print(f"  💫 Battle EXP: +{battle_exp} (Total: {self.stats['total_exp']:,})")
                            if battle_gold > 0:
                                self.stats['total_gold'] += battle_gold
                                print(f"  💰 Battle Gold: +{battle_gold} (Total: {self.stats['total_gold']:,})")
                        
                        print(f"  ✅ Continuing with travel...\n")
                        print(f"{'='*60}\n")
                    
                    # Display detailed results for EVERY travel
                    print(f"\n{'='*60}")
                    print(f"✓ Travel #{self.stats['travels_completed']} completed")
                    
                    if parsed:
                        # Track cumulative stats
                        exp_gained = parsed.get("exp", 0)
                        gold_gained = parsed.get("gold", 0)
                        items_gained = len(parsed.get("items", []))
                        
                        self.stats['total_exp'] += exp_gained
                        self.stats['total_gold'] += gold_gained
                        self.stats['total_items'] += items_gained
                        
                        # Show message if it's clean (not HTML)
                        msg = parsed.get("message", "")
                        if msg and "<" not in msg:  # Not HTML
                            # Truncate very long messages
                            if len(msg) > 150:
                                msg = msg[:150] + "..."
                            print(f"  💬 {msg}")
                        
                        # Show rewards
                        has_rewards = False
                        
                        current_exp = parsed.get("current_exp", 0)
                        current_gold = parsed.get("current_gold", 0)
                        
                        if exp_gained > 0:
                            if current_exp > 0:
                                print(f"  💫 EXP: +{exp_gained} (Session: {self.stats['total_exp']:,} | Current: {current_exp:,})")
                            else:
                                print(f"  💫 EXP: +{exp_gained} (Session Total: {self.stats['total_exp']:,})")
                            has_rewards = True
                        
                        if gold_gained > 0:
                            if current_gold > 0:
                                print(f"  💰 Gold: +{gold_gained} (Session: {self.stats['total_gold']:,} | Current: {current_gold:,})")
                            else:
                                print(f"  💰 Gold: +{gold_gained} (Session Total: {self.stats['total_gold']:,})")
                            has_rewards = True
                        
                        items = parsed.get("items", [])
                        if items:
                            print(f"  🎁 Items found:")
                            for item in items[:5]:  # Limit to first 5 items
                                if isinstance(item, dict):
                                    item_name = item.get("name", item.get("item", "Unknown"))
                                    item_qty = item.get("quantity", item.get("qty", 1))
                                    rarity = item.get("rarity", "")
                                    if rarity:
                                        print(f"     - {item_name} x{item_qty} ({rarity})")
                                    else:
                                        print(f"     - {item_name} x{item_qty}")
                                else:
                                    print(f"     - {item}")
                            if len(items) > 5:
                                print(f"     ... and {len(items) - 5} more items")
                            has_rewards = True
                        
                        # Show step count if available
                        if parsed.get("step_count", 0) > 0:
                            print(f"  👣 Steps: {parsed['step_count']}")
                        
                        # Show wait time if there's a cooldown
                        if parsed.get("wait_time", 0) > 0:
                            wait_sec = parsed['wait_time']
                            print(f"  ⏱️  Cooldown: {wait_sec:.1f}s")
                        
                        # If no rewards, show that it was a simple step
                        if not has_rewards:
                            print(f"  ➡️  Moved forward (no rewards this step)")
                    
                    print(f"{'='*60}")
                    
                    # Display full stats every 10 travels
                    if self.stats['travels_completed'] % 10 == 0:
                        self.print_stats()
                    
                    # Take random breaks to look human
                    if self.stats['travels_completed'] % self.travels_before_break == 0:
                        self.take_break()
                    
                    # Random delay between travels (already handled by bot)
                    delay = random.uniform(
                        self.bot.config.get("travel_delay_min", 15),
                        self.bot.config.get("travel_delay_max", 20)
                    )
                    
                    # Real-time countdown (like simplemmo_bot)
                    total_seconds = int(delay)
                    for remaining in range(total_seconds, 0, -1):
                        mins, secs = divmod(remaining, 60)
                        timer = f"{mins:02d}:{secs:02d}" if mins > 0 else f"{secs}s"
                        print(f"\rNext travel in: {timer}  ", end='', flush=True)
                        time.sleep(1)
                    
                    # Handle remaining fractional seconds
                    fractional = delay - total_seconds
                    if fractional > 0:
                        time.sleep(fractional)
                    
                    print("\r" + " " * 30 + "\r", end='', flush=True)  # Clear the line
                
                else:
                    # Handle errors
                    error = result.get("error", "Unknown")
                    consecutive_errors += 1
                    self.stats['errors'] += 1
                    
                    print(f"\n⚠️  Travel error: {error}")
                    self.logger.warning(f"Travel error: {error}")
                    
                    if "session" in error.lower() or "403" in error:
                        print("Session expired, re-logging in...")
                        self.bot.logged_in = False
                        self.bot = None  # Force reinitialization
                        time.sleep(5)
                    elif "rate" in error.lower() or "cooldown" in error.lower():
                        print("Rate limited, waiting 60 seconds...")
                        time.sleep(60)
                    else:
                        wait_time = min(60 * consecutive_errors, 300)  # Max 5 minutes
                        print(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print("\n\n" + "="*60)
                print("🛑 STOPPING BOT (User requested)")
                print("="*60)
                self.print_stats()
                print("Bot stopped gracefully. Goodbye!")
                break
            
            except Exception as e:
                consecutive_errors += 1
                self.stats['errors'] += 1
                
                print(f"\n❌ Unexpected error: {e}")
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
                
                if consecutive_errors >= 5:
                    print("Too many consecutive errors. Waiting 5 minutes...")
                    time.sleep(300)
                    consecutive_errors = 0
                else:
                    print(f"Waiting 30 seconds before retry... (error #{consecutive_errors})")
                    time.sleep(30)


def main():
    afk_bot = AFK24x7Bot()
    afk_bot.run_forever()


if __name__ == "__main__":
    main()
