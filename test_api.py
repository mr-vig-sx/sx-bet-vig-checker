#!/usr/bin/env python3
"""
Test SX Bet API endpoints to see what's available
"""

import requests
import json

def test_endpoint(base_url, endpoint):
    """Test a specific endpoint"""
    try:
        url = f"{base_url}{endpoint}"
        print(f"Testing: {url}")
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if isinstance(data, dict) and 'data' in data:
                print(f"Data length: {len(data['data']) if isinstance(data['data'], list) else 'Not a list'}")
            return True
        else:
            print(f"Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    # Test both mainnet and testnet
    apis = [
        ("Mainnet", "https://api.sx.bet"),
        ("Testnet", "https://api.toronto.sx.bet")
    ]
    
    endpoints_to_test = [
        "/metadata",
        "/sports", 
        "/leagues",
        "/markets",
        "/markets/active",
        "/active-markets",
        "/fixtures",
        "/events",
        "/live-scores"
    ]
    
    for api_name, base_url in apis:
        print(f"\n{'='*50}")
        print(f"Testing {api_name}: {base_url}")
        print(f"{'='*50}")
        
        working_endpoints = []
        for endpoint in endpoints_to_test:
            print(f"\n--- {endpoint} ---")
            if test_endpoint(base_url, endpoint):
                working_endpoints.append(endpoint)
        
        print(f"\n✅ Working endpoints for {api_name}: {working_endpoints}")

if __name__ == "__main__":
    main() 