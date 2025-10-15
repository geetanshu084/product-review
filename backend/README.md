# Amazon Product Analysis Agent - Backend

## Overview

This is the backend for the Amazon Product Analysis Agent, built with Python, Streamlit, and LangChain.

## Directory Structure

```
backend/
├── src/                    # Core source code
│   ├── scraper.py         # Amazon scraper
│   ├── analyzer.py        # Product analyzer with LLM
│   ├── chatbot.py         # LangChain chatbot
│   └── analysis/
│       ├── price_comparison.py
│       └── web_search.py
├── tests/                 # Test suite
├── config/                # Configuration files
│   └── prompts/          # LLM prompts
├── utils/                 # Utility functions
├── app.py                 # Streamlit application
├── example_usage.py       # Usage examples
├── verify_setup.py        # Setup verification
└── requirements.txt       # Python dependencies
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
GOOGLE_API_KEY=your_google_api_key_here
SERPER_API_KEY=your_serper_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Start Redis

```bash
redis-server
```

### 4. Run the Application

```bash
streamlit run app.py
```

Open your browser to http://localhost:8501

## Features

### 1. Product Scraping
- Scrapes Amazon product data
- Extracts reviews, ratings, features
- Caches data in Redis

### 2. AI Analysis
- Google Gemini 2.0 Flash LLM
- Price comparison across sites
- External review aggregation
- Sentiment analysis

### 3. Interactive Chat
- LangChain agent with tools
- Persistent chat history
- Context-aware responses

## Testing

Run tests:
```bash
pytest
```

Run specific test:
```bash
pytest tests/test_scraper.py
```

## API Keys

### Google Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Add to `.env`

### Serper API Key (Optional)
1. Go to https://serper.dev/
2. Sign up and get API key
3. Add to `.env`

## Development

### Verify Setup
```bash
python verify_setup.py
```

### Example Usage
```bash
python example_usage.py
```

## Modules

### scraper.py
Amazon product scraper with:
- URL validation
- Product data extraction
- Review pagination
- Redis caching

### analyzer.py
Product analyzer with:
- LLM-powered analysis
- Price comparison integration
- Web search integration
- Structured output

### chatbot.py
LangChain chatbot with:
- Custom tools
- Redis chat history
- Agent-based Q&A

### analysis/price_comparison.py
Price comparison across:
- Flipkart
- Amazon
- Other e-commerce sites

### analysis/web_search.py
External review analysis:
- Tech blog reviews
- Reddit discussions
- YouTube videos
- Sentiment analysis

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server
```

### Module Import Error
```bash
# Make sure you're in the backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt
```

### API Key Error
```bash
# Verify .env file exists and has keys
cat .env

# Export manually if needed
export GOOGLE_API_KEY="your_key"
```

## Configuration

### Prompts
Edit prompts in `config/prompts/`:
- `agent_prompt.txt` - Chatbot system prompt
- `analysis_prompt.txt` - Analysis prompt

### Redis
Configure in `.env`:
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## License

MIT License
