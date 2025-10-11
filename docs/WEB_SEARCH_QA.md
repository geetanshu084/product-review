# Web Search in Q&A Chatbot

## Overview
The Q&A chatbot now includes intelligent web search capability that automatically searches the internet when users ask questions requiring current, up-to-date information.

## How It Works

### Automatic Search Triggering
The chatbot automatically detects when a question requires web search based on keywords:

**Triggers Web Search:**
- Current information: `current`, `latest`, `now`, `today`, `recent`, `updated`
- Comparisons: `compare`, `vs`, `versus`, `alternative`, `similar`
- Pricing: `price`, `cost`, `buy`, `where to`, `available`
- Availability: `in stock`, `sale`, `discount`, `offer`, `deal`

**Uses Product Data:**
- Questions about features, specifications, warranty
- Questions about what's already in the product data
- General product information queries

### Example Questions

**Questions that trigger web search:**
- "What is the current price of this phone?"
- "Compare this with Samsung Galaxy S24"
- "Is this available in stock right now?"
- "What are the latest deals on this product?"
- "Show me similar alternatives"

**Questions that use product data:**
- "What are the key features of this phone?"
- "What color is this phone?"
- "What storage capacity does it have?"
- "Tell me about the camera"

## Setup

### 1. Get Serper API Key
1. Visit [https://serper.dev/](https://serper.dev/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes 2,500 free searches

### 2. Configure API Key
Add your Serper API key to the `.env` file:

```bash
SERPER_API_KEY=your_serper_api_key_here
```

### 3. Enable Web Search
Web search is enabled by default. To use it:

```python
from src.chatbot import ProductChatbot

chatbot = ProductChatbot(
    google_api_key="your_google_api_key",
    serper_api_key="your_serper_api_key",
    enable_web_search=True  # Default: True
)
```

## Usage

### Basic Usage

```python
from src.chatbot import ProductChatbot

# Initialize chatbot
chatbot = ProductChatbot(
    google_api_key="your_google_api_key",
    serper_api_key="your_serper_api_key"
)

# Set product data
session_id = "user_session_123"
chatbot.set_product_data(session_id, product_data)

# Ask questions (web search will trigger automatically when needed)
answer = chatbot.ask(session_id, "What is the current price?")
print(answer)
# Output: "According to current search results: ..."
```

### Disabling Web Search

To disable web search:

```python
# Option 1: Pass parameter
chatbot = ProductChatbot(
    google_api_key="your_google_api_key",
    enable_web_search=False
)

# Option 2: Don't set SERPER_API_KEY in .env
# Web search will automatically disable if no API key is found
```

## Web Search Behavior

### Search Query Construction
When web search is triggered, the chatbot:
1. Extracts the product title from the current product data
2. Combines product title + user question
3. Performs web search
4. Integrates results into the answer

Example:
- Product: "Apple iPhone 15 Pro 256GB"
- Question: "What is the current price?"
- Search Query: "Apple iPhone 15 Pro 256GB What is the current price?"

### Search Results Format
The chatbot receives top 5 organic search results:
- Title
- Snippet (description)
- Source URL

These are formatted and provided to the LLM for answering.

## Testing

Run the test script to verify web search functionality:

```bash
python test_web_search.py
```

This will test:
- Questions that should trigger web search
- Questions that should use product data
- Integration of search results into answers

## Technical Details

### Implementation
The web search feature is implemented in `src/chatbot.py`:

**Key Methods:**
- `_should_search_web(question)` - Detects if question needs web search
- `_web_search(query, num_results)` - Performs web search via Serper API
- `ask(session_id, question)` - Main method that integrates search

**Search Keywords:**
```python
search_keywords = [
    'current', 'latest', 'now', 'today', 'recent', 'updated',
    'compare', 'vs', 'versus', 'alternative', 'similar',
    'price', 'cost', 'buy', 'where to', 'available',
    'in stock', 'sale', 'discount', 'offer', 'deal'
]
```

### API Configuration
- **Endpoint**: `https://google.serper.dev/search`
- **Method**: POST
- **Response**: Organic search results with title, snippet, link
- **Timeout**: 10 seconds
- **Default Results**: 5 results per query

## Troubleshooting

### Web search not triggering
**Issue**: Web search doesn't activate for expected questions

**Solutions:**
- Check if SERPER_API_KEY is set in `.env`
- Verify question contains trigger keywords
- Check chatbot initialization: `enable_web_search=True`

### API Key errors
**Issue**: `401 Unauthorized` or `403 Forbidden`

**Solutions:**
- Verify API key is correct
- Check API usage limits at serper.dev dashboard
- Ensure API key has not expired

### Search results not relevant
**Issue**: Web search returns irrelevant results

**Solutions:**
- Question may be too vague - try more specific queries
- Product title may not be clear enough
- Search results depend on Google's index - some products may have limited data

### Slow responses
**Issue**: Chatbot takes too long to respond

**Solutions:**
- Web search adds ~1-2 seconds to response time
- Check network connectivity
- Consider disabling web search if not needed
- Reduce `num_results` parameter (default: 5)

## Cost Optimization

- **Free Tier**: 2,500 searches/month
- **Usage**: Each web-search-triggered question = 1 search
- **Recommendation**: Web search is selective - only triggers on relevant keywords
- **Monitoring**: Check usage at serper.dev dashboard

## Best Practices

1. **Ask specific questions**: "What is the current price on Amazon?" is better than "Tell me about prices"
2. **Use trigger keywords**: Include words like "current", "latest", "compare" when you want web search
3. **Product data first**: For basic questions, web search is not needed - product data is faster
4. **Monitor usage**: Keep track of API usage to stay within free tier limits

## Integration with Streamlit UI

The web search feature works automatically in the Streamlit UI:
- Users ask questions in the chat interface
- Web search triggers automatically when needed
- Visual indicator shows when search is being performed
- Search results are seamlessly integrated into answers

## Examples

### Example 1: Current Price Query
```python
question = "What is the current price?"
answer = chatbot.ask(session_id, question)
# Web search triggers automatically
# Output includes: "According to current search results: ..."
```

### Example 2: Product Comparison
```python
question = "Compare this with Samsung Galaxy S24"
answer = chatbot.ask(session_id, question)
# Web search fetches comparison data
# Output includes competitive analysis
```

### Example 3: Feature Query (No Search)
```python
question = "What are the main features?"
answer = chatbot.ask(session_id, question)
# No web search - uses product data
# Output based on scraped product information
```

## Limitations

1. **Search Quality**: Results depend on Google's index and Serper API
2. **Rate Limits**: 2,500 searches/month on free tier
3. **Response Time**: Adds 1-2 seconds to answer generation
4. **Relevance**: Search results may not always be perfectly relevant
5. **No Real-Time Data**: Serper API uses cached Google data (may be slightly delayed)

## Future Enhancements

Potential improvements for future versions:
- Custom search filters (date range, specific websites)
- Caching of search results to reduce API calls
- User control over when to trigger search
- More sophisticated keyword detection
- Integration with other search APIs (Bing, DuckDuckGo)
