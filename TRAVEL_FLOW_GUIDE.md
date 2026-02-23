# Travel Flow: Pre-Travel vs Post-Travel Checks

## Complete Travel Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  run_24_7.py calls: self.bot.travel()                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: PRE-TRAVEL CHECKS (in simplemmo_bot.py)           │
│  ─────────────────────────────────────────────────────      │
│  1. Load /travel page (before making travel API call)       │
│  2. Check for materials on page                             │
│     └─► If found: Auto-gather → return material_gather      │
│  3. Check for NPC battles on page                           │
│     └─► If found: Auto-battle → return npc_battle           │
│  4. Check for CAPTCHA                                       │
│     └─► If found: return captcha flag                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: MAKE TRAVEL API CALL                               │
│  ─────────────────────────────                              │
│  POST to /api/travel/travel                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: PARSE TRAVEL RESULT                                │
│  ───────────────────────────                                │
│  Parse JSON response from API                               │
│  Extract: exp, gold, items, message, etc.                   │
│  Check for material_encounter in result                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: RETURN RESULT TO run_24_7.py                       │
│  ────────────────────────────────────                       │
│  Returns:                                                    │
│    - success: True/False                                    │
│    - material_gather: {} (if gathered pre-travel)           │
│    - npc_battle: {} (if battled pre-travel)                 │
│    - parsed: {exp, gold, items, material_encounter, ...}    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: run_24_7.py PROCESSES RESULT                       │
│  ─────────────────────────────────────                      │
│  1. Check material_gather (PRE-travel)                      │
│     └─► Show "🔨 MATERIAL GATHERED (Pre-Travel)"            │
│  2. Check npc_battle (PRE-travel)                           │
│     └─► Show "⚔️ NPC BATTLE COMPLETED"                      │
│  3. Check parsed.material_encounter (POST-travel)           │
│     └─► Call salvage_material() and show result             │
│  4. Show travel rewards (exp, gold, items)                  │
│  5. Wait for cooldown                                       │
│  6. Repeat from STEP 1                                      │
└─────────────────────────────────────────────────────────────┘
```

## Two Types of Material Encounters

### 1. PRE-TRAVEL Materials (Before Travel API Call)
**When:** Material is waiting on `/travel` page BEFORE you click "Take a Step"
**How Detected:** Regex search for `material_session_id` in page HTML
**Processing:** 
- simplemmo_bot.py detects it
- Auto-gathers immediately
- Returns in `material_gather` key
- run_24_7.py shows: "🔨 MATERIAL GATHERED (Pre-Travel)"

**Example Flow:**
```
1. Bot loads /travel page
2. Page shows: "You found Iron Ore! Click to gather"
3. Bot extracts: material_session_id=12345, quantity=3
4. Bot calls: salvage_material(12345, 3)
5. Material gathered ✓
6. THEN bot makes travel API call
```

### 2. POST-TRAVEL Materials (During/After Travel Step)
**When:** Material is found AS A RESULT of taking a travel step
**How Detected:** `material_encounter` in travel API response
**Processing:**
- Travel API returns the encounter data
- simplemmo_bot.py parses it into `parsed.material_encounter`
- run_24_7.py detects it and calls salvage_material()
- Shows: "🔨 [Material Name] found! Gathering..."

**Example Flow:**
```
1. Bot makes travel API call
2. API response: "You found Cherry during travel"
3. Response includes: material_session_id, material_name, quantity
4. run_24_7.py calls: salvage_material()
5. Material gathered ✓
```

## Two Types of NPC Encounters

### 1. PRE-TRAVEL NPCs (Before Travel API Call)
**When:** NPC battle is waiting on `/travel` page (bot was already redirected)
**How Detected:** Check for `/npcs/attack/` or `/npcs/battle/` in URL
**Processing:**
- simplemmo_bot.py detects redirect to NPC page
- Auto-battles if configured
- Returns in `npc_battle` key
- run_24_7.py shows: "⚔️ NPC BATTLE COMPLETED"

### 2. POST-TRAVEL NPCs (During Travel Step)
**When:** NPC is encountered AS A RESULT of taking a travel step
**How Detected:** Travel API redirects to NPC battle page
**Processing:**
- Same as pre-travel NPCs
- Bot auto-battles if configured
- Shows battle results

## Why Two Checks Are Needed

### Pre-Travel Checks MUST Happen First
If you skip pre-travel checks and immediately call the travel API:
- **Materials:** May expire or become invalid
- **NPCs:** Bot gets stuck on NPC page, can't travel
- **CAPTCHA:** Bot can't make API calls until solved

### Post-Travel Checks Handle New Events
The travel step itself can trigger new encounters:
- Walking to new location finds a material
- Random NPC spawn during travel
- Event items appear

## Implementation Status in Your Bot

### ✅ Currently Working

**simplemmo_bot.py (Lines 1584-1700):**
```python
def travel(self):
    # PRE-TRAVEL CHECKS
    travel_page = self.session.get(f"{self.base_url}/travel")
    
    # Check for materials on page
    if material_session_id found:
        gather_result = self.salvage_material(...)
        material_gather_data = gather_result
    
    # Check for NPC battles on page
    if '/npcs/attack/' in travel_page.url:
        battle_result = self.attack_npc(...)
        npc_battle_data = battle_result
    
    # THEN make travel API call
    travel_result = self.session.post('/api/travel/travel')
    
    # Return both pre-travel and post-travel data
    return {
        "material_gather": material_gather_data,
        "npc_battle": npc_battle_data,
        "parsed": parse_travel_result(travel_result)
    }
