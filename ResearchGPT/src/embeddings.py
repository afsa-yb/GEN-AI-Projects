"""
Embeddings Module for ResearchGPT.
Handles generation and loading of local text embeddings via HuggingFace models.
"""

import os
import sys

# Defensive import handling for LangChain updates
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# Ensure project root is in Python path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from src.logger import logger


class EmbeddingsFactory:
    """Factory for initializing and serving local embedding models."""

    @classmethod
    def get_embedding_model(cls):
        """
        Instantiates and returns the HuggingFace Embeddings model.
        Uses EMBEDDING_MODEL_NAME specified in config.py.
        """
        model_name = getattr(settings, "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

        try:
            logger.info(f"Loading local embedding model: '{model_name}'...")
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info("Embedding model initialized successfully.")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to initialize embedding model '{model_name}': {str(e)}")
            raise e