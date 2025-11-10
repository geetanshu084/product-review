"""
Web Search Analyzer for External Product Reviews
Uses web search to find external reviews, comparisons, and issues
Uses configured LLM to summarize findings and detect red flags
"""

import os
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.llm_provider import get_llm
from src.utils.search import search
from src.utils.prompts import (
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
        """ Initialize web search analyzer """
        self.model = get_llm(temperature=0.5)

    def analyze_product(self, product_name: str, source_platform: str) -> Dict:
        """
        Perform comprehensive web search analysis for a product

        Args:
            product_name: Name of the product
            source_platform: Platform being analyzed (e.g., "amazon", "flipkart") - excluded from external reviews

        Returns:
            Complete analysis with reviews, comparisons, issues, and insights
        """
        print(f"🔍 Searching external sources for: {product_name}")

        # Run all search pipelines in parallel
        search_results = self._run_search_pipelines_parallel(product_name, source_platform)

        # Extract results
        external_reviews = search_results['external_reviews']
        comparison_articles = search_results['comparison_articles']
        issue_discussions = search_results['issue_discussions']
        reddit_discussions = search_results['reddit_discussions']
        news_articles = search_results['news_articles']

        # Combine all formatted results for video extraction and LLM analysis
        all_results = (
            external_reviews +
            comparison_articles +
            issue_discussions +
            reddit_discussions +
            news_articles
        )

        # Extract video reviews
        video_reviews = self._extract_video_reviews(all_results)

        # Run all LLM operations in parallel
        llm_results = self._run_llm_analysis_parallel(
            external_reviews, comparison_articles, reddit_discussions, news_articles,
            all_results, product_name
        )

        return {
            'external_reviews': llm_results['external_reviews'],
            'comparison_articles': llm_results['comparison_articles'],
            'issue_discussions': issue_discussions,
            'reddit_discussions': llm_results['reddit_discussions'],
            'news_articles': llm_results['news_articles'],
            'video_reviews': video_reviews,
            'key_findings': llm_results['key_findings'],
            'red_flags': llm_results['red_flags'],
            'overall_sentiment': llm_results['overall_sentiment'],
            'total_sources': len(all_results),
            'metadata': {
                'review_count': len(llm_results['external_reviews']),
                'comparison_count': len(llm_results['comparison_articles']),
                'issue_count': len(issue_discussions),
                'reddit_count': len(llm_results['reddit_discussions']),
                'news_count': len(llm_results['news_articles']),
                'video_count': len(video_reviews)
            }
        }

    def _run_search_pipelines_parallel(self, product_name: str, source_platform: str) -> Dict:
        """
        Run all search pipelines in parallel

        Args:
            product_name: Name of the product
            source_platform: Source platform to exclude

        Returns:
            Dictionary with all search results
        """
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit complete search pipelines (search → filter → format)
            pipeline_futures = {
                executor.submit(self._search_and_process, f"Reviews of {product_name}", 'reviews', source_platform): 'external_reviews',
                executor.submit(self._search_and_process, f"{product_name} vs alternatives comparison", 'comparisons', source_platform): 'comparison_articles',
                executor.submit(self._search_and_process, f"{product_name} problems issues complaints", 'issues', source_platform): 'issue_discussions',
                executor.submit(self._search_and_process, f"{product_name} site:reddit.com", 'reddit', source_platform): 'reddit_discussions',
                executor.submit(self._search_and_process, f"{product_name} news launch announcement", 'news', source_platform): 'news_articles'
            }

            # Collect results
            results = {}
            for future in as_completed(pipeline_futures):
                result_key = pipeline_futures[future]
                results[result_key] = future.result()

        return {
            'external_reviews': results['external_reviews'],
            'comparison_articles': results['comparison_articles'],
            'issue_discussions': results['issue_discussions'],
            'reddit_discussions': results['reddit_discussions'],
            'news_articles': results['news_articles']
        }

    def _shorten_product_name(self, product_name: str) -> str:
        """Shorten product name for better search results"""
        import re

        # Remove filler phrases
        remove_phrases = [
            r'\|.*?warranty', r'\|.*?years?', r'\|.*?service',
            r'no service for.*?\|', r'\d+-year.*?\|', r'\d+-in-\d+.*?\|',
            r'smart iot.*?\|', r'ro\+uv\+.*?\|',
        ]

        shortened = product_name
        for phrase in remove_phrases:
            shortened = re.sub(phrase, '', shortened, flags=re.IGNORECASE)

        # Take first 2 meaningful parts
        parts = [p.strip() for p in shortened.split('|') if len(p.strip()) > 10][:2]
        result = ' '.join(parts) if parts else product_name[:100]
        return ' '.join(result.split())

    def _search_and_process(self, query: str, search_type: str, source_platform: str) -> List[Dict]:
        """
        Complete search pipeline: search → filter → format

        Args:
            query: Search query
            search_type: Type of search ('reviews', 'comparisons', 'issues', 'reddit', 'news')
            source_platform: Source platform to exclude

        Returns:
            List of formatted results
        """
        # Shorten the query if it's too long (extract product name from query)
        if len(query) > 150:
            # Extract product name from query patterns like "Reviews of PRODUCT" or "PRODUCT vs"
            import re
            for pattern in [r'Reviews of (.+)', r'(.+) vs alternatives', r'(.+) problems', r'(.+) site:reddit', r'(.+) news']:
                match = re.match(pattern, query, re.IGNORECASE)
                if match:
                    product_name = match.group(1).strip()
                    short_name = self._shorten_product_name(product_name)
                    query = query.replace(product_name, short_name)
                    break

        # Perform search
        results = search(query, num_results=10)

        # Filter Reddit results to ensure only Reddit URLs
        if search_type == 'reddit':
            results = [r for r in results if 'reddit.com' in r.get('url', '').lower()]

        # Filter and format for frontend
        return self._filter_and_format(results, source_platform)

    def _run_llm_analysis_parallel(
        self,
        external_reviews: List[Dict],
        comparison_articles: List[Dict],
        reddit_discussions: List[Dict],
        news_articles: List[Dict],
        all_results: List[Dict],
        product_name: str
    ) -> Dict:
        """
        Run all LLM operations in parallel for maximum performance

        Args:
            external_reviews: External review results
            comparison_articles: Comparison article results
            reddit_discussions: Reddit discussion results
            news_articles: News article results
            all_results: Combined results for analysis
            product_name: Name of the product

        Returns:
            Dictionary with all LLM results (filtered content + analysis insights)
        """
        print("🧹 Filtering irrelevant content & generating insights with LLM (7 parallel operations)...")

        with ThreadPoolExecutor(max_workers=7) as executor:
            # Submit all 7 LLM operations
            futures = {
                # 4 filtering operations
                executor.submit(self._filter_irrelevant_content, external_reviews, product_name, 'review'): 'external_reviews',
                executor.submit(self._filter_irrelevant_content, comparison_articles, product_name, 'comparison'): 'comparison_articles',
                executor.submit(self._filter_irrelevant_content, reddit_discussions, product_name, 'reddit'): 'reddit_discussions',
                executor.submit(self._filter_irrelevant_content, news_articles, product_name, 'news'): 'news_articles',
                # 3 analysis operations
                executor.submit(self.summarize_with_llm, all_results, product_name): 'key_findings',
                executor.submit(self.detect_red_flags, all_results, product_name): 'red_flags',
                executor.submit(self._analyze_sentiment, all_results, product_name): 'overall_sentiment'
            }

            # Collect results
            results = {}
            for future in as_completed(futures):
                result_key = futures[future]
                results[result_key] = future.result()

        return results

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

    def _filter_and_format(self, results: List[Dict], source_platform: str) -> List[Dict]:
        """
        Filter out source platform URLs and format for frontend in one pass

        Args:
            results: List of search results
            source_platform: Source platform to exclude

        Returns:
            Filtered and formatted results (url renamed to link)
        """
        formatted = []
        for result in results:
            # Skip results from source platform
            if source_platform and self._is_source_platform_url(result.get('url', ''), source_platform):
                continue

            # Format for frontend
            formatted.append({
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'link': result.get('url', ''),  # Rename for frontend compatibility
                'source': result.get('source', ''),
                'date': result.get('date', '')
            })

        return formatted

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
            response = self.model.invoke(prompt)
            result_text = response.content.strip().upper()

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
            response = self.model.invoke(prompt)
            findings_text = response.content.strip()

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
            response = self.model.invoke(prompt)
            flags_text = response.content.strip()

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
            response = self.model.invoke(prompt)
            result_text = response.content.strip()

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
