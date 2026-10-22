"""Entities for the RAG domain."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from src.modules.rag.domain.value_objects import DocumentType


@dataclass
class Document:
    """Represents an ingested raw document."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    file_path: str = ""
    doc_type: DocumentType = DocumentType.UNKNOWN
    text_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def extension(self) -> str:
        return self.name.split(".")[-1] if "." in self.name else ""


@dataclass
class Chunk:
    """Represents a discrete text fragment produced by chunking a Document."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    document_name: str = ""
    text: str = ""
    chunk_index: int = 0
    page_number: Optional[int] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None

    def to_metadata(self) -> Dict[str, Any]:
        """Flatten metadata for vector store insertion."""
        meta = {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number if self.page_number is not None else -1,
            "tenant_id": self.tenant_id or "",
        }
        meta.update(self.metadata)
        return meta


@dataclass
class SearchResult:
    """Represents a chunk retrieved during similarity or hybrid search."""
    chunk: Chunk
    score: float
    retrieval_method: str = "dense"  # "dense", "sparse_bm25", or "hybrid"
