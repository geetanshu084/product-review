"""
Multi-Platform Price Comparison
Compares product prices across Amazon, Flipkart, eBay, Walmart, and other platforms
"""

import os
import re
import statistics
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from src.utils.search import search_shopping as search_shopping_api


class SerperPriceComparison:
    """Price comparison across multiple e-commerce platforms (supports DuckDuckGo or Serper)"""

    def __init__(self):
        """
        Initialize the price comparison service

        Note: Supports both DuckDuckGo (free, default) and Serper (premium)
        Configure via SEARCH_PROVIDER environment variable
        """
        # Check which provider is configured
        provider = os.getenv('SEARCH_PROVIDER', 'duckduckgo').lower()
        if provider == 'serper' and not os.getenv('SERPER_API_KEY'):
            print("⚠ SERPER_API_KEY not found, will use DuckDuckGo fallback")
        elif provider == 'duckduckgo':
            print("✓ Using DuckDuckGo for price comparison (free)")

    def search_shopping(
        self,
        product_name: str,
        location: str = "India",
        num_results: int = 20
    ) -> Dict:
        """
        Search for product prices across shopping platforms

        Args:
            product_name: Product name to search for
            location: Location for search (default: "India")
            num_results: Number of results to fetch (default: 20)

        Returns:
            Dictionary with shopping results
        """
        raw_response = search_shopping_api(
            product_name=product_name,
            location=location,
            num_results=num_results
        )

        # DEBUG: Print raw API response
        provider = os.getenv('SEARCH_PROVIDER', 'duckduckgo').lower()
        print("\n" + "="*80)
        print(f"🔍 DEBUG: RAW SEARCH API RESPONSE ({provider.upper()})")
        print("="*80)
        print(f"Response type: {type(raw_response)}")
        print(f"Response keys: {list(raw_response.keys()) if isinstance(raw_response, dict) else 'N/A'}")
        print("\nFull response:")
        import json
        print(json.dumps(raw_response, indent=2, ensure_ascii=False))
        print("="*80 + "\n")

        return raw_response

    def _extract_platform_from_source(self, source: str) -> str:
        """
        Extract platform name from source string

        Args:
            source: Source string (e.g., "Amazon.in", "Flipkart.com")

        Returns:
            Platform name (e.g., "amazon", "flipkart", or actual seller name for unknown platforms)
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
            return source_lower  # Return actual seller name instead of "others"

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

    def _extract_product_attributes(self, title: str) -> Dict[str, str]:
        """
        Extract key product attributes from title

        Args:
            title: Product title

        Returns:
            Dictionary of attributes (brand, model, storage, ram, color, etc.)
        """
        title_lower = title.lower()
        attributes = {}

        # Extract brand (common brands)
        brands = ['apple', 'samsung', 'oneplus', 'xiaomi', 'realme', 'oppo', 'vivo',
                  'google', 'motorola', 'nokia', 'asus', 'sony', 'lg', 'huawei',
                  'iphone', 'galaxy', 'pixel', 'redmi', 'poco']
        for brand in brands:
            if brand in title_lower:
                attributes['brand'] = brand
                break

        # Extract storage capacity (GB, TB)
        storage_match = re.search(r'(\d+)\s*(gb|tb)', title_lower)
        if storage_match:
            attributes['storage'] = f"{storage_match.group(1)}{storage_match.group(2)}"

        # Extract RAM
        ram_match = re.search(r'(\d+)\s*gb\s*ram', title_lower)
        if ram_match:
            attributes['ram'] = f"{ram_match.group(1)}gb"

        # Extract color
        colors = ['black', 'white', 'blue', 'red', 'green', 'yellow', 'pink', 'purple',
                  'gold', 'silver', 'grey', 'gray', 'titanium', 'natural', 'midnight',
                  'starlight', 'sierra', 'alpine']
        for color in colors:
            if color in title_lower:
                attributes['color'] = color
                break

        # Extract model numbers/names
        model_match = re.search(r'(pro max|pro|plus|ultra|lite|mini|\d+[a-z]?)', title_lower)
        if model_match:
            attributes['model'] = model_match.group(1)

        return attributes

    def _calculate_product_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two product titles

        Args:
            title1: First product title
            title2: Second product title

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize titles
        t1 = re.sub(r'[^\w\s]', '', title1.lower())
        t2 = re.sub(r'[^\w\s]', '', title2.lower())

        # Use SequenceMatcher for basic similarity
        sequence_similarity = SequenceMatcher(None, t1, t2).ratio()

        # Extract and compare attributes
        attrs1 = self._extract_product_attributes(title1)
        attrs2 = self._extract_product_attributes(title2)

        # Weight attribute matches more heavily
        attribute_matches = 0
        total_attributes = 0

        for key in ['brand', 'storage', 'ram', 'model']:
            if key in attrs1 or key in attrs2:
                total_attributes += 1
                if key in attrs1 and key in attrs2 and attrs1[key] == attrs2[key]:
                    attribute_matches += 1

        attribute_similarity = attribute_matches / total_attributes if total_attributes > 0 else 0

        # Weighted average (attributes are more important than text similarity)
        final_similarity = (attribute_similarity * 0.7) + (sequence_similarity * 0.3)

        return final_similarity

    def _is_same_product(self, original_title: str, result_title: str, threshold: float = 0.65) -> bool:
        """
        Check if result is the same product as original

        Args:
            original_title: Original product title
            result_title: Result product title
            threshold: Similarity threshold (default: 0.65)

        Returns:
            True if same product, False otherwise
        """
        similarity = self._calculate_product_similarity(original_title, result_title)
        return similarity >= threshold

    def _extract_direct_url(self, url: str) -> str:
        """
        Extract direct URL from Google redirect URL

        Args:
            url: URL (possibly a Google redirect)

        Returns:
            Direct URL to the product
        """
        if not url:
            return ""

        # Check if it's a Google redirect URL
        if "google.com/url" in url or "google.com/shopping" in url:
            # Try to extract the actual URL from 'q' parameter
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            # Google uses 'q' parameter for the redirect URL
            if 'q' in params:
                return params['q'][0]

            # Some Shopping URLs use 'url' parameter
            if 'url' in params:
                return params['url'][0]

        # Return original URL if not a redirect
        return url

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

            # Extract direct URL (remove Google redirect)
            raw_url = result.get("link", "")
            direct_url = self._extract_direct_url(raw_url)

            # Extract platform once during normalization
            seller = result.get("source", "N/A")
            platform = self._extract_platform_from_source(seller)

            return {
                "title": result.get("title", "N/A"),
                "price": float(extracted_price) if extracted_price else 0.0,
                "currency": self._parse_currency(price_str),
                "url": direct_url,
                "seller": seller,
                "platform": platform,  # Pre-computed platform name
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
            results: List of normalized results (with pre-computed platform field)

        Returns:
            Dictionary with results grouped by platform
        """
        grouped = {}

        for result in results:
            if not result:
                continue

            platform = result["platform"]  # Use pre-computed platform
            if platform not in grouped:
                grouped[platform] = []
            grouped[platform].append(result)

        return grouped

    def calculate_price_stats(self, results: List[Dict]) -> Dict:
        """
        Calculate price statistics

        Args:
            results: List of normalized results with valid prices (already filtered)

        Returns:
            Dictionary with price statistics
        """
        if not results:
            return {
                "min_price": 0.0,
                "max_price": 0.0,
                "avg_price": 0.0,
                "median_price": 0.0,
                "total_results": 0
            }

        prices = [r["price"] for r in results]

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
            results: List of normalized results with valid prices (already filtered)

        Returns:
            Best deal dictionary or None
        """
        if not results:
            return None

        # Sort by price (ascending), then by rating (descending)
        sorted_results = sorted(
            results,
            key=lambda x: (x["price"], -x["rating"])
        )

        best = sorted_results[0]  # Lowest price
        max_price = sorted_results[-1]["price"]  # Highest price

        savings = max_price - best["price"]
        savings_percent = (savings / max_price * 100) if max_price > 0 else 0

        return {
            "platform": best["platform"],  # Use pre-computed platform
            "title": best["title"],
            "price": best["price"],
            "currency": best["currency"],
            "url": best["url"],
            "seller": best["seller"],
            "rating": best["rating"],
            "savings": round(savings, 2),
            "savings_percent": round(savings_percent, 2)
        }

    def compare_prices(self, product_name: str, source_platform: str) -> Dict:
        """
        Compare prices across platforms for the same product

        Args:
            product_name: Product name to search for
            source_platform: Platform being analyzed (e.g., "Amazon", "Flipkart") - excluded from competitors (default: None)

        Returns:
            Dictionary with price comparison data
        """
        print(f"🔍 Searching for '{product_name}' prices across platforms...")

        # Search using Serper API
        raw_results = self.search_shopping(product_name, "India", 20)

        if "error" in raw_results:
            return {
                "error": raw_results["error"],
                "price_comparison": {},
                "price_stats": {
                    "min_price": 0.0,
                    "max_price": 0.0,
                    "avg_price": 0.0,
                    "median_price": 0.0,
                    "total_results": 0
                },
                "best_deal": None,
                "total_results": 0
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
                "best_deal": None,
                "total_results": 0
            }

        # Normalize results
        normalized_results = []
        filtered_out_count = 0
        source_platform_filtered_count = 0

        for result in shopping_results:
            normalized = self._normalize_result(result)
            if normalized:
                # Filter out source platform (use pre-computed platform)
                if normalized['platform'] == source_platform:
                    source_platform_filtered_count += 1
                    continue


                if self._is_same_product(product_name, normalized['title'], 0.65):
                    normalized_results.append(normalized)
                else:
                    filtered_out_count += 1


        # Print filtering summary
        print(f"✓ Found {len(normalized_results)} valid results (filtered: {source_platform_filtered_count} from source platform, {filtered_out_count} non-exact matches)")

        # Separate results with and without prices
        valid_price_results = [r for r in normalized_results if r and r["price"] > 0]
        no_price_results = [r for r in normalized_results if r and r["price"] == 0]

        # Group ALL results by platform (including those without prices)
        grouped = self.group_by_platform(normalized_results)

        # Calculate statistics only for results with prices
        stats = self.calculate_price_stats(valid_price_results)

        # Find best deal only from results with prices
        best_deal = self.find_best_deal(valid_price_results) if valid_price_results else None

        # Print summary
        currency = normalized_results[0]['currency'] if normalized_results else 'INR'
        print(f"\n📊 Price Summary:")
        print(f"  Platforms found: {len(grouped)}")
        if valid_price_results:
            print(f"  Price range: {currency} {stats['min_price']:.2f} - {stats['max_price']:.2f}")
            if best_deal:
                print(f"  Best deal: {best_deal['platform']} at {best_deal['currency']} {best_deal['price']:.2f}")
                print(f"  Potential savings: {best_deal['currency']} {best_deal['savings']:.2f} ({best_deal['savings_percent']:.1f}%)")
        else:
            print(f"  ⚠ No prices available, but showing {len(no_price_results)} competitor links")

        return {
            "price_comparison": grouped,
            "price_stats": stats,
            "best_deal": best_deal,
            "total_results": len(normalized_results)  # Include all results, not just those with prices
        }
