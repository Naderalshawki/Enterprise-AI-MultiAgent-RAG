from abc import ABC, abstractmethod
from typing import AsyncGenerator

from src.modules.llm.domain.entities import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    EmbeddingRequest,
    EmbeddingResponse,
)

from src.modules.llm.domain.value_objects import (
    AICapability,
    ProviderName,
)


# ==========================================================
# Provider
# ==========================================================

class LLMProvider(ABC):
    """
    Contract for all LLM providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def capabilities(self) -> set[AICapability]:
        ...

    @abstractmethod
    def supports(
        self,
        capability: AICapability,
    ) -> bool:
        ...

    # ======================================================
    # Chat
    # ======================================================

    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def generate_stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[str, None]:
        ...

    # ======================================================
    # Embeddings
    # ======================================================

    @abstractmethod
    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:
        ...

    # ======================================================
    # Models
    # ======================================================

    @abstractmethod
    async def list_models(
        self,
    ) -> list[ModelInfo]:
        ...

    # ======================================================
    # Health
    # ======================================================

    @abstractmethod
    async def health_check(
        self,
    ) -> bool:
        ...


# ==========================================================
# Router
# ==========================================================

class LLMRouter(ABC):
    """
    Contract for provider routing.
    """

    @abstractmethod
    def get_provider(
        self,
        provider: ProviderName,
    ) -> LLMProvider:
        ...

    @abstractmethod
    def get_default_provider(
        self,
    ) -> LLMProvider:
        ...

    @abstractmethod
    def get_all_providers(
        self,
    ) -> list[LLMProvider]:
        ...