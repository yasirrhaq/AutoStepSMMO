#!/usr/bin/env python3
"""
SimpleMMO World Boss Bot
------------------------
Automatically attacks world bosses when they become available.

Features:
  - Auto-discovers available world bosses
  - Attacks bosses when they are attackable
  - Handles cooldown timers and retries
  - Tracks damage dealt and rewards

Run via:
    python world_boss_bot.py
"""

import time
import random
import re
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from simplemmo_bot import SimpleMMOBot

# ────────────────────────────────────────────────────────────────────────────
# Config defaults — override these in config.json under "world_boss" key
# ────────────────────────────────────────────────────────────────────────────
DEFAULT_WB_CONFIG = {
    # Check interval in seconds (how often to check if boss is attackable)
    "check_interval": 30,
    # Minimum energy required to attack
    "min_energy": 10,
    # Use special attack (costs diamonds) - False = normal attack only
    "use_special_attack": False,
    # Boss IDs to prioritize (empty = attack any available boss)
    "target_boss_ids": [],
    # Wait for next boss if none available
    "wait_for_next": True,
    # Maximum attack attempts per boss (safety cap)
    "max_attacks_per_boss": 1000,
    # Delay between attacks on same boss (seconds)
    "attack_delay": 2.0,
}

API_BASE = "https://api.simple-mmo.com"
WEB_BASE = "https://web.simple-mmo.com"


