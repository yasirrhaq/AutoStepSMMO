#!/usr/bin/env python3
"""
SimpleMMO 24/7 AFK Mode
Runs the bot continuously with best practices for unattended operation
"""

import time
import random
import json
from datetime import datetime, timedelta
from simplemmo_bot import SimpleMMOBot
import logging


def load_config():
    """Load configuration from config.json for AFK bot settings"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return defaults if config not found or invalid
        return {
            "break_duration_min": 4,
            "break_duration_max": 12,
        }

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
            'total_items': 0,
            'npc_battles': 0,
            'materials_gathered': 0,
            'materials_log': {}  # {item_name: total_qty}
        }
        
        # Uptime segment tracking (every 10 travels)
        self.uptime_segments = []  # List of completed segment durations in seconds
        self.current_segment_number = 1
        self.segment_start_time = datetime.now()
        
        # Best practice settings - load config independently since bot isn't initialized yet
        config = load_config()
        self.travels_before_break = random.randint(100, 200)  # Random break every 100-200 travels (was 50-100)
        self.break_duration_min = config.get("break_duration_min", 4) # (was 5-10 minutes)
        self.break_duration_max = config.get("break_duration_max", 12)
        
        # Session refresh interval (every 2-4 hours)
        self.session_refresh_hours = random.uniform(2, 5)  # Randomize between 2-5 hours to avoid fixed patterns
        self.last_session_refresh = datetime.now()
        
        # Use UTF-8 console handler so emoji never raises UnicodeEncodeError
        # on Windows cp1252 terminals.
        import sys as _sys
        _utf8_console = open(1, 'w', encoding='utf-8', errors='replace', closefd=False)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('afk_24x7.log', encoding='utf-8'),
                logging.StreamHandler(stream=_utf8_console),
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def print_stats(self):
        """Print current session statistics"""
        # Calculate current segment uptime
        current_segment_uptime = (datetime.now() - self.segment_start_time).total_seconds()
        current_segment_minutes = int(current_segment_uptime / 60)
        current_segment_seconds = int(current_segment_uptime % 60)
        
        # Format current segment: show seconds if < 1 minute
        if current_segment_minutes == 0:
            current_segment_str = f"{current_segment_seconds}s"
        else:
            current_segment_str = f"{current_segment_minutes}m"
        
        # Calculate total uptime (all completed segments + current segment)
        total_uptime_seconds = sum(self.uptime_segments) + current_segment_uptime
        
        # Format total uptime with hours, minutes, seconds
        total_hours = int(total_uptime_seconds // 3600)
        total_mins = int((total_uptime_seconds % 3600) // 60)
        total_secs = int(total_uptime_seconds % 60)
        
        # Build total uptime string (only show hours if > 0)
        if total_hours > 0:
            total_uptime_str = f"{total_hours}h {total_mins}m {total_secs}s"
        else:
            total_uptime_str = f"{total_mins}m {total_secs}s"
        
        print(f"\n{'='*60}")
        print(f"📊 24/7 AFK MODE - SESSION STATS")
        print(f"{'='*60}")
        print(f"⏱️  Uptime #{self.current_segment_number}: {current_segment_str}")
        print(f"⏱️  Total Uptime: {total_uptime_str}")
        print(f"✅ Travels: {self.stats['travels_completed']}")
        print(f"💫 Total EXP: {self.stats['total_exp']:,}")
        print(f"💰 Total Gold: {self.stats['total_gold']:,}")
        print(f"🎁 Total Items: {self.stats['total_items']}")
        print(f"🤖 CAPTCHAs Solved: {self.stats['captchas_solved']}")
        print(f"⚔️  NPC Battles: {self.stats['npc_battles']}")
        print(f"🔨 Materials Gathered: {self.stats['materials_gathered']}x")
        if self.stats['materials_log']:
            for _mat_name, _mat_qty in sorted(self.stats['materials_log'].items()):
                print(f"   • {_mat_name}: x{_mat_qty}")
        print(f"⚠️  Errors Recovered: {self.stats['errors']}")
        print(f"🔄 Bot Restarts: {self.stats['restarts']}")
        
        # Show settings
        auto_battle_status = "✅ ON" if self.bot and self.bot.config.get("auto_battle_npcs", False) else "❌ OFF"
        print(f"⚔️  Auto-Battle NPCs: {auto_battle_status}")
        
        # Show auto-learning status every 10 travels
        if self.stats['travels_completed'] % 10 == 0:
            try:
                from auto_captcha_learner import AutoCaptchaLearner
                learner = AutoCaptchaLearner()
                status = learner.get_learning_status()
                
                if status['total_attempts'] > 0:
                    print(f"\n🤖 CAPTCHA Auto-Learning:")
                    print(f"   Total attempts: {status['total_attempts']} (✅ {status['successes']}, ❌ {status['failures']})")
                    print(f"   Auto-labeled: {status['auto_labeled']} | Trainings: {status['trainings']}")
                    if status['labels_until_next_training'] > 0:
                        print(f"   {status['labels_until_next_training']} more labels until next training")
                    else:
                        print(f"   🎯 Ready for training!")
            except Exception as e:
                self.logger.debug(f"Could not show auto-learning status: {e}")
        
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
        print("  ✓ Random breaks every 100-200 travels (4-12 mins)")
        print("  ✓ Session refresh every 2-4 hours")
        print("  ✓ Automatic error recovery")
        print("  ✓ CAPTCHA auto-solve enabled")
        print("  ✓ 15-20 second delays between travels")
        print("  ✓ Auto-learning from CAPTCHA attempts")
        print("\nPress Ctrl+C to stop gracefully")
        print("="*60 + "\n")
        
        # Show auto-learning status
        try:
            from auto_captcha_learner import AutoCaptchaLearner
            learner = AutoCaptchaLearner()
            learner.print_status()
        except Exception as e:
            self.logger.debug(f"Could not load auto-learning status: {e}")
        
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
                
                # ===================================================================
                # STEP 1: PRE-TRAVEL CHECKS (done automatically in bot.travel())
                # - Checks for materials on travel page BEFORE making API call
                # - Checks for NPC battles BEFORE making API call
                # - Auto-gathers/battles if configured
                # ===================================================================
                
                # Perform a single travel (includes pre-travel checks)
                result = self.bot.travel()
                
                if result.get("success"):
                    self.stats['travels_completed'] += 1
                    consecutive_errors = 0  # Reset error counter on success
                    
                    parsed = result.get("parsed", {})
                    
                    # Check for CAPTCHA
                    if parsed.get("captcha"):
                        print(f"\n{'='*60}")
                        print("🤖 CAPTCHA DETECTED - Auto-solving...")
                        print(f"{'='*60}\n")
                        
                        if self.bot._solve_captcha():
                            print("✓ CAPTCHA solved! Continuing...\n")
                            self.stats['captchas_solved'] += 1
                            
                            # Show auto-learning activity
                            try:
                                from auto_captcha_learner import AutoCaptchaLearner
                                learner = AutoCaptchaLearner()
                                status = learner.get_learning_status()
                                if status['auto_labeled'] > 0:
                                    print(f"🤖 Auto-learning: {status['auto_labeled']} past failures labeled, {status['trainings']} trainings completed\n")
                            except:
                                pass
                            
                            continue
                        else:
                            print("✗ CAPTCHA auto-solve reported failure")
                            print("Note: AI might have selected wrong answer.")
                            print("- Wrong attempts saved to captcha_learning/ for improvement")
                            print("- Bot will automatically retry if question changes")
                            print("- Checking verification status on next travel...")
                            print("Waiting 30 seconds before continuing...\n")
                            # Shorter wait - might be solved or question may change
                            for i in range(30, 0, -5):
                                mins, secs = divmod(i, 60)
                                print(f"\rCooldown: {mins:02d}:{secs:02d}  ", end='', flush=True)
                                time.sleep(5)
                            print("\r" + " "*50 + "\r", end='', flush=True)
                        
                        continue
                    
                    # Check if material gathering happened before travel (pre-travel check)
                    # This is when materials were found on /travel page BEFORE the step
                    material_gather_data = result.get("material_gather")
                    if material_gather_data:
                        if material_gather_data.get("success"):
                            self.stats['materials_gathered'] += 1
                            gather_exp   = material_gather_data.get("exp", 0)
                            gather_skill = material_gather_data.get("skill_exp", 0)
                            gather_gold  = material_gather_data.get("gold", 0)
                            gather_items = material_gather_data.get("items", [])
                            gather_msg   = material_gather_data.get("message", "")
                            
                            # Track per-item breakdown
                            for _it in gather_items:
                                _nm  = _it.get("name", "Material") if isinstance(_it, dict) else str(_it)
                                _qty = _it.get("quantity", 1)       if isinstance(_it, dict) else 1
                                self.stats['materials_log'][_nm] = self.stats['materials_log'].get(_nm, 0) + (_qty or 1)
                            
                            # Add to cumulative stats
                            self.stats['total_exp']   += gather_exp
                            self.stats['total_gold']  += gather_gold
                            self.stats['total_items'] += len(gather_items)
                            
                            print(f"\n{'='*60}")
                            print(f"🔨 MATERIAL GATHERED")
                            print(f"{'='*60}")
                            if gather_msg:
                                print(f"  📦 {gather_msg}")
                            if gather_exp > 0:
                                print(f"  💫 +{gather_exp:,} EXP")
                            if gather_skill > 0:
                                print(f"  ⚒️  +{gather_skill} Skill EXP")
                            if gather_gold > 0:
                                print(f"  💰 +{gather_gold} gold")
                            if gather_items:
                                for it in gather_items:
                                    nm = it.get("name", "item") if isinstance(it, dict) else str(it)
                                    qty = it.get("quantity", "") if isinstance(it, dict) else ""
                                    print(f"  🎁 {qty}x {nm}" if qty else f"  🎁 {nm}")
                            print(f"{'='*60}\n")
                        elif material_gather_data.get("insufficient_energy"):
                            print(f"\n⚠️  Not enough energy for gathering - skipping...")
                    
                    # Check if NPC battle occurred before travel (pre-travel check)
                    # This is when an NPC battle was found on /travel page BEFORE the step
                    npc_battle_data = result.get("npc_battle")
                    if npc_battle_data:
                        self.stats['npc_battles'] += 1  # Track battle count
                        
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
                        
                        # Check for material gathering/salvage or event items
                        # Only attempt manual gather if travel() didn't already handle it
                        # (simplemmo_bot now gathers inline when it detects type=material in the API response)
                        if parsed.get("material_encounter") and not result.get("material_gather"):
                            material_session_id = parsed.get("material_session_id")
                            material_name = parsed.get("material_name") or "Material"
                            material_qty = parsed.get("material_quantity", 1)
                            
                            # Validate we have session ID before attempting to gather
                            if not material_session_id:
                                print(f"\n  🔨 {material_name} detected, but no session ID available")
                                print(f"  ⚠️  Skipping gather (API response incomplete)")
                                self.logger.warning(f"Material encounter detected but no session ID: {parsed.get('message', '')}")
                            else:
                                print(f"\n  🔨 {material_name} found! Gathering...")
                                
                                # Auto-gather the material
                                gather_result = self.bot.salvage_material(material_session_id, material_qty, material_name)
                                
                                if gather_result.get("success"):
                                    self.stats['materials_gathered'] += 1
                                    gather_exp = gather_result.get("exp", 0)
                                    gather_gold = gather_result.get("gold", 0)
                                    gather_items = gather_result.get("items", [])
                                    
                                    # Track per-item breakdown
                                    for _it in gather_items:
                                        _nm  = _it.get("name", material_name) if isinstance(_it, dict) else str(_it)
                                        _qty = _it.get("quantity", 1)          if isinstance(_it, dict) else 1
                                        self.stats['materials_log'][_nm] = self.stats['materials_log'].get(_nm, 0) + (_qty or 1)
                                    
                                    # Add to cumulative stats
                                    self.stats['total_exp'] += gather_exp
                                    self.stats['total_gold'] += gather_gold
                                    self.stats['total_items'] += len(gather_items)
                                    
                                    print(f"  ✅ Gathered successfully!")
                                    if gather_exp > 0:
                                        print(f"  💫 +{gather_exp} EXP")
                                    if gather_gold > 0:
                                        print(f"  💰 +{gather_gold} gold")
                                    if gather_items:
                                        print(f"  🎁 +{len(gather_items)} items")
                                else:
                                    error_msg = gather_result.get('error', 'Unknown error')
                                    print(f"  ⚠️  Failed to gather '{material_name}': {error_msg}")
                            print()
                        
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
                            _RARITY_ICON = {
                                "Common": "⚪", "Uncommon": "🟢", "Rare": "🔵",
                                "Elite": "🟣", "Epic": "🟠", "Legendary": "🟡",
                                "Mythic": "🔴", "Celestial": "⭐",
                            }
                            for item in items[:5]:
                                if isinstance(item, dict):
                                    item_name = item.get("name", item.get("item", "Unknown"))
                                    item_qty = item.get("quantity", item.get("qty", 1))
                                    rarity = item.get("rarity", "")
                                    icon = _RARITY_ICON.get(rarity, "🎁")
                                    qty_str = f" x{item_qty}" if item_qty and int(item_qty) > 1 else ""
                                    if rarity:
                                        print(f"  {icon} [{rarity}] {item_name}{qty_str}")
                                    else:
                                        print(f"  🎁 {item_name}{qty_str}")
                                else:
                                    print(f"  🎁 {item}")
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
                        
                        # Close completed segment and start new one
                        segment_duration = (datetime.now() - self.segment_start_time).total_seconds()
                        self.uptime_segments.append(segment_duration)
                        self.current_segment_number += 1
                        self.segment_start_time = datetime.now()
                    
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
