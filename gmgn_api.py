"""
GMGN.ai API Wrapper - Refactored for Reusability
==============================================

A modular, extensible wrapper for the GMGN.ai API with clean separation of concerns.

Key improvements:
- Separated concerns into focused classes
- Configuration management system
- Structured data models
- Pluggable filtering and formatting
- Better error handling and logging
- Factory patterns for query creation
- Type safety and validation
- Integrated rugcheck functionality for token safety verification

Features:
- Token data fetching and parsing
- Advanced filtering (volume, market cap, liquidity, price changes)
- Multiple formatting options
- Rugcheck integration for rug pull risk assessment
- Chainlink support (Solana, Ethereum, BSC, Base)
- Cloudflare bypass capabilities
"""

import json
import random
import logging
from typing import Optional, List, Dict, Any, Union, Protocol, Callable
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import tls_client
from fake_useragent import UserAgent
from rugcheck import rugcheck


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

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
    OPEN_TIMESTAMP = "open_timestamp"
    LIQUIDITY = "liquidity"
    MARKETCAP = "marketcap"
    BLUECHIP_OWNER_PERCENTAGE = "bluechip_owner_percentage"
    HOLDER_COUNT = "holder_count"
    SMARTMONEY = "smartmoney"
    SWAPS = "swaps"
    VOLUME = "volume"
    PRICE = "price"
    CHANGE_1M = "change1m"
    CHANGE_5M = "change5m"
    CHANGE_1H = "change1h"


class SortDirection(Enum):
    """Supported sort directions"""
    ASCENDING = "asc"
    DESCENDING = "desc"


# ============================================================================
# EXCEPTIONS
# ============================================================================

class GMGNError(Exception):
    """Base exception for GMGN API errors"""
    pass


