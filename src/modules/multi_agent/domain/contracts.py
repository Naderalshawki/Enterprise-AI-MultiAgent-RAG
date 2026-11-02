from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolResult(BaseModel):
    """
    عقد موحد لنتائج أي أداة أو وكيل.

    يُستخدم لتوحيد شكل الرد بين:
        - DatabaseTool
        - RAGTool
        - AnalysisTool
        - ReportTool
        - Multi-Agent Orchestrator

    الحالات المعتمدة:
        success               : نجاح كامل
        no_results            : لا توجد نتائج مطابقة
        insufficient_evidence : أدلة غير كافية للإجابة
        validation_error      : خطأ في المدخلات
        permission_denied     : صلاحيات غير كافية
        timeout               : انتهاء الوقت
        tool_error            : خطأ داخلي في الأداة

    الحقول:
        status     : الحالة النهائية
        tool_name  : اسم الأداة أو الوكيل
        data       : البيانات النهائية (answer, chart, ...)
        sources    : المصادر المستخدمة
        warnings   : تحذيرات أو أخطاء غير حاسمة
        error_code : رمز خطأ اختياري
        trace_id   : معرّف التتبع
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    # ==========================================================
    # Status
    # ==========================================================

    status: Literal[
        "success",
        "no_results",
        "insufficient_evidence",
        "validation_error",
        "permission_denied",
        "timeout",
        "tool_error",
    ]

    # ==========================================================
    # Identity
    # ==========================================================

    tool_name: str = Field(
        ...,
        min_length=1,
        description="اسم الأداة أو الوكيل الذي أنتج النتيجة.",
    )

    # ==========================================================
    # Payload
    # ==========================================================

    data: dict[str, Any] = Field(
        default_factory=dict,
        description="البيانات النهائية (answer, chart, sql, ...).",
    )

    # ==========================================================
    # Sources
    # ==========================================================

    sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="المصادر المستخدمة (database, rag, ...).",
    )

    # ==========================================================
    # Warnings
    # ==========================================================

    warnings: list[str] = Field(
        default_factory=list,
        description="تحذيرات أو أخطاء غير حاسمة.",
    )

    # ==========================================================
    # Error
    # ==========================================================

    error_code: str | None = Field(
        default=None,
        description="رمز خطأ اختياري.",
    )

    # ==========================================================
    # Trace
    # ==========================================================

    trace_id: str | None = Field(
        default=None,
        description="معرّف التتبع.",
    )

    # ==========================================================
    # Helpers
    # ==========================================================

    @property
    def is_success(self) -> bool:
        """هل النتيجة ناجحة؟"""
        return self.status == "success"

    @property
    def is_failure(self) -> bool:
        """هل النتيجة فاشلة؟"""
        return self.status in (
            "validation_error",
            "permission_denied",
            "timeout",
            "tool_error",
        )

    @property
    def requires_user_input(self) -> bool:
        """هل تحتاج النتيجة تدخل المستخدم؟"""
        return self.status == "insufficient_evidence"

    def to_dict(self) -> dict[str, Any]:
        """
        تحويل النتيجة إلى dict جاهز للـ JSON.
        """
        return self.model_dump()