#!/usr/bin/env python
"""
Test script to verify the complete analysis workflow
Tests scraping + LLM analysis
"""

import os
from dotenv import load_dotenv
from src.scraper import AmazonScraper
from src.analyzer import ProductAnalyzer

# Load environment variables
load_dotenv()

def test_complete_workflow():
    """Test the complete scraping and analysis workflow"""

    print("=" * 60)
    print("Testing Complete Analysis Workflow")
    print("=" * 60)

    # Test URL
    test_url = "https://www.amazon.in/Native-Purifier-RO-Copper-Alkaline/dp/B0D7HG2GZD/ref=cm_cr_arp_d_product_top?ie=UTF8&th=1"
    print(f"\nTest URL: {test_url}\n")

    # Step 1: Check configuration
    print("Step 1: Checking environment configuration...")
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in .env file!")
        print("Please add your Google API key to the .env file")
        return
    print(f"✓ Google API Key found: {google_api_key[:20]}...")

    # Step 2: Scrape product
    print("\nStep 2: Scraping product data...")
    scraper = AmazonScraper()

    try:
        product_data = scraper.scrape_product(test_url)
        print(f"✓ Product scraped successfully")
        print(f"  - Title: {product_data['title'][:60]}...")
        print(f"  - Price: {product_data['price']}")
        print(f"  - Rating: {product_data['rating']}")
        print(f"  - Reviews scraped: {len(product_data['reviews'])}")

        if len(product_data['reviews']) == 0:
            print("❌ No reviews were scraped! Cannot perform analysis.")
            return

    except Exception as e:
        print(f"❌ Scraping failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Analyze with LLM
    print("\nStep 3: Analyzing product with LLM...")

    try:
        analyzer = ProductAnalyzer()
        print("✓ ProductAnalyzer initialized successfully")

        print("\nCalling LLM for analysis (this may take 10-30 seconds)...")
        analysis = analyzer.analyze_product(product_data)

        print("\n" + "=" * 60)
        print("ANALYSIS RESULT")
        print("=" * 60)
        print(analysis)
        print("\n" + "=" * 60)
        print("✅ Analysis completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_workflow()
