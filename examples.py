#!/usr/bin/env python3
"""
Example Usage of GMGN Token API (Refactored Version)
====================================================

This file demonstrates various ways to use the refactored GMGN Token API
with practical examples for different use cases including rugcheck integration.

Features demonstrated:
- Basic token fetching and filtering
- Advanced multi-criteria filtering
- Custom formatters and display options
- Cross-chain token comparison
- Rugcheck integration for token safety verification
- Factory functions for quick access

Run this file to see the API in action!
"""

from gmgn_api import (
    # Main API
    create_api, GMGNTokenAPI, GMGNConfig,
    
    # Enums
    Chain, TimePeriod, SortCriteria, SortDirection,
    
    # Data Models
    QueryParameters, FilterCriteria, Token,
    
    # Filters
    CriteriaFilter, TopNFilter, CompositeFilter,
    
    # Formatters
    GeneralFormatter, VolumeFormatter, MarketCapFormatter, GainersFormatter, SmallCapFormatter, RugcheckFormatter,
    
    # Factory Functions
    create_volume_query, create_gainers_query, create_rugcheck_api, get_safe_tokens_with_rugcheck,
    
    # Exceptions
    GMGNAPIError, GMGNParsingError
)


def example_1_basic_usage():
    """Example 1: Basic API usage - getting top volume tokens"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Usage - Top Volume Tokens")
    print("=" * 60)
    
    # Create API instance with verbose logging
    api = create_api(verbose=True)
    
    try:
        # Get top 5 Solana tokens by volume
        print("\n🔍 Getting top 5 Solana tokens by volume...")
        volume_tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=5)
        
        # Display results with volume formatter
        formatter = VolumeFormatter()
        print(f"\n📊 Found {len(volume_tokens)} tokens:")
        for i, token in enumerate(volume_tokens, 1):
            print(formatter.format(token, i))
            
    except GMGNAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


def example_2_custom_configuration():
    """Example 2: Using custom configuration"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: Custom Configuration")
    print("=" * 60)
    
    # Create custom configuration
    config = GMGNConfig(
        timeout=120,
        max_retries=5,
        verbose=False  # Silent mode
    )
    
    # Create API with custom config
    api = GMGNTokenAPI(config)
    
    try:
        print("\n🔧 Using custom configuration (120s timeout, 5 retries, silent mode)")
        
        # Get Ethereum tokens by market cap
        mcap_tokens = api.get_top_volume_tokens(Chain.ETHEREUM, limit=3)
        
        formatter = MarketCapFormatter()
        print(f"\n📈 Top 3 Ethereum tokens by volume:")
        for i, token in enumerate(mcap_tokens, 1):
            print(formatter.format(token, i))
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_gainers_and_formatters():
    """Example 3: Top gainers with different formatters"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: Top Gainers with Multiple Formatters")
    print("=" * 60)
    
    api = create_api()
    
    try:
        # Get top gainers in the last hour
        print("\n📈 Getting top gainers on Solana (last hour)...")
        gainers = api.get_top_gainers(Chain.SOLANA, TimePeriod.ONE_HOUR, limit=3)
        
        # Show with different formatters
        formatters = {
            "General": GeneralFormatter(),
            "Gainers": GainersFormatter(),
            "Volume": VolumeFormatter()
        }
        
        for name, formatter in formatters.items():
            print(f"\n🎨 {name} Format:")
            for i, token in enumerate(gainers, 1):
                print(formatter.format(token, i))
                
    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_advanced_filtering():
    """Example 4: Advanced filtering with composite filters"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 4: Advanced Filtering")
    print("=" * 60)
    
    api = create_api()
    
    try:
        # Create query parameters
        params = QueryParameters(
            chain=Chain.SOLANA,
            time_period=TimePeriod.TWENTY_FOUR_HOURS,
            criteria=SortCriteria.VOLUME,
            direction=SortDirection.DESCENDING
        )
        
        print("\n🔍 Searching for high-quality tokens with multiple criteria...")
        print("   - Minimum volume: $500,000")
        print("   - Minimum market cap: $1,000,000") 
        print("   - Minimum holder count: 50")
        print("   - Positive price change (last 1h)")
        print("   - Not honeypots")
        
        # Create composite filter
        quality_filter = CriteriaFilter(FilterCriteria(
            min_volume=500000,
            min_market_cap=1000000,
            min_holder_count=50,
            min_price_change=0,  # Positive change
            exclude_honeypots=True
        ))
        
        top_filter = TopNFilter(5)
        composite_filter = CompositeFilter([quality_filter, top_filter])
        
        # Apply filters
        quality_tokens = api.get_tokens_with_filter(params, composite_filter)
        
        print(f"\n✅ Found {len(quality_tokens)} high-quality tokens:")
        formatter = GeneralFormatter()
        for i, token in enumerate(quality_tokens, 1):
            print(formatter.format(token, i))
            print(f"    📊 Holders: {token.holder_count:,} | "
                  f"Honeypot: {'Yes' if token.is_honeypot else 'No'} | "
                  f"1h Change: {token.price_change_percent1h:.2f}%")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_5_high_value_tokens():
    """Example 5: Using built-in high-value token method"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 5: High-Value Tokens (Built-in Method)")
    print("=" * 60)
    
    api = create_api()
    
    try:
        print("\n💎 Finding high-value tokens on Base chain...")
        print("   - Minimum volume: $1,000,000")
        print("   - Minimum market cap: $5,000,000")
        
        high_value_tokens = api.get_high_value_tokens(
            Chain.BASE,
            min_volume=1000000,
            min_market_cap=5000000,
            limit=3
        )
        
        print(f"\n💰 Found {len(high_value_tokens)} high-value tokens:")
        for i, token in enumerate(high_value_tokens, 1):
            print(f"  {i}. {token.symbol}")
            print(f"     💵 Price: ${token.price:.6f}")
            print(f"     📊 Volume: ${token.volume:,.0f}")
            print(f"     🏦 Market Cap: ${token.market_cap:,.0f}")
            print(f"     💧 Liquidity: ${token.liquidity:,.0f}")
            print(f"     📈 24h Change: {token.price_change_percent:.2f}%")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_6_safe_tokens():
    """Example 6: Safe tokens with all security filters"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 6: Safe Tokens (All Security Filters)")
    print("=" * 60)
    
    api = create_api()
    
    try:
        print("\n🛡️ Finding safe tokens with all security filters...")
        print("   - Not honeypots")
        print("   - Verified contracts")
        print("   - Renounced ownership")
        
        safe_tokens = api.get_safe_tokens(
            Chain.SOLANA,
            criteria=SortCriteria.VOLUME,
            limit=3
        )
        
        print(f"\n🔒 Found {len(safe_tokens)} safe tokens:")
        for i, token in enumerate(safe_tokens, 1):
            print(f"  {i}. {token.symbol}")
            print(f"     🆔 Address: {token.address}")
            print(f"     💵 Price: ${token.price:.6f}")
            print(f"     📊 Volume: ${token.volume:,.0f}")
            print(f"     ✅ Security: Honeypot={bool(token.is_honeypot)}, "
                  f"Open Source={bool(token.is_open_source)}, "
                  f"Renounced={bool(token.renounced)}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_7_factory_functions():
    """Example 7: Using factory functions for common queries"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 7: Factory Functions")
    print("=" * 60)
    
    api = create_api()
    
    try:
        # Use factory functions to create queries
        print("\n🏭 Using factory functions for common query patterns...")
        
        # Volume query
        volume_query = create_volume_query(Chain.ETHEREUM, TimePeriod.TWENTY_FOUR_HOURS)
        print(f"📊 Volume query: {volume_query.chain.value} - {volume_query.criteria.value}")
        
        volume_tokens = api.get_tokens(volume_query)
        top_volume = TopNFilter(2).filter(volume_tokens)
        
        print(f"   Top 2 volume tokens:")
        for i, token in enumerate(top_volume, 1):
            print(f"   {i}. {token.symbol} - ${token.volume:,.0f}")
        
        # Gainers query
        gainers_query = create_gainers_query(Chain.SOLANA, TimePeriod.ONE_HOUR)
        print(f"\n📈 Gainers query: {gainers_query.chain.value} - {gainers_query.criteria.value}")
        
        gainer_tokens = api.get_tokens(gainers_query)
        top_gainers = TopNFilter(2).filter(gainer_tokens)
        
        print(f"   Top 2 gainers:")
        for i, token in enumerate(top_gainers, 1):
            print(f"   {i}. {token.symbol} - {token.price_change_percent1h:.2f}%")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_8_custom_formatter():
    """Example 8: Creating and using custom formatter"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 8: Custom Formatter")
    print("=" * 60)
    
    # Define custom formatter
    class DetailedFormatter:
        def format(self, token: Token, index: int) -> str:
            return (f"  {index}. 🪙 {token.symbol} | "
                   f"💰 ${token.price:.6f} | "
                   f"📊 Vol: ${token.volume/1000000:.1f}M | "
                   f"🏦 MC: ${token.market_cap/1000000:.1f}M | "
                   f"👥 Holders: {token.holder_count:,} | "
                   f"📈 24h: {token.price_change_percent:.1f}%")
    
    api = create_api()
    
    try:
        print("\n🎨 Using custom detailed formatter...")
        
        tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=3)
        formatter = DetailedFormatter()
        
        print("\n💫 Detailed token information:")
        for i, token in enumerate(tokens, 1):
            print(formatter.format(token, i))
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_9_error_handling():
    """Example 9: Comprehensive error handling"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 9: Error Handling")
    print("=" * 60)
    
    # Test with potentially problematic configuration
    config = GMGNConfig(timeout=1, max_retries=1)  # Very short timeout
    api = GMGNTokenAPI(config)
    
    print("\n⚠️ Testing error handling with very short timeout...")
    
    try:
        # This might timeout or fail
        tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=5)
        print(f"✅ Success! Got {len(tokens)} tokens despite short timeout")
        
    except GMGNAPIError as e:
        print(f"🔌 API Error {e.status_code}: {e.message}")
        print("   This is a network/API related error")
        
    except GMGNParsingError as e:
        print(f"📝 Parsing Error: {e}")
        print("   This indicates response structure changed")
        
    except Exception as e:
        print(f"❓ Unexpected Error: {e}")
        print("   This is an unknown error type")


def example_10_cross_chain_comparison():
    """Example 10: Cross-chain comparison"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 10: Cross-Chain Comparison")
    print("=" * 60)
    
    api = create_api()
    
    chains_to_compare = [Chain.ETHEREUM, Chain.SOLANA, Chain.BASE]
    
    print("\n🌐 Comparing top volume tokens across different chains...")
    
    for chain in chains_to_compare:
        try:
            print(f"\n🔗 {chain.value.upper()} Chain:")
            tokens = api.get_top_volume_tokens(chain, limit=2)
            
            for i, token in enumerate(tokens, 1):
                volume_str = f"${token.volume/1000000:.1f}M" if token.volume >= 1000000 else f"${token.volume:,.0f}"
                print(f"   {i}. {token.symbol} - {volume_str}")
                
        except Exception as e:
            print(f"   ❌ Error getting {chain.value} tokens: {e}")


