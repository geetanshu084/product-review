# Backend Documentation

This is the backend service for the Product Analysis Agent, built with FastAPI and Python. It handles web scraping, LLM-powered analysis, price comparison, web search integration, and conversational Q&A.

## Architecture Overview

The backend follows a modular architecture with clear separation of concerns:

```
Request → API Routes → Services → Core Logic (Scrapers/Analyzers) → LLM Providers → Response
                                  ↓
                              Redis Cache
```

### Key Architectural Patterns

- **Service Layer Pattern**: Business logic separated from API routes
- **Strategy Pattern**: Multiple LLM providers with unified interface
- **Workflow Orchestration**: LangGraph for complex multi-step analysis
- **Caching Layer**: Redis for performance optimization with 24-hour TTL
- **Configuration Management**: Centralized environment variables and prompt templates

## Directory Structure

```
backend/
├── api/                          # FastAPI application
│   ├── main.py                   # Application entry point
│   ├── core/
│   │   ├── config.py             # Configuration and environment variables
│   │   └── middleware.py         # CORS and other middleware
│   ├── routes/                   # API endpoint definitions
│   │   ├── products.py           # Product scraping and analysis endpoints
│   │   └── chat.py               # Q&A chat endpoints
│   ├── services/                 # Business logic layer
│   │   ├── product_service.py    # Product analysis orchestration
│   │   └── chat_service.py       # Chat session management
│   └── models/
│       └── schemas.py            # Pydantic request/response models
│
├── src/                          # Core business logic
│   ├── scrapers/                 # Web scraping modules
│   │   ├── base_scraper.py       # Abstract base class for scrapers
│   │   ├── amazon_scraper.py     # Amazon-specific scraper
│   │   └── flipkart_scraper.py   # Flipkart-specific scraper
│   ├── analysis/                 # Analysis modules
│   │   ├── price_comparison.py   # Multi-platform price comparison
│   │   └── web_search.py         # External reviews and web search
│   ├── llm_provider.py           # Multi-provider LLM abstraction
│   ├── llm_extractor.py          # LLM-based data extraction
│   ├── analyzer.py               # Product analysis with LLM
│   ├── chatbot.py                # Q&A chatbot with memory
│   ├── redis_manager.py          # Redis connection management
│   ├── prompts.py                # Prompt management utilities
│   ├── product_orchestrator.py   # Legacy orchestration (deprecated)
│   └── workflow_orchestrator.py  # LangGraph workflow orchestration
│
├── config/
│   └── prompts/                  # LLM prompt templates
│       ├── agent_prompt.txt
│       ├── product_extraction_prompt.txt
│       ├── structured_extraction_prompt.txt
│       ├── sentiment_analysis_prompt.txt
│       ├── review_filter_prompt.txt
│       ├── comparison_filter_prompt.txt
│       ├── reddit_filter_prompt.txt
│       ├── news_filter_prompt.txt
│       ├── web_search_summary_prompt.txt
│       ├── key_findings_prompt.txt
│       └── red_flags_prompt.txt
│
├── docs/                         # Technical documentation
│   ├── ARCHITECTURE.md
│   ├── LLM_PROVIDERS.md
│   ├── PRICE_COMPARISON.md
│   └── WEB_SEARCH_INTEGRATION.md
│
├── tests/                        # Test suite
│   ├── test_analysis.py
│   └── test_web_search_integration.py
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── example_usage.py              # Example usage scripts
└── verify_setup.py               # Setup verification script
```

## Core Components

### 1. Scraper System

The scraper system supports multiple e-commerce platforms with a unified interface.

#### Base Scraper (`src/scrapers/base_scraper.py`)

Abstract base class defining the scraper interface:

```python
class BaseScraper(ABC):
    @abstractmethod
    def scrape_product(self, url: str) -> Dict

    @abstractmethod
    def _extract_title(self, soup: BeautifulSoup) -> str

    @abstractmethod
    def _extract_price(self, soup: BeautifulSoup) -> str
    # ... more extraction methods
```

