# Migration Guide: From gmgntry.py to gmgntry_refactored.py

## Overview

The refactored version provides a more modular, extensible, and maintainable approach to using the GMGN.ai API. Here's how to migrate your existing code.

## Key Improvements

1. **Separation of Concerns**: Separate classes for HTTP client, data parsing, filtering, and formatting
2. **Configuration Management**: Centralized configuration with factory methods
3. **Structured Data Models**: Type-safe Token and QueryParameters models
4. **Pluggable Filtering**: Composable filter system
5. **Better Error Handling**: Custom exceptions with detailed error information
6. **Factory Functions**: Easy creation of common query patterns

## Migration Examples

### Basic Usage Migration

#### Old Way (gmgntry.py)
```python
from gmgntry import GMGNWrapper, Chain, TimePeriod, SortCriteria

# Initialize wrapper
gmgn = GMGNWrapper(verbose=True)

# Get Solana volume rankings
response = gmgn.get_solana_rankings(
    time_period=TimePeriod.TWENTY_FOUR_HOURS,
    criteria=SortCriteria.VOLUME
)

# Parse and display
token_data = parse_token_data(response, "Solana Volume")
for i, token in enumerate(token_data[:5], 1):
    print(format_token_info(token, i, "volume"))
```

#### New Way (gmgntry_refactored.py)
```python
from gmgntry_refactored import create_api, Chain, TimePeriod, VolumeFormatter

# Create API instance
api = create_api(verbose=True)

# Get top volume tokens directly
volume_tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=5)

# Format and display
formatter = VolumeFormatter()
for i, token in enumerate(volume_tokens, 1):
    print(formatter.format(token, i))
```

### Advanced Filtering Migration

#### Old Way (gmgntry.py)
```python
# Get filtered rankings with complex logic
filtered_results = gmgn.get_filtered_rankings(
    chain=Chain.SOLANA,
    primary_criteria=SortCriteria.VOLUME,
    criteria_filters={
        SortCriteria.VOLUME: 1000000,
        SortCriteria.MARKETCAP: 5000000
    },
    time_period=TimePeriod.TWENTY_FOUR_HOURS
)
```

#### New Way (gmgntry_refactored.py)
```python
from gmgntry_refactored import (
    create_api, Chain, QueryParameters, SortCriteria, TimePeriod,
    CriteriaFilter, FilterCriteria, TopNFilter, CompositeFilter
)

api = create_api()

# Method 1: Use built-in high-value method
high_value_tokens = api.get_high_value_tokens(
    Chain.SOLANA, 
    min_volume=1000000, 
    min_market_cap=5000000, 
    limit=10
)

# Method 2: Custom filtering approach
params = QueryParameters(
    chain=Chain.SOLANA,
    time_period=TimePeriod.TWENTY_FOUR_HOURS,
    criteria=SortCriteria.VOLUME
)

# Create composite filter
volume_filter = CriteriaFilter(FilterCriteria(
    min_volume=1000000,
    min_market_cap=5000000
))
top_filter = TopNFilter(10)
composite_filter = CompositeFilter([volume_filter, top_filter])

# Apply filters
filtered_tokens = api.get_tokens_with_filter(params, composite_filter)
```

### Top Gainers Migration

#### Old Way (gmgntry.py)
```python
# Get top gainers
gainers = gmgn.get_top_gainers(Chain.SOLANA, TimePeriod.ONE_HOUR)
token_data = parse_token_data(gainers, "Solana Gainers")

for i, token in enumerate(token_data[:3], 1):
    print(format_token_info(token, i, "gainers"))
```

#### New Way (gmgntry_refactored.py)
```python
from gmgntry_refactored import create_api, Chain, TimePeriod, GainersFormatter

api = create_api()

# Get top gainers directly
gainers = api.get_top_gainers(Chain.SOLANA, TimePeriod.ONE_HOUR, limit=3)

# Format output
formatter = GainersFormatter()
for i, token in enumerate(gainers, 1):
    print(formatter.format(token, i))
```

### Safe Tokens Migration

#### Old Way (gmgntry.py)
```python
# Get safe tokens with all filters
safe_tokens = gmgn.get_safe_tokens(
    chain=Chain.SOLANA,
    time_period=TimePeriod.TWENTY_FOUR_HOURS,
    criteria=SortCriteria.VOLUME
)
```

#### New Way (gmgntry_refactored.py)
```python
# Much simpler
safe_tokens = api.get_safe_tokens(Chain.SOLANA, criteria=SortCriteria.VOLUME, limit=10)
```

## New Features in Refactored Version

### 1. Configuration Management
```python
from gmgntry_refactored import GMGNConfig, GMGNTokenAPI

# Custom configuration
config = GMGNConfig(
    timeout=120,
    max_retries=5,
    verbose=True
)
api = GMGNTokenAPI(config)
```

