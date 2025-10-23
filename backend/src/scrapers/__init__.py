"""
Scrapers package for different e-commerce platforms
"""

from .base_scraper import BaseScraper
from .amazon_scraper import AmazonScraper
from .flipkart_scraper import FlipkartScraper
from .scraper_factory import ScraperFactory

__all__ = [
    'BaseScraper',
    'AmazonScraper',
    'FlipkartScraper',
    'ScraperFactory'
]
