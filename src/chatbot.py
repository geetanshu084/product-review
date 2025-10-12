"""
Conversational Q&A System Module
Uses LangChain's standard Redis chat message history for persistent memory
Includes web search capability via LangChain tools
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
import redis
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.tools import Tool


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

        # Simple Redis client for product data storage (not messages)
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
        # LangChain's initialize_agent handles ReAct format, tools, scratchpad automatically
        prompt_path = Path(__file__).parent.parent / "config" / "prompts" / "agent_prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.agent_prefix_template = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Agent prompt file not found at {prompt_path}. "
                "Please ensure config/prompts/agent_prompt.txt exists."
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

        # Generate answer using LangChain's initialize_agent
        # This handles ReAct format, tools, and scratchpad automatically
        try:
            # Create session-specific memory with RedisChatMessageHistory
            # LangChain manages the conversation history automatically
            memory = ConversationBufferMemory(
                chat_memory=RedisChatMessageHistory(
                    session_id=session_id,
                    url=self.redis_url,
                    key_prefix="chat_history:"
                ),
                memory_key="chat_history",
                return_messages=True
            )

            # Insert product data JSON into agent prefix using string replacement
            # Escape JSON curly braces for PromptTemplate by doubling them: { becomes {{
            product_data_escaped = product_data_json.replace('{', '{{').replace('}', '}}')
            agent_prefix_formatted = self.agent_prefix_template.replace('<<PRODUCT_DATA>>', product_data_escaped)

            # Custom parsing error handler
            def handle_parsing_error(error) -> str:
                """Handle parsing errors by returning the LLM output as-is"""
                response = str(error).split("Could not parse LLM output: `")[-1].rsplit("`", 1)[0]
                # If the response looks like it has content after "Thought:", extract it
                if "Thought:" in response and "Final Answer:" not in response:
                    # LLM likely gave a direct answer after Thought without proper format
                    # Extract everything after "Thought:" as the answer
                    parts = response.split("Thought:", 1)
                    if len(parts) > 1:
                        return parts[1].strip()
                return response

            agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                memory=memory,
                verbose=True,
                handle_parsing_errors=handle_parsing_error,
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
        key = f"product_data:{session_id}"
        self.redis_client.set(key, json.dumps(product_data))

    def get_product_data(self, session_id: str) -> Optional[Dict]:
        key = f"product_data:{session_id}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session (for UI display)

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries (for compatibility)
        """
        message_history = RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_url,
            key_prefix="chat_history:"
        )
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
        RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_url,
            key_prefix="chat_history:"
        ).clear()

    def clear_all_data(self, session_id: str):
        """
        Clear all data (conversation and product) for a session

        Args:
            session_id: Unique session identifier
        """
        # Clear conversation history
        RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_url,
            key_prefix="chat_history:"
        ).clear()

        # Clear product data
        key = f"product_data:{session_id}"
        self.redis_client.delete(key)
