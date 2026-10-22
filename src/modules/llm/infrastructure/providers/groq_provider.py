
# import json
# import logging
# from typing import AsyncGenerator

# import httpx

# from src.modules.llm.domain.entities import (
#     LLMRequest,
#     LLMResponse,
#     TokenUsage,
#     ModelInfo,
# )
# from src.modules.llm.domain.value_objects import AICapability
# from src.modules.llm.infrastructure.config.provider_config import ProviderConfig
# from src.modules.llm.infrastructure.providers.base_provider import BaseProvider


# logger = logging.getLogger(__name__)


# class GroqProvider(BaseProvider):
#     """Groq Cloud AI provider."""

#     capabilities = {
#         AICapability.CHAT,
#         AICapability.STREAMING,
#     }

#     def __init__(self, config: ProviderConfig) -> None:
#         super().__init__(config)

#         self.base_url = (
#             config.base_url or "https://api.groq.com/openai/v1"
#         ).rstrip("/")

#         self.default_model = (
#             config.default_model or "openai/gpt-oss-20b"
#         )

#         self.headers = {
#             "Authorization": f"Bearer {self.config.api_key}",
#             "Content-Type": "application/json",
#         }

#         logger.info(
#             "Initialized Groq provider: model=%s",
#             self.default_model,
#         )

#     def _format_messages(self, request: LLMRequest) -> list[dict]:
#         return [
#             {
#                 "role": message.role.value,
#                 "content": message.content,
#             }
#             for message in request.messages
#         ]

#     async def generate(self, request: LLMRequest) -> LLMResponse:
#         endpoint = f"{self.base_url}/chat/completions"
#         model = request.model or self.default_model

#         payload = {
#             "model": model,
#             "messages": self._format_messages(request),
#             "temperature": request.temperature,
#             "stream": False,
#         }

#         if request.max_tokens:
#             payload["max_tokens"] = request.max_tokens

#         try:
#             async with httpx.AsyncClient(
#                 timeout=self.config.timeout
#             ) as client:
#                 response = await client.post(
#                     endpoint,
#                     headers=self.headers,
#                     json=payload,
#                 )
#                 response.raise_for_status()
#                 data = response.json()

#             choices = data.get("choices") or []
#             if not choices:
#                 raise RuntimeError(
#                     "Groq returned no completion choices."
#                 )

#             usage = data.get("usage") or {}
#             message = choices[0].get("message") or {}

#             return LLMResponse(
#                 content=message.get("content") or "",
#                 provider=self.config.provider,
#                 model=model,
#                 usage=TokenUsage(
#                     prompt_tokens=usage.get("prompt_tokens", 0),
#                     completion_tokens=usage.get("completion_tokens", 0),
#                     total_tokens=usage.get("total_tokens", 0),
#                 ),
#             )

#         except httpx.HTTPStatusError as exc:
#             logger.exception("Groq API returned an HTTP error")
#             raise RuntimeError(
#                 f"Groq API returned HTTP {exc.response.status_code}: "
#                 f"{exc.response.text[:1000]}"
#             ) from exc

#         except httpx.HTTPError as exc:
#             logger.exception("Groq request failed")
#             raise RuntimeError(
#                 f"Groq request failed: {exc}"
#             ) from exc

#     async def generate_stream(
#         self,
#         request: LLMRequest,
#     ) -> AsyncGenerator[str, None]:
#         endpoint = f"{self.base_url}/chat/completions"
#         model = request.model or self.default_model

#         payload = {
#             "model": model,
#             "messages": self._format_messages(request),
#             "temperature": request.temperature,
#             "stream": True,
#         }

#         if request.max_tokens:
#             payload["max_tokens"] = request.max_tokens

#         try:
#             async with httpx.AsyncClient(
#                 timeout=self.config.timeout
#             ) as client:
#                 async with client.stream(
#                     "POST",
#                     endpoint,
#                     headers=self.headers,
#                     json=payload,
#                 ) as response:
#                     response.raise_for_status()

#                     async for line in response.aiter_lines():
#                         if not line.startswith("data:"):
#                             continue

#                         data_line = line[5:].strip()
#                         if not data_line or data_line == "[DONE]":
#                             continue

#                         try:
#                             chunk = json.loads(data_line)
#                         except json.JSONDecodeError:
#                             logger.warning(
#                                 "Ignoring invalid Groq stream chunk"
#                             )
#                             continue

#                         choices = chunk.get("choices") or []
#                         if not choices:
#                             continue

#                         delta = choices[0].get("delta") or {}
#                         content = delta.get("content")

#                         if content:
#                             yield content

#         except httpx.HTTPStatusError as exc:
#             logger.exception("Groq streaming returned an HTTP error")
#             raise RuntimeError(
#                 f"Groq streaming API returned HTTP "
#                 f"{exc.response.status_code}: "
#                 f"{exc.response.text[:1000]}"
#             ) from exc

#         except httpx.HTTPError as exc:
#             logger.exception("Groq streaming failed")
#             raise RuntimeError(
#                 f"Groq streaming failed: {exc}"
#             ) from exc

#     async def list_models(self) -> list[ModelInfo]:
#         endpoint = f"{self.base_url}/models"

