#!/usr/bin/env python3
"""
Test price comparison functionality
"""

import os
from dotenv import load_dotenv
from src.price_comparison import SerperPriceComparison

# Load environment variables
load_dotenv()

# Check for API key
serper_api_key = os.getenv("SERPER_API_KEY")

if not serper_api_key:
    print("❌ SERPER_API_KEY not found in .env file")
    print("Please add your Serper API key to .env file:")
    print("SERPER_API_KEY=your_api_key_here")
    print("\nGet your API key from: https://serper.dev/")
    exit(1)

# Test product search
product_name = "iPhone 15 Pro 256GB"
print(f"🧪 Testing price comparison for: {product_name}")
print("="*60)

# Initialize comparer
comparer = SerperPriceComparison(serper_api_key)

# Compare prices
results = comparer.compare_prices(product_name, "amazon")

# Display results
print("\n" + "="*60)
print("RESULTS")
print("="*60)

if results.get('error'):
    print(f"❌ Error: {results['error']}")
else:
    print(f"\n✅ Total results found: {results['total_results']}")

    # Price statistics
    stats = results['price_stats']
    print(f"\n📊 Price Statistics:")
    print(f"   Min:    ₹{stats['min_price']:.2f}")
    print(f"   Max:    ₹{stats['max_price']:.2f}")
    print(f"   Avg:    ₹{stats['avg_price']:.2f}")
    print(f"   Median: ₹{stats['median_price']:.2f}")

    # Best deal
    best_deal = results['best_deal']
    if best_deal:
        print(f"\n🏆 Best Deal:")
        print(f"   Platform: {best_deal['platform'].upper()}")
        print(f"   Price: {best_deal['currency']} {best_deal['price']:.2f}")
        print(f"   Seller: {best_deal['seller']}")
        print(f"   Rating: {best_deal.get('rating', 'N/A')}")
        print(f"   Savings: {best_deal['currency']} {best_deal['savings']:.2f} ({best_deal['savings_percent']:.1f}%)")

    # Platform breakdown
    platforms = results['price_comparison']
    print(f"\n🏪 Platforms found: {len(platforms)}")
    for platform, items in platforms.items():
        print(f"   {platform.upper()}: {len(items)} results")

print("\n✅ Price comparison test complete!")
