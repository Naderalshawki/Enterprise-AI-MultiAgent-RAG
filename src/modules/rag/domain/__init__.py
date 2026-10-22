"""Domain layer for RAG and Document Intelligence."""

from src.modules.rag.domain.entities import Chunk, Document, SearchResult
from src.modules.rag.domain.value_objects import Citation, DocumentType
from src.modules.rag.domain.exceptions import (
    RAGException,
    UnsupportedDocumentException,
    DocumentParsingException,
    VectorStoreException,
    RerankerException,
)
from src.modules.rag.domain.interfaces import (
    IDocumentLoader,
    IChunker,
    IEmbeddingGenerator,
    IVectorStore,
    IReranker,
)

__all__ = [
    "Chunk",
    "Document",
    "SearchResult",
    "Citation",
    "DocumentType",
    "RAGException",
    "UnsupportedDocumentException",
    "DocumentParsingException",
    "VectorStoreException",
    "RerankerException",
    "IDocumentLoader",
    "IChunker",
    "IEmbeddingGenerator",
    "IVectorStore",
    "IReranker",
]
