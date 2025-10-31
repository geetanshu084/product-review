#!/usr/bin/env python3
"""
Test script to verify scraper is working correctly
NOTE: The new scrapers automatically handle caching and LLM extraction.
"""

from src.scrapers import ScraperFactory

# Test URL
test_url = "https://www.amazon.in/dp/B0CXN9WCVN"

print("=" * 80)
print("Testing Scraper Functionality")
print("=" * 80)

# Test: Scrape product with factory pattern
print("\n\n### Testing with ScraperFactory ###\n")
scraper = ScraperFactory.get_scraper(test_url)
result = scraper.scrape_product(test_url)

print(f"\n✅ Scraping Complete")
print(f"   - Title: {result.get('title', 'N/A')[:60]}...")
print(f"   - Brand: {result.get('brand', 'N/A')}")
print(f"   - Price: {result.get('price', 'N/A')}")
print(f"   - Rating: {result.get('rating', 'N/A')}")
print(f"   - Reviews: {len(result.get('reviews', []))} reviews scraped")

# Show sample review data
if result.get('reviews'):
    print("\n### Sample Review ###")
    review = result['reviews'][0]
    print(f"Title: {review.get('title', 'N/A')[:80]}")
    print(f"Rating: {review.get('rating', 'N/A')}")
    print(f"Author: {review.get('author', 'N/A')}")
    print(f"Date: {review.get('date', 'N/A')}")
    print(f"Verified: {review.get('verified_purchase', False)}")
    print(f"Text: {review.get('text', 'N/A')[:150]}...")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
