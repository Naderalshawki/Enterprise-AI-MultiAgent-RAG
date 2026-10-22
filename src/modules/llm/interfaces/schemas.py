from src.modules.llm.application.dtos import (
    GenerateRequestDTO,
    GenerateResponseDTO,
    MessageDTO,
    UsageDTO,
    EmbeddingRequestDTO,
    EmbeddingResponseDTO,
    VisionRequestDTO,
    VisionResponseDTO,
)


class GenerateRequestSchema(GenerateRequestDTO):
    pass


class GenerateResponseSchema(GenerateResponseDTO):
    pass


class MessageSchema(MessageDTO):
    pass


class UsageSchema(UsageDTO):
    pass


class EmbeddingRequestSchema(EmbeddingRequestDTO):
    pass


class EmbeddingResponseSchema(EmbeddingResponseDTO):
    pass


# ==========================================================
# Vision
# ==========================================================

class VisionRequestSchema(VisionRequestDTO):
    pass


class VisionResponseSchema(VisionResponseDTO):
    pass