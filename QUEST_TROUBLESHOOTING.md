# Quest Automation - Troubleshooting Guide

## Current Issue

The automatic quest discovery is experiencing authentication issues with the SimpleMMO API. The quest data is loaded client-side via Alpine.js, and the API requires complex signed authentication that is session-dependent.

### What's Working

✅ **Login** - Bot successfully logs in with session tokens  
✅ **Brotli Decompression** - Server responses are properly decoded (brotli package installed)  
✅ **Quest Completion** - The perform quest API should work once we have quest IDs  
✅ **Endpoint Extraction** - Can extract signed perform URLs from the page  

### What's Not Working

❌ **Auto Quest Discovery** - Quest GET API returns 401 "unauthenticated"  
❌ **API Authentication** - Signed URLs require additional auth that's tied to Alpine.js context  

## Workaround Solution

Use **manual_quest_runner.py** to complete specific quests by ID:

### Step 1: Get Quest IDs

Open your browser and go to https://web.simple-mmo.com/quests

#### Method A: Browser Console
1. Press F12 to open Developer Tools
2. Go to Console tab
3. Type this command:
```javascript
getGameData('expedition').expeditions.map(e => ({id: e.id, title: e.title, level: e.level_required, completed: e.is_completed}))
```
4. Copy the quest IDs you want to complete

#### Method B: Network Inspector
1. Press F12 → Network tab
2. Refresh the quest page
3. Find the request to `api/quests/get`
4. Click it → Preview/Response
5. Look for the `expeditions` array
6. Copy quest IDs

### Step 2: Update manual_quest_runner.py

Edit line 15-20 in `manual_quest_runner.py`:
```python
quest_ids = [
    1,   # Quest Title Here
    5,   # Another Quest
    12,  # Etc
]
```

### Step 3: Run Manual Quest Runner

```bash
python manual_quest_runner.py
```

## Alternative: Selenium Auto-Discovery

If you want full automation, we can implement Selenium-based quest discovery:

### Pros:
- Fully automatic
- No manual quest ID entry needed
- Can see what's available and choose

### Cons:
- Requires ChromeDriver
- Slower (browser startup)
- More resource-intensive

To implement this, we would:
1. Use Selenium to load /quests page
2. Wait for Alpine.js to populate expeditions
3. Execute JavaScript to extract `getGameData('expedition').expeditions`
4. Parse and filter quests
5. Complete them

Would you like me to implement the Selenium-based auto-discovery?

## Complete Quest Data Structure

When the API works, each quest has:
```json
{
  "id": 18,
  "title": "Quest Name",
  "level_required": 90,
  "amount_to_complete": 100,
  "amount_completed": 46,
  "is_completed": false,
  "image_url": "/img/icons/quest.png"
}
```

## Next Steps

**Option 1:** Use manual quest runner (works now)
- Quick fix
- Requires copying quest IDs from browser
- No additional dependencies

**Option 2:** Implement Selenium auto-discovery
- Full automation
- Takes 1-2 hours to implement
- Requires Selenium/ChromeDriver already in project

**Option 3:** Debug the API auth further
- Investigate Laravel signed URL validation
- Might need to reverse-engineer Alpine.js data flow
- Time-consuming

Let me know which approach you prefer!
