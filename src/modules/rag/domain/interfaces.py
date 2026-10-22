"""Abstract interfaces defining the contracts for RAG components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.modules.rag.domain.entities import Chunk, Document, SearchResult


class IDocumentLoader(ABC):
    """Contract for extracting text and metadata from files."""

    @abstractmethod
    def load(self, file_path: str, **kwargs) -> Document:
        """Load and parse file into a Document domain entity."""
        pass

    @abstractmethod
    def can_handle(self, extension: str) -> bool:
        """Return True if this loader can handle the given file extension."""
        pass


class IChunker(ABC):
    """Contract for partitioning a Document into Chunks."""

    @abstractmethod
    def split(self, document: Document) -> List[Chunk]:
        """Split a document into sequential chunks with preserved metadata."""
        pass


class IEmbeddingGenerator(ABC):
    """Contract for embedding text strings into dense numerical vectors."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of document chunks."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate a single vector embedding for a search query."""
        pass


class IVectorStore(ABC):
    """Contract for vector database storage and similarity search."""

    @abstractmethod
    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Store chunks and their embeddings in the vector index."""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for top_k most similar chunks by vector distance."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str, tenant_id: Optional[str] = None) -> None:
        """Remove all chunks belonging to a given document ID, optionally scoped to a tenant."""
        pass


class IReranker(ABC):
    """Contract for re-scoring and ordering retrieved candidates."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[SearchResult],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Re-rank candidate search results against the query."""
        pass
