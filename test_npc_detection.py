"""
Test script to check for NPC encounters in travel responses
"""
import json
from simplemmo_bot import SimpleMMOBot

def test_npc_detection():
    """Test NPC detection in travel responses"""
    print("="*60)
    print("NPC DETECTION TEST")
    print("="*60)
    print("\nThis will perform 1 travel and show the raw API response.")
    print("If you have an NPC on the travel page, we can see what data is returned.\n")
    
    # Initialize bot
    bot = SimpleMMOBot()
    
    # Login
    print("[Logging in...]")
    if not bot.login():
        print("❌ Login failed")
        return
    
    print("✓ Login successful!\n")
    
    # Perform one travel
    print("[Traveling once to check for NPC data...]")
    result = bot.travel()
    
    if result.get("success"):
        print("\n" + "="*60)
        print("RAW API RESPONSE:")
        print("="*60)
        
        data = result.get("data", {})
        print(json.dumps(data, indent=2))
        
        print("\n" + "="*60)
        print("PARSED RESULTS:")
        print("="*60)
        
        parsed = result.get("parsed", {})
        print(f"  NPC Encounter: {parsed.get('npc_encounter', False)}")
        print(f"  NPC ID: {parsed.get('npc_id')}")
        print(f"  NPC Name: {parsed.get('npc_name')}")
        print(f"  Message: {parsed.get('message', '')[:100]}")
        print(f"  EXP: {parsed.get('exp', 0)}")
        print(f"  Gold: {parsed.get('gold', 0)}")
        
        print("\n" + "="*60)
        print("\nLook for fields like:")
        print("  - npc_id, npcId, encounter_npc_id")
        print("  - npc_name, npcName")
        print("  - encounter, battle, npc")
        print("  - Any field indicating an NPC is present")
        print("="*60)
    else:
        print(f"\n❌ Travel failed: {result.get('error')}")

if __name__ == "__main__":
    test_npc_detection()
