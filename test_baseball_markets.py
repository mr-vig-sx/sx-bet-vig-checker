#!/usr/bin/env python3
"""
Test script to check for baseball markets and other sports
"""

import requests
import json

def test_baseball_markets():
    base_url = "https://api.sx.bet"
    
    # Get active markets
    print("Fetching active markets...")
    response = requests.get(f"{base_url}/markets/active")
    if response.status_code == 200:
        data = response.json()
        markets_data = data.get('data', {})
        if isinstance(markets_data, dict):
            markets = markets_data.get('markets', [])
        else:
            markets = markets_data if isinstance(markets_data, list) else []
        
        print(f"Found {len(markets)} active markets")
        
        # Count markets by sport ID
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
        
        # Check for baseball markets specifically
        baseball_markets = [m for m in markets if m.get('sportId') == 3]
        print(f"\nBaseball markets found: {len(baseball_markets)}")
        
        if baseball_markets:
            print("Sample baseball markets:")
            for i, market in enumerate(baseball_markets[:5]):
                market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
                fixture = f"{market.get('teamOneName', 'Unknown')} vs {market.get('teamTwoName', 'Unknown')}"
                print(f"  {i+1}. {market_name} - {fixture}")
        
        # Check for other major sports
        basketball_markets = [m for m in markets if m.get('sportId') == 1]
        football_markets = [m for m in markets if m.get('sportId') == 8]
        tennis_markets = [m for m in markets if m.get('sportId') == 6]
        
        print(f"\nOther major sports:")
        print(f"  Basketball (ID 1): {len(basketball_markets)} markets")
        print(f"  Football (ID 8): {len(football_markets)} markets")
        print(f"  Tennis (ID 6): {len(tennis_markets)} markets")
        
        # Check which markets have orders
        print(f"\nChecking which markets have orders...")
        orders_response = requests.get(f"{base_url}/orders")
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            orders = orders_data.get('data', [])
            markets_with_orders = set(order.get('marketHash') for order in orders)
            
            print(f"Total orders: {len(orders)}")
            print(f"Unique markets with orders: {len(markets_with_orders)}")
            
            # Check which active markets have orders
            active_market_hashes = set(m.get('marketHash') for m in markets)
            active_markets_with_orders = active_market_hashes.intersection(markets_with_orders)
            
            print(f"Active markets with orders: {len(active_markets_with_orders)}")
            
            # Check by sport
            for sport_id in [1, 3, 5, 6, 8]:  # Basketball, Baseball, Soccer, Tennis, Football
                sport_markets = [m for m in markets if m.get('sportId') == sport_id]
                sport_market_hashes = set(m.get('marketHash') for m in sport_markets)
                sport_with_orders = sport_market_hashes.intersection(markets_with_orders)
                
                sport_label = {
                    1: "Basketball",
                    3: "Baseball", 
                    5: "Soccer",
                    6: "Tennis",
                    8: "Football"
                }.get(sport_id, f"Sport {sport_id}")
                
                print(f"  {sport_label}: {len(sport_markets)} active, {len(sport_with_orders)} with orders")

if __name__ == "__main__":
    test_baseball_markets() 