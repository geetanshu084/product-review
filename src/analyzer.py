"""
LLM Analysis Engine Module
Uses Google Gemini via LangChain to analyze Amazon product data
"""

import json
import os
from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class ProductAnalyzer:
    """Analyzes product data using Google Gemini LLM"""

    def __init__(self, credentials_path: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp", google_api_key: Optional[str] = None):
        """
        Initialize the product analyzer

        Args:
            credentials_path: Path to GCP service account JSON file (deprecated - use google_api_key instead)
            model_name: Name of the Gemini model to use
            google_api_key: Google API key for Gemini (recommended)
        """
        # Check for API key first (recommended approach)
        api_key = google_api_key or os.getenv('GOOGLE_API_KEY')

        if not api_key:
            raise ValueError(
                "Google API key is required. Please either:\n"
                "1. Set GOOGLE_API_KEY environment variable in your .env file, or\n"
                "2. Pass google_api_key parameter\n\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,  # Lower temperature for more consistent analysis
            convert_system_message_to_human=True,
            google_api_key=api_key
        )

        # Load prompt template
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config',
            'prompts',
            'product_analysis_prompt.txt'
        )

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        self.prompt = PromptTemplate(
            input_variables=["product_data"],
            template=prompt_template
        )

        # Create LLM chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def format_product_data(self, product_data: Dict) -> str:
        """
        Format product data into a readable string for the LLM

        Args:
            product_data: Dictionary containing product information

        Returns:
            Formatted string representation of product data
        """
        formatted = []

        # Basic product info
        formatted.append("=== PRODUCT INFORMATION ===")
        formatted.append(f"ASIN: {product_data.get('asin', 'N/A')}")
        formatted.append(f"Title: {product_data.get('title', 'N/A')}")
        formatted.append(f"Brand: {product_data.get('brand', 'N/A')}")
        formatted.append(f"Category: {product_data.get('category', 'N/A')}")
        formatted.append(f"Price: {product_data.get('price', 'N/A')}")
        formatted.append(f"Rating: {product_data.get('rating', 'N/A')}")
        formatted.append(f"Total Reviews: {product_data.get('total_reviews', 'N/A')}")
        formatted.append(f"Availability: {product_data.get('availability', 'N/A')}")
        formatted.append("")

        # Product description
        formatted.append("=== PRODUCT DESCRIPTION ===")
        formatted.append(product_data.get('description', 'N/A'))
        formatted.append("")

        # Product features
        if product_data.get('features'):
            formatted.append("=== PRODUCT FEATURES ===")
            for i, feature in enumerate(product_data['features'], 1):
                formatted.append(f"{i}. {feature}")
            formatted.append("")

        # Product specifications
        specifications = product_data.get('specifications', {})
        if specifications:
            formatted.append("=== PRODUCT SPECIFICATIONS ===")
            for key, value in specifications.items():
                formatted.append(f"{key}: {value}")
            formatted.append("")

        # Product details (dimensions, weight, etc.)
        product_details = product_data.get('product_details', {})
        if product_details:
            formatted.append("=== PRODUCT DETAILS ===")
            for key, value in product_details.items():
                formatted.append(f"{key}: {value}")
            formatted.append("")

        # Technical details
        technical_details = product_data.get('technical_details', {})
        if technical_details:
            formatted.append("=== TECHNICAL DETAILS ===")
            for key, value in technical_details.items():
                formatted.append(f"{key}: {value}")
            formatted.append("")

        # Additional information
        additional_info = product_data.get('additional_information', {})
        if additional_info:
            formatted.append("=== ADDITIONAL INFORMATION ===")
            for key, value in additional_info.items():
                formatted.append(f"{key}: {value}")
            formatted.append("")

        # Warranty
        warranty = product_data.get('warranty', '')
        if warranty and warranty != "Warranty information not available":
            formatted.append("=== WARRANTY INFORMATION ===")
            formatted.append(warranty)
            formatted.append("")

        # Bank offers
        bank_offers = product_data.get('bank_offers', [])
        if bank_offers:
            formatted.append("=== BANK OFFERS ===")
            for i, offer in enumerate(bank_offers, 1):
                formatted.append(f"{i}. {offer.get('bank', 'Bank')}: {offer.get('offer_type', 'Offer')} - {offer.get('description', '')}")
                if offer.get('terms'):
                    formatted.append(f"   Terms: {offer['terms']}")
            formatted.append("")

        # Seller information
        formatted.append("=== SELLER INFORMATION ===")
        formatted.append(f"Seller Name: {product_data.get('seller_name', 'N/A')}")
        formatted.append(f"Seller Rating: {product_data.get('seller_rating', 'N/A')}")
        formatted.append("")

        # Customer reviews
        reviews = product_data.get('reviews', [])
        if reviews:
            formatted.append("=== CUSTOMER REVIEWS ===")
            formatted.append(f"Total Reviews Analyzed: {len(reviews)}")
            formatted.append("")

            for i, review in enumerate(reviews, 1):
                formatted.append(f"--- Review {i} ---")
                formatted.append(f"Rating: {review.get('rating', 'N/A')}")
                formatted.append(f"Title: {review.get('title', 'N/A')}")
                formatted.append(f"Author: {review.get('author', 'Anonymous')}")
                formatted.append(f"Date: {review.get('date', 'N/A')}")
                formatted.append(f"Verified Purchase: {review.get('verified', False)}")
                formatted.append(f"Review Text: {review.get('text', 'N/A')}")
                formatted.append("")
        else:
            formatted.append("=== CUSTOMER REVIEWS ===")
            formatted.append("No reviews available for analysis")
            formatted.append("")

        return "\n".join(formatted)

    def analyze_product(self, product_data: Dict) -> str:
        """
        Analyze product data using Gemini LLM

        Args:
            product_data: Dictionary containing scraped product data

        Returns:
            Markdown-formatted analysis string

        Raises:
            Exception: If LLM analysis fails
        """
        try:
            # Format product data
            formatted_data = self.format_product_data(product_data)

            # Run analysis
            result = self.chain.run(product_data=formatted_data)

            return result.strip()

        except Exception as e:
            raise Exception(
                f"LLM analysis failed. Please check your GCP credentials and try again. Error: {str(e)}"
            )

    def get_summary(self, product_data: Dict) -> Dict:
        """
        Get a quick summary of product data without full analysis

        Args:
            product_data: Dictionary containing product data

        Returns:
            Dictionary with summary information
        """
        return {
            'title': product_data.get('title', 'N/A'),
            'brand': product_data.get('brand', 'N/A'),
            'price': product_data.get('price', 'N/A'),
            'rating': product_data.get('rating', 'N/A'),
            'total_reviews': product_data.get('total_reviews', 'N/A'),
            'reviews_analyzed': len(product_data.get('reviews', []))
        }
