from src.modules.llm.application.dtos import (
    GenerateRequestDTO,
    GenerateResponseDTO,
    UsageDTO,
    VisionRequestDTO,
    VisionResponseDTO,
    EmbeddingRequestDTO,
    EmbeddingResponseDTO,
)

from src.modules.llm.domain.entities import (
    LLMMessage,
    LLMRequest,
    LLMResponse,
    VisionRequest,
    VisionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class ApplicationMapper:
    """
    Maps between Application DTOs and Domain Entities.
    """

    # ==========================================================
    # Chat
    # ==========================================================

    @staticmethod
    def to_domain(
        dto: GenerateRequestDTO,
    ) -> LLMRequest:

        return LLMRequest(
            provider=dto.provider,
            model=dto.model,
            messages=[
                LLMMessage(
                    role=message.role,
                    content=message.content,
                )
                for message in dto.messages
            ],
            temperature=dto.temperature,
            max_tokens=dto.max_tokens,
            stream=dto.stream,
            response_format=dto.response_format,
        )

    @staticmethod
    def to_response(
        response: LLMResponse,
    ) -> GenerateResponseDTO:

        usage = UsageDTO(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return GenerateResponseDTO(
            content=response.content,
            provider=response.provider,
            model=response.model,
            usage=usage,
        )

    # ==========================================================
    # Embeddings
    # ==========================================================

    @staticmethod
    def to_embedding_domain(
        dto: EmbeddingRequestDTO,
    ) -> EmbeddingRequest:

        return EmbeddingRequest(
            input=dto.input,
            model=dto.model,
            dimensions=dto.dimensions,
            encoding_format=dto.encoding_format,
            user=dto.user,
        )

    @staticmethod
    def to_embedding_response(
        response: EmbeddingResponse,
    ) -> EmbeddingResponseDTO:

        usage = UsageDTO(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return EmbeddingResponseDTO(
            embedding=response.embedding,
            provider=response.provider,
            model=response.model,
            usage=usage,
        )

    # ==========================================================
    # Vision
    # ==========================================================

    @staticmethod
    def to_vision_domain(
        dto: VisionRequestDTO,
        image: bytes,
        mime_type: str,
    ) -> VisionRequest:

        return VisionRequest(
            provider=dto.provider,
            model=dto.model,
            image=image,
            mime_type=mime_type,
            prompt=dto.prompt,
            max_tokens=dto.max_tokens,
        )

    @staticmethod
    def to_vision_response(
        response: VisionResponse,
    ) -> VisionResponseDTO:

        usage = UsageDTO(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return VisionResponseDTO(
            content=response.content,
            provider=response.provider,
            model=response.model,
            usage=usage,
        )