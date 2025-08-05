#!/usr/bin/env python3
"""
Test script to test the sportIds parameter properly
"""

import requests
import json

def test_sport_ids_param():
    base_url = "https://api.sx.bet"
    
    # Test different sportIds parameters
    tests = [
        {"sportIds": "3"},  # Baseball only
        {"sportIds": "1"},  # Basketball only  
        {"sportIds": "5"},  # Soccer only
        {"sportIds": "1,3,5"},  # Basketball, Baseball, Soccer
        {"sportIds": "3,6,8"},  # Baseball, Tennis, Football
        {"pageSize": "100"},  # Try to get more results
        {"sportIds": "3", "pageSize": "50"},  # Baseball with page size
    ]
    
    for i, params in enumerate(tests):
        print(f"\n--- Test {i+1}: {params} ---")
        
        response = requests.get(f"{base_url}/markets/active", params=params)
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            markets_data = data.get('data', {})
            if isinstance(markets_data, dict):
                markets = markets_data.get('markets', [])
                next_key = markets_data.get('nextKey')
            else:
                markets = markets_data if isinstance(markets_data, list) else []
                next_key = None
            
            print(f"Markets returned: {len(markets)}")
            if next_key:
                print(f"Next key: {next_key}")
            
            if markets:
                # Count by sport
                sport_counts = {}
                for market in markets:
                    sport_id = market.get('sportId')
                    sport_label = market.get('sportLabel', f'Sport {sport_id}')
                    if sport_id not in sport_counts:
                        sport_counts[sport_id] = {'count': 0, 'label': sport_label}
                    sport_counts[sport_id]['count'] += 1
                
                print("Sport distribution:")
                for sport_id, info in sport_counts.items():
                    print(f"  Sport ID {sport_id} ({info['label']}): {info['count']} markets")
                
                # Show first few markets as samples
                print("Sample markets:")
                for j, market in enumerate(markets[:3]):
                    market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
                    fixture = f"{market.get('teamOneName', 'Unknown')} vs {market.get('teamTwoName', 'Unknown')}"
                    sport = market.get('sportLabel', 'Unknown')
                    print(f"  {j+1}. {market_name} - {fixture} ({sport})")
        else:
            print(f"Error: {response.text[:200]}...")

if __name__ == "__main__":
    test_sport_ids_param() 