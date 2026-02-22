# How to Use the Bot with Google Login (OAuth)

If you signed in to SimpleMMO using **"Sign in with Google"**, you can't use email/password. Instead, you need to copy **TWO cookies** from your browser.

## 📋 Step-by-Step Guide

### Step 1: Login to SimpleMMO in your browser
1. Open https://web.simple-mmo.com
2. Sign in with Google (or however you normally login)
3. Make sure you're successfully logged in

### Step 2: Get Your Session Cookies ⚠️ **BOTH REQUIRED**

#### **Using Browser DevTools (Chrome/Edge)** ⭐ RECOMMENDED

1. **Press F12** to open Developer Tools
2. Click on **"Application"** tab (or "Storage" in Firefox)
3. In the left sidebar, expand **"Cookies"**
4. Click on **"https://web.simple-mmo.com"**
5. Find **TWO** cookies:
   - **`laravelsession`** - Main session cookie (very long ~200+ chars)
   - **`XSRF-TOKEN`** - Security token (shorter, ~40 chars)
6. **Double-click the "Value" column** for each and copy them

⚠️ **CRITICAL**: You MUST copy BOTH cookies for the bot to work!

### Step 3: Add BOTH to config.json

Edit your `config.json`:

```json
{
  "base_url": "https://web.simple-mmo.com",
  
  "session_token": "paste_laravelsession_value_here",
  "xsrf_token": "paste_XSRF-TOKEN_value_here",
  
  "email": "",
  "password": "",
  
  "travel_delay_min": 2,
  "travel_delay_max": 5,
  "enable_random_delays": true
}
```

**Important:**
- Leave `email` and `password` blank
- Paste `laravelsession` value in `session_token`
- Paste `XSRF-TOKEN` value in `xsrf_token`
- Keep the quotes around them

### Step 4: Run the Bot

```bash
python test_bot.py
```

or for auto-run (no prompts):

```bash
python quick_test.py
```

The bot will use your session tokens instead of logging in!

## 🔄 When Session Expires

Session tokens expire after some time (usually hours to a few days). When that happens:

1. You'll see error: "HTTP 403 Forbidden" or "Session rejected"
2. Simply repeat Steps 1-3 to get fresh tokens (BOTH cookies)
3. Update `config.json` with the new values

## 📝 Example config.json

```json
{
  "base_url": "https://web.simple-mmo.com",
  "session_token": "eyJpdiI6IkRZT1RqOXhNK3pTUzVoQzJINnF0dz09IiwidiI6IkZKTjJqOXhNK3pTUzVINnF0dz09",
  "xsrf_token": "W8xKdF2Q3R4T5Y6U7I8O9P0A1S2D3F4G5H6J7K8L",
  "email": "",
  "password": "",
  "travel_delay_min": 2,
  "travel_delay_max": 5,
  "enable_random_delays": true
}
```

## ⚠️ Security Notes

- **Never share your session tokens** - they're like passwords!
- Session tokens give full access to your account
- Keep `config.json` private and secure
- Don't commit `config.json` to git/GitHub

## 🐛 Troubleshooting

### "HTTP 403 Forbidden"
**Most common cause**: Missing the `xsrf_token`
- Go back and copy BOTH cookies (laravelsession AND XSRF-TOKEN)
- Make sure both are in your config.json
- Get fresh cookies if they're old

### "Session rejected - redirected to login"
- Your tokens have expired
- Get fresh tokens from your browser (Steps 1-3)
- Make sure you're still logged in to SimpleMMO in your browser

### "Failed to extract CSRF token"
- Usually not a problem - bot will try anyway
- If travel continues to fail, get fresh session tokens

### "No session token or credentials provided"
- Check that you added BOTH `session_token` AND `xsrf_token` to config.json
- Make sure they're spelled correctly
- Ensure the values are in quotes

### Still not working?
- Make sure you copied BOTH cookies (laravelsession AND XSRF-TOKEN)
- Try logging out and back in with Google, then get fresh tokens
- Check `simplemmo_bot.log` for detailed errors
- Ensure you're still logged in to SimpleMMO in your browser while running the bot

## 🎯 Quick Checklist

- [ ] Logged into SimpleMMO with Google
- [ ] Opened DevTools (F12)
- [ ] Found session cookie in Application > Cookies
- [ ] Copied the entire cookie value
- [ ] Pasted into config.json under `session_token`
- [ ] Left email and password blank
- [ ] Ran `python test_bot.py`
- [ ] Bot logged in successfully!
