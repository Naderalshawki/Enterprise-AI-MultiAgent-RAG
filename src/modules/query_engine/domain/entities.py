from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.modules.query_engine.domain.enums import (
    QueryExecutionMode,
    QueryIntent,
    QueryPriority,
    QuerySource,
    QueryStatus,
)


# ============================================================
# Query Request
# ============================================================

@dataclass(slots=True)
class QueryRequest:
    """
    يمثل طلب الاستعلام القادم من المستخدم.

    يحتوي على:
        - السؤال
        - هوية المستخدم
        - الجلسة
        - المحادثة
        - Metadata إضافية
        - معرف الاستعلام
        - وقت إنشاء الطلب
    """

    question: str

    user_id: str | None = None

    session_id: str | None = None

    conversation_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    query_id: UUID = field(
        default_factory=uuid4
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """
        التحقق من صحة QueryRequest.
        """

        if not isinstance(self.question, str):
            raise TypeError(
                "Query question must be a string."
            )

        self.question = self.question.strip()

        if not self.question:
            raise ValueError(
                "Query question cannot be empty."
            )

        if len(self.question) > 4000:
            raise ValueError(
                "Query question cannot exceed 4000 characters."
            )

        if self.user_id is not None:
            self.user_id = self.user_id.strip()

        if self.session_id is not None:
            self.session_id = self.session_id.strip()

        if self.conversation_id is not None:
            self.conversation_id = self.conversation_id.strip()

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )


# ============================================================
# Query Context
# ============================================================

@dataclass(slots=True)
class QueryContext:
    """
    يمثل السياق الداخلي الذي يستخدمه Query Engine
    أثناء معالجة الاستعلام.
    """

    request: QueryRequest

    intent: QueryIntent = QueryIntent.UNKNOWN

    source: QuerySource = QuerySource.CHAT_DATABASE

    execution_mode: QueryExecutionMode = (
        QueryExecutionMode.SYNC
    )

    priority: QueryPriority = QueryPriority.NORMAL

    status: QueryStatus = QueryStatus.PENDING

    schema_context: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    error: str | None = None

    # ========================================================
    # Lifecycle
    # ========================================================

    def start_planning(self) -> None:
        """
        نقل الاستعلام إلى مرحلة التخطيط.
        """

        if self.is_terminal:
            raise RuntimeError(
                "Cannot start planning a terminal query."
            )

        self.status = QueryStatus.PLANNING

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

    # ========================================================

    def start(self) -> None:
        """
        بدء تنفيذ الاستعلام.
        """

        if self.is_terminal:
            raise RuntimeError(
                "Cannot start a terminal query."
            )

        self.status = QueryStatus.EXECUTING

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

        self.error = None

    # ========================================================

    def mark_completed(self) -> None:
        """
        إنهاء الاستعلام بنجاح.
        """

        if self.status == QueryStatus.CANCELLED:
            raise RuntimeError(
                "Cancelled query cannot be completed."
            )

        self.status = QueryStatus.COMPLETED

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

        self.completed_at = datetime.now(timezone.utc)

        self.error = None

    # ========================================================

    def mark_failed(
        self,
        error: str,
    ) -> None:
        """
        إنهاء الاستعلام بحالة فشل.
        """

        self.status = QueryStatus.FAILED

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

        self.completed_at = datetime.now(timezone.utc)

        self.error = str(error)

    # ========================================================

    def cancel(
        self,
        reason: str | None = None,
    ) -> None:
        """
        إلغاء الاستعلام.
        """

        if self.is_terminal:
            raise RuntimeError(
                "Cannot cancel a terminal query."
            )

        self.status = QueryStatus.CANCELLED

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

        self.completed_at = datetime.now(timezone.utc)

        self.error = reason

    # ========================================================
    # Properties
    # ========================================================

    @property
    def is_terminal(self) -> bool:
        """
        هل وصل الاستعلام إلى حالة نهائية؟
        """

        return self.status in {
            QueryStatus.COMPLETED,
            QueryStatus.FAILED,
            QueryStatus.CANCELLED,
        }

    # ========================================================

    @property
    def is_successful(self) -> bool:
        """
        هل تم تنفيذ الاستعلام بنجاح؟
        """

        return self.status == QueryStatus.COMPLETED

    # ========================================================

    @property
    def duration_ms(self) -> float | None:
        """
        حساب مدة تنفيذ الاستعلام بالـ milliseconds.
        """

        if self.started_at is None:
            return None

        end_time = (
            self.completed_at
            or datetime.now(timezone.utc)
        )

        return (
            end_time - self.started_at
        ).total_seconds() * 1000


