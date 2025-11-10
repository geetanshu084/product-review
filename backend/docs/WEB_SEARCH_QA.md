# Web Search & Price Comparison in Q&A Chatbot

## Overview
The Q&A chatbot includes two powerful features for answering product questions:
1. **LLM-Driven Web Search**: Uses LangChain tool-calling agent where the LLM intelligently decides when to search the internet for current information
2. **Multi-Platform Price Comparison**: Provides price data from Amazon, Flipkart, eBay, Walmart, and other platforms from cached product data
3. **Multi-Provider LLM Support**: Configurable LLM provider (Google Gemini, OpenAI, Anthropic, etc.) via environment variables

## How It Works

### Price Comparison Data in Q&A

When a product is analyzed via `/scrape-and-analyze` endpoint, price comparison data is automatically:
1. Fetched from multiple e-commerce platforms using Serper API (runs in parallel with web search)
2. Cached in Redis along with complete product data (24-hour TTL)
3. Retrieved by chatbot using product_id
4. Cleaned and formatted for LLM context (removes Google redirect URLs)
5. Included in the chatbot's system prompt as structured data

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

The chatbot uses **LangChain's tool-calling agent** with a web search tool. The LLM intelligently decides when to use the tool based on:

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

### 1. Choose Search Provider

The chatbot supports two search providers:

#### Option A: DuckDuckGo (Default - Free, No API Key)
- **Cost**: Completely free
- **Setup**: No API key required
- **Rate Limits**: Reasonable limits for personal use
- **Quality**: Good quality results from DuckDuckGo search

#### Option B: Serper (Google Search - API Key Required)
- **Cost**: Free tier includes 2,500 searches/month
- **Setup**: Requires API key from [serper.dev](https://serper.dev/)
- **Rate Limits**: 2,500 searches/month (free tier)
- **Quality**: Premium Google search results

### 2. Configure Search Provider

Add search provider configuration to the `.env` file:

```bash
# Search Provider Configuration
# Options: duckduckgo (default, free) or serper (requires API key)
SEARCH_PROVIDER=duckduckgo

# Only needed if using SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_api_key_here
```

**Switching between providers:**
- For DuckDuckGo (default): Set `SEARCH_PROVIDER=duckduckgo` or leave unset
- For Serper: Set `SEARCH_PROVIDER=serper` and add your `SERPER_API_KEY`

### 3. Configure LLM Provider
Add LLM provider configuration to `.env`:

```bash
# LLM Configuration (defaults to Google Gemini)
LLM_PROVIDER=google  # Options: google, openai, anthropic, ollama
LLM_MODEL=gemini-2.0-flash-exp  # Model name for the provider
GOOGLE_API_KEY=your_google_api_key_here
# Or for other providers:
# OPENAI_API_KEY=your_openai_key
# ANTHROPIC_API_KEY=your_anthropic_key
```

### 4. Enable Web Search
Web search is enabled automatically based on your `SEARCH_PROVIDER` configuration:
- **DuckDuckGo**: Enabled automatically, no API key needed
- **Serper**: Enabled when `SERPER_API_KEY` is set in `.env`

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

1. **Product Analysis** (LangGraph Workflow via `/scrape-and-analyze`):
   - Scrape product page (Amazon/Flipkart)
   - Run in parallel:
     - Price comparison from multiple platforms
     - Web search for external reviews
   - Combine all data and run LLM analysis
   - Save complete product data to Redis: `product:{product_id}` (24h TTL)
   - Save analysis to Redis: `product:{product_id}:analysis` (24h TTL)

2. **Data Storage** (Redis):
   - **Product Data Key**: `product:{product_id}` (e.g., `product:B0D7HG2GZD`)
   - **Analysis Key**: `product:{product_id}:analysis`
   - **Chat History Key**: `chat_history:{session_id}` (per-user conversation)
   - Contains: Product info + Reviews + Price comparison + Web search results

3. **Q&A Session** (`chatbot.py`):
   - Retrieve product data from Redis using product_id
   - Clean data (remove Google redirect URLs, simplify competitor prices)
   - Format product context as JSON in system prompt
   - Load conversation history from Redis (session-specific)
   - Answer questions using:
     - Cached product features and reviews
     - **Simplified competitor price data**
     - Web search tool (when LLM decides it's needed)

4. **Response Generation**:
   - LLM receives product data in system prompt
   - Tool-calling agent decides whether to use Search tool
   - Answers questions about product, prices, features
   - Provides platform recommendations with simplified URLs
   - Conversation history persisted to Redis automatically

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
The chatbot is implemented in `src/chatbot.py` using LangChain's standard components:

**Architecture:**
- **Memory**: `ConversationBufferMemory` with `RedisChatMessageHistory` backend
- **Agent Framework**: LangChain tool-calling agent (`create_tool_calling_agent`)
- **LLM**: Configurable provider (Google Gemini, OpenAI, Anthropic, etc.)
- **Tool**: `Search` tool using either:
  - `duckduckgo-search` (default, free)
  - `GoogleSerperAPIWrapper` (requires API key)
- **Executor**: `AgentExecutor` with memory, max 10 iterations

**What LangChain Handles Automatically:**
- ✅ Conversation history loading and saving to Redis
- ✅ `agent_scratchpad` (intermediate steps and tool calls)
- ✅ Tool-calling format (native function calling for compatible models)
- ✅ Tool descriptions and invocation
- ✅ Memory persistence across requests
- ✅ Automatic tool result integration


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

## Integration with React Web UI

The chatbot is integrated into the React frontend via FastAPI endpoints:

**API Endpoints:**
- `POST /api/v1/chat/ask` - Ask a question about a product
- `POST /api/v1/chat/clear` - Clear conversation history for a session

**How It Works:**
1. User analyzes product → Data cached in Redis with product_id
2. User asks question in Chat tab
3. Frontend sends request with session_id, product_id, and question
4. Backend retrieves product data from cache using product_id
5. Chatbot loads conversation history for session_id
6. LLM decides whether to use Search tool
7. Response returned to frontend and displayed
8. Conversation history automatically saved to Redis

**UI Features:**
- Real-time chat interface with message history
- Typing indicator during question processing
- Link detection and rich formatting
- Clear chat button to reset conversation
- Persistent history across page refreshes (via session_id)

## Limitations

1. **Search Quality**: Results depend on Google's index and Serper API
2. **Rate Limits**: 2,500 searches/month on free tier for Serper API
3. **Response Time**: Web search adds ~1-2 seconds when triggered
4. **Relevance**: Search results may not always be perfectly relevant
5. **Cached Data Staleness**: Product data cached for 24 hours (may not reflect real-time prices)
6. **Tool-Calling Support**: Best with models that support native function calling (Gemini, GPT-4, etc.)

## Current Implementation Status

**Implemented:**
- ✅ Tool-calling agent with web search capability
- ✅ Multi-provider LLM support (Google, OpenAI, Anthropic, Ollama)
- ✅ Redis-backed conversation history (per-session)
- ✅ Product data caching with 24-hour TTL
- ✅ Automatic data cleaning (removes Google redirect URLs)
- ✅ Simplified competitor price formatting
- ✅ React Web UI integration
- ✅ FastAPI endpoints for chat operations

**Future Enhancements:**
- ✅ **COMPLETED**: Integration with DuckDuckGo (free alternative to Serper)
- Custom search filters (date range, specific websites)
- Streaming responses for better UX
- User control over when to trigger search
- Integration with other search APIs (Bing, Brave Search)
- Function-calling for structured data extraction
- Voice input/output support
