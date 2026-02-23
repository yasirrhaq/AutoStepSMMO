#!/usr/bin/env python3
"""
Manual Quest Runner - Complete specific quests by ID
Use this when API auto-discovery fails
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from quest_runner import QuestRunner

def main():
    print("="*60)
    print("SimpleMMO Manual Quest Runner")
    print("="*60)
    print()
    
    # Quest IDs to complete (update this list)
    quest_ids = [
        1,  # Replace with actual quest IDs
        2,
        3,
        # Add more quest IDs here
    ]
    
    print(f"Will complete {len(quest_ids)} quests")
    print()
    
    # Initialize runner
    runner = QuestRunner()
    
    # Login
    if not runner.login():
        print("Failed to login!")
        return
    
    print("[OK] Login successful\n")
    
    # Get perform endpoint from page
    print("Fetching perform endpoint...")
    response = runner.session.get('https://web.simple-mmo.com/quests')
    page_html = response.text
    
    endpoints = runner.extract_quest_api_endpoints(page_html)
    perform_url = endpoints.get('perform_url')
    
    if not perform_url:
        print("ERROR: Could not find perform endpoint!")
        return
    
    print(f"[OK] Found perform endpoint\n")
    
    # Complete each quest
    completed = 0
    total_gold = 0
    total_exp = 0
    
    for quest_id in quest_ids:
        print(f"\n--- Quest ID {quest_id} ---")
        
        quest_data = {
            'id': quest_id,
            'title': f'Quest {quest_id}',
            'perform_url': perform_url
        }
        
        result = runner.perform_quest(quest_data)
        
        if result.get('success'):
            completed += 1
            total_gold += result.get('gold', 0)
            total_exp += result.get('exp', 0)
            print(f"[OK] Completed!")
        else:
            print(f"[FAIL] {result.get('error', 'Unknown error')}")
        
        # Small delay between quests
        import time
        time.sleep(2)
    
    print("\n" + "="*60)
    print("Manual Quest Session Complete")
    print("="*60)
    print(f"Completed: {completed}/{len(quest_ids)}")
    print(f"Total Gold: {total_gold}")
    print(f"Total EXP: {total_exp}")
    print("="*60)

if __name__ == '__main__':
    main()
