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
    include_price_comparison: bool
    include_web_search: bool

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
    LangGraph-based orchestrator for product data collection

    Workflow:
    1. Check Redis cache first
    2. If not cached, run 3 parallel nodes:
       - Amazon scraping
       - Price comparison (if enabled)
       - Web search (if enabled)
    3. Combine results
    4. Save to Redis
    5. Return complete product data
    """

    def __init__(
        self,
        google_api_key: str,
        serper_api_key: Optional[str] = None,
        redis_client=None
    ):
        """
        Initialize the workflow orchestrator

        All configuration is read from environment variables:
        - LLM_PROVIDER, LLM_MODEL, GOOGLE_API_KEY (or provider key): For LLM operations
        - SERPER_API_KEY: For price comparison and web search
        - REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD: For Redis caching

        Args:
            google_api_key: Google API key for Gemini LLM (deprecated, kept for backward compatibility)
            serper_api_key: Serper API key for price/web search (deprecated, kept for backward compatibility)
            redis_client: Redis client for caching (optional, will use centralized client if not provided)
        """
        self.google_api_key = google_api_key
        self.serper_api_key = serper_api_key

        # Use provided redis_client or get centralized one
        self.redis_client = redis_client if redis_client is not None else get_redis_client()

        # Scraper factory will select appropriate scraper based on URL
        # No need to initialize scraper here - will be created on-demand per URL

        self.price_comparer = None
        if serper_api_key:
            # SerperPriceComparison reads SERPER_API_KEY from environment
            self.price_comparer = SerperPriceComparison()

        self.web_search_analyzer = None
        if serper_api_key and google_api_key:
            # WebSearchAnalyzer reads both keys from environment
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
                "cached": "analyze_with_llm",  # Data found in cache, analyze it
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
        """Check if product data exists in Redis cache"""
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

            # Try to get from cache using platform-specific cache key
            cache_key = scraper.get_cache_key(product_id)
            cached_json = self.redis_client.get(cache_key)

            if cached_json:
                cached_data = json.loads(cached_json)

                # Check if cached data has all requested components
                has_price_comp = "price_comparison" in cached_data or "competitor_prices" in cached_data
                has_web_search = "web_search_analysis" in cached_data

                cache_complete = True
                if state.get("include_price_comparison", False) and not has_price_comp:
                    cache_complete = False
                if state.get("include_web_search", False) and not has_web_search:
                    cache_complete = False

                if cache_complete:
                    print(f"  ✓ Complete cached data found for product ID: {product_id}")
                    state["product_data"] = cached_data
                    state["scraping_complete"] = True
                    state["price_comparison_complete"] = True
                    state["web_search_complete"] = True
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
            return "cached"
        return "fetch"

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

        # Skip if not requested or no scraper available
        if not state.get("include_price_comparison", False) or not self.price_comparer:
            print("\n💰 Price comparison skipped (not enabled or no API key)")
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

        # Skip if not requested or no analyzer available
        if not state.get("include_web_search", False) or not self.web_search_analyzer:
            print("\n🌐 Web search skipped (not enabled or no API key)")
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
            orchestrator = ProductOrchestrator(redis_client=self.redis_client)
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
        if not state.get("product_data"):
            print("\n⚠ Skipping analysis (no product data available)")
            state["analysis_complete"] = True
            return state

        print("\n🤖 Running LLM analysis...")
        try:
            # Import orchestrator for analysis
            from src.product_orchestrator import ProductOrchestrator

            # Create orchestrator instance
            orchestrator = ProductOrchestrator(redis_client=self.redis_client)

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

        except Exception as e:
            print(f"  ❌ Analysis failed: {str(e)}")
            state["errors"] = state.get("errors", []) + [f"Analysis error: {str(e)}"]

        state["analysis_complete"] = True
        return state

    def run(
        self,
        url: str,
        include_price_comparison: bool = True,
        include_web_search: bool = True
    ) -> Dict:
        """
        Run the complete workflow

        Args:
            url: Amazon product URL
            include_price_comparison: Whether to include price comparison
            include_web_search: Whether to include web search

        Returns:
            Complete product data with all requested components
        """
        print(f"\n{'='*60}")
        print("🚀 Starting Product Data Collection Workflow")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"Price Comparison: {'✓' if include_price_comparison else '✗'}")
        print(f"Web Search: {'✓' if include_web_search else '✗'}")

        # Initialize state
        initial_state = ProductWorkflowState(
            url=url,
            asin=None,
            include_price_comparison=include_price_comparison,
            include_web_search=include_web_search,
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
                "errors": final_state.get("errors", []),
                "cached": final_state.get("product_data") and not final_state.get("amazon_data")
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
