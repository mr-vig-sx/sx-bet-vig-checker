#!/usr/bin/env python3
"""
Test script to check if different markets return different odds
"""

import requests
import json

def test_market_odds():
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
    
    # Test first 3 markets
    for i, market in enumerate(markets[:3]):
        market_hash = market.get('marketHash')
        market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
        
        print(f"\n--- Market {i+1}: {market_name} ---")
        print(f"Market Hash: {market_hash}")
        
        # Get orders for this market
        orders_response = requests.get(f"{base_url}/orders?market={market_hash}")
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            orders = orders_data.get('data', [])
            
            print(f"Orders found: {len(orders)}")
            
            if orders:
                # Show first order structure
                print(f"First order keys: {list(orders[0].keys())}")
                
                # Filter USDC orders
                USDC_BASE_TOKEN = "0x6629Ce1Cf35Cc1329ebB4F63202F3f197b3F050B"
                usdc_orders = [order for order in orders if order.get('baseToken') == USDC_BASE_TOKEN]
                
                print(f"USDC orders: {len(usdc_orders)}")
                
                if usdc_orders:
                    # Show sample USDC order
                    sample_order = usdc_orders[0]
                    print(f"Sample USDC order: {json.dumps(sample_order, indent=2)}")
                    
                    # Check for percentageOdds field
                    if 'percentageOdds' in sample_order:
                        print(f"Percentage odds: {sample_order['percentageOdds']}")
                    else:
                        print("No percentageOdds field found")
        else:
            print(f"Error fetching orders: {orders_response.status_code}")

if __name__ == "__main__":
    test_market_odds() 