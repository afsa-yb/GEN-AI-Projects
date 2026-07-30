"""
Text Cleaner Module for ResearchGPT.
Sanitizes raw document text before splitting and embedding.
"""

import re
from typing import List
from langchain_core.documents import Document
from src.logger import logger


class TextCleaner:
    """Cleans and sanitizes document content to improve embedding quality."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Sanitizes a string by removing excessive whitespace, null bytes,
        and non-printable characters.
        """
        if not text:
            return ""

        # Remove null bytes and non-printable control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Replace multiple newlines with at most two newlines (preserving paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace multiple spaces/tabs with a single space
        text = re.sub(r"[ \t]+", " ", text)

        # Strip leading and trailing whitespace
        return text.strip()

    @classmethod
    def clean_documents(cls, documents: List[Document]) -> List[Document]:
        """
        Iterates through a list of LangChain Document objects and cleans their text.
        """
        logger.info(f"Cleaning text across {len(documents)} document chunk(s)...")
        cleaned_docs = []
        for doc in documents:
            cleaned_content = cls.clean_text(doc.page_content)
            if cleaned_content:  # Retain only non-empty documents
                doc.page_content = cleaned_content
                cleaned_docs.append(doc)

        logger.info(f"Text cleaning complete. {len(cleaned_docs)} active chunk(s) remaining.")
        return cleaned_docs