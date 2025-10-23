#!/usr/bin/env python
"""
Test script to verify Q&A chatbot can answer questions about product details
"""

import os
import uuid
from dotenv import load_dotenv
from src.scrapers import ScraperFactory
from src.chatbot import ProductChatbot

# Load environment variables
load_dotenv()

def test_qna_with_product_details():
    """Test Q&A functionality with comprehensive product data"""

    print("=" * 60)
    print("Testing Q&A with Comprehensive Product Data")
    print("=" * 60)

    # Test URL
    test_url = "https://www.amazon.in/Native-Purifier-RO-Copper-Alkaline/dp/B0D7HG2GZD/ref=cm_cr_arp_d_product_top?ie=UTF8&th=1"

    # Step 1: Check dependencies
    print("\nStep 1: Checking dependencies...")
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found!")
        return
    print("✓ Google API Key found")

    # Step 2: Scrape product
    print("\nStep 2: Scraping product data...")
    scraper = ScraperFactory.get_scraper(test_url)
    try:
        product_data = scraper.scrape_product(test_url)
        print(f"✓ Product scraped successfully")
        print(f"  - Has dimensions: {'Product Dimensions' in product_data.get('product_details', {})}")
        print(f"  - Specifications: {len(product_data.get('specifications', {}))} fields")
        print(f"  - Product details: {len(product_data.get('product_details', {}))} fields")
    except Exception as e:
        print(f"❌ Scraping failed: {str(e)}")
        return

    # Step 3: Initialize chatbot
    print("\nStep 3: Initializing chatbot...")
    try:
        chatbot = ProductChatbot(
            google_api_key=google_api_key,
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379)),
            redis_db=int(os.getenv('REDIS_DB', 0))
        )
        print("✓ Chatbot initialized successfully")
    except Exception as e:
        print(f"❌ Chatbot initialization failed: {str(e)}")
        return

    # Step 4: Set product data in Redis
    print("\nStep 4: Storing product data in Redis...")
    session_id = str(uuid.uuid4())
    try:
        chatbot.set_product_data(session_id, product_data)
        print(f"✓ Product data stored in Redis for session: {session_id}")
    except Exception as e:
        print(f"❌ Failed to store data: {str(e)}")
        return

    # Step 5: Test Q&A with product-specific questions
    print("\n" + "=" * 60)
    print("TESTING Q&A WITH PRODUCT DETAILS")
    print("=" * 60)

    test_questions = [
        "What are the dimensions of this product?",
        "What is the weight of the water purifier?",
        "What is the maximum flow rate?",
        "Does it work during power outages?",
        "What is the warranty period?"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Q: {question}")
        try:
            answer = chatbot.ask(session_id, question)
            print(f"A: {answer}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    # Step 6: Verify data retrieval from Redis
    print("\n" + "=" * 60)
    print("VERIFYING REDIS STORAGE")
    print("=" * 60)

    try:
        # Get stored product data
        stored_data = chatbot.get_product_data(session_id)
        if stored_data:
            print("✓ Product data retrieved from Redis")
            print(f"  - Title: {stored_data.get('title', 'N/A')[:60]}...")
            print(f"  - Has specifications: {bool(stored_data.get('specifications'))}")
            print(f"  - Has product_details: {bool(stored_data.get('product_details'))}")
            print(f"  - Has dimensions: {'Product Dimensions' in stored_data.get('product_details', {})}")

            # Check if dimensions are in stored data
            if 'Product Dimensions' in stored_data.get('product_details', {}):
                dims = stored_data['product_details']['Product Dimensions']
                print(f"  - Dimensions value: {dims}")
        else:
            print("❌ No product data found in Redis")
    except Exception as e:
        print(f"❌ Error retrieving data: {str(e)}")

    # Cleanup
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_qna_with_product_details()
