#!/usr/bin/env python3
"""
Test LangChain tool-based web search implementation
The LLM should decide when to use the web search tool
"""

import os
from dotenv import load_dotenv
from src.chatbot import ProductChatbot

load_dotenv()

print("="*80)
print("🧪 TESTING LANGCHAIN TOOL-BASED WEB SEARCH")
print("="*80)

# Initialize chatbot - reads config from environment variables
chatbot = ProductChatbot()

# Create test session
session_id = "test_langchain_tool_session"

# Set sample product data
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
            "text": "The camera on this phone is incredible. Night mode works brilliantly and the action button is very useful.",
            "author": "Tech Reviewer"
        },
        {
            "rating": "4.0",
            "title": "Great but expensive",
            "text": "Excellent phone but the price is quite high. Worth it if you can afford it. Build quality is top notch.",
            "author": "Budget Buyer"
        }
    ]
}

print("\n📦 Setting up test product data...")
chatbot.set_product_data(session_id, sample_product)
print("✓ Product data saved\n")

# Test 1: Questions that should NOT trigger web search (info in product data)
print("\n" + "="*80)
print("TEST 1: Questions that should NOT trigger web search")
print("(LLM should answer directly from product data)")
print("="*80)

no_search_questions = [
    "What are the key features of this phone?",
    "What do customers say about the camera?",
    "What color is this phone?",
    "Tell me about the reviews",
    "What is the rating?"
]

for i, question in enumerate(no_search_questions, 1):
    print(f"\n{i}. Question: {question}")
    print("-" * 80)

    try:
        answer = chatbot.ask(session_id, question)
        print(f"\nAnswer: {answer}")
        print("\n✓ Answered (check above if web_search tool was used)")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Test 2: Questions that SHOULD trigger web search (current/comparison info)
print("\n\n" + "="*80)
print("TEST 2: Questions that SHOULD trigger web search")
print("(LLM should decide to use web_search tool)")
print("="*80)

search_questions = [
    "What is the current market price for this phone?",
    "Compare this phone with Samsung Galaxy S24 Ultra",
    "What are the latest deals available for this product?",
]

for i, question in enumerate(search_questions, 1):
    print(f"\n{i}. Question: {question}")
    print("-" * 80)

    try:
        answer = chatbot.ask(session_id, question)
        print(f"\nAnswer: {answer}")
        print("\n✓ Answered (check above if web_search tool was used)")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Clean up
print("\n" + "="*80)
print("Cleaning up test session...")
chatbot.clear_all_data(session_id)
print("✓ Test complete")
print("="*80)

print("\n📝 SUMMARY:")
print("- If web_search tool was NOT used for Test 1 questions: ✓ CORRECT")
print("- If web_search tool WAS used for Test 2 questions: ✓ CORRECT")
print("- The LLM should make intelligent decisions about when to search")
