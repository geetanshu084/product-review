"""
LLM-Based Product Data Extractor
Uses Google Gemini to intelligently extract ALL product information from page content
"""

import json
import os
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMProductExtractor:
    """Uses LLM to extract comprehensive product data from HTML content"""

    def __init__(self, google_api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the LLM extractor

        Args:
            google_api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
        """
        api_key = google_api_key or os.getenv('GOOGLE_API_KEY')

        if not api_key:
            raise ValueError("Google API key is required")

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.1,  # Low temperature for factual extraction
            convert_system_message_to_human=True,
            google_api_key=api_key
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
        prompt = f"""You are an expert product data extraction system. Extract ALL available product information from the following Amazon product page content.

IMPORTANT: Return ONLY a valid JSON object. Do not include any explanatory text before or after the JSON.

Extract and structure the following information:

1. **Basic Information**: ASIN, title, brand, price, rating, total reviews, category, availability
2. **Product Details**: Dimensions, weight, color, material, model name/number, package contents, etc.
3. **Specifications**: Technical specs like capacity, power, voltage, size, compatibility, etc.
4. **Features**: All bullet points and key features mentioned
5. **Description**: Product description text
6. **Warranty**: Warranty information, duration, coverage
7. **Bank Offers**: All bank offers, credit card offers, EMI options, cashback deals
8. **Seller Information**: Seller name, rating, fulfillment method (FBA/FBM)
9. **Images**: Extract any image URLs mentioned
10. **Reviews Summary**: Extract key themes from customer reviews (positive/negative points)

PRODUCT URL: {url}

PRODUCT PAGE CONTENT:
{page_text}

Return the data in this EXACT JSON structure (include all fields, use null for missing data):

```json
{{
  "asin": "string or null",
  "url": "{url}",
  "title": "string or null",
  "brand": "string or null",
  "category": "string or null",
  "price": "string or null",
  "rating": "string (e.g., '4.5/5') or null",
  "total_reviews": "string or null",
  "availability": "string or null",

  "dimensions": "string or null",
  "weight": "string or null",
  "model_name": "string or null",
  "model_number": "string or null",
  "color": "string or null",
  "material": "string or null",

  "specifications": {{
    "key": "value"
  }},

  "product_details": {{
    "key": "value"
  }},

  "features": [
    "feature 1",
    "feature 2"
  ],

  "description": "string or null",

  "warranty": {{
    "duration": "string or null",
    "coverage": "string or null",
    "details": "string or null"
  }},

  "bank_offers": [
    {{
      "bank": "string",
      "offer_type": "string (e.g., 'Cashback', 'EMI', 'Discount')",
      "description": "string",
      "terms": "string or null"
    }}
  ],

  "seller_info": {{
    "name": "string or null",
    "rating": "string or null",
    "fulfillment": "string (FBA/FBM) or null"
  }},

  "images": [
    "url1",
    "url2"
  ],

  "review_summary": {{
    "positive_highlights": [
      "point 1",
      "point 2"
    ],
    "negative_highlights": [
      "point 1",
      "point 2"
    ],
    "common_themes": [
      "theme 1",
      "theme 2"
    ]
  }}
}}
```

IMPORTANT RULES:
1. Return ONLY the JSON object, no other text
2. Ensure all string values are properly escaped
3. Use null for missing data, not empty strings
4. Extract ALL available information from the page
5. For specifications and product_details, include as many key-value pairs as you can find
6. For bank_offers, extract ALL offers mentioned (credit card, debit card, EMI, cashback, etc.)
7. For review_summary, analyze the review snippets visible on the page
"""

        return prompt


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
