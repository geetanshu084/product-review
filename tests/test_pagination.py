#!/usr/bin/env python3
"""
Test script to verify pagination is working correctly
"""

from src.scraper import AmazonScraper

# Test URL
test_url = "https://www.amazon.in/dp/B0CXN9WCVN"

print("=" * 80)
print("Testing Traditional Scraper with Pagination")
print("=" * 80)

# Test 1: Scrape 30 reviews
print("\n\n### Test 1: Scraping 30 reviews ###\n")
scraper1 = AmazonScraper(max_reviews=30, use_cache=False)
result1 = scraper1.scrape_product(test_url)
print(f"\n✅ Test 1 Complete: Scraped {len(result1['reviews'])} reviews (Target: 30)")

# Test 2: Scrape 50 reviews
print("\n\n### Test 2: Scraping 50 reviews ###\n")
scraper2 = AmazonScraper(max_reviews=50, use_cache=False)
result2 = scraper2.scrape_product(test_url)
print(f"\n✅ Test 2 Complete: Scraped {len(result2['reviews'])} reviews (Target: 50)")

# Test 3: Scrape 100 reviews
print("\n\n### Test 3: Scraping 100 reviews ###\n")
scraper3 = AmazonScraper(max_reviews=100, use_cache=False)
result3 = scraper3.scrape_product(test_url)
print(f"\n✅ Test 3 Complete: Scraped {len(result3['reviews'])} reviews (Target: 100)")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Test 1 (30 reviews): {'✅ PASS' if 25 <= len(result1['reviews']) <= 35 else '❌ FAIL'} - Got {len(result1['reviews'])}")
print(f"Test 2 (50 reviews): {'✅ PASS' if 45 <= len(result2['reviews']) <= 55 else '❌ FAIL'} - Got {len(result2['reviews'])}")
print(f"Test 3 (100 reviews): {'✅ PASS' if 95 <= len(result3['reviews']) <= 105 else '❌ FAIL'} - Got {len(result3['reviews'])}")
print("=" * 80)

# Show sample review data
if result1['reviews']:
    print("\n### Sample Review from Test 1 ###")
    review = result1['reviews'][0]
    print(f"Title: {review.get('title', 'N/A')[:80]}")
    print(f"Rating: {review.get('rating', 'N/A')}")
    print(f"Author: {review.get('author', 'N/A')}")
    print(f"Date: {review.get('date', 'N/A')}")
    print(f"Verified: {review.get('verified', False)}")
    print(f"Text: {review.get('text', 'N/A')[:150]}...")
