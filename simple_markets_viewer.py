#!/usr/bin/env python3
"""
Simple Active Markets Viewer
Just query the active markets endpoint and display them
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

def fetch_best_odds(market_hash, league_id, base_token="0x6629Ce1Cf35Cc1329ebB4F63202F3f197b3F050B"):
    """Fetch best odds for a market and calculate vig"""
    try:
        # Build parameters according to API docs - only use marketHashes, not leagueIds
        params = {
            'marketHashes': market_hash.split(',') if ',' in market_hash else [market_hash],
            'baseToken': base_token
        }
        
        url = "https://api.sx.bet/orders/odds/best"
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            best_odds = data.get('data', {}).get('bestOdds', [])
            
            if best_odds:
                # Get the first (and should be only) result
                odds_data = best_odds[0]
                
                # Get odds from the correct structure
                outcome_one_odds = int(odds_data.get('outcomeOne', {}).get('percentageOdds', 0))
                outcome_two_odds = int(odds_data.get('outcomeTwo', {}).get('percentageOdds', 0))
                
                # Convert from percentage with 18 trailing figures to decimal
                # Example: 43750000000000000000 -> 43.75%
                outcome_a_percent = outcome_one_odds / (10 ** 18)
                outcome_b_percent = outcome_two_odds / (10 ** 18)
                
                # Convert percentage odds to decimal odds
                # If percentage is 43.75%, decimal odds = 100/43.75 = 2.29
                outcome_a_decimal = 100 / outcome_a_percent if outcome_a_percent > 0 else 0
                outcome_b_decimal = 100 / outcome_b_percent if outcome_b_percent > 0 else 0
                
                # Calculate implied probabilities (1/decimal_odds)
                outcome_a_implied = 1 / outcome_a_decimal if outcome_a_decimal > 0 else 0
                outcome_b_implied = 1 / outcome_b_decimal if outcome_b_decimal > 0 else 0
                
                # Calculate vig: (1 - implied_probability_A) + (1 - implied_probability_B)
                vig_percentage = (1 - outcome_a_implied) + (1 - outcome_b_implied)
                
                return {
                    'outcome_a_odds': outcome_a_implied * 100,  # Convert to percentage for display
                    'outcome_b_odds': outcome_b_implied * 100,  # Convert to percentage for display
                    'total_probability': (outcome_a_implied + outcome_b_implied) * 100,  # Total implied probability
                    'vig_percentage': vig_percentage * 100,  # Convert vig to percentage for display
                    'best_odds_data': best_odds  # Return raw data for batch processing
                }
            else:
                return None
        else:
            return None
    except Exception as e:
        return None

def main():
    st.set_page_config(page_title="Simple Markets Viewer", layout="wide")
    
    st.title("SX.Bet Vig Checker")
    
    # API base URL
    base_url = "https://api.sx.bet"
    
    # Market types that support mainline (have lines)
    mainline_supported_types = ["3", "201", "342", "2", "835", "28", "29", "166", "1536", "866", "165", "53", "64", "66", "77", "21", "45", "46", "281", "236"]
    
    # Sport selection
    sport_options = {
        "All Sports": None,
        "Baseball": "3",
        "Basketball": "1", 
        "Soccer": "5",
        "Football": "8",
        "Tennis": "6"
    }
    
    selected_sport = st.sidebar.selectbox("Sport", list(sport_options.keys()))
    sport_id = sport_options[selected_sport]
    
    # League filter
    # Initialize league options in session state
    if 'league_options' not in st.session_state:
        st.session_state.league_options = {"All Leagues": None}
    
    # Show league dropdown with current options
    selected_league = st.sidebar.selectbox("League", list(st.session_state.league_options.keys()), key="league_select")
    league_id = st.session_state.league_options[selected_league]
    
    # Show info about available leagues
    if len(st.session_state.league_options) > 1:
        st.sidebar.info(f"📊 {len(st.session_state.league_options) - 1} leagues with active markets")
    else:
        st.sidebar.info("🔄 Select a sport to see available leagues")
    
    # Market type selection
    # Initialize market type options in session state
    if 'market_type_options' not in st.session_state:
        st.session_state.market_type_options = {"All Types": None}
    
    # Show market type dropdown with current options
    selected_market_type = st.sidebar.selectbox("Type", list(st.session_state.market_type_options.keys()), key="market_type_select")
    market_type_id = st.session_state.market_type_options[selected_market_type]
    
    # Show info about available market types
    if len(st.session_state.market_type_options) > 1:
        st.sidebar.info(f"📊 {len(st.session_state.market_type_options) - 1} market types with active markets")
    else:
        st.sidebar.info("🔄 Select a sport to see available market types")
    
    # Mainline filter (only applies to market types with lines)
    mainline_options = {
        "All Markets": None,
        "Mainline Only": "true",
        "Non-Mainline Only": "false"
    }
    
    selected_mainline = st.sidebar.selectbox("Mainline", list(mainline_options.keys()))
    mainline_value = mainline_options[selected_mainline]
    
    # Show warning if mainline filter is selected but market type doesn't support it
    if mainline_value and market_type_id and market_type_id not in mainline_supported_types:
        st.sidebar.warning("⚠️ Mainline filter only applies to market types with lines (handicaps, over/under, etc.)")
    
    # Show info about mainline support for selected market type
    if market_type_id and market_type_id in mainline_supported_types:
        st.sidebar.info("✅ This market type supports mainline filtering")
    elif market_type_id:
        st.sidebar.info("ℹ️ This market type doesn't support mainline filtering")
    
    # Vig calculation button
    calculate_vig_button = st.sidebar.button("🚀 Calculate Vig for All Markets", help="Fetch best odds and calculate vigorish for all displayed markets")
    if calculate_vig_button:
        st.sidebar.success("✅ Vig calculation triggered!")
    
    # Fetch markets
    with st.spinner("Fetching markets..."):
        try:
            # Build parameters
            params = {}
            if sport_id:
                params['sportIds'] = sport_id
            if market_type_id:
                params['type'] = market_type_id
            if league_id:
                params['leagueId'] = league_id
            # Only apply mainline filter if market type supports it
            if mainline_value and (not market_type_id or market_type_id in mainline_supported_types):
                params['mainLine'] = mainline_value
            
            # Fetch all markets using pagination
            all_markets = []
            next_key = None
            page_count = 0
            
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            while True:
                page_count += 1
                status_text.text(f"Fetching page {page_count}...")
                
                # Add pagination key if we have one
                if next_key:
                    params['paginationKey'] = next_key
                
                # Make API call
                response = requests.get(f"{base_url}/markets/active", params=params)
                response.raise_for_status()
                
                data = response.json()
                markets_data = data.get('data', {})
                
                if isinstance(markets_data, dict):
                    page_markets = markets_data.get('markets', [])
                    next_key = markets_data.get('nextKey')
                else:
                    page_markets = markets_data if isinstance(markets_data, list) else []
                    next_key = None
                
                # Add markets from this page
                all_markets.extend(page_markets)
                
                # Update progress (estimate max 10 pages)
                progress = min(page_count / 10, 1.0)
                progress_bar.progress(progress)
                
                # Show current status
                status_text.text(f"Page {page_count}: {len(page_markets)} markets (Total: {len(all_markets)})")
                
                # Break if no more pages
                if not next_key:
                    break
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            markets = all_markets
            
            # Apply client-side mainline filtering if needed
            if mainline_value == "true":
                original_count = len(markets)
                markets = [market for market in markets if market.get('mainLine') == True]
                st.info(f"🔍 Filtered from {original_count} to {len(markets)} mainline markets")
            elif mainline_value == "false":
                original_count = len(markets)
                markets = [market for market in markets if market.get('mainLine') == False]
                st.info(f"🔍 Filtered from {original_count} to {len(markets)} non-mainline markets")
            
            st.success(f"✅ Found {len(markets)} total markets across {page_count} pages")
            
            # Extract unique leagues and market types from fetched markets
            unique_leagues = {}
            unique_market_types = {}
            
            # Market type name mapping for display
            market_type_names = {
                "1": "1X2",
                "52": "12",
                "88": "To Qualify",
                "226": "12 Including Overtime",
                "3": "Asian Handicap",
                "201": "Asian Handicap Games",
                "342": "Asian Handicap Including Overtime",
                "2": "Under/Over",
                "835": "Asian Under/Over",
                "28": "Under/Over Including Overtime",
                "29": "Under/Over Rounds",
                "166": "Under/Over Games",
                "1536": "Under/Over Maps",
                "274": "Outright Winner",
                "202": "First Period Winner",
                "203": "Second Period Winner",
                "204": "Third Period Winner",
                "205": "Fourth Period Winner",
                "866": "Set Spread",
                "165": "Set Total",
                "53": "Asian Handicap Halftime",
                "64": "Asian Handicap First Period",
                "65": "Asian Handicap Second Period",
                "66": "Asian Handicap Third Period",
                "63": "12 Halftime",
                "77": "Under/Over Halftime",
                "21": "Under/Over First Period",
                "45": "Under/Over Second Period",
                "46": "Under/Over Third Period",
                "281": "1st Five Innings Asian handicap",
                "1618": "1st 5 Innings Winner-12",
                "236": "1st 5 Innings Under/Over"
            }
            
            for market in markets:
                # Extract leagues
                league_id = market.get('leagueId')
                league_label = market.get('leagueLabel', f'League {league_id}')
                if league_id:
                    unique_leagues[str(league_id)] = league_label
                
                # Extract market types
                market_type_id = str(market.get('type', ''))
                if market_type_id:
                    market_type_name = market_type_names.get(market_type_id, f"Type {market_type_id}")
                    unique_market_types[market_type_id] = market_type_name
            
            # Update league and market type options
            needs_rerun = False
            
            # Update league options
            if st.session_state.get('current_sport_id') != sport_id:
                st.session_state.league_options = {"All Leagues": None}
                for league_id, league_name in unique_leagues.items():
                    st.session_state.league_options[league_name] = league_id
                needs_rerun = True
            
            # Update market type options
            if st.session_state.get('current_sport_id') != sport_id:
                st.session_state.market_type_options = {"All Types": None}
                for type_id, type_name in unique_market_types.items():
                    st.session_state.market_type_options[type_name] = type_id
                needs_rerun = True
            
            # Update sport ID
            st.session_state.current_sport_id = sport_id
            
            # Rerun if needed
            if needs_rerun:
                st.rerun()
            
            if markets:
                # Convert to DataFrame for display
                market_list = []
                
                # Initialize vig data for all markets
                vig_data = {
                    'Outcome A %': 'N/A',
                    'Outcome B %': 'N/A',
                    'Vig %': 'N/A'
                }
                
                for market in markets:
                    # Get market type name using the same mapping
                    market_type_id = str(market.get('type', ''))
                    market_type_name = market_type_names.get(market_type_id, f"Type {market_type_id}")
                    
                    market_data = {
                        'Market': f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}",
                        'Teams': f"{market.get('teamOneName', 'Unknown')} vs {market.get('teamTwoName', 'Unknown')}",
                        'Sport': market.get('sportLabel', 'Unknown'),
                        'League': market.get('leagueLabel', 'Unknown'),
                        'Type': market_type_name,
                        'Mainline': "Yes" if market.get('mainLine') else "No"
                    }
                    
                    # Add vig data to market data
                    market_data.update(vig_data)
                    
                    market_list.append(market_data)
                
                # Calculate vig when button is clicked
                if calculate_vig_button:
                    st.subheader("🎯 Calculating Vig for All Markets")
                    
                    # Progress bar for vig calculation
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("Calculating vig for markets...")
                    
                    # Store vig results
                    vig_results = []
                    
                    # Fetch all odds at once to avoid rate limiting
                    all_market_hashes = [market.get('marketHash') for market in markets if market.get('marketHash')]
                    league_id = markets[0].get('leagueId') if markets else None
                    
                    # Fetch odds individually for each market (since batch doesn't work)
                    st.info(f"🚀 Calculating vig for {len(markets)} markets...")
                    
                    for i, market in enumerate(markets):
                        market_hash = market.get('marketHash')
                        league_id = market.get('leagueId')
                        
                        if market_hash and league_id:
                            odds_data = fetch_best_odds(market_hash, league_id)
                            
                            if odds_data and 'outcome_a_odds' in odds_data:
                                vig_results.append({
                                    'index': i,
                                    'outcome_a': f"{odds_data['outcome_a_odds']:.2f}%",
                                    'outcome_b': f"{odds_data['outcome_b_odds']:.2f}%",
                                    'vig': f"{odds_data['vig_percentage']:.2f}%"
                                })
                        
                        # Update progress
                        progress = (i + 1) / len(markets)
                        progress_bar.progress(progress)
                        status_text.text(f"Calculating vig: {i + 1}/{len(markets)} markets")
                        
                        # Add small delay to avoid rate limiting
                        time.sleep(0.2)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Update DataFrame with vig results
                    if vig_results:
                        st.success(f"✅ Calculated vig for {len(vig_results)} markets!")
                        
                        # Create a new DataFrame with the vig data properly integrated
                        market_list_with_vig = []
                        
                        for i, market in enumerate(markets):
                            # Get market type name using the same mapping
                            market_type_id = str(market.get('type', ''))
                            market_type_name = market_type_names.get(market_type_id, f"Type {market_type_id}")
                            
                            # Find vig data for this market
                            vig_data = None
                            for result in vig_results:
                                if result['index'] == i:
                                    vig_data = result
                                    break
                            
                            market_data = {
                                'Market': f"{market.get('outcomeOneName', 'Unknown')} vs {market.get('outcomeTwoName', 'Unknown')}",
                                'Teams': f"{market.get('teamOneName', 'Unknown')} vs {market.get('teamTwoName', 'Unknown')}",
                                'Sport': market.get('sportLabel', 'Unknown'),
                                'League': market.get('leagueLabel', 'Unknown'),
                                'Type': market_type_name,
                                'Mainline': "Yes" if market.get('mainLine') else "No",
                                'Outcome A %': vig_data['outcome_a'] if vig_data else 'N/A',
                                'Outcome B %': vig_data['outcome_b'] if vig_data else 'N/A',
                                'Vig %': vig_data['vig'] if vig_data else 'N/A'
                            }
                            
                            market_list_with_vig.append(market_data)
                        
                        # Calculate and display average vig summary first
                        # Get league and type names for title
                        league_name = selected_league if selected_league != "All Leagues" else "All Leagues"
                        type_name = selected_market_type if selected_market_type != "All Types" else "All Types"
                        
                        st.subheader(f"📊 Vig Summary - {league_name} | {type_name}")
                        
                        # Extract vig percentages for calculation
                        vig_percentages = []
                        for vig_data in vig_results:
                            vig_str = vig_data['vig']
                            if vig_str != 'N/A':
                                vig_percentages.append(float(vig_str.replace('%', '')))
                        
                        if vig_percentages:
                            avg_vig = sum(vig_percentages) / len(vig_percentages)
                            min_vig = min(vig_percentages)
                            max_vig = max(vig_percentages)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Average Vig", f"{avg_vig:.2f}%")
                            with col2:
                                st.metric("Min Vig", f"{min_vig:.2f}%")
                            with col3:
                                st.metric("Max Vig", f"{max_vig:.2f}%")
                        else:
                            st.warning("No vig data available for summary")
                        
                        # Create new DataFrame with vig data
                        final_df = pd.DataFrame(market_list_with_vig)
                        st.dataframe(final_df, use_container_width=True)
                    else:
                        st.warning("⚠️ No vig data could be calculated")
                
                else:
                    # Show message prompting user to calculate vig
                    st.info("🎯 Click 'Calculate Vig for All Markets' in the sidebar to see the markets table with vig data")
                
            else:
                st.warning("No markets found")
                
        except requests.RequestException as e:
            st.error(f"Error fetching markets: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 