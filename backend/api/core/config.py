"""
FastAPI configuration settings
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Product Analysis API"
    VERSION: str = "1.0.0"

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5000",  # React dev server
        "http://localhost:5001",  # Alternative port
        "http://localhost:5002",  # Alternative port
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5001",
        "http://127.0.0.1:5002",
        "http://127.0.0.1:3000",
    ]

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    # API Keys for different LLM providers
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Other API Keys
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")

    # Search Provider Configuration
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "duckduckgo")

    def has_llm_configured(self) -> bool:
        """Check if any LLM provider is configured with an API key"""
        provider_keys = {
            "google": self.GOOGLE_API_KEY,
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "groq": self.GROQ_API_KEY,
            "cohere": self.COHERE_API_KEY,
            "ollama": True,  # Ollama doesn't need an API key, just a base URL
        }

        # Check if the configured provider has a key (or is Ollama)
        current_provider = self.LLM_PROVIDER.lower()
        if current_provider in provider_keys:
            key_or_available = provider_keys[current_provider]
            return bool(key_or_available)

        # Fallback: Check if ANY provider has a key
        return any(bool(key) for provider, key in provider_keys.items() if provider != "ollama") or current_provider == "ollama"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
