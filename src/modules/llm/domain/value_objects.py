from enum import Enum


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