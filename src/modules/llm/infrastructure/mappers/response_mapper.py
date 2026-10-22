from src.modules.llm.domain.entities import (
    LLMResponse,
    VisionResponse,
    EmbeddingResponse,
    TokenUsage,
)

from src.modules.llm.domain.value_objects import (
    ProviderName,
)


class ResponseMapper:
    """
    Maps Provider Responses to Domain Entities.
    """

    # ==========================================================
    # Shared Usage
    # ==========================================================

    @staticmethod
    def _usage(response) -> TokenUsage:

        usage = getattr(response, "usage", None)

        if usage is None:
            return TokenUsage()

        return TokenUsage(
            prompt_tokens=getattr(
                usage,
                "prompt_tokens",
                0,
            ),
            completion_tokens=getattr(
                usage,
                "completion_tokens",
                0,
            ),
            total_tokens=getattr(
                usage,
                "total_tokens",
                0,
            ),
        )

    # ==========================================================
    # OpenAI Compatible Chat
    # ==========================================================

    @staticmethod
    def from_openai_compatible(
        response,
        provider: ProviderName,
    ) -> LLMResponse:

        return LLMResponse(
            content=response.choices[0].message.content,
            provider=provider,
            model=response.model,
            usage=ResponseMapper._usage(response),
        )

    # ==========================================================
    # Gemini Chat
    # ==========================================================

    @staticmethod
    def from_gemini(
        response,
        model: str,
    ) -> LLMResponse:

        return LLMResponse(
            content=response.text,
            provider=ProviderName.GEMINI,
            model=model,
            usage=TokenUsage(),
        )

    # ==========================================================
    # OpenAI Compatible Vision
    # ==========================================================

    @staticmethod
    def from_openai_vision(
        response,
        provider: ProviderName,
    ) -> VisionResponse:

        return VisionResponse(
            content=response.choices[0].message.content,
            provider=provider,
            model=response.model,
            usage=ResponseMapper._usage(response),
        )

    # ==========================================================
    # Gemini Vision
    # ==========================================================

    @staticmethod
    def from_gemini_vision(
        response,
        model: str,
    ) -> VisionResponse:

        return VisionResponse(
            content=response.text,
            provider=ProviderName.GEMINI,
            model=model,
            usage=TokenUsage(),
        )

    # ==========================================================
    # OpenAI Compatible Embeddings
    # ==========================================================

    @staticmethod
    def from_openai_embedding(
        response,
        provider: ProviderName,
    ) -> EmbeddingResponse:

        usage = getattr(response, "usage", None)

        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            provider=provider,
            model=response.model,
            usage=TokenUsage(
                prompt_tokens=getattr(
                    usage,
                    "prompt_tokens",
                    0,
                ),
                completion_tokens=0,
                total_tokens=getattr(
                    usage,
                    "total_tokens",
                    0,
                ),
            ),
        )

    # ==========================================================
    # Gemini Embeddings
    # ==========================================================

    @staticmethod
    def from_gemini_embedding(
        response,
        model: str,
    ) -> EmbeddingResponse:

        return EmbeddingResponse(
            embedding=response.embeddings[0].values,
            provider=ProviderName.GEMINI,
            model=model,
            usage=TokenUsage(),
        )