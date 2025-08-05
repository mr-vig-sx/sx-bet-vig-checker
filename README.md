# SX Bet Live Vig Tracker

A comprehensive tool for tracking live vigorish (vig) across SX Bet markets to identify value betting opportunities. This tool leverages the [SX Bet API](https://api.docs.sx.bet/) to provide real-time market analysis.

## Features

- **Real-time Vig Tracking**: Monitor live vig across all SX Bet markets
- **WebSocket Support**: Advanced version with real-time updates via WebSocket
- **Value Betting Detection**: Automatically identify low vig markets (<2%)
- **Multiple Interfaces**: Web dashboard, command-line interface, and advanced WebSocket tracker
- **Market Filtering**: Filter by sport, league, vig range, and live status
- **Analytics**: Vig distribution charts, trends, and summary statistics
- **Network Support**: Both mainnet and testnet support

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Vig\ Check
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Web Dashboard (Basic)

Run the basic web interface:
```bash
streamlit run sx_bet_vig_tracker.py
```

This provides:
- Sport and league selection
- Live market vig analysis
- Vig distribution charts
- Value betting opportunities
- Auto-refresh functionality

### 2. Advanced WebSocket Tracker

Run the advanced version with WebSocket support:
```bash
streamlit run sx_bet_websocket_tracker.py
```

This includes:
- Real-time WebSocket updates
- Order book monitoring
- Vig trend analysis
- Advanced filtering options
- Connection status monitoring

### 3. Command Line Interface

For quick vig checking without the web interface:

```bash
# Basic usage
python3 sx_vig_cli.py

# Use testnet
python3 sx_vig_cli.py --testnet

# Filter by vig range
python3 sx_vig_cli.py --min-vig 1.0 --max-vig 3.0

# List available sports
python3 sx_vig_cli.py --list-sports

# List leagues for a sport
python3 sx_vig_cli.py --list-leagues --sport <sport_id>

# Find value opportunities
python3 sx_vig_cli.py --value-threshold 1.5
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--testnet` | Use testnet instead of mainnet |
| `--sport <id>` | Filter by sport ID |
| `--league <id>` | Filter by league ID |
| `--min-vig <float>` | Minimum vig percentage (default: 0.0) |
| `--max-vig <float>` | Maximum vig percentage (default: 10.0) |
| `--sort-by <vig|name>` | Sort markets by vig or name |
| `--value-threshold <float>` | Vig threshold for value opportunities (default: 2.0) |
| `--list-sports` | List available sports |
| `--list-leagues` | List available leagues |

## Understanding Vig

**Vigorish (Vig)** is the bookmaker's built-in profit margin. It's calculated as:

```
Vig = (Total Implied Probability - 1) × 100%
```

Where:
- Total Implied Probability = (1/Outcome1_Odds) + (1/Outcome2_Odds)

**Example:**
- Outcome 1: 2.00 odds (50% implied probability)
- Outcome 2: 2.00 odds (50% implied probability)
- Total: 100% implied probability
- Vig: 0% (no vig, fair odds)

**Value Betting:**
- Markets with vig < 2% are considered good value
- Lower vig = better odds for bettors
- Higher vig = more profit for bookmakers

## SX Bet API Integration

This tool uses the following SX Bet API endpoints:

- **Metadata**: `/metadata` - Get network configuration
- **Sports**: `/sports` - Get available sports
- **Leagues**: `/leagues` - Get leagues by sport
- **Markets**: `/markets` - Get active markets
- **Best Odds**: `/markets/{marketHash}/best-odds` - Get best available odds
- **WebSocket**: Real-time market updates

### Odds Conversion

SX Bet uses implied odds format (e.g., "8391352143642350000"). The tool converts these to decimal odds:

```python
implied_decimal = implied_odds / 10^20
decimal_odds = 1 / implied_decimal
```

## Examples

### Find Low Vig Markets
```bash
python3 sx_vig_cli.py --min-vig 0.0 --max-vig 2.0 --value-threshold 1.5
```

### Monitor Specific Sport
```bash
python3 sx_vig_cli.py --sport football --sort-by vig
```

### Live Markets Only (Web Interface)
1. Open the web dashboard
2. Check "Live Markets Only"
3. Set vig range filters
4. Monitor real-time updates

## Network Configuration

### Mainnet
- **API URL**: https://api.sx.bet
- **WebSocket**: wss://api.sx.bet/ws
- **Chain ID**: 4162
- **USDC**: 0x6629Ce1Cf35Cc1329ebB4F63202F3f197b3F050B

### Testnet
- **API URL**: https://api.toronto.sx.bet
- **WebSocket**: wss://api.toronto.sx.bet/ws
- **Chain ID**: 79479957
- **USDC**: 0x1BC6326EA6aF2aB8E4b6Bc83418044B1923b2956

## Troubleshooting

### Connection Issues
- Check your internet connection
- Verify the API endpoints are accessible
- Try switching between mainnet/testnet

### No Markets Found
- Ensure you have the correct sport/league IDs
- Check if markets are currently active
- Verify the vig range filters

### WebSocket Connection
- The advanced tracker requires WebSocket support
- Some networks may block WebSocket connections
- Try using the basic version if WebSocket fails

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and informational purposes only. Always do your own research and consider the risks involved in betting. The authors are not responsible for any financial losses incurred through the use of this tool.

## Support

For issues and questions:
- Check the [SX Bet API documentation](https://api.docs.sx.bet/)
- Join the SX Bet Discord for technical support
- Open an issue in this repository

## Changelog

### v1.0.0
- Initial release
- Basic vig tracking functionality
- Web dashboard with Streamlit
- Command-line interface
- Advanced WebSocket tracker
- Support for mainnet and testnet 