# Automatic Login Fallback Guide

## What is Auto-Fallback?

The bot can automatically recover from expired session tokens by re-authenticating with email/password - **no manual intervention needed!**

## How It Works

### Normal Flow (Session Token Only)
```
1. Bot uses session token ✓
2. Travel actions work ✓
3. Session expires after X hours ✗
4. Bot stops with "Session expired" error ✗
5. You manually get new tokens ✗
6. Restart bot manually ✗
```

### Auto-Fallback Flow (Hybrid Setup)
```
1. Bot uses session token ✓
2. Travel actions work ✓
3. Session expires after X hours ✗
4. Bot detects HTTP 403 ✓
5. Bot automatically re-logins with email/password ✓
6. Bot continues automation ✓
```

## Setup

### Option 1: Email/Password Only
```json
{
  "email": "your_email@example.com",
  "password": "your_password",
  "session_token": "",
  "xsrf_token": "",
  "api_token": ""
}
```

**Pros:**
- Works for email/password accounts
- Never expires
- No need to get tokens

**Cons:**
- Slower (re-authenticates every time)
- Doesn't work for Google OAuth accounts

---

### Option 2: Session Token Only
```json
{
  "email": "",
  "password": "",
  "session_token": "eyJpdiI6Ik5hcGc...",
  "xsrf_token": "eyJpdiI6ImRjVGlO...",
  "api_token": "HkkVjzmHit2J85y..."
}
```

**Pros:**
- Works for Google OAuth accounts
- Fastest (no re-authentication)
- Uses existing session

**Cons:**
- Tokens expire after ~24 hours
- Bot stops when expired
- Need to manually refresh tokens

---

### Option 3: Hybrid (RECOMMENDED) ⭐
```json
{
  "email": "your_email@example.com",
  "password": "your_password",
  "session_token": "eyJpdiI6Ik5hcGc...",
  "xsrf_token": "eyJpdiI6ImRjVGlO...",
  "api_token": "HkkVjzmHit2J85y..."
}
```

**Pros:**
- ✅ Fast (uses session token first)
- ✅ Reliable (falls back to email/password)
- ✅ Works for Google OAuth (with fallback)
- ✅ No manual intervention needed
- ✅ Perfect for long-running automation

**Cons:**
- None! This is the best approach

## How to Set Up Hybrid Mode

### Step 1: Get Your Session Tokens
Follow [SESSION_TOKEN_GUIDE.md](SESSION_TOKEN_GUIDE.md) to get:
- `session_token` (laravelsession cookie)
- `xsrf_token` (XSRF-TOKEN cookie)
- `api_token` (from page meta tag)

### Step 2: Add Email/Password
Even if you use Google login, SimpleMMO may have created an account with your Google email. Try:
- Email: Your Google email address
- Password: If you don't know it, reset it on SimpleMMO

### Step 3: Configure config.json
```json
{
  "base_url": "https://web.simple-mmo.com",
  
  "_option1": "Email/password for fallback",
  "email": "your_email@gmail.com",
  "password": "your_password",
  
  "_option2": "Session tokens for speed",
  "session_token": "eyJpdiI6Ik5hcGc...",
  "xsrf_token": "eyJpdiI6ImRjVGlO...",
  "api_token": "HkkVjzmHit2J85y...",
  
  "auto_solve_captcha": true,
  "travel_delay_min": 10,
  "travel_delay_max": 30
}
```

### Step 4: Test It
```bash
python quick_test.py
```

Watch the logs:
```
2026-02-23 - INFO - Using session token from config...
2026-02-23 - INFO - Successfully logged in with session token
2026-02-23 - INFO - Taking a travel step via API...
```

If session expires later:
```
2026-02-23 - ERROR - HTTP 403 - Session may have expired
2026-02-23 - INFO - Attempting to re-login with email/password...
2026-02-23 - INFO - Successfully logged in with email/password
2026-02-23 - INFO - Re-login successful, retrying travel...
2026-02-23 - INFO - Taking a travel step via API...
```

## When Auto-Fallback Triggers

The bot automatically falls back to email/password when:

1. **Initial login fails** with session token
   - Token expired
   - Token invalid
   - Wrong format

2. **During travel** (HTTP 403 error)
   - Session timed out
   - Token invalidated
   - Authentication required

3. **API errors** (403 Forbidden)
   - CSRF token mismatch
   - Session validation failed

## Security Note

⚠️ **Password Storage**

Your email and password are stored in **plain text** in `config.json`. This is for convenience but has security implications:

- ✅ Keep `config.json` private (never commit to GitHub)
- ✅ Use a unique password (not your main password)
- ✅ Consider test/secondary accounts for automation
- ❌ Don't share your config.json file

## FAQ

**Q: I use Google login, can I still use hybrid mode?**  
A: Yes! Go to SimpleMMO account settings and set/reset a password. Use your Google email as the email.

**Q: Do I need to update tokens every day?**  
A: No! With hybrid mode, the bot automatically handles expired tokens.

**Q: Will the bot stop if both methods fail?**  
A: Yes, if both session token AND email/password fail, the bot will stop with an error.

**Q: Which login method is tried first?**  
A: Session token is always tried first (faster). Email/password is only used as fallback.

**Q: Can I force email/password login?**  
A: Yes, just remove the `session_token` from config.json. The bot will always use email/password.

## Example Log Output

### Successful Session Token Login
```
2026-02-23 00:15:32 - INFO - Using session token from config...
2026-02-23 00:15:32 - INFO - Logging in with session token...
2026-02-23 00:15:33 - INFO - Successfully logged in with session token
```

### Auto-Fallback in Action
```
2026-02-23 03:45:12 - INFO - Using session token from config...
2026-02-23 03:45:12 - ERROR - Session rejected - redirected to login page
2026-02-23 03:45:12 - INFO - Session token expired - trying email/password login as fallback...
2026-02-23 03:45:12 - INFO - Fetching login page...
2026-02-23 03:45:13 - INFO - Submitting login credentials...
2026-02-23 03:45:14 - INFO - Successfully logged in with email/password
```

### Session Expires During Travel
```
2026-02-23 10:22:45 - INFO - Taking a travel step via API...
2026-02-23 10:22:46 - ERROR - HTTP 403 - Session may have expired
2026-02-23 10:22:46 - INFO - Attempting to re-login with email/password...
2026-02-23 10:22:47 - INFO - Successfully logged in with email/password
2026-02-23 10:22:47 - INFO - Re-login successful, retrying travel...
2026-02-23 10:22:48 - INFO - Travel step completed successfully
```

## Conclusion

**Hybrid mode** (session token + email/password) gives you:
- ⚡ Speed of session tokens
- 🔄 Reliability of email/password fallback
- 🤖 Fully automated recovery
- 📈 Perfect for long-running bots

No more manual token refreshes! 🎉
