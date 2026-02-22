# SimpleMMO Automation Bot

Developer testing tool for automating travel actions in SimpleMMO.

## Features

- ✅ Email/Password authentication with CSRF token handling
- ✅ OAuth/Google Login Support with session tokens
- ✅ **Automatic login fallback** - Auto-recovers from expired sessions
- ✅ Automated travel actions ("Take a Step")
- ✅ **Real-time countdown timer** - Live MM:SS display of wait times
- ✅ **Detailed travel results** - Shows EXP, Gold, Items with running totals
- ✅ **CAPTCHA detection** - Automatically detects verification challenges
- ⚡ **CAPTCHA auto-solve** - AI-powered image recognition (OpenAI CLIP)
- 🌙 **24/7 AFK Mode** - Continuous operation with human-like breaks
- ✅ Configurable delays and randomization (15-20s recommended)
- ✅ Cooldown detection and automatic waiting
- ✅ Comprehensive logging (console + file)
- ✅ Error handling and recovery
- ✅ Session management with cookies
- 📊 **Real-time statistics** - EXP/hour, Gold/hour, success rates

📖 **Guides:**
- [AFK_24_7_GUIDE.md](AFK_24_7_GUIDE.md) - 24/7 continuous operation guide
- [AUTO_FALLBACK_GUIDE.md](AUTO_FALLBACK_GUIDE.md) - Never worry about expired tokens!
- [SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md) - OAuth/Google login setup

### ⚠️ CAPTCHA Auto-Solve Warning

The bot can optionally attempt to solve "I'm not a bot" challenges automatically using **AI vision (OpenAI CLIP)**. 

**This feature is for DEVELOPER TESTING ONLY.**

- ❌ Only use on test accounts you own
- ❌ May violate ToS if used on production accounts  
- ⚠️ Requires AI packages (torch, transformers, selenium)
- 🤖 Uses CLIP model for image recognition (~600MB download first time)
- 📖 See main README for setup details

By default, CAPTCHA auto-solve is **disabled**. The bot will stop and show manual instructions when a CAPTCHA appears.

## Installation

1. Install Python 3.7 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings in `config.json`:

**For Email/Password Login:**
```json
{
  "base_url": "https://web.simple-mmo.com",
  "email": "your_email@example.com",
  "password": "your_password",
  "session_token": "",
  "travel_delay_min": 2,
  "travel_delay_max": 5,
  "enable_random_delays": true
}
```

**For Google/OAuth Login:**

If you signed in with Google, see **[SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md)** for how to get your session cookie:
```json
{
  "base_url": "https://web.simple-mmo.com",
  "email": "",
  "password": "",
  "session_token": "your_session_cookie_value_here",
  "xsrf_token": "your_xsrf_token_here",
  "api_token": "your_api_token_here",
  "travel_delay_min": 2,
  "travel_delay_max": 5,
  "enable_random_delays": true
}
```

**Hybrid Setup (Recommended - Best Reliability):**

Use **BOTH** session token AND email/password for automatic fallback:
```json
{
  "base_url": "https://web.simple-mmo.com",
  "email": "your_email@example.com",
  "password": "your_password",
  "session_token": "your_session_cookie_value_here",
  "xsrf_token": "your_xsrf_token_here",
  "api_token": "your_api_token_here",
  "travel_delay_min": 2,
  "travel_delay_max": 5,
  "enable_random_delays": true
}
```

**How Auto-Fallback Works:**
1. Bot tries session token first (fastest, no re-authentication)
2. If session expired (HTTP 403), automatically tries email/password
3. Re-authenticates and continues - no manual intervention needed!

This is **especially useful** for long automation sessions where tokens may expire.

## Usage

### 🌙 24/7 AFK Mode (Recommended for Long Sessions)

Run the bot continuously with best practices:

**Easy Start:**
```bash
# Double-click run_afk.bat
# OR
python run_24_7.py
```

Features:
- ✅ Runs indefinitely (Ctrl+C to stop)
- ✅ Random 5-10 min breaks every 50-100 travels
- ✅ Session refresh every 2-4 hours
- ✅ Auto CAPTCHA solving
- ✅ Real-time statistics
- ✅ Automatic error recovery

**Example Output:**
```
============================================================
✓ Travel #142 completed
  💬 You stumble upon a hidden treasure...
  💫 EXP: +2,523 (Total: 456,789)
  💰 Gold: +892 (Total: 125,340)
  🎁 Items found:
     - Health Potion x3
  ⏱️  Cooldown: 5.0s
============================================================

Next travel in: 00:17  ← Real-time countdown

📊 24/7 AFK MODE - SESSION STATS (every 10 travels)
⏱️  Uptime: 2h 15m
✅ Travels: 230
💫 Total EXP: 456,789
💰 Total Gold: 125,340
🎁 Total Items: 87
📈 Rate: 102.2 travels/hour
📈 Rate: 12,644 EXP/hour, 5,502 gold/hour
```

