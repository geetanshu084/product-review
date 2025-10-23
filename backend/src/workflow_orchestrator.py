"""
LangGraph Workflow Orchestrator
Handles parallel execution of scraping, price comparison, and web search
"""

import json
from typing import Dict, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator
from src.scrapers import ScraperFactory
from src.price_comparison import SerperPriceComparison
from src.analysis.web_search import WebSearchAnalyzer
from src.redis_manager import get_redis_client


def merge_dicts(left: Optional[Dict], right: Optional[Dict]) -> Optional[Dict]:
    """Merge two dictionaries, with right taking precedence"""
    if left is None:
        return right
    if right is None:
        return left
    return {**left, **right}


class ProductWorkflowState(TypedDict):
    """State for the product analysis workflow"""
    # Input (these never change after initialization)
    url: str
    asin: Optional[str]

    # Outputs from parallel nodes - using Annotated to allow concurrent updates
    amazon_data: Optional[Dict]
    price_comparison_data: Optional[Dict]
    web_search_data: Optional[Dict]

    # Combined output
    product_data: Optional[Dict]

    # Analysis output
    analysis: Optional[str]

    # Error tracking - allows multiple nodes to add errors concurrently
    errors: Annotated[list, operator.add]

    # Status tracking - these are set by individual nodes independently
    scraping_complete: Annotated[bool, lambda x, y: x or y]
    price_comparison_complete: Annotated[bool, lambda x, y: x or y]
    web_search_complete: Annotated[bool, lambda x, y: x or y]
    analysis_complete: Annotated[bool, lambda x, y: x or y]


