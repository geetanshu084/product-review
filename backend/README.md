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
│       ├── product_analysis_prompt.txt     # Main analysis
│       ├── agent_prompt.txt                # Chat/Q&A
│       ├── product_extraction_prompt.txt   # HTML extraction
│       ├── structured_extraction_prompt.txt # JSON output
│       ├── sentiment_analysis_prompt.txt   # Review sentiment
│       ├── review_filter_prompt.txt        # Filter reviews
│       ├── comparison_filter_prompt.txt    # Filter comparisons
│       ├── reddit_filter_prompt.txt        # Filter Reddit
│       ├── news_filter_prompt.txt          # Filter news
│       ├── key_findings_prompt.txt         # Extract insights
│       └── red_flags_prompt.txt            # Warning detection
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

## API Structure

### Routes

#### Products API (`api/routes/products.py`)

```
POST /api/v1/products/scrape-and-analyze
- Scrapes product and runs analysis
- Body: { url, include_price_comparison, include_web_search }
- Returns: ProductData + analysis markdown

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

**Analysis & Extraction:**
- `product_analysis_prompt.txt` - Main product analysis prompt with comprehensive structure
- `product_extraction_prompt.txt` - HTML data extraction using LLM
- `structured_extraction_prompt.txt` - JSON output for missing/incomplete fields

**Chat & Q&A:**
- `agent_prompt.txt` - Chatbot system prompt for Q&A about products

**Web Search Filtering:**
- `review_filter_prompt.txt` - Filter relevant external reviews
- `comparison_filter_prompt.txt` - Filter product comparison articles
- `reddit_filter_prompt.txt` - Filter Reddit discussions
- `news_filter_prompt.txt` - Filter news articles

**Analysis Enhancement:**
- `sentiment_analysis_prompt.txt` - Analyze review sentiment
- `key_findings_prompt.txt` - Extract key insights from external sources
- `red_flags_prompt.txt` - Identify warning signs and concerns

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

1. Update prompt template in `config/prompts/product_analysis_prompt.txt`
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
