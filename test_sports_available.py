#!/usr/bin/env python3
"""
Test script to check what sports are available
"""

import requests
import json

def test_sports_available():
    base_url = "https://api.sx.bet"
    
    # Get all sports
    print("Fetching all sports...")
    sports_response = requests.get(f"{base_url}/sports")
    if sports_response.status_code == 200:
        sports_data = sports_response.json()
        sports = sports_data.get('data', [])
        
        print(f"Found {len(sports)} sports:")
        for sport in sports:
            sport_id = sport.get('id')
            sport_name = sport.get('name') or sport.get('sportName') or sport.get('title')
            print(f"  ID: {sport_id}, Name: {sport_name}")
    
    # Get active markets and check sport distribution
    print(f"\nFetching active markets...")
    markets_response = requests.get(f"{base_url}/markets/active")
    if markets_response.status_code == 200:
        markets_data = markets_response.json()
        markets_data_nested = markets_data.get('data', {})
        if isinstance(markets_data_nested, dict):
            markets = markets_data_nested.get('markets', [])
        else:
            markets = markets_data_nested if isinstance(markets_data_nested, list) else []
        
        print(f"Found {len(markets)} active markets")
        
        # Count markets by sport
        sport_counts = {}
        for market in markets:
            sport_id = market.get('sportId')
            sport_label = market.get('sportLabel', f'Sport {sport_id}')
            if sport_id not in sport_counts:
                sport_counts[sport_id] = {'count': 0, 'label': sport_label}
            sport_counts[sport_id]['count'] += 1
        
        print(f"\nMarket distribution by sport:")
        for sport_id, info in sport_counts.items():
            print(f"  Sport ID {sport_id} ({info['label']}): {info['count']} markets")
        
        # Show some sample markets from each sport
        print(f"\nSample markets by sport:")
        for sport_id, info in sport_counts.items():
            sport_markets = [m for m in markets if m.get('sportId') == sport_id][:3]
            print(f"\n  {info['label']} (ID: {sport_id}):")
            for market in sport_markets:
                market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
                print(f"    - {market_name}")

if __name__ == "__main__":
    test_sports_available() 