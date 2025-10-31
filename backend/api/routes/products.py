"""
Product routes - scraping and analysis endpoints
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import (
    ScrapeRequest,
    AnalysisResponse,
    ProductData,
)
from api.services.product_service import product_service

router = APIRouter()


@router.post("/scrape-and-analyze", response_model=AnalysisResponse)
async def scrape_and_analyze_product(request: ScrapeRequest):
    """
    UNIFIED: Complete pipeline with parallel execution + intelligent caching

    This is the recommended endpoint that uses LangGraph for optimal performance:
    1. Check Redis cache for BOTH product data AND analysis
    2. If fully cached: Return immediately (NO LLM calls - fastest!)
    3. If only data cached: Run LLM analysis only
    4. If NOT cached at all:
       - Scrape product page (Amazon/Flipkart)
       - Run in parallel: Price comparison + Web search
       - Combine results and save to Redis (24h TTL)
       - Run LLM analysis and cache it (24h TTL)
    5. Return both structured data and analysis

    Caching Strategy:
    - First call: Full scraping + analysis (~30-60 seconds)
    - Subsequent calls: Instant response from cache (<1 second)
    - Cache keys: product:{asin} and product:{asin}:analysis
    - TTL: 24 hours for both data and analysis

    Args:
        request: ScrapeRequest with product URL and optional flags

    Returns:
        AnalysisResponse with structured data and analysis
    """
    try:
        # Convert HttpUrl to string
        url = str(request.url)

        # Run unified LangGraph workflow (parallel execution + analysis)
        result = product_service.scrape_and_analyze_unified(url=url)

        structured_data = result.get('structured_data', {})
        analysis = result.get('analysis', '')

        return AnalysisResponse(
            success=True,
            message="Product scraped and analyzed successfully (with parallel execution)",
            analysis=analysis,
            product_data=ProductData(**structured_data) if structured_data else None
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


