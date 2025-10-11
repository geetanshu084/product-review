# Price Comparison Feature

## Overview
The price comparison feature allows you to compare product prices across multiple e-commerce platforms (Amazon, Flipkart, eBay, Walmart, etc.) using the Serper API.

## Setup

### 1. Get Serper API Key
1. Visit [https://serper.dev/](https://serper.dev/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes 2,500 free searches

### 2. Configure API Key
Add your Serper API key to the `.env` file:

```bash
SERPER_API_KEY=your_serper_api_key_here
```

## Features

### Multi-Platform Price Comparison
- **Supported Platforms**: Amazon, Flipkart, eBay, Walmart, Myntra, Snapdeal, Croma, Tata, and others
- **Automatic Best Deal Detection**: Finds the lowest price with good ratings
- **Price Statistics**: Min, max, average, and median prices
- **Savings Calculation**: Shows potential savings compared to highest price

### Data Extracted
For each product result:
- Product price (with currency)
- Seller name
- Delivery information
- Product rating
- Number of reviews
- Product URL

## Usage

### Programmatic Usage

```python
from src.price_comparison import SerperPriceComparison

# Initialize
comparer = SerperPriceComparison(api_key="your_api_key")

# Compare prices
results = comparer.compare_prices(
    product_name="iPhone 15 Pro 256GB",
    location="India",
    num_results=20
)

# Access results
best_deal = results['best_deal']
price_stats = results['price_stats']
platforms = results['price_comparison']
```

### Streamlit UI
When analyzing a product in the Streamlit app, price comparison results are automatically displayed:
- Best deal highlight with savings
- Price range statistics
- Platform-wise breakdown with links

## API Response Structure

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
        ...
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
        'currency': str,
        'url': str,
        'seller': str,
        'rating': float,
        'savings': float,
        'savings_percent': float
    },
    'total_results': int
}
```

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

To disable price comparison:

1. **In code**:
   ```python
   analyzer = ProductAnalyzer(
       google_api_key=key,
       enable_price_comparison=False
   )
   ```

2. **Without API key**: Simply don't set `SERPER_API_KEY` in `.env`

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

## Cost Optimization

- Free tier: 2,500 searches/month
- Each product analysis = 1 search
- Cache results when possible
- Use generic product names for better matches
