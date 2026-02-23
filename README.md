# SimpleMMO Automation Suite

A developer/testing toolkit for automating SimpleMMO. Four fully-featured bots, one config file.

---

> âš ï¸ **For developer/testing use only.** Use responsibly and only on accounts you own.

---

## Bots at a Glance

| Bot | Script | Launch |
|-----|--------|--------|
| 24/7 AFK Travel | `run_24_7.py` | `run_afk.bat` |
| Battle Arena | `battle_arena_bot.py` | `run_battle_arena.bat` |
| Quest Runner | `quest_runner.py` | `run_quest.bat` |
| Core / Single test | `simplemmo_bot.py` | `run_bot.bat` |

---

## Features

### ðŸŒ 24/7 AFK Travel Bot (`run_24_7.py`)
- Walks travel steps continuously with human-like random delays (15â€“18 s)
- **Auto-battles NPCs** encountered during travel (signed-URL attack flow)
- **Auto-gathers materials** with signed-URL extraction from HTML
- **Item drop display** â€” parses rarity (`Common` â†’ `Celestial`) and item name from HTML with 5-strategy fallback; shows coloured rarity icon (âšªðŸŸ¢ðŸ”µðŸŸ£ðŸŸ ðŸŸ¡ðŸ”´â­)
- Random breaks every 50â€“100 travels; session refresh every 2â€“4 hours
- Per-travel live stats: EXP, Gold, cooldown countdown
- Summary stats every 10 travels: EXP/hour, Gold/hour, travels/hour

### âš”ï¸ Battle Arena Bot (`battle_arena_bot.py`)
- Generates opponents and fights in a loop until gold or energy runs out
- **Live resource check** before every fight: reads gold & energy via API-first strategy with HTML fallback
- Signed-URL endpoint resolution per fight (never uses bare unsigned URLs)
- Per-hit display: damage dealt, enemy HP remaining, your HP
- **Smart wait logic**: energy-low â†’ short wait (`wait_minutes_low_energy`), gold-low â†’ longer wait (`wait_minutes_low_resources`)
- Float-safe wait (e.g. `2.5` minutes works correctly)
- Configurable: min energy, generation cost, max attacks per NPC, attack delay, max wins cap

### ðŸ“œ Quest Runner Bot (`quest_runner.py`)
- Fetches all available quests; completes them lowest-level first
- Extracts signed quest API endpoints from page HTML each run
- Tracks quest points; polls for regeneration when exhausted (`qp_poll_interval`)
- All delays configurable via `config.json` `"quest"` block
- Separate delays: between steps within a quest vs. between quests

### ðŸ¤– CAPTCHA Auto-Solve System
- **AI image recognition** using OpenAI CLIP (~600 MB, loaded once)
- Records every attempt (success + failure) to `captcha_learning/`
- **Auto-labels failures** from later successes (retroactive) or immediately with CLIP confidence score
- **`auto_captcha_training`** flag in `config.json` â€” set `false` to pause model retraining while you review labels; set `true` to allow automatic background training when 20+ new labels accumulate
- Fine-tuned model support (`use_finetuned_captcha: true`) once trained

### ðŸ” Authentication
- Email/password login with CSRF token extraction
- OAuth/Google login via `session_token` + `xsrf_token`
- **Hybrid mode** (both set) â€” automatic fallback to email/password when session expires; no manual intervention needed

---

## Installation

**1. Python 3.9+**

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Configure `config.json`** (copy from `config.template.json`)

**For Google/OAuth login** â€” see [SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md) for how to extract your session cookie from the browser.

---

## Configuration Reference

### Auth & Travel
| Key | Description | Default |
|-----|-------------|---------|
| `email` / `password` | Email login credentials | â€” |
| `session_token` / `xsrf_token` | OAuth session cookies | â€” |
| `api_token` | API Bearer token (from page) | â€” |
| `travel_delay_min` / `max` | Seconds between travel steps | `15` / `18` |
| `auto_battle_npcs` | Auto-fight NPCs on travel | `true` |
| `auto_gather_materials` | Auto-gather materials on travel | `true` |
| `debug_mode` | Log raw API responses | `false` |

### CAPTCHA
| Key | Description | Default |
|-----|-------------|---------|
| `auto_solve_captcha` | Enable AI CAPTCHA solving | `true` |
| `captcha_random_fallback` | Random guess if AI fails | `false` |
| `use_finetuned_captcha` | Use your trained model over base CLIP | `false` |
| `auto_captcha_training` | Allow automatic model retraining | `false` |

