"""Embedding function. Default: Chroma's bundled ONNX MiniLM (zero setup).
Set CODEAGENT_EMBEDDER=st:<model> to use sentence-transformers instead,
e.g. st:BAAI/bge-small-en-v1.5."""
import os


def get_embedder():
    spec = os.getenv("CODEAGENT_EMBEDDER", "default")
    if spec.startswith("st:"):
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        return SentenceTransformerEmbeddingFunction(model_name=spec[3:])
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return DefaultEmbeddingFunction()
