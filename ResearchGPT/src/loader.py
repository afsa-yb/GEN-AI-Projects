"""
Document Loader Module for ResearchGPT.
Handles file reading and parsing across PDF, DOCX, and TXT formats.
"""

from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from src.logger import logger


class DocumentLoader:
    """Loads PDF, DOCX, and TXT documents into standard LangChain Document objects."""

    @staticmethod
    def load_file(file_path: str) -> List[Document]:
        """
        Loads a single document based on its file extension.
        
        Args:
            file_path: Absolute or relative path to the file.
            
        Returns:
            List of LangChain Document objects containing page content and metadata.
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File at {file_path} does not exist.")

        file_extension = path.suffix.lower()
        logger.info(f"Loading document: {path.name} (type: {file_extension})")

        try:
            if file_extension == ".pdf":
                loader = PyPDFLoader(str(path))
            elif file_extension == ".docx":
                loader = Docx2txtLoader(str(path))
            elif file_extension == ".txt":
                loader = TextLoader(str(path), encoding="utf-8")
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            documents = loader.load()
            logger.info(f"Successfully loaded {len(documents)} page(s)/section(s) from {path.name}")
            return documents

        except Exception as e:
            logger.error(f"Failed to load document {path.name}: {str(e)}")
            raise e

    @classmethod
    def load_multiple_files(cls, file_paths: List[str]) -> List[Document]:
        """
        Loads multiple files and combines their outputs into a single list of Documents.
        
        Args:
            file_paths: List of paths to files.
            
        Returns:
            Combined list of LangChain Document objects.
        """
        all_documents: List[Document] = []
        for path in file_paths:
            docs = cls.load_file(path)
            all_documents.extend(docs)

        logger.info(f"Total documents loaded across {len(file_paths)} files: {len(all_documents)}")
        return all_documents