See [AFK_24_7_GUIDE.md](AFK_24_7_GUIDE.md) for detailed setup and customization.

### Quick Test

Test the bot with 3 travels:
```bash
python quick_test.py
```

### Quick Test

Test the bot with a single travel action:
```bash
python test_bot.py
```

The bot automatically logs in using credentials from `config.json`.

### Interactive Mode

Run the bot interactively:
```bash
python simplemmo_bot.py
```

The bot auto-logins and you can choose automation mode.

### Programmatic Usage

```python
from simplemmo_bot import SimpleMMOBot

# Initialize bot (uses config.json)
bot = SimpleMMOBot("config.json")

# Login automatically from config
bot.login()

# Run auto-travel (10 iterations)
bot.auto_travel_loop(iterations=10)

# Or infinite loop (Ctrl+C to stop)
bot.auto_travel_loop()

# Single travel action
result = bot.travel()
print(result)
```

## Configuration Options

| Option | Description | Recommended |
|--------|-------------|-------------|
| `base_url` | SimpleMMO base URL | `https://web.simple-mmo.com` |
| `email` | Your account email | - |
| `password` | Your account password | - |
| `session_token` | OAuth session cookie | - |
| `xsrf_token` | CSRF token from browser | - |
| `api_token` | API token from page | - |
| `travel_delay_min` | Min seconds between travels | `15` |
| `travel_delay_max` | Max seconds between travels | `20` |
| `enable_random_delays` | Use random delays (human-like) | `true` |
| `auto_solve_captcha` | Enable AI CAPTCHA solving | `true` |
| `debug_mode` | Show raw API responses | `false` |

## How It Works

1. **Login**: Authenticates using email/password, extracts CSRF token
2. **Session**: Maintains session with cookies
3. **Travel**: POST request to `/travel` with CSRF token
4. **Parse**: Extracts results from HTML response
5. **Repeat**: Waits random delay, then repeats

## Logging

All actions are logged to:
- **Console**: Real-time output
- **simplemmo_bot.log**: Persistent file

Log includes:
- Login success/failure
- Each travel action result
- Errors and warnings
- Cooldown detections

## Error Handling

- **Cooldown Detected**: Automatically waits 60 seconds
- **Network Errors**: Logs error and continues
- **Invalid Credentials**: Fails with clear message
- **CSRF Token Issues**: Automatically refreshes token
- **Session Expired**: Automatically re-authenticates using email/password (if configured)

### Automatic Session Recovery

If you configure **both** session token AND email/password, the bot will:
1. Detect when session expires (HTTP 403)
2. Automatically re-login with email/password
3. Continue automation without stopping

This prevents interruptions during long-running sessions!

## Development Notes

### Adjusting for Your Setup

The bot uses standard HTML form submission. You may need to adjust:

1. **CSRF Token Pattern** - If your CSRF token format is different
2. **Travel Endpoint** - Currently uses `/travel` (POST)
3. **Response Parsing** - Update `_parse_travel_response()` for your needs

### Debugging

Enable verbose logging by checking `simplemmo_bot.log`:
```bash
# Windows PowerShell
Get-Content simplemmo_bot.log -Tail 20 -Wait
```

### Testing

```bash
# Test login and single travel
python test_bot.py

# Choose option 1 for quick test
# Choose option 2 for 3 travel iterations
```

## Safety Features

- ✅ Random delays between actions (2-5 seconds)
- ✅ Automatic cooldown handling
- ✅ CSRF token rotation
- ✅ Session management
- ✅ Keyboard interrupt (Ctrl+C) support

## Troubleshooting

### Login Fails
- Verify email/password in config.json
- Check if website is accessible
- Look at simplemmo_bot.log for details
- If using session_token, ensure it's fresh (not expired)

### Session Token Expired
- **Automatic recovery**: If you have email/password in config, bot will auto re-login
- **Manual fix**: Get fresh tokens from browser (see SESSION_TOKEN_GUIDE.md)
- **Best practice**: Use hybrid setup (both session token AND email/password)

### Travel Actions Fail
- Check logs for HTTP status codes
- Verify CSRF token is being extracted
- Ensure you're not rate limited
- If seeing HTTP 403: session expired, check auto-fallback is working

### CSRF Token Issues
- Bot automatically extracts and rotates tokens
- If failing, check HTML structure of login page
- Adjust `_extract_csrf_token()` patterns if needed

## Files

- `simplemmo_bot.py` - Main bot script
- `test_bot.py` - Quick test script
- `config.json` - Configuration file
- `requirements.txt` - Python dependencies
- `simplemmo_bot.log` - Generated log file

## License

