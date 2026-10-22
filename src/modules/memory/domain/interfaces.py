from __future__ import annotations

from abc import ABC, abstractmethod

from src.modules.memory.domain.entities import Memory


class MemoryRepository(ABC):

    @abstractmethod
    async def save(self, memory: Memory) -> Memory:
        raise NotImplementedError

    @abstractmethod
    async def get(self, memory_id: str) -> Memory | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_session(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[Memory]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[Memory]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        raise NotImplementedError