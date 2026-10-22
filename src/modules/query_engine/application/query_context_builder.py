from __future__ import annotations

import logging

from src.modules.query_engine.domain.entities import (
    QueryContext,
    QueryRequest,
)

from src.modules.query_engine.domain.enums import (
    QueryExecutionMode,
    QueryIntent,
    QueryPriority,
    QuerySource,
)

from src.modules.query_engine.domain.interfaces import (
    QueryContextBuilder,
)


logger = logging.getLogger(__name__)


class DefaultQueryContextBuilder(QueryContextBuilder):
    """
    بناء QueryContext للاستعلام.

    المصدر الوحيد في Query Engine الحالي:

        CHAT_DATABASE

    أي أن Query Engine يتعامل مع
    Chat Database الخاصة بالمنصة،
    والتي تعتمد على PostgreSQL / Supabase.
    """

    DEFAULT_SOURCE = QuerySource.CHAT_DATABASE

    DEFAULT_EXECUTION_MODE = (
        QueryExecutionMode.SYNC
    )

    DEFAULT_PRIORITY = (
        QueryPriority.NORMAL
    )

    # ==========================================================
    # Build
    # ==========================================================

    async def build(
        self,
        request: QueryRequest,
    ) -> QueryContext:

        if request is None:
            raise ValueError(
                "QueryRequest cannot be None."
            )

        context = QueryContext(
            request=request,
            intent=QueryIntent.UNKNOWN,
            source=self.DEFAULT_SOURCE,
            execution_mode=(
                self.DEFAULT_EXECUTION_MODE
            ),
            priority=self.DEFAULT_PRIORITY,
            metadata={},
        )

        self._populate_metadata(context)

        logger.info(
            "[QueryContextBuilder] Context built | "
            "query_id=%s | source=%s",
            request.query_id,
            context.source.value,
        )

        return context

    # ==========================================================
    # Metadata
    # ==========================================================

    @staticmethod
    def _populate_metadata(
        context: QueryContext,
    ) -> None:

        request = context.request

        context.metadata.update(
            {
                "query_id": str(
                    request.query_id
                ),

                "user_id": request.user_id,

                "session_id": request.session_id,

                "conversation_id": (
                    request.conversation_id
                ),

                "source": (
                    context.source.value
                ),

                "execution_mode": (
                    context.execution_mode.value
                ),

                "priority": (
                    context.priority.value
                ),
            }
        )

        if request.metadata:
            context.metadata[
                "request_metadata"
            ] = dict(
                request.metadata
            )

    # ==========================================================
    # Intent
    # ==========================================================

    @staticmethod
    def set_intent(
        context: QueryContext,
        intent: QueryIntent,
    ) -> QueryContext:

        if context is None:
            raise ValueError(
                "QueryContext cannot be None."
            )

        if not isinstance(
            intent,
            QueryIntent,
        ):
            raise TypeError(
                "intent must be an instance of QueryIntent."
            )

        context.intent = intent

        context.metadata[
            "query_intent"
        ] = intent.value

        return context

    # ==========================================================
    # Priority
    # ==========================================================

    @staticmethod
    def set_priority(
        context: QueryContext,
        priority: QueryPriority,
    ) -> QueryContext:

        if context is None:
            raise ValueError(
                "QueryContext cannot be None."
            )

        if not isinstance(
            priority,
            QueryPriority,
        ):
            raise TypeError(
                "priority must be an instance of QueryPriority."
            )

        context.priority = priority

        context.metadata[
            "priority"
        ] = priority.value

        return context

    # ==========================================================
    # Execution Mode
    # ==========================================================

    @staticmethod
    def set_execution_mode(
        context: QueryContext,
        execution_mode: QueryExecutionMode,
    ) -> QueryContext:

        if context is None:
            raise ValueError(
                "QueryContext cannot be None."
            )

        if not isinstance(
            execution_mode,
            QueryExecutionMode,
        ):
            raise TypeError(
                "execution_mode must be an instance of "
                "QueryExecutionMode."
            )

        context.execution_mode = (
            execution_mode
        )

        context.metadata[
            "execution_mode"
        ] = execution_mode.value

        return context

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def validate(
        context: QueryContext,
    ) -> QueryContext:

        if context is None:
            raise ValueError(
                "QueryContext cannot be None."
            )

        if context.request is None:
            raise ValueError(
                "QueryContext request cannot be None."
            )

        if not context.request.question.strip():
            raise ValueError(
                "QueryContext question cannot be empty."
            )

        if context.source == QuerySource.UNKNOWN:
            raise ValueError(
                "QueryContext source cannot be UNKNOWN."
            )

        return context