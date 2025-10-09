# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered Amazon product analysis agent that scrapes product data from Amazon, analyzes it using Google Gemini LLM via LangChain, and provides conversational Q&A with Redis-backed persistent memory. The application uses Streamlit for the web interface.

## Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify setup (runs all checks)
python verify_setup.py
```

### Running the Application
```bash
# Start the Streamlit web application
streamlit run app.py

# Run programmatic examples (demonstrates module usage)
python example_usage.py
```

### Redis Management
```bash
# Start Redis (required for Q&A chat memory)
redis-server

# Or using brew on macOS
brew services start redis

# Check Redis is running
redis-cli ping  # Should return "PONG"

# Using Docker
docker run -d -p 6379:6379 --name redis redis:latest
```

## Architecture

### Core Components Flow

1. **Scraping Pipeline** (`src/scraper.py`)
   - Extracts ASIN from Amazon URLs
   - Scrapes product details, reviews, seller info
   - Implements respectful scraping with delays (2-3s between requests)
   - Returns structured dictionary

2. **Analysis Pipeline** (`src/analyzer.py`)
   - Takes scraped data as input
   - Loads prompt template from `config/prompts/product_analysis_prompt.txt`
   - Uses LangChain's `LLMChain` with Google Gemini
   - Formats product data into structured markdown sections
   - Returns comprehensive analysis with pros/cons, seller evaluation, recommendation

3. **Q&A Pipeline** (`src/chatbot.py`)
   - Two-layer architecture:
     - `RedisChatMemory`: Handles Redis storage for messages and product data
     - `ProductChatbot`: Manages LLM conversation with context
   - Session-based conversations keyed by `chat:{session_id}:messages`
   - Product data stored separately at `chat:{session_id}:product_data`
   - Formats conversation history (last 6 messages) as context for LLM
   - Answers questions based only on scraped product data

4. **Web Interface** (`app.py`)
   - Streamlit multi-tab interface (Analysis + Q&A)
   - Uses `st.session_state` for:
     - Product data persistence
     - Analysis results
     - Component initialization (scraper, analyzer, chatbot)
     - Session ID (UUID-based)
   - Environment variables loaded via `load_dotenv()` with explicit path resolution

### Critical Architecture Details

**Environment Variable Handling:**
- The app uses `BASE_DIR = Path(__file__).resolve().parent` to find project root
- `load_dotenv(dotenv_path=BASE_DIR / '.env')` ensures .env is loaded from project root regardless of CWD
- `GOOGLE_API_KEY` is passed directly to `ProductAnalyzer` and `ProductChatbot` classes
- API key validation happens in the class constructors with helpful error messages

**Redis Memory Pattern:**
- Conversations are stored as JSON-serialized lists in Redis
- Each message is a dict with `role` and `content`
- Product data is stored as a single JSON blob per session
- Memory persists across application restarts
- Clear operations only delete specific session data

**LangChain Integration:**
- Both analyzer and chatbot use `ChatGoogleGenerativeAI` directly (not via chains)
- Analyzer uses `LLMChain` with `PromptTemplate` for structured analysis
- Chatbot manually constructs prompts with product context + history + question
- Temperature: 0.3 for analysis (consistent), 0.5 for chatbot (conversational)

## Configuration

### Environment Variables (.env)
```bash
# Google API Key for Gemini
GOOGLE_API_KEY=your_api_key_here

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD=your_password  # Optional
```

**Get your API key:** https://makersuite.google.com/app/apikey

### Prompt Template
The analysis prompt is stored at `config/prompts/product_analysis_prompt.txt` and defines:
- Analysis structure (Executive Summary, Pros/Cons, Seller Analysis, etc.)
- Categorization of pros/cons by Quality/Performance/Value/Features/Design
- Guidelines for LLM behavior (quote reviews, be objective, state when info missing)

## Code Patterns

### Adding New Scraper Fields
When adding new data points to scrape:
1. Add extraction method to `AmazonScraper` class (e.g., `_extract_specifications()`)
2. Call method in `scrape_product()` and add to returned dict
3. Update `ProductAnalyzer.format_product_data()` to include in LLM context
4. Update prompt template if new analysis section needed

### Adding New Analysis Sections
1. Modify `config/prompts/product_analysis_prompt.txt` with new section
2. No code changes required - LLM follows prompt structure
3. Test with multiple products to ensure consistency

### Modifying Q&A Behavior
1. Adjust `qa_template` string in `ProductChatbot.__init__()`
2. Modify `format_product_context()` to change what data is sent to LLM
3. Adjust history window size in `format_history()` (currently last 6 messages)

### Session Management
Sessions are identified by UUID stored in `st.session_state.session_id`. To implement multi-user support:
1. Session ID generation happens in `initialize_session_state()`
2. All Redis operations use this session_id as namespace
3. To clear all user data: `chatbot.clear_all_data(session_id)`

## Testing Product URLs

Valid Amazon URL formats supported:
- `https://www.amazon.com/dp/XXXXXXXXXX`
- `https://www.amazon.com/gp/product/XXXXXXXXXX`
- `https://www.amazon.com/product/XXXXXXXXXX`
- Full product URLs with titles also work

