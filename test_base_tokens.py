#!/usr/bin/env python3
"""
Test script to check what base tokens are actually being used
"""

import requests
import json

def test_base_tokens():
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
    
    # Test first market
    market = markets[0]
    market_hash = market.get('marketHash')
    market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
    
    print(f"\n--- Testing Market: {market_name} ---")
    print(f"Market Hash: {market_hash}")
    
    # Get orders for this market
    orders_response = requests.get(f"{base_url}/orders?market={market_hash}")
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        orders = orders_data.get('data', [])
        
        print(f"Total orders returned: {len(orders)}")
        
        if orders:
            # Check all base tokens
            base_tokens = {}
            for order in orders:
                base_token = order.get('baseToken')
                if base_token:
                    if base_token not in base_tokens:
                        base_tokens[base_token] = 0
                    base_tokens[base_token] += 1
            
            print(f"\nBase token distribution:")
            for token, count in base_tokens.items():
                print(f"  {token}: {count} orders")
            
            # Check if any orders match our market hash
            matching_orders = [order for order in orders if order.get('marketHash') == market_hash]
            print(f"\nOrders matching market hash: {len(matching_orders)}")
            
            if matching_orders:
                print(f"\nSample matching order:")
                sample_order = matching_orders[0]
                print(json.dumps(sample_order, indent=2))
                
                # Check what base token this order uses
                base_token = sample_order.get('baseToken')
                print(f"\nThis order uses base token: {base_token}")
                
                # Check if this is the USDC token we're looking for
                USDC_BASE_TOKEN = "0x6629Ce1Cf35Cc1329ebB4F63202F3f197b3F050B"
                if base_token == USDC_BASE_TOKEN:
                    print("✅ This matches our USDC base token!")
                else:
                    print("❌ This does NOT match our USDC base token")
                    print(f"Expected: {USDC_BASE_TOKEN}")
                    print(f"Found:    {base_token}")
            else:
                print("No orders match the requested market hash!")
        else:
            print("No orders found")
    else:
        print(f"Error fetching orders: {orders_response.status_code}")

if __name__ == "__main__":
    test_base_tokens() 