def example_11_smart_filter_tokens():
    """Example 11: Using built-in high-value token method"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 11: Smart Filter Tokens (Built-in Method)")
    print("=" * 60)
    
    api = create_api()
    
    try:
        print("\n💎 Finding high-value tokens on Base chain...")
        print("   - Small cap tokens (MC < $200K, Vol < $300K):")
 
        
        high_value_tokens = api.get_small_cap_tokens(Chain.SOLANA, limit=5)

        
        print(f"\n💰 Found {len(high_value_tokens)} high-value tokens:")
        for i, token in enumerate(high_value_tokens, 1):
            print(f"  {i}. {token.symbol}")
            print(f"     💵 Price: ${token.price:.6f}")
            print(f"     📊 Volume: ${token.volume:,.0f}")
            print(f"     🏦 Market Cap: ${token.market_cap:,.0f}")
            print(f"     💧 Liquidity: ${token.liquidity:,.0f}")
            print(f"     📈 24h Change: {token.price_change_percent:.2f}%")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_12_rugcheck_verification():
    """Example 12: Rugcheck verification for token safety"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 12: Rugcheck Verification")
    print("=" * 60)
    
    print("\n🛡️ Demonstrating rugcheck functionality for token safety verification...")
    
    # Create rugcheck-enabled API
    api = create_rugcheck_api(verbose=True)
    
    try:
        # Example 7: Rugcheck verification
        print("7. Rugcheck verified tokens (risk score < 0.3):")
        try:
            rugcheck_tokens = api.get_rugcheck_verified_tokens(Chain.SOLANA, limit=3, max_risk_score=0.3)
            formatter = RugcheckFormatter()

            for i, token in enumerate(rugcheck_tokens, 1):
                print(formatter.format(token, i))
                
        except Exception as e:
            print(f"Rugcheck example failed: {e}")
            print("Note: Rugcheck may be having API issues or may only work with specific tokens")

        print("\n" + "="*50 + "\n")

        # Example 8: Individual token rugcheck with debugging
        print("8. Individual token rugcheck (with debugging):")
        try:
            # Get a token to check
            volume_tokens = api.get_top_volume_tokens(Chain.SOLANA, limit=1)
            if volume_tokens:
                token = volume_tokens[0]
                print(f"Testing rugcheck with token: {token.symbol} ({token.address})")
                
                rugcheck_result = api.check_token_rug_risk(token.address, Chain.SOLANA)
                
                # Show raw results for debugging
                print(f"Raw rugcheck result keys: {list(rugcheck_result.keys())}")
                
                formatter = RugcheckFormatter()
                formatted_output = formatter.format_with_rugcheck(token, rugcheck_result, 1)
                print(formatted_output)
                
                # Show detailed rugcheck info if no error
                if "error" not in rugcheck_result:
                    print(f"    Summary data available: {rugcheck_result.get('summary', 'No summary')}")
                    print(f"    Risk score: {rugcheck_result.get('risk_score', 'Not calculated')}")
                else:
                    print(f"    Error details: {rugcheck_result['error']}")
            else:
                print("No tokens available for rugcheck")
                
        except Exception as e:
            print(f"Individual rugcheck example failed: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

        print("\nExamples completed successfully!")
        
    except Exception as e:
        print(f"❌ Rugcheck example error: {e}")
        print("   Note: Rugcheck requires internet connection and may have rate limits")

def main():
    """Run all examples"""
    print("🚀 GMGN Token API - Comprehensive Examples")
    print("==========================================")
    print("This will demonstrate various features of the refactored API including:")
    print("• Basic token fetching and filtering")
    print("• Advanced filtering with multiple criteria")  
    print("• Custom formatters and display options")
    print("• Cross-chain token comparison")
    print("• Rugcheck integration for safety verification")
    print("Note: Some examples may take time due to API rate limits.")
    
    examples = [
        example_1_basic_usage,
        example_2_custom_configuration,
        example_3_gainers_and_formatters,
        example_4_advanced_filtering,
        example_5_high_value_tokens,
        # example_6_safe_tokens,
        # example_7_factory_functions,
        # example_8_custom_formatter,
        # example_9_error_handling,
        example_10_cross_chain_comparison,
        example_11_smart_filter_tokens,
        example_12_rugcheck_verification
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Stopped at example {i}")
            break
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")
    
    print("\n\n🎉 Examples completed!")
    print("\nKey Features Demonstrated:")
    print("   📊 Token Discovery - Find trending tokens across multiple chains")
    print("   🔍 Advanced Filtering - Filter by volume, market cap, liquidity, price changes")
    print("   🎨 Custom Formatting - Display token data in multiple formats")
    print("   🛡️ Rugcheck Integration - Verify token safety with risk scoring")
    print("   🔗 Multi-Chain Support - Ethereum, Solana, BSC, Base")
    print("   ⚡ Factory Functions - Quick access patterns for common use cases")
    print("\nFor more details, check out:")
    print("   📖 MIGRATION_GUIDE.md - How to migrate from old version")
    print("   🔧 gmgn_api.py - Main API source code with rugcheck integration")
    print("   🛡️ Rugcheck Documentation - Token safety verification guide")
    print("\n💡 Rugcheck Usage Tips:")
    print("   • Use max_risk_score=0.2 for conservative trading")
    print("   • Combine rugcheck with volume/liquidity filters")
    print("   • Always verify results with multiple data sources")


if __name__ == "__main__":
    main() 