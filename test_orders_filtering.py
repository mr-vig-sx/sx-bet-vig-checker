#!/usr/bin/env python3
"""
Test script to check order filtering by market hash
"""

import requests
import json

def test_orders_filtering():
    base_url = "https://api.sx.bet"
    
    # Get active markets
    print("Fetching active markets...")
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
    
    # Test first 2 markets
    for i, market in enumerate(markets[:2]):
        market_hash = market.get('marketHash')
        market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
        
        print(f"\n--- Market {i+1}: {market_name} ---")
        print(f"Market Hash: {market_hash}")
        
        # Get orders for this market
        orders_response = requests.get(f"{base_url}/orders?market={market_hash}")
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            orders = orders_data.get('data', [])
            
            print(f"Total orders returned: {len(orders)}")
            
            if orders:
                # Filter orders that actually match this market hash
                matching_orders = [order for order in orders if order.get('marketHash') == market_hash]
                print(f"Orders matching market hash: {len(matching_orders)}")
                
                if matching_orders:
                    # Show sample matching order
                    sample_order = matching_orders[0]
                    print(f"Sample matching order: {json.dumps(sample_order, indent=2)}")
                    
                    # Check for percentageOdds field
                    if 'percentageOdds' in sample_order:
                        print(f"Percentage odds: {sample_order['percentageOdds']}")
                        
                        # Convert to decimal odds
                        implied_decimal = float(sample_order['percentageOdds']) / (10 ** 20)
                        decimal_odds = 1 / implied_decimal
                        print(f"Decimal odds: {decimal_odds:.2f}")
                else:
                    print("No orders match the requested market hash!")
                    
                    # Show what market hashes we actually got
                    unique_market_hashes = set(order.get('marketHash') for order in orders[:10])
                    print(f"Sample market hashes in response: {list(unique_market_hashes)}")
        else:
            print(f"Error fetching orders: {orders_response.status_code}")

if __name__ == "__main__":
    test_orders_filtering() 