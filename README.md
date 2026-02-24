# SimpleMMO Automation Suite

A developer/testing toolkit for automating SimpleMMO. Four fully-featured bots, one shared config file.

> WARNING: For developer/testing use only. Use responsibly and only on accounts you own.

---

## Bots at a Glance

| Bot                | Script                | Launch                 |
|--------------------|-----------------------|------------------------|
| 24/7 AFK Travel    | `run_24_7.py`         | `run_afk.bat`          |
| Battle Arena       | `battle_arena_bot.py` | `run_battle_arena.bat` |
| Quest Runner       | `quest_runner.py`     | `run_quest.bat`        |
| Core / Single test | `simplemmo_bot.py`    | `run_bot.bat`          |

Double-click any `.bat` file to launch. When the bot stops, the window will ask:

```
 Press Enter to restart, or C to close.
```

- **Enter** - restarts the bot automatically
- **C** - closes the window

---

## Features

### 24/7 AFK Travel Bot (`run_24_7.py`)

- Walks travel steps continuously with human-like random delays (configurable, default 15-18 s)
- Auto-battles NPCs encountered during travel using signed-URL attack flow
- Auto-gathers materials using signed-URL extraction from page HTML
- Item drop display with rarity parsing: Common, Uncommon, Rare, Elite, Epic, Legendary, Mythic, Celestial
- Random breaks every 50-100 travels; automatic session refresh every 2-4 hours
- Per-travel live stats: EXP, Gold, cooldown countdown
- Summary stats every 10 travels: EXP/hour, Gold/hour, travels/hour
- Per-material breakdown in session stats (e.g. Iron Ore x12, Leather x5)
- Clean Ctrl+C stop with full session summary printed before exit

### Battle Arena Bot (`battle_arena_bot.py`)

- Generates opponents and fights in a loop until gold or energy runs out
- Live resource check before every fight (API-first, HTML fallback)
- Signed-URL endpoint resolution per fight
- Per-hit display: damage dealt, enemy HP remaining, your HP
- Smart wait: energy-low uses `wait_minutes_low_energy`, gold-low uses `wait_minutes_low_resources`
- Float-safe wait times (e.g. 2.5 minutes works correctly)
- Configurable: min energy, generation cost, max attacks per NPC, attack delay, max wins cap
- Clean Ctrl+C stop with full session stats printed before exit

### Quest Runner Bot (`quest_runner.py`)

- Fetches all available quests and completes them lowest-level first
- Extracts signed quest API endpoints from page HTML on each run
- Tracks quest points and polls for regeneration when exhausted
- Per-quest step tracking: knows how many steps done vs. remaining per quest
- Clean Ctrl+C stop with detailed summary:
  - Quests fully completed
  - Total quest steps performed
  - Total EXP and Gold earned
  - Per-quest progress breakdown (steps done / total, remaining)
- All delays configurable via the `quest` block in `config.json`

### CAPTCHA Auto-Solve System

- AI image recognition using OpenAI CLIP (loaded once, ~600 MB)
- Correct CLIP ranking: softmax across images per text prompt, then averaged across text variations
- Records every attempt (image + result) to `captcha_learning/`
- Auto-labels failures retroactively when a later success confirms the correct answer
- `auto_captcha_training` flag controls whether the model retrains automatically
- Fine-tuned model trained with 4-way CrossEntropyLoss (proper ranking loss)
- Smart model fallback: switches between base CLIP and fine-tuned model after N consecutive failures

### Authentication

- Email/password login with CSRF token extraction
- OAuth/Google login via `session_token` + `xsrf_token` cookies
- Hybrid mode: if both are configured, automatically falls back to email login when session expires

---

## Installation

**1. Requires Python 3.9 or later.**

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Copy `config.template.json` to `config.json` and fill in your credentials.**

For Google/OAuth login, see [SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md) for how to
extract your session cookie from the browser.

---

## Configuration Reference

### Auth & General

| Key                            | Description                                     | Default     |
|--------------------------------|-------------------------------------------------|-------------|
| `email` / `password`           | Email/password login credentials                | --          |
| `session_token` / `xsrf_token` | OAuth/Google session cookies                    | --          |
| `api_token`                    | API Bearer token extracted from the page        | --          |
| `travel_delay_min` / `max`     | Seconds between travel steps                    | `15` / `18` |
| `auto_battle_npcs`             | Auto-fight NPCs encountered during travel       | `true`      |
| `auto_gather_materials`        | Auto-gather materials encountered during travel | `true`      |
| `debug_mode`                   | Show raw API response logs in console           | `false`     |

### CAPTCHA

| Key                         | Description                                        | Default          |
|-----------------------------|----------------------------------------------------|------------------|
| `auto_solve_captcha`        | Enable AI CAPTCHA solving                          | `true`           |
| `captcha_random_fallback`   | Random guess if AI confidence is too low           | `false`          |
| `captcha_model_strategy`    | `base_only`, `finetuned_only`, or `smart_fallback` | `smart_fallback` |
| `captcha_failure_threshold` | Failures before switching models (smart fallback)  | `5`              |
| `use_finetuned_captcha`     | Prefer fine-tuned model over base CLIP             | `false`          |
| `auto_captcha_training`     | Allow automatic background model retraining        | `false`          |

### Battle Arena (`battle_arena` block)

