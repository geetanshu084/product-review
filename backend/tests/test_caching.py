#!/usr/bin/env python
"""
Test script to verify Redis caching functionality
"""

import time
from dotenv import load_dotenv
from src.scrapers import ScraperFactory

load_dotenv()

def test_caching():
    """Test Redis caching with same product"""

    print("=" * 60)
    print("Testing Redis Caching Functionality")
    print("=" * 60)

    test_url = "https://www.amazon.in/Native-Purifier-RO-Copper-Alkaline/dp/B0D7HG2GZD"

    # Initialize scraper (caching and LLM extraction are always enabled)
    scraper = ScraperFactory.get_scraper(test_url)

    print("\n--- FIRST SCRAPE (will fetch from Amazon) ---")
    start = time.time()
    product_data_1 = scraper.scrape_product(test_url)
    time_1 = time.time() - start

    print(f"\n✓ First scrape completed in {time_1:.2f} seconds")
    print(f"  - Title: {product_data_1['title'][:60]}...")
    print(f"  - Bank Offers: {len(product_data_1.get('bank_offers', []))}")
    print(f"  - Reviews: {len(product_data_1.get('reviews', []))}")

    print("\n" + "-" * 60)
    print("Waiting 2 seconds before second scrape...")
    time.sleep(2)

    print("\n--- SECOND SCRAPE (should use cache) ---")
    start = time.time()
    product_data_2 = scraper.scrape_product(test_url)
    time_2 = time.time() - start

    print(f"\n✓ Second scrape completed in {time_2:.2f} seconds")
    print(f"  - Title: {product_data_2['title'][:60]}...")
    print(f"  - Bank Offers: {len(product_data_2.get('bank_offers', []))}")
    print(f"  - Reviews: {len(product_data_2.get('reviews', []))}")

    # Verify data is identical
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if time_2 < 1.0:  # Cached should be nearly instant
        print(f"✅ Cache working! Second scrape was {time_1/time_2:.1f}x faster")
        print(f"   - First scrape:  {time_1:.2f}s")
        print(f"   - Second scrape: {time_2:.2f}s (from cache)")
    else:
        print(f"⚠️  Cache may not be working - second scrape took {time_2:.2f}s")

    # Verify data integrity
    if product_data_1['asin'] == product_data_2['asin']:
        print(f"✅ Data integrity verified - ASIN matches")
    else:
        print(f"❌ Data integrity failed - ASINs don't match!")

    if len(product_data_1.get('bank_offers', [])) == len(product_data_2.get('bank_offers', [])):
        print(f"✅ Bank offers preserved in cache ({len(product_data_1.get('bank_offers', []))} offers)")
    else:
        print(f"⚠️  Bank offers differ between scrapes")

    print("\n" + "=" * 60)
    print("Cache Test Complete!")
    print("=" * 60)

    # Check Redis directly
    try:
        import redis
        import os
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        asin = product_data_1['asin']
        ttl = redis_client.ttl(f"product:{asin}")
        if ttl > 0:
            hours = ttl / 3600
            print(f"\n✓ Cache TTL: {hours:.1f} hours remaining (expires in {ttl}s)")
        else:
            print(f"\n⚠️  No TTL found for cached product")
    except Exception as e:
        print(f"\n⚠️  Could not check Redis TTL: {str(e)}")


if __name__ == "__main__":
    test_caching()
