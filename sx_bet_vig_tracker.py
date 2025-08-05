import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Optional
import asyncio
import aiohttp
from dataclasses import dataclass

# SX Bet API Configuration
SX_API_BASE_URL = "https://api.sx.bet"
SX_TESTNET_API_BASE_URL = "https://api.toronto.sx.bet"

@dataclass
class MarketOdds:
    market_hash: str
    outcome_one_odds: float
    outcome_two_odds: float
    vig: float
    total_implied_probability: float
    sport: str
    league: str
    fixture: str
    market_name: str
    last_updated: datetime

class SXBetVigTracker:
    def __init__(self, use_testnet: bool = False):
        self.base_url = SX_TESTNET_API_BASE_URL if use_testnet else SX_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SX-Bet-Vig-Tracker/1.0',
            'Accept': 'application/json'
        })
    
    def get_metadata(self) -> Dict:
        """Get SX Bet metadata including token addresses and configuration"""
        try:
            response = self.session.get(f"{self.base_url}/metadata")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching metadata: {e}")
            return {}
    
    def get_sports(self) -> List[Dict]:
        """Get available sports"""
        try:
            response = self.session.get(f"{self.base_url}/sports")
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.RequestException as e:
            st.error(f"Error fetching sports: {e}")
            return []
    
    def get_leagues(self, sport_id: Optional[str] = None) -> List[Dict]:
        """Get leagues, optionally filtered by sport"""
        try:
            url = f"{self.base_url}/leagues"
            if sport_id:
                url += f"?sport={sport_id}"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.RequestException as e:
            st.error(f"Error fetching leagues: {e}")
            return []
    
    def get_active_markets(self, sport_id: Optional[str] = None, league_id: Optional[str] = None) -> List[Dict]:
        """Get active markets"""
        try:
            # Build query parameters
            params = {}
            if sport_id:
                params['sportIds'] = sport_id
            if league_id:
                params['leagueId'] = league_id
            
            # Use the correct endpoint with parameters
            response = self.session.get(f"{self.base_url}/markets/active", params=params)
            response.raise_for_status()
            data = response.json()

            # The API returns {data: {markets: [...], nextKey: "..."}}
            markets_data = data.get('data', {})
            if isinstance(markets_data, dict):
                markets = markets_data.get('markets', [])
            else:
                markets = markets_data if isinstance(markets_data, list) else []

            if not markets:
                st.warning("No active markets found")
                return []

            return markets
        except requests.RequestException as e:
            st.error(f"Error fetching markets: {e}")
            return []
    
    def get_best_odds(self, market_hash: str, debug_odds: bool = False) -> Optional[Dict]:
        """Get best odds for a specific market from the order book"""
        try:
            # Get all orders and filter by market hash
            response = self.session.get(f"{self.base_url}/orders")
            if response.status_code == 200:
                data = response.json()
                all_orders = data.get('data', [])
                
                # Filter orders for this specific market
                market_orders = [order for order in all_orders if order.get('marketHash') == market_hash]
                
                if market_orders:
                    # Calculate best odds from orders
                    return self.calculate_best_odds_from_orders(market_orders, market_hash, debug_odds=debug_odds)
            
            if debug_odds:
                st.warning(f"No orders available for market {market_hash[:10]}...")
            return None
            
        except requests.RequestException as e:
            if debug_odds:
                st.warning(f"Error fetching orders for market {market_hash[:10]}...: {e}")
            return None
    
    def calculate_best_odds_from_orders(self, orders: List[Dict], market_hash: str, debug_odds: bool = False) -> Optional[Dict]:
        """Calculate best odds from order book data"""
        if not orders:
            return None
        
        # USDC base token address from metadata (chain 416)
        USDC_BASE_TOKEN = "0xe2aa35C2039Bd0Ff196A6Ef99523CC0D3972ae3e"
        
        # Debug: show available base tokens
        base_tokens = set(order.get('baseToken') for order in orders if order.get('baseToken'))
        if base_tokens:
            st.info(f"Available base tokens: {list(base_tokens)}")
        
        # Filter orders by USDC base token AND market hash
        usdc_orders = [order for order in orders if order.get('baseToken') == USDC_BASE_TOKEN and order.get('marketHash') == market_hash]
        
        if not usdc_orders:
            st.warning(f"No USDC orders found. Total orders: {len(orders)}, USDC orders: {len(usdc_orders)}")
            return None
        
        # Group orders by outcome
        outcome_one_orders = []
        outcome_two_orders = []
        
        for order in usdc_orders:
            if order.get('isMakerBettingOutcomeOne'):
                outcome_one_orders.append(order)
            else:
                outcome_two_orders.append(order)
        
        if not outcome_one_orders or not outcome_two_orders:
            return None
        
        # Get best odds (lowest percentage odds for makers)
        best_outcome_one = min(outcome_one_orders, key=lambda x: float(x.get('percentageOdds', 0)))
        best_outcome_two = min(outcome_two_orders, key=lambda x: float(x.get('percentageOdds', 0)))
        
        # Debug: show the actual order structure
        if debug_odds and outcome_one_orders:
            st.write(f"Sample order structure: {outcome_one_orders[0]}")
        
        return {
            'outcomes': [
                {
                    'outcome': 1,
                    'odds': best_outcome_one.get('percentageOdds', '0')
                },
                {
                    'outcome': 2,
                    'odds': best_outcome_two.get('percentageOdds', '0')
                }
            ]
        }
    
    def calculate_vig(self, outcome_one_odds: float, outcome_two_odds: float) -> float:
        """Calculate vig from two outcome odds"""
        # Convert to implied probabilities
        prob_one = 1 / outcome_one_odds
        prob_two = 1 / outcome_two_odds
        
        # Calculate vig (overround) - this should be over 100%
        total_probability = prob_one + prob_two
        vig = total_probability * 100  # This gives us the overround percentage
        
        return vig
    
    def convert_implied_odds_to_decimal(self, implied_odds: str) -> float:
        """Convert SX Bet implied odds format to decimal odds"""
        try:
            # SX Bet uses implied odds format like "8391352143642350000"
            # Convert to decimal: 1 / (implied_odds / 10^20)
            implied_decimal = float(implied_odds) / (10 ** 20)
            decimal_odds = 1 / implied_decimal
            return decimal_odds
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def get_market_vig_data(self, markets: List[Dict], debug_odds: bool = False, show_markets_without_orders: bool = False, show_historical_markets: bool = False) -> List[MarketOdds]:
        """Get vig data for multiple markets using the best odds endpoint"""
        vig_data = []
        
        if not markets:
            return vig_data
        
        # Debug: check the first market structure
        if len(markets) > 0:
            first_market = markets[0]
            if isinstance(first_market, str):
                st.error(f"API returned string instead of dict. First item: {first_market[:100]}...")
                return vig_data
            elif isinstance(first_market, dict):
                st.info(f"Market structure: {list(first_market.keys())}")
        
        if debug_odds:
            st.write(f"Processing {len(markets)} active markets...")
        
        # Get all orders to check which markets have betting activity
        all_orders_response = self.session.get(f"{self.base_url}/orders")
        all_orders = []
        markets_with_orders = set()
        
        if all_orders_response.status_code == 200:
            all_orders_data = all_orders_response.json()
            all_orders = all_orders_data.get('data', [])
            markets_with_orders = set(order.get('marketHash') for order in all_orders)
            
            if debug_odds:
                st.write(f"Found {len(all_orders)} orders across {len(markets_with_orders)} markets")
        
        # Filter markets based on options
        markets_to_process = []
        
        if show_historical_markets:
            # Show all markets that have orders (including inactive ones)
            for market in markets:
                if market.get('marketHash') in markets_with_orders:
                    markets_to_process.append(market)
            
            # Also add markets from orders that aren't in active markets
            active_market_hashes = set(m.get('marketHash') for m in markets)
            historical_market_hashes = markets_with_orders - active_market_hashes
            
            if debug_odds:
                st.write(f"Found {len(historical_market_hashes)} historical markets with orders")
            
            # Create placeholder market objects for historical markets
            for market_hash in list(historical_market_hashes)[:20]:  # Limit to first 20
                historical_market = {
                    'marketHash': market_hash,
                    'outcomeOneName': 'Historical Market',
                    'outcomeTwoName': 'Historical Market',
                    'teamOneName': 'Team A',
                    'teamTwoName': 'Team B',
                    'sportLabel': 'Historical',
                    'leagueLabel': 'Historical',
                    'sportId': 'historical'
                }
                markets_to_process.append(historical_market)
        else:
            # Show active markets based on show_markets_without_orders option
            for market in markets:
                has_orders = market.get('marketHash') in markets_with_orders
                if show_markets_without_orders or has_orders:
                    markets_to_process.append(market)
        
        if debug_odds:
            st.write(f"Processing {len(markets_to_process)} markets...")
        
        for i, market in enumerate(markets_to_process):
            if not isinstance(market, dict):
                st.warning(f"Market {i} is not a dict: {type(market)}")
                continue
                
            market_hash = market.get('marketHash')
            if not market_hash:
                st.warning(f"Market {i} has no marketHash: {market}")
                continue
            
            if debug_odds:
                st.write(f"Processing market hash: {market_hash[:20]}...")
            
            # Get best odds for this market using the best odds endpoint
            best_odds = self.get_best_odds(market_hash, debug_odds=debug_odds)
            
            # If no odds and we're not showing markets without orders, skip
            if not best_odds and not show_markets_without_orders:
                continue
            
            # If no odds but we want to show the market, create placeholder data
            if not best_odds and show_markets_without_orders:
                vig_data.append(MarketOdds(
                    market_hash=market_hash,
                    outcome_one_odds=0.0,
                    outcome_two_odds=0.0,
                    vig=0.0,
                    total_implied_probability=0.0,
                    sport=market.get('sportLabel', 'Unknown'),
                    league=market.get('leagueLabel', 'Unknown'),
                    fixture=f"{market.get('teamOneName', 'Unknown')} vs {market.get('teamTwoName', 'Unknown')}",
                    market_name=f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}",
                    last_updated=datetime.now()
                ))
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
                
                # Debug: show the odds and vig calculation
                if debug_odds:
                    st.write(f"Market: {market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}")
                    st.write(f"Outcome 1 Odds: {outcome_one_odds:.2f} (Implied Prob: {1/outcome_one_odds*100:.2f}%)")
                    st.write(f"Outcome 2 Odds: {outcome_two_odds:.2f} (Implied Prob: {1/outcome_two_odds*100:.2f}%)")
                    st.write(f"Total Implied Prob: {total_implied_prob:.2f}%")
                    st.write(f"Vig: {vig:.2f}%")
                    st.write("---")
                
                vig_data.append(MarketOdds(
                    market_hash=market_hash,
                    outcome_one_odds=outcome_one_odds,
                    outcome_two_odds=outcome_two_odds,
                    vig=vig,
                    total_implied_probability=total_implied_prob,
                    sport=market.get('sportLabel', 'Unknown'),
                    league=market.get('leagueLabel', 'Unknown'),
                    fixture=f"{market.get('teamOneName', 'Unknown')} vs {market.get('teamTwoName', 'Unknown')}",
                    market_name=f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}",
                    last_updated=datetime.now()
                ))
        
        return vig_data

