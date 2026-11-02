import json
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text

from src.modules.memory.domain.entities import Memory
from src.modules.memory.domain.interfaces import MemoryRepository
from src.modules.memory.domain.value_objects import MemoryType, MemoryImportance

logger = logging.getLogger(__name__)


# ==========================================================
# 1. In-Memory Repository (للاختبارات السريعة)
# ==========================================================
class InMemoryRepository(MemoryRepository):
    def __init__(self):
        self._memories = []

    async def save(self, memory: Memory) -> None:
        self._memories.append(memory)

    async def get(self, memory_id: str) -> Memory | None:
        return None

    async def get_by_session(self, session_id: str, limit: int = 10) -> list[Memory]:
        filtered = [m for m in self._memories if m.session_id == session_id]
        return filtered[-limit:]

    async def get_by_user(self, user_id: str, limit: int = 10) -> list[Memory]:
        filtered = [m for m in self._memories if m.user_id == user_id]
        return filtered[-limit:]

    async def delete(self, memory_id: str) -> None:
        pass


# ==========================================================
# 2. SQL Repository (المؤسسي - يحفظ في PostgreSQL)
# ==========================================================
class SQLMemoryRepository(MemoryRepository):
    """ذاكرة مؤسسية تعتمد على PostgreSQL."""

    def __init__(self, database_url: str):
        self.engine: AsyncEngine = create_async_engine(database_url)

    async def save(self, memory: Memory) -> None:
        tenant_id = memory.metadata.get("tenant_id", "default-tenant")
        metadata_json = json.dumps(memory.metadata)

        query = text("""
            INSERT INTO agent_memories (
                user_id, session_id, content, memory_type, importance, metadata, tenant_id
            ) VALUES (
                :user_id, :session_id, :content, :memory_type, :importance, :metadata, :tenant_id
            )
        """)
        
        async with self.engine.begin() as conn:
            await conn.execute(query, {
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "content": memory.content,
                "memory_type": memory.memory_type.value,
                "importance": memory.importance.value,
                "metadata": metadata_json,
                "tenant_id": tenant_id,
            })
            logger.info(f"[SQL Memory] Saved memory for user {memory.user_id} | tenant: {tenant_id}")

    async def get(self, memory_id: str) -> Memory | None:
        query = text("""
            SELECT user_id, session_id, content, memory_type, importance, metadata, created_at, tenant_id
            FROM agent_memories
            WHERE id = :memory_id
        """)
        
        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"memory_id": memory_id})
            row = result.fetchone()
            
        if not row:
            return None
        return self._map_row(row)

    async def get_by_session(self, session_id: str, limit: int = 10) -> list[Memory]:
        query = text("""
            SELECT user_id, session_id, content, memory_type, importance, metadata, created_at, tenant_id
            FROM agent_memories
            WHERE session_id = :session_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"session_id": session_id, "limit": limit})
            rows = result.fetchall()
            
        return [self._map_row(row) for row in reversed(rows)]

    async def get_by_user(self, user_id: str, limit: int = 10) -> list[Memory]:
        query = text("""
            SELECT user_id, session_id, content, memory_type, importance, metadata, created_at, tenant_id
            FROM agent_memories
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"user_id": user_id, "limit": limit})
            rows = result.fetchall()
            
        return [self._map_row(row) for row in reversed(rows)]

    async def delete(self, memory_id: str) -> None:
        query = text("DELETE FROM agent_memories WHERE id = :memory_id")
        async with self.engine.begin() as conn:
            await conn.execute(query, {"memory_id": memory_id})

    def _map_row(self, row) -> Memory:
        raw_metadata = row[5]
        if isinstance(raw_metadata, dict):
            metadata = raw_metadata
        else:
            metadata = json.loads(raw_metadata or "{}")
            
        metadata["tenant_id"] = row[7] if len(row) > 7 else "default-tenant"

        return Memory(
            user_id=row[0],
            session_id=row[1],
            content=row[2],
            memory_type=MemoryType(row[3]),
            importance=MemoryImportance(row[4]),
            metadata=metadata,
        )


# ==========================================================
# 3. Semantic Repository (الذاكرة الدلالية - ChromaDB)
# ==========================================================
class SemanticMemoryRepository(MemoryRepository):
    """ذاكرة دلالية تعتمد على ChromaDB لفهم المعنى."""

    def __init__(self, persist_directory: str = "./data/memory_storage"):
        import chromadb
        from src.modules.rag.infrastructure.vector_store.embeddings import EmbeddingModel
        
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._client.get_or_create_collection(name="agent_memory")
        self._embedder = EmbeddingModel()

    async def save(self, memory: Memory) -> None:
        try:
            # تحويل النص لبصمة رقمية (Embedding)
            embedding = self._embedder.embed_query(memory.content)
            
            # حفظ المحادثة في الكرومadb
            self._collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": memory.user_id,
                    "session_id": memory.session_id,
                    "content": memory.content,
                    "memory_type": memory.memory_type.value,
                    "importance": memory.importance.value,
                    "tenant_id": memory.metadata.get("tenant_id", "default-tenant")
                }],
                documents=[memory.content]
            )
            logger.info(f"[Semantic Memory] Saved memory for user {memory.user_id}")
        except Exception as e:
            logger.error(f"[Semantic Memory] Failed to save: {e}")

    async def get(self, memory_id: str) -> Memory | None:
        return None

    async def get_by_session(self, session_id: str, limit: int = 10) -> list[Memory]:
        results = self._collection.get(
            where={"session_id": session_id},
            limit=limit
        )
        return self._map_results(results)

    async def get_by_user(self, user_id: str, limit: int = 10) -> list[Memory]:
        results = self._collection.get(
            where={"user_id": user_id},
            limit=limit
        )
        return self._map_results(results)

    async def search_semantic(self, query: str, user_id: str, limit: int = 3) -> list[Memory]:
        """البحث الدلالي عن المحادثات المشابهة في المعنى."""
        try:
            query_embedding = self._embedder.embed_query(query)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"user_id": user_id}
            )
            return self._map_results(results)
        except Exception as e:
            logger.error(f"[Semantic Memory] Failed to search: {e}")
            return []

    async def delete(self, memory_id: str) -> None:
        self._collection.delete(ids=[memory_id])

    def _map_results(self, results) -> list[Memory]:
        memories = []
        if not results or not results.get('metadatas'):
            return memories
        for meta in results['metadatas'][0]:
            memories.append(Memory(
                user_id=meta['user_id'],
                session_id=meta['session_id'],
                content=meta['content'],
                memory_type=MemoryType(meta['memory_type']),
                importance=MemoryImportance(meta['importance']),
                metadata={"tenant_id": meta.get("tenant_id")}
            ))
        return memories