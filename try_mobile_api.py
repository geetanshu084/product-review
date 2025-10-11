#!/usr/bin/env python3
"""Try Amazon AJAX reviews endpoint with proper session"""

import requests
import json
import time

asin = "B0D79G62J3"
domain = "amazon.in"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
})

# Step 1: Get cookies from product page
print("Step 1: Loading product page to get session cookies...")
product_url = f"https://www.{domain}/dp/{asin}"
resp1 = session.get(product_url)
print(f"  ✓ Cookies: {len(session.cookies)}")
time.sleep(1)

# Step 2: Try the AJAX endpoint with proper headers
print("\nStep 2: Trying AJAX reviews endpoint...")
ajax_url = f"https://www.{domain}/hz/reviews-render/ajax/reviews/get/?asin={asin}&pageNumber=2&pageSize=10"

headers = {
    'Accept': 'text/html,*/*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'https://www.{domain}/product-reviews/{asin}',
}

resp2 = session.get(ajax_url, headers=headers, timeout=10)
print(f"  Status: {resp2.status_code}")
print(f"  Content-Type: {resp2.headers.get('Content-Type')}")

if resp2.status_code == 200:
    print(f"\n✅ SUCCESS! Got response:")
    content = resp2.text
    print(f"  Length: {len(content)} bytes")

    # Check if it's HTML or JSON
    if content.strip().startswith('{'):
        data = json.loads(content)
        print(f"  JSON keys: {list(data.keys())}")
    else:
        # It's HTML - count reviews
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'lxml')
        reviews = soup.find_all('div', {'data-hook': 'review'})
        print(f"  Found {len(reviews)} reviews in HTML!")

        if reviews:
            # Show first review
            first = reviews[0]
            title_elem = first.find('a', {'data-hook': 'review-title'})
            if not title_elem:
                title_elem = first.find('span', {'data-hook': 'review-title'})
            title = title_elem.get_text().strip() if title_elem else 'N/A'
            print(f"\n  First review: {title[:80]}")
else:
    print(f"  ❌ Failed: {resp2.text[:200]}")
