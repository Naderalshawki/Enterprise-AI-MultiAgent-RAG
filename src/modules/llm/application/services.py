from dataclasses import replace

from src.modules.llm.application.prompt_builder import PromptBuilder

from src.modules.llm.domain.entities import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    EmbeddingRequest,
    EmbeddingResponse,
    VisionRequest,
    VisionResponse,
)

from src.modules.llm.domain.interfaces import (
    LLMRouter,
)

from src.modules.llm.domain.value_objects import (
    ProviderName,
)


class LLMService:
    """
    Main application service for LLM operations.
    """

    def __init__(
        self,
        router: LLMRouter,
        prompt_builder: PromptBuilder,
    ):
        self.router = router
        self.prompt_builder = prompt_builder

    # ==========================================================
    # Chat
    # ==========================================================

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        messages = self.prompt_builder.build(
            request,
        )

        validated_request = replace(
            request,
            messages=messages,
        )

        provider = self.router.get_provider(
            validated_request.provider,
        )

        return await provider.generate(
            validated_request,
        )

    # ==========================================================
    # Stream
    # ==========================================================

    async def generate_stream(
        self,
        request: LLMRequest,
    ):

        messages = self.prompt_builder.build(
            request,
        )

        validated_request = replace(
            request,
            messages=messages,
        )

        provider = self.router.get_provider(
            validated_request.provider,
        )

        async for chunk in provider.generate_stream(
            validated_request,
        ):
            yield chunk

    # ==========================================================
    # Embeddings
    # ==========================================================

    async def embed(
        self,
        provider: ProviderName,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:

        embedding_provider = self.router.get_provider(
            provider,
        )

        return await embedding_provider.embed(
            request,
        )

    # ==========================================================
    # Vision
    # ==========================================================

    async def vision(
        self,
        request: VisionRequest,
    ) -> VisionResponse:

        provider = self.router.get_provider(
            request.provider,
        )

        return await provider.vision(
            request,
        )

    # ==========================================================
    # Models
    # ==========================================================

    async def list_models(
        self,
        provider: ProviderName,
    ) -> list[ModelInfo]:

        llm_provider = self.router.get_provider(
            provider,
        )

        return await llm_provider.list_models()

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
        provider: ProviderName,
    ) -> bool:

        llm_provider = self.router.get_provider(
            provider,
        )

        return await llm_provider.health_check()