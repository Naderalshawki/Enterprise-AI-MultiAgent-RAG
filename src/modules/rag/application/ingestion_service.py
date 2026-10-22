"""Ingestion service coordinating loaders, chunkers, and vector indexing."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.modules.rag.application.dtos import IngestDocumentDTO, IngestResultDTO
from src.modules.rag.domain.entities import Chunk, Document
from src.modules.rag.domain.interfaces import IChunker, IDocumentLoader, IVectorStore
from src.modules.rag.domain.value_objects import DocumentType
from src.modules.rag.infrastructure.chunkers.recursive_chunker import RecursiveChunker
from src.modules.rag.infrastructure.hybrid_search.bm25_searcher import BM25Searcher
from src.modules.rag.infrastructure.loaders.composite_loader import CompositeDocumentLoader
from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore


class IngestionService:
    """Orchestrates the entire document ingestion pipeline: Load -> Chunk -> Embed -> Index."""

    def __init__(
        self,
        loader: Optional[IDocumentLoader] = None,
        chunker: Optional[IChunker] = None,
        vector_store: Optional[IVectorStore] = None,
        bm25_searcher: Optional[BM25Searcher] = None,
    ):
        self.loader = loader or CompositeDocumentLoader()
        self.chunker = chunker or RecursiveChunker()
        self.vector_store = vector_store or ChromaVectorStore()
        self.bm25_searcher = bm25_searcher or BM25Searcher()
        self._all_indexed_chunks: List[Chunk] = []

        # Warm up BM25 index with existing chunks from vector store if available
        if hasattr(self.vector_store, "get_all_chunks"):
            try:
                existing_chunks = self.vector_store.get_all_chunks()
                if existing_chunks:
                    self._all_indexed_chunks = existing_chunks
                    self.bm25_searcher.fit(self._all_indexed_chunks)
            except Exception:
                pass

    def ingest_file(self, dto: IngestDocumentDTO) -> IngestResultDTO:
        """Ingest a single document file into the vector and BM25 index."""
        # 1. Load document text and metadata
        doc = self.loader.load(
            file_path=dto.file_path,
            tenant_id=dto.tenant_id,
            **dto.metadata,
        )

        # Override file name if explicitly provided in DTO
        if dto.file_name:
            doc.name = dto.file_name
            doc.metadata["file_name"] = dto.file_name

        # 2. Chunk document into semantically cohesive pieces
        chunks = self.chunker.split(doc)

        if not chunks:
            return IngestResultDTO(
                document_id=doc.id,
                document_name=doc.name,
                chunks_count=0,
                status="warning",
                message="لم يتم استخراج أي مقاطع نصية صالحة من الملف.",
            )

        # 3. Store in Vector Database
        self.vector_store.add_chunks(chunks)

        # 4. Update in-memory BM25 index
        self._all_indexed_chunks.extend(chunks)
        self.bm25_searcher.fit(self._all_indexed_chunks)

        return IngestResultDTO(
            document_id=doc.id,
            document_name=doc.name,
            chunks_count=len(chunks),
            status="success",
            message=f"تم استيعاب وفهرسة المستند بنجاح إلى {len(chunks)} مقطعاً.",
        )

    def ingest_text(
        self,
        text: str,
        document_name: str = "raw_text_document.txt",
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResultDTO:
        """Directly ingest raw text into the vector and BM25 index without creating a file."""
        meta = metadata or {}
        meta.setdefault("file_name", document_name)
        meta.setdefault("file_size_bytes", len(text.encode("utf-8")))

        doc = Document(
            name=document_name,
            file_path="in_memory",
            doc_type=DocumentType.TXT,
            text_content=text,
            metadata=meta,
            tenant_id=tenant_id,
        )

        chunks = self.chunker.split(doc)
        if not chunks:
            return IngestResultDTO(
                document_id=doc.id,
                document_name=doc.name,
                chunks_count=0,
                status="warning",
                message="لم يتم استخراج أي مقاطع نصية صالحة من النص.",
            )

        self.vector_store.add_chunks(chunks)
        self._all_indexed_chunks.extend(chunks)
        self.bm25_searcher.fit(self._all_indexed_chunks)

        return IngestResultDTO(
            document_id=doc.id,
            document_name=doc.name,
            chunks_count=len(chunks),
            status="success",
            message=f"تم استيعاب وفهرسة النص بنجاح إلى {len(chunks)} مقطعاً.",
        )

    def delete_document(self, document_id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete a document only when it belongs to the requested tenant."""
        owned = [
            c for c in self._all_indexed_chunks
            if (c.document_id == document_id or c.document_name == document_id)
            and (tenant_id is None or c.tenant_id == tenant_id)
        ]
        if not owned:
            return False
        actual_id = owned[0].document_id
        self.vector_store.delete_document(actual_id, tenant_id=tenant_id)
        self._all_indexed_chunks = [
            c for c in self._all_indexed_chunks
            if not (
                (c.document_id == document_id or c.document_name == document_id)
                and (tenant_id is None or c.tenant_id == tenant_id)
            )
        ]
        self.bm25_searcher.fit(self._all_indexed_chunks)
        return True

    def list_documents(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List distinct documents with statistics."""
        if hasattr(self.vector_store, "list_documents"):
            return self.vector_store.list_documents(tenant_id=tenant_id)

        docs_map: Dict[str, Dict[str, Any]] = {}
        for chunk in self._all_indexed_chunks:
            if tenant_id and chunk.tenant_id != tenant_id:
                continue
            doc_key = chunk.document_id or chunk.document_name
            if doc_key not in docs_map:
                docs_map[doc_key] = {
                    "document_id": chunk.document_id,
                    "document_name": chunk.document_name,
                    "tenant_id": chunk.tenant_id,
                    "chunks_count": 0,
                }
            docs_map[doc_key]["chunks_count"] += 1
        return list(docs_map.values())

    def ingest_directory(
        self,
        dir_path: str,
        tenant_id: Optional[str] = None,
        recursive: bool = False,
    ) -> List[IngestResultDTO]:
        """Ingest all supported documents inside a directory."""
        directory = Path(dir_path)
        if not directory.is_dir():
            raise ValueError(f"المسار ليس مجلداً: {dir_path}")

        pattern = "**/*" if recursive else "*"
        results: List[IngestResultDTO] = []

        for path in directory.glob(pattern):
            if path.is_file() and self.loader.can_handle(path.suffix):
                dto = IngestDocumentDTO(
                    file_path=str(path),
                    file_name=path.name,
                    tenant_id=tenant_id,
                )
                try:
                    res = self.ingest_file(dto)
                    results.append(res)
                except Exception as err:
                    results.append(
                        IngestResultDTO(
                            document_id="",
                            document_name=path.name,
                            chunks_count=0,
                            status="error",
                            message=str(err),
                        )
                    )

        return results

    def get_indexed_chunks(self) -> List[Chunk]:
        return self._all_indexed_chunks

    def get_document_chunks(self, document_id: str, tenant_id: Optional[str] = None) -> List[Chunk]:
        return [
            c for c in self._all_indexed_chunks
            if (c.document_id == document_id or c.document_name == document_id)
            and (tenant_id is None or c.tenant_id == tenant_id)
        ]
