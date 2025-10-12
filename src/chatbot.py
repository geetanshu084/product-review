"""
Conversational Q&A System Module
Uses LangChain's standard Redis chat message history for persistent memory
Includes web search capability via LangChain tools
"""

import json
import os
from typing import Dict, List, Optional
import redis
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.chat_message_histories import RedisChatMessageHistory


class ProductChatbot:

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
        google_api_key: Optional[str] = None,
        serper_api_key: Optional[str] = None,
        enable_web_search: bool = True
    ):
        """
        Initialize the chatbot

        Args:
            credentials_path: Path to GCP service account JSON file (deprecated - use google_api_key instead)
            redis_host: Redis host address
            redis_port: Redis port number
            redis_db: Redis database number
            redis_password: Redis password (optional)
            model_name: Name of the Gemini model to use
            google_api_key: Google API key for Gemini (recommended)
            serper_api_key: Serper API key for web search (optional)
            enable_web_search: Enable web search capability (default: True)
        """
        # Check for API key first (recommended approach)
        # api_key = os.getenv('GOOGLE_API_KEY')

        if not os.getenv('GOOGLE_API_KEY'):
            raise ValueError(
                "Google API key is required. Please either:\n"
                "1. Set GOOGLE_API_KEY environment variable in your .env file, or\n"
                "2. Pass google_api_key parameter\n\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.5,
            convert_system_message_to_human=True,
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )

        # Store Redis connection details for creating session-specific message histories
        self.redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}" if redis_password else f"redis://{redis_host}:{redis_port}/{redis_db}"

        # Simple Redis client for product data storage (not messages)
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )

        # Initialize web search if enabled
        self.enable_web_search = enable_web_search
        self.serper_api_key = serper_api_key or os.getenv('SERPER_API_KEY')

        # Store for product context (used by tools)
        self._current_product_context = ""
        self._current_product_title = ""

        # Create tools
        self.tools = []
        if enable_web_search and self.serper_api_key:
            print("✓ Web search enabled for Q&A (LangChain tool)")
            # Create web search tool
            search_tool = Tool(
                name="web_search",
                description="Useful for searching the internet for current information about products, prices, availability, comparisons, or any up-to-date information. Input should be a search query string.",
                func=self._web_search_tool
            )
            self.tools.append(search_tool)
        elif enable_web_search and not self.serper_api_key:
            print("⚠ Web search disabled (SERPER_API_KEY not found)")
            self.enable_web_search = False

        # Single system prompt - works with or without tools
        # Build template using string concatenation to avoid .format() issues
        system_prompt_start = """You are a helpful product analysis assistant. Answer questions about products based on the provided product data.

PRODUCT DATA:
{product_context}

Guidelines:
1. First check the PRODUCT DATA for the answer
2. PRICE COMPARISON data shows prices across different platforms - use this to answer questions about where to buy, price differences, best deals, and savings
3. Use the web_search tool ONLY when you need current/updated information that's not in the product data (like current market prices, latest comparisons, real-time availability)
4. If information is in the product data, DO NOT use web_search - answer directly
5. Be specific and quote from reviews when relevant
6. When recommending where to buy, mention the platform, price, and any savings
7. Keep answers concise but informative
"""

        # Tool section - only include if tools are available
        tool_section = """
TOOLS:
------
You have access to the following tools:

{tools}

To use a tool, use this format:
```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response, or if you do not need to use a tool:
```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```
""" if self.tools else ""

        system_prompt_end = """
Begin!

Question: {input}
{agent_scratchpad}"""

        # Build full template using string concatenation
        full_template = system_prompt_start + tool_section + system_prompt_end

        # Define input variables based on whether tools are present
        if self.tools:
            input_vars = ["product_context", "input", "agent_scratchpad", "tools", "tool_names"]
        else:
            input_vars = ["product_context", "input", "agent_scratchpad"]

        self.agent_prompt = PromptTemplate(
            input_variables=input_vars,
            template=full_template
        )

        # Create agent - works with or without tools (empty list is fine)
        self.agent = create_react_agent(self.llm, self.tools, self.agent_prompt)

    def format_product_context(self, product_data: Dict) -> str:
        """
        Format product data for context

        Args:
            product_data: Product data dictionary

        Returns:
            Formatted string
        """
        context = []

        # Basic information
        context.append("=== BASIC INFORMATION ===")
        context.append(f"Product: {product_data.get('title', 'N/A')}")
        context.append(f"Brand: {product_data.get('brand', 'N/A')}")
        context.append(f"Category: {product_data.get('category', 'N/A')}")
        context.append(f"Price: {product_data.get('price', 'N/A')}")
        context.append(f"Rating: {product_data.get('rating', 'N/A')}")
        context.append(f"Total Reviews: {product_data.get('total_reviews', 'N/A')}")
        context.append(f"Availability: {product_data.get('availability', 'N/A')}")
        context.append("")

        # Product features
        if product_data.get('features'):
            context.append("=== PRODUCT FEATURES ===")
            for feature in product_data['features']:
                context.append(f"- {feature}")
            context.append("")

        # Product specifications
        specifications = product_data.get('specifications', {})
        if specifications:
            context.append("=== SPECIFICATIONS ===")
            for key, value in specifications.items():
                context.append(f"{key}: {value}")
            context.append("")

        # Product details (dimensions, weight, etc.)
        product_details = product_data.get('product_details', {})
        if product_details:
            context.append("=== PRODUCT DETAILS ===")
            for key, value in product_details.items():
                context.append(f"{key}: {value}")
            context.append("")

        # Technical details
        technical_details = product_data.get('technical_details', {})
        if technical_details:
            context.append("=== TECHNICAL DETAILS ===")
            for key, value in technical_details.items():
                context.append(f"{key}: {value}")
            context.append("")

        # Additional information
        additional_info = product_data.get('additional_information', {})
        if additional_info:
            context.append("=== ADDITIONAL INFORMATION ===")
            for key, value in additional_info.items():
                context.append(f"{key}: {value}")
            context.append("")

        # Warranty
        warranty = product_data.get('warranty', '')
        if warranty and warranty != "Warranty information not available":
            context.append("=== WARRANTY ===")
            context.append(warranty)
            context.append("")

        # Bank offers
        bank_offers = product_data.get('bank_offers', [])
        if bank_offers:
            context.append("=== BANK OFFERS ===")
            for i, offer in enumerate(bank_offers, 1):
                context.append(f"{i}. {offer.get('bank', 'Bank')}: {offer.get('offer_type', 'Offer')} - {offer.get('description', '')}")
                if offer.get('terms'):
                    context.append(f"   Terms: {offer['terms']}")
            context.append("")

        # Customer reviews
        reviews = product_data.get('reviews', [])
        if reviews:
            context.append(f"=== CUSTOMER REVIEWS ({len(reviews)} reviews) ===")
            for i, review in enumerate(reviews[:10], 1):
                context.append(f"{i}. [{review.get('rating', 'N/A')}] {review.get('title', '')}")
                context.append(f"   {review.get('text', '')[:200]}...")
            context.append("")

        # Price comparison data
        price_comparison = product_data.get('price_comparison')
        if price_comparison and price_comparison.get('total_results', 0) > 0:
            context.append("=== PRICE COMPARISON ACROSS PLATFORMS ===")
            context.append(f"Total Results Found: {price_comparison['total_results']}")
            context.append("")

            # Price statistics
            stats = price_comparison.get('price_stats', {})
            if stats and stats.get('total_results', 0) > 0:
                context.append("Price Statistics:")
                currency = "INR"  # Default currency
                context.append(f"  Minimum Price: {currency} {stats.get('min_price', 0):.2f}")
                context.append(f"  Maximum Price: {currency} {stats.get('max_price', 0):.2f}")
                context.append(f"  Average Price: {currency} {stats.get('avg_price', 0):.2f}")
                context.append(f"  Median Price: {currency} {stats.get('median_price', 0):.2f}")
                context.append("")

            # Best deal
            best_deal = price_comparison.get('best_deal')
            if best_deal:
                context.append("Best Deal Found:")
                context.append(f"  Platform: {best_deal['platform'].upper()}")
                context.append(f"  Seller: {best_deal['seller']}")
                context.append(f"  Price: {best_deal['currency']} {best_deal['price']:.2f}")
                context.append(f"  Rating: {best_deal.get('rating', 'N/A')}")
                context.append(f"  Potential Savings: {best_deal['currency']} {best_deal['savings']:.2f} ({best_deal['savings_percent']:.1f}%)")
                context.append(f"  URL: {best_deal.get('url', 'N/A')}")
                context.append("")

            # Platform breakdown (show top 3 from each platform)
            platforms = price_comparison.get('price_comparison', {})
            if platforms:
                context.append("Price by Platform (showing lowest prices):")
                for platform, items in platforms.items():
                    if items:
                        # Sort by price and show top 3
                        sorted_items = sorted(items, key=lambda x: x['price'])[:3]
                        context.append(f"  {platform.upper()} ({len(items)} total results):")
                        for idx, item in enumerate(sorted_items, 1):
                            context.append(f"    {idx}. {item['currency']} {item['price']:.2f} - {item['seller']}")
                            if item.get('rating'):
                                context.append(f"       Rating: {item['rating']}, Reviews: {item.get('reviews', 0)}")
                            context.append(f"       URL: {item.get('url', 'N/A')}")
                context.append("")

        return "\n".join(context)

    def _web_search_tool(self, query: str) -> str:
        """
        Perform web search using Serper API (LangChain tool)

        Args:
            query: Search query string

        Returns:
            Formatted search results string
        """
        if not os.getenv('SERPER_API_KEY'):
            return "Web search unavailable (API key not configured)"

        try:
            # Combine with product title for better context
            if self._current_product_title:
                search_query = f"{self._current_product_title} {query}"
            else:
                search_query = query

            payload = {
                "q": search_query,
                "num": 5  # Fixed to 5 results
            }

            headers = {
                "X-API-KEY": os.getenv('SERPER_API_KEY'),
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://google.serper.dev/search",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                return f"Web search error: HTTP {response.status_code}"

            data = response.json()
            organic_results = data.get("organic", [])

            if not organic_results:
                return "No search results found"

            # Format results
            formatted_results = []
            formatted_results.append(f"Search query: {query}")
            formatted_results.append(f"Found {len(organic_results)} results:")
            formatted_results.append("")

            for i, result in enumerate(organic_results[:5], 1):
                formatted_results.append(f"{i}. {result.get('title', 'N/A')}")
                formatted_results.append(f"   {result.get('snippet', 'N/A')}")
                formatted_results.append(f"   Source: {result.get('link', 'N/A')}")
                formatted_results.append("")

            return "\n".join(formatted_results)

        except Exception as e:
            return f"Web search failed: {str(e)}"

    def _get_message_history(self, session_id: str) -> RedisChatMessageHistory:
        """
        Get LangChain RedisChatMessageHistory for a session

        Args:
            session_id: Unique session identifier

        Returns:
            RedisChatMessageHistory instance
        """
        return RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_url,
            key_prefix="chat_history:"
        )

    def ask(self, session_id: str, question: str) -> str:
        """
        Ask a question about the product (LLM decides whether to use web search tool)

        Args:
            session_id: Unique session identifier
            question: User's question

        Returns:
            Answer string

        Raises:
            ValueError: If no product data is available
        """
        # Get product data from Redis
        product_data = self.get_product_data(session_id)
        if not product_data:
            raise ValueError("Please analyze a product first before asking questions.")

        # Format product context
        product_context = self.format_product_context(product_data)

        # Store product title for web search tool context
        self._current_product_context = product_context
        self._current_product_title = product_data.get('title', '')

        # Generate answer using unified agent approach
        try:
            # Create session-specific memory with RedisChatMessageHistory
            message_history = self._get_message_history(session_id)
            memory = ConversationBufferMemory(
                chat_memory=message_history,
                memory_key="chat_history",
                input_key="input",  # Specify which key is the main input
                return_messages=True
            )

            # Create AgentExecutor with memory (works with or without tools)
            # LangChain handles everything automatically
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,  # Can be empty list - LangChain handles it
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3
            )

            # Invoke - LangChain automatically handles:
            # - conversation history (from memory)
            # - agent_scratchpad (intermediate steps)
            # - ReAct format (thought/action/observation loop)
            # - Tool execution (if tools available)
            response = agent_executor.invoke({
                "product_context": product_context,
                "input": question
            })
            answer = response.get('output', '').strip()

            return answer

        except Exception as e:
            raise Exception(f"Failed to generate answer: {str(e)}")

    def set_product_data(self, session_id: str, product_data: Dict):
        """
        Set product data for a session

        Args:
            session_id: Unique session identifier
            product_data: Product data dictionary
        """
        key = f"product_data:{session_id}"
        self.redis_client.set(key, json.dumps(product_data))

    def get_product_data(self, session_id: str) -> Optional[Dict]:
        """
        Get product data for a session

        Args:
            session_id: Unique session identifier

        Returns:
            Product data dictionary or None
        """
        key = f"product_data:{session_id}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries (for compatibility)
        """
        message_history = self._get_message_history(session_id)
        messages = message_history.messages

        # Convert LangChain messages to dict format for compatibility
        return [
            {
                'role': 'user' if msg.type == 'human' else 'assistant',
                'content': msg.content
            }
            for msg in messages
        ]

    def clear_conversation(self, session_id: str):
        """
        Clear conversation history for a session

        Args:
            session_id: Unique session identifier
        """
        message_history = self._get_message_history(session_id)
        message_history.clear()

    def clear_all_data(self, session_id: str):
        """
        Clear all data (conversation and product) for a session

        Args:
            session_id: Unique session identifier
        """
        # Clear conversation history
        message_history = self._get_message_history(session_id)
        message_history.clear()

        # Clear product data
        key = f"product_data:{session_id}"
        self.redis_client.delete(key)
