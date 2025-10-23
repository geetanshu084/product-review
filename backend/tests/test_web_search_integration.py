"""
Test script for Web Search Integration
Tests the complete flow: scraping → price comparison → web search → analysis
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from src.analysis.web_search import WebSearchAnalyzer

def test_web_search_analyzer():
    """Test the WebSearchAnalyzer class"""
    print("=" * 80)
    print("Testing Web Search Analyzer")
    print("=" * 80)

    # Get API keys
    serper_api_key = os.getenv('SERPER_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')

    if not serper_api_key:
        print("❌ SERPER_API_KEY not found in environment")
        return False

    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        return False

    # Initialize analyzer
    print("\n📦 Initializing Web Search Analyzer...")
    try:
        # WebSearchAnalyzer reads API keys from environment
        analyzer = WebSearchAnalyzer()
        print("✓ Web Search Analyzer initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {str(e)}")
        return False

    # Test product
    product_name = "Apple iPhone 15 Pro"
    print(f"\n🔍 Testing with product: {product_name}")

    # Test individual search methods
    print("\n--- Testing Individual Search Methods ---")

    print("\n1. Testing search_external_reviews()...")
    try:
        reviews = analyzer.search_external_reviews(product_name)
        print(f"✓ Found {reviews['count']} review results")
        if reviews['results']:
            print(f"  Example: {reviews['results'][0]['title'][:60]}...")
    except Exception as e:
        print(f"❌ search_external_reviews failed: {str(e)}")

    print("\n2. Testing search_comparisons()...")
    try:
        comparisons = analyzer.search_comparisons(product_name)
        print(f"✓ Found {comparisons['count']} comparison results")
        if comparisons['results']:
            print(f"  Example: {comparisons['results'][0]['title'][:60]}...")
    except Exception as e:
        print(f"❌ search_comparisons failed: {str(e)}")

    print("\n3. Testing search_issues()...")
    try:
        issues = analyzer.search_issues(product_name)
        print(f"✓ Found {issues['count']} issue results")
        if issues['results']:
            print(f"  Example: {issues['results'][0]['title'][:60]}...")
    except Exception as e:
        print(f"❌ search_issues failed: {str(e)}")

    print("\n4. Testing search_reddit_discussions()...")
    try:
        reddit = analyzer.search_reddit_discussions(product_name)
        print(f"✓ Found {reddit['count']} reddit results")
        if reddit['results']:
            print(f"  Example: {reddit['results'][0]['title'][:60]}...")
    except Exception as e:
        print(f"❌ search_reddit_discussions failed: {str(e)}")

    # Test comprehensive analysis
    print("\n--- Testing Comprehensive Analysis ---")
    print("\n🤖 Running full analysis (this may take 30-60 seconds)...")

    try:
        analysis = analyzer.analyze_product(product_name)

        print("\n✅ Analysis Complete!")
        print(f"\nResults Summary:")
        print(f"  📝 External Reviews: {len(analysis['external_reviews'])}")
        print(f"  🔄 Comparison Articles: {len(analysis['comparison_articles'])}")
        print(f"  ⚠️  Issue Discussions: {len(analysis['issue_discussions'])}")
        print(f"  💬 Reddit Discussions: {len(analysis['reddit_discussions'])}")
        print(f"  🎥 Video Reviews: {len(analysis['video_reviews'])}")
        print(f"  📊 Total Sources: {analysis['total_sources']}")

        print(f"\n📌 Key Findings ({len(analysis['key_findings'])}):")
        for i, finding in enumerate(analysis['key_findings'][:5], 1):
            print(f"  {i}. {finding[:80]}...")

        if analysis['red_flags']:
            print(f"\n⚠️  Red Flags ({len(analysis['red_flags'])}):")
            for i, flag in enumerate(analysis['red_flags'], 1):
                print(f"  {i}. {flag[:80]}...")
        else:
            print("\n✅ No major red flags detected")

        print(f"\n💭 Overall Sentiment: {analysis['overall_sentiment'].upper()}")

        if analysis['video_reviews']:
            print(f"\n🎥 Video Reviews:")
            for video in analysis['video_reviews'][:3]:
                print(f"  - {video['title'][:60]}...")
                print(f"    {video['url']}")

        return True

    except Exception as e:
        print(f"❌ Comprehensive analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_analyzer_integration():
    """Test integration with ProductAnalyzer"""
    print("\n" + "=" * 80)
    print("Testing ProductAnalyzer Integration")
    print("=" * 80)

    from src.analyzer import ProductAnalyzer

    google_api_key = os.getenv('GOOGLE_API_KEY')
    serper_api_key = os.getenv('SERPER_API_KEY')

    if not google_api_key or not serper_api_key:
        print("❌ Missing required API keys")
        return False

    print("\n📦 Initializing ProductAnalyzer with web search...")
    try:
        analyzer = ProductAnalyzer()
        print("✓ ProductAnalyzer initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {str(e)}")
        return False

    # Check if web search analyzer is available
    if analyzer.web_search_analyzer:
        print("✓ Web search analyzer is enabled")
    else:
        print("❌ Web search analyzer not initialized")
        return False

    # Test get_web_search_analysis method
    print("\n🔍 Testing get_web_search_analysis()...")
    try:
        result = analyzer.get_web_search_analysis("Apple iPhone 15 Pro")
        if result:
            print("✓ Web search analysis returned data")
            print(f"  Total sources: {result.get('total_sources', 0)}")
            print(f"  Key findings: {len(result.get('key_findings', []))}")
        else:
            print("⚠️  Web search analysis returned None")
    except Exception as e:
        print(f"❌ get_web_search_analysis failed: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    print("Web Search Integration Test Suite")
    print("=" * 80)

    # Run tests
    test1_passed = test_web_search_analyzer()
    test2_passed = test_analyzer_integration()

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"WebSearchAnalyzer Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"ProductAnalyzer Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
