from __future__ import annotations

from pydantic import BaseModel, Field

from src.modules.memory.domain.value_objects import (
    MemoryImportance,
    MemoryType,
)


class SaveMemoryRequest(BaseModel):
    user_id: str | None = None
    session_id: str | None = None

    content: str = Field(..., min_length=1)

    memory_type: MemoryType = MemoryType.CONVERSATION
    importance: MemoryImportance = MemoryImportance.MEDIUM

    metadata: dict = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    user_id: str | None = None
    session_id: str | None = None

    query: str | None = None

    limit: int = Field(default=10, ge=1, le=100)