Developer testing tool. Use responsibly and only for development/testing purposes.

## Features

- ✅ Email/Password or API Key authentication
- ✅ Automated travel actions
- ✅ Automated adventure actions  
- ✅ Mixed automation mode (travel + adventure)
- ✅ Configurable delays and randomization
- ✅ Cooldown detection and handling
- ✅ Comprehensive logging
- ✅ Error handling and recovery

## Installation

1. Install Python 3.7 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings in `config.json`:
```json
{
  "base_url": "https://web.simple-mmo.com",
  "api_key": "your_api_key_here",
  "email": "your_email@example.com",
  "password": "your_password",
  "travel_delay_min": 2,
  "travel_delay_max": 5,
  "adventure_delay_min": 3,
  "adventure_delay_max": 8,
  "enable_random_delays": true
}
```

## Usage

### Interactive Mode

Run the bot interactively:
```bash
python simplemmo_bot.py
```

Follow the prompts to:
1. Choose login method (email/password or API key)
2. Select automation mode
3. Configure iterations (if applicable)

### Programmatic Usage

```python
from simplemmo_bot import SimpleMMOBot

# Initialize bot
bot = SimpleMMOBot("config.json")

# Login with API key
bot.login_with_api_key("your_api_key")

# Or login with email/password
# bot.login("email@example.com", "password")

# Run auto-travel (10 iterations)
bot.auto_travel_loop(iterations=10)

# Run auto-adventure (infinite)
bot.auto_adventure_loop()

# Run mixed automation
bot.mixed_automation(travel_ratio=0.6)

# Single actions
bot.travel()
bot.adventure()
```

## Automation Modes

### 1. Auto Travel
Continuously performs travel actions with configurable delays.

### 2. Auto Adventure
Continuously performs adventure actions with configurable delays.

### 3. Mixed Mode
Randomly alternates between travel and adventure based on a configurable ratio.

### 4. Single Actions
Execute individual travel or adventure actions for testing.

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `base_url` | SimpleMMO base URL | `https://web.simple-mmo.com` |
| `api_key` | Your API key (preferred) | - |
| `email` | Account email | - |
| `password` | Account password | - |
| `travel_delay_min` | Min seconds between travels | `2` |
| `travel_delay_max` | Max seconds between travels | `5` |
| `adventure_delay_min` | Min seconds between adventures | `3` |
| `adventure_delay_max` | Max seconds between adventures | `8` |
| `enable_random_delays` | Use random delays | `true` |

## Logging

All actions are logged to:
- Console output (real-time)
- `simplemmo_bot.log` file (persistent)

Log format: `YYYY-MM-DD HH:MM:SS - LEVEL - Message`

## API Endpoints

The bot uses the following endpoints (adjust based on actual API):

- `POST /travel/step` - Perform travel action
- `POST /api/adventure/start` - Start adventure
- `GET /api/player/status` - Get player status
- `GET /api/user` - Get user info (API auth)

## Error Handling

- **Cooldown Detection**: Automatically waits when cooldowns are detected
- **Network Errors**: Retries with exponential backoff
- **Invalid Credentials**: Fails gracefully with error message
- **Rate Limiting**: Respects delays and randomization

## Development Notes

### Adjusting for Actual API

You may need to modify these sections based on your actual implementation:

1. **CSRF Token Extraction** (`_extract_csrf_token` method)
2. **API Endpoints** (update URLs to match your routes)
3. **Response Parsing** (adjust based on your API response format)
4. **Authentication Flow** (if different from standard)

### Adding New Features

To add new automation features:

```python
def new_action(self) -> Dict[str, Any]:
    """Perform a new action"""
    if not self.logged_in:
        return {"success": False, "error": "Not logged in"}
    
    url = f"{self.base_url}/api/new-action"
    try:
        response = self.session.post(url)
        response.raise_for_status()
        data = response.json()
        self.logger.info(f"New action completed: {data}")
        return {"success": True, "data": data}
    except Exception as e:
        self.logger.error(f"New action error: {e}")
        return {"success": False, "error": str(e)}
```

## Safety Features

- Random delays to mimic human behavior
- Cooldown detection and waiting
- Configurable action limits
- Graceful error handling
- Keyboard interrupt handling (Ctrl+C)

## Troubleshooting

### Login Fails
- Verify credentials in `config.json`
- Check if API endpoint URLs are correct
- Ensure network connectivity

### Actions Not Working
- Check bot logs in `simplemmo_bot.log`
- Verify API endpoints match your implementation
- Check for cooldowns or rate limits

### Cooldown Issues
- Bot automatically handles cooldowns
- Adjust delay settings if needed
- Check game mechanics for cooldown durations

## License

This is a developer testing tool. Adjust according to your needs.

## Support

For issues or questions related to the bot implementation, check the logs and adjust the configuration as needed.
