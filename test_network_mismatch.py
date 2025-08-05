#!/usr/bin/env python3
"""
Test script to check for network mismatch between markets and orders
"""

import requests
import json

def test_network_mismatch():
    base_url = "https://api.sx.bet"
    
    # Get metadata to check network info
    print("Fetching metadata...")
    metadata_response = requests.get(f"{base_url}/metadata")
    if metadata_response.status_code == 200:
        metadata = metadata_response.json()
        print(f"Network info: {json.dumps(metadata, indent=2)}")
    
    # Get active markets
    print("\nFetching active markets...")
    response = requests.get(f"{base_url}/markets/active")
    if response.status_code != 200:
        print(f"Error fetching markets: {response.status_code}")
        return
    
    data = response.json()
    markets_data = data.get('data', {})
    if isinstance(markets_data, dict):
        markets = markets_data.get('markets', [])
    else:
        markets = markets_data if isinstance(markets_data, list) else []
    
    print(f"Found {len(markets)} markets")
    
    # Check first few markets for network info
    print(f"\nChecking first 3 markets:")
    for i, market in enumerate(markets[:3]):
        market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
        market_hash = market.get('marketHash')
        sport_id = market.get('sportId')
        league_id = market.get('leagueId')
        
        print(f"  {i+1}. {market_name}")
        print(f"     Hash: {market_hash}")
        print(f"     Sport ID: {sport_id}")
        print(f"     League ID: {league_id}")
        print(f"     Keys: {list(market.keys())}")
        print()
    
    # Get all orders and check their market hashes
    print("Fetching all orders...")
    orders_response = requests.get(f"{base_url}/orders")
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        orders = orders_data.get('data', [])
        
        print(f"Total orders: {len(orders)}")
        
        if orders:
            # Get unique market hashes from orders
            order_market_hashes = set(order.get('marketHash') for order in orders)
            print(f"Unique market hashes in orders: {len(order_market_hashes)}")
            
            # Get unique market hashes from active markets
            active_market_hashes = set(market.get('marketHash') for market in markets)
            print(f"Unique market hashes in active markets: {len(active_market_hashes)}")
            
            # Check overlap
            overlap = active_market_hashes.intersection(order_market_hashes)
            print(f"Overlap between active markets and orders: {len(overlap)}")
            
            if overlap:
                print("✅ Found matching markets!")
                for market_hash in list(overlap)[:3]:
                    print(f"  - {market_hash}")
            else:
                print("❌ No matching markets found")
                
                # Show some sample market hashes from each
                print(f"\nSample active market hashes:")
                for i, market_hash in enumerate(list(active_market_hashes)[:3]):
                    print(f"  {i+1}. {market_hash}")
                
                print(f"\nSample order market hashes:")
                for i, market_hash in enumerate(list(order_market_hashes)[:3]):
                    print(f"  {i+1}. {market_hash}")

if __name__ == "__main__":
    test_network_mismatch() 