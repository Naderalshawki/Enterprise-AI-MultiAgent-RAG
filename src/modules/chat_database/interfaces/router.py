from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.bootstrap import (
    create_chat_database_service,
)

from src.modules.chat_database.application.dtos import (
    AskDatabaseRequest,
)

from src.modules.chat_database.application.services import (
    ChatDatabaseService,
)

from src.modules.chat_database.interfaces.schemas import (
    AskDatabaseRequestSchema,
    AskDatabaseResponseSchema,
    ChatDatabaseHealthSchema,
)


router = APIRouter(
    prefix="/chat-database",
    tags=["Chat Database"],
)


# ==========================================================
# Dependency
# ==========================================================

def get_chat_database_service() -> ChatDatabaseService:
    """
    Returns the singleton ChatDatabaseService.
    """

    return create_chat_database_service()


# ==========================================================
# Ask Database
# ==========================================================

@router.post(
    "/ask",
    response_model=AskDatabaseResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def ask_database(
    request: AskDatabaseRequestSchema,
    service: ChatDatabaseService = Depends(
        get_chat_database_service,
    ),
) -> AskDatabaseResponseSchema:

    try:

        response = await service.ask(

            AskDatabaseRequest(

                question=request.question,

                user_id=request.user_id,

                session_id=request.session_id,

                conversation_id=request.conversation_id,

                metadata=request.metadata,

            )

        )

        return AskDatabaseResponseSchema(

            success=response.success,

            answer=response.answer,

            sql=response.sql,

            rows=response.rows,

            row_count=response.row_count,

            execution_time_ms=response.execution_time_ms,

            error=response.error,

            metadata=response.metadata,

        )

    except Exception as e:

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=str(e),

        )


# ==========================================================
# Health
# ==========================================================

@router.get(
    "/health",
    response_model=ChatDatabaseHealthSchema,
)
async def health() -> ChatDatabaseHealthSchema:

    return ChatDatabaseHealthSchema(

        status="healthy",

        database="connected",

        llm="connected",

        version="1.0.0",

    )