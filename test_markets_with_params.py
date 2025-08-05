#!/usr/bin/env python3
"""
Test script to try different parameters for the markets endpoint
"""

import requests
import json

def test_markets_with_params():
    base_url = "https://api.sx.bet"
    
    # Try different parameters for the markets endpoint
    params_to_try = [
        {},
        {"sportId": 3},  # Baseball
        {"sportId": 1},  # Basketball
        {"sportId": 5},  # Soccer
        {"limit": 100},
        {"limit": 200},
        {"status": "active"},
        {"liveEnabled": "true"},
        {"mainLine": "true"}
    ]
    
    for i, params in enumerate(params_to_try):
        print(f"\n--- Test {i+1}: {params} ---")
        
        response = requests.get(f"{base_url}/markets/active", params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            markets_data = data.get('data', {})
            if isinstance(markets_data, dict):
                markets = markets_data.get('markets', [])
            else:
                markets = markets_data if isinstance(markets_data, list) else []
            
            print(f"Markets returned: {len(markets)}")
            
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
                
                # Show first market as sample
                first_market = markets[0]
                print(f"Sample market: {first_market.get('outcomeOneName', 'Unknown')} vs {first_market.get('outcomeTwoName', 'Unknown')}")
                print(f"  Sport: {first_market.get('sportLabel', 'Unknown')} (ID: {first_market.get('sportId', 'Unknown')})")
                print(f"  Teams: {first_market.get('teamOneName', 'Unknown')} vs {first_market.get('teamTwoName', 'Unknown')}")
        else:
            print(f"Error: {response.text[:200]}...")

if __name__ == "__main__":
    test_markets_with_params() 