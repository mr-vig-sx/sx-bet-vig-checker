#!/usr/bin/env python3
"""
Test script to get all orders and find orders for specific markets
"""

import requests
import json

def test_all_orders():
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
    
    # Get first 2 markets
    test_markets = markets[:2]
    market_hashes = [market.get('marketHash') for market in test_markets]
    
    print(f"\nTesting markets:")
    for i, market in enumerate(test_markets):
        market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
        print(f"  {i+1}. {market_name}: {market.get('marketHash')}")
    
    # Try to get orders without market parameter
    print(f"\nFetching all orders...")
    orders_response = requests.get(f"{base_url}/orders")
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        orders = orders_data.get('data', [])
        
        print(f"Total orders returned: {len(orders)}")
        
        if orders:
            # Check what market hashes are in the orders
            order_market_hashes = set(order.get('marketHash') for order in orders)
            print(f"Unique market hashes in orders: {len(order_market_hashes)}")
            
            # Check if our test markets are in the orders
            for i, market_hash in enumerate(market_hashes):
                if market_hash in order_market_hashes:
                    print(f"✅ Market {i+1} found in orders")
                    
                    # Get orders for this market
                    market_orders = [order for order in orders if order.get('marketHash') == market_hash]
                    print(f"   Orders for this market: {len(market_orders)}")
                    
                    # Check base tokens
                    base_tokens = set(order.get('baseToken') for order in market_orders)
                    print(f"   Base tokens: {list(base_tokens)}")
                    
                    # Check USDC orders
                    USDC_BASE_TOKEN = "0x6629Ce1Cf35Cc1329ebB4F63202F3f197b3F050B"
                    usdc_orders = [order for order in market_orders if order.get('baseToken') == USDC_BASE_TOKEN]
                    print(f"   USDC orders: {len(usdc_orders)}")
                    
                    if usdc_orders:
                        print(f"   Sample USDC order: {json.dumps(usdc_orders[0], indent=2)}")
                else:
                    print(f"❌ Market {i+1} NOT found in orders")
            
            # Show some sample market hashes from orders
            print(f"\nSample market hashes from orders:")
            for i, market_hash in enumerate(list(order_market_hashes)[:5]):
                print(f"  {i+1}. {market_hash}")
        else:
            print("No orders found")
    else:
        print(f"Error fetching orders: {orders_response.status_code}")

if __name__ == "__main__":
    test_all_orders() 