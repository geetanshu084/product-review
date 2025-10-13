# Web Search Integration for External Reviews

## Overview
Phase 2 feature that uses Serper API and Gemini LLM to analyze external product reviews, comparisons, and discussions from across the web.

## Features Implemented

### 1. Web Search Analyzer (`src/analysis/web_search.py`)
Complete analyzer for finding and processing external product information.

**Search Types:**
- **Professional Reviews**: Tech blogs, review sites, expert opinions
- **Comparisons**: "Product vs alternatives" articles
- **Issues & Problems**: Complaints, defects, common issues
- **Reddit Discussions**: Community opinions and experiences
- **YouTube Videos**: Video reviews automatically detected

**AI-Powered Analysis:**
- **Key Findings**: Gemini summarizes 5-10 important points from all sources
- **Red Flag Detection**: Identifies recalls, defects, scams, or safety concerns
- **Sentiment Analysis**: Overall sentiment (positive/negative/mixed) from external sources

### 2. Integration with ProductAnalyzer
Added `enable_web_search` flag to ProductAnalyzer:

```python
analyzer = ProductAnalyzer(
    google_api_key="...",
    serper_api_key="...",
    enable_web_search=True  # Enable external search
)
```

### 3. Data Storage
Web search data is automatically added to `product_data` and saved to Redis:

```python
product_data['web_search_analysis'] = {
    'external_reviews': [...],
    'comparison_articles': [...],
    'issue_discussions': [...],
    'reddit_discussions': [...],
    'video_reviews': [...],
    'key_findings': [...],
    'red_flags': [...],
    'overall_sentiment': 'positive|negative|mixed',
    'total_sources': 40,
    'metadata': {...}
}
```

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

For each product, 4 different queries are executed:

1. `"{product_name} review"`
2. `"{product_name} vs alternatives comparison"`
3. `"{product_name} problems issues complaints"`
4. `"{product_name} worth it reddit"`

Total: **~40 search results** per product (10 per query)

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

## Usage

### Basic Usage

```python
from src.analysis.web_search import WebSearchAnalyzer

# Initialize
analyzer = WebSearchAnalyzer(
    serper_api_key="your_key",
    gemini_api_key="your_key"
)

# Analyze product
results = analyzer.analyze_product("Apple iPhone 15 Pro")

print(f"Total sources: {results['total_sources']}")
print(f"Key findings: {results['key_findings']}")
print(f"Red flags: {results['red_flags']}")
print(f"Sentiment: {results['overall_sentiment']}")
```

### With ProductAnalyzer

```python
from src.analyzer import ProductAnalyzer

# Initialize with web search enabled
analyzer = ProductAnalyzer(
    google_api_key="your_key",
    serper_api_key="your_key",
    enable_web_search=True
)

# Analyze product (includes web search automatically)
analysis = analyzer.analyze_product(product_data)

# Web search data is added to product_data
web_data = product_data['web_search_analysis']
```

### In Streamlit App

Web search runs automatically when analyzing a product:

1. User enters Amazon URL
2. Scraper fetches product data
3. Analyzer runs:
   - Price comparison
   - **Web search analysis** (new)
   - LLM analysis
4. Updated data saved to Redis
5. Results displayed in UI

## Data Flow

```
┌─────────────────┐
│  Scrape Amazon  │
│   Product Data  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Price Comparison│
│  (Serper API)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Web Search     │◄─── Serper Search API
│   Analysis      │◄─── Gemini LLM
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Save to Redis  │
│ product:{asin}  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chatbot Q&A    │
│ Access via ASIN │
└─────────────────┘
```

## Output Structure

### Complete Web Search Analysis

