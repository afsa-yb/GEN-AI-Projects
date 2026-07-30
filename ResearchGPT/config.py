"""
Centralized Configuration Module for ResearchGPT.
Handles path definitions, system hyperparameters, model settings, and security credentials.
"""

import os
from pathlib import Path
from typing import Union
from pydantic import Field, ConfigDict, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """System-wide configuration settings validated via Pydantic."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys (Supports both SecretStr and plain str gracefully)
    GROQ_API_KEY: Union[SecretStr, str] = Field(default="", description="Groq API Key")
    TAVILY_API_KEY: Union[SecretStr, str] = Field(default="", description="Tavily Search API Key")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Execution environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging verbosity level")

    # Project Directories
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    VECTORSTORE_DIR: Path = BASE_DIR / "vectorstore"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # FAISS Specific Path (Added for vector store module compatibility)
    FAISS_INDEX_PATH: str = Field(default="vectorstore", description="Path to FAISS index directory")

    # Document Chunking
    CHUNK_SIZE: int = Field(default=1000, description="Chunk length in characters")
    CHUNK_OVERLAP: int = Field(default=200, description="Overlap between consecutive chunks")

    # Embedding & Retrieval (100% Free Local Embeddings)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    FIRST_STAGE_TOP_K: int = 10  # Initial dense retrieval top-K
    RERANKED_TOP_K: int = 3     # Post cross-encoder top-K sent to LLM

    # Re-ranker Model
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-large"

    # LLM Settings (Free Groq Llama Model)
    LLM_MODEL_NAME: str = "llama-3.3-70b-versatile"
    DEFAULT_TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 2048

    # Web Search Fallback Threshold
    SIMILARITY_CONFIDENCE_THRESHOLD: float = 0.35

    def create_directories(self) -> None:
        """Ensure all required project directories exist on system startup."""
        for path in [self.DATA_DIR, self.UPLOADS_DIR, self.VECTORSTORE_DIR, self.LOGS_DIR]:
            path.mkdir(parents=True, exist_ok=True)


# Instantiate settings and ensure paths exist
settings = Settings()
settings.create_directories()