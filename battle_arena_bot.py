#!/usr/bin/env python3
"""
SimpleMMO Battle Arena Bot
--------------------------
Continuously generates enemies and battles them in the Battle Arena.

Flow per iteration:
  1. Check current BP (Battle Points) and Gold
  2. If not enough → wait or stop based on config
  3. POST /api/battlearena/generate → get NPC info
  4. Display NPC (level, strength, defence, health)
  5. POST /api/npcs/attack/{npc_id} in a loop until type == "success"
  6. Show rewards, repeat

Run via:
    run_battle_arena.bat
or:
    python battle_arena_bot.py
"""

import time
import random
import re
import json
import sys
from datetime import datetime
from simplemmo_bot import SimpleMMOBot

# ────────────────────────────────────────────────────────────────────────────
# Config defaults — override these in config.json under "battle_arena" key
# ────────────────────────────────────────────────────────────────────────────
DEFAULT_BA_CONFIG = {
    # Minimum BP required to generate a fight (1 BP per generation)
    "min_bp": 2,
    # Known generation cost in gold (fetched live from page if possible)
    "generation_cost": 13750,
    # Minimum gold buffer to keep after paying generation cost
    "gold_buffer": 0,
    # Minimum gold required = generation_cost + gold_buffer (computed at runtime)
    "min_gold": 0,
    # If True: wait when out of resources instead of stopping
    "wait_when_broke": True,
    # How many minutes to wait when resources are low
    "wait_minutes_low_resources": 30,
    # Maximum attacks per NPC before giving up (safety cap)
    "max_attacks_per_npc": 100,
    # Delay between attacks in seconds
    "attack_delay": 1.0,
    # Delay between fights (seconds, randomized ±20%)
    "between_fight_delay": 5,
    # Stop after this many wins (0 = run forever)
    "max_wins": 0,
}

API_BASE = "https://api.simple-mmo.com"
WEB_BASE = "https://web.simple-mmo.com"


