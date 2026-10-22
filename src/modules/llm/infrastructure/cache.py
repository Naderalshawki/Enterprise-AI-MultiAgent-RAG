from abc import ABC, abstractmethod
from typing import Optional

from src.modules.llm.domain.entities import LLMResponse


class BaseCache(ABC):
    """
    Base cache interface.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[LLMResponse]:
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: LLMResponse,
        ttl: int = 3600,
    ) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass