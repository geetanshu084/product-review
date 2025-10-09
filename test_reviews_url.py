#!/usr/bin/env python3
"""
Test the exact "See all reviews" URL pattern
"""

import requests
from bs4 import BeautifulSoup
import time

# Setup session with proper headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none'
})

asin = "B0D79G62J3"
domain = "amazon.in"

print("Step 1: Fetching product page first (to get session cookies)...")
product_url = f"https://www.{domain}/dp/{asin}"
try:
    response1 = session.get(product_url, timeout=15)
    print(f"  ✓ Product page status: {response1.status_code}")
    print(f"  ✓ Cookies received: {len(session.cookies)}")
    time.sleep(2)
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\nStep 2: Now fetching reviews page with session cookies...")
reviews_url = f"https://www.{domain}/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"

# Add Referer header
headers = session.headers.copy()
headers['Referer'] = product_url

try:
    response2 = session.get(reviews_url, headers=headers, timeout=15)
    print(f"  ✓ Reviews page status: {response2.status_code}")

    soup = BeautifulSoup(response2.content, 'lxml')

    # Check for bot detection
    page_text = soup.get_text()
    if 'robot' in page_text.lower() or 'captcha' in page_text.lower():
        print("  ❌ BOT DETECTION TRIGGERED!")
        # Save HTML for inspection
        with open('/tmp/amazon_blocked.html', 'w') as f:
            f.write(response2.text)
        print("  💾 Saved response to /tmp/amazon_blocked.html")
    else:
        # Find reviews
        review_divs = soup.find_all('div', {'data-hook': 'review'})
        print(f"  ✓ Found {len(review_divs)} reviews!")

        if review_divs:
            for i, div in enumerate(review_divs[:3], 1):
                title_elem = div.find('a', {'data-hook': 'review-title'})
                if not title_elem:
                    title_elem = div.find('span', {'data-hook': 'review-title'})
                title = title_elem.get_text().strip() if title_elem else "N/A"
                print(f"    {i}. {title[:60]}")
        else:
            print("  ⚠ No review containers found, saving HTML...")
            with open('/tmp/amazon_no_reviews.html', 'w') as f:
                f.write(response2.text)
            print("  💾 Saved to /tmp/amazon_no_reviews.html")

except Exception as e:
    print(f"  ❌ Error: {e}")