```json
{
  "external_reviews": [
    {
      "source": "techradar.com",
      "url": "https://...",
      "title": "iPhone 15 Pro Review",
      "snippet": "Impressive camera, powerful chip...",
      "date": "2 days ago",
      "category": "review"
    }
  ],
  "comparison_articles": [
    {
      "source": "gsmarena.com",
      "url": "https://...",
      "title": "iPhone 15 Pro vs Samsung S24 Ultra",
      "snippet": "Detailed comparison...",
      "date": "1 week ago",
      "category": "comparison"
    }
  ],
  "issue_discussions": [
    {
      "source": "macrumors.com",
      "url": "https://...",
      "title": "iPhone 15 Pro overheating issues",
      "snippet": "Some users report...",
      "date": "3 days ago",
      "category": "issue"
    }
  ],
  "reddit_discussions": [
    {
      "source": "reddit.com",
      "url": "https://...",
      "title": "Is iPhone 15 Pro worth it?",
      "snippet": "Reddit discussion...",
      "date": "5 days ago",
      "category": "reddit"
    }
  ],
  "video_reviews": [
    {
      "title": "iPhone 15 Pro Full Review",
      "url": "https://youtube.com/...",
      "channel": "Marques Brownlee",
      "snippet": "Comprehensive video review..."
    }
  ],
  "key_findings": [
    "Camera system praised for low-light performance",
    "Titanium build feels premium but shows fingerprints",
    "A17 Pro chip delivers excellent gaming performance",
    "Battery life criticized for heavy usage",
    "USB-C port is a welcome change"
  ],
  "red_flags": [
    "Overheating reported during intensive tasks",
    "Some units have display tinting issues"
  ],
  "overall_sentiment": "mixed",
  "total_sources": 38,
  "metadata": {
    "review_count": 10,
    "comparison_count": 9,
    "issue_count": 10,
    "reddit_count": 9,
    "video_count": 4
  }
}
```

## Testing

### Run Test Suite

```bash
cd /path/to/amazon-review
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
- **Usage per product**: 4 searches (4 different queries)
- **Capacity**: ~625 products/month on free tier
- **Upgrade**: $50/month for 10,000 searches

### Gemini API
- **Free tier**: 60 requests/minute
- **Usage per product**: 3 requests (key findings, red flags, sentiment)
- **Capacity**: Unlimited on free tier (rate limited)

## Configuration

### Environment Variables

Add to `.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key
SERPER_API_KEY=your_serper_api_key
```

### Enable/Disable Features

```python
# Enable both price comparison and web search
analyzer = ProductAnalyzer(
    enable_price_comparison=True,
    enable_web_search=True
)

# Disable web search to save API calls
analyzer = ProductAnalyzer(
    enable_price_comparison=True,
    enable_web_search=False
)

# Per-analysis control
analysis = analyzer.analyze_product(
    product_data,
    include_price_comparison=True,
    include_web_search=True
)
```

## Performance

### Timing
- **Web Search API calls**: ~2-3 seconds (4 queries)
- **LLM Processing**: ~10-15 seconds (3 analyses)
- **Total**: ~15-20 seconds per product

### Optimization Tips
1. Enable caching for repeated products
2. Use async processing for multiple products
3. Reduce `num_results` parameter if speed is critical
4. Cache LLM summaries in Redis

## Benefits

### For Buyers
- **Comprehensive View**: See what experts and users say beyond Amazon
- **Red Flag Detection**: Avoid products with known issues
- **Real Opinions**: Reddit discussions provide honest feedback
- **Video Reviews**: Visual demonstrations from YouTube

### For Analysis Quality
- **External Validation**: Verify Amazon reviews with independent sources
- **Sentiment Cross-Check**: Compare Amazon sentiment with external sentiment
- **Issue Discovery**: Find problems not mentioned in Amazon reviews
- **Competitive Context**: See how product compares to alternatives

## Limitations

1. **Search Quality**: Depends on Serper API and Google's index
2. **Rate Limits**: Free tier limits (2,500 searches/month)
3. **Response Time**: Adds 15-20 seconds to analysis
4. **Relevance**: Search results may include outdated or irrelevant content
5. **Language**: Primarily English results

## Future Enhancements

Potential improvements:
- **Multi-language support**: Search in local languages
- **Custom filters**: Date range, specific sites, etc.
- **Result caching**: Cache search results to reduce API calls
- **Parallel processing**: Run searches concurrently
- **Advanced NLP**: Extract specific features mentioned across sources
- **Trend analysis**: Track sentiment changes over time

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
