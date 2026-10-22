from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ==========================================================
# Request DTO
# ==========================================================

@dataclass(slots=True)
class AskDatabaseRequest:
    """
    Request received from the Query Engine.
    """

    question: str

    user_id: str | None = None

    session_id: str | None = None

    conversation_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


# ==========================================================
# Response DTO
# ==========================================================

@dataclass(slots=True)
class AskDatabaseResponse:
    """
    Response returned to the Query Engine.
    """

    success: bool

    answer: str

    sql: str | None = None

    rows: list[dict[str, Any]] = field(
        default_factory=list,
    )

    row_count: int = 0

    execution_time_ms: float | None = None

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )