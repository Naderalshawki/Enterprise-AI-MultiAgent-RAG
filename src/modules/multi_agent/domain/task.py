from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class TaskStatus(str, Enum):
    """
    حالة تنفيذ المهمة داخل Multi-Agent pipeline.
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class Task(BaseModel):
    """
    يمثل مهمة واحدة ضمن خطة تنفيذ Multi-Agent.

    المسؤوليات:
        - تعريف المهمة.
        - تحديد الأداة التي ستنفذها.
        - تخزين المدخلات.
        - تتبع حالة التنفيذ.
        - حفظ النتيجة.
        - حفظ الخطأ عند الفشل.
        - تتبع عدد المحاولات.
        - تسجيل أوقات التنفيذ.

    Task لا ينفذ الأداة بنفسه.
    التنفيذ الفعلي مسؤولية TaskExecutor.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=False,
    )

    # ==========================================================
    # Identity
    # ==========================================================

    id: str = Field(
        ...,
        min_length=1,
        description="المعرف الفريد للمهمة.",
    )

    name: str = Field(
        ...,
        min_length=1,
        description="اسم المهمة.",
    )

    description: str = Field(
        ...,
        min_length=1,
        description="وصف المهمة وما المطلوب تنفيذُه.",
    )

    # ==========================================================
    # Tool
    # ==========================================================

    tool_name: str = Field(
        ...,
        min_length=1,
        description="اسم الأداة المسؤولة عن تنفيذ المهمة.",
    )

    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="المدخلات المطلوبة للأداة.",
    )

    # ==========================================================
    # Execution State
    # ==========================================================

    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="الحالة الحالية للمهمة.",
    )

    result: Any | None = Field(
        default=None,
        description="نتيجة تنفيذ المهمة.",
    )

    error: str | None = Field(
        default=None,
        description="رسالة الخطأ في حال فشل المهمة.",
    )

    # ==========================================================
    # Retry / Execution Tracking
    # ==========================================================

    attempts: int = Field(
        default=0,
        ge=0,
        description="عدد محاولات تنفيذ المهمة.",
    )

    max_attempts: int = Field(
        default=2,
        ge=1,
        le=10,
        description="الحد الأقصى لمحاولات التنفيذ.",
    )

    # ==========================================================
    # Time Tracking
    # ==========================================================

    started_at: datetime | None = Field(
        default=None,
        description="وقت بدء التنفيذ.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="وقت انتهاء التنفيذ بنجاح أو فشل.",
    )

    # ==========================================================
    # Dependencies / Metadata
    # ==========================================================

    depends_on: list[str] = Field(
        default_factory=list,
        description="معرفات المهام التي يجب إكمالها قبل هذه المهمة.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="بيانات إضافية مرتبطة بالمهمة.",
    )

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def start(self) -> None:
        """
        بدء تنفيذ المهمة.

        يزيد عداد المحاولات ويغير الحالة إلى IN_PROGRESS.
        """

        if self.status == TaskStatus.COMPLETED:
            return

        if self.status == TaskStatus.SKIPPED:
            return

        if self.attempts >= self.max_attempts:
            raise RuntimeError(
                f"Task '{self.id}' exceeded maximum attempts."
            )

        self.status = TaskStatus.IN_PROGRESS
        self.attempts += 1
        self.started_at = datetime.now(timezone.utc)
        self.completed_at = None
        self.error = None

    # ==========================================================
    # Completion
    # ==========================================================

    def mark_completed(
        self,
        result: Any = None,
    ) -> None:
        """
        تحديد المهمة كمكتملة وحفظ النتيجة.
        """

        self.status = TaskStatus.COMPLETED
        self.result = result
        self.error = None
        self.completed_at = datetime.now(timezone.utc)

    # ==========================================================
    # Failure
    # ==========================================================

    def mark_failed(
        self,
        error: str,
    ) -> None:
        """
        تحديد المهمة كفاشلة وحفظ الخطأ.

        لا تعيد المحاولة هنا؛
        قرار إعادة المحاولة مسؤولية TaskExecutor.
        """

        self.status = TaskStatus.FAILED
        self.error = error
        self.result = None
        self.completed_at = datetime.now(timezone.utc)

    # ==========================================================
    # Skip
    # ==========================================================

    def mark_skipped(
        self,
        reason: str | None = None,
    ) -> None:
        """
        تخطي المهمة بدون اعتبارها نجاحًا.
        """

        self.status = TaskStatus.SKIPPED
        self.error = reason
        self.completed_at = datetime.now(timezone.utc)

    # ==========================================================
    # State Helpers
    # ==========================================================

    @property
    def is_pending(self) -> bool:
        """
        هل المهمة لم تبدأ بعد؟
        """

        return self.status == TaskStatus.PENDING

    @property
    def is_running(self) -> bool:
        """
        هل المهمة قيد التنفيذ؟
        """

        return self.status == TaskStatus.IN_PROGRESS

    @property
    def is_completed(self) -> bool:
        """
        هل المهمة اكتملت بنجاح؟
        """

        return self.status == TaskStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """
        هل المهمة فشلت؟
        """

        return self.status == TaskStatus.FAILED

    @property
    def is_skipped(self) -> bool:
        """
        هل تم تخطي المهمة؟
        """

        return self.status == TaskStatus.SKIPPED

    @property
    def is_terminal(self) -> bool:
        """
        هل وصلت المهمة إلى حالة نهائية؟
        """

        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
        )

    # ==========================================================
    # Retry Helper
    # ==========================================================

    @property
    def can_retry(self) -> bool:
        """
        هل ما زال مسموحًا بإعادة محاولة المهمة؟
        """

        return (
            self.status == TaskStatus.FAILED
            and self.attempts < self.max_attempts
        )

    # ==========================================================
    # Dependency Helper
    # ==========================================================

    def has_dependencies(self) -> bool:
        """
        هل لدى المهمة مهام تعتمد عليها؟
        """

        return bool(self.depends_on)

    # ==========================================================
    # Reset
    # ==========================================================

    def reset(self) -> None:
        """
        إعادة المهمة إلى حالتها الأولية.

        مفيدة للاختبارات أو إعادة تنفيذ خطة.
        """

        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.attempts = 0
        self.started_at = None
        self.completed_at = None

    # ==========================================================
    # Serialization Helper
    # ==========================================================

    def to_summary(self) -> dict[str, Any]:
        """
        إرجاع ملخص صغير مناسب للـlogging والـdebugging.
        """

        return {
            "id": self.id,
            "name": self.name,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "has_result": self.result is not None,
            "has_error": self.error is not None,
            "depends_on": list(self.depends_on),
        }