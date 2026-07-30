"""
RAG Engine Module for ResearchGPT.
Orchestrates vector retrieval, web search, context fusion, and Groq LLM inference.
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from src.llm import LLMFactory
from src.vector_store import VectorStoreManager
from src.search import WebSearchManager
from src.logger import logger


class RAGEngine:
    """Core orchestration engine combining vector retrieval, web search, and Groq LLM inference."""

    def __init__(self):
        self.llm = LLMFactory.get_llm()
        self.vector_store_manager = VectorStoreManager()
        self.web_search_manager = WebSearchManager()

    def retrieve_documents(self, query: str, top_k: int = 4) -> List[Document]:
        """
        Retrieves top-k relevant document chunks from the local FAISS index.
        """
        vector_store = self.vector_store_manager.load_vector_store()
        if not vector_store:
            logger.info("No active FAISS index found for document retrieval.")
            return []

        logger.info(f"Retrieving top {top_k} chunk(s) for query: '{query}'")
        try:
            retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
            docs = retriever.invoke(query)
            logger.info(f"Retrieved {len(docs)} relevant chunk(s).")
            return docs
        except Exception as e:
            logger.error(f"Error during vector document retrieval: {str(e)}")
            return []

    @staticmethod
    def build_context_string(doc_results: List[Document], web_results: List[Dict[str, Any]]) -> str:
        """
        Formats local document chunks and web search snippets into a clean, context-rich prompt section.
        """
        context_parts = []

        if doc_results:
            context_parts.append("=== LOCAL DOCUMENT CONTEXT ===")
            for idx, doc in enumerate(doc_results, 1):
                filename = doc.metadata.get("filename", "Unknown File")
                page = doc.metadata.get("page_number", "N/A")
                context_parts.append(f"[{idx}] Source File: {filename} | Page: {page}\nContent: {doc.page_content}\n")

        if web_results:
            context_parts.append("=== WEB SEARCH CONTEXT ===")
            for idx, result in enumerate(web_results, 1):
                url = result.get("url", "N/A")
                content = result.get("content", "")
                context_parts.append(f"[Web-{idx}] Source URL: {url}\nSnippet: {content}\n")

        return "\n".join(context_parts) if context_parts else "No background context available."

    def answer_query(
        self,
        query: str,
        enable_web_search: bool = False,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Executes the full RAG pipeline and returns the generated answer along with cited sources.

        Args:
            query: User's research prompt.
            enable_web_search: Flag to trigger web search integration.
            top_k: Number of vector chunks to retrieve.

        Returns:
            Dictionary containing 'answer', 'doc_sources', and 'web_sources'.
        """
        logger.info(f"Processing research query: '{query}' (Web Search: {enable_web_search})")

        # 1. Retrieve local document context
        docs = self.retrieve_documents(query, top_k=top_k)

        # 2. Retrieve web search context if requested or if no local docs match
        web_results = []
        if enable_web_search or (not docs):
            logger.info("Fetching web context via Tavily...")
            web_results = self.web_search_manager.search(query)

        # 3. Build fused context block
        fused_context = self.build_context_string(docs, web_results)

        # 4. Construct prompt
        system_instruction = (
            "You are ResearchGPT, an elite AI research assistant. "
            "Answer the user's prompt thoroughly, accurately, and professionally based strictly on the provided context.\n\n"
            "Rules:\n"
            "1. Cite sources inline using reference tags (e.g., [1] or [Web-1]) where appropriate.\n"
            "2. If the context does not contain enough information to fully answer, state what is missing and provide the best available answer.\n"
            "3. Format your output cleanly with markdown headers, key takeaways, and bullet points.\n\n"
            "Context Information:\n{context}"
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("user", "{question}")
        ])

        # 5. Invoke Groq LLM
        formatted_prompt = prompt_template.format_messages(context=fused_context, question=query)
        logger.info("Dispatching context-enriched prompt to Groq LLM...")
        llm_response = self.llm.invoke(formatted_prompt)

        # 6. Extract source citations for UI rendering
        doc_sources = [
            {
                "filename": doc.metadata.get("filename", "Unknown"),
                "page": doc.metadata.get("page_number", 1),
                "snippet": doc.page_content[:200] + "..."
            }
            for doc in docs
        ]

        web_sources = [
            {"url": res.get("url", "#"), "snippet": res.get("content", "")[:200] + "..."}
            for res in web_results
        ]

        return {
            "answer": llm_response.content,
            "doc_sources": doc_sources,
            "web_sources": web_sources,
        }