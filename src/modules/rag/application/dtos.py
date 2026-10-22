"""Data Transfer Objects (DTOs) for RAG application layer."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IngestDocumentDTO:
    file_path: str
    file_name: str
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestResultDTO:
    document_id: str
    document_name: str
    chunks_count: int
    status: str = "success"
    message: str = ""


@dataclass
class QueryInputDTO:
    query: str
    top_k: int = 5
    tenant_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    enable_hybrid: bool = True
    enable_rerank: bool = True


@dataclass
class CitationDTO:
    document_id: str
    document_name: str
    chunk_id: str
    page: Optional[int] = None
    score: float = 0.0
    snippet: str = ""


@dataclass
class QueryOutputDTO:
    query: str
    context: str
    citations: List[CitationDTO] = field(default_factory=list)
    total_retrieved: int = 0
