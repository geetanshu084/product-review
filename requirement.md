# Product Specification: Amazon Product Analysis Agent

## Project Goal
Build a Python-based intelligent agent that analyzes Amazon products by scraping product information and reviews, then uses Google Gemini LLM via LangChain to provide comprehensive analysis and answer user questions interactively.

---

## Core Requirements

### 1. Amazon Product Scraper
**Functionality:**
- Accept Amazon product URL as input
- Extract ASIN (Amazon Standard Identification Number) from URL
- Scrape the following data:
  - Product title
  - Brand name
  - Current price
  - Overall rating (e.g., 4.5/5)
  - Total number of reviews
  - Product description/features (bullet points)
  - Top 1000 customer reviews (mix of positive and negative)
  - Seller name and rating

**Technical Implementation:**
- Use `requests` library for HTTP requests
- Use `BeautifulSoup4` for HTML parsing
- Add appropriate headers (User-Agent) to avoid blocking
- Implement 2-3 second delay between requests
- Handle errors gracefully (invalid URL, product not found, scraping failures)

**Output:** Return structured data as Python dictionary

---

### 2. LLM Analysis Engine
**Functionality:**
- Take scraped product data as input
- Use Google Gemini API via LangChain to analyze the data
- Generate structured analysis with these sections:
  - **Executive Summary** (2-3 sentences)
  - **Product Overview** (name, price, category)
  - **Pros** - categorized by: Quality, Performance, Value, Features, Design
  - **Cons** - categorized by: Quality Issues, Performance Problems, Value Concerns, Usability Issues
  - **Seller Analysis** - rating, trust score, fulfillment method
  - **After-Sales Service** - warranty info, return policy, customer support quality (extracted from reviews)
  - **Recommendation** - Clear Buy/Wait/Avoid with reasoning

**Technical Implementation:**
- Load system prompt from `config/prompts/product_analysis_prompt.txt`
- Use LangChain's `ChatGoogleGenerativeAI` for Gemini integration
- Use `PromptTemplate` for structured prompt engineering
- Use `LLMChain` to connect prompt + model
- Format output in clean, readable markdown

**Output:** Formatted analysis as markdown string

---

### 3. Conversational Q&A System
**Functionality:**
- Allow users to ask follow-up questions about the analyzed product
- Maintain conversation context (remember previous questions/answers)
- Answer questions based on the scraped product data and reviews
- If information not available in data, clearly state that

**Technical Implementation:**
- Use LangChain's `ConversationBufferMemory` in redis for chat history
- Use `ConversationalRetrievalChain` or custom chain for Q&A
- Pass product data as context to each question
- Maintain session state across multiple questions

**Output:** Text response to user's question

---

### 4. Streamlit Web Interface
**Functionality:**
Create a simple, user-friendly web interface with:

**Page 1: Product Analysis**
- Text input field for Amazon product URL
- "Analyze Product" button
- Loading spinner during scraping/analysis
- Display formatted analysis results
- Show error messages if scraping fails

**Page 2: Q&A Chat**
- Chat interface for asking questions
- Display conversation history (user questions + agent responses)
- "Clear Chat" button to reset conversation
- Text input for new questions
- Send button

**Technical Implementation:**
- Use `streamlit` library
- Use `st.session_state` to store:
  - Scraped product data
  - Analysis results
  - Chat history
- Use tabs or sidebar for navigation between Analysis and Q&A
- Add proper styling with st.markdown for better readability



## User Workflow

1. User opens Streamlit app
2. User pastes Amazon product URL in input field
3. User clicks "Analyze Product" button
4. App scrapes Amazon page (shows loading spinner)
5. App sends data to Gemini for analysis
6. App displays formatted analysis results
7. User switches to Q&A tab
8. User asks questions about the product
9. Agent answers based on scraped data and context
10. User can continue conversation or analyze new product

---

## Error Handling Requirements

1. **Invalid URL**: Show error message "Invalid Amazon URL. Please provide a valid product URL."
2. **Scraping Failed**: Show error "Failed to scrape product. The page might be unavailable or blocked."
3. **API Error**: Show error "LLM analysis failed. Please check your API key and try again."
4. **No Product Data for Q&A**: Show message "Please analyze a product first before asking questions."

---

## Success Criteria

- Successfully scrape at least 90% of standard Amazon product pages
- Generate analysis in under 30 seconds
- Display results in clean, readable format
- Answer follow-up questions accurately based on available data
- Handle errors gracefully without crashing
- Simple, intuitive UI that requires no technical knowledge

---

## Optional Enhancements (Future)

- Add price comparison with other e-commerce sites
- Scrape more than 20 reviews (pagination)
- Add sentiment analysis visualization
- Export analysis as PDF
- Add product comparison feature
- Implement caching to avoid re-scraping


## Deliverables Checklist

- [ ] Complete project structure as specified
- [ ] Working Amazon scraper that extracts all required fields
- [ ] LangChain integration with Gemini for analysis
- [ ] Structured analysis output in markdown format
- [ ] Conversational Q&A system with memory. User redis to persist memory
- [ ] Streamlit UI with two tabs (Analysis + Q&A)
- [ ] Error handling for common failures
- [ ] README.md with setup and usage instructions
- [ ] requirements.txt with all dependencies
- [ ] .env.example template

---

**This specification is complete and ready for implementation. Build all components following this document.**