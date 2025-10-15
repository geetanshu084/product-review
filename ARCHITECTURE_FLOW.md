# Product Analysis Pipeline Architecture

## Complete Flow Overview

The system follows a **6-step pipeline** using **LangChain** for all LLM operations:

```
1. Scrape Amazon Page (HTML parsing)
   ↓
2. Search Internet for Competitor Prices (Serper API)
   ↓
3. Search Internet for External Reviews (Serper API + Web scraping)
   ↓
4. Send ALL Data to LLM → Get Structured JSON (LangChain chain)
   ↓
5. Save Structured Data to Redis (24-hour cache)
   ↓
6. Send Structured Data to LLM → Get Analysis Report (LangChain chain)
   ↓
7. Return to Frontend (Structured data + Analysis)
```

## Architecture Components

### 1. **Backend Modules** (`backend/src/`)

#### `scraper.py` - Amazon HTML Scraper
- **Purpose**: Basic HTML parsing of Amazon pages
- **Configuration**: `use_llm_extraction=False` (LLM disabled in scraper)
- **Output**: Raw product data (title, price, rating, reviews, etc.)
- **No LLM**: Uses BeautifulSoup for HTML parsing only

#### `price_comparison.py` - Serper Price Search
- **Purpose**: Search internet for competitive prices
- **API**: Serper.dev for Google Shopping results
- **Output**: Competitor prices with site names and URLs

#### `analysis/web_search.py` - External Reviews Searcher
- **Purpose**: Search internet for external reviews and discussions
- **Sources**: Reddit, YouTube, review sites, comparison articles
- **Output**: External reviews summary with pros/cons

#### `product_orchestrator.py` - **NEW: Main Pipeline Controller**
- **Purpose**: Orchestrates complete flow using LangChain
- **Key Features**:
  - Two LangChain chains:
    1. **Extraction Chain**: Amazon data + Competitors + Reviews → Structured JSON
    2. **Analysis Chain**: Structured JSON → Markdown Analysis Report
  - Uses `JsonOutputParser` for structured extraction
  - Uses proper LangChain prompt templates
  - Handles Redis caching
  - Error handling and fallbacks

### 2. **API Layer** (`backend/api/`)

#### `services/product_service.py` - Service Orchestrator
```python
class ProductService:
    def scrape_and_analyze(url, include_price_comparison, include_web_search):
        # Step 1: Scrape Amazon
        amazon_data = scraper.scrape_product(url)

        # Step 2: Search competitors
        competitor_data = price_comparer.compare_prices(title)

        # Step 3: Search external reviews
        external_reviews = web_search_analyzer.analyze_product(title)

        # Step 4-6: LLM Processing (orchestrator)
        result = orchestrator.process_product_sync(
            amazon_data,
            competitor_data,
            external_reviews
        )

        return result  # {structured_data, analysis}
```

#### `routes/products.py` - API Endpoints

**NEW Endpoint** (Recommended):
```
POST /api/v1/products/scrape-and-analyze
Body: {"url": "https://amazon.in/dp/..."}
Returns: {
  "success": true,
  "message": "Product scraped and analyzed successfully",
  "analysis": "# Product Analysis...",
  "product_data": {
    "asin": "...",
    "title": "...",
    "bank_offers": [...],
    "competitor_prices": [...],
    "pros": [...],
    "cons": [...],
    "red_flags": [...]
  }
}
```

**Legacy Endpoints** (Still available):
- `POST /api/v1/products/scrape` - Quick scrape without analysis
- `POST /api/v1/products/analyze` - Analyze already-scraped product
- `GET /api/v1/products/product/{asin}` - Get cached product

### 3. **LangChain Integration**

#### Extraction Chain (Structured Data)
```python
# Input: Raw data from all 3 sources
extraction_prompt = PromptTemplate(
    template="""Extract and structure ALL information into JSON:

    RAW AMAZON DATA: {amazon_data}
    COMPETITOR PRICES: {competitor_data}
    EXTERNAL REVIEWS: {external_reviews}

    Return structured JSON with:
    - Basic info (asin, title, price, rating)
    - Bank offers
    - Competitor prices
    - Reviews (Amazon + external)
    - Pros, cons, red flags, key findings
    """,
    input_variables=["amazon_data", "competitor_data", "external_reviews"]
)

extraction_chain = extraction_prompt | extraction_llm | JsonOutputParser()
```

#### Analysis Chain (Markdown Report)
```python
# Input: Structured JSON
analysis_prompt = PromptTemplate(
    template="""Generate comprehensive analysis in markdown:

    STRUCTURED PRODUCT DATA: {product_data}

    Include sections:
    - Overview
    - Pricing Analysis
    - Customer Sentiment
    - Pros & Cons
    - Red Flags
    - Final Verdict
    - Buying Tips
    """,
    input_variables=["product_data"]
)

analysis_chain = analysis_prompt | analysis_llm
```

### 4. **Frontend Integration** (`frontend/src/`)

The frontend will call the new unified endpoint:

