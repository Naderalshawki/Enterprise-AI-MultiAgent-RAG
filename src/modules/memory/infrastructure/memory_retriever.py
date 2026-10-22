from __future__ import annotations

from src.modules.memory.domain.entities import Memory
from src.modules.memory.domain.interfaces import MemoryRepository


class MemoryRetriever:

    def __init__(
        self,
        repository: MemoryRepository,
    ):
        self._repository = repository

    async def retrieve(
        self,
        user_id: str,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[Memory]:

        if session_id:

            memories = await self._repository.get_by_session(
                session_id=session_id,
                limit=limit,
            )

            if memories:
                return memories

        return await self._repository.get_by_user(
            user_id=user_id,
            limit=limit,
        )