"""
LangGraph Workflow Orchestrator
Handles parallel execution of scraping, price comparison, and web search
"""

import json
from typing import Dict, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.prompts import PromptTemplate
import operator
from src.scrapers import ScraperFactory
from src.price_comparison import SerperPriceComparison
from src.web_search import WebSearchAnalyzer
from src.utils.redis_manager import get_redis_client
from src.llm_provider import get_llm
from src.utils.prompts import get_product_analysis_prompt


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
    """Orchestrator for the product analysis workflow"""

    def __init__(self):
        self.redis_client = get_redis_client()
        self.price_comparer = SerperPriceComparison()
        self.web_search_analyzer = WebSearchAnalyzer()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        workflow = StateGraph(ProductWorkflowState)

        workflow.add_node("check_cache", self._check_cache_node)
        workflow.add_node("scrape_amazon", self._scrape_amazon_node)
        workflow.add_node("get_price_comparison", self._price_comparison_node)
        workflow.add_node("get_web_search", self._web_search_node)
        workflow.add_node("combine_results", self._combine_results_node)
        workflow.add_node("save_to_cache", self._save_to_cache_node)
        workflow.add_node("analyze_with_llm", self._analyze_with_llm_node)

        workflow.set_entry_point("check_cache")

        workflow.add_conditional_edges(
            "check_cache",
            self._should_skip_fetching,
            {
                "fully_cached": END,  # Both data and analysis cached, skip everything
                "data_cached": "analyze_with_llm",  # Data cached but need to analyze
                "fetch": "scrape_amazon"  # No cache, proceed with fetching
            }
        )

        # Add both edges from scrape_amazon - they will run in parallel
        workflow.add_edge("scrape_amazon", "get_price_comparison")
        workflow.add_edge("scrape_amazon", "get_web_search")

        workflow.add_edge("get_price_comparison", "combine_results")
        workflow.add_edge("get_web_search", "combine_results")

        workflow.add_edge("combine_results", "save_to_cache")
        workflow.add_edge("save_to_cache", "analyze_with_llm")
        workflow.add_edge("analyze_with_llm", END)

        return workflow.compile()

    def _check_cache_node(self, state: ProductWorkflowState) -> ProductWorkflowState:
        """Check if product data and analysis exist in Redis cache"""
        print("\n🔍 Checking Redis cache...")

        try:
            scraper = ScraperFactory.get_scraper(state["url"])

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
            state["amazon_data"] = product_data
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

        print("\n💰 Fetching price comparison data...")

        updates = {"price_comparison_complete": True}

        try:
            product_title = state["amazon_data"].get("title", "")
            source_platform = state["amazon_data"]["platform"]

            if product_title:
                price_data = self.price_comparer.compare_prices(
                    product_title,
                    source_platform  # Pass platform for filtering
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

        print("\n🌐 Fetching web search data (reviews, Reddit, news)...")

        updates = {"web_search_complete": True}

        try:
            product_title = state["amazon_data"].get("title", "")
            source_platform = state["amazon_data"]["platform"]

            if product_title:
                web_data = self.web_search_analyzer.analyze_product(
                    product_title,
                    source_platform
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

            # Format competitor prices for easy frontend access
            competitor_prices = []
            price_comparison = state["price_comparison_data"].get('price_comparison', {})

            for platform, products in price_comparison.items():
                if not products:
                    continue

                for product in products:
                    # Convert numeric price to formatted string
                    price_num = product.get('price', 0)
                    currency = product.get('currency', 'INR')

                    # Format price with currency symbol
                    if currency == 'INR':
                        price_str = f"₹{price_num:,.0f}" if price_num else "N/A"
                    else:
                        price_str = f"{currency} {price_num:,.2f}" if price_num else "N/A"

                    competitor_prices.append({
                        "site": product.get('seller', platform),
                        "price": price_str,
                        "url": product.get('url', ''),
                        "availability": "In Stock" if product.get('in_stock', True) else "Out of Stock"
                    })

            # Sort by numeric price (lowest first) and return top 5
            import re
            def get_numeric_price(item):
                price_str = item['price']
                match = re.search(r'[\d,]+\.?\d*', price_str)
                if match:
                    return float(match.group().replace(',', ''))
                return float('inf')

            competitor_prices.sort(key=get_numeric_price)
            product_data["competitor_prices"] = competitor_prices[:5]  # Top 5 lowest prices
            print(f"  ✓ Added {len(product_data['competitor_prices'])} competitor prices")

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
        print("\n🤖 Running LLM analysis...")
        try:
            # Create LLM chain directly for analysis
            analysis_prompt = PromptTemplate(
                template=get_product_analysis_prompt(),
                input_variables=["product_data", "title"]
            )
            analysis_chain = analysis_prompt | get_llm(temperature=0.3)

            # Generate analysis
            print(f"  📦 Analyzing {len(str(state['product_data']))} chars of product data...")
            analysis_result = analysis_chain.invoke({
                "product_data": json.dumps(state["product_data"], indent=2, ensure_ascii=False),
                "title": state["product_data"].get('title', 'Product')
            })

            # Extract analysis text
            state["analysis"] = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)
            print(f"  ✓ Analysis complete ({len(state['analysis'])} characters)")

            # Cache the analysis separately for faster future requests
            if state["analysis"]:
                self.redis_client.setex(f"product:{state['asin']}:analysis", 86400, state["analysis"])
                print(f"  ✓ Cached analysis to Redis: product:{state['asin']}:analysis")

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