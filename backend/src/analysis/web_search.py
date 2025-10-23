"""
Web Search Analyzer for External Product Reviews
Uses Serper API to find external reviews, comparisons, and issues
Uses Gemini LLM to summarize findings and detect red flags
"""

import json
import os
import requests
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import google.generativeai as genai
from src.prompts import (
    get_review_filter_prompt,
    get_reddit_filter_prompt,
    get_news_filter_prompt,
    get_comparison_filter_prompt,
    get_key_findings_prompt,
    get_red_flags_prompt,
    get_sentiment_analysis_prompt
)


class WebSearchAnalyzer:
    """Analyzes products using external web search results"""

    def __init__(self):
        """
        Initialize web search analyzer

        Reads configuration from environment variables:
        - SERPER_API_KEY: Serper API key for web search
        - GOOGLE_API_KEY: Google Gemini API key for summarization
        """
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')

        if not self.serper_api_key:
            raise ValueError("SERPER_API_KEY not found in environment")
        if not self.gemini_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        self.search_endpoint = "https://google.serper.dev/search"

    def search_external_reviews(self, product_name: str) -> Dict:
        """
        Search for external product reviews

        Args:
            product_name: Name of the product

        Returns:
            Dict with review results
        """
        query = f"{product_name} review"
        results = self._search_serper(query, num_results=10)

        return {
            'query': query,
            'results': results,
            'count': len(results)
        }

    def search_comparisons(self, product_name: str) -> Dict:
        """
        Search for product comparisons

        Args:
            product_name: Name of the product

        Returns:
            Dict with comparison results
        """
        query = f"{product_name} vs alternatives comparison"
        results = self._search_serper(query, num_results=10)

        return {
            'query': query,
            'results': results,
            'count': len(results)
        }

    def search_issues(self, product_name: str) -> Dict:
        """
        Search for product issues and problems

        Args:
            product_name: Name of the product

        Returns:
            Dict with issue results
        """
        query = f"{product_name} problems issues complaints"
        results = self._search_serper(query, num_results=10)

        return {
            'query': query,
            'results': results,
            'count': len(results)
        }

    def search_reddit_discussions(self, product_name: str) -> Dict:
        """
        Search for Reddit discussions about the product

        Args:
            product_name: Name of the product

        Returns:
            Dict with Reddit discussion results
        """
        query = f"{product_name} site:reddit.com"
        results = self._search_serper(query, num_results=10)

        # Filter to ensure only Reddit URLs
        reddit_only = [r for r in results if 'reddit.com' in r.get('url', '').lower()]

        return {
            'query': query,
            'results': reddit_only,
            'count': len(reddit_only)
        }

    def search_news_articles(self, product_name: str) -> Dict:
        """
        Search for news articles about the product (launches, announcements, updates)

        Args:
            product_name: Name of the product

        Returns:
            Dict with news article results
        """
        query = f"{product_name} news launch announcement"
        results = self._search_serper(query, num_results=10)

        return {
            'query': query,
            'results': results,
            'count': len(results)
        }

    def analyze_product(self, product_name: str, source_platform: str = None) -> Dict:
        """
        Perform comprehensive web search analysis for a product

        Args:
            product_name: Name of the product
            source_platform: Platform being analyzed (e.g., "Amazon", "Flipkart") - excluded from external reviews (default: None)

        Returns:
            Complete analysis with reviews, comparisons, issues, and insights
        """
        print(f"🔍 Searching external sources for: {product_name}")

        # Perform all searches
        reviews = self.search_external_reviews(product_name)
        comparisons = self.search_comparisons(product_name)
        issues = self.search_issues(product_name)
        reddit = self.search_reddit_discussions(product_name)
        news = self.search_news_articles(product_name)

        # Filter out source platform URLs if specified
        total_filtered = 0
        if source_platform:
            reviews['results'], count1 = self._filter_source_platform(reviews['results'], source_platform)
            comparisons['results'], count2 = self._filter_source_platform(comparisons['results'], source_platform)
            issues['results'], count3 = self._filter_source_platform(issues['results'], source_platform)
            reddit['results'], count4 = self._filter_source_platform(reddit['results'], source_platform)
            news['results'], count5 = self._filter_source_platform(news['results'], source_platform)
            total_filtered = count1 + count2 + count3 + count4 + count5

            if total_filtered > 0:
                print(f"✓ Filtered out {total_filtered} results from {source_platform} (source platform)")

        # Combine all results
        all_results = (
            reviews['results'] +
            comparisons['results'] +
            issues['results'] +
            reddit['results'] +
            news['results']
        )

        # Extract video reviews
        video_reviews = self._extract_video_reviews(all_results)

        # Categorize results
        external_reviews = self._categorize_results(reviews['results'], 'review')
        comparison_articles = self._categorize_results(comparisons['results'], 'comparison')
        reddit_discussions = self._categorize_results(reddit['results'], 'reddit')
        news_articles = self._categorize_results(news['results'], 'news')

        # Filter out irrelevant content using LLM
        print("🧹 Filtering out irrelevant external content with LLM...")
        external_reviews = self._filter_irrelevant_content(external_reviews, product_name, 'review')
        comparison_articles = self._filter_irrelevant_content(comparison_articles, product_name, 'comparison')
        reddit_discussions = self._filter_irrelevant_content(reddit_discussions, product_name, 'reddit')
        news_articles = self._filter_irrelevant_content(news_articles, product_name, 'news')

        # Generate insights using LLM
        print("🤖 Generating insights with LLM...")
        key_findings = self.summarize_with_llm(all_results, product_name)
        red_flags = self.detect_red_flags(all_results, product_name)
        overall_sentiment = self._analyze_sentiment(all_results, product_name)

        return {
            'external_reviews': external_reviews,
            'comparison_articles': comparison_articles,
            'issue_discussions': self._categorize_results(issues['results'], 'issue'),
            'reddit_discussions': reddit_discussions,
            'news_articles': news_articles,
            'video_reviews': video_reviews,
            'key_findings': key_findings,
            'red_flags': red_flags,
            'overall_sentiment': overall_sentiment,
            'total_sources': len(all_results),
            'metadata': {
                'review_count': len(external_reviews),
                'comparison_count': len(comparison_articles),
                'issue_count': len(issues['results']),
                'reddit_count': len(reddit_discussions),
                'news_count': len(news_articles),
                'video_count': len(video_reviews)
            }
        }

    def _search_serper(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Perform search using Serper API

        Args:
            query: Search query
            num_results: Number of results to fetch

        Returns:
            List of search results
        """
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'location': 'India',
            'num': num_results
        }

        try:
            response = requests.post(
                self.search_endpoint,
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
                    'source': self._extract_domain(result.get('link', '')),
                    'position': result.get('position', 0)
                })

            return formatted_results

        except Exception as e:
            print(f"❌ Serper search error: {str(e)}")
            return []

    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'Unknown'

    def _is_source_platform_url(self, url: str, source_platform: str) -> bool:
        """
        Check if URL is from the source platform

        Args:
            url: URL to check
            source_platform: Source platform name (e.g., "Amazon", "Flipkart")

        Returns:
            True if URL is from source platform, False otherwise
        """
        if not source_platform:
            return False

        url_lower = url.lower()
        platform_lower = source_platform.lower()

        # Platform-specific domain checks
        if platform_lower == "amazon":
            return "amazon.in" in url_lower or "amazon.com" in url_lower
        elif platform_lower == "flipkart":
            return "flipkart.com" in url_lower
        elif platform_lower == "ebay":
            return "ebay.in" in url_lower or "ebay.com" in url_lower
        elif platform_lower == "walmart":
            return "walmart.com" in url_lower
        elif platform_lower == "myntra":
            return "myntra.com" in url_lower
        elif platform_lower == "snapdeal":
            return "snapdeal.com" in url_lower

        return False

    def _filter_source_platform(self, results: List[Dict], source_platform: str) -> Tuple[List[Dict], int]:
        """
        Filter out results from source platform

        Args:
            results: List of search results
            source_platform: Source platform to exclude

        Returns:
            Tuple of (filtered results, count of filtered items)
        """
        if not source_platform:
            return results, 0

        filtered = []
        filtered_count = 0

        for result in results:
            url = result.get('url', '')
            if not self._is_source_platform_url(url, source_platform):
                filtered.append(result)
            else:
                filtered_count += 1

        return filtered, filtered_count

    def _extract_video_reviews(self, results: List[Dict]) -> List[Dict]:
        """Extract YouTube video reviews from search results"""
        videos = []

        for result in results:
            url = result.get('url', '')
            if 'youtube.com' in url or 'youtu.be' in url:
                videos.append({
                    'title': result.get('title', ''),
                    'url': url,
                    'channel': result.get('source', ''),
                    'snippet': result.get('snippet', '')
                })

        return videos

    def _categorize_results(self, results: List[Dict], category: str) -> List[Dict]:
        """Categorize and format search results"""
        categorized = []

        for result in results:
            categorized.append({
                'source': result.get('source', ''),
                'link': result.get('url', ''),  # Use 'link' for frontend compatibility
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'date': result.get('date', ''),
                'category': category
            })

        return categorized

    def _filter_irrelevant_content(self, results: List[Dict], product_name: str, content_type: str) -> List[Dict]:
        """
        Use LLM to filter out irrelevant external reviews and comparisons

        Args:
            results: List of external content (reviews or comparisons)
            product_name: Name of the product
            content_type: 'review' or 'comparison'

        Returns:
            Filtered list of relevant content
        """
        if not results:
            return []

        # Prepare content for LLM evaluation
        context = f"Product: {product_name}\n\n"
        context += f"Content Type: {content_type}\n\n"
        context += "Content to evaluate:\n\n"

        for i, result in enumerate(results, 1):
            context += f"{i}. Title: {result.get('title', '')}\n"
            context += f"   Source: {result.get('source', '')}\n"
            context += f"   Snippet: {result.get('snippet', '')}\n\n"

        if content_type == 'review':
            prompt = get_review_filter_prompt(context, product_name)
        elif content_type == 'reddit':
            prompt = get_reddit_filter_prompt(context, product_name)
        elif content_type == 'news':
            prompt = get_news_filter_prompt(context, product_name)
        else:  # comparison
            prompt = get_comparison_filter_prompt(context, product_name)

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip().upper()

            # Parse the response
            if result_text == "NONE" or "NONE" in result_text:
                print(f"   ⚠️ LLM filtered out all {content_type}s as irrelevant")
                return []

            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', result_text)
            relevant_indices = set(int(n) for n in numbers if n.isdigit())

            # Filter results based on LLM's evaluation
            filtered_results = [
                result for i, result in enumerate(results, 1)
                if i in relevant_indices
            ]

            removed_count = len(results) - len(filtered_results)
            if removed_count > 0:
                print(f"   ✓ Filtered out {removed_count} irrelevant {content_type}(s)")

            return filtered_results

        except Exception as e:
            print(f"   ❌ Error filtering {content_type}s: {str(e)}")
            # Return all results if filtering fails
            return results

    def summarize_with_llm(self, search_results: List[Dict], product_name: str) -> List[str]:
        """
        Use Gemini to summarize key findings from search results

        Args:
            search_results: List of search results
            product_name: Name of the product

        Returns:
            List of key findings
        """
        if not search_results:
            return ["No external information found"]

        # Prepare context for LLM
        context = f"Product: {product_name}\n\n"
        context += "External Search Results:\n\n"

        for i, result in enumerate(search_results[:20], 1):  # Limit to top 20
            context += f"{i}. Title: {result.get('title', '')}\n"
            context += f"   Source: {result.get('source', '')}\n"
            context += f"   Snippet: {result.get('snippet', '')}\n\n"

        prompt = get_key_findings_prompt(context, product_name)

        try:
            response = self.model.generate_content(prompt)
            findings_text = response.text.strip()

            # Parse findings into list
            findings = []
            for line in findings_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering/bullets
                    finding = line.lstrip('0123456789.-•) ').strip()
                    if finding:
                        findings.append(finding)

            return findings if findings else ["Analysis completed but no specific findings extracted"]

        except Exception as e:
            print(f"❌ LLM summarization error: {str(e)}")
            return [f"Error generating summary: {str(e)}"]

    def detect_red_flags(self, search_results: List[Dict], product_name: str) -> List[str]:
        """
        Use Gemini to detect red flags and warnings

        Args:
            search_results: List of search results
            product_name: Name of the product

        Returns:
            List of red flags
        """
        if not search_results:
            return []

        # Prepare context
        context = f"Product: {product_name}\n\n"
        context += "Search Results to Analyze:\n\n"

        for i, result in enumerate(search_results[:20], 1):
            context += f"{i}. {result.get('title', '')}\n"
            context += f"   {result.get('snippet', '')}\n\n"

        prompt = get_red_flags_prompt(context, product_name)

        try:
            response = self.model.generate_content(prompt)
            flags_text = response.text.strip()

            # Parse red flags
            red_flags = []

            if "no major red flags" in flags_text.lower() or "no significant red flags" in flags_text.lower():
                return []

            for line in flags_text.split('\n'):
                line = line.strip()
                if line and ('⚠️' in line or 'warning' in line.lower() or 'red flag' in line.lower()):
                    flag = line.replace('⚠️', '').strip()
                    if flag and not flag.lower().startswith('no'):
                        red_flags.append(flag)

            return red_flags

        except Exception as e:
            print(f"❌ Red flag detection error: {str(e)}")
            return []

    def _analyze_sentiment(self, search_results: List[Dict], product_name: str) -> Dict[str, str]:
        """
        Analyze overall sentiment from external sources

        Args:
            search_results: List of search results
            product_name: Name of the product

        Returns:
            Dict with sentiment, confidence, and summary
        """
        if not search_results:
            return {
                "sentiment": "unknown",
                "confidence": "low",
                "summary": "No external data available for sentiment analysis"
            }

        context = f"Product: {product_name}\n\n"
        for result in search_results[:15]:
            context += f"- {result.get('title', '')}: {result.get('snippet', '')}\n"

        prompt = get_sentiment_analysis_prompt(context, product_name)

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Try to parse JSON
            import json
            import re

            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{[^}]+\}', result_text)
            if json_match:
                sentiment_data = json.loads(json_match.group())
                return {
                    "sentiment": sentiment_data.get("sentiment", "mixed"),
                    "confidence": sentiment_data.get("confidence", "medium"),
                    "summary": sentiment_data.get("summary", "Mixed opinions found across sources")
                }
            else:
                # Fallback if JSON parsing fails
                sentiment = "mixed"
                if 'positive' in result_text.lower():
                    sentiment = 'positive'
                elif 'negative' in result_text.lower():
                    sentiment = 'negative'

                return {
                    "sentiment": sentiment,
                    "confidence": "medium",
                    "summary": result_text[:200]  # Use first 200 chars as summary
                }

        except Exception as e:
            print(f"❌ Sentiment analysis error: {str(e)}")
            return {
                "sentiment": "unknown",
                "confidence": "low",
                "summary": f"Error analyzing sentiment: {str(e)}"
            }
