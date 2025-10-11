#!/usr/bin/env python3
"""
Demonstrate exact product matching feature
"""

import os
from dotenv import load_dotenv
from src.price_comparison import SerperPriceComparison

load_dotenv()

serper_api_key = os.getenv("SERPER_API_KEY")

if not serper_api_key:
    print("❌ SERPER_API_KEY not found")
    exit(1)

# Test product
product_name = "iPhone 15 Pro 256GB Natural Titanium"
print("="*80)
print(f"🔍 PRICE COMPARISON: {product_name}")
print("="*80)

comparer = SerperPriceComparison(serper_api_key)

# Compare prices with exact match filtering (default)
results = comparer.compare_prices(
    product_name,
    location="India",
    num_results=40,
    filter_exact_match=True  # Only show exact matches
)

if results.get('error'):
    print(f"\n❌ Error: {results['error']}")
    exit(1)

# Display results
print(f"\n✅ Found {results['total_results']} exact product matches")
print("\n" + "-"*80)

# Price statistics
stats = results['price_stats']
print(f"\n💰 PRICE RANGE:")
print(f"   Lowest:  ₹{stats['min_price']:,.2f}")
print(f"   Highest: ₹{stats['max_price']:,.2f}")
print(f"   Average: ₹{stats['avg_price']:,.2f}")
print(f"   Median:  ₹{stats['median_price']:,.2f}")

# Best deal
if results.get('best_deal'):
    best = results['best_deal']
    print(f"\n🏆 BEST DEAL:")
    print(f"   Product: {best['title']}")
    print(f"   Price: {best['currency']} {best['price']:,.2f}")
    print(f"   Platform: {best['platform'].upper()}")
    print(f"   Seller: {best['seller']}")
    print(f"   Rating: {best['rating']}")
    print(f"   💸 You save: {best['currency']} {best['savings']:,.2f} ({best['savings_percent']:.1f}%)")

# Platform breakdown
print(f"\n🏪 PRICES BY PLATFORM:")
for platform, items in results['price_comparison'].items():
    if items:
        prices = [item['price'] for item in items]
        print(f"\n   {platform.upper()} ({len(items)} listings):")
        print(f"      Lowest: ₹{min(prices):,.2f}")
        print(f"      Highest: ₹{max(prices):,.2f}")

        # Show top 3 deals
        print(f"      Top deals:")
        for i, item in enumerate(sorted(items, key=lambda x: x['price'])[:3], 1):
            print(f"         {i}. ₹{item['price']:,.2f} - {item['seller']}")

print("\n" + "="*80)
print("✅ All prices shown are for the EXACT SAME PRODUCT")
print("   (Different variants like 'Pro Max', '128GB', etc. are filtered out)")
print("="*80)
