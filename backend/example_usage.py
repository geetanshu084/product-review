#!/usr/bin/env python
"""
Example usage of the Amazon Product Analysis Agent modules
This script demonstrates how to use the scraper, analyzer, and chatbot programmatically
"""

import os
from dotenv import load_dotenv
from src.scrapers import ScraperFactory
from src.workflow_orchestrator import ProductWorkflowOrchestrator
from src.chatbot import ProductChatbot

# Load environment variables
load_dotenv()


def example_scraping():
    """Example: Scraping Amazon product"""
    print("=" * 60)
    print("EXAMPLE 1: Scraping Amazon Product")
    print("=" * 60)

    # Example Amazon product URL
    url = "https://www.amazon.com/dp/B08N5WRWNW"  # Example: PlayStation 5

    print(f"\nScraping product from: {url}")

    # Initialize scraper using factory pattern
    scraper = ScraperFactory.get_scraper(url)

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


def example_analysis(url):
    """Example: Analyzing product with unified workflow (scraping + analysis)"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Unified Workflow (Scraping + Analysis)")
    print("=" * 60)

    # Initialize workflow orchestrator (reads configuration from environment variables)
    orchestrator = ProductWorkflowOrchestrator()

    print("\nRunning unified workflow (scraping + price comparison + web search + analysis)...")

    try:
        # Run complete workflow
        result = orchestrator.run(url=url)

        print("\n✓ Workflow complete!")
        print("\n" + "-" * 60)
        print(result.get("analysis", "No analysis available"))
        print("-" * 60)

        return result.get("analysis")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None


def example_qa(product_data):
    """Example: Q&A with chatbot"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Q&A with Chatbot")
    print("=" * 60)

    try:
        # Initialize chatbot - reads config from environment variables
        chatbot = ProductChatbot()

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

    # Test URL
    url = "https://www.amazon.com/dp/B08N5WRWNW"  # Example: PlayStation 5

    # Example 1: Scraping only
    product_data = example_scraping()

    # Example 2: Unified workflow (scraping + analysis)
    if product_data:
        analysis = example_analysis(url)

        # Example 3: Q&A
        if analysis:
            example_qa(product_data)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
