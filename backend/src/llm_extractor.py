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
from src.prompts import get_product_extraction_prompt


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

    def clean_html_to_text(self, html_content: str) -> str:
        """
        Convert HTML to clean text, removing all HTML elements

        Args:
            html_content: Raw HTML content

        Returns:
            Clean text content
        """
        soup = BeautifulSoup(html_content, 'lxml')

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

    def extract_product_data(self, html_content: str, url: str) -> Dict:
        """
        Extract comprehensive product data using LLM

        Args:
            html_content: Raw HTML content from product page
            url: Product URL

        Returns:
            Dictionary containing all extracted product data
        """
        # Clean HTML to text
        print("Cleaning HTML content...")
        clean_text = self.clean_html_to_text(html_content)

        # Truncate if too long (to fit within token limits)
        max_chars = 50000
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars]
            print(f"Text truncated to {max_chars} characters")

        # Create extraction prompt
        prompt = self._create_extraction_prompt(clean_text, url)

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

    def _create_extraction_prompt(self, page_text: str, url: str) -> str:
        """
        Create prompt for LLM to extract product data

        Args:
            page_text: Clean text from product page
            url: Product URL

        Returns:
            Formatted prompt string
        """
        return get_product_extraction_prompt(page_text, url)


def test_llm_extractor():
    """Test the LLM extractor"""
    import requests
    from dotenv import load_dotenv

    load_dotenv()
    extractor = LLMProductExtractor()

    # Test URL
    test_url = "https://www.amazon.in/Native-Purifier-RO-Copper-Alkaline/dp/B0D7HG2GZD"

    print("Fetching product page...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(test_url, headers=headers, timeout=15)

    print("Extracting product data with LLM...")
    product_data = extractor.extract_product_data(response.content.decode('utf-8'), test_url)

    print("\n" + "="*60)
    print("EXTRACTED PRODUCT DATA")
    print("="*60)
    print(json.dumps(product_data, indent=2, ensure_ascii=False))

    # Save to file
    with open('llm_extracted_data.json', 'w', encoding='utf-8') as f:
        json.dump(product_data, f, indent=2, ensure_ascii=False)

    print("\n✓ Data saved to llm_extracted_data.json")


if __name__ == "__main__":
    test_llm_extractor()
