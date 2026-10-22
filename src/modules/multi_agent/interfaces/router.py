from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from pydantic import BaseModel, Field

from src.bootstrap import (
    create_agent_service,
)


router = APIRouter(
    prefix="/bi-agent",
    tags=["AI BI Platform Agent"],
)


# ==========================================================
# Request Schema
# ==========================================================

class BIRequestSchema(BaseModel):
    """
    طلب Multi-Agent.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    session_id: str = (
        "default-session"
    )

    user_id: str = (
        "default-user"
    )


# ==========================================================
# Endpoint
# ==========================================================

@router.post(
    "/ask",
    status_code=status.HTTP_200_OK,
)
async def ask_bi_agent(
    request: BIRequestSchema,
):

    try:

        # ------------------------------------------------------
        # Use Bootstrap Singleton
        # ------------------------------------------------------

        agent_service = (
            create_agent_service()
        )

        # ------------------------------------------------------
        # Process
        # ------------------------------------------------------

        context = await (
            agent_service.process_question(
                question=request.question,
                user_id=request.user_id,
                session_id=request.session_id,
            )
        )

        # ------------------------------------------------------
        # Failure
        # ------------------------------------------------------

        if not context.success:

            return {
                "success": False,

                "errors": context.errors,

                "metadata": context.metadata,
            }

        # ------------------------------------------------------
        # Success
        # ------------------------------------------------------

        return {
            "success": True,

            "final_report": (
                context.final_report
            ),

            "sql_used": (
                context.sql_query
            ),

            "raw_data": (
                context.raw_data
            ),

            "source_type": (
                context.source_type
            ),

            "selected_sources": (
                context.selected_sources
            ),

            "metadata": context.metadata,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc