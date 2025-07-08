import json
import random
from typing import Optional, List, Dict, Any
from enum import Enum
import tls_client
from fake_useragent import UserAgent

class Chain(Enum):
    """Supported blockchain chains"""
    ETHEREUM = "eth"
    BINANCE_SMART_CHAIN = "bsc" 
    BASE = "base"
    SOLANA = "sol"
    TRON = "tron"


class TimePeriod(Enum):
    """Supported time periods"""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"


class SortCriteria(Enum):
    """Supported sorting criteria"""
    OPEN_TIMESTAMP = "open_timestamp"  # Age
    LIQUIDITY = "liquidity"           # Liq
    MARKETCAP = "marketcap"          # MC
    BLUECHIP_OWNER_PERCENTAGE = "bluechip_owner_percentage"  # BlueChip
    HOLDER_COUNT = "holder_count"     # Holders
    SMARTMONEY = "smartmoney"        # SmartTxn
    SWAPS = "swaps"                  # 24h TXs
    VOLUME = "volume"                # 24h Volume
    PRICE = "price"                  # Price
    CHANGE_1M = "change1m"           # 1m%
    CHANGE_5M = "change5m"           # 5m%
    CHANGE_1H = "change1h"           # 1h%


class SortDirection(Enum):
    """Supported sort directions"""
    ASCENDING = "asc"
    DESCENDING = "desc"


class GMGNWrapper:
    """
    GMGN.ai API wrapper for ranking tokens by swaps with Cloudflare bypass
    """
    
    BASE_URL = "https://gmgn.ai/defi/quotation/v1/rank"
    
    def __init__(self, timeout: int = 60, verbose: bool = False):
        """
        Initialize the GMGN wrapper with Cloudflare bypass
        
        Args:
            timeout: Request timeout in seconds
            verbose: Whether to print retry attempts and session refreshes
        """
        self.timeout = timeout
        self.verbose = verbose
        self.randomiseRequest()
    
    def randomiseRequest(self):
        """
        Randomize browser identifiers and headers to avoid Cloudflare detection
        """
        self.identifier = random.choice(
            [browser for browser in tls_client.settings.ClientIdentifiers.__args__
             if browser.startswith(('chrome', 'safari', 'firefox', 'opera'))]
        )
        parts = self.identifier.split('_')
        identifier, version, *rest = parts
        identifier = identifier.capitalize()
        
        self.session = tls_client.Session(
            random_tls_extension_order=True, 
            client_identifier=self.identifier
        )
        self.session.timeout_seconds = self.timeout

        if identifier == 'Opera':
            identifier = 'Chrome'
            osType = 'Windows'
        elif version.lower() == 'ios':
            osType = 'iOS'
        else:
            osType = 'Windows'

        try:
            self.user_agent = UserAgent(os=[osType]).random
        except Exception:
            self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0"

        self.headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://gmgn.ai/?chain=sol',
            'user-agent': self.user_agent
        }
    
    def refresh_session(self):
        """
        Refresh the session with new random identifiers
        Useful if requests start getting blocked
        """
        self.randomiseRequest()
    
    def get_token_rankings(
        self,
        chain: Chain,
        time_period: TimePeriod,
        criteria: SortCriteria,
        direction: SortDirection = SortDirection.DESCENDING,
        include_not_honeypot: bool = True,
        include_verified: bool = False,  # Changed to False - less restrictive
        include_renounced: bool = False  # Changed to False - less restrictive
    ) -> Dict[str, Any]:
        """
        Get token rankings from GMGN.ai
        
        Args:
            chain: Blockchain to query
            time_period: Time period for ranking
            criteria: Sorting criteria
            direction: Sort direction (default: descending)
            include_not_honeypot: Filter out honeypot tokens (default: True)
            include_verified: Include only verified tokens (default: False - less restrictive)
            include_renounced: Include only tokens with renounced ownership (default: False - less restrictive)
            
        Note: The combination of all three filters can be very restrictive and may return 0 results.
        By default, only honeypot filtering is applied for broader results.
            
        Returns:
            Dictionary containing API response
            
        Raises:
            Exception: If API request fails
            ValueError: If invalid parameters provided
        """
        self.randomiseRequest()
        # Validate inputs
        if not isinstance(chain, Chain):
            raise ValueError(f"Invalid chain. Must be one of: {list(Chain)}")
        if not isinstance(time_period, TimePeriod):
            raise ValueError(f"Invalid time_period. Must be one of: {list(TimePeriod)}")
        if not isinstance(criteria, SortCriteria):
            raise ValueError(f"Invalid criteria. Must be one of: {list(SortCriteria)}")
        if not isinstance(direction, SortDirection):
            raise ValueError(f"Invalid direction. Must be one of: {list(SortDirection)}")
        
        # Build URL
        url = f"{self.BASE_URL}/{chain.value}/swaps/{time_period.value}"
        
        # Build query parameters as list of tuples to handle multiple filters[] params
        params = [
            ('orderby', criteria.value),
            ('direction', direction.value)
        ]
        
        # Add filters as separate filters[] parameters
        if include_not_honeypot:
            params.append(('filters[]', 'not_honeypot'))
        if include_verified:
            params.append(('filters[]', 'verified'))
        if include_renounced:
            params.append(('filters[]', 'renounced'))
        
        # Debug output
        if self.verbose:
            print(f"DEBUG - Requesting URL: {url}")
            print(f"DEBUG - Parameters: {params}")
        
        # Retry logic with session refresh for Cloudflare bypass
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, headers=self.headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [403, 429, 503]:  # Cloudflare blocks
                    raise Exception(f"Cloudflare block detected (status {response.status_code})")
                else:
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")
                    
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    if self.verbose:
                        print(f"Attempt {attempt + 1} failed: {str(e)}")
                        print("Refreshing session and retrying...")
                    self.refresh_session()
                else:
                    break
        
        raise Exception(f"All {max_retries} attempts failed. Last error: {str(last_exception)}")
    
    def get_ethereum_rankings(
        self,
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS,
        criteria: SortCriteria = SortCriteria.VOLUME,
        direction: SortDirection = SortDirection.DESCENDING
    ) -> Dict[str, Any]:
        """
        Convenience method for Ethereum token rankings
        """
        return self.get_token_rankings(Chain.ETHEREUM, time_period, criteria, direction)
    
    def get_solana_rankings(
        self,
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS,
        criteria: SortCriteria = SortCriteria.VOLUME,
        direction: SortDirection = SortDirection.DESCENDING
    ) -> Dict[str, Any]:
        """
        Convenience method for Solana token rankings
        """
        return self.get_token_rankings(Chain.SOLANA, time_period, criteria, direction)
    
    def get_base_rankings(
        self,
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS,
        criteria: SortCriteria = SortCriteria.VOLUME,
        direction: SortDirection = SortDirection.DESCENDING
    ) -> Dict[str, Any]:
        """
        Convenience method for Base token rankings
        """
        return self.get_token_rankings(Chain.BASE, time_period, criteria, direction)
    
    def get_safe_tokens(
        self,
        chain: Chain,
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS,
        criteria: SortCriteria = SortCriteria.VOLUME,
        direction: SortDirection = SortDirection.DESCENDING
    ) -> Dict[str, Any]:
        """
        Get tokens with all safety filters applied (stricter filtering)
        This applies all three filters: not_honeypot, verified, and renounced
        May return fewer results due to strict filtering.
        """
        return self.get_token_rankings(
            chain, time_period, criteria, direction,
            include_not_honeypot=True,
            include_verified=True,
            include_renounced=True
        )
    
    def get_top_gainers(
        self,
        chain: Chain,
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS
    ) -> Dict[str, Any]:
        """
        Get top gaining tokens by price change
        """
        if time_period == TimePeriod.ONE_MINUTE:
            criteria = SortCriteria.CHANGE_1M
        elif time_period == TimePeriod.FIVE_MINUTES:
            criteria = SortCriteria.CHANGE_5M
        elif time_period == TimePeriod.ONE_HOUR:
            criteria = SortCriteria.CHANGE_1H
        else:
            criteria = SortCriteria.CHANGE_1H  # Default to 1h change for longer periods
            
        return self.get_token_rankings(chain, time_period, criteria, SortDirection.DESCENDING)
    
    def get_top_losers(
        self,
        chain: Chain,
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS
    ) -> Dict[str, Any]:
        """
        Get top losing tokens by price change
        """
        if time_period == TimePeriod.ONE_MINUTE:
            criteria = SortCriteria.CHANGE_1M
        elif time_period == TimePeriod.FIVE_MINUTES:
            criteria = SortCriteria.CHANGE_5M
        elif time_period == TimePeriod.ONE_HOUR:
            criteria = SortCriteria.CHANGE_1H
        else:
            criteria = SortCriteria.CHANGE_1H  # Default to 1h change for longer periods
            
        return self.get_token_rankings(chain, time_period, criteria, SortDirection.ASCENDING)

    def get_filtered_rankings(
        self,
        chain: Chain,
        primary_criteria: SortCriteria,
        criteria_filters: Dict[SortCriteria, float],
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS,
        direction: SortDirection = SortDirection.DESCENDING
    ) -> List[Dict[str, Any]]:
        """
        Get token rankings filtered by monetary value thresholds
        
        Args:
            chain: Blockchain to query
            primary_criteria: Main sorting criteria (e.g., SortCriteria.VOLUME)
            criteria_filters: Dict mapping criteria to minimum values (e.g., {SortCriteria.VOLUME: 1000000, SortCriteria.MARKETCAP: 5000000})
            time_period: Time period for ranking
            direction: Sort direction
            
        Returns:
            List of tokens sorted by primary criteria and filtered by minimum values
        """
        if not criteria_filters:
            raise ValueError("criteria_filters cannot be empty")
        
        print(f"Filtering tokens by: {[(k.value, f'${v:,.0f}') for k, v in criteria_filters.items()]}")
        print(f"Primary sorting by: {primary_criteria.value}")
        
        # Get tokens sorted by primary criteria
        response = self.get_token_rankings(
            chain=chain,
            time_period=time_period,
            criteria=primary_criteria,
            direction=direction
        )
        
        token_data = parse_token_data(response, f"{primary_criteria.value} ranking")
        
        if not token_data:
            return []
        
        # Filter tokens based on criteria values
        filtered_tokens = []
        
        for token in token_data:
            if not isinstance(token, dict):
                continue
                
            # Check if token meets all filter criteria
            meets_criteria = True
            
            for filter_criteria, min_value in criteria_filters.items():
                # Map criteria to token field names (from GMGN API response)
                field_mapping = {
                    SortCriteria.VOLUME: 'volume',
                    SortCriteria.MARKETCAP: 'market_cap',
                    SortCriteria.LIQUIDITY: 'liquidity',
                    SortCriteria.PRICE: 'price',
                    SortCriteria.HOLDER_COUNT: 'holder_count',
                    SortCriteria.SWAPS: 'swaps',
                    SortCriteria.SMARTMONEY: 'smart_buy_24h',
                    SortCriteria.CHANGE_1M: 'price_change_percent1m',
                    SortCriteria.CHANGE_5M: 'price_change_percent5m',
                    SortCriteria.CHANGE_1H: 'price_change_percent1h'
                }
                
                field_name = field_mapping.get(filter_criteria)
                if not field_name:
                    print(f"Warning: No field mapping for {filter_criteria.value}")
                    continue
                
                token_value = token.get(field_name, 0)
                
                # Handle None values
                if token_value is None:
                    token_value = 0
                
                # Convert to float for comparison
                try:
                    token_value = float(token_value)
                except (ValueError, TypeError):
                    token_value = 0
                
                if token_value < min_value:
                    meets_criteria = False
                    break
            
            if meets_criteria:
                # Add filter status for debugging
                token['_filter_status'] = {
                    filter_criteria.value: {
                        'value': token.get(field_mapping.get(filter_criteria), 0),
                        'threshold': min_value,
                        'passed': True
                    }
                    for filter_criteria, min_value in criteria_filters.items()
                    if field_mapping.get(filter_criteria)
                }
                filtered_tokens.append(token)
        
        print(f"Filtered to {len(filtered_tokens)} tokens from {len(token_data)} total")
        return filtered_tokens

    def get_sequential_filtered_rankings(
        self,
        chain: Chain,
        criteria_sequence: List[SortCriteria],
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS,
        tokens_per_step: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Apply multiple criteria sequentially to filter and refine results
        
        Args:
            chain: Blockchain to query
            criteria_sequence: List of criteria to apply in order (e.g., [VOLUME, MARKETCAP, CHANGE_1H])
            time_period: Time period for ranking
            tokens_per_step: Number of tokens to keep at each filtering step
            
        Returns:
            List of tokens that rank well across all criteria
        """
        if not criteria_sequence:
            raise ValueError("criteria_sequence cannot be empty")
        
        print(f"Sequential filtering with criteria: {[c.value for c in criteria_sequence]}")
        
        # Start with first criteria
        first_criteria = criteria_sequence[0]
        print(f"Step 1: Getting top {tokens_per_step} tokens by {first_criteria.value}")
        
        response = self.get_token_rankings(
            chain=chain,
            time_period=time_period,
            criteria=first_criteria,
            direction=SortDirection.DESCENDING
        )
        
        token_data = parse_token_data(response, f"Step 1 - {first_criteria.value}")
        if not token_data:
            return []
        
        # Keep top tokens from first criteria
        current_tokens = token_data[:tokens_per_step]
        
        # Apply remaining criteria as filters
        for step, criteria in enumerate(criteria_sequence[1:], 2):
            print(f"Step {step}: Filtering by {criteria.value}")
            
            # Get full ranking for this criteria
            response = self.get_token_rankings(
                chain=chain,
                time_period=time_period,
                criteria=criteria,
                direction=SortDirection.DESCENDING
            )
            
            full_ranking = parse_token_data(response, f"Step {step} - {criteria.value}")
            if not full_ranking:
                continue
            
            # Create ranking lookup
            criteria_ranks = {}
            for rank, token in enumerate(full_ranking, 1):
                if isinstance(token, dict) and 'id' in token:
                    criteria_ranks[token['id']] = rank
            
            # Filter current tokens based on this criteria ranking
            filtered_tokens = []
            for token in current_tokens:
                if isinstance(token, dict) and 'id' in token:
                    token_id = token['id']
                    if token_id in criteria_ranks:
                        token['_criteria_ranks'] = token.get('_criteria_ranks', {})
                        token['_criteria_ranks'][criteria.value] = criteria_ranks[token_id]
                        filtered_tokens.append(token)
            
            # Sort by this criteria and keep top tokens
            filtered_tokens.sort(key=lambda x: x['_criteria_ranks'][criteria.value])
            current_tokens = filtered_tokens[:tokens_per_step]
            
            print(f"  Filtered to {len(current_tokens)} tokens")
        
        return current_tokens

    def get_high_value_tokens(
        self,
        chain: Chain,
        primary_criteria: SortCriteria = SortCriteria.VOLUME,
        min_volume: float = 500000,
        min_market_cap: float = 1000000,
        min_liquidity: float = 100000,
        time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS
    ) -> List[Dict[str, Any]]:
        """
        Get high-value tokens meeting minimum thresholds
        
        Args:
            chain: Blockchain to query
            primary_criteria: Main sorting criteria
            min_volume: Minimum trading volume (default: $500k)
            min_market_cap: Minimum market cap (default: $1M)
            min_liquidity: Minimum liquidity (default: $100k)
            time_period: Time period for ranking
            
        Returns:
            List of tokens meeting all minimum thresholds
        """
        criteria_filters = {}
        
        if min_volume > 0:
            criteria_filters[SortCriteria.VOLUME] = min_volume
        if min_market_cap > 0:
            criteria_filters[SortCriteria.MARKETCAP] = min_market_cap
        if min_liquidity > 0:
            criteria_filters[SortCriteria.LIQUIDITY] = min_liquidity
        
        if not criteria_filters:
            raise ValueError("At least one minimum threshold must be set")
        
        return self.get_filtered_rankings(
            chain=chain,
            primary_criteria=primary_criteria,
            criteria_filters=criteria_filters,
            time_period=time_period
        )


# Helper function to safely parse API responses
def parse_token_data(response, response_name="Response"):
    """
    Parse GMGN API response structure
    
    Expected GMGN API Response Structure:
    {
        "data": [
            {
                "id": int,
                "chain": str,
                "address": str,
                "symbol": str,
                "logo": str,
                "price": float,
                "price_change_percent": float,
                "price_change_percent1m": float,
                "price_change_percent5m": float,
                "price_change_percent1h": float,
                "swaps": int,
                "volume": float,
                "liquidity": float,
                "market_cap": float,
                "smart_buy_24h": int,
                "smart_sell_24h": int,
                "holder_count": int,
                "total_supply": int,
                "buy_tax": str,
                "sell_tax": str,
                "is_honeypot": int,
                "is_open_source": int,
                "renounced": int,
                "buys": int,
                "sells": int,
                "bluechip_owner_percentage": float,
                "sniper_count": int,
                "lockInfo": object
            }
        ]
    }
    """
    print(f"DEBUG - {response_name} type: {type(response)}")
    
    if not isinstance(response, dict):
        print(f"DEBUG - Response is not a dictionary, got: {type(response)}")
        return None
    
    print(f"DEBUG - Response keys: {list(response.keys())}")
    
    # Check for API error messages
    if 'code' in response:
        print(f"DEBUG - API code: {response['code']}")
    if 'msg' in response:
        print(f"DEBUG - API message: {response['msg']}")
    
    # GMGN API always returns data in the "data" key
    if 'data' not in response:
        print(f"DEBUG - No 'data' key found in response")
        print(f"DEBUG - Full response: {response}")
        return None
    
    data_content = response['data']
    
    if not isinstance(data_content, dict):
        print(f"DEBUG - 'data' is not a dict, got: {type(data_content)}")
        return None
    
    print(f"DEBUG - 'data' is a dict with keys: {list(data_content.keys())}")
    
    # GMGN API structure: data.rank contains a list of tokens
    if 'rank' not in data_content:
        print(f"DEBUG - No 'rank' key found in 'data'")
        return None
    print(f"DEBUG - 'rank' key found in 'data' {data_content['rank']}")
    rank_content = data_content['rank']
    
    if not isinstance(rank_content, list):
        print(f"DEBUG - 'data.rank' is not a list, got: {type(rank_content)}")
        return None
    
    print(f"DEBUG - 'data.rank' contains {len(rank_content)} tokens")
    
    # The rank content is already the token list
    token_data = rank_content
    
    # Validate token structure
    if token_data and len(token_data) > 0 and isinstance(token_data[0], dict):
        print(f"DEBUG - Successfully found {len(token_data)} tokens in 'data.rank' list")
    else:
        print(f"DEBUG - Invalid token structure in 'data.rank' list")
        print(f"DEBUG - Token data: {token_data}")
        if token_data == 0:
            print(f"DEBUG - Token data is empty")
        return None
    
    # Show first token structure for debugging
    if token_data and len(token_data) > 0 and isinstance(token_data[0], dict):
        first_token = token_data[0]
        print(f"DEBUG - First token keys: {list(first_token.keys())}")
        print(f"DEBUG - Sample token: symbol={first_token.get('symbol', 'N/A')}, price={first_token.get('price', 'N/A')}")
    
    return token_data


def format_token_info(token, index, info_type="general"):
    """
    Format token information for display based on GMGN API structure
    """
    if not isinstance(token, dict):
        return f"  {index}. {token}"
    
    # Basic info
    symbol = token.get('symbol', 'Unknown')
    price = token.get('price', 'N/A')
    
    # Format based on info type
    if info_type == "volume":
        volume = token.get('volume', 'N/A')
        if isinstance(volume, (int, float)):
            volume_str = f"${volume:,.2f}" if volume < 1000000 else f"${volume/1000000:.2f}M"
        else:
            volume_str = str(volume)
        return f"  {index}. {symbol} - Volume: {volume_str} | Price: ${price}"
        
    elif info_type == "gainers":
        change_1h = token.get('price_change_percent1h', 'N/A')
        change_24h = token.get('price_change_percent', 'N/A')
        return f"  {index}. {symbol} - 1h: {change_1h}% | 24h: {change_24h}% | Price: ${price}"
        
    elif info_type == "marketcap":
        market_cap = token.get('market_cap', 'N/A')
        if isinstance(market_cap, (int, float)):
            mcap_str = f"${market_cap:,.0f}" if market_cap < 1000000 else f"${market_cap/1000000:.2f}M"
        else:
            mcap_str = str(market_cap)
        return f"  {index}. {symbol} - MC: {mcap_str} | Price: ${price}"
        
    elif info_type == "swaps":
        swaps = token.get('swaps', 'N/A')
        volume = token.get('volume', 'N/A')
        return f"  {index}. {symbol} - Swaps: {swaps} | Volume: ${volume} | Price: ${price}"
        
    else:
        # General info
        volume = token.get('volume', 'N/A')
        change_24h = token.get('price_change_percent', 'N/A')
        return f"  {index}. {symbol} - Price: ${price} | 24h: {change_24h}% | Volume: ${volume}"


# Example usage functions
def example_usage():
    """
    Example usage of the GMGN wrapper with Cloudflare bypass
    """
    # Initialize with verbose=True to see retry attempts
    gmgn = GMGNWrapper(verbose=True)
    
    print("=== GMGN.ai API Wrapper Examples ===\n")
    
    try:
        # Example 1: Get top volume tokens on Ethereum in the last 24 hours
        print("1. Top Ethereum tokens by 24h volume:")
        eth_volume = gmgn.get_ethereum_rankings(
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            criteria=SortCriteria.VOLUME
        )
        
        token_data = parse_token_data(eth_volume, "Ethereum Volume")
        
        if token_data and isinstance(token_data, list) and len(token_data) > 0:
            print(f"Found {len(token_data)} tokens")
            # Show first few tokens
            display_count = min(3, len(token_data))
            for i in range(display_count):
                print(format_token_info(token_data[i], i+1, "volume"))
        else:
            print("No token data found or unexpected format")
            print(f"Raw response (first 500 chars): {str(eth_volume)[:500]}...")
        
        print("\n" + "="*50 + "\n")
        
        # Example 2: Get top gainers on Solana in the last hour
        print("2. Top Solana gainers in the last hour:")
        sol_gainers = gmgn.get_top_gainers(Chain.SOLANA, TimePeriod.ONE_HOUR)
        
        token_data = parse_token_data(sol_gainers, "Solana Gainers")
        
        if token_data and isinstance(token_data, list) and len(token_data) > 0:
            print(f"Found {len(token_data)} tokens")
            # Show first few tokens
            display_count = min(3, len(token_data))
            for i in range(display_count):
                print(format_token_info(token_data[i], i+1, "gainers"))
        else:
            print("No token data found")
            print(f"Raw response (first 500 chars): {str(sol_gainers)[:500]}...")
        
        print("\n" + "="*50 + "\n")
        
        # Example 3: Get tokens by market cap on Base
        print("3. Base tokens by market cap:")
        base_mcap = gmgn.get_token_rankings(
            chain=Chain.BASE,
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            criteria=SortCriteria.MARKETCAP,
            direction=SortDirection.DESCENDING
        )
        
        token_data = parse_token_data(base_mcap, "Base Market Cap")
        
        if token_data and isinstance(token_data, list) and len(token_data) > 0:
            print(f"Found {len(token_data)} tokens")
            # Show first few tokens
            display_count = min(3, len(token_data))
            for i in range(display_count):
                print(format_token_info(token_data[i], i+1, "marketcap"))
        else:
            print("No token data found")
            print(f"Raw response (first 500 chars): {str(base_mcap)[:500]}...")
        
        print("\n" + "="*50 + "\n")
        
        # Example 4: Test different filters
        print("4. Solana tokens with custom filters:")
        sol_custom = gmgn.get_token_rankings(
            chain=Chain.SOLANA,
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            criteria=SortCriteria.SWAPS,
            direction=SortDirection.DESCENDING,
            include_not_honeypot=True,
            include_verified=False,  # Include unverified tokens
            include_renounced=True
        )
        
        token_data = parse_token_data(sol_custom, "Solana Custom Filters")
        
        if token_data and isinstance(token_data, list) and len(token_data) > 0:
            print(f"Found {len(token_data)} tokens (including unverified)")
            # Show first few tokens
            display_count = min(3, len(token_data))
            for i in range(display_count):
                print(format_token_info(token_data[i], i+1, "swaps"))
        else:
            print("No token data found")
            print(f"Raw response (first 500 chars): {str(sol_custom)[:500]}...")
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"Error in examples: {e}")
        print("This wrapper automatically retries with session refresh, so this error indicates a persistent issue.")


def test_all_chains():
    """
    Test all supported chains to verify the wrapper works
    """
    gmgn = GMGNWrapper(verbose=False)  # Silent for testing
    
    chains_to_test = [Chain.ETHEREUM, Chain.SOLANA, Chain.BASE, Chain.BINANCE_SMART_CHAIN, Chain.TRON]
    
    print("Testing all supported chains...")
    for chain in chains_to_test:
        try:
            print(f"Testing {chain.value}... ", end="")
            data = gmgn.get_token_rankings(
                chain=chain,
                time_period=TimePeriod.TWENTY_FOUR_HOURS,
                criteria=SortCriteria.VOLUME,
                direction=SortDirection.DESCENDING
            )
            token_data = parse_token_data(data, f"{chain.value} test")
            if token_data and isinstance(token_data, list):
                print(f"✓ Success ({len(token_data)} tokens)")
            else:
                print(f"✓ Success (unexpected format)")
        except Exception as e:
            print(f"✗ Failed: {str(e)[:100]}...")
    
    print("Chain testing completed!")


def multi_criteria_examples():
    """
    Examples of using multiple sorting criteria
    """
    gmgn = GMGNWrapper(verbose=False)
    
    print("=== Multiple Criteria Ranking Examples ===\n")
    
    # Example 1: Filtered ranking by monetary values
    print("1. Filtered Ranking (Min Volume $1M + Min Market Cap $5M):")
    try:
        filtered_results = gmgn.get_filtered_rankings(
            chain=Chain.SOLANA,
            primary_criteria=SortCriteria.VOLUME,  # Sort by volume
            criteria_filters={
                SortCriteria.VOLUME: 1000000,      # Minimum $1M volume
                SortCriteria.MARKETCAP: 5000000    # Minimum $5M market cap
            },
            time_period=TimePeriod.TWENTY_FOUR_HOURS
        )
        
        print(f"Found {len(filtered_results)} tokens meeting filter criteria")
        for i, token in enumerate(filtered_results[:5], 1):
            if isinstance(token, dict):
                symbol = token.get('symbol', 'Unknown')
                volume = token.get('volume', 'N/A')
                mcap = token.get('market_cap', 'N/A')
                price = token.get('price', 'N/A')
                volume_str = f"${volume:,}" if isinstance(volume, (int, float)) else str(volume)
                mcap_str = f"${mcap:,}" if isinstance(mcap, (int, float)) else str(mcap)
                print(f"  {i}. {symbol} - Volume: {volume_str} | MC: {mcap_str} | Price: ${price}")
        
        print("\n" + "="*50 + "\n")
        
    except Exception as e:
        print(f"Filtered ranking failed: {e}")
    
    # Example 2: Sequential filtering approach
    print("2. Sequential Filtering (Volume → Market Cap → Price Change):")
    try:
        filtered_results = gmgn.get_sequential_filtered_rankings(
            chain=Chain.SOLANA,
            criteria_sequence=[
                SortCriteria.VOLUME,        # Start with high volume
                SortCriteria.MARKETCAP,     # Filter by market cap
                SortCriteria.CHANGE_1H      # Final filter by price change
            ],
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            tokens_per_step=30
        )
        
        print(f"Found {len(filtered_results)} tokens passing all filters")
        for i, token in enumerate(filtered_results[:5], 1):
            if isinstance(token, dict):
                symbol = token.get('symbol', 'Unknown')
                ranks = token.get('_criteria_ranks', {})
                volume = token.get('volume', 'N/A')
                mcap = token.get('market_cap', 'N/A')
                change = token.get('price_change_percent1h', 'N/A')
                print(f"  {i}. {symbol} - Vol: ${volume} | MC: ${mcap} | 1h: {change}%")
                if ranks:
                    print(f"      Ranks: {ranks}")
        
    except Exception as e:
        print(f"Sequential filtering failed: {e}")
    
    # Example 3: High-value token filtering (simpler preset)
    print("\n3. High-Value Token Filter (Min Vol $500k, MC $1M, Liq $100k):")
    try:
        high_value_results = gmgn.get_high_value_tokens(
            chain=Chain.SOLANA,
            primary_criteria=SortCriteria.MARKETCAP,  # Sort by market cap
            min_volume=500000,      # Min $500k volume
            min_market_cap=1000000, # Min $1M market cap
            min_liquidity=100000,   # Min $100k liquidity
            time_period=TimePeriod.TWENTY_FOUR_HOURS
        )
        
        print(f"Found {len(high_value_results)} high-value tokens")
        for i, token in enumerate(high_value_results[:5], 1):
            if isinstance(token, dict):
                symbol = token.get('symbol', 'Unknown')
                volume = token.get('volume', 'N/A')
                mcap = token.get('market_cap', 'N/A')
                liquidity = token.get('liquidity', 'N/A')
                price = token.get('price', 'N/A')
                volume_str = f"${volume:,}" if isinstance(volume, (int, float)) else str(volume)
                mcap_str = f"${mcap:,}" if isinstance(mcap, (int, float)) else str(mcap)
                liq_str = f"${liquidity:,}" if isinstance(liquidity, (int, float)) else str(liquidity)
                print(f"  {i}. {symbol} - Vol: {volume_str} | MC: {mcap_str} | Liq: {liq_str} | Price: ${price}")
        
    except Exception as e:
        print(f"High-value token filter failed: {e}")


def simple_test():
    """Simple test to check if basic API call works"""
    print("=== Simple API Test ===\n")
    gmgn = GMGNWrapper(verbose=True)
    
    try:
        print("1. Testing with NO filters...")
        response = gmgn.get_token_rankings(
            chain=Chain.SOLANA,
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            criteria=SortCriteria.VOLUME,
            direction=SortDirection.DESCENDING,
            include_not_honeypot=False,
            include_verified=False,
            include_renounced=False
        )
        
        print(f"Raw response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        if isinstance(response, dict) and 'data' in response:
            print(f"Data keys: {list(response['data'].keys()) if isinstance(response['data'], dict) else 'Data not a dict'}")
            if 'rank' in response['data']:
                print(f"Rank length: {len(response['data']['rank'])}")
        
        print("\n2. Testing with ONLY not_honeypot filter...")
        response2 = gmgn.get_token_rankings(
            chain=Chain.SOLANA,
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            criteria=SortCriteria.VOLUME,
            direction=SortDirection.DESCENDING,
            include_not_honeypot=True,
            include_verified=True,
            include_renounced=False
        )
        
        if isinstance(response2, dict) and 'data' in response2:
            if 'rank' in response2['data']:
                print(f"Rank length with not_honeypot only: {len(response2['data']['rank'])}")
        
    except Exception as e:
        print(f"Simple test failed: {e}")


if __name__ == "__main__":
    print("Running GMGN.ai wrapper examples...\n")
    simple_test()
    print("\n" + "="*70 + "\n")
    #example_usage()
    print("\n" + "="*70 + "\n")
    multi_criteria_examples()
    print("\n" + "="*70 + "\n")
    #test_all_chains()
