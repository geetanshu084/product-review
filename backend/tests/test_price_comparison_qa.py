#!/usr/bin/env python3
"""
Test price comparison data availability in Q&A chatbot
"""

import os
from dotenv import load_dotenv
from src.chatbot import ProductChatbot
from src.price_comparison import SerperPriceComparison

load_dotenv()

# Get API keys
google_api_key = os.getenv("GOOGLE_API_KEY")
serper_api_key = os.getenv("SERPER_API_KEY")

if not google_api_key:
    print("❌ GOOGLE_API_KEY not found")
    exit(1)

if not serper_api_key:
    print("❌ SERPER_API_KEY not found")
    exit(1)

print("="*80)
print("🧪 TESTING PRICE COMPARISON IN Q&A CHATBOT")
print("="*80)

# Initialize chatbot
chatbot = ProductChatbot(
    google_api_key=google_api_key,
    serper_api_key=serper_api_key,
    enable_web_search=True
)

# Initialize price comparison
price_comparer = SerperPriceComparison(serper_api_key)

# Create test session
session_id = "test_price_comparison_qa"

# Step 1: Get price comparison data for a test product
product_name = "iPhone 15 Pro 256GB"
print(f"\n📦 Fetching price comparison for: {product_name}")
print("-" * 80)

price_comparison = price_comparer.compare_prices(
    product_name,
    "amazon"
)

if price_comparison.get('error'):
    print(f"❌ Error: {price_comparison['error']}")
    exit(1)

print(f"✓ Found {price_comparison['total_results']} results")

# Step 2: Create sample product data with price comparison
sample_product = {
    "title": "Apple iPhone 15 Pro 256GB Natural Titanium",
    "brand": "Apple",
    "price": "₹1,34,900",
    "rating": "4.5",
    "category": "Smartphones",
    "features": [
        "A17 Pro chip with 6-core GPU",
        "Pro camera system (48MP Main | 12MP Ultra Wide | 12MP Telephoto)",
        "Action button for quick access",
        "USB-C connectivity",
        "Titanium design"
    ],
    "reviews": [
        {
            "rating": "5.0",
            "title": "Amazing camera quality",
            "text": "The camera on this phone is incredible. Night mode works brilliantly.",
            "author": "Tech Reviewer"
        },
        {
            "rating": "4.0",
            "title": "Great but expensive",
            "text": "Excellent phone but the price is quite high. Worth it if you can afford it.",
            "author": "Budget Buyer"
        }
    ],
    "price_comparison": price_comparison  # Include price comparison data
}

print(f"\n💾 Saving product data to Redis (with price comparison)...")
chatbot.set_product_data(session_id, sample_product)
print("✓ Product data saved\n")

# Step 3: Test Q&A questions about price comparison
print("\n" + "="*80)
print("TESTING Q&A WITH PRICE COMPARISON DATA")
print("="*80)

test_questions = [
    "Where can I buy this product?",
    "What's the best price available?",
    "Which platform has the cheapest price?",
    "How much can I save if I buy from the cheapest platform?",
    "Show me prices on Amazon vs Flipkart",
    "Which seller offers the best deal?",
    "What are the prices on different platforms?",
    "Is there a significant price difference across platforms?"
]

for i, question in enumerate(test_questions, 1):
    print(f"\n{i}. Question: {question}")
    print("-" * 80)

    try:
        answer = chatbot.ask(session_id, question)
        print(f"Answer: {answer}")
        print("✓ Successfully answered using price comparison data")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Step 4: Verify context includes price comparison
print("\n" + "="*80)
print("VERIFYING PRICE COMPARISON IN CONTEXT")
print("="*80)

product_data = chatbot.redis_memory.get_product_data(session_id)
if product_data and product_data.get('price_comparison'):
    pc = product_data['price_comparison']
    print(f"✓ Price comparison data found in Redis")
    print(f"  Total results: {pc.get('total_results', 0)}")
    print(f"  Platforms: {list(pc.get('price_comparison', {}).keys())}")
    if pc.get('best_deal'):
        best = pc['best_deal']
        print(f"  Best deal: {best['platform']} at {best['currency']} {best['price']:.2f}")
else:
    print("❌ Price comparison data not found in Redis")

# Clean up
print("\n" + "="*80)
print("Cleaning up test session...")
chatbot.clear_all_data(session_id)
print("✓ Test complete")
print("="*80)
