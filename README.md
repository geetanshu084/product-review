# Amazon Product Analysis Agent

An intelligent Python-based agent that analyzes Amazon products by scraping product information and reviews, then uses Google Gemini LLM via LangChain to provide comprehensive analysis and answer user questions interactively.

## Features

- **Amazon Product Scraper**: Extracts product details, pricing, ratings, reviews, and seller information
- **AI-Powered Analysis**: Uses Google Gemini to provide structured product analysis with pros/cons
- **Multi-Platform Price Comparison**: Compare prices across Amazon, Flipkart, eBay, Walmart, and more (using Serper API)
- **Conversational Q&A with Web Search**: Ask questions about products with automatic web search for current information
- **Persistent Memory**: Redis-backed conversation history for seamless multi-session interactions
- **Interactive Web UI**: Clean Streamlit interface for easy product analysis and chat

## Project Structure

```
amazon-review/
├── app.py                              # Streamlit web application
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variables template
├── README.md                           # Project documentation
├── config/
│   └── prompts/
│       └── product_analysis_prompt.txt # LLM prompt template
├── src/
│   ├── scraper.py                     # Amazon product scraper
│   ├── analyzer.py                    # LLM analysis engine
│   ├── chatbot.py                     # Q&A system with Redis memory & web search
│   └── price_comparison.py            # Multi-platform price comparison
├── docs/
│   ├── PRICE_COMPARISON.md            # Price comparison feature docs
│   └── WEB_SEARCH_QA.md               # Web search feature docs
└── utils/                             # Utility functions (optional)
```

## Prerequisites

- Python 3.8 or higher
- Redis server (for Q&A conversation memory)
- Google API Key for Gemini (free from makersuite.google.com)
- Serper API Key (optional, for price comparison and web search - free tier: 2,500 searches/month from serper.dev)

## Installation

### 1. Clone or Download the Project

```bash
cd amazon-review
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and Start Redis

**macOS (using Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Windows:**
- Download Redis from https://github.com/microsoftarchive/redis/releases
- Extract and run `redis-server.exe`

**Docker (All platforms):**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### 5. Configure API Keys

1. Get your Google API key:
   - Go to https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API key"
   - Copy the generated API key

2. Get your Serper API key (optional, for price comparison and web search):
   - Go to https://serper.dev/
   - Sign up for a free account
   - Get your API key from the dashboard
   - Free tier includes 2,500 free searches/month

3. Copy and configure `.env`:
   ```bash
   cp .env.example .env
   ```

4. Add your API keys to `.env`:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here

   # Serper API Key (optional - for price comparison and web search)
   SERPER_API_KEY=your_serper_api_key_here

   # Redis configuration (default values)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   # REDIS_PASSWORD=your_password  # Uncomment if Redis requires authentication
   ```

## Usage

### 1. Start the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### 2. Analyze a Product

1. Go to the **Product Analysis** tab
2. Paste an Amazon product URL (e.g., `https://www.amazon.com/dp/B08N5WRWNW`)
3. Click **"Analyze Product"**
4. Wait for the scraping and analysis to complete (15-30 seconds)
5. View the comprehensive analysis with:
   - Executive summary
   - Product overview
   - Pros and cons (categorized)
   - Seller analysis
   - After-sales service evaluation
   - Buy/Wait/Avoid recommendation

### 3. Ask Questions (Q&A Tab)

1. After analyzing a product, switch to the **Q&A Chat** tab
2. Type your question in the input field
3. Click **Send** to get AI-powered answers based on the product data
4. Continue the conversation - the system remembers context
5. Use **Clear Chat** to start a new conversation

**Example questions:**

*Product Information:*
- "What are the main complaints about this product?"
- "Is this good for professional use?"
- "What do customers say about durability?"
- "Does it come with a warranty?"

*Price Comparison (uses stored data):*
- "Where can I buy this product?"
- "What's the best price available?"
- "Show me prices on Amazon vs Flipkart"
- "Which platform has the cheapest price?"
- "How much can I save if I buy from the cheapest platform?"

*Current Information (triggers web search):*
- "What is the current price?"
- "Compare this with Samsung Galaxy S24"
- "Is this available in stock?"

## Features in Detail

### Amazon Product Scraper (`src/scraper.py`)

- Extracts ASIN from product URLs
- Scrapes comprehensive product data:
  - Product title, brand, price
  - Overall rating and total reviews
  - Product description and features
  - Up to 200 customer reviews with pagination support
  - Seller name and rating
- Handles various Amazon URL formats
- Implements respectful scraping with delays
- Robust error handling

### LLM Analysis Engine (`src/analyzer.py`)

- Uses Google Gemini Pro via LangChain
- Structured analysis with predefined sections
- Categorizes pros and cons by type
- Evaluates seller trustworthiness
- Provides actionable recommendations
- Formats output in clean markdown

