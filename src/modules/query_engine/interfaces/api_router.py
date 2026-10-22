from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.modules.query_engine.domain.entities import (
    QueryRequest,
    QueryResult,
)
from src.modules.query_engine.domain.interfaces import (
    QueryEngine,
)


logger = logging.getLogger(__name__)


# ==========================================================
# Request Schema
# ==========================================================


class QueryRequestSchema(BaseModel):
    """
    HTTP request schema for Query Engine.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural-language database query.",
    )

    user_id: str | None = Field(
        default=None,
        description="Authenticated user identifier.",
    )

    session_id: str | None = Field(
        default=None,
        description="Conversation/session identifier.",
    )

    conversation_id: str | None = Field(
        default=None,
        description="Conversation identifier.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional query metadata.",
    )


# ==========================================================
# Response Schema
# ==========================================================


class QueryResultSchema(BaseModel):
    """
    HTTP response schema for Query Engine.
    """

    success: bool

    answer: str | None = None

    rows: list[Any] = Field(
        default_factory=list
    )

    row_count: int = 0

    sql: str | None = None

    execution_time_ms: float | None = None

    error: str | None = None

    query_id: str

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ==========================================================
# Router Factory
# ==========================================================


def create_query_engine_router(
    query_engine: QueryEngine,
) -> APIRouter:
    """
    إنشاء FastAPI Router خاص بـQuery Engine.

    Parameters
    ----------
    query_engine:
        QueryEngine implementation.

    Returns
    -------
    APIRouter
        FastAPI router.
    """

    if query_engine is None:
        raise ValueError(
            "query_engine cannot be None."
        )

    router = APIRouter(
        prefix="/query-engine",
        tags=["Query Engine"],
    )

    # ======================================================
    # Execute Query
    # ======================================================

    @router.post(
        "/execute",
        response_model=QueryResultSchema,
        status_code=status.HTTP_200_OK,
    )
    async def execute_query(
        payload: QueryRequestSchema,
        engine: QueryEngine = Depends(
            lambda: query_engine
        ),
    ) -> QueryResultSchema:
        """
        تنفيذ استعلام باللغة الطبيعية من خلال Query Engine.
        """

        try:

            # ------------------------------------------------
            # HTTP Schema → Domain Entity
            # ------------------------------------------------

            request = QueryRequest(
                question=payload.question,
                user_id=payload.user_id,
                session_id=payload.session_id,
                conversation_id=payload.conversation_id,
                metadata=payload.metadata,
            )

            # ------------------------------------------------
            # Execute Query Engine
            # ------------------------------------------------

            result = await engine.execute(
                request
            )

            # ------------------------------------------------
            # Domain Result → HTTP Schema
            # ------------------------------------------------

            return _to_response_schema(
                result
            )

        except ValueError as exc:

            logger.warning(
                "[QueryEngine API] Invalid request | "
                "error=%s",
                str(exc),
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        except Exception as exc:

            logger.exception(
                "[QueryEngine API] "
                "Unexpected error."
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "An unexpected error occurred "
                    "while executing the query."
                ),
            ) from exc

    # ======================================================
    # Health Check
    # ======================================================

    @router.get(
        "/health",
    )
    async def health_check(
        engine: QueryEngine = Depends(
            lambda: query_engine
        ),
    ) -> dict[str, Any]:
        """
        فحص حالة Query Engine.
        """

        try:

            # QueryEngine interface قد لا تحتوي health_check
            # لذلك نتحقق من وجودها قبل الاستدعاء.

            health_method = getattr(
                engine,
                "health_check",
                None,
            )

            if health_method is None:
                return {
                    "status": "healthy",
                    "service": "query-engine",
                }

            return await health_method()

        except Exception as exc:

            logger.exception(
                "[QueryEngine API] "
                "Health check failed."
            )

            return {
                "status": "unhealthy",
                "service": "query-engine",
                "error": str(exc),
            }

    return router


# ==========================================================
# Response Mapper
# ==========================================================


def _to_response_schema(
    result: QueryResult,
) -> QueryResultSchema:
    """
    تحويل QueryResult من Domain إلى API Response.
    """

    return QueryResultSchema(
        success=result.success,
        answer=result.answer,
        rows=result.rows,
        row_count=result.row_count,
        sql=result.sql,
        execution_time_ms=result.execution_time_ms,
        error=result.error,
        query_id=str(result.query_id),
        metadata=result.metadata,
    )