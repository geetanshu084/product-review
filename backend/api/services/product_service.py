"""
Product service - orchestrates complete product analysis pipeline
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers import ScraperFactory
from src.product_orchestrator import ProductOrchestrator
from src.workflow_orchestrator import ProductWorkflowOrchestrator
from src.price_comparison import SerperPriceComparison
from src.analysis.web_search import WebSearchAnalyzer
from src.redis_manager import get_redis_client
from api.core.config import settings
import json


class ProductService:
    """
    Service for product scraping and analysis
    NEW FLOW: Parallel execution using LangGraph
    - Scrape Amazon + Price Comparison + Web Search (all in parallel)
    - Combine results and save to Redis
    - Analyze uses cached data if available
    """

    def __init__(self):
        """Initialize services and orchestrators"""

        # Initialize Redis using centralized client (will fail at startup if not available)
        self.redis_client = get_redis_client()

        # Initialize LangGraph workflow orchestrator (NEW - handles parallel execution)
        self.workflow_orchestrator = None
        if settings.GOOGLE_API_KEY:
            try:
                self.workflow_orchestrator = ProductWorkflowOrchestrator(
                    google_api_key=settings.GOOGLE_API_KEY,
                    serper_api_key=settings.SERPER_API_KEY,
                    redis_client=self.redis_client
                )
                print("✓ LangGraph workflow orchestrator initialized")
            except Exception as e:
                print(f"⚠ Workflow orchestrator initialization failed: {str(e)}")

        # Scraper factory will select appropriate scraper based on URL
        # No need to initialize scraper here - will be created on-demand per URL

        # Initialize price comparison (for legacy /analyze endpoint)
        self.price_comparer = None
        if settings.SERPER_API_KEY:
            try:
                self.price_comparer = SerperPriceComparison()
                print("✓ Price comparison initialized")
            except Exception as e:
                print(f"⚠ Price comparison initialization failed: {str(e)}")

        # Initialize web search analyzer (for legacy /analyze endpoint)
        self.web_search_analyzer = None
        if settings.SERPER_API_KEY and settings.GOOGLE_API_KEY:
            try:
                self.web_search_analyzer = WebSearchAnalyzer()
                print("✓ Web search analyzer initialized")
            except Exception as e:
                print(f"⚠ Web search analyzer initialization failed: {str(e)}")

        # Legacy orchestrator (for /analyze endpoint)
        self.orchestrator = None
        if settings.GOOGLE_API_KEY:
            try:
                self.orchestrator = ProductOrchestrator(redis_client=self.redis_client)
                print("✓ Legacy orchestrator initialized (for /analyze endpoint)")
            except Exception as e:
                print(f"⚠ Legacy orchestrator initialization failed: {str(e)}")

    def scrape_and_analyze(
        self,
        url: str,
        include_price_comparison: bool = True,
        include_web_search: bool = True
    ) -> dict:
        """
        Complete pipeline: Scrape → Search → Structure → Analyze

        Args:
            url: Amazon product URL
            include_price_comparison: Whether to search for competitor prices
            include_web_search: Whether to search for external reviews

        Returns:
            Dictionary with structured_data and analysis

        Raises:
            ValueError: If URL is invalid or orchestrator not available
            Exception: If processing fails
        """
        # Validate URL with factory (supports multiple platforms)
        if not ScraperFactory.is_url_supported(url):
            supported = ScraperFactory.get_supported_platforms()
            raise ValueError(f"Invalid URL. Supported platforms: {', '.join(supported)}")

        if not self.orchestrator:
            raise ValueError("Orchestrator not available. Check GOOGLE_API_KEY.")

        # Step 1: Scrape product page (Amazon, Flipkart, etc.)
        scraper = ScraperFactory.get_scraper(url)
        platform = scraper.get_platform_name()
        print(f"\n📦 Step 1: Scraping {platform} page...")
        amazon_raw_data = scraper.scrape_product(url)
        product_title = amazon_raw_data.get('title', '')
        print(f"✓ Scraped: {product_title[:60]}...")

        # Step 2: Search internet for competitive prices
        competitor_data = None
        if include_price_comparison and self.price_comparer and product_title:
            print(f"\n🔍 Step 2: Searching for competitor prices...")
            try:
                # Get platform name for filtering
                source_platform = amazon_raw_data.get('platform', platform)
                competitor_data = self.price_comparer.compare_prices(
                    product_title,
                    source_platform=source_platform
                )
                alt_count = len(competitor_data.get('alternative_prices', []))
                print(f"✓ Found {alt_count} competitor prices")
            except Exception as e:
                print(f"⚠ Price comparison failed: {str(e)}")

        # Step 3: Search internet for external reviews/feedback
        external_reviews = None
        if include_web_search and self.web_search_analyzer and product_title:
            print(f"\n🌐 Step 3: Searching for external reviews...")
            try:
                # Get platform name for filtering
                source_platform = amazon_raw_data.get('platform', platform)
                external_reviews = self.web_search_analyzer.analyze_product(
                    product_title,
                    source_platform=source_platform
                )
                review_count = len(external_reviews.get('external_reviews', []))
                print(f"✓ Found {review_count} external reviews")
            except Exception as e:
                print(f"⚠ Web search failed: {str(e)}")

        # Step 4-6: LLM Structure → Save → Analyze (handled by orchestrator)
        print(f"\n🤖 Step 4-6: Processing with LLM orchestrator...")
        result = self.orchestrator.process_product_sync(
            amazon_raw_data=amazon_raw_data,
            competitor_data=competitor_data,
            external_reviews=external_reviews
        )

        return result

    def scrape_product(
        self,
        url: str,
        include_price_comparison: bool = True,
        include_web_search: bool = True
    ) -> dict:
        """
        NEW: Scrape product with parallel execution using LangGraph
        Runs Amazon scraping + price comparison + web search in parallel
        Saves everything to Redis cache

        Args:
            url: Amazon product URL
            include_price_comparison: Whether to fetch competitor prices
            include_web_search: Whether to fetch external reviews

        Returns:
            Complete product data dictionary

        Raises:
            ValueError: If URL is invalid or workflow not available
            Exception: If scraping fails
        """
        if not self.workflow_orchestrator:
            raise ValueError("Workflow orchestrator not available. Check GOOGLE_API_KEY.")

        # Validate URL with factory (supports multiple platforms)
        if not ScraperFactory.is_url_supported(url):
            supported = ScraperFactory.get_supported_platforms()
            raise ValueError(f"Invalid URL. Supported platforms: {', '.join(supported)}")

        # Run LangGraph workflow (parallel execution)
        result = self.workflow_orchestrator.run(
            url=url,
            include_price_comparison=include_price_comparison,
            include_web_search=include_web_search
        )

        if not result.get("success"):
            raise Exception(result.get("error", "Workflow execution failed"))

        return result.get("data", {})

    def scrape_and_analyze_unified(
        self,
        url: str,
        include_price_comparison: bool = True,
        include_web_search: bool = True
    ) -> dict:
        """
        UNIFIED: Complete workflow with parallel execution + LLM analysis

        Workflow:
        1. Check Redis cache first
        2. If NOT cached:
           - Scrape Amazon (parallel)
           - Get price comparison (parallel)
           - Get web search (parallel)
           - Combine results
           - Save to Redis
           - Analyze with LLM
        3. If cached:
           - Get from Redis
           - Analyze with LLM

        Args:
            url: Amazon product URL
            include_price_comparison: Whether to fetch competitor prices
            include_web_search: Whether to fetch external reviews

        Returns:
            Dictionary with 'structured_data' and 'analysis'

        Raises:
            ValueError: If URL is invalid or workflow not available
            Exception: If processing fails
        """
        if not self.workflow_orchestrator:
            raise ValueError("Workflow orchestrator not available. Check GOOGLE_API_KEY.")

        # Validate URL with factory (supports multiple platforms)
        if not ScraperFactory.is_url_supported(url):
            supported = ScraperFactory.get_supported_platforms()
            raise ValueError(f"Invalid URL. Supported platforms: {', '.join(supported)}")

        # Run LangGraph workflow (includes analysis now)
        result = self.workflow_orchestrator.run(
            url=url,
            include_price_comparison=include_price_comparison,
            include_web_search=include_web_search
        )

        if not result.get("success"):
            raise Exception(result.get("error", "Workflow execution failed"))

        return {
            "structured_data": result.get("data", {}),
            "analysis": result.get("analysis", "")
        }

    def get_product_from_cache(self, asin: str) -> dict:
        """
        Get product data from Redis cache

        Args:
            asin: Product ASIN

        Returns:
            Product data dictionary or None
        """
        try:
            key = f"product:{asin}"
            data = self.redis_client.get(key)

            if data:
                return json.loads(data)
            return None

        except Exception as e:
            print(f"Redis error: {str(e)}")
            return None


# Singleton instance
product_service = ProductService()
