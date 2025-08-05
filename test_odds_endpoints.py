#!/usr/bin/env python3
"""
Test different endpoints for getting odds from SX Bet API
"""

import requests
import json

def test_odds_endpoints():
    """Test different endpoints for getting odds"""
    base_url = "https://api.sx.bet"
    
    # Get a sample market hash first
    try:
        print("Getting sample market hash...")
        response = requests.get(f"{base_url}/markets/active")
        if response.status_code == 200:
            data = response.json()
            markets_data = data.get('data', {})
            if isinstance(markets_data, dict):
                markets = markets_data.get('markets', [])
                if markets:
                    sample_market = markets[0]
                    market_hash = sample_market.get('marketHash')
                    print(f"Sample market hash: {market_hash}")
                    
                    # Test different odds endpoints
                    odds_endpoints = [
                        f"/markets/{market_hash}/best-odds",
                        f"/markets/{market_hash}/odds",
                        f"/odds/{market_hash}",
                        f"/orders?market={market_hash}",
                        f"/active-orders?market={market_hash}",
                        f"/trades?market={market_hash}",
                        f"/markets/{market_hash}/orders",
                        f"/markets/{market_hash}/active-orders"
                    ]
                    
                    for endpoint in odds_endpoints:
                        print(f"\n--- Testing {endpoint} ---")
                        try:
                            odds_response = requests.get(f"{base_url}{endpoint}")
                            print(f"Status: {odds_response.status_code}")
                            if odds_response.status_code == 200:
                                odds_data = odds_response.json()
                                print(f"Response keys: {list(odds_data.keys()) if isinstance(odds_data, dict) else 'Not a dict'}")
                                print(f"Success! Found working endpoint: {endpoint}")
                                return endpoint
                            else:
                                print(f"Error: {odds_response.text[:200]}")
                        except Exception as e:
                            print(f"Exception: {e}")
                    
                    print("\nNo working odds endpoints found")
                    return None
                else:
                    print("No markets found")
                    return None
            else:
                print("Invalid markets data structure")
                return None
        else:
            print(f"Failed to get markets: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    test_odds_endpoints() 