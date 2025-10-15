"""
Amazon Product Scraper Module
Extracts product information and reviews from Amazon product pages
"""

import re
import time
import json
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import redis
from src.llm_extractor import LLMProductExtractor


class AmazonScraper:
    """Scrapes product information and reviews from Amazon"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

    def __init__(
        self,
        use_llm_extraction: bool = True,
        google_api_key: Optional[str] = None,
        use_cache: bool = True,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        cache_ttl: int = 86400  # 24 hours in seconds
    ):
        """
        Initialize the scraper

        Args:
            use_llm_extraction: Whether to use LLM for enhanced extraction (default: True)
            google_api_key: Google API key for LLM extraction
            use_cache: Whether to use Redis caching (default: True)
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            redis_password: Redis password (optional)
            cache_ttl: Cache time-to-live in seconds (default: 86400 = 24 hours)
        """
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.use_llm_extraction = use_llm_extraction
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl

        # Initialize Redis cache if enabled
        if self.use_cache:
            try:
                import os
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password or os.getenv('REDIS_PASSWORD'),
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                print("✓ Redis caching enabled (24-hour TTL)")
            except Exception as e:
                self.redis_client = None
                self.use_cache = False
                print(f"⚠ Redis caching disabled ({str(e)})")

        # Initialize LLM extractor if enabled
        if self.use_llm_extraction:
            try:
                import os
                api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
                if api_key:
                    self.llm_extractor = LLMProductExtractor(google_api_key=api_key)
                    print("✓ LLM extraction enabled")
                else:
                    self.llm_extractor = None
                    self.use_llm_extraction = False
                    print("⚠ LLM extraction disabled (no API key)")
            except Exception as e:
                self.llm_extractor = None
                self.use_llm_extraction = False
                print(f"⚠ LLM extraction disabled ({str(e)})")

    def extract_asin(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon product URL"""
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/ASIN/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def validate_url(self, url: str) -> bool:
        """Validate if URL is a valid Amazon product URL"""
        if not url or not isinstance(url, str):
            return False

        amazon_domains = ['amazon.com', 'amazon.in', 'amazon.co.uk', 'amazon.de', 'amazon.fr']
        is_amazon = any(domain in url.lower() for domain in amazon_domains)
        has_asin = self.extract_asin(url) is not None

        return is_amazon and has_asin

    def _extract_domain(self, url: str) -> str:
        """Extract Amazon domain from URL"""
        import re
        match = re.search(r'amazon\.(com|in|co\.uk|de|fr|ca|com\.au|es|it|co\.jp)', url.lower())
        if match:
            return f"amazon.{match.group(1)}"
        return "amazon.com"  # Default fallback

    def scrape_product(self, url: str) -> Dict:
        """
        Scrape complete product information from Amazon product page
        Uses Redis cache to avoid re-scraping same product within 24 hours

        Args:
            url: Amazon product URL

        Returns:
            Dictionary containing product data

        Raises:
            ValueError: If URL is invalid
            requests.exceptions.RequestException: If scraping fails
        """
        if not self.validate_url(url):
            raise ValueError("Invalid Amazon URL. Please provide a valid product URL.")

        asin = self.extract_asin(url)

        # Check cache first
        if self.use_cache and self.redis_client:
            cached_data = self._get_from_cache(asin)
            if cached_data:
                print(f"✓ Using cached data for ASIN: {asin} (from Redis)")
                return cached_data

        try:
            # Fetch product page
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            time.sleep(2)  # Respectful delay

            soup = BeautifulSoup(response.content, 'lxml')

            # Extract product data
            product_data = {
                'asin': asin,
                'url': url,
                'title': self._extract_title(soup),
                'brand': self._extract_brand(soup),
                'price': self._extract_price(soup),
                'rating': self._extract_rating(soup),
                'total_reviews': self._extract_total_reviews(soup),
                'description': self._extract_description(soup),
                'features': self._extract_features(soup),
                'seller_name': self._extract_seller_name(soup),
                'seller_rating': self._extract_seller_rating(soup),
                'specifications': self._extract_specifications(soup),
                'product_details': self._extract_product_details(soup),
                'technical_details': self._extract_technical_details(soup),
                'additional_information': self._extract_additional_information(soup),
                'warranty': self._extract_warranty(soup),
                'availability': self._extract_availability(soup),
                'images': self._extract_images(soup),
                'category': self._extract_category(soup),
                'reviews': []
            }

            # Scrape reviews from product page
            print(f"\n📄 Scraping reviews for ASIN: {asin}")
            reviews = self._scrape_reviews_from_product_page(soup)
            print(f"✓ Scraped {len(reviews)} reviews from product page\n")
            product_data['reviews'] = reviews

            # Use LLM extraction to enhance and fill missing data
            if self.use_llm_extraction and self.llm_extractor:
                try:
                    print("🤖 Enhancing data with LLM extraction...")
                    llm_data = self.llm_extractor.extract_product_data(response.content.decode('utf-8'), url)

                    # Merge LLM data with traditional scraping (LLM fills gaps + adds bank offers)
                    product_data = self._merge_product_data(product_data, llm_data)
                    print("✓ LLM enhancement complete")
                except Exception as e:
                    print(f"⚠ LLM enhancement failed: {str(e)}")
                    # Continue with traditional scraping data

            # Save to cache
            if self.use_cache and self.redis_client:
                self._save_to_cache(asin, product_data)
                print(f"✓ Cached data for ASIN: {asin} (TTL: 24 hours)")

            return product_data

        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to scrape product. The page might be unavailable or blocked. Error: {str(e)}"
            )

    def _get_from_cache(self, asin: str) -> Optional[Dict]:
        """
        Get product data from Redis cache

        Args:
            asin: Product ASIN

        Returns:
            Cached product data or None
        """
        try:
            cache_key = f"product:{asin}"
            cached_json = self.redis_client.get(cache_key)
            if cached_json:
                return json.loads(cached_json)
        except Exception as e:
            print(f"⚠ Cache read error: {str(e)}")
        return None

    def _save_to_cache(self, asin: str, product_data: Dict):
        """
        Save product data to Redis cache with 24-hour TTL

        Args:
            asin: Product ASIN
            product_data: Product data dictionary
        """
        try:
            cache_key = f"product:{asin}"
            product_json = json.dumps(product_data, ensure_ascii=False)
            self.redis_client.setex(cache_key, self.cache_ttl, product_json)
        except Exception as e:
            print(f"⚠ Cache write error: {str(e)}")

    def _merge_product_data(self, traditional_data: Dict, llm_data: Dict) -> Dict:
        """
        Merge traditional scraping data with LLM-extracted data
        Priority: Keep traditional data, use LLM to fill gaps and add new fields

        Args:
            traditional_data: Data from traditional HTML scraping
            llm_data: Data extracted by LLM

        Returns:
            Merged dictionary with best of both
        """
        merged = traditional_data.copy()

        # Add bank_offers from LLM (not available in traditional scraping)
        if 'bank_offers' in llm_data and llm_data['bank_offers']:
            merged['bank_offers'] = llm_data['bank_offers']
        else:
            merged['bank_offers'] = []

        # Add review_summary from LLM
        if 'review_summary' in llm_data and llm_data['review_summary']:
            merged['review_summary'] = llm_data['review_summary']

        # Fill gaps in basic info
        for key in ['title', 'brand', 'price', 'rating', 'total_reviews', 'category', 'availability']:
            if not merged.get(key) or merged.get(key) in ['N/A', 'not found', 'not available']:
                if llm_data.get(key):
                    merged[key] = llm_data[key]

        # Merge specifications (combine both sources)
        if llm_data.get('specifications'):
            if not merged.get('specifications'):
                merged['specifications'] = {}
            merged['specifications'].update(llm_data['specifications'])

        # Merge product_details (combine both sources)
        if llm_data.get('product_details'):
            if not merged.get('product_details'):
                merged['product_details'] = {}
            merged['product_details'].update(llm_data['product_details'])

        # Add structured warranty from LLM if better
        if llm_data.get('warranty') and isinstance(llm_data['warranty'], dict):
            merged['warranty_details'] = llm_data['warranty']

        # Use LLM dimensions/weight if not found traditionally
        if llm_data.get('dimensions') and not merged.get('product_details', {}).get('Product Dimensions'):
            if not merged.get('product_details'):
                merged['product_details'] = {}
            merged['product_details']['Product Dimensions'] = llm_data['dimensions']

        if llm_data.get('weight') and not merged.get('product_details', {}).get('Item Weight'):
            if not merged.get('product_details'):
                merged['product_details'] = {}
            merged['product_details']['Item Weight'] = llm_data['weight']

        print(f"  ✓ Added {len(merged.get('bank_offers', []))} bank offers from LLM")

        return merged

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title"""
        selectors = [
            ('id', 'productTitle'),
            ('class', 'product-title-word-break'),
            ('id', 'title')
        ]

        for selector_type, selector_value in selectors:
            if selector_type == 'id':
                element = soup.find(id=selector_value)
            else:
                element = soup.find(class_=selector_value)

            if element:
                return element.get_text().strip()

        return "Title not found"

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Extract brand name"""
        # Try multiple selectors
        brand_selectors = [
            {'id': 'bylineInfo'},
            {'class': 'po-brand'},
            {'class': 'a-size-base po-break-word'}
        ]

        for selector in brand_selectors:
            element = soup.find('a', selector) or soup.find('span', selector)
            if element:
                text = element.get_text().strip()
                # Clean up brand text
                text = text.replace('Brand:', '').replace('Visit the', '').replace('Store', '').strip()
                if text:
                    return text

        return "Brand not found"

    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract product price"""
        price_selectors = [
            ('class', 'a-price-whole'),
            ('class', 'a-offscreen'),
            ('id', 'priceblock_ourprice'),
            ('id', 'priceblock_dealprice'),
            ('class', 'a-price aok-align-center reinventPricePriceToPayMargin priceToPay')
        ]

        for selector_type, selector_value in price_selectors:
            if selector_type == 'id':
                element = soup.find(id=selector_value)
            else:
                element = soup.find(class_=selector_value)

            if element:
                price_text = element.get_text().strip()
                return price_text

        return "Price not available"

    def _extract_rating(self, soup: BeautifulSoup) -> str:
        """Extract overall rating"""
        rating_selectors = [
            ('class', 'a-icon-alt'),
            ('id', 'acrPopover'),
            ('class', 'a-size-base a-color-base')
        ]

        for selector_type, selector_value in rating_selectors:
            if selector_type == 'id':
                element = soup.find('span', id=selector_value)
            else:
                element = soup.find('span', class_=selector_value)

            if element:
                text = element.get_text().strip()
                # Extract rating number (e.g., "4.5 out of 5 stars")
                match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', text)
                if match:
                    return f"{match.group(1)}/5"
                elif 'out of 5' in text:
                    return text

        return "Rating not available"

    def _extract_total_reviews(self, soup: BeautifulSoup) -> str:
        """Extract total number of reviews"""
        review_selectors = [
            ('id', 'acrCustomerReviewText'),
            ('class', 'a-size-base a-link-normal')
        ]

        for selector_type, selector_value in review_selectors:
            if selector_type == 'id':
                element = soup.find(id=selector_value)
            else:
                element = soup.find('span', class_=selector_value)

            if element:
                text = element.get_text().strip()
                # Extract number (e.g., "1,234 ratings")
                match = re.search(r'([\d,]+)', text)
                if match:
                    return match.group(1)

        return "0"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        desc_selectors = [
            {'id': 'productDescription'},
            {'id': 'feature-bullets'},
            {'class': 'a-unordered-list a-vertical a-spacing-mini'}
        ]

        for selector in desc_selectors:
            element = soup.find('div', selector) or soup.find('ul', selector)
            if element:
                return element.get_text().strip()

        return "Description not available"

    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract product features/bullet points"""
        features = []

        # Try feature bullets section
        feature_div = soup.find('div', {'id': 'feature-bullets'})
        if feature_div:
            feature_items = feature_div.find_all('span', {'class': 'a-list-item'})
            for item in feature_items:
                text = item.get_text().strip()
                if text and len(text) > 5:  # Filter out empty or very short items
                    features.append(text)

        # If no features found, try alternate selector
        if not features:
            feature_list = soup.find('ul', {'class': 'a-unordered-list a-vertical a-spacing-mini'})
            if feature_list:
                items = feature_list.find_all('li')
                for item in items:
                    text = item.get_text().strip()
                    if text and len(text) > 5:
                        features.append(text)

        return features[:10]  # Limit to 10 features

    def _extract_seller_name(self, soup: BeautifulSoup) -> str:
        """Extract seller name"""
        seller_selectors = [
            {'id': 'sellerProfileTriggerId'},
            {'class': 'tabular-buybox-text'},
            {'id': 'merchantInfoFeature'}
        ]

        for selector in seller_selectors:
            element = soup.find('a', selector) or soup.find('span', selector)
            if element:
                return element.get_text().strip()

        return "Seller not found"

    def _extract_seller_rating(self, soup: BeautifulSoup) -> str:
        """Extract seller rating"""
        # Look for seller rating in merchant info
        merchant_div = soup.find('div', {'id': 'merchantInfoFeature'})
        if merchant_div:
            rating_span = merchant_div.find('span', {'class': 'a-icon-alt'})
            if rating_span:
                text = rating_span.get_text().strip()
                match = re.search(r'(\d+)%', text)
                if match:
                    return f"{match.group(1)}%"

        return "Rating not available"

    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product specifications from various sections"""
        specifications = {}

        try:
            # Try "Product information" section
            product_info_section = soup.find('div', {'id': 'productDetails_techSpec_section_1'})
            if product_info_section:
                rows = product_info_section.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = header.get_text().strip()
                        val = value.get_text().strip()
                        if key and val:
                            specifications[key] = val

            # Try alternate "Technical Details" table
            tech_details = soup.find('table', {'id': 'productDetails_techSpec_section_1'})
            if tech_details:
                rows = tech_details.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = header.get_text().strip()
                        val = value.get_text().strip()
                        if key and val:
                            specifications[key] = val

        except Exception as e:
            print(f"Error extracting specifications: {str(e)}")

        return specifications

    def _extract_product_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product details (dimensions, weight, etc.)"""
        details = {}

        try:
            # Look for "Product Details" section
            detail_sections = soup.find_all('div', {'id': re.compile(r'productDetails.*')})

            for section in detail_sections:
                # Try list format
                list_items = section.find_all('li')
                for item in list_items:
                    text = item.get_text()
                    if ':' in text:
                        parts = text.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key and value:
                                details[key] = value

                # Try table format
                rows = section.find_all('tr')
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    if len(cols) == 2:
                        key = cols[0].get_text().strip()
                        value = cols[1].get_text().strip()
                        if key and value:
                            details[key] = value

        except Exception as e:
            print(f"Error extracting product details: {str(e)}")

        return details

    def _extract_technical_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract technical specifications"""
        tech_details = {}

        try:
            # Look for technical details table
            tech_table = soup.find('table', {'id': 'productDetails_techSpec_section_2'})
            if tech_table:
                rows = tech_table.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = header.get_text().strip()
                        val = value.get_text().strip()
                        if key and val:
                            tech_details[key] = val

            # Try alternate selector for technical specs
            tech_section = soup.find('div', {'id': 'tech-spec-desktop'})
            if tech_section:
                rows = tech_section.find_all('tr')
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    if len(cols) == 2:
                        key = cols[0].get_text().strip()
                        value = cols[1].get_text().strip()
                        if key and value:
                            tech_details[key] = value

        except Exception as e:
            print(f"Error extracting technical details: {str(e)}")

        return tech_details

    def _extract_additional_information(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract additional product information"""
        additional_info = {}

        try:
            # Look for "Additional Information" section
            info_section = soup.find('div', {'id': 'productDetails_db_sections'})
            if info_section:
                rows = info_section.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = header.get_text().strip()
                        val = value.get_text().strip()
                        if key and val:
                            additional_info[key] = val

            # Try detail bullets format
            detail_bullets = soup.find('div', {'id': 'detailBullets_feature_div'})
            if detail_bullets:
                list_items = detail_bullets.find_all('li')
                for item in list_items:
                    spans = item.find_all('span')
                    if len(spans) >= 2:
                        key = spans[0].get_text().strip().rstrip(':')
                        value = spans[1].get_text().strip()
                        if key and value:
                            additional_info[key] = value

        except Exception as e:
            print(f"Error extracting additional information: {str(e)}")

        return additional_info

    def _extract_warranty(self, soup: BeautifulSoup) -> str:
        """Extract warranty information"""
        warranty_info = ""

        try:
            # Look for warranty in various places
            warranty_keywords = ['warranty', 'guarantee', 'guaranty']

            # Check product features
            features = self._extract_features(soup)
            for feature in features:
                if any(keyword in feature.lower() for keyword in warranty_keywords):
                    warranty_info += feature + " "

            # Check product details
            detail_sections = soup.find_all('div', {'id': re.compile(r'productDetails.*')})
            for section in detail_sections:
                text = section.get_text()
                if any(keyword in text.lower() for keyword in warranty_keywords):
                    lines = text.split('\n')
                    for line in lines:
                        if any(keyword in line.lower() for keyword in warranty_keywords):
                            warranty_info += line.strip() + " "

        except Exception as e:
            print(f"Error extracting warranty: {str(e)}")

        return warranty_info.strip() if warranty_info else "Warranty information not available"

    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract product availability status"""
        try:
            # Look for availability in stock status
            availability_elem = soup.find('div', {'id': 'availability'})
            if availability_elem:
                return availability_elem.get_text().strip()

            # Try alternate selector
            availability_span = soup.find('span', {'class': 'a-size-medium a-color-success'})
            if availability_span:
                return availability_span.get_text().strip()

            # Check for out of stock
            out_of_stock = soup.find('span', {'class': 'a-size-medium a-color-error'})
            if out_of_stock:
                return out_of_stock.get_text().strip()

        except Exception as e:
            print(f"Error extracting availability: {str(e)}")

        return "Availability not specified"

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product image URLs"""
        images = []

        try:
            # Try to find main image
            main_image = soup.find('img', {'id': 'landingImage'})
            if main_image and main_image.get('src'):
                images.append(main_image['src'])

            # Try alternate main image selector
            if not images:
                main_image = soup.find('img', {'data-old-hires': True})
                if main_image and main_image.get('data-old-hires'):
                    images.append(main_image['data-old-hires'])

            # Try to find thumbnail images
            thumbnails = soup.find_all('img', {'class': re.compile(r'.*thumb.*')})
            for thumb in thumbnails[:5]:  # Limit to 5 additional images
                if thumb.get('src') and thumb['src'] not in images:
                    images.append(thumb['src'])

        except Exception as e:
            print(f"Error extracting images: {str(e)}")

        return images

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract product category from breadcrumbs"""
        category = ""

        try:
            # Look for breadcrumbs
            breadcrumbs = soup.find('ul', {'class': 'a-unordered-list a-horizontal a-size-small'})
            if breadcrumbs:
                items = breadcrumbs.find_all('li')
                categories = []
                for item in items:
                    link = item.find('a')
                    if link:
                        cat_text = link.get_text().strip()
                        if cat_text:
                            categories.append(cat_text)
                category = ' > '.join(categories)

            # Try alternate selector
            if not category:
                breadcrumb_div = soup.find('div', {'id': 'wayfinding-breadcrumbs_feature_div'})
                if breadcrumb_div:
                    links = breadcrumb_div.find_all('a')
                    categories = [link.get_text().strip() for link in links if link.get_text().strip()]
                    category = ' > '.join(categories)

        except Exception as e:
            print(f"Error extracting category: {str(e)}")

        return category if category else "Category not found"

    def _extract_review_title(self, review_div: BeautifulSoup) -> str:
        """Extract review title"""
        title_elem = review_div.find('a', {'data-hook': 'review-title'})
        if not title_elem:
            title_elem = review_div.find('span', {'data-hook': 'review-title'})

        if title_elem:
            return title_elem.get_text().strip()
        return ""

    def _extract_review_rating(self, review_div: BeautifulSoup) -> str:
        """Extract review rating"""
        rating_elem = review_div.find('i', {'data-hook': 'review-star-rating'})
        if not rating_elem:
            rating_elem = review_div.find('span', {'class': 'a-icon-alt'})

        if rating_elem:
            text = rating_elem.get_text().strip()
            match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', text)
            if match:
                return f"{match.group(1)}/5"
        return ""

    def _extract_review_text(self, review_div: BeautifulSoup) -> str:
        """Extract review text"""
        text_elem = review_div.find('span', {'data-hook': 'review-body'})
        if text_elem:
            return text_elem.get_text().strip()
        return ""

    def _extract_review_author(self, review_div: BeautifulSoup) -> str:
        """Extract review author name"""
        author_elem = review_div.find('span', {'class': 'a-profile-name'})
        if author_elem:
            return author_elem.get_text().strip()
        return "Anonymous"

    def _extract_review_date(self, review_div: BeautifulSoup) -> str:
        """Extract review date"""
        date_elem = review_div.find('span', {'data-hook': 'review-date'})
        if date_elem:
            text = date_elem.get_text().strip()
            # Extract date from text like "Reviewed in the United States on January 1, 2024"
            match = re.search(r'on (.+)$', text)
            if match:
                return match.group(1)
            return text
        return ""

    def _extract_review_verified(self, review_div: BeautifulSoup) -> bool:
        """Check if review is verified purchase"""
        verified_elem = review_div.find('span', {'data-hook': 'avp-badge'})
        return verified_elem is not None

    def _scrape_reviews_from_product_page(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Scrape customer reviews directly from the product page HTML
        (doesn't require authentication, typically shows 5-10 reviews)

        Args:
            soup: BeautifulSoup object of the product page

        Returns:
            List of review dictionaries
        """
        reviews = []

        try:
            # Find review section on product page
            # Amazon product pages typically show a few top reviews
            review_divs = soup.find_all('div', {'data-hook': 'review'})

            # If not found, try alternate selectors for review containers
            if not review_divs:
                review_divs = soup.find_all('div', {'id': re.compile(r'customer_review-.*')})

            # If still not found, try looking in the reviews section
            if not review_divs:
                reviews_section = soup.find('div', {'id': 'reviewsMedley'})
                if reviews_section:
                    review_divs = reviews_section.find_all('div', {'data-hook': 'review'})

            print(f"Found {len(review_divs)} review containers on product page")

            # Extract reviews from found containers
            for review_div in review_divs:
                review_data = {
                    'title': self._extract_review_title(review_div),
                    'rating': self._extract_review_rating(review_div),
                    'text': self._extract_review_text(review_div),
                    'author': self._extract_review_author(review_div),
                    'date': self._extract_review_date(review_div),
                    'verified_purchase': self._extract_review_verified(review_div)
                }

                # Only add if we got at least some meaningful data
                if review_data['text'] or review_data['title']:
                    reviews.append(review_data)
                    print(f"  - Extracted review: {review_data['title'][:50]}..." if review_data['title'] else f"  - Extracted review with rating: {review_data['rating']}")

        except Exception as e:
            print(f"Error scraping reviews from product page: {str(e)}")

        return reviews
