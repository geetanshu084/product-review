"""
Scraper Factory
Automatically selects and returns the appropriate scraper based on product URL
"""

from typing import Optional
from .base_scraper import BaseScraper
from .amazon_scraper import AmazonScraper
from .flipkart_scraper import FlipkartScraper


class ScraperFactory:
    """Factory class to create appropriate scraper based on URL"""

    # Registry of available scrapers
    _scrapers = [
        AmazonScraper,
        FlipkartScraper
    ]

    @classmethod
    def get_scraper(cls, url: str) -> BaseScraper:
        """
        Get the appropriate scraper for the given URL

        Args:
            url: Product URL to scrape

        Returns:
            Instance of appropriate scraper (AmazonScraper, FlipkartScraper, etc.)

        Raises:
            ValueError: If URL is not supported by any scraper
        """
        if not url or not isinstance(url, str):
            raise ValueError("Invalid URL: URL must be a non-empty string")

        # Try each scraper to find one that validates the URL
        for scraper_class in cls._scrapers:
            scraper = scraper_class()
            if scraper.validate_url(url):
                platform = scraper.get_platform_name()
                print(f"✓ Selected {platform} scraper for URL")
                return scraper

        # No scraper found for this URL
        raise ValueError(
            f"Unsupported URL: {url}\n"
            f"Supported platforms: {', '.join([s().get_platform_name() for s in cls._scrapers])}"
        )

    @classmethod
    def get_supported_platforms(cls) -> list:
        """
        Get list of supported platform names

        Returns:
            List of platform names (e.g., ["Amazon", "Flipkart"])
        """
        return [scraper_class().get_platform_name() for scraper_class in cls._scrapers]

    @classmethod
    def is_url_supported(cls, url: str) -> bool:
        """
        Check if URL is supported by any scraper

        Args:
            url: URL to check

        Returns:
            True if URL is supported, False otherwise
        """
        if not url or not isinstance(url, str):
            return False

        for scraper_class in cls._scrapers:
            scraper = scraper_class()
            if scraper.validate_url(url):
                return True

        return False
