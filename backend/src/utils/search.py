"""
Generic Search Utility
Supports multiple search providers: DuckDuckGo (free, default) or Serper (Google)
"""

import os
import requests
from typing import Dict, List


def search(
    query: str,
    location: str = "India",
    num_results: int = 10
) -> List[Dict]:
    """
    Perform web search using configured provider

    Args:
        query: Search query
        location: Search location (default: "India")
        num_results: Number of results to fetch

    Returns:
        List of search results with title, url, snippet, date, source, position
    """
    provider = os.getenv('SEARCH_PROVIDER', 'duckduckgo').lower()

    if provider == 'serper':
        return _search_serper(query, location, num_results)
    else:
        return _search_duckduckgo(query, num_results)


def _search_serper(query: str, location: str, num_results: int) -> List[Dict]:
    """Search using Serper API (Google)"""
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        print("⚠ SERPER_API_KEY not found, falling back to DuckDuckGo")
        return _search_duckduckgo(query, num_results)

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    payload = {
        'q': query,
        'location': location,
        'num': num_results
    }

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        organic_results = data.get('organic', [])

        # Format results
        formatted_results = []
        for result in organic_results:
            formatted_results.append({
                'title': result.get('title', ''),
                'url': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'date': result.get('date', ''),
                'source': _extract_domain(result.get('link', '')),
                'position': result.get('position', 0)
            })

        return formatted_results

    except Exception as e:
        print(f"❌ Serper search error: {str(e)}, falling back to DuckDuckGo")
        return _search_duckduckgo(query, num_results)


def _search_duckduckgo(query: str, num_results: int) -> List[Dict]:
    """Search using DuckDuckGo (free, no API key required)"""
    try:
        from ddgs import DDGS

        results = DDGS().text(query, max_results=num_results)

        # Format results to match expected structure
        formatted_results = []
        for idx, result in enumerate(results, 1):
            formatted_results.append({
                'title': result.get('title', ''),
                'url': result.get('href', ''),
                'snippet': result.get('body', ''),
                'date': '',  # DuckDuckGo doesn't always provide dates
                'source': _extract_domain(result.get('href', '')),
                'position': idx
            })

        return formatted_results

    except Exception as e:
        print(f"❌ DuckDuckGo search error: {str(e)}")
        return []


def search_shopping(
    product_name: str,
    location: str = "India",
    num_results: int = 20
) -> Dict:
    """
    Search for product prices across shopping platforms

    Args:
        product_name: Product name to search for
        location: Search location (default: "India")
        num_results: Number of results to fetch

    Returns:
        Dictionary with shopping results
    """
    provider = os.getenv('SEARCH_PROVIDER', 'duckduckgo').lower()

    if provider == 'serper':
        return _search_shopping_serper(product_name, location, num_results)
    else:
        return _search_shopping_duckduckgo(product_name, num_results)


def _search_shopping_serper(product_name: str, location: str, num_results: int) -> Dict:
    """Search shopping using Serper API"""
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        print("⚠ SERPER_API_KEY not found, falling back to DuckDuckGo")
        return _search_shopping_duckduckgo(product_name, num_results)

    try:
        payload = {
            "q": product_name,
            "location": location,
            "num": num_results
        }

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://google.serper.dev/shopping",
            json=payload,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"⚠ Serper shopping search error: {str(e)}, falling back to DuckDuckGo")
        return _search_shopping_duckduckgo(product_name, num_results)


def _shorten_product_name(product_name: str) -> str:
    """
    Shorten product name to essential keywords for better search results

    Args:
        product_name: Full product name (can be very long)

    Returns:
        Shortened product name with key terms only
    """
    import re

    # Remove common filler phrases
    remove_phrases = [
        r'\|.*?warranty',
        r'\|.*?years?',
        r'\|.*?service',
        r'\|.*?unconditional',
        r'no service for.*?\|',
        r'\d+-year.*?\|',
        r'\d+-in-\d+.*?\|',
        r'smart iot.*?\|',
        r'ro\+uv\+.*?\|',
    ]

    shortened = product_name
    for phrase in remove_phrases:
        shortened = re.sub(phrase, '', shortened, flags=re.IGNORECASE)

    # Split by | and take first 2-3 meaningful parts
    parts = [p.strip() for p in shortened.split('|')]

    # Filter out very short parts and take max 2 parts
    meaningful_parts = [p for p in parts if len(p) > 10][:2]

    # If we got parts, use them, otherwise take first 100 chars
    if meaningful_parts:
        result = ' '.join(meaningful_parts)
    else:
        result = product_name[:100]

    # Clean up extra spaces
    result = ' '.join(result.split())

    return result


def _search_shopping_duckduckgo(product_name: str, num_results: int) -> Dict:
    """
    Search shopping using DuckDuckGo
    Note: DuckDuckGo doesn't have a dedicated shopping API, so we do a regular search
    with shopping-focused queries and parse the results
    """
    try:
        from ddgs import DDGS
        import re

        # Shorten product name for better search results
        short_name = _shorten_product_name(product_name)
        print(f"  🔍 Shortened query: '{short_name}' (from {len(product_name)} to {len(short_name)} chars)")

        # Enhance query for shopping results
        shopping_query = f"{short_name} buy price online India"
        results = DDGS().text(shopping_query, max_results=num_results)

        # Format results to mimic Serper's shopping results structure
        shopping_results = []
        for result in results:
            # Try to detect if this is an e-commerce site
            url = result.get('href', '')
            domain = _extract_domain(url)
            title = result.get('title', '')
            snippet = result.get('body', '')

            # Common Indian e-commerce domains
            ecommerce_domains = ['flipkart', 'amazon', 'myntra', 'snapdeal', 'ebay', 'tatacliq', 'ajio', 'croma']
            is_ecommerce = any(ecom in domain.lower() for ecom in ecommerce_domains)

            if is_ecommerce:
                # Try to extract price from title or snippet
                price = _extract_price_from_text(title + ' ' + snippet)

                shopping_results.append({
                    'title': title,
                    'link': url,
                    'price': price,
                    'source': domain,
                    'snippet': snippet
                })

        return {
            'shopping_results': shopping_results,
            'total': len(shopping_results)
        }

    except Exception as e:
        print(f"❌ DuckDuckGo shopping search error: {str(e)}")
        return {"shopping_results": [], "error": str(e)}


def _extract_price_from_text(text: str) -> str:
    """
    Extract price from text (title or snippet)

    Args:
        text: Text containing price information

    Returns:
        Extracted price or 'N/A'
    """
    import re

    # Common price patterns in Indian format
    patterns = [
        r'Rs\.?\s*(\d+[,\d]*)',  # Rs. 26999 or Rs 26,999
        r'₹\s*(\d+[,\d]*)',      # ₹26999 or ₹26,999
        r'INR\s*(\d+[,\d]*)',    # INR 26999
        r'only\s+for\s+Rs\.?\s*(\d+[,\d]*)',  # only for Rs. 26999
        r'price[:\s]+Rs\.?\s*(\d+[,\d]*)',    # price: Rs. 26999
        r'at\s+Rs\.?\s*(\d+[,\d]*)',          # at Rs. 26999
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            return f"₹{price_str}"

    return 'N/A'


def _extract_domain(url: str) -> str:
    """
    Extract domain from URL

    Args:
        url: Full URL

    Returns:
        Domain name
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ''
