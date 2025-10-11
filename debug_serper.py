#!/usr/bin/env python3
"""Debug Serper API connection"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SERPER_API_KEY")

print("🔍 Testing Serper API connection...")
print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
print("")

# Test shopping search
payload = {
    "q": "iPhone 15",
    "location": "India",
    "num": 5
}

headers = {
    "X-API-KEY": api_key,
    "Content-Type": "application/json"
}

print("📤 Request:")
print(f"URL: https://google.serper.dev/shopping")
print(f"Payload: {payload}")
print("")

try:
    response = requests.post(
        "https://google.serper.dev/shopping",
        json=payload,
        headers=headers,
        timeout=10
    )

    print(f"📥 Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("")

    if response.status_code == 200:
        data = response.json()
        print("✅ API Connected Successfully!")
        print(f"\nFull Response Keys: {list(data.keys())}")
        print(f"\nShopping results: {len(data.get('shopping_results', []))}")

        # Print the full response for debugging
        import json
        print(f"\n📄 Full Response:")
        print(json.dumps(data, indent=2))

        if data.get('shopping_results'):
            print("\n✅ First result:")
            result = data['shopping_results'][0]
            print(f"  Title: {result.get('title')}")
            print(f"  Source: {result.get('source')}")
            print(f"  Price: {result.get('price')}")
            print(f"  Rating: {result.get('rating')}")
        else:
            print("\n⚠️  No shopping results returned")
            print("This might be due to:")
            print("  - Location not supporting shopping results")
            print("  - Query not matching shopping products")
            print("  - Regional restrictions")
    else:
        print(f"❌ FAILED!")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Exception: {str(e)}")
    import traceback
    traceback.print_exc()
