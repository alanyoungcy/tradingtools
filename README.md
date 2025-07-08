# GMGN.ai API Wrapper

A comprehensive Python wrapper for the GMGN.ai API with Cloudflare bypass capabilities. This library allows you to fetch cryptocurrency token rankings, analyze trading data, and apply advanced filtering across multiple blockchain networks.

## 🚀 Features

- **Multi-Chain Support**: Ethereum, Solana, Base, BSC, and Tron
- **Cloudflare Bypass**: Built-in protection against Cloudflare blocking
- **Advanced Filtering**: Filter tokens by volume, market cap, liquidity, and safety criteria
- **Multiple Sorting Options**: Sort by volume, price changes, market cap, holder count, and more
- **Smart Retry Logic**: Automatic session refresh and retry on failures
- **Type Safety**: Full enum support for parameters
- **Flexible API**: Convenience methods and advanced filtering options

## 📦 Installation

### Prerequisites

```bash
pip install tls-client fake-useragent
```

### Install from Source

```bash
git clone <your-repo-url>
cd tradingdata
pip install -r requirements.txt  # If you have one
```

## 🎯 Quick Start

```python
from gmgntry import GMGNWrapper, Chain, TimePeriod, SortCriteria

# Initialize the wrapper
gmgn = GMGNWrapper(verbose=True)

# Get top Solana tokens by volume
response = gmgn.get_solana_rankings()
tokens = parse_token_data(response, "Solana Volume")

# Display results
for i, token in enumerate(tokens[:5], 1):
    if isinstance(token, dict):
        print(f"{i}. {token.get('symbol', 'Unknown')} - "
              f"Volume: ${token.get('volume', 0):,.0f}")
```

## 📚 API Reference

### Core Classes

#### GMGNWrapper

Main wrapper class for interacting with GMGN.ai API.

```python
gmgn = GMGNWrapper(timeout=60, verbose=False)
```

**Parameters:**
- `timeout` (int): Request timeout in seconds (default: 60)
- `verbose` (bool): Enable debug output (default: False)

#### Enums

```python
# Supported blockchains
class Chain(Enum):
    ETHEREUM = "eth"
    BINANCE_SMART_CHAIN = "bsc"
    BASE = "base"
    SOLANA = "sol"
    TRON = "tron"

# Time periods for analysis
class TimePeriod(Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"

# Sorting criteria
class SortCriteria(Enum):
    OPEN_TIMESTAMP = "open_timestamp"    # Age
    LIQUIDITY = "liquidity"              # Liquidity
    MARKETCAP = "marketcap"              # Market Cap
    HOLDER_COUNT = "holder_count"        # Holders
    SMARTMONEY = "smartmoney"            # Smart Transactions
    SWAPS = "swaps"                      # 24h Transactions
    VOLUME = "volume"                    # 24h Volume
    PRICE = "price"                      # Price
    CHANGE_1M = "change1m"               # 1m% Change
    CHANGE_5M = "change5m"               # 5m% Change
    CHANGE_1H = "change1h"               # 1h% Change
```

### Core Methods

#### get_token_rankings()

Get token rankings with full customization.

```python
def get_token_rankings(
    chain: Chain,
    time_period: TimePeriod,
    criteria: SortCriteria,
    direction: SortDirection = SortDirection.DESCENDING,
    include_not_honeypot: bool = True,
    include_verified: bool = False,
    include_renounced: bool = False
) -> Dict[str, Any]
```

**Example:**
```python
# Get Ethereum tokens by market cap with safety filters
response = gmgn.get_token_rankings(
    chain=Chain.ETHEREUM,
    time_period=TimePeriod.TWENTY_FOUR_HOURS,
    criteria=SortCriteria.MARKETCAP,
    include_not_honeypot=True,
    include_verified=True,
    include_renounced=True
)
```

### Convenience Methods

#### Chain-Specific Methods

```python
# Quick access to popular chains
eth_tokens = gmgn.get_ethereum_rankings()
sol_tokens = gmgn.get_solana_rankings()
base_tokens = gmgn.get_base_rankings()
```

#### Price Movement Analysis

```python
# Get top gainers/losers
gainers = gmgn.get_top_gainers(Chain.SOLANA, TimePeriod.ONE_HOUR)
losers = gmgn.get_top_losers(Chain.SOLANA, TimePeriod.ONE_HOUR)
```

#### Safety-First Approach

```python
# Get tokens with all safety filters enabled
safe_tokens = gmgn.get_safe_tokens(
    chain=Chain.SOLANA,
    criteria=SortCriteria.VOLUME
)
```

### Advanced Filtering

#### Monetary Value Filtering

Filter tokens by actual dollar amounts:

```python
# Filter by minimum thresholds
filtered_tokens = gmgn.get_filtered_rankings(
    chain=Chain.SOLANA,
    primary_criteria=SortCriteria.VOLUME,
    criteria_filters={
        SortCriteria.VOLUME: 1_000_000,      # Min $1M volume
        SortCriteria.MARKETCAP: 5_000_000,   # Min $5M market cap
        SortCriteria.LIQUIDITY: 100_000      # Min $100K liquidity
    }
)
```

#### High-Value Token Detection

