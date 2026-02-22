# Troubleshooting HTTP 403 (Forbidden) Errors

## What is HTTP 403?

**403 Forbidden** means the server understood your request but refuses to fulfill it. For SimpleMMO, this usually means:

1. **IP Address Blocked** - Your IP is temporarily or permanently banned
2. **Rate Limiting** - Too many requests in a short time
3. **Bot Detection** - Cloudflare/WAF detected automated behavior
4. **Account Locked** - Too many failed login attempts
5. **Session Issues** - Conflicting or invalid cookies

## Quick Diagnosis

Run the access checker:

```bash
python check_access.py
```

This will test:
- Home page access
- Login page access  
- Access with browser-like headers

### Interpreting Results

**All tests show 403:**
- Your IP address is blocked
- Solution: Wait 30+ minutes or use different network

**Only login page is 403:**
- Account may be locked or login endpoint blocked
- Solution: Use session token instead (see below)

**All tests pass:**
- Bot configuration issue
- Check your config.json credentials

## Common Causes & Solutions

### 1. Too Many Failed Logins

**Symptom:**
```
ERROR - HTTP 403 - Login page blocked
ERROR - Too many failed login attempts
```

**Solution:**
- Wait 30-60 minutes
- Verify credentials in config.json are correct
- Try logging in manually via browser first

---

### 2. Session Token Expired

**Symptom:**
```
ERROR - HTTP 403 Forbidden - Session token rejected
ERROR - Session token expired
```

**Solution A: Get Fresh Tokens**
1. Open browser, login to SimpleMMO
2. Open DevTools (F12) → Application → Cookies
3. Copy new values for:
   - `laravelsession` → session_token
   - `XSRF-TOKEN` → xsrf_token
4. Update config.json

**Solution B: Use Email/Password Instead**
```json
{
  "email": "your_email@example.com",
  "password": "your_password",
  "session_token": "",
  "xsrf_token": ""
}
```

---

### 3. IP Temporarily Banned

**Symptom:**
```
ERROR - HTTP 403 - Login page blocked
ERROR - IP temporarily banned/rate limited
```

**Solution:**
- Stop the bot immediately
- Wait 30-60 minutes
- Increase delays in config.json:
  ```json
  {
    "travel_delay_min": 10,
    "travel_delay_max": 30
  }
  ```
- Consider using VPN or different network

---

### 4. Cloudflare Bot Protection

**Symptom:**
- 403 on all requests
- Works in browser but not in bot

**Solution:**
Use **session token method** instead of email/password:

1. Login manually in browser
2. Pass Cloudflare challenge
3. Copy session cookies
4. Use in bot

This bypasses the login page entirely!

---

### 5. Auto-Fallback Failure

**Symptom:**
```
INFO - Session token expired - trying email/password login as fallback...
ERROR - HTTP 403 - Login page blocked
```

**Why it happens:**
- Session token expired
- Bot tried to fallback to email/password
- But login page is also blocked (rate limit)

**Solution:**

**Option 1: Manual Session Refresh**
1. Manually login in browser
2. Get fresh session token
3. Update config.json
4. Restart bot

**Option 2: Wait and Retry**
```bash
# Wait 30 minutes
# Then try again
python quick_test.py
```

**Option 3: Remove Auto-Fallback**
If fallback keeps triggering blocks, disable it:
```json
{
  "email": "",
  "password": "",
  "session_token": "your_token_here"
}
```
Bot will stop when session expires instead of triggering 403.

## Prevention Tips

### 1. Use Longer Delays

Avoid triggering rate limits:
```json
{
  "travel_delay_min": 15,
  "travel_delay_max": 45,
  "enable_random_delays": true
}
```

### 2. Monitor Logs

Watch for early warning signs:
```bash
# In PowerShell
Get-Content simplemmo_bot.log -Tail 20 -Wait
```

