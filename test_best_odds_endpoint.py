#!/usr/bin/env python3
"""
Test script to check the best odds endpoint
"""

import requests
import json

def test_best_odds_endpoint():
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
    if markets:
        market = markets[0]
        market_hash = market.get('marketHash')
        market_name = f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}"
        
        print(f"\n--- Testing Market: {market_name} ---")
        print(f"Market Hash: {market_hash}")
        
        # Use the correct USDC base token from mainnet
        USDC_BASE_TOKEN = "0x6629Ce1Cf35Cc1329ebB4F63202F3f197b3F050B"
        
        # Try different best odds endpoints
        endpoints_to_try = [
            f"{base_url}/markets/{market_hash}/best-odds?baseToken={USDC_BASE_TOKEN}",
            f"{base_url}/best-odds?market={market_hash}&baseToken={USDC_BASE_TOKEN}",
            f"{base_url}/orders/best-odds?market={market_hash}&baseToken={USDC_BASE_TOKEN}",
            f"{base_url}/best-odds?marketHash={market_hash}&baseToken={USDC_BASE_TOKEN}"
        ]
        
        for i, endpoint in enumerate(endpoints_to_try):
            print(f"\nTrying endpoint {i+1}: {endpoint}")
            response = requests.get(endpoint)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Response: {json.dumps(data, indent=2)}")
                break
            else:
                print(f"Error: {response.text[:200]}...")
        else:
            print("All endpoints failed")
    else:
        print("No markets found")

if __name__ == "__main__":
    test_best_odds_endpoint() 