```python
# Preset high-value filters
high_value = gmgn.get_high_value_tokens(
    chain=Chain.SOLANA,
    min_volume=500_000,       # $500K min volume
    min_market_cap=1_000_000, # $1M min market cap
    min_liquidity=100_000     # $100K min liquidity
)
```

#### Sequential Multi-Criteria Filtering

```python
# Apply multiple criteria sequentially
multi_filtered = gmgn.get_sequential_filtered_rankings(
    chain=Chain.SOLANA,
    criteria_sequence=[
        SortCriteria.VOLUME,      # Start with volume
        SortCriteria.MARKETCAP,   # Then filter by market cap
        SortCriteria.CHANGE_1H    # Finally by price change
    ],
    tokens_per_step=30
)
```

## 🔧 Configuration

### Security Filters

The wrapper supports three main security filters:

- **`include_not_honeypot`**: Filters out honeypot tokens (default: True)
- **`include_verified`**: Only verified tokens (default: False for broader results)
- **`include_renounced`**: Only tokens with renounced ownership (default: False)

### Cloudflare Bypass

The wrapper automatically handles Cloudflare protection:

```python
# Manual session refresh if needed
gmgn.refresh_session()

# The wrapper automatically retries with fresh sessions on 403/503 errors
```

## 📊 Data Structure

### Token Response Format

Each token contains the following fields:

```python
{
    "id": int,
    "chain": str,
    "address": str,
    "symbol": str,
    "price": float,
    "price_change_percent": float,
    "price_change_percent1h": float,
    "volume": float,
    "liquidity": float,
    "market_cap": float,
    "holder_count": int,
    "swaps": int,
    "smart_buy_24h": int,
    "smart_sell_24h": int,
    # ... additional fields
}
```

### Helper Functions

#### parse_token_data()

Safely parse GMGN API responses:

```python
tokens = parse_token_data(response, "Response Name")
```

#### format_token_info()

Format token information for display:

```python
formatted = format_token_info(token, index=1, info_type="volume")
print(formatted)
# Output: 1. SYMBOL - Volume: $1,234,567 | Price: $0.123
```

## 🚦 Error Handling

The wrapper includes robust error handling:

```python
try:
    tokens = gmgn.get_solana_rankings()
except Exception as e:
    print(f"Error fetching data: {e}")
    # The wrapper automatically retries failed requests
    # with fresh Cloudflare bypass sessions
```

### Common Issues

1. **Empty Results**: Reduce filter strictness
2. **403 Errors**: Cloudflare blocking (automatically handled)
3. **Timeout**: Increase timeout parameter

## 🔍 Examples

### Example 1: Market Analysis

```python
from gmgntry import GMGNWrapper, Chain, SortCriteria, parse_token_data

gmgn = GMGNWrapper(verbose=False)

# Get top volume tokens
response = gmgn.get_token_rankings(
    chain=Chain.SOLANA,
    time_period=TimePeriod.TWENTY_FOUR_HOURS,
    criteria=SortCriteria.VOLUME
)

tokens = parse_token_data(response, "Solana Volume")
print(f"Found {len(tokens)} tokens")

for i, token in enumerate(tokens[:10], 1):
    if isinstance(token, dict):
        symbol = token.get('symbol', 'Unknown')
        volume = token.get('volume', 0)
        price = token.get('price', 0)
        print(f"{i:2d}. {symbol:12s} | ${volume:>12,.0f} | ${price}")
```

### Example 2: Safety-First Investment Research

```python
# Find safe, high-volume tokens
safe_tokens = gmgn.get_filtered_rankings(
    chain=Chain.ETHEREUM,
    primary_criteria=SortCriteria.VOLUME,
    criteria_filters={
        SortCriteria.VOLUME: 2_000_000,     # Min $2M daily volume
        SortCriteria.MARKETCAP: 10_000_000, # Min $10M market cap
        SortCriteria.LIQUIDITY: 500_000,    # Min $500K liquidity
    }
)

print(f"Found {len(safe_tokens)} safe tokens meeting criteria")
```

### Example 3: Price Movement Analysis

```python
# Track hourly price movements
gainers = gmgn.get_top_gainers(Chain.SOLANA, TimePeriod.ONE_HOUR)
tokens = parse_token_data(gainers, "Hourly Gainers")

for i, token in enumerate(tokens[:5], 1):
    if isinstance(token, dict):
        symbol = token.get('symbol', 'Unknown')
        change_1h = token.get('price_change_percent1h', 0)
        volume = token.get('volume', 0)
        print(f"{i}. {symbol:10s} | +{change_1h:6.2f}% | Vol: ${volume:,.0f}")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This wrapper is for educational and research purposes. Always verify data independently before making investment decisions. The authors are not responsible for any financial losses.

## 🔗 Related Projects

- [GMGN.ai Official Website](https://gmgn.ai)
- [TLS Client Documentation](https://github.com/FlorianREGAZ/Python-Tls-Client)

## 📞 Support

If you encounter issues:

1. Check the verbose output for detailed error messages
2. Verify your internet connection and firewall settings
3. Try refreshing the session manually with `gmgn.refresh_session()`
4. Open an issue with detailed error logs

---

**Made with ❤️ for the crypto community** 