class GMGNAPIError(GMGNError):
    """API request failed"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class GMGNParsingError(GMGNError):
    """Failed to parse API response"""
    pass


class GMGNConfigError(GMGNError):
    """Configuration error"""
    pass


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Token:
    """Structured token data model"""
    id: int
    chain: str
    address: str
    symbol: str
    price: float
    volume: float = 0
    liquidity: float = 0
    market_cap: float = 0
    holder_count: int = 0
    swaps: int = 0
    price_change_percent: float = 0
    price_change_percent1m: float = 0
    price_change_percent5m: float = 0
    price_change_percent1h: float = 0
    smart_buy_24h: int = 0
    smart_sell_24h: int = 0
    is_honeypot: int = 0
    is_open_source: int = 0
    renounced: int = 0
    bluechip_owner_percentage: float = 0
    logo: Optional[str] = None
    buy_tax: Optional[str] = None
    sell_tax: Optional[str] = None
    total_supply: Optional[int] = None
    buys: Optional[int] = None
    sells: Optional[int] = None
    sniper_count: Optional[int] = None
    lock_info: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Token':
        """Create Token from API response data"""
        return cls(
            id=data.get('id', 0),
            chain=data.get('chain', ''),
            address=data.get('address', ''),
            symbol=data.get('symbol', ''),
            price=float(data.get('price', 0)),
            volume=float(data.get('volume', 0)),
            liquidity=float(data.get('liquidity', 0)),
            market_cap=float(data.get('market_cap', 0)),
            holder_count=int(data.get('holder_count', 0)),
            swaps=int(data.get('swaps', 0)),
            price_change_percent=float(data.get('price_change_percent', 0)),
            price_change_percent1m=float(data.get('price_change_percent1m', 0)),
            price_change_percent5m=float(data.get('price_change_percent5m', 0)),
            price_change_percent1h=float(data.get('price_change_percent1h', 0)),
            smart_buy_24h=int(data.get('smart_buy_24h', 0)),
            smart_sell_24h=int(data.get('smart_sell_24h', 0)),
            is_honeypot=int(data.get('is_honeypot', 0)),
            is_open_source=int(data.get('is_open_source', 0)),
            renounced=int(data.get('renounced', 0)),
            bluechip_owner_percentage=float(data.get('bluechip_owner_percentage', 0)),
            logo=data.get('logo'),
            buy_tax=data.get('buy_tax'),
            sell_tax=data.get('sell_tax'),
            total_supply=data.get('total_supply'),
            buys=data.get('buys'),
            sells=data.get('sells'),
            sniper_count=data.get('sniper_count'),
            lock_info=data.get('lockInfo')
        )


@dataclass
class QueryParameters:
    """Parameters for GMGN API queries"""
    chain: Chain
    time_period: TimePeriod
    criteria: SortCriteria
    direction: SortDirection = SortDirection.DESCENDING
    include_not_honeypot: bool = True
    include_verified: bool = False
    include_renounced: bool = False
    
    def to_url_params(self) -> List[tuple]:
        """Convert to URL parameters"""
        params = [
            ('orderby', self.criteria.value),
            ('direction', self.direction.value)
        ]
        
        if self.include_not_honeypot:
            params.append(('filters[]', 'not_honeypot'))
        if self.include_verified:
            params.append(('filters[]', 'verified'))
        if self.include_renounced:
            params.append(('filters[]', 'renounced'))
            
        return params


@dataclass
class FilterCriteria:
    """Criteria for filtering tokens"""
    min_volume: Optional[float] = None
    max_volume: Optional[float] = None
    min_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    min_liquidity: Optional[float] = None
    max_liquidity: Optional[float] = None
    min_holder_count: Optional[int] = None
    min_price_change: Optional[float] = None
    max_price_change: Optional[float] = None
    min_age_days: Optional[float] = None  # Minimum token age in days
    exclude_honeypots: bool = True
    
    def matches(self, token: Token) -> bool:
        """Check if token matches filter criteria"""
        if self.exclude_honeypots and token.is_honeypot:
            return False
        if self.min_volume and token.volume < self.min_volume:
            return False
        if self.max_volume and token.volume > self.max_volume:
            return False
        if self.min_market_cap and token.market_cap < self.min_market_cap:
            return False
        if self.max_market_cap and token.market_cap > self.max_market_cap:
            return False
        if self.min_liquidity and token.liquidity < self.min_liquidity:
            return False
        if self.max_liquidity and token.liquidity > self.max_liquidity:
            return False
        if self.min_holder_count and token.holder_count < self.min_holder_count:
            return False
        if self.min_price_change and token.price_change_percent < self.min_price_change:
            return False
        if self.max_price_change and token.price_change_percent > self.max_price_change:
            return False
        # Note: min_age_days filtering would require token creation timestamp
        # This would need to be implemented when timestamp data is available from API
        if self.min_age_days:
            # Placeholder - would need token.created_timestamp or similar field
            pass
        return True


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class GMGNConfig:
    """Configuration for GMGN API client"""
    base_url: str = "https://gmgn.ai/defi/quotation/v1/rank"
    timeout: int = 60
    max_retries: int = 3
    verbose: bool = False
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ])
    
    @classmethod
    def create_default(cls) -> 'GMGNConfig':
        """Create default configuration"""
        return cls()
    
    @classmethod
    def create_verbose(cls) -> 'GMGNConfig':
        """Create configuration with verbose logging"""
        return cls(verbose=True)


# ============================================================================
# PROTOCOLS AND INTERFACES
# ============================================================================

class TokenFormatter(Protocol):
    """Protocol for token formatters"""
    def format(self, token: Token, index: int) -> str:
        """Format token for display"""
        ...


class TokenFilter(Protocol):
    """Protocol for token filters"""
    def filter(self, tokens: List[Token]) -> List[Token]:
        """Filter tokens based on criteria"""
        ...


# ============================================================================
# HTTP CLIENT
# ============================================================================

class GMGNClient:
    """HTTP client with Cloudflare bypass capabilities"""
    
    def __init__(self, config: GMGNConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.session = None
        self.headers = None
        self._initialize_session()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(f"{__name__}.GMGNClient")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        return logger
    
    def _initialize_session(self):
        """Initialize TLS session with random parameters"""
        # Select random browser identifier
        browser_identifiers = [
            identifier for identifier in tls_client.settings.ClientIdentifiers.__args__
            if identifier.startswith(('chrome', 'safari', 'firefox', 'opera'))
        ]
        
        self.identifier = random.choice(browser_identifiers)
        self.logger.debug(f"Using browser identifier: {self.identifier}")
        
        # Create session
        self.session = tls_client.Session(
            random_tls_extension_order=True,
            client_identifier=self.identifier
        )
        self.session.timeout_seconds = self.config.timeout
        
        # Generate user agent
        try:
            self.user_agent = UserAgent().random
        except Exception:
            self.user_agent = random.choice(self.config.user_agents)
        
        # Setup headers
        self.headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://gmgn.ai/?chain=sol',
            'user-agent': self.user_agent
        }
        
        self.logger.debug(f"Session initialized with User-Agent: {self.user_agent}")
    
    def refresh_session(self):
        """Refresh session with new random parameters"""
        self.logger.info("Refreshing session...")
        self._initialize_session()
    
    def make_request(self, url: str, params: List[tuple]) -> Dict[str, Any]:
        """
        Make API request with retry logic
        
        Args:
            url: Request URL
            params: URL parameters as list of tuples
            
        Returns:
            API response as dictionary
            
        Raises:
            GMGNAPIError: If request fails after all retries
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.debug(f"Attempt {attempt + 1}: {url} with params {params}")
                
                response = self.session.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [403, 429, 503]:
                    raise GMGNAPIError(response.status_code, "Cloudflare block detected")
                else:
                    raise GMGNAPIError(response.status_code, response.text)
                    
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    self.refresh_session()
                else:
                    self.logger.error(f"All {self.config.max_retries} attempts failed")
        
        if isinstance(last_exception, GMGNAPIError):
            raise last_exception
        else:
            raise GMGNAPIError(500, f"Request failed: {str(last_exception)}")


