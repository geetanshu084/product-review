"""
LLM Provider Factory
Supports multiple LLM providers configured via environment variables
"""

import os
from typing import Optional, Dict, Any
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    GOOGLE = "google"  # Google Gemini
    OPENAI = "openai"  # OpenAI GPT
    ANTHROPIC = "anthropic"  # Anthropic Claude
    OLLAMA = "ollama"  # Ollama (local models)
    GROQ = "groq"  # Groq
    COHERE = "cohere"  # Cohere


class LLMFactory:
    """
    Factory class to create LLM instances based on configuration

    Environment Variables:
        LLM_PROVIDER: Provider to use (google, openai, anthropic, ollama, groq, cohere)
        LLM_MODEL: Model name (e.g., gemini-2.0-flash-exp, gpt-4, claude-3-sonnet)

        Provider-specific API keys:
        - GOOGLE_API_KEY: For Google Gemini
        - OPENAI_API_KEY: For OpenAI
        - ANTHROPIC_API_KEY: For Anthropic Claude
        - GROQ_API_KEY: For Groq
        - COHERE_API_KEY: For Cohere
        - OLLAMA_BASE_URL: For Ollama (default: http://localhost:11434)
    """

    @staticmethod
    def get_llm(
        temperature: float = 0.3,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Get LLM instance based on configuration

        Args:
            temperature: Temperature for generation (0.0 - 1.0)
            provider: Override provider from env (google, openai, anthropic, etc.)
            model: Override model from env
            **kwargs: Additional provider-specific arguments

        Returns:
            LangChain LLM instance

        Raises:
            ValueError: If provider not configured or unsupported
        """
        # Get provider from args or env
        provider = provider or os.getenv('LLM_PROVIDER', 'google').lower()

        # Validate provider
        try:
            provider_enum = LLMProvider(provider)
        except ValueError:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported: {', '.join([p.value for p in LLMProvider])}"
            )

        # Route to appropriate provider
        if provider_enum == LLMProvider.GOOGLE:
            return LLMFactory._get_google_llm(temperature, model, **kwargs)
        elif provider_enum == LLMProvider.OPENAI:
            return LLMFactory._get_openai_llm(temperature, model, **kwargs)
        elif provider_enum == LLMProvider.ANTHROPIC:
            return LLMFactory._get_anthropic_llm(temperature, model, **kwargs)
        elif provider_enum == LLMProvider.OLLAMA:
            return LLMFactory._get_ollama_llm(temperature, model, **kwargs)
        elif provider_enum == LLMProvider.GROQ:
            return LLMFactory._get_groq_llm(temperature, model, **kwargs)
        elif provider_enum == LLMProvider.COHERE:
            return LLMFactory._get_cohere_llm(temperature, model, **kwargs)
        else:
            raise ValueError(f"Provider {provider} not implemented")

    @staticmethod
    def _get_google_llm(temperature: float, model: Optional[str] = None, **kwargs):
        """Get Google Gemini LLM"""
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        model_name = model or os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key,
            convert_system_message_to_human=True,
            **kwargs
        )

    @staticmethod
    def _get_openai_llm(temperature: float, model: Optional[str] = None, **kwargs):
        """Get OpenAI GPT LLM"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "OpenAI support requires: pip install langchain-openai"
            )

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        model_name = model or os.getenv('LLM_MODEL', 'gpt-4o-mini')

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key,
            **kwargs
        )

    @staticmethod
    def _get_anthropic_llm(temperature: float, model: Optional[str] = None, **kwargs):
        """Get Anthropic Claude LLM"""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "Anthropic support requires: pip install langchain-anthropic"
            )

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        model_name = model or os.getenv('LLM_MODEL', 'claude-3-5-sonnet-20241022')

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=api_key,
            **kwargs
        )

    @staticmethod
    def _get_ollama_llm(temperature: float, model: Optional[str] = None, **kwargs):
        """Get Ollama LLM (local models)"""
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "Ollama support requires: pip install langchain-ollama"
            )

        model_name = model or os.getenv('LLM_MODEL', 'llama3.1')
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

        return ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=base_url,
            **kwargs
        )

    @staticmethod
    def _get_groq_llm(temperature: float, model: Optional[str] = None, **kwargs):
        """Get Groq LLM"""
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ImportError(
                "Groq support requires: pip install langchain-groq"
            )

        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        model_name = model or os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile')

        return ChatGroq(
            model=model_name,
            temperature=temperature,
            groq_api_key=api_key,
            **kwargs
        )

    @staticmethod
    def _get_cohere_llm(temperature: float, model: Optional[str] = None, **kwargs):
        """Get Cohere LLM"""
        try:
            from langchain_cohere import ChatCohere
        except ImportError:
            raise ImportError(
                "Cohere support requires: pip install langchain-cohere"
            )

        api_key = os.getenv('COHERE_API_KEY')
        if not api_key:
            raise ValueError("COHERE_API_KEY not found in environment")

        model_name = model or os.getenv('LLM_MODEL', 'command-r-plus')

        return ChatCohere(
            model=model_name,
            temperature=temperature,
            cohere_api_key=api_key,
            **kwargs
        )

    @staticmethod
    def get_provider_info() -> Dict[str, Any]:
        """
        Get information about current LLM configuration

        Returns:
            Dictionary with provider, model, and availability info
        """
        provider = os.getenv('LLM_PROVIDER', 'google').lower()
        model = os.getenv('LLM_MODEL', 'auto')

        # Check if API key is configured
        api_key_map = {
            'google': 'GOOGLE_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'groq': 'GROQ_API_KEY',
            'cohere': 'COHERE_API_KEY',
            'ollama': None  # No API key needed for Ollama
        }

        api_key_var = api_key_map.get(provider)
        has_api_key = (
            api_key_var is None or  # Ollama
            bool(os.getenv(api_key_var))
        )

        return {
            'provider': provider,
            'model': model,
            'configured': has_api_key,
            'api_key_var': api_key_var
        }


# Convenience function
def get_llm(temperature: float = 0.3, **kwargs):
    """
    Convenience function to get LLM instance

    Args:
        temperature: Temperature for generation (0.0 - 1.0)
        **kwargs: Additional arguments passed to LLMFactory.get_llm()

    Returns:
        LangChain LLM instance
    """
    return LLMFactory.get_llm(temperature=temperature, **kwargs)