### 2. Structured Token Objects
```python
# Access token properties directly
for token in volume_tokens:
    print(f"Symbol: {token.symbol}")
    print(f"Price: ${token.price:.6f}")
    print(f"Volume: ${token.volume:,.0f}")
    print(f"Market Cap: ${token.market_cap:,.0f}")
    print(f"Is Honeypot: {bool(token.is_honeypot)}")
```

### 3. Custom Filters
```python
from gmgntry_refactored import FilterCriteria

# Create custom filter criteria
custom_criteria = FilterCriteria(
    min_volume=100000,
    min_market_cap=500000,
    min_holder_count=100,
    min_price_change=5.0,  # At least 5% gain
    exclude_honeypots=True
)

filter_instance = CriteriaFilter(custom_criteria)
filtered_tokens = api.get_tokens_with_filter(params, filter_instance)
```

### 4. Multiple Formatters
```python
from gmgntry_refactored import (
    GeneralFormatter, VolumeFormatter, 
    MarketCapFormatter, GainersFormatter
)

# Different formatting styles
general_fmt = GeneralFormatter()
volume_fmt = VolumeFormatter()
mcap_fmt = MarketCapFormatter()
gainers_fmt = GainersFormatter()

# Use appropriate formatter for your use case
formatted_lines = api.get_formatted_tokens(params, volume_fmt, filter_instance)
for line in formatted_lines:
    print(line)
```

### 5. Factory Functions
```python
from gmgntry_refactored import create_volume_query, create_gainers_query

# Quick query creation
volume_query = create_volume_query(Chain.SOLANA)
gainers_query = create_gainers_query(Chain.SOLANA, TimePeriod.ONE_HOUR)

tokens = api.get_tokens(volume_query)
```

## Error Handling Migration

#### Old Way (gmgntry.py)
```python
try:
    response = gmgn.get_token_rankings(...)
    # Manual error checking
    if not response or 'data' not in response:
        print("API error")
        return
except Exception as e:
    print(f"Error: {e}")
```

#### New Way (gmgntry_refactored.py)
```python
from gmgntry_refactored import GMGNAPIError, GMGNParsingError

try:
    tokens = api.get_tokens(params)
except GMGNAPIError as e:
    print(f"API Error {e.status_code}: {e.message}")
except GMGNParsingError as e:
    print(f"Parsing Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
```

## Benefits of Migration

1. **Type Safety**: Structured Token objects with proper typing
2. **Modularity**: Easy to extend with custom filters and formatters
3. **Better Errors**: Specific exception types with detailed information
4. **Configuration**: Centralized config management
5. **Testability**: Easier to unit test individual components
6. **Readability**: Cleaner, more expressive code
7. **Maintainability**: Clear separation of concerns

## Complete Migration Example

Here's a complete example showing how to migrate a complex use case:

#### Old Way (gmgntry.py)
```python
def find_promising_tokens():
    gmgn = GMGNWrapper(verbose=False)
    
    # Get high volume tokens
    volume_response = gmgn.get_token_rankings(
        chain=Chain.SOLANA,
        time_period=TimePeriod.TWENTY_FOUR_HOURS,
        criteria=SortCriteria.VOLUME
    )
    
    # Parse and filter manually
    volume_tokens = parse_token_data(volume_response)
    filtered = []
    
    for token in volume_tokens:
        if (token.get('volume', 0) > 1000000 and 
            token.get('market_cap', 0) > 5000000 and
            token.get('price_change_percent1h', 0) > 0):
            filtered.append(token)
    
    # Format output manually
    for i, token in enumerate(filtered[:5], 1):
        symbol = token.get('symbol', 'Unknown')
        volume = token.get('volume', 0)
        mcap = token.get('market_cap', 0)
        change = token.get('price_change_percent1h', 0)
        print(f"{i}. {symbol} - Vol: ${volume:,.0f} MC: ${mcap:,.0f} 1h: {change:.2f}%")
```

#### New Way (gmgntry_refactored.py)
```python
def find_promising_tokens():
    from gmgntry_refactored import (
        create_api, Chain, QueryParameters, SortCriteria, TimePeriod,
        CriteriaFilter, FilterCriteria, TopNFilter, CompositeFilter
    )
    
    api = create_api()
    
    # Create query parameters
    params = QueryParameters(
        chain=Chain.SOLANA,
        time_period=TimePeriod.TWENTY_FOUR_HOURS,
        criteria=SortCriteria.VOLUME
    )
    
    # Create composite filter
    criteria_filter = CriteriaFilter(FilterCriteria(
        min_volume=1000000,
        min_market_cap=5000000,
        min_price_change=0  # Positive change
    ))
    top_filter = TopNFilter(5)
    composite_filter = CompositeFilter([criteria_filter, top_filter])
    
    # Get filtered tokens
    tokens = api.get_tokens_with_filter(params, composite_filter)
    
    # Format output
    for i, token in enumerate(tokens, 1):
        print(f"{i}. {token.symbol} - Vol: ${token.volume:,.0f} MC: ${token.market_cap:,.0f} 1h: {token.price_change_percent1h:.2f}%")
```

The refactored version is much cleaner, more maintainable, and easier to extend with new features! 