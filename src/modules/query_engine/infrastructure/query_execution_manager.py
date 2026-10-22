from __future__ import annotations

import logging

from src.modules.query_engine.domain.entities import QueryExecution
from src.modules.query_engine.domain.interfaces import QueryExecutionManager


logger = logging.getLogger(__name__)


class DefaultQueryExecutionManager(QueryExecutionManager):
    """
    Implementation of QueryExecutionManager.

    مسؤول عن إدارة دورة حياة QueryExecution:

        PENDING
          ↓
        EXECUTING
          ↓
        COMPLETED / FAILED / CANCELLED

    هذا الكلاس لا ينفذ الاستعلام نفسه.
    هو مسؤول فقط عن إدارة حالة عملية التنفيذ.

    المسؤوليات:
        - بدء التنفيذ.
        - تسجيل النجاح.
        - تسجيل الفشل.
        - إلغاء التنفيذ.
        - التحقق من عدد المحاولات.

    لا يقوم بـ:
        - SQL Generation.
        - SQL Validation.
        - SQL Execution.
        - Database Access.
        - RAG.
    """

    # ==========================================================
    # Start
    # ==========================================================

    async def start(
        self,
        execution: QueryExecution,
    ) -> QueryExecution:
        """
        بدء عملية تنفيذ QueryExecution.

        يتم هنا:
            - التحقق من صحة الكائن.
            - التأكد من عدم تجاوز عدد المحاولات.
            - تحديث الحالة إلى EXECUTING.
            - زيادة رقم المحاولة.
            - تسجيل وقت البداية.

        ملاحظة:
            لا نستخدم can_retry هنا، لأن can_retry
            مخصص لإعادة المحاولة بعد فشل التنفيذ.

            أما العملية الجديدة فتبدأ من:
                PENDING + attempt=0
        """

        self._validate_execution(execution)

        # ------------------------------------------------------
        # Terminal State
        # ------------------------------------------------------

        if execution.is_terminal:
            raise ValueError(
                "Cannot start a terminal QueryExecution."
            )

        # ------------------------------------------------------
        # Maximum Attempts
        # ------------------------------------------------------

        if execution.attempt >= execution.max_attempts:
            raise RuntimeError(
                "QueryExecution cannot be started "
                "because the maximum number of attempts "
                "has been reached."
            )

        # ------------------------------------------------------
        # Start Execution
        # ------------------------------------------------------

        execution.start()

        logger.info(
            "[QueryExecutionManager] "
            "Execution started | "
            "query_id=%s | "
            "attempt=%s/%s",
            execution.query_id,
            execution.attempt,
            execution.max_attempts,
        )

        return execution

    # ==========================================================
    # Complete
    # ==========================================================

    async def complete(
        self,
        execution: QueryExecution,
    ) -> QueryExecution:
        """
        تسجيل نجاح عملية التنفيذ.
        """

        self._validate_execution(
            execution
        )

        if execution.is_terminal:
            raise ValueError(
                "Cannot complete a terminal QueryExecution."
            )

        execution.mark_completed()

        logger.info(
            "[QueryExecutionManager] "
            "Execution completed | "
            "query_id=%s | "
            "attempt=%s",
            execution.query_id,
            execution.attempt,
        )

        return execution

    # ==========================================================
    # Fail
    # ==========================================================

    async def fail(
        self,
        execution: QueryExecution,
        error: str,
    ) -> QueryExecution:
        """
        تسجيل فشل عملية التنفيذ.

        لا يقوم هذا الكلاس بإعادة المحاولة تلقائيًا.
        فقط يسجل الفشل داخل QueryExecution.

        قرار Retry يمكن إضافته لاحقًا في طبقة
        أعلى حسب سياسة النظام.
        """

        self._validate_execution(
            execution
        )

        if execution.is_terminal:
            raise ValueError(
                "Cannot fail a terminal QueryExecution."
            )

        if not error or not error.strip():
            raise ValueError(
                "Execution error cannot be empty."
            )

        execution.mark_failed(
            error.strip()
        )

        logger.error(
            "[QueryExecutionManager] "
            "Execution failed | "
            "query_id=%s | "
            "attempt=%s | "
            "error=%s",
            execution.query_id,
            execution.attempt,
            error.strip(),
        )

        return execution

    # ==========================================================
    # Cancel
    # ==========================================================

    async def cancel(
        self,
        execution: QueryExecution,
        reason: str | None = None,
    ) -> QueryExecution:
        """
        إلغاء عملية التنفيذ.
        """

        self._validate_execution(
            execution
        )

        if execution.is_terminal:
            raise ValueError(
                "Cannot cancel a terminal QueryExecution."
            )

        execution.cancel(
            reason=reason
        )

        logger.warning(
            "[QueryExecutionManager] "
            "Execution cancelled | "
            "query_id=%s | "
            "reason=%s",
            execution.query_id,
            reason or "No reason provided.",
        )

        return execution

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def _validate_execution(
        execution: QueryExecution,
    ) -> None:
        """
        التحقق من QueryExecution قبل تغيير حالته.
        """

        if execution is None:
            raise ValueError(
                "execution cannot be None."
            )

        if not isinstance(
            execution,
            QueryExecution,
        ):
            raise TypeError(
                "execution must be an instance "
                "of QueryExecution."
            )