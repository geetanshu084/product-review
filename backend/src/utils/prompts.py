"""
Centralized Prompt Management
All LLM prompts are loaded from text files for easy modification and maintenance
"""

from pathlib import Path
from typing import Dict


class PromptLoader:
    """Loads and caches prompts from text files"""

    _cache: Dict[str, str] = {}
    _prompts_dir = Path(__file__).parent.parent.parent / "config" / "prompts"

    @classmethod
    def load_prompt(cls, filename: str) -> str:
        """
        Load a prompt from a text file

        Args:
            filename: Name of the prompt file (without path)

        Returns:
            Prompt content as string

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Check cache first
        if filename in cls._cache:
            return cls._cache[filename]

        # Load from file
        prompt_path = cls._prompts_dir / filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Please ensure {filename} exists in config/prompts/"
            )

        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Cache it
        cls._cache[filename] = content

        return content


class Prompts:
    """Centralized storage for all LLM prompts"""

    # ============================================================================
    # LLM PRODUCT EXTRACTION PROMPTS
    # ============================================================================

    @staticmethod
    def get_product_extraction_prompt(page_text: str, url: str) -> str:
        """
        Prompt for extracting product data from Amazon page HTML

        Args:
            page_text: Clean text from product page
            url: Product URL

        Returns:
            Formatted prompt string
        """
        template = PromptLoader.load_prompt("product_extraction_prompt.txt")
        return template.format(page_text=page_text, url=url)

    # ============================================================================
    # PRODUCT ORCHESTRATOR PROMPTS
    # ============================================================================

    @staticmethod
    def get_product_analysis_prompt() -> str:
        """Prompt template for product analysis in ProductOrchestrator"""
        return PromptLoader.load_prompt("product_analysis_prompt.txt")

    # ============================================================================
    # WEB SEARCH CONTENT FILTERING PROMPTS
    # ============================================================================

    @staticmethod
    def get_review_filter_prompt(context: str, product_name: str) -> str:
        """Prompt for filtering irrelevant reviews"""
        template = PromptLoader.load_prompt("review_filter_prompt.txt")
        return template.format(context=context, product_name=product_name)

    @staticmethod
    def get_reddit_filter_prompt(context: str, product_name: str) -> str:
        """Prompt for filtering irrelevant Reddit discussions"""
        template = PromptLoader.load_prompt("reddit_filter_prompt.txt")
        return template.format(context=context, product_name=product_name)

    @staticmethod
    def get_news_filter_prompt(context: str, product_name: str) -> str:
        """Prompt for filtering irrelevant news articles"""
        template = PromptLoader.load_prompt("news_filter_prompt.txt")
        return template.format(context=context, product_name=product_name)

    @staticmethod
    def get_comparison_filter_prompt(context: str, product_name: str) -> str:
        """Prompt for filtering irrelevant comparison articles"""
        template = PromptLoader.load_prompt("comparison_filter_prompt.txt")
        return template.format(context=context, product_name=product_name)

    # ============================================================================
    # WEB SEARCH ANALYSIS PROMPTS
    # ============================================================================

    @staticmethod
    def get_key_findings_prompt(context: str, product_name: str) -> str:
        """Prompt for extracting key findings from search results"""
        template = PromptLoader.load_prompt("key_findings_prompt.txt")
        return template.format(context=context, product_name=product_name)

    @staticmethod
    def get_red_flags_prompt(context: str, product_name: str) -> str:
        """Prompt for detecting red flags in search results"""
        template = PromptLoader.load_prompt("red_flags_prompt.txt")
        return template.format(context=context, product_name=product_name)

    @staticmethod
    def get_sentiment_analysis_prompt(context: str, product_name: str) -> str:
        """Prompt for analyzing sentiment from search results"""
        template = PromptLoader.load_prompt("sentiment_analysis_prompt.txt")
        return template.format(context=context, product_name=product_name)

    # ============================================================================
    # ANALYZER PROMPTS
    # ============================================================================

    @staticmethod
    def get_product_analyzer_prompt() -> str:
        """Prompt for general product analysis"""
        return PromptLoader.load_prompt("product_analysis_prompt.txt")


# Convenience functions for backward compatibility
def get_product_extraction_prompt(page_text: str, url: str) -> str:
    """Get product extraction prompt"""
    return Prompts.get_product_extraction_prompt(page_text, url)


def get_product_analysis_prompt() -> str:
    """Get product analysis prompt"""
    return Prompts.get_product_analysis_prompt()


def get_review_filter_prompt(context: str, product_name: str) -> str:
    """Get review filter prompt"""
    return Prompts.get_review_filter_prompt(context, product_name)


def get_reddit_filter_prompt(context: str, product_name: str) -> str:
    """Get Reddit filter prompt"""
    return Prompts.get_reddit_filter_prompt(context, product_name)


def get_news_filter_prompt(context: str, product_name: str) -> str:
    """Get news filter prompt"""
    return Prompts.get_news_filter_prompt(context, product_name)


def get_comparison_filter_prompt(context: str, product_name: str) -> str:
    """Get comparison filter prompt"""
    return Prompts.get_comparison_filter_prompt(context, product_name)


def get_key_findings_prompt(context: str, product_name: str) -> str:
    """Get key findings prompt"""
    return Prompts.get_key_findings_prompt(context, product_name)


def get_red_flags_prompt(context: str, product_name: str) -> str:
    """Get red flags detection prompt"""
    return Prompts.get_red_flags_prompt(context, product_name)


def get_sentiment_analysis_prompt(context: str, product_name: str) -> str:
    """Get sentiment analysis prompt"""
    return Prompts.get_sentiment_analysis_prompt(context, product_name)
