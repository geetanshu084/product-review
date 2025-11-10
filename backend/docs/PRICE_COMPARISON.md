# Price Comparison Feature

## Overview
The price comparison feature allows you to compare product prices across multiple e-commerce platforms (Amazon, Flipkart, eBay, Walmart, etc.) using either **DuckDuckGo (free, default)** or **Serper API (Google Shopping)**. It automatically filters out results from the source platform to show only genuine competitor prices.

## Setup

### Choose Your Search Provider

The system supports two search providers:

#### Option A: DuckDuckGo (Default - Free)
- **Cost**: Completely free, no API key required
- **Setup**: Works out of the box, no configuration needed
- **Quality**: Good results from general web search
- **Note**: Results are parsed from regular search (no dedicated shopping API)

Set in `.env`:
```bash
SEARCH_PROVIDER=duckduckgo  # Default, can be omitted
```

#### Option B: Serper (Google Shopping - Recommended for Best Results)
- **Cost**: Free tier includes 2,500 searches/month
- **Setup**: Requires API key from [serper.dev](https://serper.dev/)
- **Quality**: Premium Google Shopping results with structured price data
- **Best For**: Production use with high accuracy needs

1. Visit [https://serper.dev/](https://serper.dev/)
2. Sign up for a free account
3. Get your API key from the dashboard

Set in `.env`:
```bash
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_api_key_here
```

## Features

### Multi-Platform Price Comparison
- **Supported Platforms**: Amazon, Flipkart, eBay, Walmart, Myntra, Snapdeal, Croma, Tata, and others
- **Source Platform Filtering**: Automatically excludes results from the platform being analyzed (e.g., if analyzing an Amazon product, excludes Amazon from competitors)
- **Automatic Best Deal Detection**: Finds the lowest price with good ratings
- **Price Statistics**: Min, max, average, and median prices
- **Savings Calculation**: Shows potential savings compared to highest price

### 🎯 Exact Product Matching (NEW!)
- **Smart Filtering**: Automatically filters results to show only the exact same product
- **Attribute Matching**: Compares brand, model, storage, RAM, and color
- **High Accuracy**: ~70% filtering effectiveness - removes different variants
- **Example**: When searching "iPhone 15 Pro 256GB", it excludes:
  - iPhone 15 (base model)
  - iPhone 15 Plus
  - iPhone 15 Pro Max
  - iPhone 15 Pro 128GB (different storage)
  - Other unrelated products

### Data Extracted
For each product result:
- Product price (with currency)
- Seller name
- Delivery information
- Product rating
- Number of reviews
- Product URL

### Web UI Integration
When analyzing a product in the React web interface, price comparison results are automatically displayed:
- Best deal highlight with potential savings
- Price range statistics (min, max, avg, median)
- Platform-wise breakdown with direct purchase links
- Competitor prices are shown in the Analysis tab
- Source platform results are automatically excluded


## Testing

Run the test script to verify your setup:

```bash
python test_price_comparison.py
```

## Limitations

1. **Rate Limits**: Free tier has 2,500 searches/month
2. **Location-Specific**: Results vary by location (India, US, etc.)
3. **Result Quality**: Depends on Google Shopping data availability
4. **Platform Coverage**: Not all platforms may be available in all regions

## Disabling Price Comparison

To disable price comparison, simply don't set `SERPER_API_KEY` in `.env`. The workflow orchestrator will automatically detect if the API key is missing and skip price comparison during product analysis.

When disabled:
- Price comparison node is skipped in the LangGraph workflow
- Analysis continues with only scraped product data
- No additional API costs are incurred

## Troubleshooting

### No results found
- Check product name spelling
- Try simpler/more generic product names
- Verify API key is correct
- Check API usage limits

### Error: 401 Unauthorized
- API key is invalid or expired
- Check your Serper dashboard for key status

### Low quality results
- Try different search terms
- Change location parameter
- Increase `num_results` parameter

## Integration with LangGraph Workflow

Price comparison is integrated into the LangGraph workflow orchestrator:
1. Runs in parallel with web search after product scraping
2. Automatically passes source platform to exclude from results
3. Results are combined with product data before LLM analysis
4. Cached in Redis along with product data (24-hour TTL)


**Performance:**
- First request: ~10-15 seconds for price comparison (parallel with web search)
- Subsequent requests: <1 second (from Redis cache)

## Cost Optimization

- Free tier: 2,500 searches/month
- Each product analysis = 1 search (if price comparison enabled)
- Results cached in Redis for 24 hours - subsequent requests use cache
- Use generic product names for better matches
- Consider disabling for products with poor price data availability
