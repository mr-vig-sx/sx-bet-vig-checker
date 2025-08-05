#!/usr/bin/env python3
"""
Test script to check if baseball markets exist in orders but not in active markets
"""

import requests
import json

def test_baseball_in_orders():
    base_url = "https://api.sx.bet"
    
    # Get all orders first
    print("Fetching all orders...")
    orders_response = requests.get(f"{base_url}/orders")
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        orders = orders_data.get('data', [])
        
        print(f"Found {len(orders)} orders")
        
        # Get unique market hashes from orders
        market_hashes_from_orders = set(order.get('marketHash') for order in orders)
        print(f"Unique market hashes in orders: {len(market_hashes_from_orders)}")
        
        # Get active markets
        print(f"\nFetching active markets...")
        markets_response = requests.get(f"{base_url}/markets/active")
        if markets_response.status_code == 200:
            markets_data = markets_response.json()
            markets_data_nested = markets_data.get('data', {})
            if isinstance(markets_data_nested, dict):
                active_markets = markets_data_nested.get('markets', [])
            else:
                active_markets = markets_data_nested if isinstance(markets_data_nested, list) else []
            
            print(f"Active markets: {len(active_markets)}")
            
            # Create mapping from market hash to sport for active markets
            active_market_to_sport = {}
            for market in active_markets:
                market_hash = market.get('marketHash')
                sport_id = market.get('sportId')
                if market_hash:
                    active_market_to_sport[market_hash] = sport_id
            
            # Check which market hashes from orders are NOT in active markets
            active_market_hashes = set(active_market_to_sport.keys())
            inactive_market_hashes = market_hashes_from_orders - active_market_hashes
            
            print(f"Market hashes in orders but not active: {len(inactive_market_hashes)}")
            
            # Try to get sport info for some inactive markets
            print(f"\nChecking first 10 inactive market hashes...")
            for i, market_hash in enumerate(list(inactive_market_hashes)[:10]):
                print(f"  {i+1}. {market_hash}")
                
                # Try to get market info for this hash
                market_info_response = requests.get(f"{base_url}/markets/{market_hash}")
                if market_info_response.status_code == 200:
                    market_info = market_info_response.json()
                    print(f"     Market info: {json.dumps(market_info, indent=4)}")
                else:
                    print(f"     No market info available (status: {market_info_response.status_code})")
            
            # Check if there are any baseball orders
            print(f"\nChecking for baseball orders...")
            baseball_orders = []
            for order in orders:
                market_hash = order.get('marketHash')
                if market_hash in active_market_to_sport:
                    sport_id = active_market_to_sport[market_hash]
                    if sport_id == 3:  # Baseball
                        baseball_orders.append(order)
            
            print(f"Baseball orders from active markets: {len(baseball_orders)}")
            
            # Check if there are baseball orders from inactive markets
            # We can't determine sport for inactive markets without additional API calls
            print(f"\nNote: There may be baseball orders in the {len(inactive_market_hashes)} inactive markets")
            print("To check this, we would need to query each market individually")

if __name__ == "__main__":
    test_baseball_in_orders() 