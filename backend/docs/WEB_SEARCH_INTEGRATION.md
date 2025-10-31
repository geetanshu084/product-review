# Web Search Integration for External Reviews

## Overview
Uses Serper API and Gemini LLM to analyze external product reviews, comparisons, discussions, and news from across the web. Automatically filters out results from the source platform (Amazon/Flipkart) and uses AI to remove irrelevant content.

## Features Implemented

### 1. Web Search Analyzer (`src/analysis/web_search.py`)
Complete analyzer for finding and processing external product information.

**Search Types:**
- **Professional Reviews**: Tech blogs, review sites, expert opinions
- **Comparisons**: "Product vs alternatives" articles
- **Issues & Problems**: Complaints, defects, common issues
- **Reddit Discussions**: Community opinions and experiences
- **News Articles**: Latest news, updates, and announcements about the product
- **YouTube Videos**: Video reviews automatically detected

**AI-Powered Features:**
- **Source Platform Filtering**: Automatically excludes results from Amazon/Flipkart (the platform being analyzed)
- **Relevance Filtering**: LLM filters out irrelevant content (different products, unrelated articles)
- **Key Findings**: Gemini summarizes 5-10 important points from all sources
- **Red Flag Detection**: Identifies recalls, defects, scams, or safety concerns
- **Sentiment Analysis**: Overall sentiment (positive/negative/mixed) from external sources

### 2. Integration with LangGraph Workflow
Web search is integrated into the workflow orchestrator:
- Runs in parallel with price comparison after product scraping
- Automatically receives source platform (Amazon/Flipkart) to filter out
- Results combined with product data before LLM analysis
- Cached in Redis along with product data (24-hour TTL)

```python
# Web search enabled automatically if SERPER_API_KEY exists in .env
# Runs as part of unified workflow via /api/v1/products/scrape-and-analyze endpoint
```

### 3. Data Storage
Web search data is automatically added to `product_data` and saved to Redis:

```python
product_data['web_search_analysis'] = {
    'external_reviews': [...],      # Filtered by LLM for relevance
    'comparison_articles': [...],   # Filtered by LLM for relevance
    'issue_discussions': [...],     # Raw issue discussions
    'reddit_discussions': [...],    # Filtered by LLM for relevance
    'news_articles': [...],         # Filtered by LLM for relevance
    'video_reviews': [...],         # YouTube videos
    'key_findings': [...],          # LLM-generated insights
    'red_flags': [...],             # LLM-detected warnings
    'overall_sentiment': {...},     # LLM sentiment analysis
    'total_sources': 40,
    'metadata': {...}
}
```

**Note:** Source platform URLs (e.g., Amazon.in, Flipkart.com) are automatically excluded from all sections.

## Technical Implementation

### API Endpoints Used

**Serper Search API:**
```
POST https://google.serper.dev/search
Headers:
  X-API-KEY: <serper_api_key>
  Content-Type: application/json
Body:
  {
    "q": "iPhone 15 Pro review",
    "location": "India",
    "num": 10
  }
```

### Search Queries Per Product

For each product, 5 different queries are executed:

1. `"{product_name} review"` - Professional reviews
2. `"{product_name} vs alternatives comparison"` - Comparison articles
3. `"{product_name} problems issues complaints"` - Problem discussions
4. `"{product_name} worth it reddit"` - Reddit discussions
5. `"{product_name} news"` - Latest news articles

Total: **~50 search results** per product (10 per query)

**Filtering Pipeline:**
1. Source platform URLs filtered out (e.g., Amazon.in if analyzing Amazon product)
2. LLM filters irrelevant content (different products, unrelated articles)
3. Final results typically reduced to 10-20 highly relevant sources

### LLM Processing

**Key Findings Extraction:**
```
Analyzes top 20 results → Gemini generates 5-10 key points
Focus: reputation, praises, complaints, value, reliability
```

**Red Flag Detection:**
```
Looks for: recalls, defects, scams, failures, security issues
Returns: List of serious warnings or empty if none found
```

**Sentiment Analysis:**
```
Analyzes all results → Returns: positive/negative/mixed
```


### In Web UI (React Frontend)

Web search runs automatically as part of the unified workflow:

1. User enters product URL (Amazon/Flipkart)
2. Workflow orchestrator executes in parallel:
   - Product scraping
   - Price comparison (parallel with web search)
   - **Web search analysis** (parallel with price comparison)
