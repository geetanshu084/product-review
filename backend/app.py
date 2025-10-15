"""
Streamlit Web Interface for Amazon Product Analysis Agent
"""

import os
import uuid
import re
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

from src.scraper import AmazonScraper
from src.analyzer import ProductAnalyzer
from src.chatbot import ProductChatbot

# Load environment variables from .env file in project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

# Page configuration
st.set_page_config(
    page_title="Amazon Product Analysis Agent",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def extract_urls_from_text(text):
    """Extract URLs from text and return them with context"""
    # Pattern to match URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return urls


def detect_ecommerce_site(url):
    """Detect which e-commerce site the URL belongs to"""
    url_lower = url.lower()

    if 'amazon' in url_lower:
        return 'Amazon', '🛒'
    elif 'flipkart' in url_lower:
        return 'Flipkart', '🛍️'
    elif 'ebay' in url_lower:
        return 'eBay', '🏪'
    elif 'walmart' in url_lower:
        return 'Walmart', '🏬'
    elif 'aliexpress' in url_lower:
        return 'AliExpress', '🌐'
    elif 'myntra' in url_lower:
        return 'Myntra', '👗'
    elif 'ajio' in url_lower:
        return 'Ajio', '👔'
    elif 'snapdeal' in url_lower:
        return 'Snapdeal', '🛒'
    else:
        return 'External Link', '🔗'


def format_message_with_links(message_text):
    """Format message text to display URLs as clickable cards"""
    urls = extract_urls_from_text(message_text)

    # Display the main message text
    # Replace URLs with placeholder text for cleaner display
    display_text = message_text
    for url in urls:
        display_text = display_text.replace(url, f"[Link]({url})")

    st.markdown(display_text)

    # Display URL cards if any URLs found
    if urls:
        st.markdown("---")
        st.markdown("**🔗 Referenced Links:**")

        for i, url in enumerate(urls, 1):
            site_name, icon = detect_ecommerce_site(url)

            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"**{icon} {site_name}**")
                    # Truncate long URLs for display
                    display_url = url if len(url) <= 60 else url[:57] + "..."
                    st.caption(display_url)

                with col2:
                    # Create link that opens in new tab
                    st.markdown(
                        f'<a href="{url}" target="_blank" rel="noopener noreferrer">'
                        f'<button style="background-color:#FF4B4B;color:white;border:none;'
                        f'padding:8px 16px;border-radius:4px;cursor:pointer;width:100%;">'
                        f'Visit →</button></a>',
                        unsafe_allow_html=True
                    )

                st.markdown("---")


def initialize_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if 'product_data' not in st.session_state:
        st.session_state.product_data = None

    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'scraper' not in st.session_state:
        st.session_state.scraper = AmazonScraper()

    if 'analyzer' not in st.session_state:
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if google_api_key:
            try:
                st.session_state.analyzer = ProductAnalyzer(google_api_key=google_api_key)
            except Exception as e:
                st.session_state.analyzer = None
                st.session_state.analyzer_error = str(e)
        else:
            st.session_state.analyzer = None
            st.session_state.analyzer_error = "GOOGLE_API_KEY not found in .env file"

    if 'chatbot' not in st.session_state:
        # google_api_key = os.getenv('GOOGLE_API_KEY')
        # redis_host = os.getenv('REDIS_HOST', 'localhost')
        # redis_port = int(os.getenv('REDIS_PORT', 6379))
        # redis_db = int(os.getenv('REDIS_DB', 0))
        # redis_password = os.getenv('REDIS_PASSWORD', None)

        # if google_api_key:
        try:
            st.session_state.chatbot = ProductChatbot()
        except Exception as e:
            st.session_state.chatbot = None
            st.session_state.redis_error = str(e)
        # else:
        #     st.session_state.chatbot = None
        #     st.session_state.redis_error = "GOOGLE_API_KEY not found in .env file"


def show_sidebar():
    """Display sidebar with information"""
    with st.sidebar:
        st.title("🛍️ Product Analyzer")
        st.markdown("---")

        st.markdown("""
        ### How to use:
        1. **Analyze Tab**: Paste an Amazon product URL and click "Analyze Product"
        2. **Reviews Tab**: View Amazon reviews and external sources
        3. **Q&A Tab**: Ask questions about the analyzed product

        ### Features:
        - Comprehensive product analysis
        - **Multi-platform price comparison**
        - **External reviews from web sources**
        - Amazon customer reviews with filters
        - Comparison articles and video reviews
        - Reddit discussions and issue reports
        - Key findings and red flag detection
        - Bank offers extraction
        - Product specifications
        - Pros and cons from customer reviews
        - Seller evaluation
        - After-sales service evaluation
        - Interactive Q&A with memory
        - Buy/Wait/Avoid recommendation

        ### Requirements:
        - Valid Amazon product URL
        - GOOGLE_API_KEY in .env
        - SERPER_API_KEY in .env (optional, for price comparison & web search)
        - Redis server running
        """)

        st.markdown("---")


