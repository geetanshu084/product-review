"""
Flipkart Product Scraper
Implements BaseScraper interface for Flipkart e-commerce platform
"""

import re
import time
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from src.llm_extractor import LLMProductExtractor


class FlipkartScraper(BaseScraper):
    """Scrapes product information and reviews from Flipkart"""

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

    def __init__(self):
        """Initialize Flipkart scraper"""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.llm_extractor = LLMProductExtractor()

    def get_platform_name(self) -> str:
        """Returns platform name"""
        return "flipkart"

    def validate_url(self, url: str) -> bool:
        """Validate if URL is a valid Flipkart product URL"""
        if not url or not isinstance(url, str):
            return False

        flipkart_domains = ['flipkart.com']
        is_flipkart = any(domain in url.lower() for domain in flipkart_domains)
        has_product_id = self.extract_product_id(url) is not None

        return is_flipkart and has_product_id

    def extract_product_id(self, url: str) -> Optional[str]:
        """
        Extract FSN (Flipkart Serial Number) or product ID from URL
        Flipkart URLs typically have format: /product-name/p/itm<FSN>?pid=<FSN>
        """
        # Try to extract from 'pid' parameter
        pid_match = re.search(r'[?&]pid=([A-Z0-9]+)', url, re.IGNORECASE)
        if pid_match:
            return pid_match.group(1)

        # Try to extract from /p/ path
        path_match = re.search(r'/p/([A-Z0-9]+)', url, re.IGNORECASE)
        if path_match:
            return path_match.group(1)

        # Try to extract from itm prefix
        itm_match = re.search(r'itm([a-z0-9]+)', url, re.IGNORECASE)
        if itm_match:
            return itm_match.group(1)

        return None

    def scrape_product(self, url: str) -> Dict:
        """
        Scrape complete product information from Flipkart product page

        Args:
            url: Flipkart product URL

        Returns:
            Dictionary containing product data

        Raises:
            ValueError: If URL is invalid
            requests.exceptions.RequestException: If scraping fails
        """
        if not self.validate_url(url):
            raise ValueError("Invalid Flipkart URL. Please provide a valid product URL.")

        product_id = self.extract_product_id(url)

        try:
            # Fetch product page
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Extract product data
            product_data = {
                'platform': self.get_platform_name(),
                'product_id': product_id,
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
                'product_details': {},
                'warranty': self._extract_warranty(soup),
                'availability': self._extract_availability(soup),
                'images': self._extract_images(soup),
                'category': self._extract_category(soup),
                'reviews': []
            }

            # Scrape reviews from product page
            print(f"\n📄 Scraping reviews for Product ID: {product_id}")
            reviews = self._scrape_reviews_from_product_page(soup)
            print(f"✓ Scraped {len(reviews)} reviews from product page")

            # If no reviews found via traditional scraping, note that LLM will provide summary
            if len(reviews) == 0:
                print(f"⚠️  No individual reviews found via HTML scraping.")
                print(f"    Note: LLM extraction will provide review summary from page content\n")
            else:
                print()

            product_data['reviews'] = reviews

            # Extract bank offers from page (visible offers only, as hidden ones require JavaScript)
            print("\n💳 Extracting bank offers...")
            bank_offers = self._extract_bank_offers(soup)
            print(f"✓ Extracted {len(bank_offers)} bank offers from page\n")
            product_data['bank_offers'] = bank_offers

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

        # Merge bank_offers from both traditional scraping and LLM
        traditional_offers = merged.get('bank_offers', [])
        llm_offers = llm_data.get('bank_offers', [])

        # Combine and deduplicate offers based on description
        all_offers = traditional_offers.copy()
        traditional_descriptions = set(offer.get('description', '').lower() for offer in traditional_offers)

        for llm_offer in llm_offers:
            llm_desc = llm_offer.get('description', '').lower()
            if llm_desc not in traditional_descriptions:
                all_offers.append(llm_offer)

        merged['bank_offers'] = all_offers
        print(f"  ✓ Combined {len(traditional_offers)} traditional + {len(llm_offers)} LLM offers = {len(all_offers)} total bank offers")

        # Handle reviews: If no traditional reviews, create synthetic review from LLM summary
        traditional_reviews = merged.get('reviews', [])
        if len(traditional_reviews) == 0 and 'review_summary' in llm_data and llm_data['review_summary']:
            # Create a synthetic review from the LLM summary
            summary_data = llm_data['review_summary']

            # Convert summary to string if it's a dict
            if isinstance(summary_data, dict):
                summary_parts = []
                if 'positive_highlights' in summary_data and summary_data['positive_highlights']:
                    summary_parts.append("**Positive Highlights:**\n" + "\n".join(f"• {h}" for h in summary_data['positive_highlights']))
                if 'negative_highlights' in summary_data and summary_data['negative_highlights']:
                    summary_parts.append("\n**Negative Highlights:**\n" + "\n".join(f"• {h}" for h in summary_data['negative_highlights']))
                summary_text = "\n".join(summary_parts) if summary_parts else "Review summary available in analysis section."
            else:
                summary_text = str(summary_data)

            rating = merged.get('rating', '').split('/')[0] if merged.get('rating') else '4.0'

            synthetic_review = {
                'title': 'Summary of Customer Reviews',
                'rating': f"{rating}/5" if rating else '4.0/5',
                'text': summary_text,
                'author': 'AI Summary',
                'date': 'Based on available reviews',
                'verified_purchase': False
            }
            merged['reviews'] = [synthetic_review]
            print(f"  ✓ Created 1 synthetic review from LLM summary (no individual reviews available)")

        # Store review_summary separately as well
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

        return merged

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title"""
        # Flipkart uses various selectors for title
        selectors = [
            ('class', 'VU-ZEz'),
            ('class', 'B_NuCI'),
            ('class', '_35KyD6'),
            ('class', 'yhB1nd')
        ]

        for selector_type, selector_value in selectors:
            element = soup.find('span', class_=selector_value)
            if not element:
                element = soup.find('h1', class_=selector_value)

            if element:
                return self.clean_text(element.get_text())

        return "Title not found"

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Extract brand name"""
        # Try multiple selectors
        brand_selectors = [
            {'class': '_2WkVRV'},
            {'class': '_1nIIJx'}
        ]

        for selector in brand_selectors:
            element = soup.find('a', selector) or soup.find('div', selector)
            if element:
                text = self.clean_text(element.get_text())
                if text and text.lower() not in ['home', 'search', 'more']:
                    return text

        # Try extracting from title
        title = self._extract_title(soup)
        if title and title != "Title not found":
            # Often brand is the first word
            words = title.split()
            if words:
                return words[0]

        return "Brand not found"

    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract product price"""
        price_selectors = [
            ('class', 'Nx9bqj'),
            ('class', '_30jeq3'),
            ('class', '_1vC4OE'),
            ('class', '_3I9_wc')
        ]

        for selector_type, selector_value in price_selectors:
            element = soup.find('div', class_=selector_value)
            if element:
                price_text = self.clean_text(element.get_text())
                return price_text

        return "Price not available"

    def _extract_rating(self, soup: BeautifulSoup) -> str:
        """Extract overall rating"""
        rating_selectors = [
            ('class', 'XQDdHH'),
            ('class', '_3LWZlK'),
            ('class', 'hGSR34')
        ]

        for selector_type, selector_value in rating_selectors:
            element = soup.find('div', class_=selector_value)
            if element:
                text = self.clean_text(element.get_text())
                parsed = self.parse_rating(text)
                if parsed:
                    return parsed
                # Flipkart often shows just the number
                if text and re.match(r'^\d+\.?\d*$', text):
                    return f"{text}/5"

        return "Rating not available"

    def _extract_total_reviews(self, soup: BeautifulSoup) -> str:
        """Extract total number of reviews"""
        review_selectors = [
            ('class', 'Wphh3N'),
            ('class', '_2_R_DZ'),
            ('class', '_3UAT2v')
        ]

        for selector_type, selector_value in review_selectors:
            element = soup.find('span', class_=selector_value)
            if element:
                text = self.clean_text(element.get_text())
                # Extract number from text like "1,234 Ratings & 567 Reviews"
                match = re.search(r'([\d,]+)\s*(?:Ratings|Reviews)', text, re.IGNORECASE)
                if match:
                    return match.group(1)

        return "0"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        desc_selectors = [
            {'class': '_1mXcCf'},
            {'class': '_2418kt'},
            {'class': 'RmoJUa'}
        ]

        for selector in desc_selectors:
            element = soup.find('div', selector) or soup.find('p', selector)
            if element:
                return self.clean_text(element.get_text())

        return "Description not available"

    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract product features/highlights"""
        features = []

        # Look for highlights section
        highlights_div = soup.find('div', {'class': '_2418kt'})
        if highlights_div:
            feature_items = highlights_div.find_all('li')
            for item in feature_items:
                text = self.clean_text(item.get_text())
                if text and len(text) > 5:
                    features.append(text)

        # Try alternate selectors
        if not features:
            feature_list = soup.find('ul', {'class': '_1G_vzX'})
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
            {'class': '_2b_kHQ'},
            {'id': 'sellerName'}
        ]

        for selector in seller_selectors:
            element = soup.find('div', selector) or soup.find('a', selector)
            if element:
                return self.clean_text(element.get_text())

        return "Seller not found"

    def _extract_seller_rating(self, soup: BeautifulSoup) -> str:
        """Extract seller rating"""
        # Flipkart may show seller rating near seller name
        seller_section = soup.find('div', {'id': 'sellerSection'})
        if seller_section:
            rating_elem = seller_section.find('div', {'class': '_3Kaxyi'})
            if rating_elem:
                text = rating_elem.get_text().strip()
                match = re.search(r'(\d+)%', text)
                if match:
                    return f"{match.group(1)}%"

        return "Rating not available"

    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product specifications"""
        specifications = {}

        try:
            # Look for specifications table
            spec_sections = soup.find_all('div', {'class': '_2PF8IO'})

            for section in spec_sections:
                rows = section.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = self.clean_text(cols[0].get_text())
                        value = self.clean_text(cols[1].get_text())
                        if key and value:
                            specifications[key] = value

            # Try alternate selectors
            if not specifications:
                spec_list = soup.find_all('li', {'class': '_2-riNZ'})
                for item in spec_list:
                    text = item.get_text()
                    if ':' in text:
                        parts = text.split(':', 1)
                        if len(parts) == 2:
                            key = self.clean_text(parts[0])
                            value = self.clean_text(parts[1])
                            if key and value:
                                specifications[key] = value

        except Exception as e:
            print(f"Error extracting specifications: {str(e)}")

        return specifications

    def _extract_warranty(self, soup: BeautifulSoup) -> str:
        """Extract warranty information"""
        warranty_info = ""

        try:
            warranty_keywords = ['warranty', 'guarantee']

            # Check features
            features = self._extract_features(soup)
            for feature in features:
                if any(keyword in feature.lower() for keyword in warranty_keywords):
                    warranty_info += feature + " "

            # Check specifications
            specs = self._extract_specifications(soup)
            for key, value in specs.items():
                if any(keyword in key.lower() for keyword in warranty_keywords):
                    warranty_info += f"{key}: {value} "

        except Exception as e:
            print(f"Error extracting warranty: {str(e)}")

        return warranty_info.strip() if warranty_info else "Warranty information not available"

    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract product availability status"""
        try:
            # Look for availability indicators
            availability_elem = soup.find('div', {'class': '_16FRp0'})
            if availability_elem:
                return self.clean_text(availability_elem.get_text())

            # Check for out of stock
            out_of_stock = soup.find('div', text=re.compile(r'Out of Stock', re.IGNORECASE))
            if out_of_stock:
                return "Out of Stock"

            # Check for in stock
            in_stock = soup.find('button', text=re.compile(r'ADD TO CART|BUY NOW', re.IGNORECASE))
            if in_stock:
                return "In Stock"

        except Exception as e:
            print(f"Error extracting availability: {str(e)}")

        return "Availability not specified"

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product images"""
        images = []

        try:
            print("\n🖼️  Extracting product images from page...")

            # Strategy 1: Find main/large product image (most reliable)
            main_img = soup.find('img', {'class': lambda x: x and ('DByuf4' in x or 'jLEJ7H' in x)})
            if main_img:
                src = main_img.get('src') or main_img.get('data-src')
                if src and 'rukminim' in src:
                    full_url = self._convert_to_fullsize_image(src)
                    if full_url and full_url not in images:
                        images.append(full_url)
                        print(f"  ✓ Found main image: {full_url[:80]}...")

            # Strategy 2: Find thumbnail images in gallery (current structure)
            thumbnail_imgs = soup.find_all('img', {'class': '_0DkuPH'})
            for img in thumbnail_imgs:
                src = img.get('src') or img.get('data-src')
                if src and 'rukminim' in src:
                    full_url = self._convert_to_fullsize_image(src)
                    if full_url and full_url not in images:
                        images.append(full_url)
                        print(f"  ✓ Found thumbnail image: {full_url[:80]}...")

            # Strategy 3: Find all images with Flipkart CDN URLs (fallback)
            if len(images) < 3:
                all_imgs = soup.find_all('img')
                for img in all_imgs:
                    src = img.get('src') or img.get('data-src') or img.get('srcset', '').split(',')[0].split(' ')[0]
                    if src and 'rukminim' in src and 'water-purifier' in src.lower():
                        full_url = self._convert_to_fullsize_image(src)
                        if full_url and full_url not in images:
                            # Exclude icons, badges, and small images
                            if 'cms-rpd-img' not in src and 'attributeglossary' not in src:
                                if '/xif0q/' in src or '/image/' in src:
                                    images.append(full_url)
                                    print(f"  ✓ Found product image: {full_url[:80]}...")

            # Strategy 4: Old selectors (for backward compatibility)
            if not images:
                image_divs = soup.find_all('li', {'class': '_1T7P5R'})
                for div in image_divs:
                    img = div.find('img')
                    if img:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            full_url = self._convert_to_fullsize_image(src)
                            if full_url and full_url not in images:
                                images.append(full_url)
                                print(f"  ✓ Found image (old selector): {full_url[:80]}...")

            # Strategy 5: Try alternate old selector
            if not images:
                img_container = soup.find('div', {'class': '_2_AcLJ'})
                if img_container:
                    imgs = img_container.find_all('img')
                    for img in imgs:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            full_url = self._convert_to_fullsize_image(src)
                            if full_url and full_url not in images:
                                images.append(full_url)
                                print(f"  ✓ Found image (alt selector): {full_url[:80]}...")

            print(f"\n✓ Total product images extracted: {len(images)}\n")
            return images[:8]

        except Exception as e:
            print(f"❌ Error extracting images: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _convert_to_fullsize_image(self, thumbnail_url: str) -> str:
        """Convert Flipkart thumbnail URL to full-size image URL"""
        if not thumbnail_url:
            return ""

        full_size = thumbnail_url

        # Convert Flipkart image URLs to high-resolution
        # Format: https://rukminim2.flixcart.com/image/WIDTH/HEIGHT/...
        # Replace small sizes with 832/832 (high-res)
        full_size = re.sub(r'/image/\d+/\d+/', '/image/832/832/', full_size)

        # Also handle 'original' keyword for maximum resolution
        if '128/128' in full_size or '200/200' in full_size or '312/312' in full_size or '416/416' in full_size:
            full_size = re.sub(r'/\d+/\d+/', '/832/832/', full_size)

        return full_size

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract product category from breadcrumbs"""
        category = ""

        try:
            # Look for breadcrumbs
            breadcrumbs = soup.find('div', {'class': '_1MR4o5'})
            if breadcrumbs:
                links = breadcrumbs.find_all('a')
                categories = [self.clean_text(link.get_text()) for link in links if self.clean_text(link.get_text())]
                category = ' > '.join(categories)

            # Try alternate selector
            if not category:
                breadcrumb_links = soup.find_all('a', {'class': '_2whKao'})
                if breadcrumb_links:
                    categories = [self.clean_text(link.get_text()) for link in breadcrumb_links if self.clean_text(link.get_text())]
                    category = ' > '.join(categories)

        except Exception as e:
            print(f"Error extracting category: {str(e)}")

        return category if category else "Category not found"

    def _extract_bank_offers(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract bank offers from Flipkart product page
        Note: This only extracts visible offers. Hidden offers (shown after clicking "View more")
        are loaded via JavaScript and won't be captured.
        """
        bank_offers = []

        try:
            # Find the offers section
            offer_rows = soup.find_all('span', class_='+-2B3d row')

            for row in offer_rows:
                try:
                    # Extract offer type (Bank Offer, Special Price, etc.)
                    offer_type_elem = row.find('span', class_='ynXjOy')
                    offer_type = self.clean_text(offer_type_elem.get_text()) if offer_type_elem else ''

                    # Extract offer description
                    # The description is in a span after the offer type
                    description_elem = row.find('span', class_='')  # Empty class contains the description
                    if not description_elem:
                        # Try to get all text and remove the offer type
                        full_text = self.clean_text(row.get_text())
                        description = full_text.replace(offer_type, '').strip()
                    else:
                        description = self.clean_text(description_elem.get_text())

                    # Skip if we couldn't extract description
                    if not description or description == offer_type:
                        continue

                    # Determine bank name
                    bank = None
                    description_lower = description.lower()

                    # Common bank names in India
                    banks = ['hdfc', 'icici', 'sbi', 'axis', 'kotak', 'citibank', 'american express',
                             'standard chartered', 'yes bank', 'indusind', 'paytm', 'rupay']

                    for bank_name in banks:
                        if bank_name in description_lower:
                            bank = bank_name.upper()
                            break

                    # Extract discount amount
                    discount_amount = None
                    # Try to find rupee amount: ₹X,XXX or ₹XXX
                    amount_match = re.search(r'₹\s?([\d,]+)', description)
                    if amount_match:
                        try:
                            discount_amount = float(amount_match.group(1).replace(',', ''))
                        except:
                            pass

                    # Classify offer type
                    if not offer_type or offer_type.lower() == 'bank offer':
                        if 'cashback' in description_lower:
                            classified_type = 'Cashback'
                        elif 'emi' in description_lower:
                            classified_type = 'EMI'
                        elif 'discount' in description_lower or 'off' in description_lower:
                            classified_type = 'Discount'
                        else:
                            classified_type = 'Bank Offer'
                    elif 'special price' in offer_type.lower():
                        classified_type = 'Discount'
                    else:
                        classified_type = offer_type

                    bank_offer = {
                        'bank': bank,
                        'offer_type': classified_type,
                        'description': description,
                        'discount_amount': discount_amount,
                        'terms': None  # T&C links are available but not extracted
                    }

                    bank_offers.append(bank_offer)
                    print(f"  - {classified_type}: {description[:60]}...")

                except Exception as e:
                    print(f"  ⚠ Error extracting individual offer: {str(e)}")
                    continue

        except Exception as e:
            print(f"❌ Error extracting bank offers: {str(e)}")

        return bank_offers

    def _scrape_reviews_from_product_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Scrape customer reviews from product page"""
        reviews = []

        try:
            # Flipkart reviews are typically in specific divs
            review_divs = soup.find_all('div', {'class': '_1PBCrt'})

            if not review_divs:
                review_divs = soup.find_all('div', {'class': 'col _2wzgFH'})

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
        title_elem = review_div.find('p', {'class': '_2xg6Ul'})
        if title_elem:
            return self.clean_text(title_elem.get_text())
        return ""

    def _extract_review_rating(self, review_div: BeautifulSoup) -> str:
        """Extract review rating"""
        rating_elem = review_div.find('div', {'class': 'hGSR34'})
        if rating_elem:
            text = rating_elem.get_text().strip()
            parsed = self.parse_rating(text)
            if parsed:
                return parsed
            if text and re.match(r'^\d+\.?\d*$', text):
                return f"{text}/5"
        return ""

    def _extract_review_text(self, review_div: BeautifulSoup) -> str:
        """Extract review text"""
        text_elem = review_div.find('div', {'class': 'ZmyHeo'})
        if not text_elem:
            text_elem = review_div.find('div', {'class': 't-ZTKy'})

        if text_elem:
            return self.clean_text(text_elem.get_text())
        return ""

    def _extract_review_author(self, review_div: BeautifulSoup) -> str:
        """Extract review author name"""
        author_elem = review_div.find('p', {'class': '_2NsDsF'})
        if author_elem:
            return self.clean_text(author_elem.get_text())
        return "Anonymous"

    def _extract_review_date(self, review_div: BeautifulSoup) -> str:
        """Extract review date"""
        date_elem = review_div.find('p', {'class': '_2mcZGG'})
        if date_elem:
            text = date_elem.get_text().strip()
            # Remove extra text like "Certified Buyer,"
            text = re.sub(r'Certified Buyer[,\s]*', '', text, flags=re.IGNORECASE)
            return self.clean_text(text)
        return ""

    def _extract_review_verified(self, review_div: BeautifulSoup) -> bool:
        """Check if review is verified purchase"""
        verified_elem = review_div.find(text=re.compile(r'Certified Buyer', re.IGNORECASE))
        return verified_elem is not None