#### Amazon Scraper (`src/scrapers/amazon_scraper.py`)

- Extracts ASIN from various Amazon URL formats
- Handles product details, specifications, reviews, Q&A
- Implements pagination for reviews (up to 20 pages, 200 reviews)
- Uses multiple CSS selector strategies for robustness
- Respectful scraping with 2-second delays between requests

Key features:
- Rating and review count extraction
- Feature bullets and description parsing
- Technical specifications table extraction
- Bank offers and seller information
- Review pagination with verified purchase detection

#### Flipkart Scraper (`src/scrapers/flipkart_scraper.py`)

- Extracts product ID from Flipkart URLs
- Handles dynamic CSS classes and JavaScript-loaded content
- Multiple image extraction strategies (main, thumbnails, CDN fallback)
- LLM-enhanced data extraction for missing fields
- Synthetic review generation from LLM summaries

Key features:
- Image URL conversion to full-size (832x832)
- Specification extraction from key-value pairs
- Seller information and rating extraction
- LLM fallback for missing structured data
- Synthetic reviews when individual reviews unavailable

### 2. LLM Provider System (`src/llm_provider.py`)

Unified interface for multiple LLM providers:

**Supported Providers:**
- Google Gemini (default: `gemini-2.0-flash-exp`)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude
- Ollama (local models)
- Groq
- Cohere

**Configuration:**
```python
provider = LLMProvider(
    provider="google",  # or "openai", "anthropic", "ollama", "groq", "cohere"
    model="gemini-2.0-flash-exp",
    temperature=0.3,
    api_key=os.getenv("GOOGLE_API_KEY")
)
llm = provider.get_llm()
```

### 3. Analysis System

#### Product Analyzer (`src/analyzer.py`)

Generates comprehensive product analysis using LLM:

**Analysis Sections:**
- Executive Summary
- Product Details & Specifications
- Price Analysis
- Pros & Cons (categorized by Quality, Performance, Value, Features, Design)
- Bank Offers & Discounts
- Seller/Brand Analysis
- External Reviews & Reddit Discussions
- Red Flags & Key Findings
- Recommendations

**Features:**
- Template-based prompts from `config/prompts/`
- Structured data formatting for LLM context
- Markdown output for rich formatting
- Temperature: 0.3 for consistent analysis

#### LLM Extractor (`src/llm_extractor.py`)

Extracts structured data from raw HTML using LLM:

- Missing field extraction (title, price, rating, etc.)
- Review summarization
- Specification parsing
- Feature extraction

### 4. Price Comparison (`src/analysis/price_comparison.py`)

Multi-platform price discovery using Serper API:

**Features:**
- Search across Amazon, Flipkart, Snapdeal, Croma, Vijay Sales
- Price extraction and normalization
- Availability status detection
- Savings calculation
- Competitor URL discovery

**Search Strategy:**
```python
def search_product_prices(product_name: str, brand: str) -> PriceComparison
    # Searches: "{brand} {product_name} price"
    # Filters by domain (amazon.in, flipkart.com, etc.)
    # Returns: current_price, alternative_prices[], best_price, savings
```

### 5. Web Search Integration (`src/analysis/web_search.py`)

Aggregates external product information using Serper API:

**Data Sources:**
- External reviews (tech blogs, review sites)
- Comparison articles
- Reddit discussions (multiple subreddits)
- News articles
- Video reviews (YouTube)
- Issue discussions

**LLM Filtering:**
- Relevance scoring for search results
- Sentiment analysis
- Key findings extraction
- Red flag detection

**Output:**
```python
{
    "external_reviews": [...],
    "comparison_articles": [...],
    "reddit_discussions": [...],
    "news_articles": [...],
    "video_reviews": [...],
    "key_findings": [...],
    "red_flags": [...],
    "overall_sentiment": {
        "sentiment": "Positive/Negative/Mixed",
        "confidence": "High/Medium/Low",
        "summary": "..."
    }
}
```

