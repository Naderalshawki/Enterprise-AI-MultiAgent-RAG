from __future__ import annotations

from src.modules.memory.application.dtos import (
    SaveMemoryRequest,
    MemorySearchRequest,
)
from src.modules.memory.domain.entities import Memory
from src.modules.memory.domain.interfaces import MemoryRepository


class MemoryService:

    def __init__(self, repository: MemoryRepository):
        self._repository = repository

    async def save(
        self,
        request: SaveMemoryRequest,
    ) -> Memory:

        memory = Memory(
            user_id=request.user_id,
            session_id=request.session_id,
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            metadata=request.metadata,
        )

        return await self._repository.save(memory)

    async def get_session_memories(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[Memory]:

        return await self._repository.get_by_session(
            session_id=session_id,
            limit=limit,
        )

    async def get_user_memories(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[Memory]:

        return await self._repository.get_by_user(
            user_id=user_id,
            limit=limit,
        )

    async def delete(
        self,
        memory_id: str,
    ) -> bool:

        return await self._repository.delete(memory_id)