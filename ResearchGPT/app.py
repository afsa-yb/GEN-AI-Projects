"""
ResearchGPT Application Entrypoint.
Streamlit web interface for document ingestion, web research, and conversational RAG.
"""

import os
import tempfile
import streamlit as st
from src.loader import DocumentLoader
from src.cleaner import TextCleaner
from src.splitter import DocumentSplitter
from src.vector_store import VectorStoreManager
from src.rag import RAGEngine
from src.logger import logger

# --- Page Configuration ---
st.set_page_config(
    page_title="ResearchGPT - AI Research Assistant",
    page_icon="🔬",
    layout="wide",
)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []


@st.cache_resource
def get_rag_engine() -> RAGEngine:
    """Instantiates and caches the core RAG Engine."""
    return RAGEngine()


st.session_state.rag_engine = get_rag_engine()


def process_uploaded_files(uploaded_files) -> bool:
    """
    Saves uploaded files to a temp directory, runs the ingestion pipeline,
    and updates the local FAISS vector store.
    """
    if not uploaded_files:
        return False

    temp_paths = []
    file_names = []

    try:
        with st.status("Processing and indexing documents...", expanded=True) as status:
            # 1. Save uploaded files to temp directory
            status.write("📁 Saving uploaded files...")
            temp_dir = tempfile.mkdtemp()
            for uploaded_file in uploaded_files:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                temp_paths.append(temp_path)
                file_names.append(uploaded_file.name)

            # 2. Load Documents
            status.write("📖 Extracting text from files...")
            raw_docs = DocumentLoader.load_multiple_files(temp_paths)

            # 3. Clean Text
            status.write("🧹 Sanitizing and cleaning text...")
            cleaned_docs = TextCleaner.clean_documents(raw_docs)

            # 4. Split Text into Chunks
            status.write("✂️ Splitting documents into overlapping chunks...")
            splitter = DocumentSplitter()
            chunked_docs = splitter.split_documents(cleaned_docs)

            # 5. Build and Save FAISS Index
            status.write("🧠 Generating dense embeddings and indexing in FAISS...")
            vector_manager = VectorStoreManager()
            vector_store = vector_manager.create_vector_store(chunked_docs)
            vector_manager.save_vector_store(vector_store)

            st.session_state.indexed_files = file_names
            status.update(label="✅ Indexing Complete!", state="complete", expanded=False)
            return True

    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        st.error(f"Failed to process documents: {str(e)}")
        return False


# --- Sidebar Interface ---
with st.sidebar:
    st.title("🔬 ResearchGPT")
    st.caption("Production RAG Assistant with Groq & Tavily")
    st.divider()

    st.subheader("1. Document Knowledge Base")
    uploaded_files = st.file_uploader(
        "Upload research materials (PDF, DOCX, TXT):",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    if st.button("Build Index", type="primary", use_container_width=True):
        if uploaded_files:
            if process_uploaded_files(uploaded_files):
                st.success("Knowledge Base Built Successfully!")
        else:
            st.warning("Please select at least one file first.")

    if st.session_state.indexed_files:
        st.write("---")
        st.markdown("**Currently Indexed Files:**")
        for fname in st.session_state.indexed_files:
            st.markdown(f"- `{fname}`")

    st.divider()

    st.subheader("2. Search & Retrieval Settings")
    enable_web_search = st.toggle(
        "Enable Tavily Web Search",
        value=False,
        help="Allows the assistant to pull real-time information from the web alongside local documents.",
    )

    st.divider()
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# --- Main Chat Interface ---
st.header("Chat & Research Dashboard")
st.caption("Ask questions about your uploaded documents or query general web topics.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Render document citations if present
        if "doc_sources" in message and message["doc_sources"]:
            with st.expander("📄 Document Sources Used"):
                for src in message["doc_sources"]:
                    st.markdown(f"**File:** `{src['filename']}` | **Page:** {src['page']}")
                    st.caption(f'"{src["snippet"]}"')

        # Render web search sources if present
        if "web_sources" in message and message["web_sources"]:
            with st.expander("🌐 Web Sources Used"):
                for wsrc in message["web_sources"]:
                    st.markdown(f"[{wsrc['url']}]({wsrc['url']})")
                    st.caption(f'"{wsrc["snippet"]}"')

# Handle User Input
if prompt := st.chat_input("Ask a research question..."):
    # Render user prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing context & generating response..."):
            rag_result = st.session_state.rag_engine.answer_query(
                query=prompt,
                enable_web_search=enable_web_search,
            )

            answer = rag_result["answer"]
            doc_sources = rag_result["doc_sources"]
            web_sources = rag_result["web_sources"]

            st.markdown(answer)

            if doc_sources:
                with st.expander("📄 Document Sources Used"):
                    for src in doc_sources:
                        st.markdown(f"**File:** `{src['filename']}` | **Page:** {src['page']}")
                        st.caption(f'"{src["snippet"]}"')

            if web_sources:
                with st.expander("🌐 Web Sources Used"):
                    for wsrc in web_sources:
                        st.markdown(f"[{wsrc['url']}]({wsrc['url']})")
                        st.caption(f'"{wsrc["snippet"]}"')

            # Append to session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "doc_sources": doc_sources,
                "web_sources": web_sources,
            })