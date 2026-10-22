from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


# ==========================================================
# Request
# ==========================================================

class AskDatabaseRequestSchema(BaseModel):
    """
    API request schema.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural language question.",
    )

    user_id: str | None = None

    session_id: str | None = None

    conversation_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# ==========================================================
# Response
# ==========================================================

class AskDatabaseResponseSchema(BaseModel):
    """
    API response schema.
    """

    success: bool

    answer: str

    sql: str | None = None

    rows: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    row_count: int = 0

    execution_time_ms: float | None = None

    error: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    model_config = ConfigDict(
        extra="ignore",
    )


# ==========================================================
# Health
# ==========================================================

class ChatDatabaseHealthSchema(BaseModel):
    """
    Health check response.
    """

    status: str

    database: str

    llm: str

    version: str

    model_config = ConfigDict(
        extra="ignore",
    )