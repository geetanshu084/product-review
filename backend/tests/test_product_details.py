#!/usr/bin/env python
"""
Test script to verify comprehensive product data scraping
"""

import json
from src.scrapers import ScraperFactory

def test_product_details():
    """Test comprehensive product details scraping"""

    print("=" * 60)
    print("Testing Comprehensive Product Data Scraping")
    print("=" * 60)

    # Test URL
    test_url = "https://www.amazon.in/Native-Purifier-RO-Copper-Alkaline/dp/B0D7HG2GZD/ref=cm_cr_arp_d_product_top?ie=UTF8&th=1"
    print(f"\nTest URL: {test_url}\n")

    # Scrape product
    print("Scraping product data...")
    scraper = ScraperFactory.get_scraper(test_url)

    try:
        product_data = scraper.scrape_product(test_url)

        print("\n" + "=" * 60)
        print("COMPREHENSIVE PRODUCT DATA")
        print("=" * 60)

        # Basic info
        print("\n--- BASIC INFORMATION ---")
        print(f"ASIN: {product_data.get('asin')}")
        print(f"Title: {product_data.get('title')[:80]}...")
        print(f"Brand: {product_data.get('brand')}")
        print(f"Category: {product_data.get('category')}")
        print(f"Price: {product_data.get('price')}")
        print(f"Rating: {product_data.get('rating')}")
        print(f"Total Reviews: {product_data.get('total_reviews')}")
        print(f"Availability: {product_data.get('availability')}")

        # Specifications
        specs = product_data.get('specifications', {})
        if specs:
            print(f"\n--- SPECIFICATIONS ({len(specs)} found) ---")
            for key, value in list(specs.items())[:5]:  # Show first 5
                print(f"{key}: {value}")
            if len(specs) > 5:
                print(f"... and {len(specs) - 5} more")
        else:
            print("\n--- SPECIFICATIONS ---")
            print("No specifications found")

        # Product details
        details = product_data.get('product_details', {})
        if details:
            print(f"\n--- PRODUCT DETAILS ({len(details)} found) ---")
            for key, value in list(details.items())[:5]:  # Show first 5
                print(f"{key}: {value}")
            if len(details) > 5:
                print(f"... and {len(details) - 5} more")
        else:
            print("\n--- PRODUCT DETAILS ---")
            print("No product details found")

        # Technical details
        tech_details = product_data.get('technical_details', {})
        if tech_details:
            print(f"\n--- TECHNICAL DETAILS ({len(tech_details)} found) ---")
            for key, value in list(tech_details.items())[:5]:  # Show first 5
                print(f"{key}: {value}")
            if len(tech_details) > 5:
                print(f"... and {len(tech_details) - 5} more")
        else:
            print("\n--- TECHNICAL DETAILS ---")
            print("No technical details found")

        # Additional information
        add_info = product_data.get('additional_information', {})
        if add_info:
            print(f"\n--- ADDITIONAL INFORMATION ({len(add_info)} found) ---")
            for key, value in list(add_info.items())[:5]:  # Show first 5
                print(f"{key}: {value}")
            if len(add_info) > 5:
                print(f"... and {len(add_info) - 5} more")
        else:
            print("\n--- ADDITIONAL INFORMATION ---")
            print("No additional information found")

        # Warranty
        warranty = product_data.get('warranty', '')
        print(f"\n--- WARRANTY ---")
        print(f"{warranty[:200]}..." if len(warranty) > 200 else warranty)

        # Images
        images = product_data.get('images', [])
        print(f"\n--- IMAGES ({len(images)} found) ---")
        for i, img_url in enumerate(images[:3], 1):
            print(f"{i}. {img_url[:60]}...")

        # Reviews
        reviews = product_data.get('reviews', [])
        print(f"\n--- REVIEWS ({len(reviews)} scraped) ---")

        # Save to JSON for inspection
        output_file = "/Users/geetanshu/vibegf/product-review/test_product_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Full product data saved to: {output_file}")
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)

        # Check for dimensions specifically
        all_keys = set()
        for d in [specs, details, tech_details, add_info]:
            all_keys.update(d.keys())

        dimension_keys = [k for k in all_keys if 'dimension' in k.lower() or 'size' in k.lower() or 'weight' in k.lower()]
        if dimension_keys:
            print(f"\n📐 Found dimension-related fields: {dimension_keys}")
        else:
            print("\n⚠️ No dimension fields found in scraped data")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_product_details()