3. Results combined and saved to Redis (24-hour TTL)
4. LLM analysis runs on combined data
5. Results displayed in UI across multiple tabs:
   - **External tab**: Reviews, comparisons, news, Reddit discussions
   - **Summary tab**: Key findings, red flags, sentiment analysis

**API Endpoint:** `POST /api/v1/products/scrape-and-analyze`

## Data Flow (LangGraph Workflow)

```
┌─────────────────┐
│  Check Cache    │
│ (Redis Lookup)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Scrape Product  │
│ (Amazon/Flipkart│
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│ Price Comparison│  │  Web Search     │◄─── 5 Search Queries
│  (Serper API)   │  │   Analysis      │◄─── Platform Filtering
└────────┬────────┘  └────────┬────────┘◄─── LLM Filtering
         │                  │                ◄─── Gemini LLM
         │                  │
         └──────────┬───────┘
                    ▼
         ┌─────────────────┐
         │ Combine Results │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Save to Redis  │
         │ product:{id}    │◄─── 24h TTL
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  LLM Analysis   │◄─── Gemini LLM
         │ & Cache Result  │◄─── 24h TTL
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Return to UI   │
         └─────────────────┘
```

**Parallel Execution:** Price comparison and web search run simultaneously after scraping.


## Testing

### Run Test Suite

```bash
cd /path/to/product-review
python tests/test_web_search_integration.py
```

### Test Coverage

1. **WebSearchAnalyzer Tests:**
   - Individual search methods (reviews, comparisons, issues, reddit)
   - Comprehensive analysis
   - LLM summarization
   - Red flag detection
   - Sentiment analysis

2. **Integration Tests:**
   - ProductAnalyzer integration
   - get_web_search_analysis() method
   - Full analysis flow

### Expected Output

```
Web Search Integration Test Suite
================================================================================
Testing Web Search Analyzer
================================================================================

📦 Initializing Web Search Analyzer...
✓ Web Search Analyzer initialized

🔍 Testing with product: Apple iPhone 15 Pro

--- Testing Individual Search Methods ---

1. Testing search_external_reviews()...
✓ Found 10 review results
  Example: iPhone 15 Pro review: the best of the best...

2. Testing search_comparisons()...
✓ Found 9 comparison results
  Example: iPhone 15 Pro vs Samsung Galaxy S24 Ultra...

3. Testing search_issues()...
✓ Found 10 issue results
  Example: iPhone 15 Pro overheating: what you need to know...

4. Testing search_reddit_discussions()...
✓ Found 9 reddit results
  Example: Is the iPhone 15 Pro worth upgrading to? : r/iphone...

--- Testing Comprehensive Analysis ---

🤖 Running full analysis (this may take 30-60 seconds)...

✅ Analysis Complete!

Results Summary:
  📝 External Reviews: 10
  🔄 Comparison Articles: 9
  ⚠️  Issue Discussions: 10
  💬 Reddit Discussions: 9
  🎥 Video Reviews: 4
  📊 Total Sources: 38

📌 Key Findings (5):
  1. Camera system praised for exceptional low-light performance and versatility
  2. Titanium build feels premium but shows fingerprints easily
  3. A17 Pro chip delivers excellent gaming performance
  4. Battery life criticized for heavy usage scenarios
  5. USB-C port is a welcome change from Lightning

⚠️  Red Flags (2):
  1. Overheating reported during intensive tasks like gaming
  2. Some units have display tinting issues

💭 Overall Sentiment: MIXED

🎥 Video Reviews:
  - iPhone 15 Pro Review: The Best iPhone Ever?
    https://youtube.com/...
  - iPhone 15 Pro vs 14 Pro: Should You Upgrade?
    https://youtube.com/...

================================================================================
Testing ProductAnalyzer Integration
================================================================================

📦 Initializing ProductAnalyzer with web search...
✓ ProductAnalyzer initialized
✓ Web search analyzer is enabled

🔍 Testing get_web_search_analysis()...
✓ Web search analysis returned data
  Total sources: 38
  Key findings: 5

================================================================================
Test Summary
================================================================================
WebSearchAnalyzer Test: ✅ PASSED
ProductAnalyzer Integration: ✅ PASSED

🎉 All tests passed!
```

## API Costs

