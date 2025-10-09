#!/usr/bin/env python3
"""
Debug pagination issue with specific URL
"""

from src.scraper import AmazonScraper

# The URL that's not working
test_url = "https://www.amazon.in/Native-Purifier-RO-Copper-Alkaline/dp/B0D79G62J3/ref=cm_cr_arp_d_product_top?ie=UTF8"

print("=" * 80)
print("Debugging Pagination Issue")
print("=" * 80)
print(f"\nURL: {test_url}\n")

# Test with small number first
scraper = AmazonScraper(max_reviews=30, use_cache=False)

print("\n🔄 Starting scrape with max_reviews=30...\n")
result = scraper.scrape_product(test_url)

print(f"\n{'=' * 80}")
print(f"RESULT: Scraped {len(result['reviews'])} reviews")
print(f"{'=' * 80}")

if result['reviews']:
    print(f"\nFirst 3 reviews:")
    for i, review in enumerate(result['reviews'][:3], 1):
        print(f"\n--- Review {i} ---")
        print(f"Title: {review.get('title', 'N/A')[:60]}")
        print(f"Rating: {review.get('rating', 'N/A')}")
        print(f"Author: {review.get('author', 'N/A')}")
else:
    print("\n❌ No reviews scraped!")
