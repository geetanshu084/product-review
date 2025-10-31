"""
Base Scraper Interface
Defines the contract that all platform scrapers must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import re


class BaseScraper(ABC):
    """Abstract base class for all e-commerce platform scrapers"""

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        Validate if the URL belongs to this platform

        Args:
            url: Product URL to validate

        Returns:
            True if URL is valid for this platform, False otherwise
        """
        pass

    @abstractmethod
    def extract_product_id(self, url: str) -> Optional[str]:
        """
        Extract unique product identifier from URL

        Args:
            url: Product URL

        Returns:
            Product ID (e.g., ASIN for Amazon, FSN for Flipkart) or None if not found
        """
        pass

    @abstractmethod
    def scrape_product(self, url: str) -> Dict:
        """
        Scrape product data from the platform

        Args:
            url: Product URL

        Returns:
            Dictionary containing product data

        Raises:
            ValueError: If URL is invalid
            Exception: If scraping fails
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the name of the platform

        Returns:
            Platform name (e.g., "Amazon", "Flipkart")
        """
        pass

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def parse_price(self, price_text: str) -> Optional[str]:
        """
        Parse price from text

        Args:
            price_text: Price text to parse

        Returns:
            Formatted price string or None
        """
        if not price_text:
            return None

        # Extract numeric price
        price_match = re.search(r'[\d,]+\.?\d*', price_text)
        if price_match:
            return price_match.group()

        return None

    def parse_rating(self, rating_text: str) -> Optional[str]:
        """
        Parse rating from text

        Args:
            rating_text: Rating text to parse

        Returns:
            Formatted rating string or None
        """
        if not rating_text:
            return None

        # Extract numeric rating
        rating_match = re.search(r'(\d+\.?\d*)\s*out of\s*(\d+)', rating_text, re.IGNORECASE)
        if rating_match:
            return f"{rating_match.group(1)}/{rating_match.group(2)}"

        # Try simple numeric rating
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            return f"{rating_match.group(1)}/5"

        return None