class WorldBossBot:
    def __init__(self):
        self.bot = SimpleMMOBot()
        self.wb_config = dict(DEFAULT_WB_CONFIG)
        # Merge user overrides from config.json
        user_wb = self.bot.config.get("world_boss", {})
        self.wb_config.update(user_wb)

        self.stats = {
            "total_attacks": 0,
            "total_damage": 0,
            "total_exp": 0,
            "total_gold": 0,
            "bosses_killed": 0,
            "start_time": datetime.now(),
            "current_boss": None,
        }
        
        # Track attacked bosses to avoid over-attacking
        self.attacked_bosses = {}

    # ── helpers ───────────────────────────────────────────────────────────────

    def _headers(self, referer: str = None) -> dict:
        """Generate request headers with proper authentication"""
        h = {
            "X-XSRF-TOKEN": self.bot.csrf_token or "",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
            "Origin": WEB_BASE,
            "Referer": referer or f"{WEB_BASE}/worldboss/all",
        }
        if self.bot.api_token:
            h["Authorization"] = f"Bearer {self.bot.api_token}"
        return h

    def _fmt_number(self, n) -> str:
        """Format number with commas"""
        try:
            return f"{int(n):,}"
        except Exception:
            return str(n)

    def _parse_time_remaining(self, timer_text: str) -> Optional[int]:
        """Parse time remaining from boss timer text"""
        if "can be attacked now" in timer_text.lower():
            return 0
        
        # Parse formats like "2 days 5 hours 30 minutes 15 seconds"
        days = hours = minutes = seconds = 0
        
        day_match = re.search(r'(\d+)\s+day', timer_text)
        if day_match:
            days = int(day_match.group(1))
        
        hour_match = re.search(r'(\d+)\s+hour', timer_text)
        if hour_match:
            hours = int(hour_match.group(1))
        
        minute_match = re.search(r'(\d+)\s+minute', timer_text)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        second_match = re.search(r'(\d+)\s+second', timer_text)
        if second_match:
            seconds = int(second_match.group(1))
        
        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
        return total_seconds if total_seconds > 0 else None

    def _extract_countdown_timestamp(self, html: str) -> Optional[int]:
        """Extract Unix timestamp from countdown JavaScript"""
        # Look for: var countDownDate = 1772197043*1000;
        match = re.search(r'countDownDate\s*=\s*(\d+)\*1000', html)
        if match:
            return int(match.group(1))
        return None

    # ── core methods ──────────────────────────────────────────────────────────

    def login(self) -> bool:
        """Login to SimpleMMO"""
        if not self.bot.logged_in:
            success = self.bot.login()
            if not success:
                print("❌ Failed to login. Please check your config.json")
                return False
        return True

    def get_world_bosses(self) -> List[Dict[str, Any]]:
        """
        Fetch list of all world bosses from the battle menu page.
        Returns list of boss dicts with id, name, level, stats, etc.
        """
        bosses = []
        try:
            # Get the battle menu page which shows upcoming world bosses
            response = self.bot.session.get(
                f"{WEB_BASE}/battle/menu",
                headers=self._headers(f"{WEB_BASE}/battle/menu")
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch battle menu: {response.status_code}")
                return bosses
            
            html = response.text
            
            # Parse boss info from the HTML
            # Look for boss links like /worldboss/view/3464
            boss_links = re.findall(r'href="/worldboss/view/(\d+)"', html)
            
            for boss_id in set(boss_links):
                boss_info = self.get_boss_details(boss_id)
                if boss_info:
                    bosses.append(boss_info)
            
            # Also check the world boss list page
            response = self.bot.session.get(
                f"{WEB_BASE}/worldboss/all",
                headers=self._headers(f"{WEB_BASE}/worldboss/all")
            )
            
            if response.status_code == 200:
                # Parse additional bosses from the list page
                boss_links = re.findall(r'href="/worldboss/view/(\d+)"', response.text)
                existing_ids = {b['id'] for b in bosses}
                
                for boss_id in set(boss_links):
                    if boss_id not in existing_ids:
                        boss_info = self.get_boss_details(boss_id)
                        if boss_info:
                            bosses.append(boss_info)
            
            return bosses
            
        except Exception as e:
            print(f"❌ Error fetching world bosses: {e}")
            return bosses

    def get_boss_details(self, boss_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information about a specific world boss.
        Returns dict with boss details or None if failed.
        """
        try:
            response = self.bot.session.get(
                f"{WEB_BASE}/worldboss/view/{boss_id}",
                headers=self._headers(f"{WEB_BASE}/worldboss/view/{boss_id}")
            )
            
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Extract boss name
            name_match = re.search(r'<h1[^>]*class="[^"]*truncate[^"]*"[^>]*>(.*?)</h1>', html)
            name = name_match.group(1).strip() if name_match else f"Boss {boss_id}"
            
            # Extract level
            level_match = re.search(r'Level\s+(\d+)', html)
            level = int(level_match.group(1)) if level_match else 0
            
            # Extract stats (Strength, Dexterity, Defence, Health)
            stats = {}
            stat_patterns = [
                (r'Strength.*?<dd[^>]*>(\d+)</dd>', 'strength'),
                (r'Dexterity.*?<dd[^>]*>(\d+)</dd>', 'dexterity'),
                (r'Defence.*?<dd[^>]*>(\d+)</dd>', 'defence'),
                (r'Health.*?<dd[^>]*>(\d+)</dd>', 'health'),
            ]
            
            for pattern, stat_name in stat_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    stats[stat_name] = int(match.group(1))
            
            # Extract countdown timestamp
            attackable_at = self._extract_countdown_timestamp(html)
            
            # Check if currently attackable
            is_attackable = "can be attacked now" in html.lower() or \
                          (attackable_at and attackable_at * 1000 <= time.time() * 1000)
            
            # Parse timer text
            timer_match = re.search(r'id="bossTimer"[^>]*>(.*?)</span>', html)
            timer_text = timer_match.group(1) if timer_match else ""
            
            return {
                'id': boss_id,
                'name': name,
                'level': level,
                'stats': stats,
                'is_attackable': is_attackable,
                'attackable_at': attackable_at,
                'timer_text': timer_text,
                'html': html,  # Store for attack extraction
            }
            
        except Exception as e:
            print(f"❌ Error fetching boss details for {boss_id}: {e}")
            return None

    def attack_boss(self, boss_id: str, special_attack: bool = False) -> Dict[str, Any]:
        """
        Attack a world boss.
        Returns dict with attack results.
        """
        try:
            # Get fresh boss details to extract tokens
            boss_info = self.get_boss_details(boss_id)
            if not boss_info:
                return {'success': False, 'error': 'Could not fetch boss details'}
            
            html = boss_info['html']
            
            # Extract _token from the HTML (CSRF token)
            token_match = re.search(r'name="_token"\s+value="([^"]+)"', html)
            if not token_match:
                # Try alternate pattern
                token_match = re.search(r'"_token":"([^"]+)"', html)
            
            csrf_token = token_match.group(1) if token_match else self.bot.csrf_token
            
            # Build attack URL
            attack_url = f"{API_BASE}/api/worldboss/attack/{boss_id}"
            
            # Prepare payload
            payload = {
                '_token': csrf_token,
                'special_attack': 'true' if special_attack else 'false',
                'api_token': self.bot.api_token or '',
            }
            
            print(f"⚔️  Attacking boss {boss_info['name']} (Level {boss_info['level']})...")
            
            response = self.bot.session.post(
                attack_url,
                data=payload,
                headers=self._headers(f"{WEB_BASE}/worldboss/view/{boss_id}")
            )
            
            print(f"   Response status: {response.status_code}")
            
            # Parse response
            try:
                result = response.json()
            except:
                result = {'text': response.text}
            
            # Check for success
            if response.status_code == 200:
                self.stats['total_attacks'] += 1
                
                # Track attack on this boss
                if boss_id not in self.attacked_bosses:
                    self.attacked_bosses[boss_id] = 0
                self.attacked_bosses[boss_id] += 1
                
                # Extract damage/exp/gold from result
                damage = result.get('damage', 0)
                exp_gained = result.get('exp', 0) or result.get('experience', 0)
                gold_gained = result.get('gold', 0)
                
                self.stats['total_damage'] += damage
                self.stats['total_exp'] += exp_gained
                self.stats['total_gold'] += gold_gained
                
                # Check if boss was killed
                if result.get('killed') or result.get('boss_defeated'):
                    self.stats['bosses_killed'] += 1
                    print(f"   💀 BOSS DEFEATED!")
                
                print(f"   ✅ Damage: {self._fmt_number(damage)} | "
                      f"EXP: +{self._fmt_number(exp_gained)} | "
                      f"Gold: +{self._fmt_number(gold_gained)}")
                
                return {
                    'success': True,
                    'damage': damage,
                    'exp': exp_gained,
                    'gold': gold_gained,
                    'killed': result.get('killed', False),
                    'result': result,
                }
            
            elif response.status_code == 401:
                print(f"   ❌ Unauthorized - session expired or invalid token")
                return {'success': False, 'error': 'Unauthorized', 'retry': False}
            
            elif response.status_code == 429:
                print(f"   ⏳ Rate limited - too many attacks")
                return {'success': False, 'error': 'Rate limited', 'retry': True}
            
            else:
                error_msg = result.get('message', result.get('error', response.text[:200]))
                print(f"   ❌ Attack failed: {error_msg}")
                return {'success': False, 'error': error_msg, 'retry': True}
                
        except Exception as e:
            print(f"   ❌ Error during attack: {e}")
            return {'success': False, 'error': str(e), 'retry': True}

    def find_attackable_boss(self) -> Optional[Dict[str, Any]]:
        """Find a world boss that is currently attackable"""
        print("🔍 Checking for attackable world bosses...")
        
        bosses = self.get_world_bosses()
        
        if not bosses:
            print("   No world bosses found")
            return None
        
        print(f"   Found {len(bosses)} world boss(es)")
        
        # Filter for attackable bosses
        attackable = [b for b in bosses if b.get('is_attackable')]
        
        # Filter by target list if specified
        target_ids = self.wb_config.get('target_boss_ids', [])
        if target_ids:
            attackable = [b for b in attackable if b['id'] in target_ids]
        
        if attackable:
            # Sort by level (highest first)
            attackable.sort(key=lambda x: x.get('level', 0), reverse=True)
            boss = attackable[0]
            print(f"   ✅ {boss['name']} (Level {boss['level']}) is attackable!")
            return boss
        
        # Find the boss with shortest wait time
        soonest_boss = None
        soonest_time = float('inf')
        
        for boss in bosses:
            attackable_at = boss.get('attackable_at')
            if attackable_at:
                wait_time = attackable_at - time.time()
                if 0 < wait_time < soonest_time:
                    soonest_time = wait_time
                    soonest_boss = boss
        
        if soonest_boss:
            hours, remainder = divmod(int(soonest_time), 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"   ⏳ {soonest_boss['name']} attackable in {hours}h {minutes}m {seconds}s")
        else:
            print("   ⏳ No bosses currently attackable")
        
        return None

    def print_stats(self):
        """Print current session statistics"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        h, rem = divmod(int(uptime), 3600)
        m, s = divmod(rem, 60)
        
        print("\n" + "=" * 50)
        print("📊 WORLD BOSS BOT STATS")
        print("=" * 50)
        print(f"Uptime: {h}h {m}m {s}s")
        print(f"Total Attacks: {self._fmt_number(self.stats['total_attacks'])}")
        print(f"Total Damage: {self._fmt_number(self.stats['total_damage'])}")
        print(f"Total EXP: {self._fmt_number(self.stats['total_exp'])}")
        print(f"Total Gold: {self._fmt_number(self.stats['total_gold'])}")
        print(f"Bosses Killed: {self.stats['bosses_killed']}")
        if self.stats['current_boss']:
            print(f"Current Target: {self.stats['current_boss']}")
        print("=" * 50 + "\n")

    def run(self):
        """Main bot loop"""
        print("=" * 60)
        print("🐉 SIMPLEMMO WORLD BOSS BOT")
        print("=" * 60)
        print(f"Config: check_interval={self.wb_config['check_interval']}s, "
              f"special_attack={self.wb_config['use_special_attack']}")
        print("=" * 60)
        
        # Login
        if not self.login():
            return
        
        print("\n✅ Logged in successfully!")
        print("Press Ctrl+C to stop\n")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            while True:
                try:
                    # Find an attackable boss
                    boss = self.find_attackable_boss()
                    
                    if boss:
                        self.stats['current_boss'] = boss['name']
                        boss_id = boss['id']
                        max_attacks = self.wb_config['max_attacks_per_boss']
                        attack_delay = self.wb_config['attack_delay']
                        
                        print(f"\n🎯 Targeting: {boss['name']} (ID: {boss_id})")
                        print(f"   Stats: STR {boss['stats'].get('strength', '?')} | "
                              f"DEX {boss['stats'].get('dexterity', '?')} | "
                              f"DEF {boss['stats'].get('defence', '?')} | "
                              f"HP {boss['stats'].get('health', '?')}")
                        print()
                        
                        # Attack loop
                        attacks_this_boss = self.attacked_bosses.get(boss_id, 0)
                        
                        while attacks_this_boss < max_attacks:
                            # Check if still attackable
                            boss_info = self.get_boss_details(boss_id)
                            if not boss_info or not boss_info.get('is_attackable'):
                                print(f"\n⏹️  Boss is no longer attackable")
                                break
                            
                            # Perform attack
                            result = self.attack_boss(
                                boss_id, 
                                special_attack=self.wb_config['use_special_attack']
                            )
                            
                            if not result['success']:
                                if not result.get('retry', True):
                                    print("   Stopping - non-retryable error")
                                    return
                                
                                # Wait before retry
                                time.sleep(5)
                                continue
                            
                            attacks_this_boss += 1
                            consecutive_errors = 0
                            
                            # Check if boss killed
                            if result.get('killed'):
                                print(f"\n🎉 Boss defeated!")
                                break
                            
                            # Delay between attacks
                            time.sleep(attack_delay + random.uniform(0, 0.5))
                        
                        print(f"\n✅ Finished attacking {boss['name']}")
                        print(f"   Total attacks this session: {attacks_this_boss}")
                        
                    else:
                        # No boss available - wait and check again
                        check_interval = self.wb_config['check_interval']
                        print(f"\n😴 No attackable bosses. Checking again in {check_interval}s...")
                        print("   (Press Ctrl+C to stop)")
                        time.sleep(check_interval)
                    
                    # Print stats periodically
                    if self.stats['total_attacks'] > 0 and self.stats['total_attacks'] % 10 == 0:
                        self.print_stats()
                        
                except Exception as e:
                    consecutive_errors += 1
                    print(f"\n❌ Error in main loop: {e}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"   Too many consecutive errors ({consecutive_errors}). Stopping.")
                        break
                    
                    print(f"   Retrying in 10s... (error {consecutive_errors}/{max_consecutive_errors})")
                    time.sleep(10)
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Stopped by user")
        
        finally:
            self.print_stats()
            print("\n👋 World Boss Bot stopped")


# ── entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot = WorldBossBot()
    bot.run()