# ============================================================
# Query Result
# ============================================================

@dataclass(slots=True)
class QueryResult:
    """
    يمثل النتيجة النهائية التي يرجعها Query Engine.
    """

    success: bool

    answer: str = ""

    rows: list[dict[str, Any]] = field(
        default_factory=list
    )

    row_count: int = 0

    sql: str | None = None

    execution_time_ms: float | None = None

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    query_id: UUID | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ========================================================
    # Properties
    # ========================================================

    @property
    def has_rows(self) -> bool:
        return bool(self.rows)

    # ========================================================

    @property
    def is_empty(self) -> bool:
        return not self.rows

    # ========================================================
    # Metadata
    # ========================================================

    def add_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        إضافة قيمة إلى Metadata.
        """

        if not key or not key.strip():
            raise ValueError(
                "Metadata key cannot be empty."
            )

        self.metadata[key.strip()] = value

    # ========================================================
    # Serialization
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        تحويل QueryResult إلى Dictionary.
        """

        return {
            "success": self.success,
            "answer": self.answer,
            "rows": self.rows,
            "row_count": self.row_count,
            "sql": self.sql,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "metadata": self.metadata,
            "query_id": (
                str(self.query_id)
                if self.query_id is not None
                else None
            ),
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# Query Execution
# ============================================================

@dataclass(slots=True)
class QueryExecution:
    """
    يمثل عملية تنفيذ Query واحدة داخل Query Engine.
    """

    query_id: UUID = field(
        default_factory=uuid4
    )

    status: QueryStatus = QueryStatus.PENDING

    source: QuerySource = QuerySource.CHAT_DATABASE

    intent: QueryIntent = QueryIntent.UNKNOWN

    execution_mode: QueryExecutionMode = (
        QueryExecutionMode.SYNC
    )

    priority: QueryPriority = QueryPriority.NORMAL

    attempt: int = 0

    max_attempts: int = 1

    started_at: datetime | None = None

    completed_at: datetime | None = None

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    # ========================================================
    # Lifecycle
    # ========================================================

    def start(self) -> None:
        """
        بدء عملية التنفيذ.
        """

        if self.is_terminal:
            raise RuntimeError(
                "Cannot start a terminal query execution."
            )

        if self.attempt >= self.max_attempts:
            raise RuntimeError(
                "Maximum execution attempts reached."
            )

        self.attempt += 1

        self.status = QueryStatus.EXECUTING

        self.started_at = datetime.now(timezone.utc)

        self.completed_at = None

        self.error = None

    # ========================================================

    def mark_completed(self) -> None:
        """
        تسجيل نجاح عملية التنفيذ.
        """

        if self.status == QueryStatus.CANCELLED:
            raise RuntimeError(
                "Cancelled execution cannot be completed."
            )

        self.status = QueryStatus.COMPLETED

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

        self.completed_at = datetime.now(timezone.utc)

        self.error = None

    # ========================================================

    def mark_failed(
        self,
        error: str,
    ) -> None:
        """
        تسجيل فشل عملية التنفيذ.
        """

        self.status = QueryStatus.FAILED

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

        self.completed_at = datetime.now(timezone.utc)

        self.error = str(error)

    # ========================================================

    def cancel(
        self,
        reason: str | None = None,
    ) -> None:
        """
        إلغاء عملية التنفيذ.
        """

        if self.is_terminal:
            raise RuntimeError(
                "Cannot cancel a terminal execution."
            )

        self.status = QueryStatus.CANCELLED

        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

        self.completed_at = datetime.now(timezone.utc)

        self.error = reason

    # ========================================================
    # Properties
    # ========================================================

    @property
    def is_completed(self) -> bool:
        return self.status == QueryStatus.COMPLETED

    # ========================================================

    @property
    def is_failed(self) -> bool:
        return self.status == QueryStatus.FAILED

    # ========================================================

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            QueryStatus.COMPLETED,
            QueryStatus.FAILED,
            QueryStatus.CANCELLED,
        }

    # ========================================================

    @property
    def can_retry(self) -> bool:
        return (
            self.status == QueryStatus.FAILED
            and self.attempt < self.max_attempts
        )