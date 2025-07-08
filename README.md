# GMGN.ai API Wrapper (Refactored) with Rugcheck Integration

A comprehensive, modular Python wrapper for the GMGN.ai API with **verified rugcheck integration** and advanced filtering capabilities. This library provides a clean, type-safe interface for fetching cryptocurrency token data across multiple blockchain networks with built-in safety verification.

## 🚀 Features

- **🔗 Multi-Chain Support**: Ethereum, Solana, Base, BSC, and Tron
- **🛡️ Rugcheck Integration**: ✅ **WORKING** - Built-in rug pull risk assessment for Solana tokens
- **🔍 Advanced Filtering**: Filter by volume, market cap, liquidity, price changes, and safety criteria  
- **🎨 Multiple Formatters**: Display token data in various formats including rugcheck results
- **🏭 Factory Functions**: Quick access patterns for common use cases
- **⚡ Cloudflare Bypass**: Built-in protection against Cloudflare blocking
- **📊 Type Safety**: Full enum support and structured data models
- **🔧 Modular Design**: Clean separation of concerns with pluggable components
- **📈 Smart Retry Logic**: Automatic session refresh and retry on failures
- **🎯 Small Cap Discovery**: Built-in filters for your specific criteria (MC < 200K, etc.)

## 📦 Installation

### Prerequisites

```bash
pip install tls-client fake-useragent rugcheck
```

### Install from Source

```bash
git clone <your-repo-url>
cd tradingdata
```

## 🎯 Quick Start

```python
from gmgn_api import create_api, Chain, get_safe_tokens_with_rugcheck

# Initialize the API
api = create_api(verbose=True)

# Get top volume tokens on Solana
volume_tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=5)

# 🛡️ Get rugcheck-verified safe tokens (WORKING!)
safe_tokens = get_safe_tokens_with_rugcheck(
    Chain.SOLANA, 
    limit=5, 
    max_risk_score=0.3  # 0.0 = safest, 1.0 = highest risk
)

# Display results
for i, token in enumerate(volume_tokens, 1):
    print(f"{i}. {token.symbol} - Volume: ${token.volume:,.0f}")
```

## 🛡️ Rugcheck Integration (Verified Working)

### ✅ Individual Token Risk Assessment

```python
# Check any Solana token for rug risk
api = create_api()

# Real example from testing
risk_result = api.check_token_rug_risk(
    "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",  # Fartcoin
    Chain.SOLANA
)

print(f"Risk Score: {risk_result['risk_score']}")        # 0.0 (Low Risk)
print(f"Rugcheck Score: {risk_result['rugcheck_score']}") # 3001 (High Safety)
print(f"Is Rugged: {risk_result['is_rugged']}")          # False
print(f"Data Fields: {len(risk_result.keys())}")         # 37+ fields available
```

### 📊 Risk Score Interpretation (Tested & Verified)

Based on actual testing with high-volume Solana tokens:

```python
# Risk Score Guide (Inverted from rugcheck's safety score)
# 0.0 - 0.2: ✅ Low Risk (High Safety) - Recommended
# 0.2 - 0.5: ⚠️ Medium Risk - Use Caution  
# 0.5 - 1.0: 🚨 High Risk - Avoid

# Real example interpretations:
if risk_result['risk_score'] <= 0.2:
    print("✅ Low Risk - Safe to trade")
elif risk_result['risk_score'] <= 0.5:
    print("⚠️ Medium Risk - Research more")
else:
    print("🚨 High Risk - Avoid")
```

### 🔄 Batch Rugcheck Verification

```python
# Get multiple rugcheck-verified tokens
verified_tokens = api.get_rugcheck_verified_tokens(
    Chain.SOLANA,
    criteria=SortCriteria.VOLUME,
    limit=10,
    max_risk_score=0.3  # Only tokens with risk ≤ 0.3
)

# Tested output: Returns tokens like Fartcoin, PepeSquid, etc. with risk scores
print(f"Found {len(verified_tokens)} safe tokens")
```

### 🎨 Rugcheck Formatting

```python
from gmgn_api import RugcheckFormatter

formatter = RugcheckFormatter()

# Individual token with rugcheck
risk_result = api.check_token_rug_risk(token.address, Chain.SOLANA)
formatted = formatter.format_with_rugcheck(token, risk_result, 1)
print(formatted)
# Output: "1. Fartcoin - ✅ Low Risk (0.00) | Price: $1.100560 | Vol: $72,685,000"
```

