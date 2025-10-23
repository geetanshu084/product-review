"""
Product routes - scraping and analysis endpoints
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import (
    ScrapeRequest,
    AnalyzeRequest,
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


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_product(request: AnalyzeRequest):
    """
    NEW: Analyze product using ONLY cached data (no re-scraping)

    If product data is already in Redis cache (from /scrape):
    - Skip Amazon scraping
    - Skip price comparison
    - Skip web search
    - Directly run LLM analysis on cached data

    If NOT in cache, returns 404 (user should call /scrape first)

    Args:
        request: AnalyzeRequest with ASIN

    Returns:
        AnalysisResponse with analysis based on cached data
    """
    try:
        # Get product data from cache
        product_data = product_service.get_product_from_cache(request.asin)

        if not product_data:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ASIN {request.asin} not found in cache. Please call /scrape endpoint first to collect product data."
            )

        # Check if cached data has all requested components
        has_price = "price_comparison" in product_data or "competitor_prices" in product_data
        has_web_search = "web_search_analysis" in product_data

        # Warn if missing requested data
        warnings = []
        if request.include_price_comparison and not has_price:
            warnings.append("Price comparison data not in cache. Re-scrape with include_price_comparison=true.")
        if request.include_web_search and not has_web_search:
            warnings.append("Web search data not in cache. Re-scrape with include_web_search=true.")

        # Use orchestrator to analyze cached product
        if not product_service.orchestrator:
            raise ValueError("Orchestrator not available. Check GOOGLE_API_KEY.")

        print(f"\n📊 Analyzing cached data for ASIN: {request.asin}")
        if warnings:
            for warning in warnings:
                print(f"  ⚠ {warning}")

        # Run analysis on cached data
        result = product_service.orchestrator.process_product_sync(
            amazon_raw_data=product_data,
            competitor_data=product_data.get('price_comparison'),
            external_reviews=product_data.get('web_search_analysis')
        )

        structured_data = result.get('structured_data', product_data)
        analysis = result.get('analysis', '')

        message = "Product analyzed successfully using cached data"
        if warnings:
            message += f" (Warnings: {'; '.join(warnings)})"

        return AnalysisResponse(
            success=True,
            message=message,
            analysis=analysis,
            product_data=ProductData(**structured_data) if structured_data else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


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
