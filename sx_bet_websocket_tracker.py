import asyncio
import aiohttp
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import websockets
import threading
from collections import defaultdict

# SX Bet API Configuration
SX_API_BASE_URL = "https://api.sx.bet"
SX_TESTNET_API_BASE_URL = "https://api.toronto.sx.bet"
SX_WS_URL = "wss://api.sx.bet/ws"
SX_TESTNET_WS_URL = "wss://api.toronto.sx.bet/ws"

@dataclass
class LiveMarketData:
    market_hash: str
    market_name: str
    fixture: str
    sport: str
    league: str
    outcome_one_odds: float
    outcome_two_odds: float
    vig: float
    total_implied_probability: float
    last_updated: datetime
    order_book_depth: Dict
    volume_24h: float
    is_live: bool

class SXBetWebSocketTracker:
    def __init__(self, use_testnet: bool = False):
        self.base_url = SX_TESTNET_API_BASE_URL if use_testnet else SX_API_BASE_URL
        self.ws_url = SX_TESTNET_WS_URL if use_testnet else SX_WS_URL
        self.session = aiohttp.ClientSession()
        self.websocket = None
        self.is_connected = False
        self.market_data = {}
        self.vig_history = defaultdict(list)
        self.subscribed_markets = set()
        
    async def connect_websocket(self):
        """Connect to SX Bet WebSocket"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            st.success("Connected to SX Bet WebSocket")
            return True
        except Exception as e:
            st.error(f"Failed to connect to WebSocket: {e}")
            return False
    
    async def subscribe_to_markets(self, market_hashes: List[str]):
        """Subscribe to market updates"""
        if not self.is_connected:
            return
        
        subscription_message = {
            "type": "subscribe",
            "channels": ["order_book_v2", "active_orders_v2"],
            "markets": market_hashes
        }
        
        try:
            await self.websocket.send(json.dumps(subscription_message))
            self.subscribed_markets.update(market_hashes)
            st.info(f"Subscribed to {len(market_hashes)} markets")
        except Exception as e:
            st.error(f"Failed to subscribe to markets: {e}")
    
    async def listen_for_updates(self):
        """Listen for real-time market updates"""
        if not self.is_connected:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_websocket_message(data)
        except websockets.exceptions.ConnectionClosed:
            st.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            st.error(f"WebSocket error: {e}")
    
    async def process_websocket_message(self, data: Dict):
        """Process incoming WebSocket messages"""
        message_type = data.get('type')
        
        if message_type == 'order_book_v2':
            await self.process_order_book_update(data)
        elif message_type == 'active_orders_v2':
            await self.process_active_orders_update(data)
        elif message_type == 'market_update':
            await self.process_market_update(data)
    
    async def process_order_book_update(self, data: Dict):
        """Process order book updates"""
        market_hash = data.get('marketHash')
        if not market_hash:
            return
        
        # Update order book depth
        if market_hash in self.market_data:
            self.market_data[market_hash].order_book_depth = data.get('orderBook', {})
            self.market_data[market_hash].last_updated = datetime.now()
    
    async def process_active_orders_update(self, data: Dict):
        """Process active orders updates"""
        market_hash = data.get('marketHash')
        if not market_hash:
            return
        
        # Update market data with new orders
        if market_hash in self.market_data:
            # Recalculate best odds from active orders
            await self.update_market_odds(market_hash, data.get('orders', []))
    
    async def process_market_update(self, data: Dict):
        """Process general market updates"""
        market_hash = data.get('marketHash')
        if not market_hash:
            return
        
        # Update market status, live status, etc.
        if market_hash in self.market_data:
            self.market_data[market_hash].is_live = data.get('isLive', False)
    
    async def update_market_odds(self, market_hash: str, orders: List[Dict]):
        """Update market odds from active orders"""
        if not orders:
            return
        
        # Calculate best odds from order book
        outcome_one_orders = [o for o in orders if o.get('isMakerBettingOutcomeOne')]
        outcome_two_orders = [o for o in orders if not o.get('isMakerBettingOutcomeOne')]
        
        if outcome_one_orders and outcome_two_orders:
            # Get best odds (lowest percentage odds for makers)
            best_outcome_one = min(outcome_one_orders, key=lambda x: float(x.get('percentageOdds', 0)))
            best_outcome_two = min(outcome_two_orders, key=lambda x: float(x.get('percentageOdds', 0)))
            
            # Convert to decimal odds
            outcome_one_odds = self.convert_implied_odds_to_decimal(best_outcome_one.get('percentageOdds', '0'))
            outcome_two_odds = self.convert_implied_odds_to_decimal(best_outcome_two.get('percentageOdds', '0'))
            
            if outcome_one_odds > 0 and outcome_two_odds > 0:
                vig = self.calculate_vig(outcome_one_odds, outcome_two_odds)
                total_implied_prob = (1/outcome_one_odds + 1/outcome_two_odds) * 100
                
                if market_hash in self.market_data:
                    self.market_data[market_hash].outcome_one_odds = outcome_one_odds
                    self.market_data[market_hash].outcome_two_odds = outcome_two_odds
                    self.market_data[market_hash].vig = vig
                    self.market_data[market_hash].total_implied_probability = total_implied_prob
                    self.market_data[market_hash].last_updated = datetime.now()
                    
                    # Store vig history
                    self.vig_history[market_hash].append({
                        'timestamp': datetime.now(),
                        'vig': vig,
                        'outcome_one_odds': outcome_one_odds,
                        'outcome_two_odds': outcome_two_odds
                    })
                    
                    # Keep only last 100 data points
                    if len(self.vig_history[market_hash]) > 100:
                        self.vig_history[market_hash] = self.vig_history[market_hash][-100:]
    
    def calculate_vig(self, outcome_one_odds: float, outcome_two_odds: float) -> float:
        """Calculate vig from two outcome odds"""
        prob_one = 1 / outcome_one_odds
        prob_two = 1 / outcome_two_odds
        total_probability = prob_one + prob_two
        vig = (total_probability - 1) * 100
        return vig
    
    def convert_implied_odds_to_decimal(self, implied_odds: str) -> float:
        """Convert SX Bet implied odds format to decimal odds"""
        try:
            implied_decimal = float(implied_odds) / (10 ** 20)
            decimal_odds = 1 / implied_decimal
            return decimal_odds
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    async def get_markets_data(self, sport_id: Optional[str] = None, league_id: Optional[str] = None) -> List[Dict]:
        """Get markets data via REST API"""
        try:
            params = {}
            if sport_id:
                params['sport'] = sport_id
            if league_id:
                params['league'] = league_id
            
            async with self.session.get(f"{self.base_url}/markets", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    st.error(f"Failed to fetch markets: {response.status}")
                    return []
        except Exception as e:
            st.error(f"Error fetching markets: {e}")
            return []
    
    async def initialize_market_data(self, markets: List[Dict]):
        """Initialize market data from REST API"""
        for market in markets:
            market_hash = market.get('marketHash')
            if not market_hash:
                continue
            
            # Get initial odds
            try:
                async with self.session.get(f"{self.base_url}/markets/{market_hash}/best-odds") as response:
                    if response.status == 200:
                        data = await response.json()
                        best_odds = data.get('data', {})
                        
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
                            
                            self.market_data[market_hash] = LiveMarketData(
                                market_hash=market_hash,
                                market_name=market.get('marketName', 'Unknown'),
                                fixture=market.get('fixture', 'Unknown'),
                                sport=market.get('sport', 'Unknown'),
                                league=market.get('league', 'Unknown'),
                                outcome_one_odds=outcome_one_odds,
                                outcome_two_odds=outcome_two_odds,
                                vig=vig,
                                total_implied_probability=total_implied_prob,
                                last_updated=datetime.now(),
                                order_book_depth={},
                                volume_24h=0.0,
                                is_live=market.get('isLive', False)
                            )
            except Exception as e:
                st.error(f"Error initializing market {market_hash}: {e}")
    
    def get_vig_summary(self) -> Dict:
        """Get summary statistics for current vig data"""
        if not self.market_data:
            return {}
        
        vigs = [data.vig for data in self.market_data.values()]
        
        return {
            'average_vig': sum(vigs) / len(vigs),
            'min_vig': min(vigs),
            'max_vig': max(vigs),
            'total_markets': len(self.market_data),
            'low_vig_markets': len([v for v in vigs if v < 2.0]),
            'high_vig_markets': len([v for v in vigs if v > 5.0])
        }
    
    def get_value_opportunities(self, threshold: float = 2.0) -> List[LiveMarketData]:
        """Get markets with vig below threshold (value opportunities)"""
        return [
            data for data in self.market_data.values()
            if data.vig < threshold
        ]
    
    async def close(self):
        """Close connections"""
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()

def create_advanced_vig_dashboard():
    st.set_page_config(
        page_title="SX Bet Advanced Vig Tracker",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🚀 SX Bet Advanced Live Vig Tracker")
    st.markdown("Real-time vigorish tracking with WebSocket updates and advanced analytics")
    
    # Initialize session state
    if 'tracker' not in st.session_state:
        st.session_state.tracker = None
    if 'websocket_task' not in st.session_state:
        st.session_state.websocket_task = None
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    use_testnet = st.sidebar.checkbox("Use Testnet", value=False)
    
    # Initialize tracker
    if st.session_state.tracker is None:
        st.session_state.tracker = SXBetWebSocketTracker(use_testnet=use_testnet)
    
    tracker = st.session_state.tracker
    
    # Connection status
    col1, col2 = st.columns(2)
    with col1:
        if tracker.is_connected:
            st.success("🟢 WebSocket Connected")
        else:
            st.error("🔴 WebSocket Disconnected")
    
    with col2:
        if st.button("Connect WebSocket"):
            asyncio.run(tracker.connect_websocket())
    
    # Sport and league selection
    st.subheader("Market Selection")
    
    # Get sports (simplified for demo)
    sports = ["Football", "Basketball", "Baseball", "Hockey", "Soccer"]
    selected_sport = st.selectbox("Select Sport", sports)
    
    leagues = ["NFL", "NBA", "MLB", "NHL", "Premier League"]
    selected_league = st.selectbox("Select League", leagues)
    
    # Market filtering
    st.subheader("Market Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_vig = st.slider("Min Vig (%)", 0.0, 10.0, 0.0, 0.1)
    with col2:
        max_vig = st.slider("Max Vig (%)", 0.0, 10.0, 10.0, 0.1)
    with col3:
        show_live_only = st.checkbox("Live Markets Only", value=False)
    
    # Main dashboard
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Market Data")
        
        # Filter market data based on criteria
        filtered_markets = []
        for market_data in tracker.market_data.values():
            if (min_vig <= market_data.vig <= max_vig and
                (not show_live_only or market_data.is_live)):
                filtered_markets.append(market_data)
        
        if filtered_markets:
            # Create DataFrame
            df = pd.DataFrame([
                {
                    'Market': data.market_name,
                    'Fixture': data.fixture,
                    'Outcome 1': f"{data.outcome_one_odds:.2f}",
                    'Outcome 2': f"{data.outcome_two_odds:.2f}",
                    'Vig (%)': f"{data.vig:.2f}%",
                    'Total Prob (%)': f"{data.total_implied_probability:.1f}%",
                    'Live': "🟢" if data.is_live else "⚪",
                    'Last Updated': data.last_updated.strftime('%H:%M:%S')
                }
                for data in filtered_markets
            ])
            
            st.dataframe(df, use_container_width=True)
            
            # Vig distribution chart
            st.subheader("Vig Distribution")
            fig = px.histogram(
                x=[data.vig for data in filtered_markets],
                nbins=20,
                title="Distribution of Vig Across Markets",
                labels={'x': 'Vig (%)', 'y': 'Number of Markets'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Vig trends over time
            if tracker.vig_history:
                st.subheader("Vig Trends")
                # Show trends for top 5 markets by volume
                top_markets = sorted(filtered_markets, key=lambda x: x.volume_24h, reverse=True)[:5]
                
                for market in top_markets:
                    if market.market_hash in tracker.vig_history:
                        history = tracker.vig_history[market.market_hash]
                        if len(history) > 1:
                            timestamps = [h['timestamp'] for h in history]
                            vigs = [h['vig'] for h in history]
                            
                            fig = px.line(
                                x=timestamps,
                                y=vigs,
                                title=f"{market.market_name} - Vig Trend",
                                labels={'x': 'Time', 'y': 'Vig (%)'}
                            )
                            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No markets match the current filters")
    
    with col2:
        st.subheader("Vig Summary")
        
        summary = tracker.get_vig_summary()
        if summary:
            st.metric("Average Vig", f"{summary['average_vig']:.2f}%")
            st.metric("Min Vig", f"{summary['min_vig']:.2f}%")
            st.metric("Max Vig", f"{summary['max_vig']:.2f}%")
            st.metric("Total Markets", summary['total_markets'])
            st.metric("Low Vig (<2%)", summary['low_vig_markets'])
            st.metric("High Vig (>5%)", summary['high_vig_markets'])
        
        # Value opportunities
        st.subheader("Value Opportunities")
        value_markets = tracker.get_value_opportunities(threshold=2.0)
        
        if value_markets:
            st.metric("Low Vig Markets", len(value_markets))
            st.write("**Best Value Markets:**")
            for market in sorted(value_markets, key=lambda x: x.vig)[:5]:
                st.write(f"• {market.market_name}: {market.vig:.2f}% vig")
        else:
            st.info("No low vig markets found")
        
        # WebSocket status
        st.subheader("Connection Status")
        st.write(f"Connected: {tracker.is_connected}")
        st.write(f"Subscribed Markets: {len(tracker.subscribed_markets)}")
    
    # Auto-refresh
    if st.checkbox("Auto-refresh", value=True):
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    create_advanced_vig_dashboard() 