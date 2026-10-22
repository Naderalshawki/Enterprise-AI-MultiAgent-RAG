from abc import ABC, abstractmethod
from typing import AsyncGenerator

from src.modules.llm.domain.entities import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    EmbeddingRequest,
    EmbeddingResponse,
    VisionRequest,
    VisionResponse,
)

from src.modules.llm.domain.interfaces import LLMProvider

from src.modules.llm.domain.value_objects import (
    AICapability,
)

from src.modules.llm.domain.exceptions.exceptions import (
    FeatureNotSupportedError,
)

from src.modules.llm.infrastructure.config.provider_config import (
    ProviderConfig,
)


class BaseProvider(LLMProvider, ABC):
    """
    Base class لجميع مزودي الذكاء الاصطناعي.
    """

    capabilities: set[AICapability] = set()

    def __init__(
        self,
        config: ProviderConfig,
    ):
        self.config = config

    @property
    def provider_name(self) -> str:
        return self.config.provider.value

    # =====================================================
    # Capabilities
    # =====================================================

    def supports(
        self,
        capability: AICapability,
    ) -> bool:
        return capability in self.capabilities

    # =====================================================
    # Chat
    # =====================================================

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

    # =====================================================
    # Embeddings
    # =====================================================

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:

        raise FeatureNotSupportedError(
            f"Provider '{self.provider_name}' does not support embeddings."
        )

    # =====================================================
    # Vision
    # =====================================================

    async def vision(
        self,
        request: VisionRequest,
    ) -> VisionResponse:

        raise FeatureNotSupportedError(
            f"Provider '{self.provider_name}' does not support vision."
        )

    # =====================================================
    # Models
    # =====================================================

    @abstractmethod
    async def list_models(
        self,
    ) -> list[ModelInfo]:
        ...

    @abstractmethod
    async def health_check(
        self,
    ) -> bool:
        ...