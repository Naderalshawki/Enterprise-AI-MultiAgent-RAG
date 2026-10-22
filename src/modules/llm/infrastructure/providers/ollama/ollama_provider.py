from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

import httpx

from src.modules.llm.domain.entities import (
    LLMRequest,
    LLMResponse,
    TokenUsage,
    ModelInfo,
)

from src.modules.llm.domain.value_objects import (
    AICapability,
)

from src.modules.llm.infrastructure.providers.base_provider import (
    BaseProvider,
)

from src.modules.llm.infrastructure.config.provider_config import (
    ProviderConfig,
)


logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """
    Local Ollama AI Provider.

    Connects to local Ollama server:
    http://127.0.0.1:11434
    """

    capabilities = {
        AICapability.CHAT,
        AICapability.STREAMING,
    }

    def __init__(
        self,
        config: ProviderConfig,
    ) -> None:

        super().__init__(config)

        self.base_url = (
            config.base_url
            or "http://127.0.0.1:11434"
        ).rstrip("/")

        self.default_model = (
            config.default_model
            or "qwen2.5-coder:7b"
        )

        logger.info(
            "Initialized Ollama provider: %s",
            self.default_model,
        )

    # ==========================================================
    # Messages → Ollama Prompt
    # ==========================================================

    @staticmethod
    def _build_prompt(request: LLMRequest) -> str:

        parts: list[str] = []

        for message in request.messages:

            role = message.role.value

            parts.append(
                f"{role.upper()}: {message.content}"
            )

        return "\n\n".join(parts)

    # ==========================================================
    # Chat
    # ==========================================================

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        endpoint = f"{self.base_url}/api/generate"

        prompt = self._build_prompt(request)

        model = (
            request.model
            or self.default_model
        )

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:

            async with httpx.AsyncClient(
                timeout=600.0
            ) as client:

                response = await client.post(
                    endpoint,
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()

            prompt_tokens = data.get(
                "prompt_eval_count",
                0,
            )

            completion_tokens = data.get(
                "eval_count",
                0,
            )

            return LLMResponse(
                content=data.get(
                    "response",
                    "",
                ),
                provider=self.config.provider,
                model=model,
                usage=TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=(
                        prompt_tokens
                        + completion_tokens
                    ),
                ),
                metadata={
                    "done": data.get(
                        "done",
                        False,
                    )
                },
            )

        except httpx.HTTPError as exc:

            logger.exception(
                "Ollama request failed"
            )

            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

    # ==========================================================
    # Streaming
    # ==========================================================

    async def generate_stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[str, None]:

        endpoint = f"{self.base_url}/api/generate"

        prompt = self._build_prompt(request)

        model = (
            request.model
            or self.default_model
        )

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:

            async with httpx.AsyncClient(
                timeout=600.0
            ) as client:

                async with client.stream(
                    "POST",
                    endpoint,
                    json=payload,
                ) as response:

                    response.raise_for_status()

                    async for line in response.aiter_lines():

                        if not line:
                            continue

                        data = json.loads(line)

                        chunk = data.get(
                            "response",
                            "",
                        )

                        if chunk:
                            yield chunk

        except httpx.HTTPError as exc:

            logger.exception(
                "Ollama streaming failed"
            )

            raise RuntimeError(
                f"Ollama streaming failed: {exc}"
            ) from exc

    # ==========================================================
    # Models
    # ==========================================================

    async def list_models(
        self,
    ) -> list[ModelInfo]:

        try:

            async with httpx.AsyncClient(
                timeout=10.0
            ) as client:

                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

                data = response.json()

            return [
                ModelInfo(
                    provider=self.config.provider,
                    model_name=model["name"],
                    supports_stream=True,
                    supports_json=False,
                    context_window=None,
                )
                for model in data.get(
                    "models",
                    []
                )
            ]

        except httpx.HTTPError as exc:

            logger.exception(
                "Failed to list Ollama models"
            )

            raise RuntimeError(
                f"Failed to list Ollama models: {exc}"
            ) from exc

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
    ) -> bool:

        try:

            async with httpx.AsyncClient(
                timeout=5.0
            ) as client:

                response = await client.get(
                    f"{self.base_url}/"
                )

                return response.status_code == 200

        except Exception:

            return False