### Serper API
- **Free tier**: 2,500 searches/month
- **Usage per product**: 5 searches (reviews, comparisons, issues, reddit, news)
- **Capacity**: ~500 products/month on free tier
- **Upgrade**: $50/month for 10,000 searches
- **Note**: Results cached in Redis for 24 hours - subsequent requests use cache

### Gemini API
- **Free tier**: 60 requests/minute
- **Usage per product**: ~7-8 requests
  - 4 relevance filtering calls (reviews, comparisons, reddit, news)
  - 3 insight generation calls (key findings, red flags, sentiment)
- **Capacity**: Unlimited on free tier (rate limited)
- **Note**: Analysis results cached in Redis for 24 hours

## Configuration

### Environment Variables

Add to `.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key
SERPER_API_KEY=your_serper_api_key
```

## Performance

### Timing (First Request)
- **Web Search API calls**: ~3-5 seconds (5 queries)
- **Source Platform Filtering**: <1 second
- **LLM Relevance Filtering**: ~5-8 seconds (4 filtering calls)
- **LLM Insight Generation**: ~5-10 seconds (3 generation calls)
- **Total**: ~15-25 seconds per product

### Timing (Cached Request)
- **Cache Lookup**: <100ms
- **Total**: <1 second (from Redis cache)

### Optimization Tips
1. **Automatic Caching**: Results cached in Redis for 24 hours
2. **Parallel Execution**: Runs in parallel with price comparison
3. **Smart Filtering**: LLM removes irrelevant content before analysis
4. **Disable if not needed**: Set `include_web_search=False` in API request

## Benefits

### For Buyers
- **Comprehensive View**: See what experts and users say beyond the source platform
- **Red Flag Detection**: Avoid products with known issues
- **Real Opinions**: Reddit discussions provide honest feedback
- **Latest News**: Stay updated with product announcements and updates
- **Video Reviews**: Visual demonstrations from YouTube
- **Clean Results**: Only relevant content (irrelevant articles filtered out by AI)

### For Analysis Quality
- **External Validation**: Verify platform reviews with independent sources
- **Sentiment Cross-Check**: Compare platform sentiment with external sentiment
- **Issue Discovery**: Find problems not mentioned in platform reviews
- **Competitive Context**: See how product compares to alternatives
- **Multi-Platform Support**: Works with Amazon, Flipkart, and other e-commerce platforms
- **Source Independence**: Automatically excludes results from the platform being analyzed

## Limitations

1. **Search Quality**: Depends on Serper API and Google's index
2. **Rate Limits**: Free tier limits (2,500 searches/month, ~500 products)
3. **Response Time**: Adds 15-25 seconds to first request (cached requests <1s)
4. **LLM Accuracy**: Relevance filtering may occasionally remove useful content
5. **Language**: Primarily English results
6. **Platform Coverage**: Some e-commerce platforms may not be recognized for filtering

## Current Implementation Status

**Implemented:**
- ✅ Source platform filtering (Amazon, Flipkart, etc.)
- ✅ LLM-powered relevance filtering
- ✅ News articles search
- ✅ Reddit subreddit extraction
- ✅ 24-hour Redis caching (data + analysis)
- ✅ Parallel execution with price comparison
- ✅ LangGraph workflow integration

**Future Enhancements:**
- Multi-language support (search in local languages)
- Custom date range filters
- Advanced NLP (extract specific features mentioned across sources)
- Trend analysis (track sentiment changes over time)
- Video review transcription and analysis

## Troubleshooting

### No Results Found
**Issue**: `total_sources: 0`
**Solutions**:
- Check SERPER_API_KEY is valid
- Verify product name is clear (avoid special characters)
- Check API quota hasn't been exceeded

### LLM Errors
**Issue**: "Failed to generate summary"
**Solutions**:
- Check GOOGLE_API_KEY is valid
- Verify Gemini API quota
- Check network connectivity

### Slow Performance
**Issue**: Takes >30 seconds
**Solutions**:
- Reduce `num_results` parameter (default: 10)
- Disable if not needed for specific analysis
- Check network speed

### Red Flags Not Detected
**Issue**: Known issues not appearing
**Solutions**:
- LLM may be conservative - check `issue_discussions` manually
- Not all issues trigger "red flag" status
- Some issues may be too minor to report

## References

- **Serper API Docs**: https://serper.dev/docs
- **Gemini API Docs**: https://ai.google.dev/docs
- **Requirements**: See req2.md for original specifications
