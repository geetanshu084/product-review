"""
Advanced Amazon Scraper with Selenium for Enhanced Review Scraping
Handles JavaScript-loaded content and pagination
"""

import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent


class AdvancedAmazonScraper:
    """Advanced scraper using Selenium for comprehensive review extraction"""

    def __init__(self, headless: bool = True, max_reviews: int = 100):
        """
        Initialize the advanced scraper

        Args:
            headless: Run browser in headless mode (no UI)
            max_reviews: Maximum number of reviews to scrape (default: 100, max: 200)
        """
        self.headless = headless
        self.max_reviews = min(max_reviews, 200)  # Cap at 200
        self.driver = None
        self.wait = None

    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')

        # Essential options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        # Random user agent
        ua = UserAgent()
        chrome_options.add_argument(f'user-agent={ua.random}')

        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Setup driver - try multiple methods
        try:
            # Method 1: Use webdriver-manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"⚠ ChromeDriver installation via webdriver-manager failed: {str(e)}")
            print("  Trying direct Chrome initialization...")
            # Method 2: Try system Chrome
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                raise Exception(f"Failed to initialize Chrome WebDriver. Please ensure Chrome is installed. Error: {str(e2)}")

        # Execute CDP command to remove webdriver flag
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        # Setup wait with longer timeout
        self.wait = WebDriverWait(self.driver, 20)

        print("✓ Selenium WebDriver initialized")

    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            print("✓ WebDriver closed")

    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL"""
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'product/([A-Z0-9]{10})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _build_reviews_url(self, asin: str, domain: str = 'amazon.in') -> str:
        """Build Amazon reviews page URL"""
        if 'amazon.com' in domain:
            return f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
        else:  # amazon.in
            return f"https://www.amazon.in/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"

    def _scroll_page(self):
        """Scroll page to load dynamic content"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)

    def _parse_review_date(self, date_str: str) -> str:
        """
        Parse review date string to ISO format

        Examples:
            "Reviewed in India on 15 January 2024" -> "2024-01-15"
            "Reviewed in the United States on January 15, 2024" -> "2024-01-15"
        """
        try:
            # Remove "Reviewed in [Country] on " prefix
            date_str = re.sub(r'Reviewed in .* on ', '', date_str)

            # Try different date formats
            date_formats = [
                '%d %B %Y',      # 15 January 2024
                '%B %d, %Y',     # January 15, 2024
                '%d %b %Y',      # 15 Jan 2024
                '%b %d, %Y',     # Jan 15, 2024
            ]

            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            return date_str  # Return original if parsing fails
        except Exception:
            return date_str

    def _parse_rating(self, rating_str: str) -> int:
        """
        Parse rating from string

        Example: "5.0 out of 5 stars" -> 5
        """
        try:
            match = re.search(r'(\d+(?:\.\d+)?)', rating_str)
            if match:
                return int(float(match.group(1)))
            return 0
        except Exception:
            return 0

    def _parse_helpful_votes(self, helpful_text: str) -> int:
        """
        Parse helpful votes count

        Examples:
            "25 people found this helpful" -> 25
            "One person found this helpful" -> 1
        """
        try:
            if 'One person' in helpful_text or 'one person' in helpful_text:
                return 1

            match = re.search(r'(\d+)', helpful_text)
            if match:
                return int(match.group(1))

            return 0
        except Exception:
            return 0

    def _extract_review_from_element(self, review_element) -> Optional[Dict]:
        """Extract review data from a single review element"""
        try:
            review_data = {
                'text': '',
                'rating': 0,
                'title': '',
                'date': '',
                'verified_purchase': False,
                'helpful_votes': 0,
                'reviewer_name': ''
            }

            # Rating
            try:
                rating_element = review_element.find_element(By.CSS_SELECTOR, 'i[data-hook="review-star-rating"], i[data-hook="cmps-review-star-rating"]')
                rating_text = rating_element.get_attribute('class')
                review_data['rating'] = self._parse_rating(rating_text)
            except NoSuchElementException:
                pass

            # Title
            try:
                title_element = review_element.find_element(By.CSS_SELECTOR, 'a[data-hook="review-title"]')
                review_data['title'] = title_element.text.strip()
            except NoSuchElementException:
                pass

            # Review text
            try:
                text_element = review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="review-body"]')
                review_data['text'] = text_element.text.strip()
            except NoSuchElementException:
                pass

            # Date
            try:
                date_element = review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="review-date"]')
                review_data['date'] = self._parse_review_date(date_element.text)
            except NoSuchElementException:
                pass

            # Verified purchase
            try:
                review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="avp-badge"]')
                review_data['verified_purchase'] = True
            except NoSuchElementException:
                review_data['verified_purchase'] = False

            # Helpful votes
            try:
                helpful_element = review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="helpful-vote-statement"]')
                review_data['helpful_votes'] = self._parse_helpful_votes(helpful_element.text)
            except NoSuchElementException:
                review_data['helpful_votes'] = 0

            # Reviewer name
            try:
                name_element = review_element.find_element(By.CSS_SELECTOR, 'span.a-profile-name')
                review_data['reviewer_name'] = name_element.text.strip()
            except NoSuchElementException:
                pass

            # Only return if we have at least text or title
            if review_data['text'] or review_data['title']:
                return review_data

            return None

        except Exception as e:
            print(f"⚠ Error extracting review: {str(e)}")
            return None

    def _scrape_reviews_from_page(self) -> List[Dict]:
        """Scrape reviews from current page"""
        reviews = []

        try:
            # Try multiple selectors for review elements
            selectors = [
                'div[data-hook="review"]',
                'div.review',
                'div[id*="review"]'
            ]

            review_elements = []
            for selector in selectors:
                try:
                    # Wait for reviews to load with this selector
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    review_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if review_elements:
                        print(f"  Found {len(review_elements)} reviews using selector: {selector}")
                        break
                except TimeoutException:
                    continue

            if not review_elements:
                print("⚠ No reviews found with any selector")
                # Save screenshot for debugging
                try:
                    self.driver.save_screenshot('/tmp/amazon_scraper_debug.png')
                    print("  Debug screenshot saved to /tmp/amazon_scraper_debug.png")
                except:
                    pass
                return reviews

            # Scroll to load lazy content
            self._scroll_page()

            for review_element in review_elements:
                review_data = self._extract_review_from_element(review_element)
                if review_data:
                    reviews.append(review_data)

        except Exception as e:
            print(f"⚠ Error scraping page: {str(e)}")

        return reviews

    def _click_next_page(self) -> bool:
        """
        Click the next page button

        Returns:
            bool: True if successfully navigated to next page, False otherwise
        """
        try:
            # Find next page button
            next_button = self.driver.find_element(By.CSS_SELECTOR, 'li.a-last a')

            if 'a-disabled' in next_button.get_attribute('class'):
                return False  # No more pages

            # Click next button
            next_button.click()

            # Wait for page to load
            time.sleep(2)

            # Wait for reviews to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-hook="review"]')))

            return True

        except NoSuchElementException:
            return False
        except TimeoutException:
            print("⚠ Timeout waiting for next page to load")
            return False
        except Exception as e:
            print(f"⚠ Error navigating to next page: {str(e)}")
            return False

    def scrape_reviews(self, product_url: str, prioritize_verified: bool = True) -> Dict:
        """
        Scrape reviews with pagination

        Args:
            product_url: Amazon product URL
            prioritize_verified: If True, prioritize verified purchase reviews

        Returns:
            Dictionary with reviews list
        """
        try:
            # Setup driver
            self._setup_driver()

            # Extract ASIN
            asin = self._extract_asin_from_url(product_url)
            if not asin:
                raise ValueError("Could not extract ASIN from URL")

            # Determine domain
            domain = 'amazon.in' if 'amazon.in' in product_url else 'amazon.com'

            # Build reviews URL
            reviews_url = self._build_reviews_url(asin, domain)

            print(f"🔄 Scraping reviews for ASIN: {asin}")
            print(f"   URL: {reviews_url}")
            print(f"   Target: {self.max_reviews} reviews")

            # Navigate to reviews page
            self.driver.get(reviews_url)

            # Wait longer for JavaScript to execute and render reviews
            time.sleep(5)

            # Scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)

            all_reviews = []
            page_num = 1

            while len(all_reviews) < self.max_reviews:
                print(f"\n📄 Scraping page {page_num}...")

                # Scrape reviews from current page
                page_reviews = self._scrape_reviews_from_page()
                all_reviews.extend(page_reviews)

                print(f"   Total reviews collected: {len(all_reviews)}/{self.max_reviews}")

                # Check if we have enough reviews
                if len(all_reviews) >= self.max_reviews:
                    break

                # Try to navigate to next page
                if not self._click_next_page():
                    print("✓ No more pages available")
                    break

                page_num += 1

                # Safety limit
                if page_num > 20:  # Max 20 pages
                    print("⚠ Reached maximum page limit (20 pages)")
                    break

            # Trim to max_reviews
            all_reviews = all_reviews[:self.max_reviews]

            # Sort by verified purchases first if requested
            if prioritize_verified:
                all_reviews.sort(key=lambda x: (not x['verified_purchase'], -x['helpful_votes']))

            print(f"\n✅ Successfully scraped {len(all_reviews)} reviews")
            if prioritize_verified:
                verified_count = sum(1 for r in all_reviews if r['verified_purchase'])
                print(f"   Verified purchases: {verified_count}/{len(all_reviews)}")

            return {
                'reviews': all_reviews,
                'total_scraped': len(all_reviews),
                'asin': asin
            }

        except Exception as e:
            print(f"❌ Error scraping reviews: {str(e)}")
            return {
                'reviews': [],
                'total_scraped': 0,
                'error': str(e)
            }
        finally:
            self._close_driver()


if __name__ == "__main__":
    # Test the scraper
    import sys

    if len(sys.argv) < 2:
        print("Usage: python advanced_amazon_scraper.py <amazon_url> [max_reviews]")
        sys.exit(1)

    url = sys.argv[1]
    max_reviews = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    scraper = AdvancedAmazonScraper(headless=True, max_reviews=max_reviews)
    result = scraper.scrape_reviews(url)

    print(f"\n{'='*60}")
    print(f"Scraped {result['total_scraped']} reviews")
    if result['reviews']:
        print(f"\nFirst review:")
        print(f"  Title: {result['reviews'][0]['title']}")
        print(f"  Rating: {result['reviews'][0]['rating']}/5")
        print(f"  Date: {result['reviews'][0]['date']}")
        print(f"  Verified: {result['reviews'][0]['verified_purchase']}")
        print(f"  Text: {result['reviews'][0]['text'][:100]}...")