| Key                          | Description                             | Default |
|------------------------------|-----------------------------------------|---------|
| `min_bp`                     | Minimum energy (battle points) to fight | `1`     |
| `generation_cost`            | Gold cost to generate an opponent       | `13750` |
| `gold_buffer`                | Extra gold to keep in reserve           | `0`     |
| `wait_when_broke`            | Wait instead of stopping when low gold  | `true`  |
| `wait_minutes_low_energy`    | Wait time (minutes) when energy is low  | `2.5`   |
| `wait_minutes_low_resources` | Wait time (minutes) when gold is low    | `15`    |
| `max_attacks_per_npc`        | Attack cap per NPC (safety limit)       | `100`   |
| `attack_delay`               | Seconds between attack hits             | `1.0`   |
| `between_fight_delay`        | Seconds between fights                  | `5`     |
| `max_wins`                   | Stop after N wins (`0` = unlimited)     | `0`     |

### Quest Runner (`quest` block)

| Key                            | Description                                        | Default   |
|--------------------------------|----------------------------------------------------|-----------|
| `delay_between_steps_min/max`  | Delay between steps within a single quest          | `2` / `4` |
| `delay_between_quests_min/max` | Delay after a quest fully completes                | `3` / `6` |
| `qp_poll_interval`             | Seconds between checks when quest points are empty | `60`      |
| `error_retry_delay`            | Wait seconds on error before retrying              | `10`      |

---

## Example Output

### Travel Bot

```
============================================================
[OK] Travel #142 completed
  You stumble upon a hidden treasure...
  EXP  : +2,523  (Session: 456,789)
  Gold : +892    (Session: 125,340 | Current: 2,614,010)
  [Elite] Shadowblade Dagger
  Cooldown: 5.2s
============================================================
Next travel in: 00:16
```

### Travel Bot - Ctrl+C Summary

```
============================================================
STOPPING BOT (User requested)
============================================================
Uptime #1: 1h 23m
Total Uptime: 1h 23m
Travels: 312
Total EXP: 1,234,567
Total Gold: 98,210
Total Items: 14
CAPTCHAs Solved: 2
NPC Battles: 18
Materials Gathered: 9
   Iron Ore: x5
   Leather: x4
Errors Recovered: 0
============================================================
Bot stopped gracefully. Goodbye!
```

### Battle Arena Bot

```
------------------------------------------------------------
[Fight #12]  Total wins: 11
------------------------------------------------------------
  Gold in hand    : 2,600,260
  Generation cost : 13,750 gold per fight
  Fights afford   : 189 fights possible
  Energy          : 3 available (need 1)

  Generating opponent...
  Opponent: Lunar Warrior (Lvl 1,550)
     STR: 720  |  DEF: 1,572  |  HP: 5,769

  Hit #  1  |  Dealt: 6,894  |  Enemy HP: 0 (0%)  |  Your HP: 7,815
  [WIN] Victory after 1 attacks!
  EXP: +17,723
  Next fight in 5.1s...
```

### Quest Runner - Ctrl+C Summary

```
============================================================
Quest Runner stopped.
============================================================
  Quests fully completed : 2
  Quest steps done       : 67
  Total EXP              : 345,210
  Total Gold             : 12,430
------------------------------------------------------------
  Quest Progress:
   [OK] Investigate the missing sheep: 10/10 done, completed
   [OK] The case of the missing ring: 53/53 done, completed
   [->] Play SimpleMMO: 4/101 done, 97 left
============================================================
```

---

## Project Structure

```
simplemmo_bot.py         Core bot: login, travel, NPC attack, material gather
run_24_7.py              24/7 AFK travel loop with stats and break system
battle_arena_bot.py      Battle Arena automation
quest_runner.py          Quest automation
auto_captcha_learner.py  CAPTCHA auto-label and auto-training system
train_captcha_model.py   Fine-tune CLIP on collected labels
config.json              All settings (shared by all bots)
requirements.txt         Python dependencies
run_afk.bat              Launch AFK bot (double-click)
run_battle_arena.bat     Launch Battle Arena bot (double-click)
run_quest.bat            Launch Quest Runner (double-click)
captcha_learning/        Saved CAPTCHA attempt images, labels, and stats
models/                  Fine-tuned CAPTCHA model (generated after training)
```

---

## Logging

| File                                   | Contents                                |
|----------------------------------------|-----------------------------------------|
| `simplemmo_bot.log`                    | Travel, NPC, and material gather events |
| `afk_24x7.log`                         | 24/7 AFK session events                 |
| `quest_runner.log`                     | Quest step and completion events        |
| `battle_arena.log`                     | Arena fight events                      |
| `captcha_learning/learning_stats.json` | CAPTCHA attempt counts, training runs   |

To see raw API responses in the console, set `"debug_mode": true` in `config.json`.

---

## Guides

| Guide                                            | Topic                       |
|--------------------------------------------------|-----------------------------|
| [SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md) | OAuth/Google login setup    |
| [AUTO_FALLBACK_GUIDE.md](AUTO_FALLBACK_GUIDE.md) | Session auto-recovery       |
| [AUTO_LEARNING_GUIDE.md](AUTO_LEARNING_GUIDE.md) | CAPTCHA self-improvement    |
| [CAPTCHA_SETUP.md](CAPTCHA_SETUP.md)             | CAPTCHA AI dependencies     |
| [QUEST_AUTOMATION.md](QUEST_AUTOMATION.md)       | Quest runner details        |
| [TROUBLESHOOTING_403.md](TROUBLESHOOTING_403.md) | Fixing 403 / session issues |

---

## License

Developer/testing tool. Use responsibly and only on accounts you own.