```typescript
// Call unified endpoint
const response = await axios.post(
  `${API_BASE_URL}/api/v1/products/scrape-and-analyze`,
  { url: amazonUrl }
);

// Response includes BOTH structured data and analysis
const { product_data, analysis } = response.data;

// Display structured pricing overview
<PriceOverview product={product_data} />

// Display tabs with analysis, reviews, etc.
<Tabs>
  <Tab label="Analysis">{analysis}</Tab>
  <Tab label="Reviews">{product_data.reviews}</Tab>
  <Tab label="Chat"><ChatTab /></Tab>
</Tabs>
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│  User enters Amazon URL → POST /scrape-and-analyze         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    BACKEND API (FastAPI)                    │
│                  products.py: /scrape-and-analyze           │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│               PRODUCT SERVICE ORCHESTRATOR                  │
│            service.scrape_and_analyze(url)                  │
└─────┬───────────┬─────────────┬────────────────┬────────────┘
      │           │             │                │
   Step 1      Step 2        Step 3          Step 4-6
      │           │             │                │
┌─────▼─────┐ ┌──▼──────┐  ┌───▼────────┐  ┌───▼─────────────┐
│  SCRAPER  │ │  PRICE  │  │    WEB     │  │  ORCHESTRATOR   │
│  scraper  │ │COMPARER │  │   SEARCH   │  │  (LangChain)    │
│   .py     │ │  .py    │  │ ANALYZER   │  │                 │
└─────┬─────┘ └──┬──────┘  └───┬────────┘  │  ┌────────────┐ │
      │          │             │            │  │ Extraction │ │
      │          │             │            │  │   Chain    │ │
 Amazon HTML  Serper API   Serper API      │  │    (LLM)   │ │
      │          │             │            │  └──────┬─────┘ │
      │          │             │            │         │       │
      └──────────┴─────────────┴────────────┼─────────▼───────┤
                                            │  Structured     │
                                            │  JSON Data      │
                                            │         │       │
                                            │    Save to      │
                                            │     Redis       │
                                            │         │       │
                                            │  ┌──────▼─────┐ │
                                            │  │ Analysis   │ │
                                            │  │   Chain    │ │
                                            │  │   (LLM)    │ │
                                            │  └──────┬─────┘ │
                                            └─────────┼───────┘
                                                      │
                                            Markdown Analysis
                                                      │
┌─────────────────────────────────────────────────────▼───────┐
│                   RESPONSE TO FRONTEND                      │
│  {                                                          │
│    structured_data: {...},  // With pricing, offers, etc.  │
│    analysis: "# Product Analysis..."                       │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

## Key Improvements

### ✅ Proper LangChain Usage
- **Two separate chains** for different purposes
- **Prompt templates** with clear input variables
- **Output parsers** for structured extraction
- **Proper chain composition** using `|` operator

### ✅ Clean Separation of Concerns
- **Scraper**: Only HTML parsing, no LLM
- **Searchers**: Only web search, no analysis
- **Orchestrator**: Only LLM operations with LangChain
- **Service**: Only orchestration logic

### ✅ Complete Data Flow
1. ✅ Scrape Amazon
2. ✅ Search competitors
3. ✅ Search external reviews
4. ✅ LLM structured extraction
5. ✅ Redis caching
6. ✅ LLM analysis
7. ✅ Return both to frontend

### ✅ Frontend Display
- **PriceOverview component**: Shows Amazon price, bank offers, exchange, competitors
- **Analysis tab**: Shows LLM-generated analysis
- **Reviews tab**: Shows reviews with verified badges
- **Chat tab**: Q&A about product

## Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_google_api_key

# Optional (enables price comparison & web search)
SERPER_API_KEY=your_serper_api_key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Feature Flags
```python
# In product_service.py
result = product_service.scrape_and_analyze(
    url=url,
    include_price_comparison=True,   # Toggle competitor search
    include_web_search=True           # Toggle external reviews
)
```

## Testing the New Flow

### Using curl:
```bash
# Complete pipeline
curl -X POST "http://localhost:8000/api/v1/products/scrape-and-analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://amazon.in/dp/B0D79G62J3"}'
```

### Using Frontend:
1. Enter Amazon URL
2. Click "Analyze"
3. See pricing overview at top
4. See complete analysis in tabs
5. Bank offers, competitor prices, pros/cons all displayed

## Benefits

1. **Clean Architecture**: Each component has single responsibility
2. **LangChain Best Practices**: Proper chains, prompts, parsers
3. **Complete Data**: Amazon + Competitors + External reviews
4. **Structured Output**: JSON for display, Markdown for analysis
5. **Caching**: Redis saves processed data
6. **Error Handling**: Graceful fallbacks at each step
7. **Scalable**: Easy to add more data sources or LLM providers

## Next Steps

1. ✅ **Test complete flow** with real product
2. Update frontend to use new `/scrape-and-analyze` endpoint
3. Add loading states for each step
4. Add progress indicators (Step 1/6, Step 2/6, etc.)
5. Add error handling UI
6. Add retry logic for failed steps