### Battle Arena (`battle_arena` block)
| Key | Description | Default |
|-----|-------------|---------|
| `min_bp` | Minimum energy (battle points) required | `1` |
| `generation_cost` | Gold cost to generate an opponent | `13750` |
| `wait_minutes_low_energy` | Wait time when energy is too low | `2.5` |
| `wait_minutes_low_resources` | Wait time when gold is too low | `15` |
| `max_attacks_per_npc` | Attack cap per NPC | `100` |
| `attack_delay` | Seconds between attack hits | `1.0` |
| `between_fight_delay` | Seconds between fights | `5` |
| `max_wins` | Stop after N wins (`0` = unlimited) | `0` |

### Quest Runner (`quest` block)
| Key | Description | Default |
|-----|-------------|---------|
| `delay_between_steps_min/max` | Delay between perform attempts within a quest | `2` / `4` |
| `delay_between_quests_min/max` | Delay after a quest completes | `3` / `6` |
| `qp_poll_interval` | Seconds between quest-point checks when exhausted | `60` |
| `error_retry_delay` | Wait on unexpected errors before retry | `10` |

---

## Example Output

### Travel Bot
```
============================================================
âœ“ Travel #142 completed
  ðŸ’¬ You stumble upon a hidden treasure...
  ðŸ’« EXP: +2,523  (Session: 456,789)
  ðŸ’° Gold: +892   (Session: 125,340 | Current: 2,614,010)
  ðŸŸ£ [Elite] Shadowblade Dagger
  â±ï¸  Cooldown: 5.2s
============================================================
Next travel in: 00:16
```

### Battle Arena Bot
```
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
âš”ï¸  Fight #12  |  Total wins: 11
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  ðŸ’° Gold in hand   : 2,600,260
  ðŸŽ² Generation cost: 13,750 gold per fight
  âš”ï¸  Fights afford  : 189 fights possible
  âš¡ Energy available : 3 (need 1)

  ðŸŽ² Generating opponent...
  ðŸ‘¹ Opponent: Lunar Warrior (Lvl 1,550)

  Hit #  1  |  Dealt: 6,894  |  Enemy HP: 0 (0%)  |  Your HP: 7,815
  âœ… Victory after 1 attacks!
  ðŸ’« EXP: +17,723
  â³ Next fight in 5.1s...
```

---

## Project Structure

```
simplemmo_bot.py       â€” Core bot: login, travel, NPC attack, material gather
run_24_7.py            â€” 24/7 AFK loop with stats and break system
battle_arena_bot.py    â€” Battle Arena automation
quest_runner.py        â€” Quest automation
auto_captcha_learner.py â€” CAPTCHA auto-label + auto-training system
train_captcha_model.py  â€” Fine-tune CLIP on collected labels
config.json            â€” All settings for all bots
requirements.txt       â€” Python dependencies
captcha_learning/      â€” Saved attempt images + labels + stats
models/                â€” Fine-tuned CAPTCHA model (after training)
```

---

## Guides

| Guide | Topic |
|-------|-------|
| [AFK_24_7_GUIDE.md](AFK_24_7_GUIDE.md) | 24/7 AFK mode setup |
| [SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md) | OAuth/Google login |
| [AUTO_FALLBACK_GUIDE.md](AUTO_FALLBACK_GUIDE.md) | Session auto-recovery |
| [AUTO_LEARNING_GUIDE.md](AUTO_LEARNING_GUIDE.md) | CAPTCHA self-improvement loop |
| [CAPTCHA_SETUP.md](CAPTCHA_SETUP.md) | CAPTCHA AI dependencies |
| [QUEST_AUTOMATION.md](QUEST_AUTOMATION.md) | Quest runner details |
| [TRAVEL_FLOW_GUIDE.md](TRAVEL_FLOW_GUIDE.md) | How travel parsing works |
| [TROUBLESHOOTING_403.md](TROUBLESHOOTING_403.md) | Fixing 403 / session issues |

---

## Logging

| File | Contents |
|------|----------|
| `simplemmo_bot.log` | Travel, NPC, gather events |
| `quest_runner.log` | Quest completion events |
| `captcha_learning/learning_stats.json` | CAPTCHA attempt counts, training runs |

Enable verbose output with `"debug_mode": true` in `config.json` to see raw API responses.

---

## License

Developer/testing tool. Use responsibly and only on accounts you own.
