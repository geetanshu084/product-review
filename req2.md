# Phase 2 Requirements: Enhanced Amazon Product Analysis Agent

## Overview
Phase 1 is complete with basic scraping and analysis. Phase 2 adds advanced scraping capabilities, price comparison using Serper API, sentiment analysis, web search integration, and database caching.

---

## New Features to Implement
### Web Search Integration for External Reviews
**Goal:** Find product reviews, comparisons, and mentions from external sources using Serper API

**Requirements:**
- Use Serper API for web search (not just shopping)
- Search for:
  - Professional reviews (tech blogs, review sites)
  - YouTube video reviews
  - Reddit/forum discussions
  - Comparison articles
  - Recall notices or safety concerns
- Search queries to use:
  - "[Product Name] review"
  - "[Product Name] vs alternatives"
  - "[Product Name] problems issues"
  - "[Product Name] worth it reddit"
- Fetch and summarize top 5-10 results
- Use Gemini to summarize external content
- Identify any red flags or warnings
- Do this with Price_comparison after scrapping amazon data.
- Save this data also in redis with product json.
- 
**Technical Implementation:**
- Use Serper API search endpoint (not shopping)
- Create: `src/analysis/web_search.py`
- Endpoint: POST https://google.serper.dev/search
- Request format:
```python
payload = {
    "q": f"{product_name} review",
    "location": "India",
    "num": 10
}
```

**Serper Search Response Structure:**
```json
{
  "organic": [
    {
      "position": 1,
      "title": "Review Title",
      "link": "https://...",
      "snippet": "Preview text...",
      "date": "3 days ago"
    }
  ]
}
```

**Methods to Implement:**
```python
class WebSearchAnalyzer:
    def __init__(self, serper_api_key: str, gemini_api_key: str)
    def search_external_reviews(self, product_name: str) -> Dict
    def search_comparisons(self, product_name: str) -> Dict
    def search_issues(self, product_name: str) -> Dict
    def summarize_with_llm(self, search_results: List) -> str
    def detect_red_flags(self, search_results: List) -> List[str]
```

**Output Structure:**
```python
{
    'external_reviews': [
        {
            'source': str,  # Website name
            'url': str,
            'title': str,
            'snippet': str,
            'date': str,
            'summary': str  # LLM-generated summary
        },
        ...
    ],
    'comparison_articles': [
        {
            'title': str,
            'url': str,
            'snippet': str,
            'summary': str
        },
        ...
    ],
    'key_findings': List[str],  # Important points from all sources
    'red_flags': List[str],  # Any warnings, recalls, or major issues
    'overall_sentiment': str,  # positive/negative/mixed based on external sources
    'video_reviews': [  # YouTube reviews if found
        {
            'title': str,
            'url': str,
            'channel': str
        }
    ]
}
```

---