# ============================================================================
# DATA PARSING
# ============================================================================

class TokenDataParser:
    """Parser for GMGN API responses"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(f"{__name__}.TokenDataParser")
    
    def parse_response(self, response: Dict[str, Any]) -> List[Token]:
        """
        Parse GMGN API response into Token objects
        
        Args:
            response: Raw API response
            
        Returns:
            List of Token objects
            
        Raises:
            GMGNParsingError: If response structure is invalid
        """
        try:
            if not isinstance(response, dict):
                raise GMGNParsingError(f"Expected dict, got {type(response)}")
            
            if 'data' not in response:
                raise GMGNParsingError("No 'data' key in response")
            
            data = response['data']
            if not isinstance(data, dict) or 'rank' not in data:
                raise GMGNParsingError("Invalid data structure")
            
            rank_data = data['rank']
            if not isinstance(rank_data, list):
                raise GMGNParsingError("Rank data is not a list")
            
            tokens = []
            for item in rank_data:
                if isinstance(item, dict):
                    try:
                        token = Token.from_dict(item)
                        tokens.append(token)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse token: {e}")
                        continue
            
            self.logger.info(f"Successfully parsed {len(tokens)} tokens")
            return tokens
            
        except Exception as e:
            if isinstance(e, GMGNParsingError):
                raise
            raise GMGNParsingError(f"Parsing failed: {str(e)}")


# ============================================================================
# FILTERING SYSTEM
# ============================================================================

class BaseTokenFilter:
    """Base class for token filters"""
    
    def filter(self, tokens: List[Token]) -> List[Token]:
        """Filter tokens - override in subclasses"""
        return tokens


class CriteriaFilter(BaseTokenFilter):
    """Filter tokens based on FilterCriteria"""
    
    def __init__(self, criteria: FilterCriteria):
        self.criteria = criteria
    
    def filter(self, tokens: List[Token]) -> List[Token]:
        return [token for token in tokens if self.criteria.matches(token)]


class TopNFilter(BaseTokenFilter):
    """Keep only top N tokens"""
    
    def __init__(self, n: int):
        self.n = n
    
    def filter(self, tokens: List[Token]) -> List[Token]:
        return tokens[:self.n]


class CompositeFilter(BaseTokenFilter):
    """Combine multiple filters"""
    
    def __init__(self, filters: List[BaseTokenFilter]):
        self.filters = filters
    
    def filter(self, tokens: List[Token]) -> List[Token]:
        result = tokens
        for filter_instance in self.filters:
            result = filter_instance.filter(result)
        return result


# ============================================================================
# FORMATTING SYSTEM
# ============================================================================

class GeneralFormatter:
    """General purpose token formatter"""
    
    def format(self, token: Token, index: int) -> str:
        return f"  {index}. {token.symbol} - Price: ${token.price:.6f} | 24h: {token.price_change_percent:.2f}% | Volume: ${token.volume:,.0f}"


class VolumeFormatter:
    """Volume-focused formatter"""
    
    def format(self, token: Token, index: int) -> str:
        volume_str = f"${token.volume/1000000:.2f}M" if token.volume >= 1000000 else f"${token.volume:,.0f}"
        return f"  {index}. {token.symbol} - Volume: {volume_str} | Price: ${token.price:.6f}"


class MarketCapFormatter:
    """Market cap focused formatter"""
    
    def format(self, token: Token, index: int) -> str:
        mcap_str = f"${token.market_cap/1000000:.2f}M" if token.market_cap >= 1000000 else f"${token.market_cap:,.0f}"
        return f"  {index}. {token.symbol} - MC: {mcap_str} | Price: ${token.price:.6f}"


class GainersFormatter:
    """Price change focused formatter"""
    
    def format(self, token: Token, index: int) -> str:
        return f"  {index}. {token.symbol} - 1h: {token.price_change_percent1h:.2f}% | 24h: {token.price_change_percent:.2f}% | Price: ${token.price:.6f}"


class SmallCapFormatter:
    """Small cap focused formatter showing MC, liquidity, and volume"""
    
    def format(self, token: Token, index: int) -> str:
        def format_value(value: float) -> str:
            if value >= 1000000:
                return f"${value/1000000:.2f}M"
            elif value >= 1000:
                return f"${value/1000:.0f}K"
            else:
                return f"${value:.0f}"
        
        mc_str = format_value(token.market_cap)
        liq_str = format_value(token.liquidity)
        vol_str = format_value(token.volume)
        
        return f"  {index}. {token.symbol} - MC: {mc_str} | Liq: {liq_str} | Vol: {vol_str} | Price: ${token.price:.6f}"


class RugcheckFormatter:
    """Formatter that includes rugcheck risk information"""
    
    def format(self, token: Token, index: int) -> str:
        """Format token without rugcheck info"""
        return f"  {index}. {token.symbol} - Price: ${token.price:.6f} | Vol: ${token.volume:,.0f}"
    
    def format_with_rugcheck(self, token: Token, rugcheck_result: Dict[str, Any], index: int) -> str:
        """Format token with rugcheck information"""
        if "error" in rugcheck_result:
            risk_display = "❌ Error"
        else:
            risk_score = rugcheck_result.get('risk_score')
            if risk_score is not None:
                if risk_score <= 0.2:
                    risk_display = f"✅ Low Risk ({risk_score:.2f})"
                elif risk_score <= 0.5:
                    risk_display = f"⚠️ Medium Risk ({risk_score:.2f})"
                else:
                    risk_display = f"🚨 High Risk ({risk_score:.2f})"
            else:
                # Try to show rugcheck score instead
                rugcheck_score = rugcheck_result.get('rugcheck_score', 0)
                if rugcheck_score > 0:
                    risk_display = f"📊 Score: {rugcheck_score}"
                else:
                    risk_display = "❓ No Score"
        
        return f"  {index}. {token.symbol} - {risk_display} | Price: ${token.price:.6f} | Vol: ${token.volume:,.0f}"


# ============================================================================
# MAIN API CLASS
# ============================================================================

class GMGNTokenAPI:
    """Main GMGN Token API wrapper with modular design"""
    
    def __init__(self, config: Optional[GMGNConfig] = None):
        """Initialize with optional configuration"""
        self.config = config or GMGNConfig.create_default()
        self.client = GMGNClient(self.config)
        self.parser = TokenDataParser()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(f"{__name__}.GMGNTokenAPI")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        return logger
    
    def get_tokens(self, params: QueryParameters) -> List[Token]:
        """
        Get tokens based on query parameters
        
        Args:
            params: Query parameters
            
        Returns:
            List of Token objects
        """
        url = f"{self.config.base_url}/{params.chain.value}/swaps/{params.time_period.value}"
        url_params = params.to_url_params()
        
        self.logger.info(f"Fetching tokens for {params.chain.value} with criteria {params.criteria.value}")
        
        response = self.client.make_request(url, url_params)
        tokens = self.parser.parse_response(response)
        
        return tokens
    
    def get_tokens_with_filter(self, params: QueryParameters, filter_instance: BaseTokenFilter) -> List[Token]:
        """Get tokens and apply filter"""
        tokens = self.get_tokens(params)
        return filter_instance.filter(tokens)
    
    def get_formatted_tokens(self, params: QueryParameters, formatter: TokenFormatter, filter_instance: Optional[BaseTokenFilter] = None) -> List[str]:
        """Get tokens with formatting applied"""
        tokens = self.get_tokens(params)
        
        if filter_instance:
            tokens = filter_instance.filter(tokens)
        
        return [formatter.format(token, i+1) for i, token in enumerate(tokens)]
    
    # Convenience methods
    def get_top_volume_tokens(self, chain: Chain, time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS, limit: int = 10) -> List[Token]:
        """Get top volume tokens"""
        params = QueryParameters(chain=chain, time_period=time_period, criteria=SortCriteria.VOLUME)
        filter_instance = TopNFilter(limit)
        return self.get_tokens_with_filter(params, filter_instance)
    
    def get_top_gainers(self, chain: Chain, time_period: TimePeriod = TimePeriod.ONE_HOUR) -> List[Token]:
        """Get top gaining tokens"""
        if time_period == TimePeriod.ONE_MINUTE:
            criteria = SortCriteria.CHANGE_1M
        elif time_period == TimePeriod.FIVE_MINUTES:
            criteria = SortCriteria.CHANGE_5M
        elif time_period == TimePeriod.ONE_HOUR:
            criteria = SortCriteria.CHANGE_1H
        else:
            criteria = SortCriteria.CHANGE_1H
        
        params = QueryParameters(chain=chain, time_period=time_period, criteria=criteria)
        filter_instance = TopNFilter(limit)
        return self.get_tokens_with_filter(params, filter_instance)
    
    def get_high_value_tokens(self, chain: Chain, min_volume: float = 500000, min_market_cap: float = 1000000, limit: int = 10) -> List[Token]:
        """Get high-value tokens meeting minimum criteria"""
        params = QueryParameters(chain=chain, time_period=TimePeriod.TWENTY_FOUR_HOURS, criteria=SortCriteria.VOLUME)
        criteria_filter = CriteriaFilter(FilterCriteria(min_volume=min_volume, min_market_cap=min_market_cap))
        top_filter = TopNFilter(limit)
        composite_filter = CompositeFilter([criteria_filter, top_filter])
        
        return self.get_tokens_with_filter(params, composite_filter)
    
    def get_safe_tokens(self, chain: Chain, criteria: SortCriteria = SortCriteria.VOLUME, limit: int = 10) -> List[Token]:
        """Get tokens with all safety filters applied"""
        params = QueryParameters(
            chain=chain,
            criteria=criteria,
            include_not_honeypot=True,
            include_verified=True,
            include_renounced=True
        )
        filter_instance = TopNFilter(limit)
        return self.get_tokens_with_filter(params, filter_instance)
    
    def get_small_cap_tokens(self, chain: Chain, criteria: SortCriteria = SortCriteria.VOLUME, limit: int = 10) -> List[Token]:
        """
        Get small cap tokens with specific criteria:
        - Market cap below 200K
        - Liquidity under 150K
        - Trading volume less than 300K
        - Minimum 1-day-old (when timestamp data is available)
        """
        params = QueryParameters(chain=chain, time_period=TimePeriod.TWENTY_FOUR_HOURS, criteria=criteria)
        
        small_cap_filter = CriteriaFilter(FilterCriteria(
            max_market_cap=200000,      # Below 200K
            max_liquidity=150000,       # Under 150K
            max_volume=300000,          # Less than 300K
            min_age_days=1,             # Minimum 1-day-old (placeholder)
            exclude_honeypots=True
        ))
        
        top_filter = TopNFilter(limit)
        composite_filter = CompositeFilter([small_cap_filter, top_filter])
        
        return self.get_tokens_with_filter(params, composite_filter)
    
    def get_filtered_tokens(self, chain: Chain, filter_criteria: FilterCriteria, criteria: SortCriteria = SortCriteria.VOLUME, limit: int = 10) -> List[Token]:
        """Get tokens with custom filter criteria"""
        params = QueryParameters(chain=chain, time_period=TimePeriod.TWENTY_FOUR_HOURS, criteria=criteria)
        
        criteria_filter = CriteriaFilter(filter_criteria)
        top_filter = TopNFilter(limit)
        composite_filter = CompositeFilter([criteria_filter, top_filter])
        
        return self.get_tokens_with_filter(params, composite_filter)

    # Rugcheck methods
    def check_token_rug_risk(self, token_address: str, chain: Chain = Chain.SOLANA) -> Dict[str, Any]:
        """
        Check a single token for rug risk using rugcheck
        
        Args:
            token_address: Token contract address
            chain: Blockchain chain (Note: rugcheck may only support Solana)
            
        Returns:
            Dictionary containing rugcheck results
        """
        try:
            # Note: rugcheck library appears to be Solana-focused only
            if chain != Chain.SOLANA:
                self.logger.warning(f"Rugcheck may only support Solana tokens. Requested chain: {chain.value}")
            
            # Create rugcheck instance with token address
            rug_checker = rugcheck(token_address, get_price=True, get_votes=True)
            
            # Get the results as dictionary
            result = rug_checker.to_dict()
            
            # Extract normalized risk score from rugcheck data
            risk_score = self._extract_risk_score(result)
            result['risk_score'] = risk_score
            
            # Add some convenience fields for easier access
            result['is_rugged'] = result.get('rugged', False)
            result['rugcheck_score'] = result.get('score', 0)
            result['normalized_score'] = result.get('score_normalised', 0.5)
            
            self.logger.info(f"Rugcheck completed for {token_address}")
            return result
            
        except Exception as e:
            self.logger.error(f"Rugcheck failed for {token_address}: {str(e)}")
            return {"error": str(e), "risk_score": None}
    
    def _extract_risk_score(self, rugcheck_result: Dict[str, Any]) -> float:
        """
        Extract and normalize risk score from rugcheck result
        
        Args:
            rugcheck_result: Raw rugcheck result dictionary
            
        Returns:
            Risk score from 0.0 (safe) to 1.0 (high risk)
        """
        try:
            # Use rugcheck's normalized score if available (0-1 scale)
            if 'score_normalised' in rugcheck_result and rugcheck_result['score_normalised'] is not None:
                score = float(rugcheck_result['score_normalised'])
                # rugcheck score_normalised: higher = better, so invert for risk score
                return max(0.0, min(1.0, 1.0 - score))
            
            # Use raw score if available (typically 0-100 scale)
            elif 'score' in rugcheck_result and rugcheck_result['score'] is not None:
                score = float(rugcheck_result['score'])
                # Assume 0-100 scale, higher = better, so invert and normalize
                normalized = score / 100.0
                return max(0.0, min(1.0, 1.0 - normalized))
            
            # Check for explicit rugged flag
            elif rugcheck_result.get('rugged', False):
                return 1.0  # Maximum risk if flagged as rugged
            
            # Check risks array if available
            elif 'risks' in rugcheck_result and isinstance(rugcheck_result['risks'], list):
                risk_count = len(rugcheck_result['risks'])
                # Assume more risks = higher risk score (max 10 risks = 1.0 score)
                return min(1.0, risk_count / 10.0)
            
            else:
                # Default to medium risk if no score available
                return 0.5
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to extract risk score: {e}")
            return 0.5  # Default to medium risk on error
    
    def check_tokens_rug_risk(self, tokens: List[Token], chain: Chain = Chain.SOLANA) -> Dict[str, Dict[str, Any]]:
        """
        Check multiple tokens for rug risk
        
        Args:
            tokens: List of Token objects
            chain: Blockchain chain
            
        Returns:
            Dictionary mapping token addresses to rugcheck results
        """
        results = {}
        
        for token in tokens:
            self.logger.debug(f"Checking rugcheck for {token.symbol} ({token.address})")
            result = self.check_token_rug_risk(token.address, chain)
            results[token.address] = result
            
        return results
    
    def get_tokens_with_rugcheck(self, params: QueryParameters, check_rug: bool = True) -> List[tuple]:
        """
        Get tokens with rugcheck results
        
        Args:
            params: Query parameters
            check_rug: Whether to perform rugcheck (default: True)
            
        Returns:
            List of tuples (Token, rugcheck_result)
        """
        tokens = self.get_tokens(params)
        
        if not check_rug:
            return [(token, None) for token in tokens]
        
        results = []
        for token in tokens:
            rug_result = self.check_token_rug_risk(token.address, params.chain)
            results.append((token, rug_result))
            
        return results
    
    def filter_safe_tokens_by_rugcheck(self, tokens: List[Token], chain: Chain = Chain.SOLANA, 
                                     max_risk_score: float = 0.3) -> List[Token]:
        """
        Filter tokens based on rugcheck risk score
        
        Args:
            tokens: List of tokens to check
            chain: Blockchain chain
            max_risk_score: Maximum acceptable risk score (0.0 = safe, 1.0 = high risk)
            
        Returns:
            List of tokens that pass the rugcheck filter
        """
        safe_tokens = []
        
        for token in tokens:
            rug_result = self.check_token_rug_risk(token.address, chain)
            
            # Check if token passes rugcheck
            if "error" not in rug_result:
                risk_score = rug_result.get("risk_score")
                if risk_score is not None and risk_score <= max_risk_score:
                    safe_tokens.append(token)
                    self.logger.debug(f"Token {token.symbol} passed rugcheck (risk: {risk_score})")
                else:
                    self.logger.debug(f"Token {token.symbol} failed rugcheck (risk: {risk_score})")
            else:
                self.logger.warning(f"Could not check {token.symbol}: {rug_result.get('error')}")
        
        return safe_tokens
    
    def get_rugcheck_verified_tokens(self, chain: Chain, criteria: SortCriteria = SortCriteria.VOLUME, 
                                   limit: int = 10, max_risk_score: float = 0.3) -> List[Token]:
        """
        Get tokens that pass both GMGN filters and rugcheck verification
        
        Args:
            chain: Blockchain chain
            criteria: Sorting criteria
            limit: Maximum number of tokens to return
            max_risk_score: Maximum acceptable rugcheck risk score
            
        Returns:
            List of rugcheck-verified tokens
        """
        # Get initial token list
        params = QueryParameters(
            chain=chain,
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            criteria=criteria,
            include_not_honeypot=True
        )
        
        # Get more tokens initially since some will be filtered out by rugcheck
        initial_tokens = self.get_tokens(params)[:limit * 3]  
        
        # Filter by rugcheck
        safe_tokens = self.filter_safe_tokens_by_rugcheck(initial_tokens, chain, max_risk_score)
        
        # Return top N safe tokens
        return safe_tokens[:limit]


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_api(verbose: bool = False) -> GMGNTokenAPI:
    """Factory function to create API instance"""
    config = GMGNConfig.create_verbose() if verbose else GMGNConfig.create_default()
    return GMGNTokenAPI(config)


def create_volume_query(chain: Chain, time_period: TimePeriod = TimePeriod.TWENTY_FOUR_HOURS) -> QueryParameters:
    """Factory function for volume queries"""
    return QueryParameters(chain=chain, time_period=time_period, criteria=SortCriteria.VOLUME)


def create_gainers_query(chain: Chain, time_period: TimePeriod = TimePeriod.ONE_HOUR) -> QueryParameters:
    """Factory function for gainers queries"""
    if time_period == TimePeriod.ONE_MINUTE:
        criteria = SortCriteria.CHANGE_1M
    elif time_period == TimePeriod.FIVE_MINUTES:
        criteria = SortCriteria.CHANGE_5M
    else:
        criteria = SortCriteria.CHANGE_1H
    
    return QueryParameters(chain=chain, time_period=time_period, criteria=criteria)


def create_rugcheck_api(verbose: bool = False) -> GMGNTokenAPI:
    """Factory function to create API instance with rugcheck enabled"""
    config = GMGNConfig.create_verbose() if verbose else GMGNConfig.create_default()
    return GMGNTokenAPI(config)


def get_safe_tokens_with_rugcheck(chain: Chain, limit: int = 10, max_risk_score: float = 0.3, verbose: bool = False) -> List[Token]:
    """
    Convenience function to get safe tokens with rugcheck verification
    
    Args:
        chain: Blockchain chain
        limit: Maximum number of tokens to return
        max_risk_score: Maximum acceptable rugcheck risk score (0.0-1.0)
        verbose: Enable verbose logging
        
    Returns:
        List of rugcheck-verified safe tokens
    """
    api = create_rugcheck_api(verbose)
    return api.get_rugcheck_verified_tokens(chain, limit=limit, max_risk_score=max_risk_score)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def main():
    """Example usage of the refactored API"""
    print("=== GMGN Token API - Refactored Version ===\n")
    
    # Create API instance
    api = create_api(verbose=True)
    
    try:
        # Example 1: Get top volume tokens on Solana
        print("1. Top 5 Solana tokens by volume:")
        volume_tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=5)
        formatter = VolumeFormatter()
        
        for i, token in enumerate(volume_tokens, 1):
            print(formatter.format(token, i))
        
        print("\n" + "="*50 + "\n")
        
        # Example 2: Get top gainers with custom filter
        print("2. Top gainers with high volume (>$100k):")
        params = create_gainers_query(Chain.SOLANA, TimePeriod.ONE_HOUR)
        high_volume_filter = CriteriaFilter(FilterCriteria(min_volume=100000))
        top_filter = TopNFilter(3)
        composite_filter = CompositeFilter([high_volume_filter, top_filter])
        
        gainers = api.get_tokens_with_filter(params, composite_filter)
        formatter = GainersFormatter()
        
        for i, token in enumerate(gainers, 1):
            print(formatter.format(token, i))
        
        print("\n" + "="*50 + "\n")
        
        # Example 3: High-value tokens
        print("3. High-value tokens (Min Vol: $1M, Min MC: $5M):")
        high_value = api.get_high_value_tokens(Chain.SOLANA, min_volume=1000000, min_market_cap=5000000, limit=3)
        formatter = MarketCapFormatter()
        
        for i, token in enumerate(high_value, 1):
            print(formatter.format(token, i))
        
        print("\n" + "="*50 + "\n")
        
        # Example 4: Safe tokens
        print("4. Safe tokens (all filters applied):")
        safe_tokens = api.get_safe_tokens(Chain.SOLANA, limit=3)
        formatter = GeneralFormatter()
        
        for i, token in enumerate(safe_tokens, 1):
            print(formatter.format(token, i))
        
        print("\n" + "="*50 + "\n")

        # Example 5: Small cap tokens
        print("5. Small cap tokens (MC < $200K, Vol < $300K):")
        small_cap_tokens = api.get_small_cap_tokens(Chain.SOLANA, limit=3)
        formatter = SmallCapFormatter()

        for i, token in enumerate(small_cap_tokens, 1):
            print(formatter.format(token, i))

        print("\n" + "="*50 + "\n")

        # Example 6: Custom filtered tokens
        print("6. Custom filtered tokens (MC < $100K, Vol < $200K):")
        custom_filter_criteria = FilterCriteria(
            max_market_cap=100000,
            max_volume=200000,
            exclude_honeypots=True
        )
        custom_tokens = api.get_filtered_tokens(Chain.SOLANA, custom_filter_criteria, limit=3)
        formatter = SmallCapFormatter()

        for i, token in enumerate(custom_tokens, 1):
            print(formatter.format(token, i))

        print("\n" + "="*50 + "\n")

        # Example 7: Rugcheck verification
        print("7. Rugcheck verified tokens (risk score < 0.3):")
        try:
            rugcheck_tokens = api.get_rugcheck_verified_tokens(Chain.SOLANA, limit=3, max_risk_score=0.3)
            formatter = RugcheckFormatter()

            for i, token in enumerate(rugcheck_tokens, 1):
                print(formatter.format(token, i))
                
        except Exception as e:
            print(f"Rugcheck example failed: {e}")

        print("\n" + "="*50 + "\n")

        # Example 8: Individual token rugcheck
        print("8. Individual token rugcheck:")
        try:
            # Get a token to check
            volume_tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=1)
            if volume_tokens:
                token = volume_tokens[0]
                rugcheck_result = api.check_token_rug_risk(token.address, Chain.SOLANA)
                
                formatter = RugcheckFormatter()
                formatted_output = formatter.format_with_rugcheck(token, rugcheck_result, 1)
                print(formatted_output)
                
                # Show detailed rugcheck info
                if "error" not in rugcheck_result:
                    print(f"    Detailed info: {rugcheck_result}")
            else:
                print("No tokens available for rugcheck")
                
        except Exception as e:
            print(f"Individual rugcheck example failed: {e}")

        print("\nExamples completed successfully!")
        
        # Quick usage examples for rugcheck:
        print("\n" + "="*60)
        print("RUGCHECK USAGE EXAMPLES:")
        print("="*60)
        print("# Get safe tokens with rugcheck verification:")
        print("safe_tokens = api.get_rugcheck_verified_tokens(Chain.SOLANA, limit=5, max_risk_score=0.2)")
        print()
        print("# Check individual token:")
        print("result = api.check_token_rug_risk('TOKEN_ADDRESS', Chain.SOLANA)")
        print()
        print("# Factory function for quick access:")
        print("from gmgn_api import get_safe_tokens_with_rugcheck")
        print("tokens = get_safe_tokens_with_rugcheck(Chain.SOLANA, limit=10, max_risk_score=0.3)")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 