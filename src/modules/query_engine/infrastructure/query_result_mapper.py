from __future__ import annotations

from typing import Any

from src.modules.chat_database.application.dtos import (
    AskDatabaseResponse,
)
from src.modules.query_engine.domain.entities import (
    QueryContext,
    QueryRequest,
    QueryResult,
)
from src.modules.query_engine.domain.enums import (
    QuerySource,
)
from src.modules.query_engine.domain.interfaces import (
    QueryResultMapper,
)


class DefaultQueryResultMapper(QueryResultMapper):
    """
    المسؤول عن تحويل نتيجة ChatDatabase إلى
    QueryResult موحد داخل Query Engine.

    Flow:

        AskDatabaseResponse
                ↓
        DefaultQueryResultMapper
                ↓
            QueryResult

    المسؤوليات:
        - التحقق من نوع النتيجة.
        - نقل بيانات النتيجة.
        - توحيد Metadata.
        - ربط النتيجة بـ QueryRequest.
        - الحفاظ على Query ID.

    لا يقوم بـ:
        - توليد SQL.
        - التحقق من SQL.
        - تنفيذ SQL.
        - الوصول إلى Database.
        - استدعاء LLM.
        - تنفيذ RAG.
    """

    # ==========================================================
    # Map
    # ==========================================================

    def map(
        self,
        source_result: Any,
        request: QueryRequest,
        context: QueryContext,
    ) -> QueryResult:
        """
        تحويل نتيجة المصدر إلى QueryResult.

        Parameters
        ----------
        source_result:
            النتيجة القادمة من ChatDatabase.

        request:
            QueryRequest الأصلي.

        context:
            QueryContext الخاص بالاستعلام.

        Returns
        -------
        QueryResult
            النتيجة الموحدة داخل Query Engine.
        """

        # ------------------------------------------------------
        # Validate Request
        # ------------------------------------------------------

        if request is None:
            raise ValueError(
                "QueryRequest cannot be None."
            )

        # ------------------------------------------------------
        # Validate Context
        # ------------------------------------------------------

        if context is None:
            raise ValueError(
                "QueryContext cannot be None."
            )

        # ------------------------------------------------------
        # Validate Source Result
        # ------------------------------------------------------

        if source_result is None:
            raise ValueError(
                "source_result cannot be None."
            )

        if not isinstance(
            source_result,
            AskDatabaseResponse,
        ):
            raise TypeError(
                "source_result must be an "
                "AskDatabaseResponse."
            )

        # ------------------------------------------------------
        # Build Metadata
        # ------------------------------------------------------

        metadata = dict(
            source_result.metadata or {}
        )

        metadata.update(
            {
                "source": (
                    QuerySource.CHAT_DATABASE.value
                ),
                "query_intent": (
                    context.intent.value
                ),
                "query_source": (
                    context.source.value
                ),
                "query_id": str(
                    request.query_id
                ),
            }
        )

        # ------------------------------------------------------
        # Build QueryResult
        # ------------------------------------------------------

        return QueryResult(
            success=source_result.success,
            answer=source_result.answer,
            rows=source_result.rows,
            row_count=source_result.row_count,
            sql=source_result.sql,
            execution_time_ms=(
                source_result.execution_time_ms
            ),
            error=source_result.error,
            metadata=metadata,
            query_id=request.query_id,
            created_at=source_result.created_at,
        )