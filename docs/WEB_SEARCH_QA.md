# Web Search & Price Comparison in Q&A Chatbot

## Overview
The Q&A chatbot includes two powerful features for answering product questions:
1. **LLM-Driven Web Search**: Uses LangChain tools where the LLM intelligently decides when to search the internet for current information
2. **Multi-Platform Price Comparison**: Provides price data from Amazon, Flipkart, eBay, Walmart, and other platforms stored in Redis

## How It Works

### Price Comparison Data in Q&A

When a product is analyzed, price comparison data is automatically:
1. Fetched from multiple e-commerce platforms using Serper API
2. Saved to Redis along with product data
3. Made available to the Q&A chatbot
4. Formatted and included in the LLM context

The chatbot can now answer questions like:
- "Where can I buy this product?"
- "What's the best price available?"
- "Which platform has the cheapest price?"
- "How much can I save if I buy from the cheapest platform?"
- "Show me prices on Amazon vs Flipkart"
- "Which seller offers the best deal?"

**Example:**
```
User: "Where can I buy this product?"
Bot: "According to the price comparison data, the best deal is on FLIPKART
      at INR 55,900 from iNvent - Apple Premium Reseller. This offers
      potential savings of INR 79,000 (58.5%) compared to other platforms."
```

### LLM-Driven Web Search (LangChain Tool Integration)

The chatbot uses **LangChain's ReAct agent** with a web search tool. The LLM (Google Gemini) intelligently decides when to use the tool based on:

**The LLM uses web search when:**
- Information is not available in the product data
- Question requires current/real-time information
- User asks for comparisons with other products
- User asks about market conditions, availability, or deals

**The LLM answers directly when:**
- Information is already in the product data
- Question is about features, specs, reviews, or warranty
- Price comparison data in Redis has the answer

**Key Advantage:** The LLM makes context-aware decisions instead of relying on keyword matching. It understands the question's intent and only searches when necessary.

### Example Questions

**Questions where LLM decides to use web search:**
- "Compare this with Samsung Galaxy S24" → LLM uses web_search tool
- "What are the latest deals on this product?" → LLM uses web_search tool
- "Is this phone better than iPhone 14 Pro?" → LLM uses web_search tool
- "Show me similar alternatives" → LLM uses web_search tool

**Questions where LLM answers directly:**
- "What are the key features of this phone?" → Direct answer from product data
- "What do customers say about the camera?" → Direct answer from reviews
- "What color is this phone?" → Direct answer from product data
- "What is the price?" → Direct answer (from product data, not web search)
- "Tell me about the reviews" → Direct answer from reviews

**How the LLM Decides:**
The LLM follows a thought process (visible in verbose mode):
```
Question: Compare this with Samsung Galaxy S24
Thought: I need comparison info that's not in product data
Action: web_search
Action Input: "Apple iPhone 15 Pro vs Samsung Galaxy S24"
Observation: [search results]
Thought: I now have the comparison information
Final Answer: [provides comparison]
```

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

## Data Flow

### Complete Product Analysis to Q&A Flow

1. **Product Analysis** (`app.py` → `analyzer.py`):
   - Scrape Amazon product data
   - Fetch price comparison from multiple platforms
   - Save complete product data (including price comparison) to Redis

2. **Data Storage** (Redis):
   - Key: `chat:{session_id}:product_data`
   - Contains: Product info + Reviews + **Price comparison data**

3. **Q&A Session** (`chatbot.py`):
   - Retrieve product data from Redis (includes price comparison)
   - Format product context with price comparison section
   - Answer questions using:
     - Product features and reviews
     - **Price comparison across platforms**
     - Web search results (when triggered)

4. **Response Generation**:
   - LLM receives full context including price comparison
   - Answers questions about prices, platforms, best deals
   - Provides specific platform and seller recommendations

## Technical Details

### Price Comparison Context Format

The chatbot formats price comparison data in the context as:

```
=== PRICE COMPARISON ACROSS PLATFORMS ===
Total Results Found: 12

Price Statistics:
  Minimum Price: INR 55900.00
  Maximum Price: INR 179900.00
  Average Price: INR 89234.50
  Median Price: INR 75000.00

Best Deal Found:
  Platform: FLIPKART
  Seller: iNvent - Apple Premium Reseller
  Price: INR 55900.00
  Rating: 4.5
  Potential Savings: INR 79000.00 (58.5%)
  URL: https://...

Price by Platform (showing lowest prices):
  AMAZON (5 total results):
    1. INR 67900.00 - Amazon.in
       Rating: 4.6, Reviews: 1234
       URL: https://...
  FLIPKART (3 total results):
    1. INR 55900.00 - iNvent
       Rating: 4.5, Reviews: 567
       URL: https://...
```

### Implementation
The LangChain tool-based web search is implemented in `src/chatbot.py`:

**Architecture:**
- **Agent Framework**: LangChain ReAct agent (`create_react_agent`)
- **LLM**: Google Gemini (makes decisions about tool usage)
- **Tool**: `web_search` tool using Serper API
- **Executor**: `AgentExecutor` with max 3 iterations

**Key Components:**

1. **Tool Definition** (lines ~178-183):
```python
search_tool = Tool(
    name="web_search",
    description="Useful for searching the internet for current information...",
    func=self._web_search_tool
)
```

2. **Agent Creation** (lines ~230-237):
```python
self.agent = create_react_agent(self.llm, self.tools, self.agent_prompt)
self.agent_executor = AgentExecutor(
    agent=self.agent,
    tools=self.tools,
    verbose=True,  # Shows agent's reasoning
    handle_parsing_errors=True,
    max_iterations=3
)
```

3. **Query Execution** (lines ~517-525):
```python
if self.tools:
    # LLM decides whether to use web search
    response = self.agent_executor.invoke({
        "product_context": product_context,
        "history": history,
        "input": question,
        "agent_scratchpad": ""
    })
```

**Key Methods:**
- `format_product_context(product_data)` - Formats all product data including price comparison
- `_web_search_tool(query)` - Web search tool function (called by agent)
- `ask(session_id, question)` - Main method using agent executor
- `set_product_data(session_id, product_data)` - Saves data to Redis
- `get_product_data(session_id)` - Retrieves data from Redis

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

### Example 1: Price Comparison Query (Uses Redis Data)
```python
question = "Where can I buy this product?"
answer = chatbot.ask(session_id, question)
# Uses price comparison data from Redis
# Output: "The best deal is on FLIPKART at INR 55,900 from
#         iNvent - Apple Premium Reseller. This offers potential
#         savings of INR 79,000 (58.5%)..."
```

### Example 2: Platform Comparison (Uses Redis Data)
```python
question = "Show me prices on Amazon vs Flipkart"
answer = chatbot.ask(session_id, question)
# Uses price comparison data from Redis
# Output: Detailed price breakdown from both platforms with
#         specific sellers and savings information
```

### Example 3: Current Price Query (Triggers Web Search)
```python
question = "What is the current price?"
answer = chatbot.ask(session_id, question)
# Web search triggers automatically
# Output includes: "According to current search results: ..."
```

### Example 4: Product Comparison (Triggers Web Search)
```python
question = "Compare this with Samsung Galaxy S24"
answer = chatbot.ask(session_id, question)
# Web search fetches comparison data
# Output includes competitive analysis
```

### Example 5: Feature Query (Uses Product Data)
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
