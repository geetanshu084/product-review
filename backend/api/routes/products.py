"""
Product routes - scraping and analysis endpoints
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import (
    ScrapeRequest,
    AnalyzeRequest,
    ScrapeResponse,
    AnalysisResponse,
    ProductData,
)
from api.services.product_service import product_service

router = APIRouter()


@router.post("/scrape-and-analyze", response_model=AnalysisResponse)
async def scrape_and_analyze_product(request: ScrapeRequest):
    """
    Complete pipeline: Scrape → Search Competitors → Search Reviews → Structure → Analyze

    This is the recommended endpoint that follows the complete flow:
    1. Scrape Amazon page
    2. Search internet for competitive prices
    3. Search internet for external reviews/feedback
    4. Send all data to LLM for structured extraction
    5. Save structured data to Redis
    6. Send to LLM for analysis
    7. Return both structured data and analysis

    Args:
        request: ScrapeRequest with Amazon URL

    Returns:
        AnalysisResponse with structured data and analysis
    """
    try:
        # Convert HttpUrl to string
        url = str(request.url)

        # Run complete pipeline
        result = product_service.scrape_and_analyze(
            url=url,
            include_price_comparison=True,
            include_web_search=True
        )

        structured_data = result.get('structured_data', {})
        analysis = result.get('analysis', '')

        return AnalysisResponse(
            success=True,
            message="Product scraped and analyzed successfully",
            analysis=analysis,
            product_data=ProductData(**structured_data) if structured_data else None
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_product(request: ScrapeRequest):
    """
    Scrape product data from Amazon URL

    Args:
        request: ScrapeRequest with Amazon URL

    Returns:
        ScrapeResponse with product data
    """
    try:
        # Convert HttpUrl to string
        url = str(request.url)

        # Scrape product
        product_data = product_service.scrape_product(url)

        return ScrapeResponse(
            success=True,
            message="Product scraped successfully",
            data=ProductData(**product_data)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_product(request: AnalyzeRequest):
    """
    Analyze already-scraped product using LLM

    NOTE: This endpoint is for legacy compatibility.
    For new requests, use /scrape-and-analyze which runs the complete pipeline.

    Args:
        request: AnalyzeRequest with ASIN and options

    Returns:
        AnalysisResponse with analysis and updated product data
    """
    try:
        # Get product data from cache
        product_data = product_service.get_product_from_cache(request.asin)

        if not product_data:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ASIN {request.asin} not found in cache. Please scrape first or use /scrape-and-analyze endpoint."
            )

        # Use orchestrator to analyze cached product
        if not product_service.orchestrator:
            raise ValueError("Orchestrator not available. Check GOOGLE_API_KEY.")

        # Run analysis on cached data
        result = product_service.orchestrator.process_product_sync(
            amazon_raw_data=product_data,
            competitor_data=product_data.get('price_comparison'),
            external_reviews=product_data.get('web_search_analysis')
        )

        structured_data = result.get('structured_data', product_data)
        analysis = result.get('analysis', '')

        return AnalysisResponse(
            success=True,
            message="Product analyzed successfully",
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
