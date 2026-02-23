# SimpleMMO Auto-Quest Runner

Automatically completes quests (expeditions) in SimpleMMO in order from lowest to highest level.

## Features

- ✅ Automatically fetches all available quests
- ✅ Filters incomplete quests and sorts by level requirement
- ✅ Completes quests in order (lowest level first)
- ✅ Tracks progress and remaining completions
- ✅ Moves to next quest after current one is complete
- ✅ Continues until all eligible quests are completed
- ✅ Detailed logging of gold and EXP earned

## Quick Start

### 1. Configure Your Bot

Make sure your `config.json` has login credentials:

**Option A: Session Token (Recommended for Google/OAuth login)**
```json
{
  "session_token": "your_laravel_session_token",
  "xsrf_token": "your_xsrf_token"
}
```

**Option B: Email/Password**
```json
{
  "email": "your@email.com",
  "password": "your_password"
}
```

### 2. Run the Bot

Simply double-click `run_quest.bat` or run from command line:

```bash
run_quest.bat
```

Or run directly with Python:

```bash
python quest_runner.py
```

## How It Works

### Quest Selection Logic

1. **Fetches All Quests**: Loads the `/quests` page and extracts all available expeditions
2. **Filters Incomplete**: Only considers quests that haven't been completed
3. **Sorts by Level**: Orders quests from lowest to highest level requirement
4. **Sequential Completion**: Works on one quest at a time until complete
5. **Auto-Progress**: Moves to next quest automatically

### Quest Execution Flow

```
For each incomplete quest:
  1. Display quest info (title, level, remaining)
  2. Perform quest action via API
  3. Track rewards (gold, EXP)
  4. Wait between attempts (2-4 seconds)
  5. Repeat until quest is complete
  6. Move to next quest
```

### Example Output

```
============================================================
Current Quest: Save a cat
Level Requirement: 1
Remaining: 50
============================================================

Attempt 1 - Performing quest...
✓ Quest result - Status: success
Message: You rescued the cat from the tree!
💰 Earned: 10 gold
⭐ Earned: 5 EXP
Quest progress: 49 remaining

Waiting 2.3s before next attempt...

[... continues until quest is complete ...]

🎉 Quest Completed!
Total quests completed this session: 1
Total gold earned: 500
Total EXP earned: 250

Waiting 4.1s before next quest...
```

## Configuration Options

You can customize delays in `config.json`:

```json
{
  "quest_delay_min": 2,
  "quest_delay_max": 4,
  "enable_random_delays": true
}
```

- **quest_delay_min**: Minimum seconds between quest attempts (default: 2)
- **quest_delay_max**: Maximum seconds between quest attempts (default: 4)
- **enable_random_delays**: Use random delays within range (default: true)

## Quest API Details

### Endpoint
```
POST https://web.simple-mmo.com/api/quests/perform
```

### Parameters
- **expires**: Timestamp for signature expiration
- **signature**: Authentication signature for the request
- **expedition_id**: ID of the quest/expedition to perform

### Response Format
```json
{
  "status": "success",
  "message": "Quest completion message",
  "gold": 480,
  "gold_amount_before_guild_tax": 564,
  "experience": 2458,
  "rewards": "Reward summary",
  "looted_items": [],
  "expedition": {
    "id": 18,
    "title": "Quest title",
    "level_required": 90,
    ...
  }
}
```

## Quest Parsing

The bot extracts quest data from the `/quests` page HTML:

### Data Sources

1. **Alpine.js Data**: Attempts to extract expedition array from JavaScript
2. **HTML Structure**: Parses quest buttons if JavaScript extraction fails
3. **API Parameters**: Extracts `expires` and `signature` from page

### Extracted Quest Data

```python
{
  'id': 18,                          # Expedition ID
  'title': 'Quest title',             # Quest name
  'level_required': 90,               # Minimum level
  'is_completed': False,              # Completion status
  'remaining': 96,                    # Times left to complete
  'image_url': '/img/icons/...',      # Quest icon
  'api_params': {                     # API authentication
    'expires': '1771925047',
    'signature': '4728751d3a72b...'
  }
}
```

## Logs

Quest activity is logged to `quest_runner.log`:

```
2026-02-23 10:30:15 - INFO - Fetching available quests...
2026-02-23 10:30:16 - INFO - Successfully parsed 60 quests
2026-02-23 10:30:16 - INFO - Found 45 incomplete quests
2026-02-23 10:30:16 - INFO -   - Save a cat (Level 1, 50 left)
2026-02-23 10:30:16 - INFO -   - Protect a farmer (Level 3, 48 left)
...
```

## Troubleshooting

### No Quests Found

**Problem**: Bot says "No more incomplete quests available!"

**Solutions**:
1. Check if you've already completed all quests
2. Verify your level meets quest requirements
3. Check if session is still active

### Session Expired Error

**Problem**: "HTTP 403 - Session may have expired"

**Solutions**:
1. Get fresh session tokens from your browser
2. Update `session_token` and `xsrf_token` in `config.json`
3. Or use email/password login instead

### Quest Fails Repeatedly

**Problem**: Quest keeps failing with errors

**Solutions**:
1. Check `quest_runner.log` for detailed error messages
2. Verify quest is available (not time-limited or special)
3. Ensure cooldowns are not active
4. Try refreshing session tokens

### Rate Limited

**Problem**: "Rate limited / Cooldown"

**Solutions**:
1. Bot will automatically wait 30 seconds
2. Increase delays: set `quest_delay_min` to 3-5 seconds
3. Check if there's a cooldown on the quest

## Advanced Usage

### Run Specific Number of Quests

Modify `quest_runner.py` main function:

```python
# Complete only 5 quests then stop
bot.auto_quest_loop(max_quests=5)
```

### Custom Quest Filter

Add custom filtering in `get_incomplete_quests()`:

```python
# Only quests under level 100
incomplete = [q for q in all_quests 
              if not q.get('is_completed', False) 
              and q.get('level_required', 0) <= 100]
```

## Integration with Other Bots

The quest runner can be combined with other automation:

```python
from quest_runner import QuestRunner
from simplemmo_bot import SimpleMMOBot

# Run quests, then travel
quest_bot = QuestRunner()
quest_bot.login_with_session_token(token, xsrf)
quest_bot.auto_quest_loop(max_quests=3)

# Continue with travel bot
travel_bot = SimpleMMOBot()
travel_bot.session = quest_bot.session  # Re-use session
travel_bot.auto_travel_loop(iterations=10)
```

## Safety Features

- ✅ Random delays between actions (2-4 seconds default)
- ✅ Respects rate limiting (auto-waits 30s)
- ✅ Session expiry detection
- ✅ Detailed error logging
- ✅ Graceful shutdown on Ctrl+C

## Files Created

- `quest_runner.py` - Main quest automation script
- `run_quest.bat` - Windows launcher script
- `quest_runner.log` - Detailed activity log
- `QUEST_AUTOMATION.md` - This documentation

## Support

For issues or questions:
1. Check `quest_runner.log` for detailed errors
2. Verify your `config.json` settings
3. Ensure you're logged in with valid credentials
4. Check if the quest page structure has changed

## Version History

### v1.0.0 (2026-02-23)
- Initial release
- Automatic quest detection and completion
- Level-based quest ordering
- Reward tracking
- Session management
