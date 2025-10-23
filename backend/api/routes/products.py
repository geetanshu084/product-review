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
    UNIFIED: Complete pipeline with parallel execution + LLM analysis

    This is the recommended endpoint that uses LangGraph for optimal performance:
    1. Check Redis cache first
    2. If NOT cached, run in parallel:
       - Scrape Amazon page
       - Search internet for competitive prices
       - Search internet for external reviews/feedback
    3. Combine results and save to Redis (24h cache)
    4. Run LLM analysis on complete data
    5. Return both structured data and analysis

    Subsequent calls with same URL will use cached data (much faster!)

    Args:
        request: ScrapeRequest with Amazon URL and optional flags

    Returns:
        AnalysisResponse with structured data and analysis
    """
    try:
        # Convert HttpUrl to string
        url = str(request.url)

        # Run unified LangGraph workflow (parallel execution + analysis)
        result = product_service.scrape_and_analyze_unified(
            url=url,
            include_price_comparison=request.include_price_comparison,
            include_web_search=request.include_web_search
        )

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


@router.get("/product/{asin}", response_model=ProductData)
async def get_product(asin: str):
    """
    Get product data by ASIN from cache

    Args:
        asin: Product ASIN

    Returns:
        ProductData
    """
    try:
        product_data = product_service.get_product_from_cache(asin)

        if not product_data:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ASIN {asin} not found"
            )

        return ProductData(**product_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
