from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
)

from fastapi.responses import StreamingResponse

from src.bootstrap import create_llm_service

from src.modules.llm.application.mapper import (
    ApplicationMapper,
)

from src.modules.llm.application.services import (
    LLMService,
)

from src.modules.llm.domain.value_objects import (
    ProviderName,
)

from src.modules.llm.interfaces.schemas import (
    GenerateRequestSchema,
    GenerateResponseSchema,
    EmbeddingRequestSchema,
    EmbeddingResponseSchema,
    VisionRequestSchema,
    VisionResponseSchema,
)

router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


def get_llm_service() -> LLMService:
    return create_llm_service()


# ==========================================================
# Chat
# ==========================================================

@router.post(
    "/generate",
    response_model=GenerateResponseSchema,
)
async def generate(
    request: GenerateRequestSchema,
    service: LLMService = Depends(get_llm_service),
):

    domain_request = ApplicationMapper.to_domain(
        request,
    )

    response = await service.generate(
        domain_request,
    )

    return ApplicationMapper.to_response(
        response,
    )


# ==========================================================
# Stream
# ==========================================================

@router.post("/stream")
async def stream(
    request: GenerateRequestSchema,
    service: LLMService = Depends(get_llm_service),
):

    domain_request = ApplicationMapper.to_domain(
        request,
    )

    async def generator():
        async for chunk in service.generate_stream(
            domain_request,
        ):
            yield chunk

    return StreamingResponse(
        generator(),
        media_type="text/plain",
    )


# ==========================================================
# Embeddings
# ==========================================================

@router.post(
    "/embed",
    response_model=EmbeddingResponseSchema,
)
async def embed(
    request: EmbeddingRequestSchema,
    provider: ProviderName,
    service: LLMService = Depends(get_llm_service),
):

    domain_request = ApplicationMapper.to_embedding_domain(
        request,
    )

    response = await service.embed(
        provider,
        domain_request,
    )

    return ApplicationMapper.to_embedding_response(
        response,
    )


# ==========================================================
# Vision
# ==========================================================

@router.post(
    "/vision",
    response_model=VisionResponseSchema,
)
async def vision(
    provider: ProviderName = Form(...),
    model: str = Form(...),
    prompt: str = Form(...),
    max_tokens: int = Form(1024),
    image: UploadFile = File(...),
    service: LLMService = Depends(get_llm_service),
):

    image_bytes = await image.read()

    mime_type = image.content_type or "image/jpeg"

    request = VisionRequestSchema(
        provider=provider,
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
    )

    domain_request = ApplicationMapper.to_vision_domain(
        dto=request,
        image=image_bytes,
        mime_type=mime_type,
    )

    response = await service.vision(
        domain_request,
    )

    return ApplicationMapper.to_vision_response(
        response,
    )


# ==========================================================
# Models
# ==========================================================

@router.get("/models")
async def list_models(
    provider: ProviderName,
    service: LLMService = Depends(get_llm_service),
):

    return await service.list_models(
        provider,
    )


# ==========================================================
# Health
# ==========================================================

@router.get("/health")
async def health_check(
    provider: ProviderName,
    service: LLMService = Depends(get_llm_service),
):

    return {
        "healthy": await service.health_check(
            provider,
        )
    }