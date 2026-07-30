"""
LLM Factory Module for ResearchGPT.
Initializes high-speed Groq inference using Llama 3.1 / 3.3 Pro series models.
"""

from typing import Optional
from langchain_groq import ChatGroq
from config import settings
from src.logger import logger


class LLMFactory:
    """Factory class to manage and initialize Groq LLM instances."""

    @staticmethod
    def get_llm(
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        streaming: bool = True
    ) -> ChatGroq:
        """
        Creates and returns a configured ChatGroq instance.

        Args:
            model_name: Override model name (defaults to config settings).
            temperature: Sampling temperature for deterministic vs creative output.
            streaming: Whether to enable token streaming.

        Returns:
            Configured ChatGroq instance.
        """
        selected_model = model_name or settings.LLM_MODEL_NAME
        if hasattr(settings.GROQ_API_KEY, "get_secret_value"):
           api_key = settings.GROQ_API_KEY.get_secret_value()
        else:
           api_key = settings.GROQ_API_KEY

        if not api_key:
            logger.error("GROQ_API_KEY is missing from environment/config.")
            raise ValueError("GROQ_API_KEY must be provided in the .env file.")

        logger.info(f"Initializing Groq LLM: {selected_model} (Temp: {temperature}, Streaming: {streaming})")

        try:
            llm = ChatGroq(
                model=selected_model,
                groq_api_key=api_key,
                temperature=temperature,
                streaming=streaming,
                max_retries=3,
            )
            logger.info("Groq LLM initialized successfully.")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize ChatGroq model '{selected_model}': {str(e)}")
            raise e