# FastAPI Backend API

RESTful API backend for the Amazon Product Analysis Agent, built with FastAPI and LangChain.

## Architecture

```
api/
├── core/              # Configuration
│   └── config.py     # Settings with Pydantic
├── models/           # Pydantic schemas
│   └── schemas.py    # Request/Response models
├── routes/           # API endpoints
│   ├── products.py   # Product scraping/analysis
│   └── chat.py       # Q&A chat
├── services/         # Business logic
│   ├── product_service.py
│   └── chat_service.py
└── main.py           # FastAPI application
```

## Features

- **RESTful API** with FastAPI
- **Type Safety** with Pydantic v2
- **LangChain Integration** for AI features
- **CORS** configured for React frontend
- **Auto Documentation** via Swagger/ReDoc
- **Redis Caching** for products and chat

## API Endpoints

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products/scrape` | Scrape Amazon product |
| POST | `/api/v1/products/analyze` | Analyze product with LLM |
| GET | `/api/v1/products/product/{asin}` | Get cached product |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/ask` | Ask question about product |
| GET | `/api/v1/chat/history/{session_id}` | Get chat history |
| POST | `/api/v1/chat/clear` | Clear chat history |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# API Keys
GOOGLE_API_KEY=your_google_api_key
SERPER_API_KEY=your_serper_api_key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 3. Start Redis

```bash
redis-server
```

### 4. Run the API

```bash
# From backend directory
python -m api.main

# Or with uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Access:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- Health: http://localhost:8000/health

## Usage Examples

### Scrape Product

```bash
curl -X POST "http://localhost:8000/api/v1/products/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://amazon.in/dp/B0D79G62J3"
  }'
```

### Analyze Product

```bash
curl -X POST "http://localhost:8000/api/v1/products/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "B0D79G62J3",
    "include_price_comparison": true,
    "include_web_search": true
  }'
```

### Ask Question

```bash
curl -X POST "http://localhost:8000/api/v1/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user123",
    "product_id": "B0D79G62J3",
    "question": "What are the main pros and cons?"
  }'
```

## Configuration

### CORS Origins

Edit `api/core/config.py`:

```python
BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:5000",  # React dev server
    "http://localhost:3000",  # Alternative
    # Add production URLs
]
```

### API Settings

```python
API_V1_STR: str = "/api/v1"
PROJECT_NAME: str = "Amazon Product Analysis API"
VERSION: str = "1.0.0"
```

## Development

### Hot Reload

The API automatically reloads on code changes:

```bash
uvicorn api.main:app --reload
```

### API Documentation

FastAPI generates interactive docs:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

### Testing

Test endpoints with the Swagger UI or use curl/Postman.

## Integration with Frontend

The frontend (React) calls these endpoints:

```typescript
// frontend/src/services/api.ts
const API_BASE_URL = 'http://localhost:8000';

await axios.post(`${API_BASE_URL}/api/v1/products/scrape`, {
  url: 'https://amazon.in/dp/B0D79G62J3'
});
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- 200: Success
- 400: Bad Request (invalid input)
- 404: Not Found (product not in cache)
- 500: Internal Server Error

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

Set in production:
- `GOOGLE_API_KEY`
- `SERPER_API_KEY`
- `REDIS_HOST`
- `REDIS_PORT`
- Update `BACKEND_CORS_ORIGINS` with production URLs

## Troubleshooting

### Import Errors

Ensure you're running from the backend directory:

```bash
cd backend
python -m api.main
```

### CORS Errors

Add frontend URL to `BACKEND_CORS_ORIGINS` in `api/core/config.py`.

### Redis Connection

Check Redis is running:

```bash
redis-cli ping  # Should return PONG
```

### API Keys

Verify `.env` file exists and has valid keys:

```bash
cat .env
```

## Directory Structure

```
backend/
├── api/                    # FastAPI application
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   └── schemas.py
│   ├── routes/
│   │   ├── products.py
│   │   └── chat.py
│   ├── services/
│   │   ├── product_service.py
│   │   └── chat_service.py
│   └── main.py
├── src/                    # Core logic (shared)
│   ├── scraper.py
│   ├── analyzer.py
│   └── chatbot.py
└── requirements.txt
```

## API vs Streamlit

You can run both:
- **Streamlit app**: `streamlit run app.py` (port 8501)
- **FastAPI**: `python -m api.main` (port 8000)

They share the same core logic (`src/`) but have different interfaces:
- Streamlit: Web UI for direct use
- FastAPI: REST API for React frontend
