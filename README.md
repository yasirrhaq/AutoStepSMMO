# SimpleMMO Automation Suite

A developer/testing toolkit for automating SimpleMMO. Four fully-featured bots, one shared config file.

> WARNING: For developer/testing use only. Use responsibly and only on accounts you own.

---

## 🆕 What's New (February 2026)

### Web Dashboard (Coming Soon!)
Monitor your bots from anywhere with a real-time web dashboard!

- **📊 Real-time Stats** - View all bot stats live (EXP, Gold, Items, Uptime)
- **📈 Historical Charts** - Track performance over time (24h+ history)
- **📱 Mobile Friendly** - Access from phone, tablet, or desktop
- **🔔 Error Alerts** - Get notified when bots encounter issues
- **🌐 Hostinger Compatible** - Works on shared hosting (Laravel + React)

**Architecture:**
```
Python Bots (Your PC) → HTTP API → Laravel Dashboard (Hostinger) → Web/Mobile UI
```

**Getting Started:**
1. See [`docs/`](docs/) folder for complete documentation
2. Start with [`docs/PRD_DASHBOARD.md`](docs/PRD_DASHBOARD.md) for requirements
3. Follow [`docs/DASHBOARD_IMPLEMENTATION_GUIDE.md`](docs/DASHBOARD_IMPLEMENTATION_GUIDE.md) for step-by-step setup

**Quick Files:**
- [`stats_reporter.py`](stats_reporter.py) - Python module for sending stats to dashboard
- [`docs/`](docs/) - Complete dashboard documentation

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

- **Enter**  restarts the bot automatically
- **C**  closes the window

---

## Features

### 24/7 AFK Travel Bot (`run_24_7.py`)

- Walks travel steps continuously with human-like random delays (configurable, default 1518 s)
- Auto-battles NPCs encountered during travel using signed-URL attack flow
- Auto-gathers materials using signed-URL extraction from page HTML
- Item drop display with rarity parsing: Common, Uncommon, Rare, Elite, Epic, Legendary, Mythic, Celestial
- Random breaks every 50100 travels; automatic session refresh every 24 hours
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
- **Interactive startup prompt:**
  - Enter a number to run that many fights then stop
  - If a number is entered, asked whether to continue with unlimited battles after reaching the target
  - Press Enter to run unlimited battles immediately
- Clean Ctrl+C stop with full session stats printed before exit

### Quest Runner Bot (`quest_runner.py`)

- Fetches all available quests with level requirements, remaining steps, and **success rate**
- Extracts signed quest API endpoints from page HTML on each run
- Tracks quest points and polls for regeneration when exhausted
- Per-quest step tracking: knows how many steps done vs. remaining per quest

**Interactive startup prompt:**

1. Displays the full list of incomplete quests with level, remaining steps, and success rate (colour-coded green = 100%, red = <100%)
2. **Multi-quest queue**  add as many quests as you want to run in order before the normal loop:
   - Type the list number to pick a quest, enter how many times to run it, repeat
   - Press Enter on an empty slot to stop adding and proceed
3. **Direction choice** for the automatic loop after the queue:
   - `L` (default)  lowest level first
   - `H`  highest level first
   - In both modes the bot **skips quests below 100% success rate**, scanning toward the chosen end until it finds a 100% quest; falls back to the nearest available quest only if none are 100%

- Clean Ctrl+C stop with detailed summary:
  - Quests fully completed
  - Total attempts performed
  - Total EXP and Gold earned
  - Per-quest progress breakdown (attempts done / total, remaining)
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
============================================================
  SimpleMMO BATTLE ARENA BOT
============================================================
  Min energy required: 1
  Generation cost    : 13,750 gold (fetched live each fight)
  Wait when broke    : True
  Attack delay       : 1.0s
============================================================

  How many fights to run? (Enter = unlimited): 125
  Continue with unlimited battles after 125 fights? (y/N): y
  -> Will run 125 fights, then continue indefinitely.

[Logging in...]
```

```
------------------------------------------------------------
  Fight #125  |  Total wins: 115
------------------------------------------------------------
  ...

============================================================
  Target of 125 fights reached — continuing indefinitely.
============================================================

  Fight #126  |  Total wins: 116
------------------------------------------------------------
  ...
```

### Quest Runner - Startup Prompt

```
============================================================
  Available Incomplete Quests
============================================================
    1. [Lvl     50] Investigate the missing sheep  (remaining: 10)   [100%]
    2. [Lvl    100] Read a scroll about Mahol       (remaining: 212)  [100%]
    3. [Lvl    200] The Cursed Dungeon              (remaining: 50)   [60%]
    4. [Lvl    300] Dragon's Lair                   (remaining: 30)   [100%]
============================================================

  You can queue multiple quests to run in order before the normal loop.
  For each slot: type a NUMBER to pick a quest, or press Enter to stop
  adding quests and start the bot.

  Quest #1 (Enter to start bot): 2
  How many times to run 'Read a scroll about Mahol'? (remaining: 212, Enter = 1): 50
  -> Added: 'Read a scroll about Mahol' x50

  Quest #2 (Enter to start bot): 1
  How many times to run 'Investigate the missing sheep'? (remaining: 10, Enter = 1): 10
  -> Added: 'Investigate the missing sheep' x10

  Quest #3 (Enter to start bot):

  Queue:
    1. Read a scroll about Mahol  x50
    2. Investigate the missing sheep  x10
  After the queue finishes, the bot will continue with the
  auto-loop using the direction you choose below.

  Normal loop direction (after queue, or immediately if no queue):
    [L] Lowest level first - skips quests below 100% success rate
    [H] Highest level first - skips quests below 100% success rate,
        works downward looking for the highest 100% quest

  Direction (L/H, Enter = lowest): h
  -> Highest-level 100% quests first, working downward.
```

### Quest Runner - Ctrl+C Summary

```
============================================================
Quest Runner stopped.
============================================================
  Quests fully completed : 2
  Total attempts         : 67
  Total EXP              : 345,210
  Total Gold             : 12,430
------------------------------------------------------------
  Quest Progress:
   [OK] Read a scroll about Mahol: 50/50 done, completed
   [OK] Investigate the missing sheep: 10/10 done, completed
   [->] Dragon's Lair: 7/30 done, 23 left
============================================================
```

---

## Project Structure

```
simplemmo_bot.py              Core bot: login, travel, NPC attack, material gather
run_24_7.py                   24/7 AFK travel loop with stats and break system
battle_arena_bot.py           Battle Arena automation
quest_runner.py               Quest automation
stats_reporter.py             Dashboard integration - sends stats to web dashboard
auto_captcha_learner.py       CAPTCHA auto-label and auto-training system
train_captcha_model.py        Fine-tune CLIP on collected labels
config.json                   All settings (shared by all bots)
requirements.txt              Python dependencies
run_afk.bat                   Launch AFK bot (double-click)
run_battle_arena.bat          Launch Battle Arena bot (double-click)
run_quest.bat                 Launch Quest Runner (double-click)
captcha_learning/             Saved CAPTCHA attempt images, labels, and stats
models/                       Fine-tuned CAPTCHA model (generated after training)
docs/                         Web dashboard documentation (NEW!)
  ├── PRD_DASHBOARD.md        Product requirements for web dashboard
  ├── DASHBOARD_IMPLEMENTATION_GUIDE.md  Step-by-step setup guide
  ├── DASHBOARD_QUICKREF.md   Quick reference guide
  └── README.md               Documentation index
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