def create_vig_dashboard():
    st.set_page_config(
        page_title="SX Bet Live Vig Tracker",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🎯 SX Bet Live Vig Tracker")
    st.markdown("Track live vigorish (vig) across SX Bet markets to identify value betting opportunities")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    use_testnet = st.sidebar.checkbox("Use Testnet", value=False)  # Default to mainnet
    
    # Debug options - define these first
    debug_mode = st.sidebar.checkbox("Debug: Show API Responses", key="debug_api")
    debug_odds = st.sidebar.checkbox("Debug: Show Odds Calculations", key="debug_odds")
    
    # Initialize tracker
    tracker = SXBetVigTracker(use_testnet=use_testnet)
    
    # Get metadata
    with st.spinner("Loading SX Bet metadata..."):
        metadata = tracker.get_metadata()
    
    if not metadata:
        st.error("Failed to connect to SX Bet API. Please check your connection.")
        return
    
    # Test API connectivity
    st.sidebar.subheader("API Status")
    try:
        test_response = tracker.session.get(f"{tracker.base_url}/metadata")
        if test_response.status_code == 200:
            st.sidebar.success(f"✅ Connected to {tracker.base_url}")
        else:
            st.sidebar.error(f"❌ API Error: {test_response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Connection failed: {e}")
    
    # Display metadata info
    with st.expander("SX Bet Network Info"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Network", "Testnet" if use_testnet else "Mainnet")
            st.metric("Chain ID", metadata.get('chainId', 'Unknown'))
        with col2:
            st.metric("USDC Address", metadata.get('usdcAddress', 'Unknown')[:10] + "...")
            st.metric("WSX Address", metadata.get('wsxAddress', 'Unknown')[:10] + "...")
    
    # Get sports and leagues
    sports = tracker.get_sports()
    if not sports:
        st.error("Failed to fetch sports data")
        return
    
            # Sport selection (optional)
        if sports:
            if debug_mode:
                st.sidebar.json(sports[0] if sports else {})
        
        # Create sport options using the correct sport IDs
        sport_options = {"All Sports": None}
        for sport in sports:
            sport_name = sport.get('label', f"Sport {sport.get('sportId', 'Unknown')}")
            sport_id = sport.get('sportId')
            if sport_id:
                sport_options[sport_name] = str(sport_id)
        
        selected_sport = st.selectbox("Select Sport (Optional)", list(sport_options.keys()))
        selected_sport_id = sport_options[selected_sport]
    else:
        st.warning("No sports data available - showing all markets")
        selected_sport_id = None
    
    # League selection (optional)
    if selected_sport_id:
        leagues = tracker.get_leagues(selected_sport_id)
        if leagues and debug_mode:
            st.sidebar.json(leagues[0] if leagues else {})
        
        if leagues:
            league_options = {"All Leagues": None}
            for league in leagues:
                league_name = league.get('name') or league.get('leagueName') or league.get('title') or f"League {league.get('id', 'Unknown')}"
                league_id = league.get('id') or league.get('leagueId') or league.get('_id')
                if league_id:
                    league_options[league_name] = league_id
            
            selected_league = st.selectbox("Select League (Optional)", list(league_options.keys()))
            selected_league_id = league_options[selected_league]
        else:
            selected_league_id = None
    else:
        selected_league_id = None
    
    # Display options
    st.sidebar.subheader("Display Options")
    show_markets_without_orders = st.sidebar.checkbox("Show markets without orders", value=False, help="Show all active markets, even those without betting activity")
    show_historical_markets = st.sidebar.checkbox("Show historical markets with orders", value=False, help="Show markets from orders that are no longer active")
    
    # Auto-refresh option
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)
    refresh_interval = 30 if auto_refresh else 0
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Market Vig Analysis")
        
        # Get markets and vig data
        with st.spinner("Fetching market data..."):
            markets = tracker.get_active_markets(selected_sport_id, selected_league_id)
            
            if debug_mode:
                st.subheader("Raw API Response")
                st.json(markets[:3] if markets else [])  # Show first 3 markets
            
            vig_data = tracker.get_market_vig_data(
                markets, 
                debug_odds=debug_odds,
                show_markets_without_orders=show_markets_without_orders,
                show_historical_markets=show_historical_markets
            )
        
        if not vig_data:
            st.warning("No active markets found for the selected sport and league")
            return
        
        # Convert to DataFrame for display
        df = pd.DataFrame([
            {
                'Market': data.market_name,
                'Fixture': data.fixture,
                'Outcome 1 Odds': f"{data.outcome_one_odds:.2f}",
                'Outcome 2 Odds': f"{data.outcome_two_odds:.2f}",
                'Vig (%)': f"{data.vig:.2f}%",
                'Total Implied Prob (%)': f"{data.total_implied_probability:.1f}%",
                'Last Updated': data.last_updated.strftime('%H:%M:%S')
            }
            for data in vig_data
        ])
        
        # Display table
        st.dataframe(df, use_container_width=True)
        
        # Vig distribution chart
        st.subheader("Vig Distribution")
        fig = px.histogram(
            x=[data.vig for data in vig_data],
            nbins=20,
            title="Distribution of Vig Across Markets",
            labels={'x': 'Vig (%)', 'y': 'Number of Markets'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Vig Summary")
        
        if vig_data:
            avg_vig = sum(data.vig for data in vig_data) / len(vig_data)
            min_vig = min(data.vig for data in vig_data)
            max_vig = max(data.vig for data in vig_data)
            
            st.metric("Average Vig", f"{avg_vig:.2f}%")
            st.metric("Min Vig", f"{min_vig:.2f}%")
            st.metric("Max Vig", f"{max_vig:.2f}%")
            st.metric("Total Markets", len(vig_data))
            
            # Value betting opportunities (low vig markets)
            low_vig_threshold = 2.0  # Markets with vig < 2%
            low_vig_markets = [data for data in vig_data if data.vig < low_vig_threshold]
            
            st.subheader("Value Opportunities")
            st.metric("Low Vig Markets (<2%)", len(low_vig_markets))
            
            if low_vig_markets:
                st.write("**Best Value Markets:**")
                for market in sorted(low_vig_markets, key=lambda x: x.vig)[:5]:
                    st.write(f"• {market.market_name}: {market.vig:.2f}% vig")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    create_vig_dashboard() 