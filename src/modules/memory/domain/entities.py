from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.modules.memory.domain.value_objects import (
    MemoryImportance,
    MemoryType,
)


@dataclass(slots=True)
class Memory:
    id: UUID = field(default_factory=uuid4)

    user_id: str | None = None

    session_id: str | None = None

    content: str = ""

    memory_type: MemoryType = MemoryType.CONVERSATION

    importance: MemoryImportance = MemoryImportance.MEDIUM

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )