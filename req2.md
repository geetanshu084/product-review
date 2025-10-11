# Phase 2 Requirements: Enhanced Amazon Product Analysis Agent

## Overview
Phase 1 is complete with basic scraping and analysis. Phase 2 adds advanced scraping capabilities, price comparison using Serper API, sentiment analysis, web search integration, and database caching.

---

## New Features to Implement
Multi-Platform Price Comparison using Serper API
**Goal:** Compare product prices across Amazon, Flipkart, eBay, Walmart and other platforms using Serper API

**Requirements:**
- Use Serper API (serper.dev) for Google Shopping results
- Search for the same/similar product across platforms
- Extract:
  - Product price (with currency)
  - Seller name
  - Delivery information
  - In stock / Out of stock status
  - Product URL
  - Product rating
  - Number of reviews
- Handle product name variations and search strategies
- Identify best deal automatically
- Calculate price difference and potential savings
- Support different countries/locations (default: India)

**Serper API Endpoints to Use:**
- POST https://google.serper.dev/shopping - For shopping results
- POST https://google.serper.dev/search - For general search (if needed)

**Technical Implementation:**
- Install: `requests`
- Create: `src/scrapers/serper_price_comparison.py`
- API Documentation: https://serper.dev/playground
- Request format:
```python
payload = {
    "q": product_name,
    "location": "India",  # or "United States"
    "num": 20  # number of results
}
headers = {
    "X-API-KEY": serper_api_key,
    "Content-Type": "application/json"
}
response = requests.post(
    "https://google.serper.dev/shopping",
    json=payload,
    headers=headers
)
```

**Serper API Response Structure:**
```json
{
  "shopping_results": [
    {
      "position": 1,
      "title": "Product Name",
      "source": "Amazon.in",
      "link": "https://...",
      "price": "₹15,999",
      "extracted_price": 15999,
      "rating": 4.5,
      "reviews": 1234,
      "delivery": "Free delivery",
      "thumbnail": "https://..."
    }
  ],
  "search_parameters": {...}
}
```

**Methods to Implement:**
```python
class SerperPriceComparison:
    def __init__(self, api_key: str)
    def search_shopping(self, product_name: str, location: str = "India", num_results: int = 20) -> Dict
    def compare_prices(self, product_name: str) -> Dict
    def group_by_platform(self, results: List) -> Dict
    def find_best_deal(self, results: List) -> Dict
    def calculate_price_stats(self, results: List) -> Dict  # min, max, avg, median
```

**Output Structure:**
```python
{
    'price_comparison': {
        'amazon': [
            {
                'title': str,
                'price': float,
                'currency': str,
                'url': str,
                'seller': str,
                'rating': float,
                'reviews': int,
                'delivery': str,
                'in_stock': bool
            },
            ...
        ],
        'flipkart': [...],
        'ebay': [...],
        'walmart': [...],
        'others': [...]
    },
    'price_stats': {
        'min_price': float,
        'max_price': float,
        'avg_price': float,
        'median_price': float,
        'total_results': int
    },
    'best_deal': {
        'platform': str,
        'title': str,
        'price': float,
        'url': str,
        'savings': float,  # compared to max price
        'savings_percent': float
    }
}
