#!/usr/bin/env python3
"""
Find the AJAX/API endpoint that loads reviews dynamically
"""

import requests
from bs4 import BeautifulSoup
import json
import re

# Setup session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

asin = "B0D79G62J3"
domain = "amazon.in"

print("🔍 Searching for AJAX endpoints in page source...\n")

# Fetch the reviews page
url = f"https://www.{domain}/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
response = session.get(url, timeout=15)

# Look for API endpoints in the HTML
html = response.text

# Common patterns for Amazon API endpoints
patterns = [
    r'(https?://[^"\']+/api/[^"\']+)',
    r'(/api/[^"\']+reviews[^"\']*)',
    r'(reviews/[^"\']+\.json)',
    r'(/gp/customer-reviews/[^"\']+)',
    r'(/hz/reviews-render/[^"\']+)',
    r'(cm_cr_arp_[^"\']+)',
]

print("Found potential endpoints:")
found_any = False
for pattern in patterns:
    matches = re.findall(pattern, html)
    if matches:
        found_any = True
        print(f"\nPattern: {pattern}")
        for match in set(matches[:5]):  # Show first 5 unique matches
            print(f"  - {match}")

if not found_any:
    print("  (No API endpoints found in patterns)")

# Look for JavaScript variables that might contain data
print("\n\n🔍 Searching for embedded JSON data...\n")

# Common variable names Amazon uses
js_vars = [
    r'var\s+CustomerReviews\s*=\s*({.+?});',
    r'window\.CustomerReviews\s*=\s*({.+?});',
    r'var\s+reviewsData\s*=\s*({.+?});',
    r'"reviews"\s*:\s*(\[.+?\])',
]

for var_pattern in js_vars:
    matches = re.findall(var_pattern, html, re.DOTALL)
    if matches:
        print(f"Found: {var_pattern[:50]}")
        print(f"  Sample: {matches[0][:200]}...")

# Try to find the pagination widget endpoint
print("\n\n🔍 Searching for pagination widget...\n")

soup = BeautifulSoup(html, 'lxml')

# Look for pagination links
pagination = soup.find('ul', {'class': 'a-pagination'})
if pagination:
    print("Found pagination widget!")
    links = pagination.find_all('a')
    for link in links[:3]:
        href = link.get('href', '')
        if href:
            print(f"  - {href}")

# Look for "next page" URL
next_page = soup.find('li', {'class': 'a-last'})
if next_page:
    next_link = next_page.find('a')
    if next_link and next_link.get('href'):
        print(f"\nNext page URL: {next_link['href']}")

# Save the HTML for manual inspection
with open('/tmp/reviews_page_source.html', 'w') as f:
    f.write(html)

print(f"\n💾 Full HTML saved to /tmp/reviews_page_source.html")
print(f"   File size: {len(html)} bytes")
