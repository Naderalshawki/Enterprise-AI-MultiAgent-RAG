from src.modules.llm.domain.entities import (
    LLMRequest,
    EmbeddingRequest,
    VisionRequest,
)


class RequestMapper:

    # ==========================================================
    # OpenAI Compatible Chat
    # ==========================================================

    @staticmethod
    def to_openai_messages(
        request: LLMRequest,
    ) -> list[dict]:

        return [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in request.messages
        ]

    # ==========================================================
    # Gemini Prompt
    # ==========================================================

    @staticmethod
    def to_gemini_prompt(
        request: LLMRequest,
    ) -> str:

        return "\n".join(
            message.content
            for message in request.messages
        )

    # ==========================================================
    # OpenAI Compatible Vision
    # ==========================================================

    @staticmethod
    def to_openai_vision_messages(
        request: VisionRequest,
    ) -> list[dict]:

        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": request.prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": request.image,
                        },
                    },
                ],
            }
        ]

    # ==========================================================
    # Gemini Vision
    # ==========================================================

    @staticmethod
    def to_gemini_vision_prompt(
        request: VisionRequest,
    ) -> dict:

        return {
            "image": request.image,
            "prompt": request.prompt,
        }

    # ==========================================================
    # OpenAI Compatible Embeddings
    # ==========================================================

    @staticmethod
    def to_openai_embedding_request(
        request: EmbeddingRequest,
    ) -> dict:

        data = {
            "model": request.model,
            "input": request.input,
        }

        if request.dimensions is not None:
            data["dimensions"] = request.dimensions

        if request.encoding_format:
            data["encoding_format"] = request.encoding_format

        if request.user:
            data["user"] = request.user

        return data

    # ==========================================================
    # Gemini Embeddings
    # ==========================================================

    @staticmethod
    def to_gemini_embedding_request(
        request: EmbeddingRequest,
    ) -> dict:

        return {
            "model": request.model,
            "contents": request.input,
        }