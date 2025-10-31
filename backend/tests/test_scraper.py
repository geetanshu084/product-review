#!/usr/bin/env python
"""
Test script to verify Amazon scraper functionality
Run this to test if scraping is working correctly
"""

from src.scrapers import ScraperFactory

def test_scraper():
    """Test the scraper with a sample product"""
    # Use a popular product that definitely has reviews
    test_url = "https://www.amazon.in/Native-Purifier-RO-Copper-Alkaline/dp/B0D7HG2GZD/ref=cm_cr_arp_d_product_top?ie=UTF8&th=1"
    scraper = ScraperFactory.get_scraper(test_url)

    print("=" * 60)
    print("Testing Amazon Scraper")
    print("=" * 60)
    print(f"\nTest URL: {test_url}\n")

    # Validate URL
    print("1. Validating URL...")
    if not scraper.validate_url(test_url):
        print("❌ URL validation failed!")
        return
    print("✓ URL is valid")

    # Extract ASIN
    asin = scraper.extract_asin(test_url)
    print(f"✓ ASIN extracted: {asin}")

    # Scrape product
    print("\n2. Scraping product data...")
    try:
        product_data = scraper.scrape_product(test_url)

        print("\n" + "=" * 60)
        print("SCRAPING RESULTS")
        print("=" * 60)
        print(f"\nTitle: {product_data['title']}")
        print(f"Brand: {product_data['brand']}")
        print(f"Price: {product_data['price']}")
        print(f"Rating: {product_data['rating']}")
        print(f"Total Reviews: {product_data['total_reviews']}")
        print(f"Features: {len(product_data['features'])} features found")
        print(f"Seller: {product_data['seller_name']}")
        print(f"\n✓ Reviews Scraped: {len(product_data['reviews'])} reviews")

        if len(product_data['reviews']) > 0:
            print("\nSample review:")
            review = product_data['reviews'][0]
            print(f"  Title: {review['title'][:50]}...")
            print(f"  Rating: {review['rating']}")
            print(f"  Author: {review['author']}")
            print(f"  Verified: {review['verified']}")
            print(f"  Text: {review['text'][:100]}...")
        else:
            print("\n⚠️ WARNING: No reviews were scraped!")
            print("This could mean:")
            print("  - Amazon blocked the request")
            print("  - The product has no reviews")
            print("  - HTML structure has changed")
            print("  - Network/timeout issues")

        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper()
