# Product Analysis Agent

An AI-powered product analysis platform that scrapes e-commerce product data from Amazon and Flipkart, analyzes it using LLMs, and provides comprehensive insights through a modern web interface.

## Features

### Core Capabilities
- **Multi-Platform Support**: Analyze products from Amazon and Flipkart
- **AI-Powered Analysis**: Comprehensive product evaluation using Google Gemini LLM
- **Price Comparison**: Find best deals across multiple platforms
- **Web Search Integration**: External reviews, Reddit discussions, and news aggregation
- **Interactive Chat**: Ask questions about products using LangChain-powered Q&A
- **Intelligent Caching**: Dual-layer Redis caching (product data + analysis) with 24-hour TTL
- **Rich UI**: Modern React TypeScript interface with real-time updates

### Analysis Components
- Executive Summary
- Product Details & Specifications
- Price Analysis (current platform + competitors)
- Pros & Cons (categorized by Quality, Performance, Value, Features, Design)
- Bank Offers & Discounts
- Seller/Brand Analysis
- External Reviews & Reddit Discussions
- Red Flags & Key Findings
- AI-generated Recommendations

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **LLM Integration**: LangChain + Google Gemini
- **Scraping**: BeautifulSoup4, Requests
- **Caching**: Redis
- **Data Processing**: Pandas, NumPy
- **Workflow**: LangGraph for orchestration

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: CSS-in-JS (inline styles)
- **HTTP Client**: Axios
- **State Management**: React Context API
- **Query Management**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Markdown Rendering**: react-markdown

### Infrastructure
- **API**: RESTful API with OpenAPI/Swagger docs
- **CORS**: Configured for local development
- **Environment**: .env configuration
- **Development**: Hot reload for both frontend and backend

## Project Structure

```
product-review/
├── backend/          # Python FastAPI backend (see backend/README.md)
└── frontend/         # React TypeScript frontend (see frontend/README.md)
```

