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
from langchain.agents import initialize_agent, AgentType
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

        # Store for product title (used by web search tool)
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

        # System prefix template for agent - just high-level instructions
        # LangChain's initialize_agent handles ReAct format, tools, scratchpad automatically
        # Note: Product data will be inserted via string replacement (not .format())
        self.agent_prefix_template = """You are a helpful product analysis assistant. Answer questions about products based on the provided product data.

Guidelines:
1. First check the PRODUCT DATA (JSON format) for the answer
2. The product data includes: title, brand, price, rating, features, reviews, specifications, warranty, bank_offers, etc.
3. If there's a 'price_comparison' field, it shows prices across different platforms (Amazon, Flipkart, eBay, etc.) - use this to answer questions about where to buy, price differences, best deals, and savings
4. Use the web_search tool ONLY when you need current/updated information that's not in the product data (like current market prices, latest comparisons, real-time availability)
5. If information is in the product data, DO NOT use web_search - answer directly
6. Be specific and quote from reviews when relevant
7. When recommending where to buy, mention the platform, price, and any savings
8. Keep answers concise but informative

PRODUCT DATA (JSON):
<<PRODUCT_DATA>>"""

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

        # Convert product data to JSON string for LLM context
        product_data_json = json.dumps(product_data, indent=2, ensure_ascii=False)

        # Store product title for web search tool context
        self._current_product_title = product_data.get('title', '')

        # Generate answer using LangChain's initialize_agent
        # This handles ReAct format, tools, and scratchpad automatically
        try:
            # Create session-specific memory with RedisChatMessageHistory
            message_history = self._get_message_history(session_id)
            memory = ConversationBufferMemory(
                chat_memory=message_history,
                memory_key="chat_history",
                return_messages=True
            )

            # Insert product data JSON into agent prefix using string replacement
            # Escape JSON curly braces for PromptTemplate by doubling them: { becomes {{
            product_data_escaped = product_data_json.replace('{', '{{').replace('}', '}}')
            agent_prefix_formatted = self.agent_prefix_template.replace('<<PRODUCT_DATA>>', product_data_escaped)

            # Use initialize_agent - LangChain handles everything automatically:
            # - ReAct format (Thought/Action/Observation)
            # - Tool descriptions and invocation
            # - Agent scratchpad management
            # - Conversation memory integration
            agent = initialize_agent(
                tools=self.tools,  # Can be empty list
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                agent_kwargs={
                    "prefix": agent_prefix_formatted
                }
            )

            # Invoke agent - LangChain handles all the complexity
            response = agent.invoke({"input": question})
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