### 6. Chatbot System (`src/chatbot.py`)

LangChain-powered Q&A with Redis-backed memory:

**Architecture:**
```
User Question → ProductChatbot → RedisChatMemory → Redis
                    ↓
                LLM Provider
                    ↓
                  Answer
```

**Features:**
- Session-based conversations
- Product context injection
- Conversation history (last 6 messages)
- Persistent memory across restarts

**Redis Schema:**
- Messages: `chat:{session_id}:messages` (JSON list)
- Product data: `chat:{session_id}:product_data` (JSON object)

### 7. Workflow Orchestration (`src/workflow_orchestrator.py`)

LangGraph-based workflow for complex analysis:

**Workflow States:**
1. Start → Product Extraction
2. Product Extraction → Review Analysis
3. Review Analysis → Price Comparison (optional)
4. Price Comparison → Web Search (optional)
5. Web Search → Synthesis
6. Synthesis → End

**Features:**
- State management for multi-step analysis
- Conditional branching based on options
- Error recovery and retry logic
- Progress tracking

### 8. Redis Manager (`src/redis_manager.py`)

Centralized Redis connection management:

**Features:**
- Connection pooling
- Automatic reconnection
- Health checks
- TTL management (default: 24 hours)

**Cache Keys:**
- Product data: `product:{asin}`
- Chat sessions: `chat:{session_id}:*`

## API Structure

### Routes

#### Products API (`api/routes/products.py`)

```
POST /api/v1/products/scrape-and-analyze
- Scrapes product and runs analysis
- Body: { url, include_price_comparison, include_web_search }
- Returns: ProductData + analysis markdown

GET /api/v1/products/{product_id}
- Retrieves cached product data
- Returns: ProductData
```

#### Chat API (`api/routes/chat.py`)

```
POST /api/v1/chat/ask
- Ask question about product
- Body: { session_id, product_id, question }
- Returns: { answer }

GET /api/v1/chat/history/{session_id}
- Get conversation history
- Returns: { history: [{ role, content }] }

DELETE /api/v1/chat/clear/{session_id}
- Clear chat history
- Returns: { message }
```

### Services

#### Product Service (`api/services/product_service.py`)

Orchestrates product analysis workflow:

```python
async def scrape_and_analyze_product(
    url: str,
    include_price_comparison: bool = False,
    include_web_search: bool = False
) -> Tuple[ProductData, str]
```

#### Chat Service (`api/services/chat_service.py`)

Manages chat sessions and Q&A:

```python
async def ask_question(
    session_id: str,
    product_id: str,
    question: str
) -> str
```

### Models (`api/models/schemas.py`)

Pydantic schemas for request/response validation:

- `ScrapeAndAnalyzeRequest`
- `ProductResponse`
- `ChatRequest`
- `ChatResponse`
- `ErrorResponse`

## Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# LLM Provider Configuration
LLM_PROVIDER=google          # google, openai, anthropic, ollama, groq, cohere
LLM_MODEL=gemini-2.0-flash-exp
GOOGLE_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here

# Web Search API
SERPER_API_KEY=your_key_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD=your_password  # Optional

# Cache Configuration
CACHE_TTL=86400              # 24 hours in seconds

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Product Analysis Agent
```

### Prompt Templates

Prompts are stored in `config/prompts/` for easy modification:

- `agent_prompt.txt` - Main analysis prompt with structure guidelines
- `product_extraction_prompt.txt` - Data extraction from HTML
- `structured_extraction_prompt.txt` - JSON output for missing fields
- `sentiment_analysis_prompt.txt` - Review sentiment analysis
- `*_filter_prompt.txt` - Relevance filtering for web search results
- `web_search_summary_prompt.txt` - Web search aggregation
- `key_findings_prompt.txt` - Important insights extraction
- `red_flags_prompt.txt` - Warning signs detection

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Verify setup
python verify_setup.py
```

### Running