For detailed structure of backend and frontend, see their respective README files:
- [Backend Structure](backend/README.md#directory-structure)
- [Frontend Structure](frontend/README.md#project-structure)

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Redis server
- Google Gemini API key (or other LLM provider)
- Serper API key (for web search)

### Setup

**1. Backend Setup**
```bash
cd backend
# Follow detailed setup instructions in backend/README.md
```
See [Backend README](backend/README.md#setup) for complete setup guide.

**2. Frontend Setup**
```bash
cd frontend
# Follow detailed setup instructions in frontend/README.md
```
See [Frontend README](frontend/README.md#setup) for complete setup guide.

**3. Access the Application**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/v1/docs
- Frontend UI: http://localhost:3000

### Usage

1. Open http://localhost:3000 in your browser
2. Paste an Amazon or Flipkart product URL
3. Click "Analyze Product"
4. View comprehensive analysis, reviews, and pricing
5. Use the Chat tab to ask questions about the product

## Key Features Explained

### Multi-Platform Scraping
The system automatically detects the platform (Amazon/Flipkart) and uses the appropriate scraper with platform-specific selectors and LLM enhancement.

### Intelligent Caching
Dual-layer Redis caching system with 24-hour TTL:
- **Product Data Cache**: Stores scraped product information, price comparison, and external reviews
- **Analysis Cache**: Stores LLM-generated analysis separately to avoid redundant AI calls
- **Performance**: First request ~30-60 seconds (full scraping + analysis), subsequent requests <1 second (from cache)
- **Cache Keys**: `product:{id}` for data, `product:{id}:analysis` for analysis
- **Three-Tier Routing**:
  - Fully cached: Returns instantly with no scraping or LLM calls
  - Data cached: Skips scraping, runs LLM analysis only
  - Not cached: Full pipeline (scrape → analyze → cache)

### LLM-Powered Analysis
- Uses Google Gemini (configurable to other providers)
- Structured extraction for missing data
- Sentiment analysis of reviews
- Price trend analysis
- Red flag detection

### Price Comparison
Searches across multiple platforms using Serper API to find the best deals and calculate potential savings.

### Web Search Integration
Aggregates external reviews, comparison articles, Reddit discussions, and news about the product for comprehensive context.

### Interactive Chat
LangChain-powered Q&A allows users to ask specific questions about the product with context-aware responses.

## Architecture

### LangGraph Workflow with Intelligent Caching

The application uses LangGraph for workflow orchestration with a three-tier caching strategy:

```
Request → Check Cache → Route Based on Cache Status
                    ↓
            ┌───────┴───────┬─────────────┐
            │               │             │
        Fully Cached   Data Cached    Not Cached
            │               │             │
            ↓               ↓             ↓
    Return Instantly  Run LLM Only   Full Pipeline
    (<1 second)      (~10-15 sec)   (~30-60 sec)
                                           │
                                           ↓
                                    ┌──────────────┐
                                    │   Scraping   │
                                    └──────┬───────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ↓                                      ↓
                 ┌─────────────┐                      ┌──────────────┐
                 │Price Compare│ (Parallel)           │ Web Search   │
                 └──────┬──────┘                      └──────┬───────┘
                        │                                    │
                        └──────────────┬─────────────────────┘
                                       ↓
                              ┌────────────────┐
                              │ Combine Results│
                              └────────┬───────┘
                                       ↓
                              ┌────────────────┐
                              │ Cache Product  │ → product:{id}
                              │      Data      │
                              └────────┬───────┘
                                       ↓
                              ┌────────────────┐
                              │  LLM Analysis  │
                              └────────┬───────┘
                                       ↓
                              ┌────────────────┐
                              │Cache Analysis  │ → product:{id}:analysis
                              └────────┬───────┘
                                       ↓
                              ┌────────────────┐
                              │  Return Result │
                              └────────────────┘
```

**Key Benefits:**
- **Eliminates Redundant LLM Calls**: Analysis cached separately from data
- **Parallel Execution**: Price comparison and web search run simultaneously
- **Cost Optimization**: Reduces API calls to Serper and LLM providers
- **Improved Performance**: 30-60x faster for cached requests

## API Endpoints

### Products
- `POST /api/v1/products/scrape-and-analyze` - Scrape and analyze product with intelligent caching
  - Checks cache for both product data and analysis
  - Returns instantly if fully cached (<1s)
  - Runs LLM analysis only if data is cached but analysis is not
  - Runs full pipeline if nothing is cached

### Chat
- `POST /api/v1/chat/ask` - Ask question about product
- `GET /api/v1/chat/history/{session_id}` - Get chat history
- `DELETE /api/v1/chat/clear/{session_id}` - Clear chat history

See API documentation at http://localhost:8000/api/v1/docs for full details.

## Configuration

The application requires configuration for both backend and frontend:

**Backend Configuration:**
- LLM providers (Google Gemini, OpenAI, Anthropic, Ollama, Groq, Cohere)
- API keys (LLM provider, Serper API)
- Redis connection settings
- Cache configuration

See [Backend Configuration](backend/README.md#configuration) for detailed environment variables.

**Frontend Configuration:**
- API base URL
- Timeout settings
- Debug mode

See [Frontend Configuration](frontend/README.md#configuration) for detailed environment variables.

## Documentation

- [Backend README](backend/README.md) - Backend architecture and development
- [Frontend README](frontend/README.md) - Frontend structure and components
- [LLM Providers](backend/docs/LLM_PROVIDERS.md) - LLM configuration guide
- [Price Comparison](backend/docs/PRICE_COMPARISON.md) - Price comparison system
- [Web Search Integration](backend/docs/WEB_SEARCH_INTEGRATION.md) - External data aggregation

## Development

For detailed development guides, see:
- [Backend Development Guide](backend/README.md#development) - Setup, running, testing, and adding features
- [Frontend Development Guide](frontend/README.md#development) - Setup, running, HMR, and development tips

## Troubleshooting

### Common Issues

**Redis Connection Issues**
```bash
redis-cli ping  # Should return PONG
redis-server    # Start Redis if not running
```

**CORS Errors**
- Backend is configured for ports 5000, 5001, 5002, and 3000
- Update `BACKEND_CORS_ORIGINS` in `backend/api/core/config.py` if using different port

**Port Conflicts**
- Vite automatically tries next available port if 5002 is in use

For detailed troubleshooting guides:
- [Backend Troubleshooting](backend/README.md#troubleshooting)
- [Frontend Troubleshooting](frontend/README.md#troubleshooting)

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- Check existing documentation
- Review API docs at http://localhost:8000/api/v1/docs
- Check Redis logs for caching issues
- Review browser console for frontend errors
