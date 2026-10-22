import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI

from src.modules.llm.domain.entities import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    EmbeddingRequest,
    EmbeddingResponse,
    VisionRequest,
    VisionResponse,
)

from src.modules.llm.domain.value_objects import (
    AICapability,
)

logger = logging.getLogger(__name__)

from src.modules.llm.infrastructure.config.provider_config import (
    ProviderConfig,
)

from src.modules.llm.infrastructure.providers.base_provider import (
    BaseProvider,
)

from src.modules.llm.infrastructure.mappers.request_mapper import (
    RequestMapper,
)

from src.modules.llm.infrastructure.mappers.response_mapper import (
    ResponseMapper,
)


class OpenAICompatibleProvider(BaseProvider):
    """
    Generic Provider for any OpenAI Compatible API.

    Supported:
    - OpenAI
    - GEMINI
    - DeepSeek
    - Kimi
    - OpenRouter
    - Together AI
    """

    capabilities = {
        AICapability.CHAT,
        AICapability.EMBEDDING,
        AICapability.VISION,
    }

    def __init__(
        self,
        config: ProviderConfig,
    ):
        super().__init__(config)

        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    # ==========================================================
    # Chat
    # ==========================================================

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        params = {
            "model": request.model,
            "messages": RequestMapper.to_openai_messages(request),
            "temperature": request.temperature,
            "max_completion_tokens": request.max_tokens,
        }

        # GPT-OSS can spend its entire completion budget on reasoning, leaving
        # message.content empty. Keep low reasoning effort limited to SQL tasks
        # so normal planner/chat calls retain their existing behavior.
        provider_name = str(
            getattr(self.config.provider, "value", self.config.provider)
        ).lower()
        metadata = getattr(request, "metadata", None) or {}
        is_GEMINI_gpt_oss_sql = (
            provider_name == "gemini"
            and request.model.startswith("openai/gpt-oss")
            and metadata.get("task") == "sql_generation"
        )
        if is_GEMINI_gpt_oss_sql:
            params["reasoning_effort"] = "low"

        response = await self.client.chat.completions.create(**params)

        # Log only safe diagnostics, never prompts, SQL, or credentials.
        choices = getattr(response, "choices", None) or []
        if choices:
            message = getattr(choices[0], "message", None)
            content = getattr(message, "content", None) if message else None
            if not (isinstance(content, str) and content.strip()):
                usage = getattr(response, "usage", None)
                logger.warning(
                    "LLM returned empty content | provider=%s model=%s "
                    "finish_reason=%s completion_tokens=%s task=%s",
                    provider_name,
                    request.model,
                    getattr(choices[0], "finish_reason", None),
                    getattr(usage, "completion_tokens", None),
                    metadata.get("task", "unspecified"),
                )

        return ResponseMapper.from_openai_compatible(
            response=response,
            provider=self.config.provider,
        )

    # ==========================================================
    # Stream
    # ==========================================================

    async def generate_stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[str, None]:

        stream = await self.client.chat.completions.create(
            model=request.model,
            messages=RequestMapper.to_openai_messages(
                request,
            ),
            temperature=request.temperature,
            max_completion_tokens=request.max_tokens,
            stream=True,
        )

        async for chunk in stream:

            if (
                chunk.choices
                and chunk.choices[0].delta
                and chunk.choices[0].delta.content
            ):
                yield chunk.choices[0].delta.content

    # ==========================================================
    # Vision
    # ==========================================================

    async def vision(
        self,
        request: VisionRequest,
    ) -> VisionResponse:

        response = await self.client.chat.completions.create(
            model=request.model,
            messages=RequestMapper.to_openai_vision_messages(
                request,
            ),
            max_completion_tokens=request.max_tokens,
        )

        return ResponseMapper.from_openai_vision(
            response=response,
            provider=self.config.provider,
        )

    # ==========================================================
    # Embeddings
    # ==========================================================

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:

        response = await self.client.embeddings.create(
            **RequestMapper.to_openai_embedding_request(
                request,
            )
        )

        return ResponseMapper.from_openai_embedding(
            response=response,
            provider=self.config.provider,
        )

    # ==========================================================
    # Models
    # ==========================================================

    async def list_models(
        self,
    ) -> list[ModelInfo]:

        response = await self.client.models.list()

        return [
            ModelInfo(
                provider=self.config.provider,
                model_name=model.id,
                supports_stream=True,
                supports_json=True,
                context_window=None,
            )
            for model in response.data
        ]

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
    ) -> bool:

        try:

            await self.client.models.list()

            return True

        except Exception:

            return False