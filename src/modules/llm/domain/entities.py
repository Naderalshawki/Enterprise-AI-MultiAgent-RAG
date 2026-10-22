
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .tools import Tool
from .value_objects import (
    ProviderName,
    ResponseFormat,
    Role,
)


# ==========================================================
# Chat
# ==========================================================

@dataclass(slots=True)
class LLMMessage:
    role: Role
    content: str


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(slots=True)
class LLMRequest:
    provider: ProviderName
    model: str
    messages: list[LLMMessage]
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False
    response_format: ResponseFormat = ResponseFormat.TEXT
    tools: list[Tool] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LLMResponse:
    content: str
    provider: ProviderName
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


# ==========================================================
# Models
# ==========================================================

@dataclass(slots=True)
class ModelInfo:
    provider: ProviderName
    model_name: str
    supports_stream: bool = True
    supports_json: bool = True
    context_window: int | None = None


# ==========================================================
# Embeddings
# ==========================================================

@dataclass(slots=True)
class EmbeddingRequest:
    input: str | list[str]
    model: str
    dimensions: int | None = None
    encoding_format: str = "float"
    user: str | None = None


@dataclass(slots=True)
class EmbeddingResponse:
    embedding: list[float] | list[list[float]]
    provider: ProviderName
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


# ==========================================================
# Vision
# ==========================================================

@dataclass(slots=True)
class VisionRequest:
    provider: ProviderName
    model: str
    image: bytes
    mime_type: str
    prompt: str
    max_tokens: int = 1024
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VisionResponse:
    content: str
    provider: ProviderName
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