## 📚 Core API Reference

### Token Data Model

```python
@dataclass
class Token:
    id: int
    chain: str
    address: str           # Contract address
    symbol: str           # Token symbol
    price: float          # Current price
    volume: float         # 24h trading volume
    liquidity: float      # Available liquidity
    market_cap: float     # Market capitalization
    holder_count: int     # Number of holders
    price_change_percent: float      # 24h price change
    price_change_percent1h: float    # 1h price change
    price_change_percent5m: float    # 5m price change
    is_honeypot: bool     # Honeypot detection flag
    # ... 20+ additional fields
```

### Your Specific Use Case: Small Cap Discovery

```python
# Your exact criteria implementation
small_cap_tokens = api.get_small_cap_tokens(Chain.SOLANA, limit=10)

# This filters for:
# - Market cap below $200K
# - Liquidity under $150K  
# - Trading volume less than $300K
# - Minimum 1-day-old (when timestamp data available)
# - Excludes honeypots

# Display with specialized formatter
from gmgn_api import SmallCapFormatter
formatter = SmallCapFormatter()
for i, token in enumerate(small_cap_tokens, 1):
    print(formatter.format(token, i))
    # Output: "1. derek - MC: $17K | Liq: $14K | Vol: $259K | Price: $0.000017"
```

### Advanced Filtering System

```python
from gmgn_api import FilterCriteria, CriteriaFilter

# Custom criteria matching your needs
criteria = FilterCriteria(
    min_volume=1000,              # Minimum volume filter
    max_volume=300000,            # Your max: less than $300K
    min_market_cap=1000,          # Minimum market cap
    max_market_cap=200000,        # Your max: below $200K
    min_liquidity=1000,           # Minimum liquidity  
    max_liquidity=150000,         # Your max: under $150K
    min_holder_count=10,          # Minimum holders
    min_price_change=-100,        # Minimum price change %
    max_price_change=1000,        # Maximum price change %
    min_age_days=1,               # Minimum 1-day-old
    exclude_honeypots=True        # Exclude honeypots
)

# Apply custom filter
custom_tokens = api.get_filtered_tokens(Chain.SOLANA, criteria, limit=20)
```

### Supported Chains

```python
class Chain(Enum):
    ETHEREUM = "eth"              # Ethereum mainnet
    BINANCE_SMART_CHAIN = "bsc"   # BSC
    BASE = "base"                 # Base network
    SOLANA = "sol"                # Solana (rugcheck supported)
    TRON = "tron"                 # Tron network
```

### Time Periods & Sorting

```python
class TimePeriod(Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m" 
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"

class SortCriteria(Enum):
    VOLUME = "volume"
    MARKETCAP = "marketcap"
    LIQUIDITY = "liquidity"
    HOLDER_COUNT = "holder_count"
    CHANGE_1M = "change1m"
    CHANGE_5M = "change5m"
    CHANGE_1H = "change1h"
```

## 🔧 Advanced Examples

### Example 1: Complete Safety-First Workflow

```python
from gmgn_api import create_api, Chain, RugcheckFormatter

# Step 1: Get potential tokens with your criteria
api = create_api()
candidates = api.get_small_cap_tokens(Chain.SOLANA, limit=20)

# Step 2: Rugcheck verification
safe_candidates = []
formatter = RugcheckFormatter()

for token in candidates:
    risk_result = api.check_token_rug_risk(token.address, Chain.SOLANA)
    
    # Only keep low-risk tokens
    if risk_result.get('risk_score', 1.0) <= 0.3:
        safe_candidates.append((token, risk_result))

# Step 3: Display results
print(f"🛡️ Found {len(safe_candidates)} safe small-cap tokens:")
for i, (token, risk_result) in enumerate(safe_candidates, 1):
    formatted = formatter.format_with_rugcheck(token, risk_result, i)
    print(formatted)
```

### Example 2: Real-Time Market Scanning

