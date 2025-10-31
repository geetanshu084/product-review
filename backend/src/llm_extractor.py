"""
LLM-Based Product Data Extractor
Uses configured LLM provider to intelligently extract ALL product information from page content
"""

import json
import os
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
from src.llm_provider import get_llm
from src.utils.prompts import get_product_extraction_prompt


class LLMProductExtractor:
    """Uses LLM to extract comprehensive product data from HTML content"""

    def __init__(self):
        """
        Initialize the LLM extractor

        All configuration is read from environment variables:
        - LLM_PROVIDER: LLM provider to use (google, openai, anthropic, etc.)
        - LLM_MODEL: Model name (provider-specific)
        - GOOGLE_API_KEY, OPENAI_API_KEY, etc.: Provider-specific API keys
        """
        self.llm = get_llm(
            temperature=0.1  # Low temperature for factual extraction
        )

    def clean_html_to_text(self, soup: BeautifulSoup) -> str:
        """
        Convert BeautifulSoup object to clean text, removing all HTML elements

        Args:
            soup: BeautifulSoup object

        Returns:
            Clean text content
        """
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Extract comprehensive product data using LLM

        Args:
            soup: BeautifulSoup object from product page
            url: Product URL

        Returns:
            Dictionary containing all extracted product data
        """
        # Clean HTML to text
        print("Cleaning HTML content...")
        clean_text = self.clean_html_to_text(soup)

        # Truncate if too long (to fit within token limits)
        max_chars = 50000
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars]
            print(f"Text truncated to {max_chars} characters")

        # Create extraction prompt
        prompt = get_product_extraction_prompt(clean_text, url)

        print("Sending to LLM for extraction...")
        try:
            response = self.llm.invoke(prompt)
            result_text = response.content.strip()

            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'(\{.*\})', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = result_text

            # Parse JSON
            product_data = json.loads(json_str)
            print("✓ LLM extraction successful")

            return product_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {str(e)}")
            print(f"Response received: {result_text[:500]}...")
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            print(f"❌ LLM extraction error: {str(e)}")
            raise
