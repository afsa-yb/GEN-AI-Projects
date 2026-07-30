"""
Vector Store Manager for ResearchGPT using FAISS.
Handles vector store creation, saving, and safe loading.
"""

import os
import sys
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

# Ensure root directory is in Python path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from src.embeddings import EmbeddingsFactory
from src.logger import logger


class VectorStoreManager:
    """Manages FAISS vector database initialization, queries, and disk persistence."""

    def __init__(self):
        self.embedding_model = EmbeddingsFactory.get_embedding_model()
        self.index_path = getattr(settings, "FAISS_INDEX_PATH", "vectorstore")
        self.vector_store: Optional[FAISS] = self.load_vector_store()

    def create_vector_store(self, documents: List[Document], output_path: Optional[str] = None) -> Optional[FAISS]:
        """Creates a FAISS vector store from document chunks and saves to disk."""
        if not documents:
            logger.warning("No documents provided to create vector store.")
            return None

        try:
            logger.info(f"Creating FAISS vector store with {len(documents)} document chunks...")
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embedding_model
            )
            save_path = output_path if output_path else self.index_path
            self.save_vector_store(save_path)
            return self.vector_store
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise e

    def save_vector_store(self, folder_path: Optional[str] = None) -> None:
        """
        Saves current FAISS index to disk.
        Accepts optional folder_path to remain compatible with positional argument calls.
        """
        target_path = folder_path if folder_path else self.index_path
        if self.vector_store:
            try:
                os.makedirs(target_path, exist_ok=True)
                self.vector_store.save_local(target_path)
                logger.info(f"FAISS vector store saved successfully to '{target_path}'.")
            except Exception as e:
                logger.error(f"Failed to save FAISS vector store: {str(e)}")

    def load_vector_store(self, folder_path: Optional[str] = None) -> Optional[FAISS]:
        """
        Safely loads FAISS vector store from disk.
        Returns None gracefully if no index file exists yet.
        """
        target_path = folder_path if folder_path else self.index_path
        faiss_file = os.path.join(target_path, "index.faiss")
        
        if os.path.exists(target_path) and os.path.exists(faiss_file):
            try:
                logger.info(f"Loading existing FAISS index from '{target_path}'...")
                self.vector_store = FAISS.load_local(
                    folder_path=target_path,
                    embeddings=self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                logger.info("FAISS vector store loaded successfully.")
                return self.vector_store
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {str(e)}")
                return None
        else:
            logger.info(f"No existing vector store index found at '{target_path}'. Ready for document uploads.")
            return None

    def similarity_search(self, query: str, top_k: int = 4, **kwargs) -> List[Document]:
        """Performs similarity search against FAISS index."""
        if not self.vector_store:
            self.vector_store = self.load_vector_store()

        if not self.vector_store:
            logger.info("Similarity search skipped: Vector store is empty/uninitialized.")
            return []

        try:
            logger.info(f"Executing vector search for query: '{query}'")
            return self.vector_store.similarity_search(query, k=top_k, **kwargs)
        except Exception as e:
            logger.error(f"Error during vector similarity search: {str(e)}")
            return []