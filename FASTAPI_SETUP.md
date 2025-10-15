# FastAPI Backend Setup Guide

## Overview

The FastAPI backend provides a RESTful API that integrates with the React TypeScript frontend. It uses LangChain for AI features and wraps the existing scraper, analyzer, and chatbot modules.

## Directory Structure

```
backend/
├── api/                          # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py            # Settings with Pydantic
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Request/Response models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── products.py          # Product endpoints
│   │   └── chat.py              # Chat endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── product_service.py   # Product business logic
│   │   └── chat_service.py      # Chat business logic
│   ├── main.py                  # FastAPI app entry point
│   └── README.md                # API documentation
│
├── src/                         # Core modules (shared)
│   ├── scraper.py
│   ├── analyzer.py
│   ├── chatbot.py
│   └── analysis/
│
├── app.py                       # Streamlit app (alternative UI)
└── requirements.txt             # All dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- Core dependencies (BeautifulSoup, LangChain, Redis)
- Streamlit (for alternative UI)
- FastAPI, Uvicorn, Pydantic (for REST API)

### 2. Configure Environment

Ensure `.env` file exists with:

```bash
GOOGLE_API_KEY=your_google_api_key
SERPER_API_KEY=your_serper_api_key
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 3. Start Redis

```bash
redis-server
```

### 4. Run FastAPI Server

```bash
cd backend
python -m api.main
```

Or with uvicorn directly:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the API

Open in browser:
- API Documentation: http://localhost:8000/api/v1/docs
- Alternative Docs: http://localhost:8000/api/v1/redoc
- Health Check: http://localhost:8000/health

## API Endpoints

### Products API

**Scrape Product**
```bash
POST /api/v1/products/scrape
Content-Type: application/json

{
  "url": "https://amazon.in/dp/B0D79G62J3"
}
```

**Analyze Product**
```bash
POST /api/v1/products/analyze
Content-Type: application/json

{
  "asin": "B0D79G62J3",
  "include_price_comparison": true,
  "include_web_search": true
}
```

**Get Product**
```bash
GET /api/v1/products/product/{asin}
```

### Chat API

**Ask Question**
```bash
POST /api/v1/chat/ask
Content-Type: application/json

{
  "session_id": "user_123",
  "product_id": "B0D79G62J3",
  "question": "What are the pros and cons?"
}
```

**Get Chat History**
```bash
GET /api/v1/chat/history/{session_id}
```

**Clear Chat**
```bash
POST /api/v1/chat/clear
Content-Type: application/json

{
  "session_id": "user_123"
}
```

## Integration with Frontend

The React frontend (port 5000) calls the FastAPI backend (port 8000):

```typescript
// frontend/src/services/api.ts
const API_BASE_URL = 'http://localhost:8000';

const response = await axios.post(
  `${API_BASE_URL}/api/v1/products/scrape`,
  { url: amazonUrl }
);
```

### CORS Configuration

The API is configured to allow requests from:
- `http://localhost:5000` (React dev server)
- `http://localhost:3000` (Alternative port)

To add more origins, edit `backend/api/core/config.py`:

```python
BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:5000",
    "https://your-production-domain.com",
]
```

## Architecture

### Service Layer Pattern

```
Frontend (React)
    ↓ HTTP/REST
FastAPI Routes (products.py, chat.py)
    ↓ Function calls
Services (product_service.py, chat_service.py)
    ↓ Function calls
Core Modules (scraper.py, analyzer.py, chatbot.py)
    ↓ Redis/External APIs
Redis Cache, Google Gemini, Serper API
```

### Key Components

1. **FastAPI Routes** (`api/routes/`)
   - Handle HTTP requests
   - Validate input with Pydantic
   - Return JSON responses

2. **Services** (`api/services/`)
   - Business logic layer
   - Wrap core modules (scraper, analyzer, chatbot)
   - Handle Redis caching
   - Manage errors

3. **Core Modules** (`src/`)
   - Shared between Streamlit and FastAPI
   - Amazon scraping logic
   - LLM analysis
   - LangChain chatbot

