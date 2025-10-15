"""
Product service - orchestrates complete product analysis pipeline
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scraper import AmazonScraper
from src.product_orchestrator import ProductOrchestrator
from src.price_comparison import SerperPriceComparison
from src.analysis.web_search import WebSearchAnalyzer
from api.core.config import settings
import redis
import json


class ProductService:
    """
    Service for product scraping and analysis
    Flow: Scrape → Search Competitors → Search Reviews → LLM Structure → Save → Analyze
    """

    def __init__(self):
        """Initialize scraper, web searchers, and orchestrator"""

        # Initialize basic scraper (no LLM, just HTML parsing)
        self.scraper = AmazonScraper(
            use_llm_extraction=False,  # Disable LLM in scraper
            use_cache=True
        )

        # Initialize Redis
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True
            )
            self.redis_client.ping()
            print("✓ Redis client initialized")
        except Exception as e:
            print(f"⚠ Redis initialization failed: {str(e)}")
            self.redis_client = None

        # Initialize price comparison
        self.price_comparer = None
        if settings.SERPER_API_KEY:
            try:
                self.price_comparer = SerperPriceComparison(settings.SERPER_API_KEY)
                print("✓ Price comparison initialized")
            except Exception as e:
                print(f"⚠ Price comparison disabled: {str(e)}")

        # Initialize web search analyzer
        self.web_search_analyzer = None
        if settings.SERPER_API_KEY and settings.GOOGLE_API_KEY:
            try:
                self.web_search_analyzer = WebSearchAnalyzer(
                    settings.SERPER_API_KEY,
                    settings.GOOGLE_API_KEY
                )
                print("✓ Web search analyzer initialized")
            except Exception as e:
                print(f"⚠ Web search disabled: {str(e)}")

        # Initialize orchestrator
        self.orchestrator = None
        if settings.GOOGLE_API_KEY:
            try:
                self.orchestrator = ProductOrchestrator(
                    google_api_key=settings.GOOGLE_API_KEY,
                    serper_api_key=settings.SERPER_API_KEY,
                    redis_client=self.redis_client
                )
                print("✓ Product orchestrator initialized")
            except Exception as e:
                print(f"⚠ Orchestrator initialization failed: {str(e)}")

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
        if not self.scraper.validate_url(url):
            raise ValueError("Invalid Amazon URL")

        if not self.orchestrator:
            raise ValueError("Orchestrator not available. Check GOOGLE_API_KEY.")

        # Step 1: Scrape Amazon page (basic HTML parsing, no LLM)
        print(f"\n📦 Step 1: Scraping Amazon page...")
        amazon_raw_data = self.scraper.scrape_product(url)
        product_title = amazon_raw_data.get('title', '')
        print(f"✓ Scraped: {product_title[:60]}...")

        # Step 2: Search internet for competitive prices
        competitor_data = None
        if include_price_comparison and self.price_comparer and product_title:
            print(f"\n🔍 Step 2: Searching for competitor prices...")
            try:
                competitor_data = self.price_comparer.compare_prices(product_title)
                alt_count = len(competitor_data.get('alternative_prices', []))
                print(f"✓ Found {alt_count} competitor prices")
            except Exception as e:
                print(f"⚠ Price comparison failed: {str(e)}")

        # Step 3: Search internet for external reviews/feedback
        external_reviews = None
        if include_web_search and self.web_search_analyzer and product_title:
            print(f"\n🌐 Step 3: Searching for external reviews...")
            try:
                external_reviews = self.web_search_analyzer.analyze_product(product_title)
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

    def scrape_product(self, url: str) -> dict:
        """
        Quick scrape without analysis (for compatibility)

        Args:
            url: Amazon product URL

        Returns:
            Product data dictionary

        Raises:
            ValueError: If URL is invalid
            Exception: If scraping fails
        """
        if not self.scraper.validate_url(url):
            raise ValueError("Invalid Amazon URL")

        product_data = self.scraper.scrape_product(url)
        return product_data

    def get_product_from_cache(self, asin: str) -> dict:
        """
        Get product data from Redis cache

        Args:
            asin: Product ASIN

        Returns:
            Product data dictionary or None
        """
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True
            )

            key = f"product:{asin}"
            data = redis_client.get(key)

            if data:
                return json.loads(data)
            return None

        except Exception as e:
            print(f"Redis error: {str(e)}")
            return None


# Singleton instance
product_service = ProductService()
