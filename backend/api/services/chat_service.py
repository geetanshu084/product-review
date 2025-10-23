"""
Chat service - wraps chatbot
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.chatbot import ProductChatbot


class ChatService:
    """Service for chat/Q&A functionality"""

    def __init__(self):
        """Initialize chatbot lazily"""
        self._chatbot = None

    @property
    def chatbot(self):
        """Lazy initialization of chatbot"""
        if self._chatbot is None:
            try:
                self._chatbot = ProductChatbot()
            except Exception as e:
                print(f"Error initializing chatbot: {str(e)}")
                import traceback
                traceback.print_exc()
                raise ValueError(f"Chatbot initialization failed: {str(e)}")
        return self._chatbot

    def ask_question(self, session_id: str, product_id: str, question: str) -> str:
        """
        Ask a question about a product

        Args:
            session_id: User session ID
            product_id: Product ASIN
            question: User's question

        Returns:
            Answer string

        Raises:
            ValueError: If chatbot not available
            Exception: If query fails
        """
        answer = self.chatbot.ask(session_id, product_id, question)
        return answer

    def get_chat_history(self, session_id: str) -> list:
        """
        Get chat history for a session

        Args:
            session_id: User session ID

        Returns:
            List of message dictionaries

        Note:
            Chat history is managed by LangChain's RedisChatMessageHistory
        """
        # Chat history is managed internally by LangChain
        # Frontend maintains display history
        return []


# Singleton instance
chat_service = ChatService()