class BattleArenaBot:
    def __init__(self):
        self.bot = SimpleMMOBot()
        self.ba_config = dict(DEFAULT_BA_CONFIG)
        # Merge user overrides from config.json
        user_ba = self.bot.config.get("battle_arena", {})
        self.ba_config.update(user_ba)

        self.stats = {
            "wins": 0,
            "losses": 0,
            "total_exp": 0,
            "total_gold": 0,
            "total_attacks": 0,
            "start_time": datetime.now(),
        }

    # ── helpers ───────────────────────────────────────────────────────────────

    def _headers(self, referer: str = None) -> dict:
        h = {
            "X-XSRF-TOKEN": self.bot.csrf_token or "",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Accept": "application/json",
            "Origin": WEB_BASE,
            "Referer": referer or f"{WEB_BASE}/battle-arena",
        }
        if self.bot.api_token:
            h["Authorization"] = f"Bearer {self.bot.api_token}"
        return h

    def _fmt_number(self, n) -> str:
        try:
            return f"{int(n):,}"
        except Exception:
            return str(n)

    def _print_stats(self):
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        h, rem = divmod(int(uptime), 3600)
        m, s = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

        print(f"\n{'='*60}")
        print(f"📊 BATTLE ARENA STATS")
        print(f"{'='*60}")
        print(f"⏱️  Uptime      : {uptime_str}")
        print(f"⚔️  Wins        : {self.stats['wins']}")
        print(f"💀 Losses      : {self.stats['losses']}")
        print(f"💫 Total EXP   : {self._fmt_number(self.stats['total_exp'])}")
        print(f"💰 Total Gold  : {self._fmt_number(self.stats['total_gold'])}")
        print(f"🗡️  Total Attacks: {self._fmt_number(self.stats['total_attacks'])}")
        if uptime > 0:
            wins_hr = self.stats["wins"] / (uptime / 3600)
            print(f"📈 Rate        : {wins_hr:.1f} wins/hour")
        print(f"{'='*60}\n")

    # ── resource check ────────────────────────────────────────────────────────

    def get_user_resources(self) -> dict:
        """
        Fetch current BP, gold and live generation cost.
        Returns dict with 'bp', 'gold', 'generation_cost' (all may be None).
        """
        result = {"bp": None, "gold": None, "generation_cost": None}

        # Try the battle arena page — embeds stats in Alpine.js data
        try:
            r = self.bot.session.get(
                f"{WEB_BASE}/battle-arena",
                headers={"Accept": "text/html"},
                timeout=10,
            )
            if r.status_code == 200:
                html = r.text

                # Battle points
                bp_match = re.search(
                    r'"(?:battle_points|bp|battlepoints)"\s*:\s*(\d+)', html, re.IGNORECASE
                )
                if bp_match:
                    result["bp"] = int(bp_match.group(1))

                # Gold — shown as e.g. x-text="format_number(gold)" or "gold":12345
                gold_match = re.search(r'"gold"\s*:\s*(\d+)', html)
                if gold_match:
                    result["gold"] = int(gold_match.group(1))

                # Live generation cost — e.g. x-text="format_number(generation_cost)"
                # and inline like >13,750< or generation_cost: 13750
                cost_match = re.search(
                    r'"?generation_cost"?\s*[:\s]+["\']?([\d,]+)', html, re.IGNORECASE
                )
                if cost_match:
                    result["generation_cost"] = int(cost_match.group(1).replace(",", ""))
                else:
                    # Fallback: grab the number next to the gold coin icon in the generate button
                    cost_match2 = re.search(
                        r'I_GoldCoin[^>]+>\s*([\d,]+)', html
                    )
                    if cost_match2:
                        result["generation_cost"] = int(cost_match2.group(1).replace(",", ""))
        except Exception as e:
            print(f"  ⚠️  Could not fetch BA page: {e}")

        # Fallback: user API
        if result["bp"] is None or result["gold"] is None:
            try:
                r2 = self.bot.session.get(
                    f"{API_BASE}/api/user",
                    headers=self._headers(),
                    timeout=10,
                )
                if r2.status_code == 200:
                    data = r2.json()
                    if result["bp"] is None:
                        result["bp"] = (
                            data.get("battle_points")
                            or data.get("bp")
                            or data.get("battlePoints")
                        )
                    if result["gold"] is None:
                        result["gold"] = data.get("gold")
            except Exception:
                pass

        # If cost still unknown, fall back to config value
        if result["generation_cost"] is None:
            result["generation_cost"] = self.ba_config.get("generation_cost", 13750)

        return result

    def check_resources(self) -> bool:
        """
        Fetch live gold/BP, show how many fights can be afforded, and return
        True if resources are sufficient for at least one generation.
        Returns None to signal a hard stop.
        """
        resources = self.get_user_resources()
        bp   = resources["bp"]
        gold = resources["gold"]
        cost = resources["generation_cost"]

        # Update tracked cost so the rest of the bot uses the live value
        if cost:
            self.ba_config["generation_cost"] = cost

        min_bp     = self.ba_config["min_bp"]
        buffer     = self.ba_config.get("gold_buffer", 0)
        min_needed = cost + buffer  # gold required for one generation

        # How many fights can we afford right now?
        if gold is not None and cost:
            spendable    = max(0, gold - buffer)
            fights_avail = spendable // cost
        else:
            fights_avail = None

        # ── Print affordability summary ───────────────────────────────────────
        print(f"\n  {'─'*50}")
        print(f"  💰 Gold in hand   : {self._fmt_number(gold) if gold is not None else '?'}")
        print(f"  🎲 Generation cost: {self._fmt_number(cost)} gold per fight")
        if buffer:
            print(f"  🛡️  Gold buffer    : {self._fmt_number(buffer)} (kept in reserve)")
        if fights_avail is not None:
            print(f"  ⚔️  Fights afford  : {fights_avail} fight{'s' if fights_avail != 1 else ''} possible")
        print(f"  ⚡ BP available   : {bp if bp is not None else '?'} (need {min_bp})")
        print(f"  {'─'*50}")

        bp_ok   = bp   is None or bp   >= min_bp
        gold_ok = gold is None or gold >= min_needed

        if bp_ok and gold_ok:
            return True

        reasons = []
        if not bp_ok:
            reasons.append(f"BP too low ({bp} < {min_bp})")
        if not gold_ok:
            shortfall = min_needed - (gold or 0)
            reasons.append(
                f"Gold too low — have {self._fmt_number(gold)}, "
                f"need {self._fmt_number(min_needed)} (short {self._fmt_number(shortfall)})"
            )

        print(f"\n  ⛔ Cannot generate: {', '.join(reasons)}")

        if self.ba_config["wait_when_broke"]:
            wait_min = self.ba_config["wait_minutes_low_resources"]
            print(f"  ⏳ Waiting {wait_min} min for resources to replenish...")
            for remaining in range(wait_min * 60, 0, -30):
                m, s = divmod(remaining, 60)
                print(f"\r  Waiting: {m:02d}:{s:02d}  ", end="", flush=True)
                time.sleep(min(30, remaining))
            print("\r" + " " * 40 + "\r", end="", flush=True)
            return False
        else:
            print("  🛑 wait_when_broke=false → stopping.")
            return None

    # ── generate ──────────────────────────────────────────────────────────────

    def generate_npc(self) -> dict | None:
        """POST to battle arena generate endpoint. Returns NPC dict or None."""
        try:
            r = self.bot.session.post(
                f"{API_BASE}/api/battlearena/generate",
                headers=self._headers(),
                data={
                    "_token": self.bot.csrf_token or "",
                },
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                # API may return the npc directly or nested under a key
                npc = data if "id" in data else data.get("npc") or data.get("data") or data
                return npc
            else:
                print(f"  ❌ Generate failed: HTTP {r.status_code} — {r.text[:200]}")
                return None
        except Exception as e:
            print(f"  ❌ Generate error: {e}")
            return None

    # ── attack loop ───────────────────────────────────────────────────────────

    def attack_loop(self, npc_id: int, npc_name: str) -> dict:
        """
        Repeatedly POST /api/npcs/attack/{npc_id} until victory or cap.
        Returns dict with success, exp, gold, attacks.
        """
        attack_url = f"{API_BASE}/api/npcs/attack/{npc_id}"
        referer    = f"{WEB_BASE}/npcs/attack/{npc_id}"
        max_att    = self.ba_config["max_attacks_per_npc"]
        delay      = self.ba_config["attack_delay"]

        total_exp   = 0
        total_gold  = 0
        attack_count = 0

        print(f"\n  ⚔️  Fighting {npc_name} (ID: {npc_id})")

        while attack_count < max_att:
            attack_count += 1
            self.stats["total_attacks"] += 1

            try:
                r = self.bot.session.post(
                    attack_url,
                    headers=self._headers(referer),
                    data={
                        "_token":       self.bot.csrf_token or "",
                        "npc_id":       str(npc_id),
                        "special_attack": "false",
                    },
                    timeout=15,
                )
            except Exception as e:
                print(f"\n  ❌ Attack request error: {e}")
                time.sleep(delay * 2)
                continue

            if r.status_code != 200:
                print(f"\n  ❌ Attack HTTP {r.status_code}")
                time.sleep(delay * 2)
                continue

            try:
                d = r.json()
            except Exception:
                time.sleep(delay)
                continue

            t          = (d.get("type") or "").lower()
            player_hp  = d.get("player_hp", "?")
            opp_hp     = d.get("opponent_hp", "?")
            opp_pct    = d.get("opponent_hp_percentage", "?")
            dmg_dealt  = d.get("damage_given_to_opponent", 0)
            dmg_taken  = d.get("damage_given_to_player", 0)

            print(
                f"\r  Hit #{attack_count:>3}  |  Dealt: {dmg_dealt:>5}  |  "
                f"Enemy HP: {self._fmt_number(opp_hp)} ({opp_pct}%)  |  "
                f"Your HP: {self._fmt_number(player_hp)}   ",
                end="",
                flush=True,
            )

            # ── Victory ──────────────────────────────────────────────────────
            if (t == "success"
                    or "winner" in (d.get("title") or "").lower()
                    or d.get("npc_killed") is True
                    or d.get("battle_over") is True
                    or (isinstance(opp_hp, (int, float)) and opp_hp <= 0)):
                print()  # newline after progress line

                # Parse EXP from result HTML if structured rewards not present
                rewards = d.get("rewards") or []
                result_html = d.get("result") or ""

                for reward in rewards:
                    if isinstance(reward, dict):
                        total_exp  += reward.get("exp",  reward.get("experience", 0)) or 0
                        total_gold += reward.get("gold", reward.get("coins",      0)) or 0

                if total_exp == 0:
                    # Fall back to direct fields
                    total_exp  = d.get("exp",  d.get("experience", 0)) or 0
                    total_gold = d.get("gold", d.get("coins",      0)) or 0

                if total_exp == 0 and result_html:
                    # Last resort: parse "20,893 Total EXP" from HTML
                    exp_match = re.search(r"([\d,]+)\s*Total\s*EXP", result_html)
                    if exp_match:
                        total_exp = int(exp_match.group(1).replace(",", ""))

                self.stats["wins"]      += 1
                self.stats["total_exp"] += total_exp
                self.stats["total_gold"] += total_gold

                print(f"  ✅ Victory after {attack_count} attacks!")
                if total_exp  > 0: print(f"  💫 EXP:  +{self._fmt_number(total_exp)}")
                if total_gold > 0: print(f"  💰 Gold: +{self._fmt_number(total_gold)}")
                if d.get("title"):
                    print(f"  🏆 {d['title']}")

                return {"success": True, "exp": total_exp, "gold": total_gold, "attacks": attack_count}

            # ── Error ────────────────────────────────────────────────────────
            elif t == "error":
                print()
                err = d.get("message", "Unknown battle error")
                print(f"  ❌ Battle error: {err}")
                self.stats["losses"] += 1
                return {"success": False, "error": err, "attacks": attack_count}

            time.sleep(delay)

        print()
        print(f"  ⚠️  Hit max attack cap ({max_att}) — something went wrong")
        self.stats["losses"] += 1
        return {"success": False, "error": "max attacks reached", "attacks": attack_count}

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        print("=" * 60)
        print("⚔️  SimpleMMO BATTLE ARENA BOT")
        print("=" * 60)
        print(f"  Min BP required    : {self.ba_config['min_bp']}")
        print(f"  Generation cost    : {self._fmt_number(self.ba_config.get('generation_cost', 13750))} gold (fetched live each fight)")
        gold_buffer = self.ba_config.get('gold_buffer', 0)
        if gold_buffer:
            print(f"  Gold buffer        : {self._fmt_number(gold_buffer)} (kept in reserve)")
        print(f"  Wait when broke    : {self.ba_config['wait_when_broke']}")
        print(f"  Attack delay       : {self.ba_config['attack_delay']}s")
        max_wins = self.ba_config["max_wins"]
        if max_wins:
            print(f"  Stop after wins    : {max_wins}")
        print("Press Ctrl+C to stop\n" + "=" * 60 + "\n")

        # Login
        print("[Logging in...]")
        if not self.bot.login():
            print("✗ Login failed. Exiting.")
            sys.exit(1)
        print("✓ Login successful!\n")

        fight_num = 0

        while True:
            try:
                max_wins = self.ba_config["max_wins"]
                if max_wins and self.stats["wins"] >= max_wins:
                    print(f"\n🏁 Reached max wins ({max_wins}). Stopping.")
                    break

                fight_num += 1
                print(f"\n{'─'*60}")
                print(f"⚔️  Fight #{fight_num}  |  Total wins: {self.stats['wins']}")
                print(f"{'─'*60}")

                # 1. Resource check
                ok = self.check_resources()
                if ok is None:   # hard stop
                    break
                if not ok:       # wait and retry
                    continue

                # 2. Generate NPC
                print("  🎲 Generating opponent...")
                npc = self.generate_npc()
                if not npc:
                    print("  ❌ Failed to generate NPC. Waiting 30s...")
                    time.sleep(30)
                    continue

                npc_id    = npc.get("id") or npc.get("npc_id")
                npc_name  = npc.get("name",    "Unknown")
                npc_level = npc.get("level",   "?")
                npc_str   = npc.get("strength","?")
                npc_def   = npc.get("defence", npc.get("defense","?"))
                npc_hp    = npc.get("health",  npc.get("hp","?"))

                if not npc_id:
                    print(f"  ❌ No NPC ID in generate response: {npc}")
                    time.sleep(30)
                    continue

                print(f"  👹 Opponent: {npc_name} (Lvl {self._fmt_number(npc_level)})")
                print(f"     STR: {self._fmt_number(npc_str)}  |  DEF: {self._fmt_number(npc_def)}  |  HP: {self._fmt_number(npc_hp)}")

                # 3. Fight!
                result = self.attack_loop(npc_id, npc_name)

                # 4. Print overall stats every 5 wins
                if self.stats["wins"] % 5 == 0 and self.stats["wins"] > 0:
                    self._print_stats()

                # 5. Delay before next fight
                base_delay = self.ba_config["between_fight_delay"]
                delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
                print(f"\n  ⏳ Next fight in {delay:.1f}s...")
                time.sleep(delay)

            except KeyboardInterrupt:
                print("\n\n🛑 Stopped by user.")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                print("Waiting 30s before retry...")
                time.sleep(30)

        self._print_stats()
        print("Battle Arena Bot stopped.")


if __name__ == "__main__":
    BattleArenaBot().run()
