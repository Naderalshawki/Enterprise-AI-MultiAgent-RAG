# from enum import Enum

# class ProviderName(str, Enum):
#     OPENAI = "openai"
#     DEEPSEEK = "deepseek"
#     KIMI = "kimi"
#     GEMINI = "gemini"
#     OPENROUTER = "openrouter"
#     TOGETHER = "together"
#     ANTHROPIC = "anthropic"
#     OLLAMA = "ollama"  # 🚀 إضافة المزود المحلي الجديد


# # ==========================================================
# # Chat Roles
# # ==========================================================

# class Role(str, Enum):
#     SYSTEM = "system"
#     USER = "user"
#     ASSISTANT = "assistant"
#     TOOL = "tool"


# # ==========================================================
# # Response Format
# # ==========================================================

# class ResponseFormat(str, Enum):
#     TEXT = "text"
#     JSON = "json"


# # ==========================================================
# # Finish Reason
# # ==========================================================

# class FinishReason(str, Enum):
#     STOP = "stop"
#     TOOL_CALLS = "tool_calls"
#     LENGTH = "length"
#     CONTENT_FILTER = "content_filter"


# # ==========================================================
# # Provider Status
# # ==========================================================

# class ProviderStatus(str, Enum):
#     ONLINE = "online"
#     OFFLINE = "offline"
#     UNKNOWN = "unknown"


# # ==========================================================
# # AI Capabilities
# # ==========================================================

# class AICapability(str, Enum):
#     CHAT = "chat"
#     EMBEDDING = "embedding"
#     STREAMING = "streaming"
#     JSON_MODE = "json_mode"
#     TOOL_CALLING = "tool_calling"
#     VISION = "vision"
#     AUDIO_INPUT = "audio_input"
#     AUDIO_OUTPUT = "audio_output"
#     IMAGE_GENERATION = "image_generation"



from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field

# ==========================================================
# Providers
# ==========================================================

class ProviderName(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    TOGETHER = "together"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"  # 🚀 إضافة المزود المحلي الجديد


# ==========================================================
# Chat Roles
# ==========================================================

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# ==========================================================
# Response Format
# ==========================================================

class ResponseFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


# ==========================================================
# Finish Reason
# ==========================================================

class FinishReason(str, Enum):
    STOP = "stop"
    TOOL_CALLS = "tool_calls"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"


# ==========================================================
# Provider Status
# ==========================================================

class ProviderStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


# ==========================================================
# AI Capabilities
# ==========================================================

class AICapability(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    TOOL_CALLING = "tool_calling"
    VISION = "vision"
    AUDIO_INPUT = "audio_input"
    AUDIO_OUTPUT = "audio_output"
    IMAGE_GENERATION = "image_generation"


# ==========================================================
# Contracts & Tool Results
# ==========================================================

class ToolResult(BaseModel):
    status: Literal[
        "success",
        "no_results",
        "insufficient_evidence",
        "validation_error",
        "permission_denied",
        "timeout",
        "tool_error",
    ]
    tool_name: str
    data: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    trace_id: str | None = None