```

**run_24_7.py (Lines 208-357):**
```python
result = self.bot.travel()  # Includes pre-travel checks!

# Handle pre-travel material gathering
if result.get("material_gather"):
    # Show "PRE-TRAVEL" material gathering

# Handle pre-travel NPC battles  
if result.get("npc_battle"):
    # Show NPC battle results

# Handle post-travel material encounters
if parsed.get("material_encounter"):
    # Call salvage_material() and show results
```

### ✅ Auto-Learning Integration

**CAPTCHA solving (simplemmo_bot.py):**
- Records ALL attempts (success + failure)
- Auto-labels failures when later succeeds
- Auto-trains when 20+ labels
- Bot auto-uses improved model

**run_24_7.py shows:**
- Auto-learning status at startup
- Auto-learning activity after solving CAPTCHA
- Periodic status every 10 travels

## Material Name Display

Both systems now show the material name when gathering fails:

**Before:**
```
⚠️ Gathering failed: HTTP 403
```

**After:**
```
⚠️ Failed to gather 'Iron Ore': HTTP 403
```

This helps identify which materials are causing problems.

## Testing the Flow

To verify everything is working:

1. **Start bot:**
   ```bash
   cd SMMO
   python run_24_7.py
   ```

2. **Watch for pre-travel events:**
   ```
   🔨 MATERIAL GATHERED (Pre-Travel)
   ⚔️ NPC BATTLE COMPLETED
   ```

3. **Watch for post-travel events:**
   ```
   🔨 Iron Ore found! Gathering...
   ✅ Gathered successfully!
   ```

4. **Check auto-learning:**
   ```
   🤖 Auto-labeled 3 past failure(s) for question: Cherry
   
   🤖 CAPTCHA Auto-Learning:
      Total attempts: 45 (✅ 38, ❌ 7)
      Auto-labeled: 5 | Trainings: 0
      15 more labels until next training
   ```

## Summary

✅ **Pre-travel checks:** Already implemented in `simplemmo_bot.py`
✅ **Post-travel checks:** Already implemented in `run_24_7.py`
✅ **Auto-learning:** Fully integrated and automatic
✅ **Material names:** Shown in all error messages
✅ **Status visibility:** Shown at startup and every 10 travels

**Your bot checks for materials and NPCs BEFORE every travel step!** 🎉

The flow is:
1. Load /travel page
2. Check for materials → gather if found
3. Check for NPCs → battle if found
4. Check for CAPTCHA → solve if found
5. THEN make travel API call
6. Handle any post-travel encounters
7. Repeat

No materials or NPCs are skipped! 🚀
