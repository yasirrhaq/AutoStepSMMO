# 24/7 AFK Mode Guide

## Overview
The 24/7 AFK mode allows you to run the bot continuously for extended periods (hours/days) while following best practices to avoid detection and bans.

## Features

### 🤖 Automatic Operation
- Runs indefinitely until you stop it (Ctrl+C)
- Auto-login and session management
- Automatic CAPTCHA solving with AI
- Error recovery and auto-restart

### 🎭 Human-Like Behavior
- **Random breaks**: Takes 5-10 minute breaks every 50-100 travels
- **Variable delays**: 15-20 seconds between each travel (randomized)
- **Session refresh**: Refreshes login every 2-4 hours to prevent expiration
- **Natural patterns**: Randomizes timing to look more human

### 🛡️ Safety Features
- Automatic error recovery
- Rate limit detection and cooldown
- Session expiration handling
- Consecutive error tracking (max 5 before long pause)
- Detailed logging for troubleshooting

## Quick Start

### Option 1: Batch File (Easiest)
Double-click `run_afk.bat` in the SMMO folder.

### Option 2: Command Line
```bash
cd "F:\Research\Project\Code\Bot Project\SMMO"
python run_24_7.py
```

## Configuration

Edit `config.json` to adjust settings:

```json
{
  "travel_delay_min": 15,       // Minimum seconds between travels
  "travel_delay_max": 20,       // Maximum seconds between travels
  "auto_solve_captcha": true,   // Enable AI CAPTCHA solving
  "email": "your@email.com",    // Your login credentials
  "password": "yourpassword"
}
```

## Best Practices

### ✅ Recommended Settings
- **Delay**: 15-20 seconds (current setting) - Good balance
- **Breaks**: Enabled automatically (50-100 travels)
- **Session refresh**: Enabled automatically (2-4 hours)
- **CAPTCHA solving**: Enabled (auto)

### ⚠️ What to Avoid
- ❌ Delays under 10 seconds (triggers rate limits)
- ❌ Disabling breaks (looks suspicious)
- ❌ Running on multiple accounts from same IP
- ❌ Using VPN that frequently changes IP mid-session

### 🎯 Optimal Configuration
The current setup (15-20s delays + random breaks) gives you approximately:
- **~150-200 travels per hour**
- **~3,600-4,800 travels per 24 hours**
- Minimal CAPTCHA triggers
- Low ban risk

## Monitoring

### Real-Time Stats
The bot prints stats every 10 travels:
- ⏱️ Uptime
- ✅ Total travels completed
- 🤖 CAPTCHAs solved
- ⚠️ Errors recovered
- 📈 Travels per hour

### Logs
Check these files for detailed information:
- `afk_24x7.log` - Detailed 24/7 mode log
- `simplemmo_bot.log` - Core bot operations log

## Stopping the Bot

### Graceful Stop (Recommended)
Press **Ctrl+C** in the terminal window. The bot will:
1. Finish current action
2. Print final statistics
3. Exit cleanly

### Emergency Stop
Close the terminal window (may leave session cookies stale).

## Troubleshooting

### Bot keeps getting CAPTCHAs
- **Solution**: Increase delays to 20-30 seconds
- Edit `config.json`: `"travel_delay_min": 20, "travel_delay_max": 30`

### Session expires frequently
- **Solution**: Check your session token is fresh
- Follow `SESSION_TOKEN_GUIDE.md` to get new token

### "Too many errors" restart loop
- **Possible causes**:
  - Rate limited by server
  - IP blocked temporarily
  - Credentials invalid
- **Solution**: Wait 10-15 minutes, then restart

### Bot stops after CAPTCHA
- **Check**: `auto_solve_captcha` is `true` in config.json
- **Check**: AI libraries installed: `pip install torch transformers pillow`
- **Check**: Chrome/Chromium is installed

## Advanced: Customizing Behavior

Edit `run_24_7.py` to adjust:

### Break Frequency
```python
self.travels_before_break = random.randint(50, 100)  # Change these numbers
```

### Break Duration
```python
self.break_duration_min = 5   # Change to 3-10 minutes
self.break_duration_max = 10
```

### Session Refresh
```python
self.session_refresh_hours = random.uniform(2, 4)  # Change timing
```

## Statistics Example

After 24 hours, you might see:
```
============================================================
✓ Travel #4,253 completed
  💬 You stumble upon a hidden treasure chest...
  💫 EXP: +1,523 (Total: 456,789)
  💰 Gold: +892 (Total: 125,340)
  🎁 Items found:
     - Health Potion x3
     - Iron Sword x1 (Rare)
  ⏱️  Cooldown: 5.0s
============================================================

Next travel in: 00:17  ← Real-time countdown

📊 24/7 AFK MODE - SESSION STATS (every 10 travels)
============================================================
⏱️  Uptime: 24h 3m
✅ Travels: 4,253
💫 Total EXP: 456,789
💰 Total Gold: 125,340
🎁 Total Items: 87
🤖 CAPTCHAs Solved: 8
⚠️  Errors Recovered: 2
🔄 Bot Restarts: 0
📈 Rate: 177.2 travels/hour
📈 Rate: 19,016 EXP/hour, 5,223 gold/hour
============================================================
```

## Safety Tips

1. **Start slow**: Test with a few hours first
2. **Monitor initially**: Watch for issues in first 1-2 hours
3. **Check logs**: Review logs daily for unusual patterns
4. **Use test account**: Don't risk main account while testing
5. **Follow ToS**: Understand SimpleMMO's automation policy

## Support

If issues persist:
1. Check `afk_24x7.log` for errors
2. Review `TROUBLESHOOTING_403.md` for HTTP errors
3. Ensure all dependencies installed: `pip install -r requirements.txt`
4. Verify session tokens are fresh (see `SESSION_TOKEN_GUIDE.md`)

---

**Remember**: This is a testing tool. Use at your own risk and respect the game's terms of service.