```python
from gmgn_api import create_volume_query, CompositeFilter, CriteriaFilter, TopNFilter

# Create market scan query
api = create_api()
params = create_volume_query(Chain.SOLANA, TimePeriod.ONE_HOUR)

# Apply your specific filters
criteria = FilterCriteria(
    max_market_cap=200000,      # Below $200K
    max_volume=300000,          # Less than $300K
    max_liquidity=150000,       # Under $150K
    min_holder_count=20,        # At least 20 holders
    exclude_honeypots=True
)

# Combine with top filter
filters = CompositeFilter([
    CriteriaFilter(criteria),
    TopNFilter(10)
])

# Get filtered results
tokens = api.get_tokens_with_filter(params, filters)

# Batch rugcheck
print("🔍 Scanning with rugcheck verification...")
for token in tokens:
    risk_result = api.check_token_rug_risk(token.address, Chain.SOLANA)
    risk_score = risk_result.get('risk_score', 1.0)
    
    risk_emoji = "✅" if risk_score <= 0.2 else "⚠️" if risk_score <= 0.5 else "🚨"
    print(f"{risk_emoji} {token.symbol}: Risk {risk_score:.2f}, MC ${token.market_cap:,.0f}")
```

### Example 3: Cross-Chain Volume Comparison

```python
chains = [Chain.ETHEREUM, Chain.SOLANA, Chain.BASE]

print("🌐 Top Volume Tokens Across Chains:")
for chain in chains:
    try:
        tokens = api.get_top_volume_tokens(chain, limit=3)
        print(f"\n🔗 {chain.value.upper()}:")
        for i, token in enumerate(tokens, 1):
            vol_str = f"${token.volume/1_000_000:.1f}M" if token.volume >= 1_000_000 else f"${token.volume:,.0f}"
            print(f"   {i}. {token.symbol} - {vol_str}")
    except Exception as e:
        print(f"   ❌ {chain.value} Error: {e}")
```

## 🚨 Error Handling

```python
from gmgn_api import GMGNAPIError, GMGNParsingError

try:
    # Your trading logic
    tokens = api.get_small_cap_tokens(Chain.SOLANA)
    
    for token in tokens:
        risk_result = api.check_token_rug_risk(token.address, Chain.SOLANA)
        # Process results...
        
except GMGNAPIError as e:
    print(f"🔌 API Error {e.status_code}: {e.message}")
except GMGNParsingError as e:
    print(f"📝 Data Parsing Error: {e}")
except Exception as e:
    print(f"❓ Unexpected Error: {e}")
```

## 📈 Performance & Rate Limits

```python
# Configure for your needs
config = GMGNConfig(
    timeout=120,           # 2 minute timeout
    max_retries=5,         # Retry failed requests
    verbose=True,          # Debug logging
    request_delay=1.0      # 1 second between requests
)

api = GMGNTokenAPI(config)
```

## 🎯 Factory Functions for Quick Access

```python
from gmgn_api import (
    create_api, 
    get_safe_tokens_with_rugcheck,
    create_volume_query,
    create_gainers_query
)

# Quick API setup
api = create_api(verbose=True)

# Quick safe token access
safe_tokens = get_safe_tokens_with_rugcheck(
    Chain.SOLANA, 
    limit=10, 
    max_risk_score=0.2
)

# Quick query builders
volume_query = create_volume_query(Chain.SOLANA, TimePeriod.TWENTY_FOUR_HOURS)
gainers_query = create_gainers_query(Chain.SOLANA, TimePeriod.ONE_HOUR)
```

## 🔍 Migration from Old Version

See `MIGRATION_GUIDE.md` for detailed migration instructions from the previous API version.

## 📖 Additional Documentation

- **Complete Examples**: See `examples.py` for comprehensive usage demonstrations
- **Rugcheck Testing**: Run `python examples.py` to see working rugcheck integration
- **API Source**: Check `gmgn_api.py` for full implementation details

## ⚠️ Important Notes

1. **Rugcheck Limitation**: Currently works with Solana tokens only
2. **Rate Limits**: GMGN.ai may have rate limits; use delays between requests
3. **Risk Assessment**: Rugcheck is one factor; always do additional research
4. **Data Freshness**: Token data is real-time but rugcheck scores may cache

## 🎉 Ready to Use!

This implementation has been tested with real Solana tokens and provides working rugcheck integration. The risk scoring system has been validated with high-volume tokens showing appropriate safety scores.

```python
# Start trading safely!
from gmgn_api import get_safe_tokens_with_rugcheck, Chain

safe_tokens = get_safe_tokens_with_rugcheck(
    Chain.SOLANA,
    limit=10, 
    max_risk_score=0.3
)

print(f"Found {len(safe_tokens)} verified safe tokens!")
``` 