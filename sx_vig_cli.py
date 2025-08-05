#!/usr/bin/env python3
"""
SX Bet Vig Tracker - Command Line Interface
Quick vig checking tool for SX Bet markets
"""

import requests
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from tabulate import tabulate

class SXBetVigCLI:
    def __init__(self, use_testnet: bool = False):
        self.base_url = "https://api.toronto.sx.bet" if use_testnet else "https://api.sx.bet"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SX-Bet-Vig-CLI/1.0',
            'Accept': 'application/json'
        })
    
    def get_metadata(self) -> Dict:
        """Get SX Bet metadata"""
        try:
            response = self.session.get(f"{self.base_url}/metadata")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching metadata: {e}")
            return {}
    
    def get_sports(self) -> List[Dict]:
        """Get available sports"""
        try:
            response = self.session.get(f"{self.base_url}/sports")
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.RequestException as e:
            print(f"Error fetching sports: {e}")
            return []
    
    def get_leagues(self, sport_id: Optional[str] = None) -> List[Dict]:
        """Get leagues"""
        try:
            url = f"{self.base_url}/leagues"
            if sport_id:
                url += f"?sport={sport_id}"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.RequestException as e:
            print(f"Error fetching leagues: {e}")
            return []
    
    def get_active_markets(self, sport_id: Optional[str] = None, league_id: Optional[str] = None) -> List[Dict]:
        """Get active markets"""
        try:
            # Use the correct endpoint based on API test results
            response = self.session.get(f"{self.base_url}/markets/active")
            response.raise_for_status()
            data = response.json()
            markets = data.get('data', [])
            
            # If we have sport_id or league_id, filter the results
            if sport_id or league_id:
                filtered_markets = []
                for market in markets:
                    market_sport = market.get('sport') or market.get('sportId') or market.get('sport_id')
                    market_league = market.get('league') or market.get('leagueId') or market.get('league_id')
                    
                    sport_match = not sport_id or str(market_sport) == str(sport_id)
                    league_match = not league_id or str(market_league) == str(league_id)
                    
                    if sport_match and league_match:
                        filtered_markets.append(market)
                
                return filtered_markets
            
            return markets
        except requests.RequestException as e:
            print(f"Error fetching markets: {e}")
            return []
    
    def get_best_odds(self, market_hash: str) -> Optional[Dict]:
        """Get best odds for a specific market"""
        try:
            response = self.session.get(f"{self.base_url}/markets/{market_hash}/best-odds")
            response.raise_for_status()
            data = response.json()
            return data.get('data')
        except requests.RequestException as e:
            print(f"Error fetching best odds for market {market_hash}: {e}")
            return None
    
    def convert_implied_odds_to_decimal(self, implied_odds: str) -> float:
        """Convert SX Bet implied odds format to decimal odds"""
        try:
            implied_decimal = float(implied_odds) / (10 ** 20)
            decimal_odds = 1 / implied_decimal
            return decimal_odds
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def calculate_vig(self, outcome_one_odds: float, outcome_two_odds: float) -> float:
        """Calculate vig from two outcome odds"""
        prob_one = 1 / outcome_one_odds
        prob_two = 1 / outcome_two_odds
        total_probability = prob_one + prob_two
        vig = (total_probability - 1) * 100
        return vig
    
    def analyze_markets(self, sport_id: Optional[str] = None, league_id: Optional[str] = None, 
                       min_vig: float = 0.0, max_vig: float = 10.0) -> List[Dict]:
        """Analyze markets and return vig data"""
        markets = self.get_active_markets(sport_id, league_id)
        vig_data = []
        
        print(f"Analyzing {len(markets)} markets...")
        
        for i, market in enumerate(markets, 1):
            market_hash = market.get('marketHash')
            if not market_hash:
                continue
            
            print(f"Processing market {i}/{len(markets)}: {market.get('marketName', 'Unknown')}")
            
            best_odds = self.get_best_odds(market_hash)
            if not best_odds:
                continue
            
            # Extract odds for both outcomes
            outcome_one_odds = 0.0
            outcome_two_odds = 0.0
            
            for outcome in best_odds.get('outcomes', []):
                if outcome.get('outcome') == 1:
                    outcome_one_odds = self.convert_implied_odds_to_decimal(outcome.get('odds', '0'))
                elif outcome.get('outcome') == 2:
                    outcome_two_odds = self.convert_implied_odds_to_decimal(outcome.get('odds', '0'))
            
            if outcome_one_odds > 0 and outcome_two_odds > 0:
                vig = self.calculate_vig(outcome_one_odds, outcome_two_odds)
                total_implied_prob = (1/outcome_one_odds + 1/outcome_two_odds) * 100
                
                # Filter by vig range
                if min_vig <= vig <= max_vig:
                    vig_data.append({
                        'market_name': market.get('marketName', 'Unknown'),
                        'fixture': market.get('fixture', 'Unknown'),
                        'sport': market.get('sport', 'Unknown'),
                        'league': market.get('league', 'Unknown'),
                        'outcome_one_odds': outcome_one_odds,
                        'outcome_two_odds': outcome_two_odds,
                        'vig': vig,
                        'total_implied_prob': total_implied_prob,
                        'is_live': market.get('isLive', False)
                    })
        
        return vig_data
    
    def print_vig_summary(self, vig_data: List[Dict]):
        """Print summary statistics"""
        if not vig_data:
            print("No markets found matching criteria")
            return
        
        vigs = [data['vig'] for data in vig_data]
        avg_vig = sum(vigs) / len(vigs)
        min_vig = min(vigs)
        max_vig = max(vigs)
        low_vig_count = len([v for v in vigs if v < 2.0])
        high_vig_count = len([v for v in vigs if v > 5.0])
        
        print("\n" + "="*50)
        print("VIG SUMMARY")
        print("="*50)
        print(f"Total Markets: {len(vig_data)}")
        print(f"Average Vig: {avg_vig:.2f}%")
        print(f"Min Vig: {min_vig:.2f}%")
        print(f"Max Vig: {max_vig:.2f}%")
        print(f"Low Vig Markets (<2%): {low_vig_count}")
        print(f"High Vig Markets (>5%): {high_vig_count}")
        print("="*50)
    
    def print_market_table(self, vig_data: List[Dict], sort_by: str = 'vig'):
        """Print markets in a formatted table"""
        if not vig_data:
            return
        
        # Sort data
        if sort_by == 'vig':
            vig_data = sorted(vig_data, key=lambda x: x['vig'])
        elif sort_by == 'name':
            vig_data = sorted(vig_data, key=lambda x: x['market_name'])
        
        # Prepare table data
        table_data = []
        for data in vig_data:
            table_data.append([
                data['market_name'][:30],  # Truncate long names
                data['fixture'][:25],
                f"{data['outcome_one_odds']:.2f}",
                f"{data['outcome_two_odds']:.2f}",
                f"{data['vig']:.2f}%",
                f"{data['total_implied_prob']:.1f}%",
                "🟢" if data['is_live'] else "⚪"
            ])
        
        headers = ['Market', 'Fixture', 'Outcome 1', 'Outcome 2', 'Vig (%)', 'Total Prob (%)', 'Live']
        
        print("\n" + "="*100)
        print("MARKET VIG ANALYSIS")
        print("="*100)
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def print_value_opportunities(self, vig_data: List[Dict], threshold: float = 2.0):
        """Print value betting opportunities"""
        value_markets = [data for data in vig_data if data['vig'] < threshold]
        
        if not value_markets:
            print(f"\nNo markets with vig < {threshold}% found")
            return
        
        print(f"\n" + "="*60)
        print(f"VALUE OPPORTUNITIES (Vig < {threshold}%)")
        print("="*60)
        
        for i, market in enumerate(sorted(value_markets, key=lambda x: x['vig']), 1):
            print(f"{i:2d}. {market['market_name']}")
            print(f"    Fixture: {market['fixture']}")
            print(f"    Odds: {market['outcome_one_odds']:.2f} | {market['outcome_two_odds']:.2f}")
            print(f"    Vig: {market['vig']:.2f}%")
            print(f"    Live: {'Yes' if market['is_live'] else 'No'}")
            print()

