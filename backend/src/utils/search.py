"""
Generic Search Utility
Abstracts search API implementation (currently using Serper, but can be replaced)
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
    Perform web search

    Args:
        query: Search query
        location: Search location (default: "India")
        num_results: Number of results to fetch

    Returns:
        List of search results with title, url, snippet, date, source, position
    """
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        raise ValueError("SERPER_API_KEY not found in environment")

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
        print(f"❌ Search error: {str(e)}")
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
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        raise ValueError("SERPER_API_KEY not found in environment")

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
        print(f"⚠ Shopping search error: {str(e)}")
        return {"shopping_results": [], "error": str(e)}


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