Stop bot if you see:
- Multiple HTTP 429 (rate limit)
- Multiple HTTP 403 warnings
- "Too fast" messages from API

### 3. Use Session Token Method

**Advantages:**
- ✅ Faster (no login page needed)
- ✅ Bypasses Cloudflare challenges
- ✅ Works with OAuth/Google accounts
- ✅ Longer session lifetime

**Setup:**
See [SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md)

### 4. Refresh Tokens Manually

Don't rely on auto-fallback for critical bots:

**Strategy:**
1. Get fresh session token every 12 hours
2. Update config.json
3. Restart bot

**Cron/Scheduled Task:**
```powershell
# Windows Task Scheduler
# Run every 12 hours:
cd "F:\Research\Project\Code\Bot Project\SMMO"
python update_tokens.py  # (You would create this)
```

## When Nothing Works

### Last Resort Options

**1. Contact SimpleMMO Support**
- Explain you're testing automation (if allowed)
- Ask if your IP is banned
- Request unban if mistaken

**2. Use Different Network**
- Mobile hotspot
- VPN service  
- Different internet connection
- Cloud/VPS server

**3. Fresh Account**
- Create test account
- Use for bot testing only
- Keep main account safe

**4. Manual Operation**
If automated access is blocked:
- Run bot manually from browser console
- Use browser extensions instead
- Consider if automation is appropriate

## Checking If You're Banned

### Method 1: Browser Test
1. Open browser (private/incognito mode)
2. Go to https://web.simple-mmo.com
3. Try to login

**If it works:** Bot configuration issue  
**If it fails:** IP/account banned

### Method 2: Different Device
1. Try accessing from phone (mobile data)
2. If it works on phone: Your home IP is blocked
3. If it fails on phone: Account is banned

### Method 3: Online Tools
1. Use https://isitdownrightnow.com/
2. Check SimpleMMO status
3. If site is up but you can't access: You're blocked

## Current Best Practices (2026)

Based on your error log, here's what to do:

1. **Stop the bot immediately** ✋
   ```
   Press Ctrl+C if running
   ```

2. **Run access checker** 🔍
   ```bash
   python check_access.py
   ```

3. **Wait 30 minutes** ⏰
   - Don't try to login during this time
   - Let any temp bans expire

4. **Get fresh session token** 🔑
   - Login manually in browser
   - Copy cookies (see SESSION_TOKEN_GUIDE.md)
   - Update config.json

5. **Test with single travel** 🧪
   ```bash
   python quick_test.py
   ```

6. **If working, increase delays** ⏱️
   ```json
   {
     "travel_delay_min": 20,
     "travel_delay_max": 60
   }
   ```

## FAQ

**Q: How long do 403 bans last?**  
A: Usually 30-60 minutes for rate limits. Longer for repeated violations.

**Q: Will I be permanently banned?**  
A: Unlikely for first offense. But repeated 403s may lead to permanent ban.

**Q: Can I use a VPN?**  
A: Yes, but some VPN IPs are already blacklisted. Try different locations.

**Q: Is automation allowed?**  
A: Check SimpleMMO's Terms of Service. This bot is for TESTING only.

**Q: Should I keep trying if I get 403?**  
A: **NO!** Stop immediately. Wait 30+ minutes. Repeated attempts make it worse.

**Q: Can I switch to email/password if session fails?**  
A: Yes, but if you're already getting 403, fallback will also fail. Fix the block first.

## Getting Help

If still stuck:

1. **Check the logs:**
   ```bash
   type simplemmo_bot.log
   ```

2. **Share relevant info (NO passwords!):**
   - Error messages from log
   - Output from check_access.py
   - What you tried
   - When it started failing

3. **Include config (sanitized):**
   ```json
   {
     "email": "***@gmail.com",
     "session_token": "eyJ..." // Just first few chars
   }
   ```

4. **Environment:**
   - Windows/Linux?
   - Home network or VPN?
   - How many times did you run bot?
   - When did 403 start appearing?
