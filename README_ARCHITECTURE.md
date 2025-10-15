# Amazon Product Analysis Agent - Architecture Documentation

## Overview

The application has been refactored into a modern **Backend + Frontend** architecture:

- **Backend**: FastAPI with LangChain integration
- **Frontend**: React with TypeScript
- **Cache Layer**: Redis for product data and chat history

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │ Components │  │   Context   │  │   API Client     │     │
│  │   - Tabs   │  │ - Product   │  │  (Axios)         │     │
│  │   - Forms  │  │ - Session   │  │                  │     │
│  └────────────┘  └─────────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              API Routes                                 │ │
│  │  /api/v1/products  │  /api/v1/chat                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Services Layer                             │ │
│  │  ProductService  │  ChatService                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Core Modules (src/)                        │ │
│  │  Scraper │ Analyzer │ Chatbot │ PriceComparison        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
               ┌────────────────────────┐
               │       Redis Cache       │
               │  - Product Data        │
               │  - Chat History        │
               └────────────────────────┘
```

## Directory Structure

```
amazon-review/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── products.py # Product endpoints
│   │   │       └── chat.py     # Chat endpoints
│   │   ├── core/
│   │   │   └── config.py       # Configuration
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic models
│   │   ├── services/
│   │   │   ├── product_service.py
│   │   │   └── chat_service.py
│   │   └── main.py             # FastAPI app
│   └── requirements.txt
│
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── tabs/
│   │   │   │   ├── AnalysisTab.tsx
│   │   │   │   ├── ReviewsTab.tsx
│   │   │   │   └── ChatTab.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── ScrapeForm.tsx
│   │   │   └── ProductDetails.tsx
│   │   ├── contexts/
│   │   │   └── ProductContext.tsx
│   │   ├── services/
│   │   │   └── api.ts          # API client
│   │   ├── types/
│   │   │   └── index.ts        # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
└── src/                        # Core logic (shared)
    ├── scraper.py              # Amazon scraper
    ├── analyzer.py             # Product analyzer
    ├── chatbot.py              # LangChain chatbot
    ├── analysis/
    │   ├── price_comparison.py
    │   └── web_search.py
    └── config/
```

## Backend (FastAPI)

### Key Components

#### 1. API Routes (`backend/app/api/routes/`)

**Products Routes** (`products.py`):
- `POST /api/v1/products/scrape` - Scrape Amazon product
- `POST /api/v1/products/analyze` - Analyze product with LLM
- `GET /api/v1/products/product/{asin}` - Get cached product data

**Chat Routes** (`chat.py`):
- `POST /api/v1/chat/ask` - Ask question about product
- `GET /api/v1/chat/history/{session_id}` - Get chat history
- `POST /api/v1/chat/clear` - Clear chat history

#### 2. Services Layer (`backend/app/services/`)

**ProductService**:
- Wraps `AmazonScraper` and `ProductAnalyzer`
- Handles product scraping and analysis
- Manages Redis cache interactions

**ChatService**:
- Wraps `ProductChatbot`
- Handles Q&A interactions
- Manages chat history with Redis

#### 3. Configuration (`backend/app/core/config.py`)

Uses Pydantic Settings for configuration:
- API settings
- CORS origins
- Redis connection
- API keys (Google, Serper)

#### 4. Models (`backend/app/models/schemas.py`)

Pydantic v2 models for:
- Request validation
- Response serialization
- Type safety

### Running the Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your_key"
export SERPER_API_KEY="your_key"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Frontend (React + TypeScript)

### Key Components

#### 1. Context (`src/contexts/ProductContext.tsx`)

Global state management:
- Product data
- Analysis results
- Chat history
- Session ID
- Loading/error states

#### 2. API Client (`src/services/api.ts`)

Axios-based client with:
- Typed requests/responses
- Error handling
- Base URL configuration
- Request/response interceptors

#### 3. Components

**Main Components**:
- `Header` - Application header
- `ScrapeForm` - URL input form
- `ProductDetails` - Product information display

**Tab Components**:
- `AnalysisTab` - AI analysis with options
- `ReviewsTab` - Amazon + external reviews with filters
- `ChatTab` - Interactive Q&A interface

#### 4. Types (`src/types/index.ts`)

TypeScript interfaces matching backend models:
- ProductData
- Review
- WebSearchAnalysis
- Request/Response types

### Running the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

Frontend available at: http://localhost:3000

### Building for Production

```bash
npm run build
npm run preview  # Preview production build
```

## Core Modules (src/)

These modules contain the business logic and are used by both backend services:

### 1. Scraper (`src/scraper.py`)
- Amazon product scraping
- Review extraction with pagination
- Data validation

### 2. Analyzer (`src/analyzer.py`)
- LLM-based product analysis
- Integration with price comparison
- Integration with web search

### 3. Chatbot (`src/chatbot.py`)
- LangChain agent setup
- Redis chat history
- Tool-calling capabilities

### 4. Price Comparison (`src/analysis/price_comparison.py`)
- Multi-site price checking
- Availability tracking

### 5. Web Search (`src/analysis/web_search.py`)
- External review aggregation
- Reddit discussions
- YouTube video reviews
- Sentiment analysis

## Data Flow

### 1. Product Scraping Flow

```
User enters URL → Frontend sends POST /scrape
    ↓
