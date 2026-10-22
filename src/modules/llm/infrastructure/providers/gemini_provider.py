
# import logging
# from typing import AsyncGenerator

# from google import genai
# from google.genai import types

# from src.modules.llm.domain.entities import (
#     LLMRequest,
#     LLMResponse,
#     ModelInfo,
#     EmbeddingRequest,
#     EmbeddingResponse,
#     VisionRequest,
#     VisionResponse,
# )

# from src.modules.llm.domain.value_objects import (
#     AICapability,
#     ProviderName,
# )

# from src.modules.llm.infrastructure.providers.base_provider import (
#     BaseProvider,
# )

# from src.modules.llm.infrastructure.config.provider_config import (
#     ProviderConfig,
# )

# from src.modules.llm.infrastructure.mappers.request_mapper import (
#     RequestMapper,
# )

# from src.modules.llm.infrastructure.mappers.response_mapper import (
#     ResponseMapper,
# )


# logger = logging.getLogger(__name__)


# class GeminiProvider(BaseProvider):
#     """
#     Google Gemini Provider
#     """

#     capabilities = {
#         AICapability.CHAT,
#         AICapability.EMBEDDING,
#         AICapability.VISION,
#     }

#     def __init__(
#         self,
#         config: ProviderConfig,
#     ):
#         super().__init__(config)

#         self.client = genai.Client(
#             api_key=config.api_key,
#         )

#     # ==========================================================
#     # Chat
#     # ==========================================================

#     async def generate(
#         self,
#         request: LLMRequest,
#     ) -> LLMResponse:

#         prompt = RequestMapper.to_gemini_prompt(
#             request,
#         )

#         logger.info(
#             "[Gemini] Generating content | model=%s",
#             request.model,
#         )

#         try:
#             response = await self.client.aio.models.generate_content(
#                 model=request.model,
#                 contents=prompt,
#             )

#             return ResponseMapper.from_gemini(
#                 response=response,
#                 model=request.model,
#             )

#         except Exception:
#             logger.exception(
#                 "[Gemini] Generation failed | model=%s",
#                 request.model,
#             )
#             raise

#     # ==========================================================
#     # Stream
#     # ==========================================================

#     async def generate_stream(
#         self,
#         request: LLMRequest,
#     ) -> AsyncGenerator[str, None]:

#         prompt = RequestMapper.to_gemini_prompt(
#             request,
#         )

#         logger.info(
#             "[Gemini] Starting stream | model=%s",
#             request.model,
#         )

#         try:
#             stream = await (
#                 self.client.aio.models.generate_content_stream(
#                     model=request.model,
#                     contents=prompt,
#                 )
#             )

#             async for chunk in stream:
#                 if getattr(chunk, "text", None):
#                     yield chunk.text

#         except Exception:
#             logger.exception(
#                 "[Gemini] Stream failed | model=%s",
#                 request.model,
#             )
#             raise

#     # ==========================================================
#     # Vision
#     # ==========================================================

#     async def vision(
#         self,
#         request: VisionRequest,
#     ) -> VisionResponse:

#         image_part = types.Part.from_bytes(
#             data=request.image,
#             mime_type=request.mime_type,
#         )

#         logger.info(
#             "[Gemini] Processing vision request | model=%s",
#             request.model,
#         )

#         try:
#             response = await self.client.aio.models.generate_content(
#                 model=request.model,
#                 contents=[
#                     image_part,
#                     request.prompt,
#                 ],
#             )

#             return ResponseMapper.from_gemini_vision(
#                 response=response,
#                 model=request.model,
#             )

#         except Exception:
#             logger.exception(
#                 "[Gemini] Vision request failed | model=%s",
#                 request.model,
#             )
#             raise

#     # ==========================================================
#     # Embeddings
#     # ==========================================================

#     async def embed(
#         self,
#         request: EmbeddingRequest,
#     ) -> EmbeddingResponse:

#         logger.info(
#             "[Gemini] Generating embeddings | model=%s",
#             request.model,
#         )

#         try:
#             response = await self.client.aio.models.embed_content(
#                 **RequestMapper.to_gemini_embedding_request(
#                     request,
#                 )
#             )

#             return ResponseMapper.from_gemini_embedding(
#                 response=response,
#                 model=request.model,
#             )

#         except Exception:
#             logger.exception(
#                 "[Gemini] Embedding generation failed | model=%s",
#                 request.model,
#             )
#             raise

#     # ==========================================================
#     # Models
#     # ==========================================================

#     async def list_models(
#         self,
#     ) -> list[ModelInfo]:

#         logger.info(
#             "[Gemini] Listing available models"
#         )

#         try:
#             response = await self.client.aio.models.list()

#             models = []

#             for model in response:
#                 models.append(
#                     ModelInfo(
#                         provider=ProviderName.GEMINI,
#                         model_name=model.name,
#                         supports_stream=True,
#                         supports_json=True,
#                         context_window=getattr(
#                             model,
#                             "input_token_limit",
#                             None,
#                         ),
#                     )
#                 )

#             logger.info(
#                 "[Gemini] Models retrieved | count=%d",
#                 len(models),
#             )

#             return models

