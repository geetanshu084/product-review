"""
Conversational Q&A System Module
Uses LangChain's standard Redis chat message history for persistent memory
Includes web search capability via LangChain tools
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path
import redis

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

class ProductChatbot:

    def __init__(self):

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv('MODEL_NAME', 'gemini-2.5-flash'),
            temperature=0.5,
            convert_system_message_to_human=True
        )

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

        self.tools = []

        search = GoogleSerperAPIWrapper(serper_api_key=os.getenv('SERPER_API_KEY'))
        search_tool = Tool(
            name="Search",
            description="Useful for searching the internet for current information about products, prices, availability, comparisons, or any up-to-date information. Input should be a search query string.",
            func=search.run
        )
        self.tools = [search_tool]


        # Load system prompt template from config file
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

        # Convert product data to JSON string for LLM context
        product_data_json = json.dumps(product_data, indent=2, ensure_ascii=False)

        # Generate answer using modern LangChain agent
        try:
            # Create session-specific memory with RedisChatMessageHistory
            # memory = ConversationBufferMemory(
            #     chat_memory=RedisChatMessageHistory(
            #         session_id=session_id,
            #         url=self.redis_url,
            #         key_prefix="chat_history:"
            #     ),
            #     memory_key="chat_history",
            #     return_messages=False,  # Return as string for ReAct agent
            #     output_key="output"
            # )
            memory = RedisChatMessageHistory(
                session_id=session_id,
                url=self.redis_url,
                key_prefix="chat_history:"
            )
            # Insert product data JSON into system prompt
            # Escape JSON curly braces for PromptTemplate by doubling them: { becomes {{
            product_data_escaped = product_data_json.replace('{', '{{').replace('}', '}}')

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt_template.replace('<<PRODUCT_DATA>>', product_data_escaped)),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            # agent_executor = AgentExecutor(agent, self.tools, memory=memory)
            #
            # Create agent executor with memory
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
            raise Exception(f"Failed to generate answer: {str(e)}")

    def get_product_data(self, product_id: str) -> Optional[Dict]:
        """
        Get product data from Redis (set by scraper after scraping)

        Args:
            product_id: Product identifier (ASIN from scraper)

        Returns:
            Product data dictionary or None
        """
        # Use same key format as scraper: "product:{asin}"
        key = f"product:{product_id}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

