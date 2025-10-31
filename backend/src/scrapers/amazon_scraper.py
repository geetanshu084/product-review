"""
Amazon Product Scraper
Implements BaseScraper interface for Amazon e-commerce platform
"""

import re
import time
import random
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from src.llm_extractor import LLMProductExtractor


class AmazonScraper(BaseScraper):
    """Scrapes product information and reviews from Amazon"""

    # Rotate between multiple realistic user agents
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    ]

    def __init__(self):
        """Initialize Amazon scraper with anti-bot evasion"""
        self.session = requests.Session()

        # Select a random user agent for this session
        self.user_agent = random.choice(self.USER_AGENTS)

        # Build realistic headers
        self.headers = self._build_headers()
        self.session.headers.update(self.headers)

        # Initialize LLM extractor
        self.llm_extractor = LLMProductExtractor()

        # Request count for realistic delays
        self.request_count = 0

    def _build_headers(self) -> Dict[str, str]:
        """Build realistic browser headers"""
        return {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def _realistic_delay(self):
        """Add realistic human-like delays between requests"""
        self.request_count += 1

        # Random delay between 1-3 seconds
        delay = random.uniform(1.0, 3.0)

        # Add longer delay every 3rd request to mimic human behavior
        if self.request_count % 3 == 0:
            delay += random.uniform(1.0, 2.0)

        time.sleep(delay)

    def _detect_captcha(self, response: requests.Response) -> bool:
        """Detect if Amazon is showing a CAPTCHA page"""
        content = response.text.lower()

        # Check for common CAPTCHA indicators
        captcha_indicators = [
            'captcha',
            'robot check',
            'enter the characters you see',
            'type the characters',
            'sorry, we just need to make sure',
            'automated access',
        ]

        # Very short responses are suspicious
        if len(response.text) < 10000:
            for indicator in captcha_indicators:
                if indicator in content:
                    return True

        return False

    def get_platform_name(self) -> str:
        """Returns platform name"""
        return "amazon"

    def validate_url(self, url: str) -> bool:
        """Validate if URL is a valid Amazon product URL"""
        if not url or not isinstance(url, str):
            return False

        amazon_domains = ['amazon.com', 'amazon.in', 'amazon.co.uk', 'amazon.de', 'amazon.fr']
        is_amazon = any(domain in url.lower() for domain in amazon_domains)
        has_asin = self.extract_product_id(url) is not None

        return is_amazon and has_asin

    def extract_product_id(self, url: str) -> Optional[str]:
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

    def scrape_product(self, url: str) -> Dict:
        """
        Scrape complete product information from Amazon product page

        Args:
            url: Amazon product URL

        Returns:
            Dictionary containing product data

        Raises:
            ValueError: If URL is invalid or CAPTCHA detected
            requests.exceptions.RequestException: If scraping fails
        """
        if not self.validate_url(url):
            raise ValueError("Invalid Amazon URL. Please provide a valid product URL.")

        asin = self.extract_product_id(url)

        try:
            # Add realistic delay before first request
            self._realistic_delay()

            # Fetch product page with realistic browser behavior
            response = self.session.get(url, timeout=20)
            response.raise_for_status()

            # Check for CAPTCHA/bot detection
            if self._detect_captcha(response):
                raise ValueError(
                    "Amazon has detected automated access for this product. "
                    "This usually happens with high-demand items like smartphones. "
                    "The product may require manual access on Amazon.in. "
                    f"Product ASIN: {asin}"
                )

            soup = BeautifulSoup(response.content, 'lxml')

            # Extract product data
            product_data = {
                'platform': self.get_platform_name(),
                'product_id': asin,  # Generic product ID
                'asin': asin,  # Amazon-specific ASIN (for backward compatibility)
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
            try:
                print("🤖 Enhancing data with LLM extraction...")
                # Pass BeautifulSoup object directly instead of raw HTML to avoid double parsing
                llm_data = self.llm_extractor.extract_product_data(soup, url)

                # Merge LLM data with traditional scraping
                product_data = self._merge_product_data(product_data, llm_data)
                print("✓ LLM enhancement complete")
            except Exception as e:
                print(f"⚠ LLM enhancement failed: {str(e)}")

            return product_data

        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to scrape product. The page might be unavailable or blocked. Error: {str(e)}"
            )

    def _merge_product_data(self, traditional_data: Dict, llm_data: Dict) -> Dict:
        """Merge traditional scraping data with LLM-extracted data"""
        merged = traditional_data.copy()

        # Add bank_offers from LLM
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

        # Merge specifications
        if llm_data.get('specifications'):
            if not merged.get('specifications'):
                merged['specifications'] = {}
            merged['specifications'].update(llm_data['specifications'])

        # Merge product_details
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
                return self.clean_text(element.get_text())

        return "Title not found"

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Extract brand name"""
        brand_selectors = [
            {'id': 'bylineInfo'},
            {'class': 'po-brand'},
            {'class': 'a-size-base po-break-word'}
        ]

        for selector in brand_selectors:
            element = soup.find('a', selector) or soup.find('span', selector)
            if element:
                text = element.get_text().strip()
                text = text.replace('Brand:', '').replace('Visit the', '').replace('Store', '').strip()
                if text:
                    return self.clean_text(text)

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
                parsed = self.parse_rating(text)
                if parsed:
                    return parsed

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
                return self.clean_text(element.get_text())

        return "Description not available"

    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract product features/bullet points"""
        features = []

        feature_div = soup.find('div', {'id': 'feature-bullets'})
        if feature_div:
            feature_items = feature_div.find_all('span', {'class': 'a-list-item'})
            for item in feature_items:
                text = self.clean_text(item.get_text())
                if text and len(text) > 5:
                    features.append(text)

        if not features:
            feature_list = soup.find('ul', {'class': 'a-unordered-list a-vertical a-spacing-mini'})
            if feature_list:
                items = feature_list.find_all('li')
                for item in items:
                    text = self.clean_text(item.get_text())
                    if text and len(text) > 5:
                        features.append(text)

        return features[:10]

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
                return self.clean_text(element.get_text())

        return "Seller not found"

    def _extract_seller_rating(self, soup: BeautifulSoup) -> str:
        """Extract seller rating"""
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
        """Extract product specifications"""
        specifications = {}

        try:
            product_info_section = soup.find('div', {'id': 'productDetails_techSpec_section_1'})
            if product_info_section:
                rows = product_info_section.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = self.clean_text(header.get_text())
                        val = self.clean_text(value.get_text())
                        if key and val:
                            specifications[key] = val

            tech_details = soup.find('table', {'id': 'productDetails_techSpec_section_1'})
            if tech_details:
                rows = tech_details.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = self.clean_text(header.get_text())
                        val = self.clean_text(value.get_text())
                        if key and val:
                            specifications[key] = val

        except Exception as e:
            print(f"Error extracting specifications: {str(e)}")

        return specifications

    def _extract_product_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product details"""
        details = {}

        try:
            detail_sections = soup.find_all('div', {'id': re.compile(r'productDetails.*')})

            for section in detail_sections:
                list_items = section.find_all('li')
                for item in list_items:
                    text = item.get_text()
                    if ':' in text:
                        parts = text.split(':', 1)
                        if len(parts) == 2:
                            key = self.clean_text(parts[0])
                            value = self.clean_text(parts[1])
                            if key and value:
                                details[key] = value

                rows = section.find_all('tr')
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    if len(cols) == 2:
                        key = self.clean_text(cols[0].get_text())
                        value = self.clean_text(cols[1].get_text())
                        if key and value:
                            details[key] = value

        except Exception as e:
            print(f"Error extracting product details: {str(e)}")

        return details

    def _extract_technical_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract technical specifications"""
        tech_details = {}

        try:
            tech_table = soup.find('table', {'id': 'productDetails_techSpec_section_2'})
            if tech_table:
                rows = tech_table.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = self.clean_text(header.get_text())
                        val = self.clean_text(value.get_text())
                        if key and val:
                            tech_details[key] = val

            tech_section = soup.find('div', {'id': 'tech-spec-desktop'})
            if tech_section:
                rows = tech_section.find_all('tr')
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    if len(cols) == 2:
                        key = self.clean_text(cols[0].get_text())
                        value = self.clean_text(cols[1].get_text())
                        if key and value:
                            tech_details[key] = value

        except Exception as e:
            print(f"Error extracting technical details: {str(e)}")

        return tech_details

    def _extract_additional_information(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract additional product information"""
        additional_info = {}

        try:
            info_section = soup.find('div', {'id': 'productDetails_db_sections'})
            if info_section:
                rows = info_section.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        key = self.clean_text(header.get_text())
                        val = self.clean_text(value.get_text())
                        if key and val:
                            additional_info[key] = val

            detail_bullets = soup.find('div', {'id': 'detailBullets_feature_div'})
            if detail_bullets:
                list_items = detail_bullets.find_all('li')
                for item in list_items:
                    spans = item.find_all('span')
                    if len(spans) >= 2:
                        key = self.clean_text(spans[0].get_text().rstrip(':'))
                        value = self.clean_text(spans[1].get_text())
                        if key and value:
                            additional_info[key] = value

        except Exception as e:
            print(f"Error extracting additional information: {str(e)}")

        return additional_info

    def _extract_warranty(self, soup: BeautifulSoup) -> str:
        """Extract warranty information"""
        warranty_info = ""

        try:
            warranty_keywords = ['warranty', 'guarantee', 'guaranty']

            features = self._extract_features(soup)
            for feature in features:
                if any(keyword in feature.lower() for keyword in warranty_keywords):
                    warranty_info += feature + " "

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
            availability_elem = soup.find('div', {'id': 'availability'})
            if availability_elem:
                return self.clean_text(availability_elem.get_text())

            availability_span = soup.find('span', {'class': 'a-size-medium a-color-success'})
            if availability_span:
                return self.clean_text(availability_span.get_text())

            out_of_stock = soup.find('span', {'class': 'a-size-medium a-color-error'})
            if out_of_stock:
                return self.clean_text(out_of_stock.get_text())

        except Exception as e:
            print(f"Error extracting availability: {str(e)}")

        return "Availability not specified"

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product images from top carousel"""
        images = []

        try:
            print("\n🖼️  Extracting product images from top carousel...")

            scripts = soup.find_all('script', {'type': 'text/javascript'})
            for script in scripts:
                if script.string and ('colorImages' in script.string or 'ImageBlockATF' in script.string):
                    script_text = script.string

                    color_images_match = re.search(r'"colorImages":\s*\{[^}]*"initial":\s*\[([^\]]+)\]', script_text)
                    if color_images_match:
                        images_json = color_images_match.group(1)
                        large_urls = re.findall(r'"(?:large|hiRes)":\s*"([^"]+)"', images_json)
                        for url in large_urls:
                            if url and url.startswith('http') and url not in images:
                                images.append(url)
                                print(f"  ✓ Found image from colorImages: {url[:80]}...")

                    if not images:
                        hiRes_urls = re.findall(r'"hiRes":\s*"([^"]+)"', script_text)
                        for url in hiRes_urls:
                            if url and url.startswith('http') and url not in images:
                                images.append(url)
                                print(f"  ✓ Found image from hiRes: {url[:80]}...")

            if not images:
                print("  → Trying landing image selector...")
                landing_img = soup.find('img', {'id': 'landingImage'})
                if landing_img:
                    src = landing_img.get('data-old-hires') or landing_img.get('src')
                    if src and src.startswith('http'):
                        images.append(src)
                        print(f"  ✓ Found landing image: {src[:80]}...")

            if len(images) < 2:
                print("  → Searching imageBlock section...")
                image_block = soup.find('div', {'id': 'imageBlock'})
                if image_block:
                    alt_images = image_block.find('div', {'id': 'altImages'})
                    if alt_images:
                        thumb_items = alt_images.find_all('li', {'class': 'imageThumbnail'})
                        for item in thumb_items:
                            img_tag = item.find('img')
                            if img_tag:
                                large_url = img_tag.get('data-old-hires') or img_tag.get('src')
                                if large_url and large_url.startswith('http') and large_url not in images:
                                    full_url = self._convert_to_fullsize_image(large_url)
                                    images.append(full_url)
                                    print(f"  ✓ Found image from altImages: {full_url[:80]}...")

            if len(images) < 2:
                print("  → Searching imgTagWrapperDiv...")
                thumb_wrappers = soup.find_all('div', {'class': 'imgTagWrapper'})
                for wrapper in thumb_wrappers[:7]:
                    img = wrapper.find('img')
                    if img:
                        src = img.get('src') or img.get('data-src')
                        if src and src.startswith('http') and src not in images:
                            full_url = self._convert_to_fullsize_image(src)
                            images.append(full_url)
                            print(f"  ✓ Found image from imgTagWrapper: {full_url[:80]}...")

            filtered_images = []
            for img_url in images:
                url_lower = img_url.lower()
                if not any(keyword in url_lower for keyword in ['review', 'customer-image', 'ugc-image', 'user-image']):
                    filtered_images.append(img_url)
                else:
                    print(f"  ✗ Filtered out review/user image: {img_url[:80]}...")

            print(f"\n✓ Total product images extracted: {len(filtered_images)}\n")
            return filtered_images[:8]

        except Exception as e:
            print(f"❌ Error extracting images: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _convert_to_fullsize_image(self, thumbnail_url: str) -> str:
        """Convert Amazon thumbnail URL to full-size image URL"""
        full_size = thumbnail_url
        full_size = re.sub(r'_[AS][XYC][\d]+_', '_AC_SL1500_', full_size)
        full_size = re.sub(r'_AC_[A-Z]{2}[\d]+_', '_AC_SL1500_', full_size)
        return full_size

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract product category from breadcrumbs"""
        category = ""

        try:
            breadcrumbs = soup.find('ul', {'class': 'a-unordered-list a-horizontal a-size-small'})
            if breadcrumbs:
                items = breadcrumbs.find_all('li')
                categories = []
                for item in items:
                    link = item.find('a')
                    if link:
                        cat_text = self.clean_text(link.get_text())
                        if cat_text:
                            categories.append(cat_text)
                category = ' > '.join(categories)

            if not category:
                breadcrumb_div = soup.find('div', {'id': 'wayfinding-breadcrumbs_feature_div'})
                if breadcrumb_div:
                    links = breadcrumb_div.find_all('a')
                    categories = [self.clean_text(link.get_text()) for link in links if self.clean_text(link.get_text())]
                    category = ' > '.join(categories)

        except Exception as e:
            print(f"Error extracting category: {str(e)}")

        return category if category else "Category not found"

    def _scrape_reviews_from_product_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Scrape customer reviews from product page"""
        reviews = []

        try:
            review_divs = soup.find_all('div', {'data-hook': 'review'})

            if not review_divs:
                review_divs = soup.find_all('div', {'id': re.compile(r'customer_review-.*')})

            if not review_divs:
                reviews_section = soup.find('div', {'id': 'reviewsMedley'})
                if reviews_section:
                    review_divs = reviews_section.find_all('div', {'data-hook': 'review'})

            print(f"Found {len(review_divs)} review containers on product page")

            for review_div in review_divs:
                review_data = {
                    'title': self._extract_review_title(review_div),
                    'rating': self._extract_review_rating(review_div),
                    'text': self._extract_review_text(review_div),
                    'author': self._extract_review_author(review_div),
                    'date': self._extract_review_date(review_div),
                    'verified_purchase': self._extract_review_verified(review_div)
                }

                if review_data['text'] or review_data['title']:
                    reviews.append(review_data)
                    print(f"  - Extracted review: {review_data['title'][:50]}..." if review_data['title'] else f"  - Extracted review with rating: {review_data['rating']}")

        except Exception as e:
            print(f"Error scraping reviews from product page: {str(e)}")

        return reviews

    def _extract_review_title(self, review_div: BeautifulSoup) -> str:
        """Extract review title"""
        title_elem = review_div.find('a', {'data-hook': 'review-title'})
        if not title_elem:
            title_elem = review_div.find('span', {'data-hook': 'review-title'})

        if title_elem:
            return self.clean_text(title_elem.get_text())
        return ""

    def _extract_review_rating(self, review_div: BeautifulSoup) -> str:
        """Extract review rating"""
        rating_elem = review_div.find('i', {'data-hook': 'review-star-rating'})
        if not rating_elem:
            rating_elem = review_div.find('span', {'class': 'a-icon-alt'})

        if rating_elem:
            text = rating_elem.get_text().strip()
            parsed = self.parse_rating(text)
            if parsed:
                return parsed
        return ""

    def _extract_review_text(self, review_div: BeautifulSoup) -> str:
        """Extract review text"""
        text_elem = review_div.find('span', {'data-hook': 'review-body'})
        if text_elem:
            return self.clean_text(text_elem.get_text())
        return ""

    def _extract_review_author(self, review_div: BeautifulSoup) -> str:
        """Extract review author name"""
        author_elem = review_div.find('span', {'class': 'a-profile-name'})
        if author_elem:
            return self.clean_text(author_elem.get_text())
        return "Anonymous"

    def _extract_review_date(self, review_div: BeautifulSoup) -> str:
        """Extract review date"""
        date_elem = review_div.find('span', {'data-hook': 'review-date'})
        if date_elem:
            text = date_elem.get_text().strip()
            match = re.search(r'on (.+)$', text)
            if match:
                return match.group(1)
            return text
        return ""

    def _extract_review_verified(self, review_div: BeautifulSoup) -> bool:
        """Check if review is verified purchase"""
        verified_elem = review_div.find('span', {'data-hook': 'avp-badge'})
        return verified_elem is not None