def product_analysis_tab():
    """Product Analysis tab content"""
    st.header("📊 Product Analysis")

    st.markdown("""
    Enter an Amazon product URL below to get a comprehensive analysis including:
    """)

    # URL input
    url = st.text_input(
        "Amazon Product URL",
        placeholder="https://www.amazon.com/dp/XXXXXXXXXX",
        help="Enter the full Amazon product URL"
    )

    # Note about review limitations
    st.info("ℹ️ **Review Scraping Limit**: Due to Amazon's bot protection, we can scrape ~8-10 reviews from the product page. This is sufficient for basic sentiment analysis.")

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        analyze_button = st.button("🔍 Analyze Product", type="primary", use_container_width=True)

    with col2:
        clear_button = st.button("🗑️ Clear Results", use_container_width=True)

    if clear_button:
        st.session_state.product_data = None
        st.session_state.analysis_result = None
        st.rerun()

    # Check for Google API Key
    if not st.session_state.analyzer:
        st.error("⚠️ Google API Key not configured. Please set GOOGLE_API_KEY in your .env file.")
        st.info("Get your API key from: https://makersuite.google.com/app/apikey")
        if hasattr(st.session_state, 'analyzer_error'):
            st.error(f"Error: {st.session_state.analyzer_error}")
        return

    # Analyze product
    if analyze_button:
        if not url:
            st.warning("⚠️ Please enter an Amazon product URL")
            return

        # Validate URL
        if not st.session_state.scraper.validate_url(url):
            st.error("❌ Invalid Amazon URL. Please provide a valid product URL.")
            return

        # Show progress
        progress_text = st.empty()
        progress_bar = st.progress(0)

        try:
            progress_text.text(f"🔄 Scraping product details...")
            progress_bar.progress(10)

            # Use default scraper (gets ~8-10 reviews from product page)
            product_data = st.session_state.scraper.scrape_product(url)

            progress_bar.progress(50)
            progress_text.text(f"✅ Scraped {len(product_data.get('reviews', []))} reviews")

            st.session_state.product_data = product_data

            # Note: Product data is already saved to Redis by scraper
            # Chatbot will access it directly using the ASIN

            progress_bar.progress(100)
            progress_text.empty()
            progress_bar.empty()

        except Exception as e:
            progress_text.empty()
            progress_bar.empty()
            st.error(f"❌ Failed to scrape product: {str(e)}")
            st.error(f"Debug: URL attempted: {url}")
            return

        # Analyze with LLM
        with st.spinner("🤖 Analyzing product with AI..."):
            try:
                analysis = st.session_state.analyzer.analyze_product(product_data)
                st.session_state.analysis_result = analysis

                # Save updated product_data (with price_comparison and web_search_analysis) to Redis
                asin = product_data.get('asin')
                if asin:
                    st.session_state.scraper._save_to_cache(asin, product_data)
                    print(f"✓ Updated product data saved to Redis for ASIN: {asin}")

            except Exception as e:
                st.error(f"❌ LLM analysis failed: {str(e)}")
                return

        st.success("✅ Analysis complete!")

    # Display results
    if st.session_state.analysis_result:
        st.markdown("---")

        # Product summary box
        if st.session_state.product_data:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Price", st.session_state.product_data.get('price', 'N/A'))

            with col2:
                st.metric("Rating", st.session_state.product_data.get('rating', 'N/A'))

            with col3:
                st.metric("Reviews", st.session_state.product_data.get('total_reviews', 'N/A'))

        st.markdown("---")

        # Price comparison results (if available)
        price_comparison = st.session_state.product_data.get('price_comparison')
        if price_comparison and price_comparison.get('total_results', 0) > 0:
            st.subheader("💰 Price Comparison Across Platforms")

            # Best deal highlight
            best_deal = price_comparison.get('best_deal')
            if best_deal:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Best Price", f"{best_deal['currency']} {best_deal['price']:.2f}")
                with col2:
                    st.metric("Platform", best_deal['platform'].upper())
                with col3:
                    st.metric("Potential Savings", f"{best_deal['currency']} {best_deal['savings']:.2f}")
                with col4:
                    st.metric("Savings %", f"{best_deal['savings_percent']:.1f}%")

            # Price statistics
            stats = price_comparison.get('price_stats', {})
            if stats:
                st.markdown("**Price Range:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Minimum", f"₹{stats['min_price']:.2f}")
                with col2:
                    st.metric("Average", f"₹{stats['avg_price']:.2f}")
                with col3:
                    st.metric("Maximum", f"₹{stats['max_price']:.2f}")

            # Platform breakdown
            platforms = price_comparison.get('price_comparison', {})
            if platforms:
                st.markdown("**Prices by Platform:**")
                for platform, items in platforms.items():
                    if items:
                        with st.expander(f"{platform.upper()} ({len(items)} results)"):
                            for item in items[:5]:  # Show top 5
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"**{item['title'][:80]}...**")
                                    st.caption(f"Seller: {item['seller']} | Rating: {item['rating']}")
                                with col2:
                                    st.markdown(f"**{item['currency']} {item['price']:.2f}**")
                                    if item['url']:
                                        st.markdown(f"[View →]({item['url']})")

            st.markdown("---")

        # Display analysis
        st.markdown(st.session_state.analysis_result)

        # Download button
        st.download_button(
            label="📥 Download Analysis",
            data=st.session_state.analysis_result,
            file_name=f"product_analysis_{st.session_state.product_data.get('asin', 'unknown')}.md",
            mime="text/markdown"
        )


