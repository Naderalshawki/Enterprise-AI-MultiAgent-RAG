from fastapi import APIRouter

from src.modules.memory.application.dtos import SaveMemoryRequest


router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)


@router.post("/")
async def save_memory(request: SaveMemoryRequest):

    return {
        "message": "Memory endpoint is ready",
        "content": request.content,
    }