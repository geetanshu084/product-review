"""
Multi-Platform Price Comparison using Serper API
Compares product prices across Amazon, Flipkart, eBay, Walmart, and other platforms
"""

import re
import statistics
from typing import Dict, List, Optional
import requests


class SerperPriceComparison:
    """Price comparison across multiple e-commerce platforms using Serper API"""

    def __init__(self, api_key: str):
        """
        Initialize the price comparison service

        Args:
            api_key: Serper API key from serper.dev
        """
        self.api_key = api_key
        self.base_url = "https://google.serper.dev"

    def search_shopping(
        self,
        product_name: str,
        location: str = "India",
        num_results: int = 20
    ) -> Dict:
        """
        Search for product prices using Serper Shopping API

        Args:
            product_name: Product name to search for
            location: Location for search (default: "India")
            num_results: Number of results to fetch (default: 20)

        Returns:
            Dictionary with shopping results
        """
        try:
            payload = {
                "q": product_name,
                "location": location,
                "num": num_results
            }

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.base_url}/shopping",
                json=payload,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"⚠ Serper API error: {str(e)}")
            return {"shopping_results": [], "error": str(e)}

    def _extract_platform_from_source(self, source: str) -> str:
        """
        Extract platform name from source string

        Args:
            source: Source string (e.g., "Amazon.in", "Flipkart.com")

        Returns:
            Platform name (e.g., "amazon", "flipkart")
        """
        source_lower = source.lower()

        if "amazon" in source_lower:
            return "amazon"
        elif "flipkart" in source_lower:
            return "flipkart"
        elif "ebay" in source_lower:
            return "ebay"
        elif "walmart" in source_lower:
            return "walmart"
        elif "myntra" in source_lower:
            return "myntra"
        elif "snapdeal" in source_lower:
            return "snapdeal"
        elif "croma" in source_lower:
            return "croma"
        elif "tata" in source_lower:
            return "tata"
        else:
            return "others"

    def _parse_currency(self, price_str: str) -> str:
        """
        Extract currency symbol from price string

        Args:
            price_str: Price string (e.g., "₹15,999", "$199.99")

        Returns:
            Currency symbol or code
        """
        if "₹" in price_str:
            return "INR"
        elif "$" in price_str:
            return "USD"
        elif "€" in price_str:
            return "EUR"
        elif "£" in price_str:
            return "GBP"
        else:
            return "INR"  # Default

    def _normalize_result(self, result: Dict) -> Dict:
        """
        Normalize a single shopping result

        Args:
            result: Raw result from Serper API

        Returns:
            Normalized result dictionary
        """
        try:
            price_str = result.get("price", "0")
            extracted_price = result.get("extracted_price", 0)

            # If extracted_price is not available, try to parse from price string
            if not extracted_price and price_str:
                # Remove currency symbols and commas
                price_clean = re.sub(r'[^\d.]', '', price_str)
                try:
                    extracted_price = float(price_clean)
                except ValueError:
                    extracted_price = 0

            return {
                "title": result.get("title", "N/A"),
                "price": float(extracted_price) if extracted_price else 0.0,
                "currency": self._parse_currency(price_str),
                "url": result.get("link", ""),
                "seller": result.get("source", "N/A"),
                "rating": result.get("rating", 0.0),
                # API returns "ratingCount" (not "reviews")
                "reviews": result.get("ratingCount", result.get("reviews", 0)),
                "delivery": result.get("delivery", "N/A"),
                "in_stock": True,  # Assume in stock if listed
                # API returns "imageUrl" (not "thumbnail")
                "thumbnail": result.get("imageUrl", result.get("thumbnail", ""))
            }
        except Exception as e:
            print(f"⚠ Error normalizing result: {str(e)}")
            return None

    def group_by_platform(self, results: List[Dict]) -> Dict:
        """
        Group results by platform

        Args:
            results: List of normalized results

        Returns:
            Dictionary with results grouped by platform
        """
        grouped = {
            "amazon": [],
            "flipkart": [],
            "ebay": [],
            "walmart": [],
            "myntra": [],
            "snapdeal": [],
            "croma": [],
            "tata": [],
            "others": []
        }

        for result in results:
            if not result:
                continue

            platform = self._extract_platform_from_source(result["seller"])
            grouped[platform].append(result)

        # Remove empty platforms
        grouped = {k: v for k, v in grouped.items() if v}

        return grouped

    def calculate_price_stats(self, results: List[Dict]) -> Dict:
        """
        Calculate price statistics

        Args:
            results: List of normalized results

        Returns:
            Dictionary with price statistics
        """
        prices = [r["price"] for r in results if r and r["price"] > 0]

        if not prices:
            return {
                "min_price": 0.0,
                "max_price": 0.0,
                "avg_price": 0.0,
                "median_price": 0.0,
                "total_results": 0
            }

        return {
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": statistics.mean(prices),
            "median_price": statistics.median(prices),
            "total_results": len(prices)
        }

    def find_best_deal(self, results: List[Dict]) -> Optional[Dict]:
        """
        Find the best deal (lowest price with good rating)

        Args:
            results: List of normalized results

        Returns:
            Best deal dictionary or None
        """
        valid_results = [r for r in results if r and r["price"] > 0]

        if not valid_results:
            return None

        # Sort by price (ascending), then by rating (descending)
        sorted_results = sorted(
            valid_results,
            key=lambda x: (x["price"], -x["rating"])
        )

        best = sorted_results[0]
        max_price = max(r["price"] for r in valid_results)

        savings = max_price - best["price"]
        savings_percent = (savings / max_price * 100) if max_price > 0 else 0

        platform = self._extract_platform_from_source(best["seller"])

        return {
            "platform": platform,
            "title": best["title"],
            "price": best["price"],
            "currency": best["currency"],
            "url": best["url"],
            "seller": best["seller"],
            "rating": best["rating"],
            "savings": round(savings, 2),
            "savings_percent": round(savings_percent, 2)
        }

    def compare_prices(
        self,
        product_name: str,
        location: str = "India",
        num_results: int = 20
    ) -> Dict:
        """
        Compare prices across platforms

        Args:
            product_name: Product name to search for
            location: Location for search (default: "India")
            num_results: Number of results to fetch

        Returns:
            Dictionary with price comparison data
        """
        print(f"🔍 Searching for '{product_name}' prices across platforms...")

        # Search using Serper API
        raw_results = self.search_shopping(product_name, location, num_results)

        if "error" in raw_results:
            return {
                "error": raw_results["error"],
                "price_comparison": {},
                "price_stats": {},
                "best_deal": None
            }

        # Serper API returns results in "shopping" key (not "shopping_results")
        shopping_results = raw_results.get("shopping", raw_results.get("shopping_results", []))

        if not shopping_results:
            print("⚠ No shopping results found")
            return {
                "price_comparison": {},
                "price_stats": {
                    "min_price": 0.0,
                    "max_price": 0.0,
                    "avg_price": 0.0,
                    "median_price": 0.0,
                    "total_results": 0
                },
                "best_deal": None
            }

        # Normalize results
        normalized_results = []
        for result in shopping_results:
            normalized = self._normalize_result(result)
            if normalized:
                normalized_results.append(normalized)

        print(f"✓ Found {len(normalized_results)} valid results")

        # Group by platform
        grouped = self.group_by_platform(normalized_results)

        # Calculate statistics
        stats = self.calculate_price_stats(normalized_results)

        # Find best deal
        best_deal = self.find_best_deal(normalized_results)

        # Print summary
        currency = normalized_results[0]['currency'] if normalized_results else 'INR'
        print(f"\n📊 Price Summary:")
        print(f"  Platforms found: {len(grouped)}")
        print(f"  Price range: {currency} {stats['min_price']:.2f} - {stats['max_price']:.2f}")
        if best_deal:
            print(f"  Best deal: {best_deal['platform']} at {best_deal['currency']} {best_deal['price']:.2f}")
            print(f"  Potential savings: {best_deal['currency']} {best_deal['savings']:.2f} ({best_deal['savings_percent']:.1f}%)")

        return {
            "price_comparison": grouped,
            "price_stats": stats,
            "best_deal": best_deal,
            "total_results": len(normalized_results)
        }


