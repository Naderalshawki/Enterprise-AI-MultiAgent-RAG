from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, model_validator

from src.modules.multi_agent.domain.task import (
    Task,
    TaskStatus,
)


class PlanStatus(str, Enum):
    """
    الحالة العامة لخطة التنفيذ.
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"


class Plan(BaseModel):
    """
    خطة تنفيذ كاملة ينشئها Planner ويقوم TaskExecutor بتنفيذها.

    مسؤوليات Plan:
        - حفظ السؤال الأصلي.
        - حفظ قائمة المهام.
        - تتبع حالة الخطة.
        - تحديد المهمة الحالية.
        - التحقق من المهام والتبعيات.
        - معرفة ما إذا كانت الخطة قابلة للتنفيذ.
        - حفظ أخطاء الخطة.
        - توفير ملخص مناسب للـlogging والـmonitoring.

    Plan لا ينفذ المهام بنفسه.
    التنفيذ الفعلي مسؤولية TaskExecutor.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=False,
    )

    # ==========================================================
    # Plan Identity
    # ==========================================================

    plan_id: str = Field(
        default="",
        description="معرف الخطة.",
    )

    original_question: str = Field(
        ...,
        min_length=1,
        description="السؤال الأصلي للمستخدم.",
    )

    # ==========================================================
    # Tasks
    # ==========================================================

    tasks: list[Task] = Field(
        default_factory=list,
        description="المهام التي تتكون منها الخطة.",
    )

    # ==========================================================
    # Plan State
    # ==========================================================

    status: PlanStatus = Field(
        default=PlanStatus.PENDING,
        description="الحالة العامة للخطة.",
    )

    # ==========================================================
    # Execution Tracking
    # ==========================================================

    current_task_id: str | None = Field(
        default=None,
        description="معرف المهمة الحالية.",
    )

    # عدد المهام المكتملة
    completed_tasks: int = Field(
        default=0,
        ge=0,
    )

    # عدد المهام الفاشلة
    failed_tasks: int = Field(
        default=0,
        ge=0,
    )

    # ==========================================================
    # Errors
    # ==========================================================

    errors: list[str] = Field(
        default_factory=list,
        description="أخطاء الخطة.",
    )

    # ==========================================================
    # Metadata
    # ==========================================================

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="بيانات إضافية للخطة.",
    )

    # ==========================================================
    # Time Tracking
    # ==========================================================

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    # ==========================================================
    # Validation
    # ==========================================================

    @model_validator(mode="after")
    def validate_plan(self) -> "Plan":
        """
        التحقق من صحة الخطة بعد إنشائها.
        """

        task_ids = [task.id for task in self.tasks]

        # منع تكرار معرف المهمة
        if len(task_ids) != len(set(task_ids)):
            raise ValueError(
                "Plan contains duplicate task IDs."
            )

        # التحقق من التبعيات
        task_id_set = set(task_ids)

        for task in self.tasks:
            for dependency in task.depends_on:
                if dependency not in task_id_set:
                    raise ValueError(
                        f"Task '{task.id}' depends on unknown "
                        f"task '{dependency}'."
                    )

                if dependency == task.id:
                    raise ValueError(
                        f"Task '{task.id}' cannot depend on itself."
                    )

        return self

    # ==========================================================
    # Basic State
    # ==========================================================

    @property
    def is_empty(self) -> bool:
        """
        هل الخطة فارغة؟
        """

        return len(self.tasks) == 0

    @property
    def is_completed(self) -> bool:
        """
        هل اكتملت جميع مهام الخطة بنجاح؟
        """

        return bool(self.tasks) and all(
            task.status == TaskStatus.COMPLETED
            for task in self.tasks
        )

    @property
    def is_failed(self) -> bool:
        """
        هل فشلت الخطة بالكامل؟
        """

        return any(
            task.status == TaskStatus.FAILED
            for task in self.tasks
        )

    @property
    def is_terminal(self) -> bool:
        """
        هل وصلت الخطة إلى حالة نهائية؟
        """

        return self.status in (
            PlanStatus.COMPLETED,
            PlanStatus.FAILED,
            PlanStatus.PARTIAL,
            PlanStatus.CANCELLED,
        )

    # ==========================================================
    # Current Task
    # ==========================================================

    @property
    def current_task(self) -> Task | None:
        """
        إرجاع المهمة الحالية.

        الأولوية للمهمة المحددة في current_task_id،
        ثم يتم البحث عن أول مهمة قيد التنفيذ،
        ثم أول مهمة قابلة للتنفيذ.
        """

        # 1. المهمة المحددة صراحة
        if self.current_task_id:

            for task in self.tasks:
                if task.id == self.current_task_id:
                    return task

        # 2. أي مهمة قيد التنفيذ
        for task in self.tasks:

            if task.status == TaskStatus.IN_PROGRESS:
                return task

        # 3. أول مهمة جاهزة للتنفيذ
        for task in self.tasks:

            if (
                task.status == TaskStatus.PENDING
                and self.can_execute_task(task)
            ):
                return task

        return None

    # ==========================================================
    # Ready Tasks
    # ==========================================================

    @property
    def ready_tasks(self) -> list[Task]:
        """
        إرجاع جميع المهام الجاهزة للتنفيذ.

        المهمة تكون جاهزة عندما:
            - تكون PENDING
            - جميع تبعياتها COMPLETED
        """

        return [
            task
            for task in self.tasks
            if (
                task.status == TaskStatus.PENDING
                and self.can_execute_task(task)
            )
        ]

    # ==========================================================
    # Start Plan
    # ==========================================================

    def start(self) -> None:
        """
        بدء تنفيذ الخطة.
        """

        if self.is_empty:
            raise ValueError(
                "Cannot start an empty plan."
            )

        if self.is_terminal:
            raise RuntimeError(
                f"Cannot start plan in terminal state: "
                f"{self.status.value}"
            )

        self.status = PlanStatus.IN_PROGRESS

        if self.started_at is None:
            self.started_at = datetime.now(
                timezone.utc
            )

        current = self.current_task

        if current:
            self.current_task_id = current.id

    # ==========================================================
    # Complete Plan
    # ==========================================================

    def mark_completed(self) -> None:
        """
        تعليم الخطة كمكتملة.
        """

        self.refresh_counters()

        if not self.is_completed:
            raise RuntimeError(
                "Cannot mark plan as completed before "
                "all tasks are completed."
            )

        self.status = PlanStatus.COMPLETED
        self.completed_at = datetime.now(
            timezone.utc
        )

        self.current_task_id = None

    # ==========================================================
    # Fail Plan
    # ==========================================================

    def mark_failed(
        self,
        error: str,
    ) -> None:
        """
        تعليم الخطة كفاشلة وإضافة الخطأ.
        """

        self.status = PlanStatus.FAILED

        self.errors.append(error)

        self.completed_at = datetime.now(
            timezone.utc
        )

        self.refresh_counters()

    # ==========================================================
    # Partial Completion
    # ==========================================================

    def mark_partial(self) -> None:
        """
        تعليم الخطة بأنها انتهت بنتيجة جزئية.
        """

        self.refresh_counters()

        self.status = PlanStatus.PARTIAL

        self.completed_at = datetime.now(
            timezone.utc
        )

    # ==========================================================
    # Cancel
    # ==========================================================

    def cancel(
        self,
        reason: str | None = None,
    ) -> None:
        """
        إلغاء الخطة.
        """

        if self.is_terminal:
            return

        self.status = PlanStatus.CANCELLED

        if reason:
            self.errors.append(reason)

        self.completed_at = datetime.now(
            timezone.utc
        )

        self.current_task_id = None

    # ==========================================================
    # Task Lookup
    # ==========================================================

    def get_task(
        self,
        task_id: str,
    ) -> Task | None:
        """
        البحث عن مهمة بواسطة ID.
        """

        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    # ==========================================================
    # Task Dependency Check
    # ==========================================================

    def can_execute_task(
        self,
        task: Task,
    ) -> bool:
        """
        تحديد ما إذا كانت المهمة جاهزة للتنفيذ.

        الشروط:
            - المهمة PENDING.
            - جميع المهام التابعة لها COMPLETED.
        """

        if task.status != TaskStatus.PENDING:
            return False

        for dependency_id in task.depends_on:

            dependency = self.get_task(
                dependency_id
            )

            if dependency is None:
                return False

            if dependency.status != TaskStatus.COMPLETED:
                return False

        return True

    # ==========================================================
    # Set Current Task
    # ==========================================================

    def set_current_task(
        self,
        task_id: str,
    ) -> Task:
        """
        تحديد المهمة الحالية.
        """

        task = self.get_task(task_id)

        if task is None:
            raise ValueError(
                f"Task '{task_id}' not found in plan."
            )

        self.current_task_id = task_id

        return task

    # ==========================================================
    # Counters
    # ==========================================================

    def refresh_counters(self) -> None:
        """
        تحديث عدادات المهام.
        """

        self.completed_tasks = sum(
            task.status == TaskStatus.COMPLETED
            for task in self.tasks
        )

        self.failed_tasks = sum(
            task.status == TaskStatus.FAILED
            for task in self.tasks
        )

    # ==========================================================
    # Update Status
    # ==========================================================

    def update_status(self) -> None:
        """
        مزامنة حالة الخطة مع حالات المهام.
        """

        self.refresh_counters()

        if self.is_empty:
            self.status = PlanStatus.FAILED

            if "Plan contains no tasks." not in self.errors:
                self.errors.append(
                    "Plan contains no tasks."
                )

            return

        # جميع المهام مكتملة
        if self.is_completed:
            self.status = PlanStatus.COMPLETED
            self.current_task_id = None

            if self.completed_at is None:
                self.completed_at = datetime.now(
                    timezone.utc
                )

            return

        # يوجد فشل
        if self.failed_tasks > 0:

            # إذا كانت هناك مهام أخرى لم تنتهِ
            remaining_tasks = any(
                task.status
                in (
                    TaskStatus.PENDING,
                    TaskStatus.IN_PROGRESS,
                )
                for task in self.tasks
            )

            if remaining_tasks:
                self.status = PlanStatus.PARTIAL
            else:
                self.status = PlanStatus.FAILED

            return

        # الخطة بدأت
        if any(
            task.status == TaskStatus.IN_PROGRESS
            for task in self.tasks
        ):
            self.status = PlanStatus.IN_PROGRESS

            current = self.current_task

            if current:
                self.current_task_id = current.id

            return

        # لم تبدأ بعد
        self.status = PlanStatus.PENDING

    # ==========================================================
    # Add Error
    # ==========================================================

    def add_error(
        self,
        error: str,
    ) -> None:
        """
        تسجيل خطأ مرتبط بالخطة.
        """

        self.errors.append(error)

    # ==========================================================
    # Plan Reset
    # ==========================================================

    def reset(self) -> None:
        """
        إعادة الخطة بالكامل لحالتها الأولية.

        تستخدم للاختبار أو إعادة التنفيذ.
        """

        for task in self.tasks:
            task.reset()

        self.status = PlanStatus.PENDING
        self.current_task_id = None
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.errors.clear()
        self.started_at = None
        self.completed_at = None

    # ==========================================================
    # Progress
    # ==========================================================

    @property
    def progress(self) -> float:
        """
        نسبة إنجاز الخطة من 0 إلى 1.
        """

        if not self.tasks:
            return 0.0

        return self.completed_tasks / len(
            self.tasks
        )

    @property
    def progress_percentage(self) -> float:
        """
        نسبة إنجاز الخطة بالمئة.
        """

        return round(
            self.progress * 100,
            2,
        )

    # ==========================================================
    # Summary
    # ==========================================================

    def summary(self) -> dict[str, Any]:
        """
        إنشاء ملخص للخطة مناسب للـlogging
        والـmonitoring والـdebugging.
        """

        self.refresh_counters()

        return {
            "plan_id": self.plan_id,
            "question": self.original_question,
            "status": self.status.value,
            "total_tasks": len(self.tasks),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "progress_percentage": self.progress_percentage,
            "current_task_id": self.current_task_id,
            "errors": list(self.errors),
            "tasks": [
                task.to_summary()
                for task in self.tasks
            ],
        }