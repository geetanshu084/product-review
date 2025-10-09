#!/usr/bin/env python3
"""
Debug script to see what Selenium is actually loading from Amazon
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')

# Initialize driver
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

try:
    # Navigate to Amazon reviews page
    asin = "B0CXN9WCVN"
    url = f"https://www.amazon.in/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"

    print(f"Navigating to: {url}")
    driver.get(url)

    time.sleep(5)  # Wait for page to fully load

    # Get page title
    print(f"\nPage title: {driver.title}")

    # Save screenshot
    driver.save_screenshot('/tmp/amazon_reviews_page.png')
    print(f"Screenshot saved to /tmp/amazon_reviews_page.png")

    # Save page source
    with open('/tmp/amazon_reviews_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"Page source saved to /tmp/amazon_reviews_page.html")

    # Try to find reviews with different selectors
    selectors = [
        'div[data-hook="review"]',
        'div.review',
        'div[id*="review"]',
        'div.a-section.review',
        'div[class*="review"]'
    ]

    print("\nTrying different selectors:")
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"  {selector}: Found {len(elements)} elements")
            if elements:
                print(f"    First element text preview: {elements[0].text[:100]}")
        except Exception as e:
            print(f"  {selector}: Error - {str(e)}")

    # Check if we got a CAPTCHA
    page_text = driver.page_source.lower()
    if 'captcha' in page_text or 'robot' in page_text:
        print("\n⚠️  WARNING: CAPTCHA or bot detection may be present")

    # Check for "Sorry, we just need to make sure you're not a robot"
    if "sorry" in page_text and "robot" in page_text:
        print("⚠️  Amazon is blocking automated access")

finally:
    driver.quit()
    print("\nDriver closed")
