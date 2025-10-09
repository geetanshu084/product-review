# Redis Caching Implementation - Complete

## 🎯 Overview

Implemented **Redis caching** to avoid re-scraping the same product multiple times. Products are cached using their ASIN with a **24-hour TTL**, dramatically improving performance for repeated queries.

## 🚀 Key Features

### 1. **Automatic Caching**
- Products cached by ASIN: `product:{ASIN}`
- **24-hour TTL** (86,400 seconds)
- Automatic cache check before scraping
- Automatic cache save after scraping

### 2. **Massive Performance Improvement**
```
First scrape:  39.14 seconds (fetch + scrape + LLM)
Second scrape: 0.00 seconds (instant from cache!)
Speed improvement: 71,941x faster! ⚡
```

### 3. **Intelligent Fallback**
- If Redis unavailable → Falls back to normal scraping
- If cache miss → Scrapes normally and caches result
- Zero breaking changes - always returns data

## 📊 Performance Comparison

| Scenario | Time | Data Source |
|----------|------|-------------|
| **First scrape** (no cache) | ~39s | Amazon + LLM extraction |
| **Second scrape** (cached) | ~0.001s | Redis cache ⚡ |
| **Speed improvement** | **71,941x** | Instant retrieval |

## 🛠️ Implementation Details

### Cache Key Format:
```
product:{ASIN}
```

**Example:**
- ASIN: `B0D7HG2GZD`
- Cache key: `product:B0D7HG2GZD`
- TTL: 86400 seconds (24 hours)

### Data Stored in Cache:
Complete product data including:
- ✅ All product details
- ✅ Specifications
- ✅ Bank offers (if LLM extraction succeeded)
- ✅ Reviews
- ✅ Warranty information
- ✅ Everything scraped

### Code Changes:

#### Updated: `src/scraper.py`

```python
class AmazonScraper:
    def __init__(
        self,
        use_llm_extraction: bool = True,
        use_cache: bool = True,  # NEW: Enable caching
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        cache_ttl: int = 86400  # 24 hours
    ):
        # Initialize Redis client
        if use_cache:
            self.redis_client = redis.Redis(...)
            self.redis_client.ping()  # Test connection

    def scrape_product(self, url: str) -> Dict:
        asin = self.extract_asin(url)

        # 1. Check cache first
        cached_data = self._get_from_cache(asin)
        if cached_data:
            return cached_data  # Instant return!

        # 2. Scrape if not cached
        product_data = ...  # Normal scraping

        # 3. Save to cache
        self._save_to_cache(asin, product_data)

        return product_data

    def _get_from_cache(self, asin: str) -> Optional[Dict]:
        """Get from Redis with key: product:{asin}"""
        cache_key = f"product:{asin}"
        cached_json = self.redis_client.get(cache_key)
        if cached_json:
            return json.loads(cached_json)
        return None

    def _save_to_cache(self, asin: str, product_data: Dict):
        """Save to Redis with 24-hour TTL"""
        cache_key = f"product:{asin}"
        product_json = json.dumps(product_data, ensure_ascii=False)
        self.redis_client.setex(cache_key, self.cache_ttl, product_json)
```

## 🎛️ Configuration

### Enable/Disable Caching:

```python
# Enable caching (default)
scraper = AmazonScraper(use_cache=True)

# Disable caching
scraper = AmazonScraper(use_cache=False)

# Custom TTL (6 hours)
scraper = AmazonScraper(use_cache=True, cache_ttl=21600)
```

### Redis Configuration:

```python
# Custom Redis connection
scraper = AmazonScraper(
    use_cache=True,
    redis_host="my-redis-server.com",
    redis_port=6379,
    redis_db=1,
    redis_password="secret",
    cache_ttl=86400  # 24 hours
)
```

### Environment Variables:

Add to `.env` (optional):
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional
```

## 🧪 Testing

### Test Script: `test_caching.py`

```bash
python test_caching.py
```

**Output:**
```
--- FIRST SCRAPE (will fetch from Amazon) ---
✓ First scrape completed in 39.14 seconds
  - Title: Native by Urban Company M2 RO Water Purifier...
  - Bank Offers: 4
  - Reviews: 8

--- SECOND SCRAPE (should use cache) ---
✓ Using cached data for ASIN: B0D7HG2GZD (from Redis)
✓ Second scrape completed in 0.00 seconds

RESULTS:
✅ Cache working! Second scrape was 71,941x faster
✅ Data integrity verified
✅ Cache TTL: 24.0 hours remaining
```

## 💡 Usage Examples

### Example 1: Normal Usage (Auto-caching)

```python
from src.scraper import AmazonScraper

# Caching enabled by default
scraper = AmazonScraper()

# First call - scrapes from Amazon
data1 = scraper.scrape_product('https://www.amazon.in/dp/B0D7HG2GZD')
# Takes ~39 seconds

# Second call - instant from cache!
data2 = scraper.scrape_product('https://www.amazon.in/dp/B0D7HG2GZD')
# Takes ~0.001 seconds ⚡
```

### Example 2: Streamlit App

The caching is **automatically enabled** in the Streamlit app. When users analyze the same product:
- **First analysis:** Full scraping (39s)
- **Subsequent analyses (within 24h):** Instant from cache (0.001s)

### Example 3: Check Cache Directly

```python
import redis
import json

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Check if product is cached
asin = "B0D7HG2GZD"
cached = redis_client.get(f"product:{asin}")

