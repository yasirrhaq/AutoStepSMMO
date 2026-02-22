# SimpleMMO Bot - Quick Start Guide

## 🚀 Quick Setup (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

Or use the setup script:
```bash
# Windows
setup.bat
```

### Step 2: Add Your Credentials

**Option A: Email/Password Login**

Edit `config.json`:
```json
{
  "email": "your_email@example.com",
  "password": "yourpassword",
  "session_token": ""
}
```

**Option B: Google/OAuth Login** 

If you use "Sign in with Google", see **[SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md)** for instructions on getting your session cookie.

```json
{
  "email": "",
  "password": "",
  "session_token": "your_session_cookie_here"
}
```

⚠️ **IMPORTANT**: Use ONE method only (email/password OR session_token)!

### Step 3: Run the Bot
```bash
# Quick test (recommended first time)
python test_bot.py

# Or double-click
run_test.bat
```

The bot will automatically login and start traveling!

## 📝 Quick Usage Examples

### Test Login + Single Travel
```bash
python test_bot.py
# Select: 1 (Login + Single Travel)
# Bot automatically logs in from config.json
```

### Run Auto Travel (3 iterations)
```bash
python test_bot.py
# Select: 2 (Auto Travel Test)
```

### Run Continuous Travel
```bash
python simplemmo_bot.py
# Bot auto-logins
# Select: 1 (Auto Travel)
# Enter number of iterations or leave blank
# Press Ctrl+C to stop
```

## 🛠️ Common Use Cases

### Testing Travel Mechanics
```python
from simplemmo_bot import SimpleMMOBot

bot = SimpleMMOBot()
bot.login("email@example.com", "password")

# Single travel
result = bot.travel()
print(result)
```

### Automated Travel Loop
```python
bot = SimpleMMOBot()
bot.login("email@example.com", "password")

# Run 10 travels
bot.auto_travel_loop(iterations=10)

# Or infinite (Ctrl+C to stop)
bot.auto_travel_loop()
```

## ⚙️ Customization

### Change Travel Delays
Edit `config.json`:
```json
{
  "travel_delay_min": 1,
  "travel_delay_max": 3,
  "enable_random_delays": true
}
```

### Disable Random Delays
```json
{
  "enable_random_delays": false
}
```

## 🐛 Troubleshooting

### Bot won't login
- Check email/password in config.json
- Verify you can login manually on the website
- Check `simplemmo_bot.log` for error details

### Travel actions fail
- Check if you're hitting rate limits/cooldowns
- Look at the log file for HTTP status codes
- Verify the website is accessible

### CSRF token errors
- Bot automatically handles CSRF tokens
- If failing, check website HTML structure hasn't changed
- Review logs for token extraction issues

## 📊 Monitoring

### View Logs in Real-Time
```powershell
# Windows PowerShell
Get-Content simplemmo_bot.log -Wait -Tail 20
```

### Check Current Status
The bot logs every action:
- ✓ Login successful
- ✓ Travel step completed
- Waiting X seconds before next travel
- Travel #5 successful

## 🎯 What the Bot Does

1. **Logs in** to SimpleMMO with your credentials
2. **Extracts CSRF token** from the page
3. **Clicks "Take a Step"** (sends POST to /travel)
4. **Waits** random delay (2-5 seconds by default)
5. **Repeats** until stopped or iteration limit reached

## 💡 Pro Tips

- ✅ Start with `test_bot.py` to verify everything works
- ✅ Use random delays for more natural behavior
- ✅ Monitor the log file for any errors
- ✅ Start with small iteration counts (5-10)
- ✅ Use Ctrl+C to gracefully stop the bot
- ✅ Check cooldowns - bot waits automatically

## 📞 Need Help?

1. Run `python test_bot.py` first
2. Check `simplemmo_bot.log` for errors
3. Verify config.json has correct credentials
4. Ensure Python 3.7+ and dependencies installed
5. Try manual login on website to verify credentials

## ⚡ Quick Reference

| Command | Purpose |
|---------|---------|
| `python test_bot.py` | Quick test with 1-3 travels |
| `python simplemmo_bot.py` | Full bot with options |
| `pip install -r requirements.txt` | Install dependencies |
| `Ctrl+C` | Stop the bot gracefully |

## 📁 Important Files

- **config.json** - Your credentials and settings
- **simplemmo_bot.log** - All bot activity logs
- **test_bot.py** - Quick testing script
- **simplemmo_bot.py** - Main bot script
