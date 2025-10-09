#!/usr/bin/env python3
"""
Test script for advanced Amazon scraper
Tests Selenium-based scraping with enhanced review data extraction
"""

import sys
from src.scrapers import AdvancedAmazonScraper

def test_advanced_scraper():
    """Test the advanced scraper with a real Amazon URL"""

    # Test URL (Amazon India water purifier - commonly used in previous tests)
    test_url = "https://www.amazon.in/dp/B0CXN9WCVN"

    print("=" * 80)
    print("Testing Advanced Amazon Scraper")
    print("=" * 80)
    print(f"\nTest URL: {test_url}")
    print(f"Target: 20 reviews (for quick testing)")
    print("\n" + "-" * 80 + "\n")

    # Initialize scraper with headless mode
    scraper = AdvancedAmazonScraper(headless=True, max_reviews=20)

    try:
        # Scrape reviews
        result = scraper.scrape_reviews(test_url, prioritize_verified=True)

        # Display results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)

        print(f"\nTotal reviews scraped: {result['total_scraped']}")
        print(f"ASIN: {result.get('asin', 'N/A')}")

        if result['reviews']:
            verified_count = sum(1 for r in result['reviews'] if r['verified_purchase'])
            print(f"Verified purchases: {verified_count}/{len(result['reviews'])}")

            # Show first 3 reviews
            print(f"\n{'-' * 80}")
            print("First 3 Reviews:")
            print("-" * 80)

            for i, review in enumerate(result['reviews'][:3], 1):
                print(f"\n--- Review {i} ---")
                print(f"Rating: {'⭐' * review['rating']} ({review['rating']}/5)")
                print(f"Title: {review['title']}")
                print(f"Date: {review['date']}")
                print(f"Verified Purchase: {'✓' if review['verified_purchase'] else '✗'}")
                print(f"Helpful Votes: {review['helpful_votes']}")
                print(f"Reviewer: {review['reviewer_name']}")
                print(f"Text: {review['text'][:150]}...")

            print(f"\n{'=' * 80}")
            print("✅ TEST PASSED - Advanced scraper working correctly!")
            print("=" * 80)

            return True
        else:
            print("\n❌ TEST FAILED - No reviews scraped")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED - Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test the integration with existing AmazonScraper"""
    from src.scraper import AmazonScraper

    test_url = "https://www.amazon.in/dp/B0CXN9WCVN"

    print("\n" + "=" * 80)
    print("Testing Integration with AmazonScraper")
    print("=" * 80)

    try:
        # Initialize with advanced scraper enabled
        scraper = AmazonScraper(
            use_advanced_scraper=True,
            max_reviews=15
        )

        print(f"\nScraping with advanced scraper enabled...")
        result = scraper.scrape_product(test_url)

        print(f"\n✅ Integration test passed!")
        print(f"   Total reviews: {len(result.get('reviews', []))}")
        print(f"   Product: {result.get('title', 'N/A')[:60]}...")

        # Check for enhanced review fields
        if result['reviews']:
            first_review = result['reviews'][0]
            has_date = 'date' in first_review
            has_verified = 'verified_purchase' in first_review
            has_helpful = 'helpful_votes' in first_review

            print(f"\n   Enhanced fields present:")
            print(f"     - Date: {has_date}")
            print(f"     - Verified Purchase: {has_verified}")
            print(f"     - Helpful Votes: {has_helpful}")

        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🧪 Starting Advanced Scraper Tests\n")

    # Test 1: Direct advanced scraper test
    test1_passed = test_advanced_scraper()

    # Test 2: Integration test
    if test1_passed:
        print("\n\n")
        test2_passed = test_integration()
    else:
        print("\n⚠️  Skipping integration test due to direct scraper test failure")
        test2_passed = False

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Direct Scraper Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 80 + "\n")

    sys.exit(0 if (test1_passed and test2_passed) else 1)
