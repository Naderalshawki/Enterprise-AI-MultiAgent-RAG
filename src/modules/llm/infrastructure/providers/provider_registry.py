
# from src.modules.llm.infrastructure.providers.openai_compatible_provider import (
#     OpenAICompatibleProvider,
# )
# from src.modules.llm.infrastructure.providers.gemini_provider import (
#     GeminiProvider,
# )
# from src.modules.llm.infrastructure.providers.GEMINI_provider import (
#     GEMINIProvider,
# )
# from src.modules.llm.infrastructure.providers.ollama.ollama_provider import (
#     OllamaProvider,
# )


# PROVIDERS = {
#     "openai": {
#         "provider": OpenAICompatibleProvider,
#         "base_url": "https://api.openai.com/v1",
#     },
#     "GEMINI": {
#         "provider": GEMINIProvider,
#         "base_url": "https://api.GEMINI.com/openai/v1",
#     },
#     "deepseek": {
#         "provider": OpenAICompatibleProvider,
#         "base_url": "https://api.deepseek.com",
#     },
#     "kimi": {
#         "provider": OpenAICompatibleProvider,
#         "base_url": "https://api.moonshot.ai/v1",
#     },
#     "openrouter": {
#         "provider": OpenAICompatibleProvider,
#         "base_url": "https://openrouter.ai/api/v1",
#     },
#     "together": {
#         "provider": OpenAICompatibleProvider,
#         "base_url": "https://api.together.xyz/v1",
#     },
#     "gemini": {
#         "provider": GeminiProvider,
#         "base_url": None,
#     },
#     "ollama": {
#         "provider": OllamaProvider,
#         "base_url": "http://127.0.0.1:11434",
#     },
# }




from src.modules.llm.infrastructure.providers.openai_compatible_provider import (
    OpenAICompatibleProvider,
)
from src.modules.llm.infrastructure.providers.gemini_provider import (
    GeminiProvider,
)
from src.modules.llm.infrastructure.providers.groq_provider import (
    GroqProvider,
)
from src.modules.llm.infrastructure.providers.ollama.ollama_provider import (
    OllamaProvider,
)

PROVIDERS = {
    "openai": {
        "provider": OpenAICompatibleProvider,
        "base_url": "https://api.openai.com/v1",
    },
    "gemini": {
        "provider": GeminiProvider,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "deepseek": {
        "provider": OpenAICompatibleProvider,
        "base_url": "https://api.deepseek.com",
    },
    "kimi": {
        "provider": OpenAICompatibleProvider,
        "base_url": "https://api.moonshot.ai/v1",
    },
    "openrouter": {
        "provider": OpenAICompatibleProvider,
        "base_url": "https://openrouter.ai/api/v1",
    },
    "together": {
        "provider": OpenAICompatibleProvider,
        "base_url": "https://api.together.xyz/v1",
    },
    "gemini": {
        "provider": GeminiProvider,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "ollama": {
        "provider": OllamaProvider,
        "base_url": "http://127.0.0.1:11434",
    },
}