The scraper extracts the ASIN (10-character alphanumeric) via regex patterns.

## API Limits and Rate Considerations

**Google Gemini:**
- Free tier: 60 requests/minute
- Each analysis = 1 request
- Each Q&A question = 1 request
- Rate limit errors will show in UI

**Amazon Scraping:**
- Built-in 2-second delay between product page and reviews page
- Avoid scraping more than ~20-30 products per hour
- Some products may have different HTML structures (graceful failures return "N/A")

## Common Development Tasks

### Modifying the Analysis Structure
Edit `config/prompts/product_analysis_prompt.txt` - no code changes needed.

### Changing LLM Models
Update `model_name` parameter in `ProductAnalyzer` or `ProductChatbot` initialization:
- Default: `"gemini-2.0-flash-exp"` (Gemini 2.0 experimental)
- Other options: `"gemini-1.5-pro"`, `"gemini-1.5-flash"`

### Adjusting Review Scraping Limit
In `src/scraper.py`, modify `max_reviews` parameter in `_scrape_reviews()` method (default: 200).
- The method now handles pagination automatically
- Scrapes up to 20 pages (10 reviews per page)
- Each page request includes a 2-second delay for respectful scraping
- Progress is printed to console during scraping

### Adding New Scraper Methods
Follow the pattern: `_extract_[field_name](self, soup: BeautifulSoup) -> str/List`
- Use multiple CSS selectors as fallbacks
- Return "N/A" or empty list if not found
- Add error handling for missing elements

### Debugging Redis Issues
```python
# Connect to Redis CLI
redis-cli

# Check keys for a session
KEYS chat:*

# View messages for session
LRANGE chat:{session_id}:messages 0 -1

# View product data
GET chat:{session_id}:product_data

# Clear all chat data
FLUSHDB
```

## File Locations

- **Web app:** `app.py`
- **Core modules:** `src/scraper.py`, `src/analyzer.py`, `src/chatbot.py`
- **Prompt template:** `config/prompts/product_analysis_prompt.txt`
- **Setup verification:** `verify_setup.py`
- **Usage examples:** `example_usage.py`
- **Documentation:** `README.md`, `QUICKSTART.md`, `GCP_SETUP_GUIDE.md`

## Error Handling Patterns

The codebase uses these error handling conventions:
- Scraper: Raises `ValueError` for invalid URLs, `requests.exceptions.RequestException` for scraping failures
- Analyzer: Raises `Exception` with descriptive message on LLM failures
- Chatbot: Raises `ValueError` if no product data, `Exception` for LLM failures
- Streamlit UI: Catches exceptions and displays user-friendly error messages with `st.error()`

When adding new features, follow this pattern to maintain consistent UX.