def qa_tab():
    """Q&A tab content"""
    st.header("💬 Ask Questions")

    # Check prerequisites
    if not st.session_state.chatbot:
        st.error("⚠️ Q&A system not available. Please ensure:")
        st.markdown("""
        1. GOOGLE_API_KEY is configured in .env
        2. Redis server is running
        3. Redis connection details are correct in .env
        """)
        st.info("Get your API key from: https://makersuite.google.com/app/apikey")

        if hasattr(st.session_state, 'redis_error'):
            st.error(f"Redis Error: {st.session_state.redis_error}")
        return

    if not st.session_state.product_data:
        st.info("ℹ️ Please analyze a product first before asking questions.")
        st.markdown("Go to the **Product Analysis** tab to analyze a product.")
        return

    # Display product info
    st.markdown(f"**Current Product:** {st.session_state.product_data.get('title', 'N/A')}")
    st.markdown("---")

    # Clear chat button at top
    if st.button("🗑️ Clear Chat", use_container_width=False):
        st.session_state.chat_history = []
        st.success("✅ Conversation cleared!")
        st.rerun()

    st.markdown("---")

    # Chat interface
    st.markdown("### Conversation")

    # Display chat history from session state
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                with st.chat_message("user"):
                    st.write(msg['content'])
            else:
                with st.chat_message("assistant"):
                    # Use enhanced formatting for assistant messages
                    format_message_with_links(msg['content'])
    else:
        st.info("💭 No conversation yet. Ask a question to get started!")

    # Chat input at bottom (automatically clears after submission)
    question = st.chat_input("Ask a question about this product...", key="chat_input")

    if question:
        # Get ASIN from product data
        asin = st.session_state.product_data.get('asin')
        if not asin:
            st.error("❌ Product ASIN not found. Please re-analyze the product.")
            st.stop()

        # Get answer with spinner
        with st.spinner("🤔 Thinking..."):
            try:
                # Call chatbot with session_id, product_id (asin), and question
                answer = st.session_state.chatbot.ask(st.session_state.session_id, asin, question)

                # Add to session chat history (will display on rerun)
                st.session_state.chat_history.append({'role': 'user', 'content': question})
                st.session_state.chat_history.append({'role': 'assistant', 'content': answer})

                # Rerun to display in conversation section
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to generate answer: {str(e)}")


