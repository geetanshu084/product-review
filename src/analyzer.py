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
from src.price_comparison import SerperPriceComparison


class ProductAnalyzer:
    """Analyzes product data using Google Gemini LLM"""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
        google_api_key: Optional[str] = None,
        serper_api_key: Optional[str] = None,
        enable_price_comparison: bool = True
    ):
        """
        Initialize the product analyzer

        Args:
            credentials_path: Path to GCP service account JSON file (deprecated - use google_api_key instead)
            model_name: Name of the Gemini model to use
            google_api_key: Google API key for Gemini (recommended)
            serper_api_key: Serper API key for price comparison (optional)
            enable_price_comparison: Whether to enable price comparison feature
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

        # Initialize price comparison if enabled
        self.enable_price_comparison = enable_price_comparison
        self.price_comparer = None

        if enable_price_comparison:
            serper_key = serper_api_key or os.getenv('SERPER_API_KEY')
            if serper_key:
                try:
                    self.price_comparer = SerperPriceComparison(serper_key)
                    print("✓ Price comparison enabled")
                except Exception as e:
                    print(f"⚠ Price comparison disabled: {str(e)}")
                    self.price_comparer = None
            else:
                print("⚠ SERPER_API_KEY not found - price comparison disabled")

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

    def get_price_comparison(self, product_title: str) -> Optional[Dict]:
        """
        Get price comparison data for the product

        Args:
            product_title: Product title to search for

        Returns:
            Price comparison dictionary or None
        """
        if not self.price_comparer:
            return None

        try:
            return self.price_comparer.compare_prices(product_title)
        except Exception as e:
            print(f"⚠ Price comparison failed: {str(e)}")
            return None

    def format_product_data(self, product_data: Dict, price_comparison: Optional[Dict] = None) -> str:
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

        # Price comparison data
        if price_comparison and price_comparison.get('total_results', 0) > 0:
            formatted.append("=== PRICE COMPARISON ===")
            formatted.append(f"Total Results Found: {price_comparison['total_results']}")
            formatted.append("")

            # Price statistics
            stats = price_comparison.get('price_stats', {})
            if stats:
                formatted.append("Price Statistics:")
                formatted.append(f"  Minimum Price: {stats.get('min_price', 0):.2f}")
                formatted.append(f"  Maximum Price: {stats.get('max_price', 0):.2f}")
                formatted.append(f"  Average Price: {stats.get('avg_price', 0):.2f}")
                formatted.append(f"  Median Price: {stats.get('median_price', 0):.2f}")
                formatted.append("")

            # Best deal
            best_deal = price_comparison.get('best_deal')
            if best_deal:
                formatted.append("Best Deal Found:")
                formatted.append(f"  Platform: {best_deal['platform'].upper()}")
                formatted.append(f"  Seller: {best_deal['seller']}")
                formatted.append(f"  Price: {best_deal['currency']} {best_deal['price']:.2f}")
                formatted.append(f"  Rating: {best_deal.get('rating', 'N/A')}")
                formatted.append(f"  Potential Savings: {best_deal['currency']} {best_deal['savings']:.2f} ({best_deal['savings_percent']:.1f}%)")
                formatted.append("")

            # Platform breakdown
            platforms = price_comparison.get('price_comparison', {})
            if platforms:
                formatted.append("Price by Platform:")
                for platform, items in platforms.items():
                    if items:
                        prices = [item['price'] for item in items if item['price'] > 0]
                        if prices:
                            formatted.append(f"  {platform.upper()}: {len(items)} results, min {items[0]['currency']} {min(prices):.2f}")
                formatted.append("")

        return "\n".join(formatted)

    def analyze_product(self, product_data: Dict, include_price_comparison: bool = True) -> str:
        """
        Analyze product data using Gemini LLM

        Args:
            product_data: Dictionary containing scraped product data
            include_price_comparison: Whether to include price comparison in analysis

        Returns:
            Markdown-formatted analysis string

        Raises:
            Exception: If LLM analysis fails
        """
        try:
            # Get price comparison if enabled
            price_comparison = None
            if include_price_comparison and self.price_comparer:
                product_title = product_data.get('title', '')
                if product_title:
                    print("\n🔍 Fetching price comparison data...")
                    price_comparison = self.get_price_comparison(product_title)
                    # Store in product_data for later use
                    product_data['price_comparison'] = price_comparison

            # Format product data
            formatted_data = self.format_product_data(product_data, price_comparison)

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
