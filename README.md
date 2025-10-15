# Amazon Product Analysis Agent

An intelligent product analysis system with AI-powered insights, built with a modern backend/frontend architecture.

## Architecture

This project consists of two main components:

```
amazon-review/
├── backend/          # Python backend (Streamlit app + core logic)
├── frontend/         # React TypeScript frontend (in development)
└── README.md         # This file
```

## Quick Start

### Backend (Streamlit App)

The backend contains the complete working Streamlit application with all features:

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# Start Redis
redis-server

# Run the application
streamlit run app.py
```

See [backend/README.md](backend/README.md) for detailed backend documentation.

### Frontend (React TypeScript)

The frontend is a modern React TypeScript interface (currently in development):

```bash
cd frontend

# Install dependencies
npm install

# Environment is pre-configured in .env.development
# For custom settings, create .env.local (see frontend/ENVIRONMENT_SETUP.md)

# Run development server
npm run dev
```

See [frontend/README.md](frontend/README.md) and [frontend/ENVIRONMENT_SETUP.md](frontend/ENVIRONMENT_SETUP.md) for detailed documentation.

## Features

### ✅ Product Analysis
- **Amazon Scraper**: Extracts product details, reviews, ratings
- **AI Analysis**: Google Gemini-powered insights with pros/cons
- **Price Comparison**: Multi-platform price checking (Amazon, Flipkart, etc.)
- **External Reviews**: Aggregates reviews from tech blogs, Reddit, YouTube

### ✅ Interactive Q&A
- **LangChain Agent**: Context-aware question answering
- **Persistent Memory**: Redis-backed chat history
- **Smart Search**: LLM decides when to search the web
- **Rich Responses**: Formatted answers with product links

### ✅ Web Search Integration
- External review analysis
- Reddit discussions
- YouTube video reviews
- Sentiment analysis
- Red flag detection

## Technology Stack

### Backend
- **Python 3.9+**
- **Streamlit** - Web interface
- **LangChain** - Agent framework
- **Google Gemini** - LLM (gemini-2.0-flash-exp)
- **Redis** - Caching and chat history
- **BeautifulSoup4** - Web scraping
- **Serper API** - Web search

### Frontend (In Development)
- **React 18**
- **TypeScript**
- **Vite** - Build tool
- **Axios** - HTTP client
- **React Context** - State management

## Prerequisites

- Python 3.9 or higher
- Node.js 18+ (for frontend)
- Redis server
- Google API Key (Gemini)
- Serper API Key (optional, for web search)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd amazon-review
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add:
# - GOOGLE_API_KEY
# - SERPER_API_KEY (optional)
# - REDIS_HOST, REDIS_PORT
```

### 3. Start Redis
```bash
# macOS with Homebrew
brew services start redis

# Linux
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Verify
redis-cli ping  # Should return PONG
```

