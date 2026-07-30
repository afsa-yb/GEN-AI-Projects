"""
Web Search Manager for ResearchGPT using Tavily API.
Handles real-time web search integration safely with fallback error handling.
"""

import os
import sys
from typing import List, Dict, Any

# Fix for module placement in langchain_community
try:
    from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
except ImportError:
    from langchain_community.utilities import TavilySearchAPIWrapper

# Ensure root folder (where config.py lives) is in Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from config import settings
except ImportError:
    settings = None

from src.logger import logger


class WebSearchManager:
    """Manages real-time web search integration using Tavily."""

    def __init__(self, max_results: int = 3):
        self.max_results = max_results
        self.search_wrapper = None

        # 1. Safely extract API key from config or system environment
        api_key = self._get_tavily_api_key()

        # 2. Inject into os.environ & initialize wrapper
        if api_key:
            os.environ["TAVILY_API_KEY"] = api_key
            try:
                self.search_wrapper = TavilySearchAPIWrapper(tavily_api_key=api_key)
                logger.info("Tavily Web Search initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily search wrapper: {str(e)}")
        else:
            logger.warning(
                "TAVILY_API_KEY is not configured or is empty. Web search will be disabled."
            )

    def _get_tavily_api_key(self) -> str:
        """Helper method to safely extract the string value of the API key."""
        if settings and hasattr(settings, "TAVILY_API_KEY"):
            raw_key = settings.TAVILY_API_KEY
            if hasattr(raw_key, "get_secret_value"):
                key = raw_key.get_secret_value()
            else:
                key = str(raw_key) if raw_key else ""
            
            if key and key.strip():
                return key.strip()

        return os.getenv("TAVILY_API_KEY", "").strip()

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Executes a web search query using Tavily API."""
        if not self.search_wrapper:
            logger.warning("Tavily search skipped: API key is not configured.")
            return []

        try:
            logger.info(f"Executing web search for: '{query}'")
            results = self.search_wrapper.results(
                query=query, 
                max_results=self.max_results
            )
            return results
        except Exception as e:
            logger.error(f"Error during Tavily web search execution: {str(e)}")
            return []