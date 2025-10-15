"""
Pydantic schemas for request/response validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl


# Base Models
class Review(BaseModel):
    """Review model"""
    rating: str
    title: str
    text: str
    date: str
    verified_purchase: bool
    helpful_votes: Optional[int] = None


class BankOffer(BaseModel):
    """Bank offer model"""
    bank: str
    offer_type: str  # e.g., 'Cashback', 'EMI', 'Discount', 'Exchange'
    description: str
    terms: Optional[str] = None


class CompetitorPrice(BaseModel):
    """Competitor price model"""
    site: str
    price: str
    url: str
    availability: str


class PriceComparison(BaseModel):
    """Price comparison model"""
    current_price: str
    alternative_prices: List[Dict[str, str]] = []


class WebSearchAnalysis(BaseModel):
    """Web search analysis model"""
    external_reviews: List[Dict[str, str]] = []
    comparison_articles: List[Dict[str, str]] = []
    issue_discussions: List[Dict[str, str]] = []
    reddit_discussions: List[Dict[str, str]] = []
    video_reviews: List[Dict[str, str]] = []
    key_findings: List[str] = []
    red_flags: List[str] = []
    overall_sentiment: Optional[Dict[str, str]] = None


class ProductData(BaseModel):
    """Product data model"""
    asin: str
    title: str
    brand: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[str] = None
    ratings_count: Optional[str] = None
    features: List[str] = []
    description: Optional[str] = None
    specifications: Optional[Dict[str, str]] = None
    images: List[str] = []
    reviews: List[Review] = []
    bank_offers: List[BankOffer] = []
    competitor_prices: List[CompetitorPrice] = []
    price_comparison: Optional[PriceComparison] = None
    web_search_analysis: Optional[WebSearchAnalysis] = None


# Request Models
class ScrapeRequest(BaseModel):
    """Request to scrape a product"""
    url: HttpUrl
    session_id: Optional[str] = None


class AnalyzeRequest(BaseModel):
    """Request to analyze a product"""
    asin: str
    include_price_comparison: bool = True
    include_web_search: bool = True


class ChatRequest(BaseModel):
    """Request to ask a question"""
    session_id: str
    product_id: str  # ASIN
    question: str


class ClearChatRequest(BaseModel):
    """Request to clear chat history"""
    session_id: str


# Response Models
class ScrapeResponse(BaseModel):
    """Response from scraping"""
    success: bool
    message: str
    data: Optional[ProductData] = None


class AnalysisResponse(BaseModel):
    """Response from analysis"""
    success: bool
    message: str
    analysis: str
    product_data: Optional[ProductData] = None


class ChatResponse(BaseModel):
    """Response from chat"""
    success: bool
    message: str
    answer: str


class ChatMessage(BaseModel):
    """Chat message"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatHistoryResponse(BaseModel):
    """Response with chat history"""
    success: bool
    message: str
    history: List[ChatMessage] = []


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
