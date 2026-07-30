"""
Document Splitter Module for ResearchGPT.
Splits cleaned documents into overlapping semantic chunks and enriches metadata.
"""

from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings
from src.logger import logger


class DocumentSplitter:
    """Splits documents into fixed-size chunks with context overlap."""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of documents into smaller chunks and assigns unique metadata IDs.

        Args:
            documents: List of cleaned LangChain Document objects.

        Returns:
            List of chunked Document objects with enriched metadata.
        """
        logger.info(
            f"Splitting {len(documents)} document(s) with chunk_size={self.chunk_size} "
            f"and chunk_overlap={self.chunk_overlap}..."
        )

        chunked_docs = self.splitter.split_documents(documents)

        # Attach tracking metadata to each chunk
        for index, doc in enumerate(chunked_docs):
            source_file = doc.metadata.get("source", "unknown")
            page_num = doc.metadata.get("page", 1)

            # Enrich metadata
            doc.metadata["chunk_id"] = f"{source_file}_page_{page_num}_chunk_{index}"
            doc.metadata["filename"] = str(source_file).split("/")[-1]
            doc.metadata["page_number"] = page_num

        logger.info(f"Successfully generated {len(chunked_docs)} chunks.")
        return chunked_docs