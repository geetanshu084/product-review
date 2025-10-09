#!/usr/bin/env python
"""
Example usage of the Amazon Product Analysis Agent modules
This script demonstrates how to use the scraper, analyzer, and chatbot programmatically
"""

import os
from dotenv import load_dotenv
from src.scraper import AmazonScraper
from src.analyzer import ProductAnalyzer
from src.chatbot import ProductChatbot

# Load environment variables
load_dotenv()


def example_scraping():
    """Example: Scraping Amazon product"""
    print("=" * 60)
    print("EXAMPLE 1: Scraping Amazon Product")
    print("=" * 60)

    # Initialize scraper
    scraper = AmazonScraper()

    # Example Amazon product URL
    url = "https://www.amazon.com/dp/B08N5WRWNW"  # Example: PlayStation 5

    print(f"\nScraping product from: {url}")

    try:
        # Scrape product data
        product_data = scraper.scrape_product(url)

        print("\n✓ Scraping successful!")
        print(f"\nProduct Title: {product_data['title']}")
        print(f"Brand: {product_data['brand']}")
        print(f"Price: {product_data['price']}")
        print(f"Rating: {product_data['rating']}")
        print(f"Total Reviews: {product_data['total_reviews']}")
        print(f"Reviews Scraped: {len(product_data['reviews'])}")

        return product_data

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None


def example_analysis(product_data):
    """Example: Analyzing product with LLM"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Analyzing Product with AI")
    print("=" * 60)

    # Get GCP credentials path
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path or not os.path.exists(credentials_path):
        print("\n✗ GOOGLE_APPLICATION_CREDENTIALS not found or file doesn't exist")
        return None

    # Initialize analyzer
    analyzer = ProductAnalyzer(credentials_path=credentials_path)

    print("\nAnalyzing product with Google Gemini...")

    try:
        # Analyze product
        analysis = analyzer.analyze_product(product_data)

        print("\n✓ Analysis complete!")
        print("\n" + "-" * 60)
        print(analysis)
        print("-" * 60)

        return analysis

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None


def example_qa(product_data):
    """Example: Q&A with chatbot"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Q&A with Chatbot")
    print("=" * 60)

    # Get GCP credentials path
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path or not os.path.exists(credentials_path):
        print("\n✗ GOOGLE_APPLICATION_CREDENTIALS not found or file doesn't exist")
        return

    try:
        # Initialize chatbot
        chatbot = ProductChatbot(credentials_path=credentials_path)

        # Create a session
        session_id = "example_session"

        # Set product data
        chatbot.set_product_data(session_id, product_data)

        print("\nChatbot initialized. Asking questions...")

        # Example questions
        questions = [
            "What are the main pros of this product?",
            "Are there any common complaints?",
            "Is it worth the price?"
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n[Question {i}]: {question}")

            try:
                answer = chatbot.ask(session_id, question)
                print(f"[Answer]: {answer}")
            except Exception as e:
                print(f"[Error]: {str(e)}")

        # Clear conversation
        chatbot.clear_conversation(session_id)
        print("\n✓ Conversation cleared")

    except Exception as e:
        print(f"\n✗ Error initializing chatbot: {str(e)}")
        print("Make sure Redis is running!")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Amazon Product Analysis Agent - Example Usage")
    print("=" * 60)

    # Example 1: Scraping
    product_data = example_scraping()

    if product_data:
        # Example 2: Analysis
        analysis = example_analysis(product_data)

        # Example 3: Q&A
        if analysis:
            example_qa(product_data)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