4. **Pydantic Models** (`api/models/schemas.py`)
   - Type-safe request/response models
   - Auto-validated by FastAPI
   - Auto-generated API docs

## Running Both UIs

You can run both Streamlit and FastAPI simultaneously:

**Terminal 1 - FastAPI (for React frontend):**
```bash
cd backend
python -m api.main
# Runs on http://localhost:8000
```

**Terminal 2 - Streamlit (standalone UI):**
```bash
cd backend
streamlit run app.py
# Runs on http://localhost:8501
```

**Terminal 3 - React Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5000
```

They all share the same core logic and Redis cache!

## Testing

### Using Swagger UI

1. Open http://localhost:8000/api/v1/docs
2. Click on an endpoint (e.g., POST /scrape)
3. Click "Try it out"
4. Enter request body
5. Click "Execute"
6. View response

### Using cURL

```bash
# Scrape product
curl -X POST "http://localhost:8000/api/v1/products/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://amazon.in/dp/B0D79G62J3"}'

# Get product
curl "http://localhost:8000/api/v1/products/product/B0D79G62J3"

# Ask question
curl -X POST "http://localhost:8000/api/v1/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "product_id": "B0D79G62J3",
    "question": "Is this worth buying?"
  }'
```

### Using Python

```python
import requests

# Scrape
response = requests.post(
    "http://localhost:8000/api/v1/products/scrape",
    json={"url": "https://amazon.in/dp/B0D79G62J3"}
)
product = response.json()
print(product)

# Analyze
response = requests.post(
    "http://localhost:8000/api/v1/products/analyze",
    json={
        "asin": "B0D79G62J3",
        "include_price_comparison": True,
        "include_web_search": True
    }
)
analysis = response.json()
print(analysis['analysis'])
```

## Development

### Hot Reload

FastAPI automatically reloads on code changes when using `--reload`:

```bash
uvicorn api.main:app --reload
```

### Adding New Endpoints

1. Create route in `api/routes/`
2. Add Pydantic models in `api/models/schemas.py`
3. Implement logic in `api/services/`
4. Register router in `api/main.py`

Example:

```python
# api/routes/new_feature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}

# api/main.py
from api.routes import new_feature

app.include_router(
    new_feature.router,
    prefix=f"{settings.API_V1_STR}/new",
    tags=["new"]
)
```

## Production Deployment

### Using Gunicorn + Uvicorn Workers

```bash
pip install gunicorn
gunicorn api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t amazon-analysis-api .
docker run -p 8000:8000 --env-file .env amazon-analysis-api
```

### Environment Variables

Set in production:
```bash
GOOGLE_API_KEY=production_key
SERPER_API_KEY=production_key
REDIS_HOST=production-redis.example.com
REDIS_PORT=6379
```

Update CORS origins:
```python
BACKEND_CORS_ORIGINS = [
    "https://your-frontend-domain.com",
]
```

## Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'api'`

**Solution:** Run from backend directory:
```bash
cd backend
python -m api.main
```

### CORS Errors

**Error:** Frontend gets CORS errors

**Solution:** Add frontend URL to `BACKEND_CORS_ORIGINS` in `api/core/config.py`

### Redis Connection

**Error:** `ConnectionError: Error connecting to Redis`

**Solution:**
```bash
# Check Redis is running
redis-cli ping

# Start Redis
redis-server
```

### API Keys

**Error:** `ValueError: API key not provided`

**Solution:** Check `.env` file exists and has valid keys

## Next Steps

1. ✅ FastAPI backend created
2. ✅ API endpoints defined
3. ✅ Service layer implemented
4. ✅ Frontend can integrate via API client
5. 📋 Test all endpoints
6. 📋 Deploy to production

## Summary

- **FastAPI Backend:** `backend/api/`
- **Entry Point:** `api/main.py`
- **Endpoints:** Products, Chat, Health
- **Port:** 8000
- **Docs:** http://localhost:8000/api/v1/docs
- **Frontend Integration:** React calls REST API
- **Shared Code:** Uses `src/` modules
- **Alternative UI:** Streamlit still available

The backend is now ready to integrate with the React TypeScript frontend! 🚀