if __name__ == "__main__":
    # Test the price comparison
    import os
    from dotenv import load_dotenv

    load_dotenv()

    serper_api_key = os.getenv("SERPER_API_KEY")

    if not serper_api_key:
        print("❌ SERPER_API_KEY not found in .env file")
        exit(1)

    # Test with a product
    comparer = SerperPriceComparison(serper_api_key)
    results = comparer.compare_prices(
        "iPhone 15 Pro 256GB",
        location="India",
        num_results=20
    )

    print("\n" + "="*60)
    print("PRICE COMPARISON RESULTS")
    print("="*60)

    if results.get("error"):
        print(f"❌ Error: {results['error']}")
    else:
        print(f"\nTotal results: {results['total_results']}")
        print(f"\nPrice Statistics:")
        stats = results["price_stats"]
        print(f"  Min: ₹{stats['min_price']:.2f}")
        print(f"  Max: ₹{stats['max_price']:.2f}")
        print(f"  Avg: ₹{stats['avg_price']:.2f}")
        print(f"  Median: ₹{stats['median_price']:.2f}")

        if results["best_deal"]:
            print(f"\nBest Deal:")
            best = results["best_deal"]
            print(f"  Platform: {best['platform']}")
            print(f"  Price: {best['currency']} {best['price']:.2f}")
            print(f"  Seller: {best['seller']}")
            print(f"  Savings: {best['currency']} {best['savings']:.2f} ({best['savings_percent']:.1f}%)")

        print(f"\nPlatform Breakdown:")
        for platform, items in results["price_comparison"].items():
            print(f"  {platform.capitalize()}: {len(items)} results")