def reviews_tab():
    """Reviews tab content - shows Amazon and external reviews"""
    st.header("📝 Reviews & External Sources")

    # Check if product data is available
    if not st.session_state.product_data:
        st.info("ℹ️ Please analyze a product first to see reviews.")
        st.markdown("Go to the **Product Analysis** tab to analyze a product.")
        return

    # Display product info
    st.markdown(f"**Product:** {st.session_state.product_data.get('title', 'N/A')}")
    st.markdown("---")

    # Get data
    amazon_reviews = st.session_state.product_data.get('reviews', [])
    web_search_data = st.session_state.product_data.get('web_search_analysis', {})

    # Create sub-tabs
    review_tab1, review_tab2, review_tab3, review_tab4 = st.tabs([
        f"🛒 Amazon Reviews ({len(amazon_reviews)})",
        f"🌐 External Reviews ({len(web_search_data.get('external_reviews', []))})",
        f"🔍 Comparisons ({len(web_search_data.get('comparison_articles', []))})",
        f"📊 Summary"
    ])

    # Amazon Reviews Tab
    with review_tab1:
        st.subheader("Amazon Customer Reviews")

        if not amazon_reviews:
            st.info("No Amazon reviews were scraped for this product.")
        else:
            # Rating filter
            col1, col2 = st.columns([3, 1])
            with col1:
                rating_filter = st.select_slider(
                    "Filter by minimum rating",
                    options=[1, 2, 3, 4, 5],
                    value=1,
                    key="amazon_rating_filter"
                )
            with col2:
                verified_only = st.checkbox("Verified purchases only", value=False, key="verified_filter")

            st.markdown("---")

            # Filter reviews
            filtered_reviews = amazon_reviews
            if rating_filter > 1:
                def get_rating_value(review):
                    """Extract numeric rating from review"""
                    try:
                        rating_str = review.get('rating', '0')
                        if isinstance(rating_str, str):
                            rating_parts = rating_str.split()
                            if rating_parts:
                                return float(rating_parts[0])
                        elif isinstance(rating_str, (int, float)):
                            return float(rating_str)
                    except (ValueError, IndexError):
                        pass
                    return 0

                filtered_reviews = [r for r in filtered_reviews if get_rating_value(r) >= rating_filter]

            if verified_only:
                filtered_reviews = [r for r in filtered_reviews if r.get('verified', False)]

            st.write(f"Showing **{len(filtered_reviews)}** of **{len(amazon_reviews)}** reviews")

            # Display reviews
            for i, review in enumerate(filtered_reviews, 1):
                with st.expander(f"⭐ {review.get('rating', 'N/A')} - {review.get('title', 'No title')}", expanded=(i == 1)):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Author:** {review.get('author', 'Anonymous')}")
                        st.markdown(f"**Date:** {review.get('date', 'N/A')}")
                        if review.get('verified'):
                            st.markdown("✅ **Verified Purchase**")

                    with col2:
                        rating_val = review.get('rating', 'N/A')
                        st.metric("Rating", rating_val)

                    st.markdown("---")
                    st.markdown(f"**Review:**")
                    st.write(review.get('text', 'No review text available'))

    # External Reviews Tab
    with review_tab2:
        st.subheader("External Reviews & Mentions")

        external_reviews = web_search_data.get('external_reviews', [])

        if not external_reviews:
            st.info("No external reviews found. Web search may be disabled or no results were available.")
        else:
            st.write(f"Found **{len(external_reviews)}** external sources")
            st.markdown("---")

            for i, review in enumerate(external_reviews, 1):
                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"### {i}. {review.get('title', 'No title')}")
                        st.caption(f"🌐 **Source:** {review.get('source', 'Unknown')} | 📅 {review.get('date', 'N/A')}")

                    with col2:
                        if review.get('url'):
                            st.link_button("View Source", review['url'], use_container_width=True)

                    st.markdown(f"**Snippet:**")
                    st.write(review.get('snippet', 'No snippet available'))

                    st.markdown("---")

        # Issue discussions
        issue_discussions = web_search_data.get('issue_discussions', [])
        if issue_discussions:
            st.subheader("⚠️ Issue Discussions")
            st.write(f"Found **{len(issue_discussions)}** discussions about issues")

            for i, issue in enumerate(issue_discussions[:5], 1):
                with st.expander(f"{i}. {issue.get('title', 'No title')[:80]}..."):
                    st.caption(f"🌐 {issue.get('source', 'Unknown')} | 📅 {issue.get('date', 'N/A')}")
                    st.write(issue.get('snippet', 'No details available'))
                    if issue.get('url'):
                        st.markdown(f"[Read more →]({issue['url']})")

        # Reddit discussions
        reddit_discussions = web_search_data.get('reddit_discussions', [])
        if reddit_discussions:
            st.subheader("💬 Reddit Discussions")
            st.write(f"Found **{len(reddit_discussions)}** Reddit threads")

            for i, discussion in enumerate(reddit_discussions[:5], 1):
                with st.expander(f"{i}. {discussion.get('title', 'No title')[:80]}..."):
                    st.caption(f"🌐 {discussion.get('source', 'Unknown')} | 📅 {discussion.get('date', 'N/A')}")
                    st.write(discussion.get('snippet', 'No details available'))
                    if discussion.get('url'):
                        st.markdown(f"[Read more →]({discussion['url']})")

    # Comparisons Tab
    with review_tab3:
        st.subheader("Product Comparisons")

        comparison_articles = web_search_data.get('comparison_articles', [])

        if not comparison_articles:
            st.info("No comparison articles found.")
        else:
            st.write(f"Found **{len(comparison_articles)}** comparison articles")
            st.markdown("---")

            for i, comparison in enumerate(comparison_articles, 1):
                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"### {i}. {comparison.get('title', 'No title')}")
                        st.caption(f"🌐 **Source:** {comparison.get('source', 'Unknown')} | 📅 {comparison.get('date', 'N/A')}")

                    with col2:
                        if comparison.get('url'):
                            st.link_button("View Article", comparison['url'], use_container_width=True)

                    st.markdown(f"**Snippet:**")
                    st.write(comparison.get('snippet', 'No snippet available'))

                    st.markdown("---")

        # Video reviews
        video_reviews = web_search_data.get('video_reviews', [])
        if video_reviews:
            st.subheader("🎥 Video Reviews")
            st.write(f"Found **{len(video_reviews)}** video reviews")

            for i, video in enumerate(video_reviews, 1):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{i}. {video.get('title', 'No title')}**")
                    st.caption(f"📺 {video.get('channel', 'Unknown channel')}")

                with col2:
                    if video.get('url'):
                        st.link_button("▶️ Watch", video['url'], use_container_width=True)

    # Summary Tab
    with review_tab4:
        st.subheader("Reviews Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Amazon Reviews", len(amazon_reviews))

        with col2:
            st.metric("External Reviews", len(web_search_data.get('external_reviews', [])))

        with col3:
            st.metric("Comparisons", len(web_search_data.get('comparison_articles', [])))

        with col4:
            st.metric("Total Sources", web_search_data.get('total_sources', 0))

        st.markdown("---")

        # Key findings
        key_findings = web_search_data.get('key_findings', [])
        if key_findings:
            st.subheader("🔑 Key Findings from External Sources")
            for i, finding in enumerate(key_findings, 1):
                st.markdown(f"{i}. {finding}")

            st.markdown("---")

        # Red flags
        red_flags = web_search_data.get('red_flags', [])
        if red_flags:
            st.subheader("⚠️ Red Flags Detected")
            for flag in red_flags:
                st.warning(f"⚠️ {flag}")

            st.markdown("---")
        else:
            st.success("✅ No major red flags detected")
            st.markdown("---")

        # Sentiment
        overall_sentiment = web_search_data.get('overall_sentiment', 'unknown')
        st.subheader("💭 Overall External Sentiment")

        if overall_sentiment == 'positive':
            st.success(f"✅ **Positive** - External sources are generally favorable")
        elif overall_sentiment == 'negative':
            st.error(f"❌ **Negative** - External sources raise concerns")
        elif overall_sentiment == 'mixed':
            st.warning(f"⚖️ **Mixed** - External sources have varied opinions")
        else:
            st.info(f"❓ **Unknown** - Not enough data to determine sentiment")

        st.markdown("---")

        # Amazon vs External comparison
        if amazon_reviews and web_search_data:
            st.subheader("📊 Amazon vs External Sources")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Amazon Reviews:**")
                # Calculate average rating safely
                try:
                    ratings = []
                    for r in amazon_reviews:
                        rating_str = r.get('rating', '0')
                        if isinstance(rating_str, str):
                            # Extract first number from string (e.g., "5.0 out of 5 stars" -> 5.0)
                            rating_parts = rating_str.split()
                            if rating_parts:
                                try:
                                    ratings.append(float(rating_parts[0]))
                                except ValueError:
                                    pass
                        elif isinstance(rating_str, (int, float)):
                            ratings.append(float(rating_str))

                    avg_rating = sum(ratings) / len(ratings) if ratings else 0
                except Exception:
                    avg_rating = 0

                st.metric("Average Rating", f"{avg_rating:.1f}⭐")
                verified_count = sum(1 for r in amazon_reviews if r.get('verified', False))
                st.metric("Verified Purchases", f"{verified_count}/{len(amazon_reviews)}")

            with col2:
                st.markdown("**External Sources:**")
                st.metric("Overall Sentiment", overall_sentiment.capitalize())
                st.metric("Sources Analyzed", web_search_data.get('total_sources', 0))


def main():
    """Main application"""
    initialize_session_state()

    # Title
    st.title("🛍️ Amazon Product Analysis Agent")

    # Sidebar
    show_sidebar()

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Product Analysis", "📝 Reviews", "💬 Q&A Chat"])

    with tab1:
        product_analysis_tab()

    with tab2:
        reviews_tab()

    with tab3:
        qa_tab()


if __name__ == "__main__":
    main()
