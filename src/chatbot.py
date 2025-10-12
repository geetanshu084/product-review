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
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate


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
        prompt_path = Path(__file__).parent.parent / "config" / "prompts" / "agent_prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt_template = f.read()
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

        # Generate answer using modern LangChain agent
        try:
            # Create session-specific memory with RedisChatMessageHistory
            memory = ConversationBufferMemory(
                chat_memory=RedisChatMessageHistory(
                    session_id=session_id,
                    url=self.redis_url,
                    key_prefix="chat_history:"
                ),
                memory_key="chat_history",
                return_messages=False,  # Return as string for ReAct agent
                output_key="output"
            )

            # Insert product data JSON into system prompt
            # Escape JSON curly braces for PromptTemplate by doubling them: { becomes {{
            product_data_escaped = product_data_json.replace('{', '{{').replace('}', '}}')
            prompt_with_product = PromptTemplate.from_template(
                self.system_prompt_template.replace('<<PRODUCT_DATA>>', product_data_escaped) + """

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Chat History:
{chat_history}

Question: {input}
Thought:{agent_scratchpad}"""
            )

            # Create the modern ReAct agent
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt_with_product
            )

            # Create agent executor with memory
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                return_intermediate_steps=False
            )

            # Invoke agent
            result = agent_executor.invoke({"input": question})
            answer = result.get('output', '').strip()

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