### Multi-Platform Price Comparison (`src/price_comparison.py`)

- Compares prices across Amazon, Flipkart, eBay, Walmart, and more
- Exact product matching with attribute filtering (brand, model, storage, RAM, color)
- Finds best deals with savings calculation
- Price statistics (min, max, average, median)
- Platform-wise breakdown with direct purchase links
- Powered by Serper Shopping API
- See [docs/PRICE_COMPARISON.md](docs/PRICE_COMPARISON.md) for details

### Conversational Q&A System (`src/chatbot.py`)

- Redis-backed persistent memory with full product data (including price comparison)
- Maintains conversation context
- Session-based conversation history
- Answers based on:
  - Scraped product data and reviews
  - **Multi-platform price comparison** (saved to Redis during analysis)
  - **Intelligent web search** for current information
- Can answer questions like:
  - "Where can I buy this product?" (uses price comparison data)
  - "What's the best price available?" (uses price comparison data)
  - "Show me prices on Amazon vs Flipkart" (uses price comparison data)
  - "What is the current price?" (triggers web search)
  - "Compare with Samsung Galaxy S24" (triggers web search)
- Keyword-based search triggering (price, compare, latest, etc.)
- Seamless integration of price comparison and web search results
- Clear indication when information is unavailable
- Memory survives application restarts
- See [docs/WEB_SEARCH_QA.md](docs/WEB_SEARCH_QA.md) for details

### Streamlit Web Interface (`app.py`)

- Two-tab interface (Analysis + Q&A)
- Real-time progress indicators
- Error handling with user-friendly messages
- Download analysis as markdown
- Configuration status indicators
- Responsive design

## API Limits and Considerations

### Google Gemini API
- Free tier: 60 requests per minute
- Each analysis uses 1 request
- Each Q&A question uses 1 request
- If you hit rate limits, wait a minute and try again

### Amazon Scraping
- Be respectful: 2-3 second delays between requests
- Don't scrape aggressively or you may be blocked
- Use the tool for personal analysis only
- Some product pages may have different HTML structures

## Troubleshooting

### Redis Connection Errors

**Error:** `Connection refused` or `Error connecting to Redis`

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start Redis:
# macOS/Linux:
redis-server

# Or using brew services:
brew services start redis

# Check Redis status:
brew services list
```

### Google API Key Errors

**Error:** `Google API Key not configured` or `Authentication error`

**Solution:**
- Verify your `GOOGLE_API_KEY` is set in `.env` file
- Get your API key from: https://makersuite.google.com/app/apikey
- Make sure the API key is valid and not expired
- Check that you haven't exceeded the free tier rate limits

### Scraping Failures

**Error:** `Failed to scrape product`

**Solution:**
- Verify the URL is a valid Amazon product page
- Check your internet connection
- Try a different product URL
- Amazon may have temporarily blocked your IP (wait and try again)
- Some products may have different page structures

### Import Errors

**Error:** `ModuleNotFoundError`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini | Yes | - |
| `SERPER_API_KEY` | Serper API key for price comparison & web search | No | None |
| `REDIS_HOST` | Redis server hostname | No | localhost |
| `REDIS_PORT` | Redis server port | No | 6379 |
| `REDIS_DB` | Redis database number | No | 0 |
| `REDIS_PASSWORD` | Redis password | No | None |

## Limitations

1. **Scraping Reliability**: Amazon's HTML structure may change, affecting scraping accuracy
2. **Review Limit**: Scrapes up to 200 reviews with pagination (can take 40+ seconds for full scraping)
3. **Rate Limits**: Subject to Google Gemini API rate limits
4. **Regional Variations**: Optimized for Amazon.com (other regions may need adjustments)
5. **Dynamic Content**: Some Amazon pages load content dynamically via JavaScript (not supported)

## Future Enhancements

- [x] Add price comparison with other e-commerce sites (Completed - Phase 2)
- [x] Add web search capability to Q&A chatbot (Completed - Phase 2)
- [x] Scrape more reviews with pagination support (up to 200 reviews)
- [ ] Add sentiment analysis visualization charts
- [ ] Export analysis as PDF
- [ ] Product comparison feature (side-by-side)
- [ ] Implement caching to avoid re-scraping
- [ ] Support for multiple Amazon regional domains
- [ ] Email notifications for price drops
- [ ] Historical price tracking

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this project.

## License

This project is for educational and personal use only. Please respect Amazon's Terms of Service and robots.txt when scraping.

## Disclaimer

This tool is intended for personal use only. Scraping Amazon at scale or for commercial purposes may violate Amazon's Terms of Service. Use responsibly and ethically.

---

**Built with:**
- Python 3.8+
- Streamlit
- LangChain
- Google Gemini AI
- BeautifulSoup4
- Redis

**Author:** AI Product Analysis Team

**Version:** 2.0.0 (Phase 2: Price Comparison + Web Search)
