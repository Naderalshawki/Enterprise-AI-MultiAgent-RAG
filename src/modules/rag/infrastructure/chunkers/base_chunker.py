"""Base class for text chunkers extending IChunker interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.modules.rag.domain.entities import Chunk, Document
from src.modules.rag.domain.interfaces import IChunker


class BaseChunker(IChunker, ABC):
    """Abstract base chunker providing standard chunk creation logic."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError("يجب أن يكون حجم التداخل (chunk_overlap) أصغر من حجم المقطع (chunk_size).")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def split(self, document: Document) -> List[Chunk]:
        """Split a document into sequential chunks with preserved metadata."""
        pass

    def create_chunk(
        self,
        document: Document,
        text: str,
        chunk_index: int,
        page_number: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Chunk:
        """Helper to create a Chunk entity with inherited document metadata."""
        meta = dict(document.metadata)
        if extra_metadata:
            meta.update(extra_metadata)

        return Chunk(
            document_id=document.id,
            document_name=document.name,
            text=text.strip(),
            chunk_index=chunk_index,
            page_number=page_number,
            metadata=meta,
            tenant_id=document.tenant_id,
        )
