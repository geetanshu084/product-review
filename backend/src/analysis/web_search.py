"""
Web Search Analyzer for External Product Reviews
Uses Serper API to find external reviews, comparisons, and issues
Uses Gemini LLM to summarize findings and detect red flags
"""

import json
import requests
from typing import Dict, List, Optional
from urllib.parse import urlparse
import google.generativeai as genai


class WebSearchAnalyzer:
    """Analyzes products using external web search results"""

    def __init__(self, serper_api_key: str, gemini_api_key: str):
        """
        Initialize web search analyzer

        Args:
            serper_api_key: Serper API key for web search
            gemini_api_key: Google Gemini API key for summarization
        """
        self.serper_api_key = serper_api_key
        self.gemini_api_key = gemini_api_key

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
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
        query = f"{product_name} worth it reddit"
        results = self._search_serper(query, num_results=10)

        return {
            'query': query,
            'results': results,
            'count': len(results)
        }

    def analyze_product(self, product_name: str) -> Dict:
        """
        Perform comprehensive web search analysis for a product

        Args:
            product_name: Name of the product

        Returns:
            Complete analysis with reviews, comparisons, issues, and insights
        """
        print(f"🔍 Searching external sources for: {product_name}")

        # Perform all searches
        reviews = self.search_external_reviews(product_name)
        comparisons = self.search_comparisons(product_name)
        issues = self.search_issues(product_name)
        reddit = self.search_reddit_discussions(product_name)

        # Combine all results
        all_results = (
            reviews['results'] +
            comparisons['results'] +
            issues['results'] +
            reddit['results']
        )

        # Extract video reviews
        video_reviews = self._extract_video_reviews(all_results)

        # Categorize results
        external_reviews = self._categorize_results(reviews['results'], 'review')
        comparison_articles = self._categorize_results(comparisons['results'], 'comparison')

        # Generate insights using LLM
        print("🤖 Generating insights with LLM...")
        key_findings = self.summarize_with_llm(all_results, product_name)
        red_flags = self.detect_red_flags(all_results, product_name)
        overall_sentiment = self._analyze_sentiment(all_results, product_name)

        return {
            'external_reviews': external_reviews,
            'comparison_articles': comparison_articles,
            'issue_discussions': self._categorize_results(issues['results'], 'issue'),
            'reddit_discussions': self._categorize_results(reddit['results'], 'reddit'),
            'video_reviews': video_reviews,
            'key_findings': key_findings,
            'red_flags': red_flags,
            'overall_sentiment': overall_sentiment,
            'total_sources': len(all_results),
            'metadata': {
                'review_count': len(reviews['results']),
                'comparison_count': len(comparisons['results']),
                'issue_count': len(issues['results']),
                'reddit_count': len(reddit['results']),
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
                'url': result.get('url', ''),
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'date': result.get('date', ''),
                'category': category
            })

        return categorized

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

        prompt = f"""Analyze the following external search results about "{product_name}" and provide key findings.

{context}

Extract 5-10 key findings that would help a buyer make a decision. Focus on:
- Overall reception and reputation
- Common praises
- Common complaints
- Expert opinions
- Value for money consensus
- Reliability and build quality mentions

Return only the key findings as a numbered list, one finding per line."""

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

        prompt = f"""Analyze the following search results about "{product_name}" and identify any RED FLAGS or WARNINGS.

{context}

Look for:
- Product recalls or safety issues
- Widespread defects or failures
- Scam or counterfeit warnings
- Company reputation problems
- Major quality control issues
- False advertising claims
- Security or privacy concerns

Return ONLY serious red flags that would make someone reconsider purchasing. If no significant red flags are found, return "No major red flags detected".

List each red flag on a separate line starting with "⚠️"."""

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

    def _analyze_sentiment(self, search_results: List[Dict], product_name: str) -> str:
        """
        Analyze overall sentiment from external sources

        Args:
            search_results: List of search results
            product_name: Name of the product

        Returns:
            Sentiment: 'positive', 'negative', or 'mixed'
        """
        if not search_results:
            return "unknown"

        context = f"Product: {product_name}\n\n"
        for result in search_results[:15]:
            context += f"- {result.get('title', '')}: {result.get('snippet', '')}\n"

        prompt = f"""Based on these external search results about "{product_name}", what is the overall sentiment?

{context}

Respond with ONLY ONE WORD:
- "positive" if most sources are favorable
- "negative" if most sources are unfavorable
- "mixed" if there's a balance of opinions

Response:"""

        try:
            response = self.model.generate_content(prompt)
            sentiment = response.text.strip().lower()

            # Validate response
            if 'positive' in sentiment:
                return 'positive'
            elif 'negative' in sentiment:
                return 'negative'
            elif 'mixed' in sentiment:
                return 'mixed'
            else:
                return 'mixed'  # Default

        except Exception as e:
            print(f"❌ Sentiment analysis error: {str(e)}")
            return "unknown"
