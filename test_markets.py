#!/usr/bin/env python3
"""
Test the /markets/active endpoint to see the actual response structure
"""

import requests
import json

def test_markets_active():
    """Test the /markets/active endpoint"""
    base_url = "https://api.sx.bet"
    
    try:
        print(f"Testing: {base_url}/markets/active")
        response = requests.get(f"{base_url}/markets/active")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if isinstance(data, dict) and 'data' in data:
                markets = data['data']
                print(f"Markets type: {type(markets)}")
                
                if isinstance(markets, dict):
                    print(f"Markets dict keys: {list(markets.keys())}")
                    print(f"Markets dict: {markets}")
                elif isinstance(markets, list):
                    print(f"Number of markets: {len(markets)}")
                    if len(markets) > 0:
                        first_market = markets[0]
                        print(f"First market type: {type(first_market)}")
                        print(f"First market: {first_market}")
                        
                        if isinstance(first_market, dict):
                            print(f"First market keys: {list(first_market.keys())}")
                        elif isinstance(first_market, str):
                            print(f"First market (string): {first_market[:200]}...")
                else:
                    print(f"Markets is neither dict nor list: {markets}")
            else:
                print(f"Full response: {data}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_markets_active() 