### 4. Run the Application
```bash
cd backend
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### 5. Frontend Setup (Optional)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5000 in your browser.

## Usage

### 1. Analyze a Product

1. Go to the **Product Analysis** tab
2. Paste an Amazon product URL:
   ```
   https://amazon.in/dp/B0D79G62J3
   ```
3. Click **"Scrape & Analyze"**
4. View comprehensive analysis with:
   - Product details
   - Pros and cons
   - Price comparison
   - External reviews
   - AI recommendations

### 2. Ask Questions

1. Switch to the **Q&A Chat** tab
2. Ask questions like:
   - "What are the main complaints?"
   - "Is this good value for money?"
   - "Where can I buy this cheaper?"
   - "Compare with similar products"
3. Get AI-powered answers with context

### 3. Review Analysis

1. Go to the **Reviews** tab
2. Filter by rating or verified purchases
3. View:
   - Amazon reviews
   - External tech reviews
   - Comparison articles
   - Reddit discussions
   - Summary with sentiment analysis

## API Keys

### Google Gemini API
1. Visit https://makersuite.google.com/app/apikey
2. Create API key
3. Add to `.env` as `GOOGLE_API_KEY`

### Serper API (Optional)
1. Visit https://serper.dev/
2. Sign up for free tier (2,500 searches/month)
3. Add to `.env` as `SERPER_API_KEY`

## Project Structure

```
amazon-review/
├── backend/
│   ├── src/                      # Core source code
│   │   ├── scraper.py           # Amazon scraper
│   │   ├── analyzer.py          # Product analyzer
│   │   ├── chatbot.py           # LangChain chatbot
│   │   └── analysis/
│   │       ├── price_comparison.py
│   │       └── web_search.py
│   ├── tests/                   # Test suite
│   ├── config/                  # Configuration
│   │   └── prompts/            # LLM prompts
│   ├── app.py                   # Streamlit app
│   ├── requirements.txt         # Dependencies
│   └── README.md               # Backend docs
│
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── contexts/          # State management
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript types
│   ├── package.json
│   └── README.md              # Frontend docs
│
├── README.md                   # This file
├── README_ARCHITECTURE.md      # Architecture details
└── SETUP.md                    # Setup guide
```

## Documentation

- [README_ARCHITECTURE.md](README_ARCHITECTURE.md) - Detailed architecture
- [SETUP.md](SETUP.md) - Comprehensive setup guide
- [backend/README.md](backend/README.md) - Backend documentation
- [frontend/README.md](frontend/README.md) - Frontend documentation

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server
```

### API Key Error
- Verify `.env` file exists in `backend/`
- Check API keys are valid
- Ensure no extra spaces in `.env`

### Module Not Found
```bash
cd backend
pip install -r requirements.txt
```

### Scraping Fails
- Verify Amazon URL is valid
- Check internet connection
- Amazon may block aggressive scraping
- Try a different product

## Features in Detail

### Product Scraping
- Extracts ASIN from URLs
- Scrapes product details, reviews, ratings
- Supports pagination (up to 200 reviews)
- Redis caching for performance

### AI Analysis
- Google Gemini 2.0 Flash LLM
- Structured markdown output
- Price comparison integration
- External review aggregation
- Sentiment analysis

### Price Comparison
- Multi-platform checking
- Amazon, Flipkart, eBay, Walmart
- Best deal recommendations
- Savings calculation

### Web Search Integration
- Tech blog reviews
- Reddit discussions
- YouTube videos
- Issue tracking
- Red flags detection

### Interactive Chat
- LangChain ReAct agent
- Redis chat history
- Context-aware responses
- Rich link formatting

## Development

### Running Tests
```bash
cd backend
pytest
```

### Verify Setup
```bash
cd backend
python verify_setup.py
```

### Code Structure
- `src/scraper.py` - Amazon scraping logic
- `src/analyzer.py` - LLM analysis
- `src/chatbot.py` - Q&A system
- `src/analysis/price_comparison.py` - Price checking
- `src/analysis/web_search.py` - External reviews

## Limitations

1. **Scraping**: Amazon HTML may change
2. **Reviews**: Limited to 200 per product
3. **Rate Limits**: Google Gemini API limits apply
4. **Regions**: Optimized for Amazon India
5. **Dynamic Content**: No JavaScript rendering

## Future Enhancements

- ✅ Price comparison (completed)
- ✅ Web search integration (completed)
- ✅ External reviews (completed)
- ⏳ React frontend (in progress)
- 📋 FastAPI backend (planned)
- 📋 Sentiment visualization
- 📋 PDF export
- 📋 Product comparison
- 📋 Price tracking

## Contributing

Contributions welcome! Please submit issues or pull requests.

## License

MIT License - For educational and personal use only.

## Disclaimer

This tool is for personal use. Respect Amazon's Terms of Service. Do not scrape aggressively or for commercial purposes.

---

**Built with:**
- Python, Streamlit, LangChain, Google Gemini
- React, TypeScript (frontend in development)
- Redis, BeautifulSoup4, Serper API

**Version:** 3.0.0 (Backend/Frontend Architecture)

**Author:** AI Product Analysis Team