#         except Exception:
#             logger.exception(
#                 "[Gemini] Failed to list models"
#             )
#             raise

#     # ==========================================================
#     # Health
#     # ==========================================================

#     async def health_check(
#         self,
#     ) -> bool:

#         model = self.config.default_model

#         try:
#             logger.info(
#                 "[Gemini] Health check | model=%s",
#                 model,
#             )

#             await self.client.aio.models.generate_content(
#                 model=model,
#                 contents="Hello",
#             )

#             logger.info(
#                 "[Gemini] Health check succeeded | model=%s",
#                 model,
#             )

#             return True

#         except Exception:
#             logger.exception(
#                 "[Gemini] Health check failed | model=%s",
#                 model,
#             )

#             return False











import logging
from typing import AsyncGenerator

from google import genai
from google.genai import types

from src.modules.llm.domain.entities import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    EmbeddingRequest,
    EmbeddingResponse,
    VisionRequest,
    VisionResponse,
)

from src.modules.llm.domain.value_objects import (
    AICapability,
    ProviderName,
)

from src.modules.llm.infrastructure.providers.base_provider import (
    BaseProvider,
)

from src.modules.llm.infrastructure.config.provider_config import (
    ProviderConfig,
)

from src.modules.llm.infrastructure.mappers.request_mapper import (
    RequestMapper,
)

from src.modules.llm.infrastructure.mappers.response_mapper import (
    ResponseMapper,
)


logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """
    Google Gemini Provider
    """

    capabilities = {
        AICapability.CHAT,
        AICapability.EMBEDDING,
        AICapability.VISION,
    }

    def __init__(
        self,
        config: ProviderConfig,
    ):
        super().__init__(config)

        self.client = genai.Client(
            api_key=config.api_key,
        )

    # ==========================================================
    # Chat
    # ==========================================================

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        prompt = RequestMapper.to_gemini_prompt(
            request,
        )

        logger.info(
            "[Gemini] Generating content | model=%s",
            request.model,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=request.model,
                contents=prompt,
            )

            return ResponseMapper.from_gemini(
                response=response,
                model=request.model,
            )

        except Exception:
            logger.exception(
                "[Gemini] Generation failed | model=%s",
                request.model,
            )
            raise

    # ==========================================================
    # Stream
    # ==========================================================

    async def generate_stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[str, None]:

        prompt = RequestMapper.to_gemini_prompt(
            request,
        )

        logger.info(
            "[Gemini] Starting stream | model=%s",
            request.model,
        )

        try:
            stream = await (
                self.client.aio.models.generate_content_stream(
                    model=request.model,
                    contents=prompt,
                )
            )

            async for chunk in stream:
                if getattr(chunk, "text", None):
                    yield chunk.text

        except Exception:
            logger.exception(
                "[Gemini] Stream failed | model=%s",
                request.model,
            )
            raise

    # ==========================================================
    # Vision
    # ==========================================================

    async def vision(
        self,
        request: VisionRequest,
    ) -> VisionResponse:

        image_part = types.Part.from_bytes(
            data=request.image,
            mime_type=request.mime_type,
        )

        logger.info(
            "[Gemini] Processing vision request | model=%s",
            request.model,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=request.model,
                contents=[
                    image_part,
                    request.prompt,
                ],
            )

            return ResponseMapper.from_gemini_vision(
                response=response,
                model=request.model,
            )

        except Exception:
            logger.exception(
                "[Gemini] Vision request failed | model=%s",
                request.model,
            )
            raise

    # ==========================================================
    # Embeddings
    # ==========================================================

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:

        logger.info(
            "[Gemini] Generating embeddings | model=%s",
            request.model,
        )

        try:
            response = await self.client.aio.models.embed_content(
                **RequestMapper.to_gemini_embedding_request(
                    request,
                )
            )

            return ResponseMapper.from_gemini_embedding(
                response=response,
                model=request.model,
            )

        except Exception:
            logger.exception(
                "[Gemini] Embedding generation failed | model=%s",
                request.model,
            )
            raise

    # ==========================================================
    # Models
    # ==========================================================

    async def list_models(
        self,
    ) -> list[ModelInfo]:

        logger.info(
            "[Gemini] Listing available models"
        )

        try:
            response = await self.client.aio.models.list()

            models = []

            for model in response:
                models.append(
                    ModelInfo(
                        provider=ProviderName.GEMINI,
                        model_name=model.name,
                        supports_stream=True,
                        supports_json=True,
                        context_window=getattr(
                            model,
                            "input_token_limit",
                            None,
                        ),
                    )
                )

            logger.info(
                "[Gemini] Models retrieved | count=%d",
                len(models),
            )

            return models

        except Exception:
            logger.exception(
                "[Gemini] Failed to list models"
            )
            raise

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
    ) -> bool:

        model = self.config.default_model

        try:
            logger.info(
                "[Gemini] Health check | model=%s",
                model,
            )

            await self.client.aio.models.generate_content(
                model=model,
                contents="Hello",
            )

            logger.info(
                "[Gemini] Health check succeeded | model=%s",
                model,
            )

            return True

        except Exception:
            logger.exception(
                "[Gemini] Health check failed | model=%s",
                model,
            )

            return False
