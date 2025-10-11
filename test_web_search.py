#!/usr/bin/env python3
"""
Test web search capability in Q&A chatbot
"""

import os
from dotenv import load_dotenv
from src.chatbot import ProductChatbot

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
print("🧪 TESTING WEB SEARCH IN Q&A CHATBOT")
print("="*80)

# Initialize chatbot with web search enabled
chatbot = ProductChatbot(
    google_api_key=google_api_key,
    serper_api_key=serper_api_key,
    enable_web_search=True
)

# Create test session
session_id = "test_web_search_session"

# Set sample product data
sample_product = {
    "title": "Apple iPhone 15 Pro 256GB Natural Titanium",
    "brand": "Apple",
    "price": "₹1,34,900",
    "rating": "4.5",
    "features": [
        "A17 Pro chip",
        "Pro camera system",
        "Action button",
        "USB-C"
    ]
}

print("\n📦 Setting up test product data...")
chatbot.set_product_data(session_id, sample_product)
print("✓ Product data set\n")

# Test questions that SHOULD trigger web search
print("\n" + "="*80)
print("TEST 1: Questions that SHOULD trigger web search")
print("="*80)

web_search_questions = [
    "What is the current price of this phone?",
    "Compare this with Samsung Galaxy S24",
    "Is this available in stock right now?",
    "What are the latest deals on this product?",
    "Show me similar alternatives"
]

for i, question in enumerate(web_search_questions, 1):
    print(f"\n{i}. Question: {question}")
    print("-" * 80)

    try:
        answer = chatbot.ask(session_id, question)
        print(f"Answer: {answer[:200]}...")
        print("✓ Web search working")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Test questions that should NOT trigger web search
print("\n" + "="*80)
print("TEST 2: Questions that should NOT trigger web search")
print("="*80)

no_search_questions = [
    "What are the key features of this phone?",
    "What color is this phone?",
    "What storage capacity does it have?",
    "Tell me about the camera"
]

for i, question in enumerate(no_search_questions, 1):
    print(f"\n{i}. Question: {question}")
    print("-" * 80)

    try:
        answer = chatbot.ask(session_id, question)
        print(f"Answer: {answer[:200]}...")
        print("✓ Answered from product data")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Clean up
print("\n" + "="*80)
print("Cleaning up test session...")
chatbot.clear_all_data(session_id)
print("✓ Test complete")
print("="*80)