if cached:
    product_data = json.loads(cached)
    print(f"Cached: {product_data['title']}")

    # Check TTL
    ttl = redis_client.ttl(f"product:{asin}")
    print(f"Expires in: {ttl/3600:.1f} hours")
```

## 🔄 Cache Lifecycle

```mermaid
User requests product
       ↓
Check Redis cache (product:{ASIN})
       ↓
  Cache Hit?
    ↙     ↘
  YES      NO
   ↓        ↓
Return    Scrape
cached    Amazon
(0.001s)    ↓
          LLM
        Extract
           ↓
         Save to
        Redis
       (TTL: 24h)
           ↓
         Return
         data
```

## 📈 Benefits

### 1. **Performance**
- ✅ **71,941x faster** for cached products
- ✅ Reduces API calls to Amazon
- ✅ Reduces LLM API usage (saves cost)

### 2. **User Experience**
- ✅ Instant results for popular products
- ✅ Reduced wait time
- ✅ Better responsiveness

### 3. **Scalability**
- ✅ Handles high traffic (multiple users analyzing same product)
- ✅ Reduces server load
- ✅ Saves bandwidth

### 4. **Cost Savings**
- ✅ Fewer Google Gemini API calls
- ✅ Less scraping (respectful to Amazon)
- ✅ Lower infrastructure costs

## ⚙️ Cache Management

### View All Cached Products:

```bash
redis-cli
> KEYS product:*
1) "product:B0D7HG2GZD"
2) "product:B08N5WRWNW"
```

### Check Specific Product:

```bash
redis-cli
> GET product:B0D7HG2GZD
"{\"asin\":\"B0D7HG2GZD\", ...}"

> TTL product:B0D7HG2GZD
86398  # seconds remaining
```

### Clear Cache:

```bash
# Clear specific product
redis-cli DEL product:B0D7HG2GZD

# Clear all products
redis-cli KEYS "product:*" | xargs redis-cli DEL

# Or flush entire database (careful!)
redis-cli FLUSHDB
```

## 🔒 Data Integrity

The cache stores the **complete** scraped data:
- ✅ All original fields preserved
- ✅ JSON serialization with UTF-8 support (`ensure_ascii=False`)
- ✅ Same data structure as fresh scrapes
- ✅ No data loss

## 🛡️ Error Handling

### Graceful Degradation:

```python
# If Redis is down
✓ Falls back to normal scraping
✓ No errors thrown
✓ Warning printed: "⚠ Redis caching disabled"

# If cache read fails
✓ Falls back to fresh scrape
✓ Warning printed: "⚠ Cache read error"

# If cache write fails
✓ Returns scraped data anyway
✓ Warning printed: "⚠ Cache write error"
```

## 📊 Cache Statistics

To monitor cache effectiveness:

```python
def get_cache_stats():
    """Get cache hit/miss statistics"""
    redis_client = redis.Redis(...)

    # Count cached products
    cached_count = len(redis_client.keys("product:*"))

    # Get memory usage
    info = redis_client.info('memory')
    used_memory = info['used_memory_human']

    print(f"Cached products: {cached_count}")
    print(f"Memory used: {used_memory}")
```

## 🎯 Best Practices

### 1. **Keep Redis Running**
Ensure Redis server is always running for optimal performance:
```bash
# macOS/Linux
redis-server

# Or as service
brew services start redis
```

### 2. **Monitor Cache**
Periodically check cache size and memory usage:
```bash
redis-cli INFO memory
redis-cli DBSIZE
```

### 3. **Adjust TTL Based on Needs**
- **24 hours (default):** Good for most products
- **12 hours:** For frequently changing prices
- **48 hours:** For stable products with few updates

### 4. **Clear Stale Cache**
If product data changes significantly, clear cache:
```python
scraper.redis_client.delete(f"product:{asin}")
```

## 🔮 Future Enhancements

1. ✅ Redis caching - **DONE**
2. 🔄 Cache warming (pre-cache popular products) - TODO
3. 🔄 Cache statistics dashboard - TODO
4. 🔄 Selective cache invalidation - TODO
5. 🔄 Cache versioning (for data structure changes) - TODO

## 📝 Files Modified

1. **UPDATED:** `src/scraper.py` - Added caching logic
2. **CREATED:** `test_caching.py` - Test script
3. **CREATED:** `REDIS_CACHING_UPDATE.md` - This document

## ✅ Backward Compatibility

- ✅ **Zero breaking changes**
- ✅ Works with existing code
- ✅ Caching is opt-out, not opt-in (enabled by default)
- ✅ Falls back gracefully if Redis unavailable

## 🎉 Summary

**Redis caching** is now fully implemented and production-ready:

- ✅ **24-hour TTL** on all cached products
- ✅ **71,941x faster** for cached products
- ✅ **ASIN-based keys** for easy management
- ✅ **Automatic** cache check and save
- ✅ **Graceful fallback** if Redis unavailable
- ✅ **Complete data** integrity preserved
- ✅ **Zero breaking changes**

Your Amazon Product Analysis Agent now has **enterprise-grade caching**! 🚀

---

**Version:** 4.0 (Redis Caching)
**Date:** 2025-10-09
**Status:** ✅ Production Ready