Backend validates URL
    ↓
AmazonScraper scrapes product
    ↓
Data saved to Redis cache (product:{asin})
    ↓
Response sent to frontend
    ↓
Frontend updates ProductContext
    ↓
UI displays product details
```

### 2. Analysis Flow

```
User clicks "Analyze" → Frontend sends POST /analyze
    ↓
Backend retrieves product from cache
    ↓
ProductAnalyzer runs:
  - Price comparison (if enabled)
  - Web search (if enabled)
  - LLM analysis
    ↓
Updated data saved to cache
    ↓
Analysis markdown sent to frontend
    ↓
Frontend renders with ReactMarkdown
```

### 3. Chat Flow

```
User asks question → Frontend sends POST /chat/ask
    ↓
Backend retrieves product from cache
    ↓
ProductChatbot processes:
  - Gets chat history from Redis
  - Runs LangChain agent with tools
  - Saves message to history
    ↓
Answer sent to frontend
    ↓
Frontend updates chat display
```

## Redis Cache Structure

### Product Cache
```
Key: product:{asin}
Value: JSON object with:
  - Basic product info
  - Reviews
  - Price comparison (if analyzed)
  - Web search analysis (if analyzed)
```

### Chat History
```
Key: chat_history:{session_id}
Value: LangChain RedisChatMessageHistory
  - Managed by LangChain
  - Stores conversation messages
```

## API Endpoints Reference

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products/scrape` | Scrape Amazon product |
| POST | `/api/v1/products/analyze` | Analyze with LLM |
| GET | `/api/v1/products/product/{asin}` | Get cached product |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/ask` | Ask question |
| GET | `/api/v1/chat/history/{session_id}` | Get history |
| POST | `/api/v1/chat/clear` | Clear history |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Configuration

### Backend Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_google_api_key
SERPER_API_KEY=your_serper_api_key

# Optional (defaults shown)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### Frontend Environment Variables

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Features

### ✅ Implemented

1. **Product Scraping**
   - Amazon URL validation
   - Product details extraction
   - Review scraping with pagination
   - Image URLs

2. **AI Analysis**
   - Gemini 2.0 Flash LLM
   - Structured markdown output
   - Price comparison integration
   - Web search integration

3. **Price Comparison**
   - Multi-site checking
   - Alternative prices
   - Availability status

4. **External Reviews**
   - Tech blog reviews
   - Reddit discussions
   - YouTube videos
   - Issue tracking
   - Sentiment analysis

5. **Interactive Chat**
   - LangChain agent
   - Persistent history
   - Context-aware responses
   - Rich link formatting

6. **UI Features**
   - Responsive design
   - Tab navigation
   - Filter controls
   - Loading states
   - Error handling

## Migration from Streamlit

The previous Streamlit application (`app.py`) has been refactored into this architecture. Key changes:

1. **Session State** → **React Context**
   - Product data managed in ProductContext
   - Chat history in context + Redis

2. **Streamlit Tabs** → **React Tabs**
   - Analysis, Reviews, Q&A tabs
   - Sub-tabs for review categories

3. **Direct Function Calls** → **API Endpoints**
   - All operations now go through REST API
   - Better separation of concerns

4. **st.chat_input** → **Custom Chat Component**
   - Auto-clearing input
   - Message history display
   - Rich link rendering

## Development Workflow

### 1. Start Redis
```bash
redis-server
```

### 2. Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend
```bash
cd frontend
npm run dev
```

### 4. Access Application
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/api/v1/docs
- Health Check: http://localhost:8000/health

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Deployment Considerations

### Backend
- Use production ASGI server (Uvicorn with Gunicorn)
- Set environment variables securely
- Configure Redis with authentication
- Enable HTTPS
- Add rate limiting

### Frontend
- Build with `npm run build`
- Serve with Nginx or CDN
- Configure API base URL for production
- Enable gzip compression
- Add monitoring

## Future Enhancements

1. **Authentication**
   - User accounts
   - Session management
   - API keys

2. **Database**
   - PostgreSQL for persistent storage
   - Product history
   - User favorites

3. **Real-time Updates**
   - WebSocket support
   - Streaming LLM responses
   - Live scraping progress

4. **Additional Features**
   - Product comparison side-by-side
   - Price tracking alerts
   - Export reports (PDF)
   - Share analysis links

## Troubleshooting

### CORS Errors
- Check `BACKEND_CORS_ORIGINS` in `backend/app/core/config.py`
- Ensure frontend URL is allowed

### Redis Connection
- Verify Redis is running: `redis-cli ping`
- Check Redis host/port configuration

### API Errors
- Check API logs: `uvicorn app.main:app --log-level debug`
- Verify environment variables are set
- Check API documentation at `/api/v1/docs`

### Build Errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run lint`
- Verify Python dependencies: `pip install -r requirements.txt`

## Support

For issues or questions:
1. Check API documentation: http://localhost:8000/api/v1/docs
2. Review error messages in browser console
3. Check backend logs
4. Verify Redis is running and accessible
