from typing import List, Optional

from pydantic import BaseModel, Field

from src.modules.llm.domain.value_objects import (
    ProviderName,
    ResponseFormat,
    Role,
)


class MessageDTO(BaseModel):
    role: Role
    content: str


class GenerateRequestDTO(BaseModel):
    provider: ProviderName

    model: str

    messages: List[MessageDTO]

    temperature: float = Field(default=0.7, ge=0, le=2)

    max_tokens: int = Field(default=1024, gt=0)

    stream: bool = False

    response_format: ResponseFormat = ResponseFormat.TEXT


class UsageDTO(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class GenerateResponseDTO(BaseModel):
    content: str

    provider: ProviderName

    model: str

    usage: Optional[UsageDTO] = None

    # ==========================================================
# Embeddings
# ==========================================================

class EmbeddingRequestDTO(BaseModel):
    provider: ProviderName

    model: str

    input: str | List[str]

    dimensions: Optional[int] = None

    encoding_format: str = "float"

    user: Optional[str] = None


class EmbeddingResponseDTO(BaseModel):
    embedding: List[float] | List[List[float]]

    provider: ProviderName

    model: str

    usage: Optional[UsageDTO] = None

# ==========================================================
# Vision
# ==========================================================

class VisionRequestDTO(BaseModel):
    provider: ProviderName

    model: str

    prompt: str

    max_tokens: int = Field(
        default=1024,
        gt=0,
    )


class VisionResponseDTO(BaseModel):
    content: str

    provider: ProviderName

    model: str

    usage: Optional[UsageDTO] = None