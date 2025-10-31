"""
Conversational Q&A System Module
Uses LangChain's standard Redis chat message history for persistent memory
Includes web search capability via LangChain tools
Supports multiple LLM providers via environment configuration
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path
import redis
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory

# Load environment variables from .env file
# Find the .env file in the backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

from src.llm_provider import get_llm
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

class ProductChatbot:

    def __init__(self):

        # Initialize LLM using provider factory
        # Provider is configured via LLM_PROVIDER and LLM_MODEL env vars
        self.llm = get_llm(temperature=0.5)

        # Read Redis configuration from environment
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '0'))
        redis_password = os.getenv('REDIS_PASSWORD')

        # Store Redis connection details for creating session-specific message histories
        self.redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}" if redis_password else f"redis://{redis_host}:{redis_port}/{redis_db}"

        # Simple Redis client for product data storage (common across all sessions)
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )

        # Initialize search tool (automatically gets SERPER_API_KEY from env)
        search = GoogleSerperAPIWrapper()

        # Custom search function that returns URLs along with content
        def search_with_urls(query: str) -> str:
            """
            Search and return results with URLs included

            Args:
                query: Search query string

            Returns:
                Formatted search results with titles and URLs
            """
            try:
                results = search.results(query)

                # Format results to include URLs
                formatted_results = []

                # Handle organic results
                if 'organic' in results:
                    for result in results['organic'][:5]:  # Top 5 results
                        title = result.get('title', '')
                        link = result.get('link', '')
                        snippet = result.get('snippet', '')

                        formatted_results.append(f"Title: {title}\nURL: {link}\nSnippet: {snippet}\n")

                # Handle video results (YouTube)
                if 'videos' in results:
                    for video in results['videos'][:5]:  # Top 5 videos
                        title = video.get('title', '')
                        link = video.get('link', '')

                        formatted_results.append(f"Video: {title}\nURL: {link}\n")

                if not formatted_results:
                    # Fallback to basic search if no structured results
                    return search.run(query)

                return "\n".join(formatted_results)

            except Exception as e:
                # Fallback to basic search on error
                return search.run(query)

        search_tool = Tool(
            name="Search",
            description="Useful for searching the internet for current information about products, prices, availability, comparisons, or any up-to-date information. Input should be a search query string. Returns results with URLs.",
            func=search_with_urls
        )
        self.tools = [search_tool]

        # Load system prompt template
        prompt_path = Path(__file__).parent.parent / "config" / "prompts" / "agent_prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt_template = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Agent prompt file not found at {prompt_path}. "
                "Please ensure config/prompts/agent_prompt.txt exists."
            )

    def ask(self, session_id: str, product_id: str, question: str) -> str:
        """
        Ask a question about a product

        Args:
            session_id: Session ID for conversation history
            product_id: Product ID (e.g., ASIN or URL hash) to fetch product data
            question: User's question

        Returns:
            Answer string
        """
        # Get product data from Redis using product_id (common for all sessions)
        product_data = self.get_product_data(product_id)
        if not product_data:
            raise ValueError("Please analyze a product first before asking questions.")

        # Clean product data - remove Google Shopping URLs and keep only direct URLs
        # cleaned_data = self._clean_product_data(product_data)
        product_data_json = json.dumps(product_data, indent=2, ensure_ascii=False)

        # Generate answer using modern LangChain agent
        try:
            chat_histroy = RedisChatMessageHistory(
                session_id=session_id,
                url=self.redis_url,
            )
            memory = ConversationBufferMemory(
                memory_key="chat_history",  # must match your prompt's variable name
                chat_memory=chat_histroy,
                return_messages=True  # recommended for agent chat
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt(product_data_json)),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),

            ])

            agent = create_tool_calling_agent(self.llm, self.tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10,
            )

            # Invoke agent
            result = agent_executor.invoke({"input": question})
            answer = result.get('output', '').strip()

            return answer

        except Exception as e:
            error_msg = str(e)
            # Check if it's a Google API internal error (temporary)
            if "500" in error_msg and "internal error" in error_msg.lower():
                raise Exception("The AI service is temporarily unavailable. Please try asking your question again in a moment.")
            raise Exception(f"Failed to generate answer: {error_msg}")

    def _get_system_prompt(self, product_data_json: str) -> str:
        """
        Get formatted system prompt with product data

        Args:
            product_data_json: Product data in JSON format

        Returns:
            Formatted system prompt string
        """
        # Escape braces for prompt template formatting
        product_data_escaped = product_data_json.replace('{', '{{').replace('}', '}}')

        # Replace placeholder with actual product data
        return self.system_prompt_template.replace('<<PRODUCT_DATA>>', product_data_escaped)

    def _clean_product_data(self, product_data: Dict) -> Dict:
        """
        Clean product data - simplify competitor prices for chatbot context

        Args:
            product_data: Raw product data from Redis

        Returns:
            Cleaned product data optimized for chatbot use
        """
        import copy
        cleaned = copy.deepcopy(product_data)

        # Simplify competitor_prices - remove Google redirect URLs but keep price info
        if 'competitor_prices' in cleaned:
            simplified_competitors = []
            for competitor in cleaned['competitor_prices']:
                simplified = {
                    'site': competitor.get('site', 'Unknown'),
                    'price': competitor.get('price', 'N/A'),
                    'availability': competitor.get('availability', 'Unknown')
                }
                # Only add URL if it's a direct product URL (not Google Shopping search)
                url = competitor.get('url', '')
                if url and not url.startswith('https://www.google.com/search'):
                    simplified['url'] = url

                simplified_competitors.append(simplified)

            cleaned['competitor_prices'] = simplified_competitors

        # Simplify price_comparison to just essential summary data
        if 'price_comparison' in cleaned:
            price_comp = cleaned['price_comparison']
            # Keep only the summary, remove raw search results
            if isinstance(price_comp, dict):
                cleaned['price_comparison_summary'] = {
                    'total_results': price_comp.get('total_results', 0),
                    'lowest_price': price_comp.get('lowest_price'),
                    'highest_price': price_comp.get('highest_price'),
                    'current_price': price_comp.get('current_price'),
                }
            # Remove the full price_comparison object to reduce context size
            del cleaned['price_comparison']

        # Add Amazon URL for easy reference
        if 'asin' in cleaned:
            cleaned['amazon_url'] = f"https://www.amazon.in/dp/{cleaned['asin']}"

        return cleaned

    def get_product_data(self, product_id: str) -> Optional[Dict]:
        key = f"product:{product_id}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

