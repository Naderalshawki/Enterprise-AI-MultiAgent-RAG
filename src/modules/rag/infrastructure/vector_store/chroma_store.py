"""ChromaDB implementation of IVectorStore."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.modules.rag.config.settings import rag_settings
from src.modules.rag.domain.entities import Chunk, SearchResult
from src.modules.rag.domain.exceptions import VectorStoreException
from src.modules.rag.domain.interfaces import IEmbeddingGenerator, IVectorStore
from src.modules.rag.infrastructure.vector_store.embeddings import ChromaDefaultEmbeddingGenerator


class ChromaVectorStore(IVectorStore):
    """Vector storage and similarity search powered by ChromaDB."""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[Path] = None,
        embedding_generator: Optional[IEmbeddingGenerator] = None,
        in_memory: bool = False,
    ):
        self.collection_name = collection_name or rag_settings.chroma_collection_name
        self.persist_directory = persist_directory or rag_settings.chroma_persist_dir
        self.embedding_generator = embedding_generator or ChromaDefaultEmbeddingGenerator()

        try:
            if in_memory:
                self.client = chromadb.EphemeralClient()
            else:
                self.persist_directory.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=str(self.persist_directory),
                    settings=ChromaSettings(anonymized_telemetry=False),
                )

            # Cosine similarity space collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise VectorStoreException(f"فشل في تهيئة قاعدة بيانات ChromaDB: {e}") from e

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Store chunks and their vectors into Chroma collection."""
        if not chunks:
            return

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        embeddings_to_generate: List[str] = []
        chunks_missing_embeddings: List[int] = []

        for idx, chunk in enumerate(chunks):
            ids.append(chunk.id)
            documents.append(chunk.text)
            metadatas.append(self._sanitize_metadata(chunk.to_metadata()))

            if chunk.embedding is None:
                embeddings_to_generate.append(chunk.text)
                chunks_missing_embeddings.append(idx)

        # Generate embeddings in batch if not already present
        if embeddings_to_generate:
            generated_vectors = self.embedding_generator.embed_documents(embeddings_to_generate)
            for local_idx, chunk_idx in enumerate(chunks_missing_embeddings):
                chunks[chunk_idx].embedding = generated_vectors[local_idx]

        embeddings = [chunk.embedding for chunk in chunks]

        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as e:
            raise VectorStoreException(f"فشل في إضافة المقاطع لقاعدة المتجهات: {e}") from e

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search top_k most similar chunks by vector distance."""
        try:
            where_clause = self._build_where_clause(filters)

            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            search_results: List[SearchResult] = []

            ids = results.get("ids", [[]])[0]
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for i in range(len(ids)):
                chunk_id = ids[i]
                text = docs[i]
                meta = metas[i] if i < len(metas) else {}
                distance = distances[i] if i < len(distances) else 1.0

                # In cosine space, similarity = 1 - distance
                score = round(max(0.0, 1.0 - distance), 4)

                page_number = meta.get("page_number")
                if page_number == -1:
                    page_number = None

                chunk = Chunk(
                    id=chunk_id,
                    document_id=str(meta.get("document_id", "")),
                    document_name=str(meta.get("document_name", "")),
                    text=text,
                    chunk_index=int(meta.get("chunk_index", 0)),
                    page_number=page_number,
                    tenant_id=str(meta.get("tenant_id")) if meta.get("tenant_id") else None,
                    metadata=meta,
                )

                search_results.append(
                    SearchResult(
                        chunk=chunk,
                        score=score,
                        retrieval_method="dense_vector",
                    )
                )

            return search_results
        except Exception as e:
            raise VectorStoreException(f"فشل في عملية البحث المتجهي: {e}") from e

    def search_by_text(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Helper to directly search with query text without pre-embedding."""
        query_vector = self.embedding_generator.embed_query(query_text)
        return self.search(query_vector=query_vector, top_k=top_k, filters=filters)

    def delete_document(self, document_id: str, tenant_id: Optional[str] = None) -> None:
        """Delete only chunks belonging to a document inside tenant scope."""
        try:
            where = {"document_id": document_id}
            if tenant_id:
                where = {"$and": [{"document_id": document_id}, {"tenant_id": tenant_id}]}
            self.collection.delete(where=where)
        except Exception as e:
            raise VectorStoreException(f"فشل في حذف المستند {document_id}: {e}") from e

    def get_all_chunks(self, tenant_id: Optional[str] = None) -> List[Chunk]:
        """Retrieve all stored chunks from Chroma collection."""
        try:
            where_clause = {"tenant_id": tenant_id} if tenant_id else None
            data = self.collection.get(
                where=where_clause,
                include=["documents", "metadatas"],
            )
            chunks: List[Chunk] = []
            ids = data.get("ids", [])
            docs = data.get("documents", [])
            metas = data.get("metadatas", [])

            for i in range(len(ids)):
                meta = metas[i] if i < len(metas) and metas[i] else {}
                page_number = meta.get("page_number")
                if page_number == -1:
                    page_number = None

                chunk = Chunk(
                    id=ids[i],
                    document_id=str(meta.get("document_id", "")),
                    document_name=str(meta.get("document_name", "")),
                    text=docs[i] if i < len(docs) else "",
                    chunk_index=int(meta.get("chunk_index", 0)),
                    page_number=page_number,
                    tenant_id=str(meta.get("tenant_id")) if meta.get("tenant_id") else None,
                    metadata=meta,
                )
                chunks.append(chunk)
            return chunks
        except Exception as e:
            raise VectorStoreException(f"فشل في استرجاع المقاطع: {e}") from e

    def list_documents(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List distinct documents with chunk counts and metadata."""
        chunks = self.get_all_chunks(tenant_id=tenant_id)
        docs_map: Dict[str, Dict[str, Any]] = {}

        for chunk in chunks:
            doc_id = chunk.document_id or chunk.document_name
            if doc_id not in docs_map:
                docs_map[doc_id] = {
                    "document_id": chunk.document_id,
                    "document_name": chunk.document_name,
                    "tenant_id": chunk.tenant_id,
                    "chunks_count": 0,
                    "created_at": chunk.metadata.get("created_at", ""),
                }
            docs_map[doc_id]["chunks_count"] += 1

        return list(docs_map.values())

    def count(self) -> int:
        """Return total chunks count in collection."""
        return self.collection.count()

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all metadata values are Chroma-compatible primitives (str, int, float, bool)."""
        clean = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif v is None:
                clean[k] = ""
            else:
                clean[k] = str(v)
        return clean

    def _build_where_clause(self, filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Construct Chroma-compliant where query."""
        if not filters:
            return None

        # Filter out empty criteria
        valid_filters = {k: v for k, v in filters.items() if v is not None and v != ""}
        if not valid_filters:
            return None

        if len(valid_filters) == 1:
            k, v = next(iter(valid_filters.items()))
            return {k: v}

        return {"$and": [{k: v} for k, v in valid_filters.items()]}
