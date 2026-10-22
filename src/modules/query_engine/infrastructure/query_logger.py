from __future__ import annotations

import logging

from src.modules.query_engine.domain.entities import (
    QueryContext,
    QueryRequest,
    QueryResult,
)
from src.modules.query_engine.domain.interfaces import (
    QueryLogger,
)


logger = logging.getLogger(__name__)


class DefaultQueryLogger(QueryLogger):
    """
    Implementation of QueryLogger using Python logging.

    مسؤول عن تسجيل الأحداث التقنية الخاصة بدورة
    حياة الاستعلام داخل Query Engine.

    لا يقوم بـ:
        - توليد SQL.
        - تنفيذ SQL.
        - تصنيف Query.
        - توجيه Query.
        - الوصول إلى Database.
        - تنفيذ Audit Log مستقل.
    """

    # ==========================================================
    # Query Started
    # ==========================================================

    async def log_started(
        self,
        request: QueryRequest,
        context: QueryContext,
    ) -> None:
        """
        تسجيل بداية تنفيذ الاستعلام.
        """

        logger.info(
            "[QueryEngine] Query started | "
            "query_id=%s | "
            "user_id=%s | "
            "session_id=%s | "
            "source=%s | "
            "intent=%s",
            request.query_id,
            request.user_id,
            request.session_id,
            context.source.value,
            context.intent.value,
        )

    # ==========================================================
    # Query Completed
    # ==========================================================

    async def log_completed(
        self,
        request: QueryRequest,
        context: QueryContext,
        result: QueryResult,
    ) -> None:
        """
        تسجيل اكتمال تنفيذ الاستعلام.
        """

        logger.info(
            "[QueryEngine] Query completed | "
            "query_id=%s | "
            "success=%s | "
            "row_count=%s | "
            "execution_time_ms=%s",
            request.query_id,
            result.success,
            result.row_count,
            result.execution_time_ms,
        )

    # ==========================================================
    # Query Failed
    # ==========================================================

    async def log_failed(
        self,
        request: QueryRequest,
        context: QueryContext,
        error: str,
    ) -> None:
        """
        تسجيل فشل تنفيذ الاستعلام.
        """

        logger.error(
            "[QueryEngine] Query failed | "
            "query_id=%s | "
            "source=%s | "
            "intent=%s | "
            "error=%s",
            request.query_id,
            context.source.value,
            context.intent.value,
            error,
        )