#         try:
#             async with httpx.AsyncClient(
#                 timeout=self.config.timeout
#             ) as client:
#                 response = await client.get(
#                     endpoint,
#                     headers=self.headers,
#                 )
#                 response.raise_for_status()
#                 data = response.json()

#             return [
#                 ModelInfo(
#                     provider=self.config.provider,
#                     model_name=item["id"],
#                     supports_stream=True,
#                     supports_json=True,
#                 )
#                 for item in data.get("data", [])
#                 if item.get("id")
#             ]

#         except httpx.HTTPStatusError as exc:
#             logger.exception("Groq model listing returned an HTTP error")
#             raise RuntimeError(
#                 f"Groq models API returned HTTP "
#                 f"{exc.response.status_code}: "
#                 f"{exc.response.text[:1000]}"
#             ) from exc

#         except httpx.HTTPError as exc:
#             logger.exception("Failed to list Groq models")
#             raise RuntimeError(
#                 f"Failed to list Groq models: {exc}"
#             ) from exc

#     async def health_check(self) -> bool:
#         try:
#             async with httpx.AsyncClient(
#                 timeout=self.config.timeout
#             ) as client:
#                 response = await client.get(
#                     f"{self.base_url}/models",
#                     headers=self.headers,
#                 )
#                 response.raise_for_status()
#                 return True

#         except httpx.HTTPError:
#             logger.exception("Groq health check failed")
#             return False




















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
from src.modules.llm.domain.value_objects import AICapability
from src.modules.llm.infrastructure.config.provider_config import ProviderConfig
from src.modules.llm.infrastructure.providers.base_provider import BaseProvider


logger = logging.getLogger(__name__)


class GroqProvider(BaseProvider):
    """Groq Cloud AI provider."""

    capabilities = {
        AICapability.CHAT,
        AICapability.STREAMING,
    }

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)

        self.base_url = (
            config.base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        ).rstrip("/")

        self.default_model = (
            config.default_model or "gemini-3.8-flash"
        )

        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "Initialized Groq provider: model=%s",
            self.default_model,
        )

    def _format_messages(self, request: LLMRequest) -> list[dict]:
        return [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in request.messages
        ]

    async def generate(self, request: LLMRequest) -> LLMResponse:
        endpoint = f"{self.base_url}/chat/completions"
        model = request.model or self.default_model

        payload = {
            "model": model,
            "messages": self._format_messages(request),
            "temperature": request.temperature,
            "stream": False,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout
            ) as client:
                response = await client.post(
                    endpoint,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError(
                    "Groq returned no completion choices."
                )

            usage = data.get("usage") or {}
            message = choices[0].get("message") or {}

            return LLMResponse(
                content=message.get("content") or "",
                provider=self.config.provider,
                model=model,
                usage=TokenUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                ),
            )

        except httpx.HTTPStatusError as exc:
            logger.exception("Groq API returned an HTTP error")
            raise RuntimeError(
                f"Groq API returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:1000]}"
            ) from exc

        except httpx.HTTPError as exc:
            logger.exception("Groq request failed")
            raise RuntimeError(
                f"Groq request failed: {exc}"
            ) from exc

    async def generate_stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[str, None]:
        endpoint = f"{self.base_url}/chat/completions"
        model = request.model or self.default_model

        payload = {
            "model": model,
            "messages": self._format_messages(request),
            "temperature": request.temperature,
            "stream": True,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout
            ) as client:
                async with client.stream(
                    "POST",
                    endpoint,
                    headers=self.headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue

                        data_line = line[5:].strip()
                        if not data_line or data_line == "[DONE]":
                            continue

                        try:
                            chunk = json.loads(data_line)
                        except json.JSONDecodeError:
                            logger.warning(
                                "Ignoring invalid Groq stream chunk"
                            )
                            continue

                        choices = chunk.get("choices") or []
                        if not choices:
                            continue

                        delta = choices[0].get("delta") or {}
                        content = delta.get("content")

                        if content:
                            yield content

        except httpx.HTTPStatusError as exc:
            logger.exception("Groq streaming returned an HTTP error")
            raise RuntimeError(
                f"Groq streaming API returned HTTP "
                f"{exc.response.status_code}: "
                f"{exc.response.text[:1000]}"
            ) from exc

        except httpx.HTTPError as exc:
            logger.exception("Groq streaming failed")
            raise RuntimeError(
                f"Groq streaming failed: {exc}"
            ) from exc

    async def list_models(self) -> list[ModelInfo]:
        endpoint = f"{self.base_url}/models"

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout
            ) as client:
                response = await client.get(
                    endpoint,
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()

            return [
                ModelInfo(
                    provider=self.config.provider,
                    model_name=item["id"],
                    supports_stream=True,
                    supports_json=True,
                )
                for item in data.get("data", [])
                if item.get("id")
            ]

        except httpx.HTTPStatusError as exc:
            logger.exception("Groq model listing returned an HTTP error")
            raise RuntimeError(
                f"Groq models API returned HTTP "
                f"{exc.response.status_code}: "
                f"{exc.response.text[:1000]}"
            ) from exc

        except httpx.HTTPError as exc:
            logger.exception("Failed to list Groq models")
            raise RuntimeError(
                f"Failed to list Groq models: {exc}"
            ) from exc

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout
            ) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True

        except httpx.HTTPError:
            logger.exception("Groq health check failed")
            return False
