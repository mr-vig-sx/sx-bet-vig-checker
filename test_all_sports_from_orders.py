#!/usr/bin/env python3
"""
Test script to check what sports exist by looking at all orders
"""

import requests
import json

def test_all_sports_from_orders():
    base_url = "https://api.sx.bet"
    
    # Get all orders to see what markets exist
    print("Fetching all orders...")
    orders_response = requests.get(f"{base_url}/orders")
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        orders = orders_data.get('data', [])
        
        print(f"Found {len(orders)} orders")
        
        # Get unique market hashes
        market_hashes = set(order.get('marketHash') for order in orders)
        print(f"Unique market hashes: {len(market_hashes)}")
        
        # Get active markets to map hashes to sports
        print(f"\nFetching active markets to map sports...")
        markets_response = requests.get(f"{base_url}/markets/active")
        if markets_response.status_code == 200:
            markets_data = markets_response.json()
            markets_data_nested = markets_data.get('data', {})
            if isinstance(markets_data_nested, dict):
                active_markets = markets_data_nested.get('markets', [])
            else:
                active_markets = markets_data_nested if isinstance(markets_data_nested, list) else []
            
            # Create a mapping from market hash to sport
            market_to_sport = {}
            for market in active_markets:
                market_hash = market.get('marketHash')
                sport_id = market.get('sportId')
                sport_label = market.get('sportLabel', f'Sport {sport_id}')
                if market_hash:
                    market_to_sport[market_hash] = {'sport_id': sport_id, 'sport_label': sport_label}
            
            # Check which market hashes from orders are in active markets
            active_market_hashes = set(market_to_sport.keys())
            overlap = market_hashes.intersection(active_market_hashes)
            
            print(f"Market hashes in orders that are also active: {len(overlap)}")
            print(f"Market hashes in orders but not active: {len(market_hashes - active_market_hashes)}")
            
            # Show sport distribution for active markets that have orders
            sport_counts = {}
            for market_hash in overlap:
                sport_info = market_to_sport[market_hash]
                sport_id = sport_info['sport_id']
                sport_label = sport_info['sport_label']
                if sport_id not in sport_counts:
                    sport_counts[sport_id] = {'count': 0, 'label': sport_label}
                sport_counts[sport_id]['count'] += 1
            
            print(f"\nSport distribution for markets with orders:")
            for sport_id, info in sport_counts.items():
                print(f"  Sport ID {sport_id} ({info['label']}): {info['count']} markets")
            
            # Show some sample market hashes that are not active
            inactive_hashes = list(market_hashes - active_market_hashes)[:5]
            print(f"\nSample inactive market hashes:")
            for hash_val in inactive_hashes:
                print(f"  {hash_val}")
        else:
            print(f"Error fetching active markets: {markets_response.status_code}")
    else:
        print(f"Error fetching orders: {orders_response.status_code}")

if __name__ == "__main__":
    test_all_sports_from_orders() 