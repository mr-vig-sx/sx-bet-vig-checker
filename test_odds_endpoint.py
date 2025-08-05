#!/usr/bin/env python3
"""
Test script to debug the odds endpoint
"""

import requests
import json

def test_odds_endpoint():
    base_url = "https://api.sx.bet"
    
    # First, let's get some markets to test with
    print("Fetching markets...")
    markets_response = requests.get(f"{base_url}/markets/active?sportIds=3")
    
    if markets_response.status_code == 200:
        markets_data = markets_response.json()
        markets = markets_data.get('data', {}).get('markets', [])
        
        if markets:
            # Test with the first market
            test_market = markets[0]
            market_hash = test_market.get('marketHash')
            
            print(f"Testing with market hash: {market_hash}")
            print(f"Market: {test_market.get('outcomeOneName')} vs {test_market.get('outcomeTwoName')}")
            
            # Test different endpoint formats
            endpoints_to_test = [
                f"/orders/odds/best?market={market_hash}",
                f"/orders/odds/best?marketHash={market_hash}",
                f"/orders/odds/best?market_id={market_hash}",
                f"/orders/odds/best?marketId={market_hash}",
                f"/best-odds?market={market_hash}",
                f"/odds/best?market={market_hash}"
            ]
            
            for endpoint in endpoints_to_test:
                print(f"\nTesting endpoint: {endpoint}")
                try:
                    response = requests.get(f"{base_url}{endpoint}")
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"Response: {json.dumps(data, indent=2)}")
                        break
                    else:
                        print(f"Error response: {response.text}")
                except Exception as e:
                    print(f"Exception: {e}")
        else:
            print("No markets found")
    else:
        print(f"Failed to fetch markets: {markets_response.status_code}")

if __name__ == "__main__":
    test_odds_endpoint() 