def main():
    parser = argparse.ArgumentParser(description='SX Bet Vig Tracker CLI')
    parser.add_argument('--testnet', action='store_true', help='Use testnet instead of mainnet')
    parser.add_argument('--sport', type=str, help='Filter by sport ID')
    parser.add_argument('--league', type=str, help='Filter by league ID')
    parser.add_argument('--min-vig', type=float, default=0.0, help='Minimum vig percentage')
    parser.add_argument('--max-vig', type=float, default=10.0, help='Maximum vig percentage')
    parser.add_argument('--sort-by', choices=['vig', 'name'], default='vig', help='Sort markets by')
    parser.add_argument('--value-threshold', type=float, default=2.0, help='Vig threshold for value opportunities')
    parser.add_argument('--list-sports', action='store_true', help='List available sports')
    parser.add_argument('--list-leagues', action='store_true', help='List available leagues')
    
    args = parser.parse_args()
    
    # Initialize tracker
    tracker = SXBetVigCLI(use_testnet=args.testnet)
    
    print(f"SX Bet Vig Tracker CLI")
    print(f"Network: {'Testnet' if args.testnet else 'Mainnet'}")
    print(f"API URL: {tracker.base_url}")
    print()
    
    # Get metadata
    metadata = tracker.get_metadata()
    if metadata:
        print(f"Chain ID: {metadata.get('chainId', 'Unknown')}")
        print(f"USDC Address: {metadata.get('usdcAddress', 'Unknown')[:10]}...")
        print()
    
    # List sports if requested
    if args.list_sports:
        sports = tracker.get_sports()
        if sports:
            print("Available Sports:")
            for sport in sports:
                sport_name = sport.get('name') or sport.get('sportName') or sport.get('title') or f"Sport {sport.get('id', 'Unknown')}"
                sport_id = sport.get('id') or sport.get('sportId') or sport.get('_id')
                print(f"  {sport_id}: {sport_name}")
        return
    
    # List leagues if requested
    if args.list_leagues:
        leagues = tracker.get_leagues(args.sport)
        if leagues:
            print("Available Leagues:")
            for league in leagues:
                league_name = league.get('name') or league.get('leagueName') or league.get('title') or f"League {league.get('id', 'Unknown')}"
                league_id = league.get('id') or league.get('leagueId') or league.get('_id')
                print(f"  {league_id}: {league_name}")
        return
    
    # Analyze markets
    vig_data = tracker.analyze_markets(
        sport_id=args.sport,
        league_id=args.league,
        min_vig=args.min_vig,
        max_vig=args.max_vig
    )
    
    # Print results
    tracker.print_vig_summary(vig_data)
    tracker.print_market_table(vig_data, sort_by=args.sort_by)
    tracker.print_value_opportunities(vig_data, threshold=args.value_threshold)

if __name__ == "__main__":
    main() 