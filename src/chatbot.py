"""
Conversational Q&A System Module
Maintains conversation context using Redis for persistent memory
"""

import json
import os
from typing import Dict, List, Optional
import redis
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain


class RedisChatMemory:
    """Redis-backed conversation memory"""

    def __init__(self, redis_host: str, redis_port: int, redis_db: int, redis_password: Optional[str] = None):
        """
        Initialize Redis connection for conversation memory

        Args:
            redis_host: Redis host address
            redis_port: Redis port number
            redis_db: Redis database number
            redis_password: Redis password (optional)
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )

    def save_message(self, session_id: str, role: str, content: str):
        """
        Save a message to Redis

        Args:
            session_id: Unique session identifier
            role: Message role (user/assistant)
            content: Message content
        """
        key = f"chat:{session_id}:messages"
        message = json.dumps({
            'role': role,
            'content': content
        })
        self.redis_client.rpush(key, message)

    def get_messages(self, session_id: str) -> List[Dict]:
        """
        Retrieve all messages for a session

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries
        """
        key = f"chat:{session_id}:messages"
        messages = self.redis_client.lrange(key, 0, -1)
        return [json.loads(msg) for msg in messages]

    def clear_messages(self, session_id: str):
        """
        Clear all messages for a session

        Args:
            session_id: Unique session identifier
        """
        key = f"chat:{session_id}:messages"
        self.redis_client.delete(key)

    def save_product_data(self, session_id: str, product_data: Dict):
        """
        Save product data to Redis for this session

        Args:
            session_id: Unique session identifier
            product_data: Product data dictionary
        """
        key = f"chat:{session_id}:product_data"
        self.redis_client.set(key, json.dumps(product_data))

    def get_product_data(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve product data for a session

        Args:
            session_id: Unique session identifier

        Returns:
            Product data dictionary or None
        """
        key = f"chat:{session_id}:product_data"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None


class ProductChatbot:
    """Conversational Q&A system for product inquiries"""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
        google_api_key: Optional[str] = None
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
        """
        # Check for API key first (recommended approach)
        api_key = google_api_key or os.getenv('GOOGLE_API_KEY')

        if not api_key:
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
            google_api_key=api_key
        )

        # Initialize Redis memory
        self.redis_memory = RedisChatMemory(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db,
            redis_password=redis_password
        )

        # Create prompt template for Q&A
        self.qa_template = """You are a helpful product analysis assistant. You answer questions about products based on the product data provided.

PRODUCT DATA:
{product_context}

CONVERSATION HISTORY:
{history}

USER QUESTION: {input}

Guidelines:
1. Answer based ONLY on the product data provided above
2. If the information is not available in the product data, clearly state "I don't have that information in the product data"
3. Be specific and quote from reviews when relevant
4. Keep answers concise but informative
5. Maintain a helpful and professional tone

YOUR ANSWER:"""

        self.prompt = PromptTemplate(
            input_variables=["product_context", "history", "input"],
            template=self.qa_template
        )

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

        return "\n".join(context)

    def format_history(self, messages: List[Dict]) -> str:
        """
        Format conversation history

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted history string
        """
        if not messages:
            return "No previous conversation"

        history = []
        for msg in messages[-6:]:  # Last 6 messages (3 exchanges)
            role = "User" if msg['role'] == 'user' else "Assistant"
            history.append(f"{role}: {msg['content']}")

        return "\n".join(history)

    def ask(self, session_id: str, question: str) -> str:
        """
        Ask a question about the product

        Args:
            session_id: Unique session identifier
            question: User's question

        Returns:
            Answer string

        Raises:
            ValueError: If no product data is available
        """
        # Get product data from Redis
        product_data = self.redis_memory.get_product_data(session_id)
        if not product_data:
            raise ValueError("Please analyze a product first before asking questions.")

        # Get conversation history
        messages = self.redis_memory.get_messages(session_id)

        # Format context and history
        product_context = self.format_product_context(product_data)
        history = self.format_history(messages)

        # Generate answer
        try:
            full_prompt = self.prompt.format(
                product_context=product_context,
                history=history,
                input=question
            )

            response = self.llm.invoke(full_prompt)
            answer = response.content.strip()

            # Save to Redis
            self.redis_memory.save_message(session_id, 'user', question)
            self.redis_memory.save_message(session_id, 'assistant', answer)

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
        self.redis_memory.save_product_data(session_id, product_data)

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries
        """
        return self.redis_memory.get_messages(session_id)

    def clear_conversation(self, session_id: str):
        """
        Clear conversation history for a session

        Args:
            session_id: Unique session identifier
        """
        self.redis_memory.clear_messages(session_id)

    def clear_all_data(self, session_id: str):
        """
        Clear all data (conversation and product) for a session

        Args:
            session_id: Unique session identifier
        """
        self.redis_memory.clear_messages(session_id)
        key = f"chat:{session_id}:product_data"
        self.redis_memory.redis_client.delete(key)
