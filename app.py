"""
Streamlit Web Interface for Amazon Product Analysis Agent
"""

import os
import uuid
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
        google_api_key = os.getenv('GOOGLE_API_KEY')
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD', None)

        if google_api_key:
            try:
                st.session_state.chatbot = ProductChatbot(
                    google_api_key=google_api_key,
                    redis_host=redis_host,
                    redis_port=redis_port,
                    redis_db=redis_db,
                    redis_password=redis_password if redis_password else None
                )
            except Exception as e:
                st.session_state.chatbot = None
                st.session_state.redis_error = str(e)
        else:
            st.session_state.chatbot = None
            st.session_state.redis_error = "GOOGLE_API_KEY not found in .env file"


def show_sidebar():
    """Display sidebar with information"""
    with st.sidebar:
        st.title("🛍️ Product Analyzer")
        st.markdown("---")

        st.markdown("""
        ### How to use:
        1. **Analyze Tab**: Paste an Amazon product URL and click "Analyze Product"
        2. **Q&A Tab**: Ask questions about the analyzed product

        ### Features:
        - Comprehensive product analysis
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

    # Max reviews slider
    max_reviews = st.slider(
        "Maximum Reviews to Scrape",
        min_value=10,
        max_value=200,
        value=100,
        step=10,
        help="Number of customer reviews to scrape (more reviews = better analysis but slower)"
    )

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
            progress_text.text(f"🔄 Scraping product details (targeting {max_reviews} reviews)...")
            progress_bar.progress(10)

            # Create scraper with specified max_reviews
            scraper = AmazonScraper(max_reviews=max_reviews)
            product_data = scraper.scrape_product(url)

            progress_bar.progress(50)
            progress_text.text(f"✅ Scraped {len(product_data.get('reviews', []))} reviews")

            st.session_state.product_data = product_data

            # Save to chatbot for Q&A
            if st.session_state.chatbot:
                st.session_state.chatbot.set_product_data(
                    st.session_state.session_id,
                    product_data
                )

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

    # Chat interface
    st.markdown("### Conversation")

    # Display chat history
    try:
        chat_history = st.session_state.chatbot.get_conversation_history(st.session_state.session_id)

        if chat_history:
            for msg in chat_history:
                if msg['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg['content'])
        else:
            st.info("💭 No conversation yet. Ask a question to get started!")

    except Exception as e:
        st.error(f"Failed to load conversation history: {str(e)}")

    # Question input
    st.markdown("---")

    col1, col2 = st.columns([5, 1])

    with col1:
        question = st.text_input(
            "Your question",
            placeholder="e.g., What are the main complaints about this product?",
            label_visibility="collapsed",
            key="question_input"
        )

    with col2:
        send_button = st.button("Send", type="primary", use_container_width=True)
        clear_button = st.button("Clear Chat", use_container_width=True)

    if send_button and question:
        with st.spinner("🤔 Thinking..."):
            try:
                answer = st.session_state.chatbot.ask(st.session_state.session_id, question)

                # Display new Q&A
                with st.chat_message("user"):
                    st.write(question)

                with st.chat_message("assistant"):
                    st.write(answer)

                # Clear input by rerunning
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to generate answer: {str(e)}")

    if clear_button:
        try:
            st.session_state.chatbot.clear_conversation(st.session_state.session_id)
            st.success("✅ Conversation cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to clear conversation: {str(e)}")


def main():
    """Main application"""
    initialize_session_state()

    # Title
    st.title("🛍️ Amazon Product Analysis Agent")

    # Sidebar
    show_sidebar()

    # Main tabs
    tab1, tab2 = st.tabs(["📊 Product Analysis", "💬 Q&A Chat"])

    with tab1:
        product_analysis_tab()

    with tab2:
        qa_tab()


if __name__ == "__main__":
    main()
