from __future__ import annotations

from src.modules.memory.domain.entities import Memory
from src.modules.memory.domain.interfaces import MemoryRepository


class ConversationStore:

    def __init__(
        self,
        repository: MemoryRepository,
    ):
        self._repository = repository

    async def add_message(
        self,
        user_id: str,
        session_id: str,
        content: str,
    ) -> Memory:

        memory = Memory(
            user_id=user_id,
            session_id=session_id,
            content=content,
        )

        return await self._repository.save(memory)

    async def get_history(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[Memory]:

        return await self._repository.get_by_session(
            session_id=session_id,
            limit=limit,
        )