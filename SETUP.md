# Setup Guide - Amazon Product Analysis Agent

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Redis Server
- Google API Key (Gemini)
- Serper API Key (optional, for web search)

### Step 1: Clone and Setup

```bash
cd /path/to/amazon-review
```

### Step 2: Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your_google_api_key_here"
export SERPER_API_KEY="your_serper_api_key_here"  # Optional
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Or create a .env file in backend/
cat > backend/.env << EOF
GOOGLE_API_KEY=your_google_api_key_here
SERPER_API_KEY=your_serper_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
EOF
```

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000
EOF
```

### Step 4: Start Redis

```bash
# On macOS with Homebrew
brew services start redis

# On Linux
sudo systemctl start redis

# Or run directly
redis-server
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Step 5: Start Backend Server

```bash
# From project root
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Verify backend is running:
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/api/v1/docs

### Step 6: Start Frontend Server

```bash
# From project root
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Step 7: Open Application

Open your browser and navigate to: **http://localhost:3000**

## Testing the Application

### 1. Test Product Scraping

1. Go to http://localhost:3000
2. Paste an Amazon product URL, for example:
   ```
   https://amazon.in/dp/B0D79G62J3
   ```
3. Click "🔍 Scrape Product"
4. You should see product details appear

### 2. Test Analysis

1. After scraping, click the "📊 Analysis" tab
2. Check/uncheck options:
   - ✓ Include Price Comparison
   - ✓ Include External Reviews
3. Click "🤖 Analyze Product"
4. Wait for AI analysis (may take 30-60 seconds)
5. View the markdown-formatted analysis

### 3. Test Reviews

1. Click the "⭐ Reviews" tab
2. Navigate through sub-tabs:
   - 🛒 Amazon Reviews
   - 🌐 External Reviews
   - 🔍 Comparisons
   - 📊 Summary
3. Use filters on Amazon Reviews tab:
   - Rating slider
   - Verified purchases checkbox

### 4. Test Chat

1. Click the "💬 Q&A" tab
2. Type a question, for example:
   - "What are the main pros and cons?"
   - "Is this good value for money?"
3. Press Enter or click send
4. View the AI response
5. Ask follow-up questions

## API Testing

### Using cURL

**Scrape Product:**
```bash
curl -X POST "http://localhost:8000/api/v1/products/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://amazon.in/dp/B0D79G62J3",
    "session_id": "test-session"
  }'
```

**Analyze Product:**
```bash
curl -X POST "http://localhost:8000/api/v1/products/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "B0D79G62J3",
    "include_price_comparison": true,
    "include_web_search": true
  }'
```

**Ask Question:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "product_id": "B0D79G62J3",
    "question": "What are the main features?"
  }'
```

### Using API Documentation

Open http://localhost:8000/api/v1/docs to use the interactive Swagger UI.

## Configuration Options

### Backend Configuration

Edit `backend/app/core/config.py` or use environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `SERPER_API_KEY` | Serper web search API key | Optional |
| `REDIS_HOST` | Redis server host | localhost |
| `REDIS_PORT` | Redis server port | 6379 |
| `REDIS_DB` | Redis database number | 0 |
| `REDIS_PASSWORD` | Redis password | None |

### Frontend Configuration

Edit `frontend/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | http://localhost:8000 |

## Troubleshooting

### Issue: Redis Connection Error

**Error:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution:**
1. Check if Redis is running:
   ```bash
   redis-cli ping
   ```
2. If not running, start Redis:
   ```bash
   redis-server
   ```
3. Verify Redis configuration in backend

### Issue: CORS Error in Browser

**Error:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution:**
1. Check backend CORS configuration in `backend/app/core/config.py`
2. Ensure frontend URL (http://localhost:3000) is in `BACKEND_CORS_ORIGINS`
3. Restart backend server

### Issue: API Key Error

**Error:** `ValueError: API key not provided`

**Solution:**
1. Set environment variables:
   ```bash
   export GOOGLE_API_KEY="your_key_here"
   ```
2. Or create `backend/.env` file with keys
3. Restart backend server

### Issue: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r backend/requirements.txt
```

### Issue: Cannot Connect to Backend

**Error:** Frontend shows "Failed to fetch" or connection errors

**Solution:**
1. Verify backend is running: http://localhost:8000/health
2. Check `VITE_API_BASE_URL` in frontend/.env
3. Clear browser cache and reload

### Issue: Scraping Fails

**Error:** "Failed to scrape product"

**Solution:**
1. Verify the Amazon URL is valid
2. Check if Amazon is blocking requests (use VPN if needed)
3. Amazon may have changed their HTML structure - check scraper code

## Development Tips

### Hot Reload

Both backend and frontend support hot reload:
- Backend: Automatically reloads when Python files change
- Frontend: Automatically reloads when React files change

### Debugging Backend

Add debug logging:
```bash
uvicorn app.main:app --reload --log-level debug
```

### Debugging Frontend

Open browser DevTools:
- Console: View errors and logs
- Network: Inspect API requests/responses
- React DevTools: Inspect component state

### Redis Debugging

View cached data:
```bash
redis-cli

# List all keys
KEYS *

# Get product data
GET product:B0D79G62J3

# View chat history
KEYS chat_history:*
```

Clear cache:
```bash
redis-cli FLUSHALL
```

## Production Deployment

### Backend

1. **Use production ASGI server:**
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Set secure environment variables**

3. **Enable HTTPS**

4. **Configure Redis with password**

5. **Add rate limiting**

### Frontend

1. **Build for production:**
   ```bash
   npm run build
   ```

2. **Serve with Nginx:**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           root /path/to/frontend/dist;
           try_files $uri /index.html;
       }

       location /api {
           proxy_pass http://localhost:8000;
       }
   }
   ```

3. **Update environment variables:**
   ```bash
   VITE_API_BASE_URL=https://api.yourdomain.com
   ```

## Next Steps

1. Read [README_ARCHITECTURE.md](./README_ARCHITECTURE.md) for detailed architecture
2. Explore API documentation at http://localhost:8000/api/v1/docs
3. Customize prompts in `src/config/prompts/`
4. Add new features or modify existing components

## Getting API Keys

### Google Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Serper API Key (Optional)
1. Go to https://serper.dev/
2. Sign up for free account
3. Copy API key from dashboard

## Support

If you encounter issues:
1. Check this guide first
2. Review error messages carefully
3. Check API documentation
4. Verify all services are running (Redis, Backend, Frontend)
