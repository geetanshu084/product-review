"""
Product service - orchestrates complete product analysis pipeline
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers import ScraperFactory
from src.workflow_orchestrator import ProductWorkflowOrchestrator
from src.utils.redis_manager import get_redis_client
from api.core.config import settings
import json


class ProductService:
    """
    Service for product scraping and analysis using LangGraph workflow

    Features:
    - Parallel execution: Scraping + Price Comparison + Web Search
    - Intelligent dual-layer caching (product data + analysis)
    - Multi-platform support: Amazon, Flipkart, and more
    - Multi-provider LLM support: Google, OpenAI, Anthropic, Groq, Cohere, Ollama
    """

    def __init__(self):
        """Initialize services and orchestrators"""

        # Initialize Redis using centralized client (will fail at startup if not available)
        self.redis_client = get_redis_client()

        # Initialize LangGraph workflow orchestrator (NEW - handles parallel execution)
        # LLM is validated at server startup, so we can assume it's available
        try:
            self.workflow_orchestrator = ProductWorkflowOrchestrator()
            print(f"✓ LangGraph workflow orchestrator initialized (LLM: {settings.LLM_PROVIDER})")
        except Exception as e:
            print(f"❌ CRITICAL: Workflow orchestrator initialization failed: {str(e)}")
            raise

        # All services now use the unified LangGraph workflow
        # No legacy endpoints remain

    def scrape_and_analyze_unified(self, url: str) -> dict:
        """
        UNIFIED: Complete workflow with parallel execution + LLM analysis

        Workflow:
        1. Check Redis cache first
        2. If NOT cached:
           - Scrape Amazon/Flipkart
           - Get price comparison (if SERPER_API_KEY is set)
           - Get web search (if SERPER_API_KEY is set)
           - Combine results
           - Save to Redis
           - Analyze with LLM
        3. If cached:
           - Get from Redis
           - Analyze with LLM

        Args:
            url: Product URL (Amazon, Flipkart, etc.)

        Returns:
            Dictionary with 'structured_data' and 'analysis'

        Raises:
            ValueError: If URL is invalid or workflow not available
            Exception: If processing fails
        """
        # Validate URL with factory (supports multiple platforms)
        if not ScraperFactory.is_url_supported(url):
            supported = ScraperFactory.get_supported_platforms()
            raise ValueError(f"Invalid URL. Supported platforms: {', '.join(supported)}")

        # Run LangGraph workflow (includes analysis now)
        # Price comparison and web search are automatically enabled if SERPER_API_KEY is set
        result = self.workflow_orchestrator.run(url=url)

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
