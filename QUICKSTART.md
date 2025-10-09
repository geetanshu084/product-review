# Quick Start Guide

Get the Amazon Product Analysis Agent up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- Redis server
- Google API key for Gemini (free from makersuite.google.com)

## Setup Steps

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Start Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis
```

**Verify Redis:**
```bash
redis-cli ping
# Should return: PONG
```

### 3. Configure Google API Key

1. Get your API key from: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API key"
4. Copy the generated key

In `.env`:
```
GOOGLE_API_KEY=your_api_key_here
```

### 4. Verify Setup

```bash
python verify_setup.py
```

All checks should pass!

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## First Analysis

1. Go to **Product Analysis** tab
2. Paste an Amazon URL (e.g., `https://www.amazon.com/dp/B08N5WRWNW`)
3. Click **Analyze Product**
4. Wait 15-30 seconds
5. View the comprehensive analysis!

## Ask Questions

1. Switch to **Q&A Chat** tab
2. Type your question
3. Click **Send**
4. Get AI-powered answers based on the product data!

## Example Questions

- "What are the main complaints?"
- "Is this good for beginners?"
- "How's the build quality?"
- "Does it come with a warranty?"

## Troubleshooting

**Redis not connecting?**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server
```

**Google API key error?**
- Verify `GOOGLE_API_KEY` is set in `.env` file
- Get your key from: https://makersuite.google.com/app/apikey
- Make sure the key is valid
- Restart Streamlit app

**Scraping fails?**
- Verify it's a valid Amazon product URL
- Try a different product
- Wait a moment and try again

## Next Steps

- Check `README.md` for detailed documentation
- See `example_usage.py` for programmatic usage
- Explore the code in `src/` directory

## Support

For issues or questions:
- Check the troubleshooting section in README.md
- Review error messages in the terminal
- Ensure all prerequisites are installed

---

**That's it! You're ready to analyze Amazon products with AI!**
