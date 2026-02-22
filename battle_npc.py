"""
Manual NPC Battle Test
Use this when you encounter an NPC to test auto-battle
"""
import sys
from simplemmo_bot import SimpleMMOBot

def battle_npc_manual(npc_id: int):
    """Battle a specific NPC by ID"""
    print("="*60)
    print(f"NPC AUTO-BATTLE TEST")
    print("="*60)
    print(f"\nBattling NPC ID: {npc_id}")
    print("The bot will keep attacking until the battle is complete.\n")
    
    # Initialize bot
    bot = SimpleMMOBot()
    
    # Login
    print("[Logging in...]")
    if not bot.login():
        print("❌ Login failed")
        return
    
    print("✓ Login successful!\n")
    
    # Battle the NPC
    print("="*60)
    print(f"⚔️  STARTING BATTLE")
    print("="*60)
    print()
    
    result = bot.attack_npc(npc_id)
    
    print("\n" + "="*60)
    print("BATTLE RESULT")
    print("="*60)
    
    if result.get("success"):
        print("✅ VICTORY!")
        
        data = result.get("data", {})
        if isinstance(data, dict):
            attacks = data.get("attacks", 0)
            damage = data.get("damage", 0)
            exp = data.get("exp", 0)
            gold = data.get("gold", 0)
            message = data.get("message", "")
            
            if message:
                print(f"\n💬 {message}")
            if attacks > 0:
                print(f"⚔️  Total Attacks: {attacks}")
            if damage > 0:
                print(f"💥 Total Damage: {damage}")
            if exp > 0:
                print(f"💫 EXP Gained: +{exp}")
            if gold > 0:
                print(f"💰 Gold Gained: +{gold}")
    else:
        print(f"❌ DEFEAT or ERROR")
        print(f"Error: {result.get('error', 'Unknown')}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    # Check if NPC ID provided as command line argument
    if len(sys.argv) > 1:
        try:
            npc_id = int(sys.argv[1])
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid NPC ID number")
            print("\nUsage: python battle_npc.py <NPC_ID>")
            print("Example: python battle_npc.py 463753009")
            sys.exit(1)
    else:
        # Prompt for NPC ID
        print("="*60)
        print("NPC AUTO-BATTLE TEST")
        print("="*60)
        print("\nEnter the NPC ID from the URL.")
        print("Example URL: /npcs/attack/463753009")
        print("          ID: 463753009\n")
        
        npc_id_input = input("Enter NPC ID: ").strip()
        
        try:
            npc_id = int(npc_id_input)
        except ValueError:
            print(f"Error: '{npc_id_input}' is not a valid number")
            sys.exit(1)
    
    battle_npc_manual(npc_id)
    
    print("\nPress Enter to exit...")
    input()