class ProductWorkflowOrchestrator:
    """
    LangGraph-based orchestrator for product data collection with intelligent caching

    Workflow:
    1. Check Redis cache first for both product data AND analysis
    2. If fully cached (data + analysis): Return immediately (NO LLM calls!)
    3. If only data cached: Skip to LLM analysis
    4. If not cached at all:
       a. Scrape product page (Amazon, Flipkart, etc.)
       b. Run in parallel:
          - Price comparison (if enabled)
          - Web search for reviews (if enabled)
       c. Combine all results
       d. Save product data to Redis (24h TTL)
       e. Run LLM analysis
       f. Save analysis to Redis (24h TTL)
    5. Return complete product data + analysis

    Cache Keys:
    - Product data: product:{asin} or flipkart:{fsn}
    - Analysis: product:{asin}:analysis or flipkart:{fsn}:analysis
    """

    def __init__(self):
        """
        Initialize the workflow orchestrator

        All configuration is read from environment variables:
        - LLM_PROVIDER, LLM_MODEL, and corresponding provider API key: For LLM operations
        - SERPER_API_KEY: For price comparison and web search
        - REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD: For Redis caching
        """
        # Get centralized Redis client from utility function
        self.redis_client = get_redis_client()

        # Get SERPER_API_KEY from environment
        import os
        serper_api_key = os.getenv("SERPER_API_KEY")

        # Scraper factory will select appropriate scraper based on URL
        # No need to initialize scraper here - will be created on-demand per URL

        self.price_comparer = None
        if serper_api_key:
            # SerperPriceComparison reads SERPER_API_KEY from environment
            self.price_comparer = SerperPriceComparison()

        self.web_search_analyzer = None
        if serper_api_key:
            # WebSearchAnalyzer uses LLM factory pattern internally
            # It will use whatever LLM provider is configured
            self.web_search_analyzer = WebSearchAnalyzer()

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Create workflow graph
        workflow = StateGraph(ProductWorkflowState)

        # Add nodes
        workflow.add_node("check_cache", self._check_cache_node)
        workflow.add_node("scrape_amazon", self._scrape_amazon_node)
        workflow.add_node("get_price_comparison", self._price_comparison_node)
        workflow.add_node("get_web_search", self._web_search_node)
        workflow.add_node("combine_results", self._combine_results_node)
        workflow.add_node("save_to_cache", self._save_to_cache_node)
        workflow.add_node("analyze_with_llm", self._analyze_with_llm_node)

        # Set entry point
        workflow.set_entry_point("check_cache")

        # Add conditional edges from cache check
        workflow.add_conditional_edges(
            "check_cache",
            self._should_skip_fetching,
            {
                "fully_cached": END,  # Both data and analysis cached, skip everything
                "data_cached": "analyze_with_llm",  # Data cached but need to analyze
                "fetch": "scrape_amazon"  # No cache, proceed with fetching
            }
        )

        # After scraping completes, both price and web search can run
        # Add both edges from scrape_amazon - they will run in parallel
        workflow.add_edge("scrape_amazon", "get_price_comparison")
        workflow.add_edge("scrape_amazon", "get_web_search")

        # Both price_comparison and web_search go to combine_results
        # combine_results will wait for BOTH to complete before executing
        workflow.add_edge("get_price_comparison", "combine_results")
        workflow.add_edge("get_web_search", "combine_results")

        # Save to cache then analyze
        workflow.add_edge("combine_results", "save_to_cache")
        workflow.add_edge("save_to_cache", "analyze_with_llm")
        workflow.add_edge("analyze_with_llm", END)

        # Compile workflow
        return workflow.compile()

    def _check_cache_node(self, state: ProductWorkflowState) -> ProductWorkflowState:
        """Check if product data and analysis exist in Redis cache"""
        print("\n🔍 Checking Redis cache...")

        try:
            # Get appropriate scraper for this URL
            scraper = ScraperFactory.get_scraper(state["url"])

            # Extract product ID (ASIN for Amazon, FSN for Flipkart, etc.)
            product_id = scraper.extract_product_id(state["url"])
            state["asin"] = product_id

            if not product_id:
                print("  ⚠ Could not extract product ID from URL")
                return state

            # Try to get product data from cache using consistent cache key
            # Use product:{id} format consistently
            cache_key = f"product:{product_id}"
            cached_json = self.redis_client.get(cache_key)

            # Try to get analysis from cache
            analysis_cache_key = f"{cache_key}:analysis"
            cached_analysis = self.redis_client.get(analysis_cache_key)

            if cached_json:
                cached_data = json.loads(cached_json)

                # Check if cached data has all requested components based on available services
                has_price_comp = "price_comparison" in cached_data or "competitor_prices" in cached_data
                has_web_search = "web_search_analysis" in cached_data

                cache_complete = True
                if self.price_comparer and not has_price_comp:
                    cache_complete = False
                if self.web_search_analyzer and not has_web_search:
                    cache_complete = False

                if cache_complete:
                    print(f"  ✓ Complete cached data found for product ID: {product_id}")
                    state["product_data"] = cached_data
                    state["scraping_complete"] = True
                    state["price_comparison_complete"] = True
                    state["web_search_complete"] = True

                    # Check if analysis is also cached
                    if cached_analysis:
                        print(f"  ✓ Cached analysis found - skipping LLM call")
                        state["analysis"] = cached_analysis.decode('utf-8') if isinstance(cached_analysis, bytes) else cached_analysis
                        state["analysis_complete"] = True
                    else:
                        print(f"  ⚠ No cached analysis found - will run LLM analysis")

                    return state
                else:
                    print(f"  ⚠ Partial cache found - missing requested components")
                    return state
            else:
                print(f"  ⚠ No cache found for product ID: {product_id}")
                return state

        except Exception as e:
            print(f"  ⚠ Cache check error: {str(e)}")
            state["errors"] = state.get("errors", []) + [f"Cache check error: {str(e)}"]
            return state

    def _should_skip_fetching(self, state: ProductWorkflowState) -> str:
        """Determine if we should skip fetching based on cache"""
        if state.get("product_data"):
            # Check if analysis is also cached
            if state.get("analysis_complete") and state.get("analysis"):
                return "fully_cached"  # Both data and analysis cached
            return "data_cached"  # Only data cached, need to analyze
        return "fetch"  # Nothing cached, need to fetch everything

    def _scrape_amazon_node(self, state: ProductWorkflowState) -> ProductWorkflowState:
        """Scrape product page (Amazon, Flipkart, etc.)"""
        try:
            # Get appropriate scraper for this URL
            scraper = ScraperFactory.get_scraper(state["url"])
            platform = scraper.get_platform_name()

            print(f"\n🛒 Scraping {platform} product page...")

            product_data = scraper.scrape_product(state["url"])
            state["amazon_data"] = product_data  # Keep key name for compatibility
            state["asin"] = product_data.get("asin") or product_data.get("product_id")
            state["scraping_complete"] = True
            print(f"  ✓ {platform} scraping complete for: {product_data.get('title', 'N/A')[:50]}...")

        except Exception as e:
            print(f"  ❌ Product scraping failed: {str(e)}")
            state["errors"] = state.get("errors", []) + [f"Scraping error: {str(e)}"]
            state["scraping_complete"] = True  # Mark as complete even if failed

        return state

    def _price_comparison_node(self, state: ProductWorkflowState) -> Dict:
        """Get price comparison data (runs in parallel with web search)"""

        # Skip if price comparer not available (no API key was set during initialization)
        if not self.price_comparer:
            print("\n💰 Price comparison skipped (no API key)")
            return {"price_comparison_complete": True}

        # Wait for Amazon data
        if not state.get("amazon_data"):
            print("\n⚠ Waiting for Amazon data before price comparison...")
            return {"price_comparison_complete": True}

        print("\n💰 Fetching price comparison data...")

        updates = {"price_comparison_complete": True}

        try:
            product_title = state["amazon_data"].get("title", "")
            source_platform = state["amazon_data"].get("platform", "")  # Get platform from scraped data

            if product_title:
                price_data = self.price_comparer.compare_prices(
                    product_title,
                    location="India",
                    num_results=20,
                    source_platform=source_platform  # Pass platform for filtering
                )
                updates["price_comparison_data"] = price_data
                print(f"  ✓ Price comparison complete: {price_data.get('total_results', 0)} results")
            else:
                print("  ⚠ No product title available for price comparison")

        except Exception as e:
            print(f"  ❌ Price comparison failed: {str(e)}")
            updates["errors"] = [f"Price comparison error: {str(e)}"]

        return updates

    def _web_search_node(self, state: ProductWorkflowState) -> Dict:
        """Get web search data (runs in parallel with price comparison)"""

        # Skip if web search analyzer not available (no API key was set during initialization)
        if not self.web_search_analyzer:
            print("\n🌐 Web search skipped (no API key)")
            return {"web_search_complete": True}

        # Wait for Amazon data
        if not state.get("amazon_data"):
            print("\n⚠ Waiting for Amazon data before web search...")
            return {"web_search_complete": True}

        print("\n🌐 Fetching web search data (reviews, Reddit, news)...")

        updates = {"web_search_complete": True}

        try:
            product_title = state["amazon_data"].get("title", "")
            source_platform = state["amazon_data"].get("platform", "")  # Get platform from scraped data

            if product_title:
                web_data = self.web_search_analyzer.analyze_product(
                    product_title,
                    source_platform=source_platform  # Pass platform for filtering
                )
                updates["web_search_data"] = web_data

                total_sources = (
                    len(web_data.get("external_reviews", [])) +
                    len(web_data.get("reddit_discussions", [])) +
                    len(web_data.get("news_articles", []))
                )
                print(f"  ✓ Web search complete: {total_sources} sources found")
            else:
                print("  ⚠ No product title available for web search")

        except Exception as e:
            print(f"  ❌ Web search failed: {str(e)}")
            updates["errors"] = [f"Web search error: {str(e)}"]

        return updates

    def _combine_results_node(self, state: ProductWorkflowState) -> ProductWorkflowState:
        """Combine all results into final product data"""
        print("\n🔄 Combining all results...")

        # Start with Amazon data
        product_data = state.get("amazon_data", {})

        # Add price comparison if available
        if state.get("price_comparison_data"):
            product_data["price_comparison"] = state["price_comparison_data"]

            # Also prepare competitor_prices for easy frontend access
            from src.product_orchestrator import ProductOrchestrator
            # Use the existing helper to format competitor prices
            orchestrator = ProductOrchestrator()
            competitor_prices = orchestrator._prepare_competitor_prices(state["price_comparison_data"])
            product_data["competitor_prices"] = competitor_prices
            print(f"  ✓ Added {len(competitor_prices)} competitor prices")

        # Add web search if available
        if state.get("web_search_data"):
            product_data["web_search_analysis"] = state["web_search_data"]

            total_sources = (
                len(state["web_search_data"].get("external_reviews", [])) +
                len(state["web_search_data"].get("reddit_discussions", [])) +
                len(state["web_search_data"].get("news_articles", []))
            )
            print(f"  ✓ Added {total_sources} external sources")

        state["product_data"] = product_data
        print("  ✓ Results combined successfully")

        return state

    def _save_to_cache_node(self, state: ProductWorkflowState) -> ProductWorkflowState:
        """Save combined results to Redis cache"""

        if not state.get("product_data"):
            print("\n⚠ Skipping cache save (no data)")
            return state

        print("\n💾 Saving to Redis cache...")

        try:
            asin = state.get("asin")
            if asin:
                cache_key = f"product:{asin}"
                product_json = json.dumps(state["product_data"], ensure_ascii=False)
                self.redis_client.setex(cache_key, 86400, product_json)  # 24 hour TTL
                print(f"  ✓ Saved to Redis: {cache_key} (TTL: 24 hours)")
            else:
                print("  ⚠ No ASIN available, skipping cache save")

        except Exception as e:
            print(f"  ❌ Cache save error: {str(e)}")
            state["errors"] = state.get("errors", []) + [f"Cache save error: {str(e)}"]

        return state

    def _analyze_with_llm_node(self, state: ProductWorkflowState) -> ProductWorkflowState:
        """Analyze product data with LLM (final step)"""
        # Skip if analysis already exists (from cache)
        if state.get("analysis_complete") and state.get("analysis"):
            print("\n✓ Using cached analysis - skipping LLM call")
            return state

        if not state.get("product_data"):
            print("\n⚠ Skipping analysis (no product data available)")
            state["analysis_complete"] = True
            return state

        print("\n🤖 Running LLM analysis...")
        try:
            # Import orchestrator for analysis
            from src.product_orchestrator import ProductOrchestrator

            # Create orchestrator instance
            orchestrator = ProductOrchestrator()

            # Run analysis on the combined product data
            result = orchestrator.process_product_sync(
                amazon_raw_data=state["product_data"],
                competitor_data=state["product_data"].get("price_comparison"),
                external_reviews=state["product_data"].get("web_search_analysis")
            )

            # Extract analysis and structured data
            state["analysis"] = result.get("analysis", "")

            # Update product_data with structured data if available
            if result.get("structured_data"):
                state["product_data"] = result["structured_data"]

            print(f"  ✓ Analysis complete ({len(state['analysis'])} characters)")

            # Cache the analysis separately for faster future requests
            if state.get("asin") and state["analysis"]:
                try:
                    # Use consistent cache key format: product:{id}
                    cache_key = f"product:{state['asin']}"
                    analysis_cache_key = f"{cache_key}:analysis"

                    # Save analysis with same TTL as product data (24 hours)
                    self.redis_client.setex(analysis_cache_key, 86400, state["analysis"])
                    print(f"  ✓ Cached analysis to Redis: {analysis_cache_key}")
                except Exception as cache_error:
                    print(f"  ⚠ Failed to cache analysis: {str(cache_error)}")

        except Exception as e:
            print(f"  ❌ Analysis failed: {str(e)}")
            state["errors"] = state.get("errors", []) + [f"Analysis error: {str(e)}"]

        state["analysis_complete"] = True
        return state

    def run(self, url: str) -> Dict:
        """
        Run the complete workflow

        Args:
            url: Product URL (Amazon, Flipkart, etc.)

        Returns:
            Complete product data with all requested components

        Note:
            Price comparison and web search are automatically enabled
            if SERPER_API_KEY is set in environment variables.
        """
        print(f"\n{'='*60}")
        print("🚀 Starting Product Data Collection Workflow")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"Price Comparison: {'✓' if self.price_comparer else '✗'}")
        print(f"Web Search: {'✓' if self.web_search_analyzer else '✗'}")

        # Initialize state
        initial_state = ProductWorkflowState(
            url=url,
            asin=None,
            amazon_data=None,
            price_comparison_data=None,
            web_search_data=None,
            product_data=None,
            analysis=None,
            errors=[],
            scraping_complete=False,
            price_comparison_complete=False,
            web_search_complete=False,
            analysis_complete=False
        )

        # Run workflow
        try:
            final_state = self.workflow.invoke(initial_state)

            print(f"\n{'='*60}")
            print("✅ Workflow Complete!")
            print(f"{'='*60}")

            if final_state.get("errors"):
                print(f"\n⚠ Errors encountered: {len(final_state['errors'])}")
                for error in final_state["errors"]:
                    print(f"  - {error}")

            return {
                "success": True,
                "data": final_state.get("product_data", {}),
                "analysis": final_state.get("analysis", ""),
                "errors": final_state.get("errors", [])
            }

        except Exception as e:
            print(f"\n❌ Workflow failed: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "errors": [str(e)]
            }
