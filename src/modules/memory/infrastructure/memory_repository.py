from __future__ import annotations

from src.modules.memory.domain.entities import Memory
from src.modules.memory.domain.interfaces import MemoryRepository


class InMemoryRepository(MemoryRepository):

    def __init__(self):
        self._memories: dict[str, Memory] = {}

    async def save(self, memory: Memory) -> Memory:

        self._memories[str(memory.id)] = memory

        return memory

    async def get(
        self,
        memory_id: str,
    ) -> Memory | None:

        return self._memories.get(memory_id)

    async def get_by_session(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[Memory]:

        memories = [
            memory
            for memory in self._memories.values()
            if memory.session_id == session_id
        ]

        return memories[-limit:]

    async def get_by_user(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[Memory]:

        memories = [
            memory
            for memory in self._memories.values()
            if memory.user_id == user_id
        ]

        return memories[-limit:]

    async def delete(
        self,
        memory_id: str,
    ) -> bool:

        return self._memories.pop(memory_id, None) is not None