```bash
# Start Redis
redis-server

# Start FastAPI (with auto-reload)
python -m api.main

# API available at: http://localhost:8000
# Docs available at: http://localhost:8000/api/v1/docs
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_analysis.py

# Run with coverage
pytest --cov=src tests/

# Run example usage
python example_usage.py
```

## Adding New Features

### Adding a New Scraper

1. Create `src/scrapers/platform_scraper.py` inheriting from `BaseScraper`
2. Implement required extraction methods
3. Add platform detection in `product_service.py`
4. Update API documentation

### Adding a New LLM Provider

1. Add provider configuration in `src/llm_provider.py`
2. Add API key to `.env.example`
3. Update `docs/LLM_PROVIDERS.md`
4. Test with `verify_setup.py`

### Adding a New Analysis Section

1. Update prompt template in `config/prompts/agent_prompt.txt`
2. No code changes required (LLM follows prompt structure)
3. Test with multiple products

### Adding a New API Endpoint

1. Define route in `api/routes/`
2. Create service method in `api/services/`
3. Add Pydantic schemas in `api/models/schemas.py`
4. Update API documentation

## Troubleshooting

### Redis Issues

```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# View cache keys
redis-cli KEYS "*"

# Clear all cache
redis-cli FLUSHDB

# Monitor Redis commands
redis-cli MONITOR
```

### Scraping Issues

- Check network connectivity
- Verify User-Agent headers in scraper
- Inspect HTML structure (may change over time)
- Check rate limits (2-second delay between requests)
- Review scraper logs for CSS selector mismatches

### LLM Issues

- Verify API key is set correctly
- Check API rate limits for your provider
- Monitor token usage and costs
- Adjust temperature for desired consistency
- Review prompt templates for clarity

### CORS Issues

- Update `BACKEND_CORS_ORIGINS` in `api/core/config.py`
- Add your frontend port to allowed origins
- Restart backend after configuration changes

## Performance Optimization

### Caching Strategy

- Product data cached for 24 hours in Redis
- Chat sessions persist indefinitely until cleared
- Cache key structure: `{type}:{id}`
- TTL configured via `CACHE_TTL` environment variable

### Request Optimization

- Use `include_price_comparison=false` to skip price search
- Use `include_web_search=false` to skip external reviews
- Adjust review pagination limit in scraper
- Consider async scraping for multiple products

### LLM Optimization

- Use faster models for simple tasks (gemini-2.0-flash-exp)
- Use larger models for complex analysis (gemini-1.5-pro)
- Batch multiple extractions in single LLM call
- Cache LLM responses in Redis

## API Rate Limits

### Google Gemini
- Free tier: 60 requests/minute
- Each analysis = 3-5 requests (extraction + analysis + chat)
- Consider request batching for high volume

### Serper API
- Free tier: 2,500 searches/month
- Each price comparison = 1 search
- Each web search analysis = 6-8 searches

### Amazon/Flipkart
- No official rate limits, but respect robots.txt
- Implement 2-second delays between requests
- Avoid scraping more than 20-30 products per hour

## Security Considerations

- Store API keys in `.env` (never commit to git)
- Use `.gitignore` to exclude `.env` files
- Validate all user inputs with Pydantic
- Sanitize URLs before scraping
- Implement rate limiting in production
- Use HTTPS for API in production
- Enable CORS only for trusted origins

## LLM Providers

Supports multiple LLM providers! Choose the one that fits your needs:

| Provider | Setup | Cost |
|----------|-------|------|
| **Google Gemini** (Default) | [Get API Key](https://makersuite.google.com/app/apikey) | Free tier |
| **OpenAI** | [Get API Key](https://platform.openai.com/api-keys) | Paid |
| **Anthropic Claude** | [Get API Key](https://console.anthropic.com/) | Paid |
| **Ollama** (Local) | [Install Ollama](https://ollama.ai/) | Free |
| **Groq** | [Get API Key](https://console.groq.com/) | Free tier |
| **Cohere** | [Get API Key](https://dashboard.cohere.com/) | Paid |

See [docs/LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md) for detailed setup instructions.
