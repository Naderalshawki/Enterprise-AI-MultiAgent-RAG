from __future__ import annotations

import logging
from typing import Any

from src.modules.multi_agent.domain.bi_context import (
    BIContext,
)

from src.modules.query_engine.domain.entities import (
    QueryRequest,
)

from src.modules.query_engine.domain.interfaces import (
    QueryEngine,
)


logger = logging.getLogger(__name__)


class DatabaseTool:
    """
    DatabaseTool

    يربط Multi-Agent مع Query Engine.

    Flow:

        Multi-Agent
             ↓
        DatabaseTool
             ↓
        QueryEngine
             ↓
        QueryRouter
             ↓
        ChatDatabaseAdapter
             ↓
        ChatDatabaseService
             ↓
        Supabase / PostgreSQL
    """

    def __init__(
        self,
        query_engine: QueryEngine | None = None,
    ) -> None:

        self.name = "DatabaseTool"

        self.description = (
            "يستخدم لاستخراج البيانات من قواعد البيانات "
            "من خلال Query Engine."
        )

        self.query_engine = query_engine

    # ==========================================================
    # Execute
    # ==========================================================

    async def execute(
        self,
        inputs: dict[str, Any],
        context: BIContext,
    ) -> dict[str, Any]:

        if context is None:
            raise ValueError(
                "BIContext cannot be None."
            )

        inputs = inputs or {}

        query = inputs.get(
            "query",
            context.question,
        )

        if not query:

            error = (
                "Database query cannot be empty."
            )

            context.add_error(
                self.name,
                error,
            )

            return {
                "success": False,
                "answer": None,
                "rows": [],
                "row_count": 0,
                "sql": None,
                "execution_time_ms": None,
                "error": error,
                "metadata": {},
            }

        query = str(query).strip()

        if self.query_engine is None:

            error = (
                "QueryEngine is not configured."
            )

            context.add_error(
                self.name,
                error,
            )

            return {
                "success": False,
                "answer": None,
                "rows": [],
                "row_count": 0,
                "sql": None,
                "execution_time_ms": None,
                "error": error,
                "metadata": {},
            }

        # ------------------------------------------------------
        # Metadata
        # ------------------------------------------------------

        metadata = {
            "agent": "MultiAgent",
            "tool": self.name,
        }

        # ------------------------------------------------------
        # Query Request
        # ------------------------------------------------------

        request = QueryRequest(
            question=query,

            user_id=context.user_id,

            session_id=context.session_id,

            conversation_id=context.session_id,

            metadata=metadata,
        )

        logger.info(
            "[Tool:%s] Executing database query",
            self.name,
        )

        try:

            result = await (
                self.query_engine.execute(
                    request
                )
            )

            if result is None:
                raise RuntimeError(
                    "QueryEngine returned None."
                )

            # ==================================================
            # Failure
            # ==================================================

            if not result.success:

                error = (
                    result.error
                    or "Database query failed."
                )

                context.add_error(
                    self.name,
                    error,
                )

                context.metadata[
                    "database"
                ] = {
                    "success": False,
                    "row_count": result.row_count,
                    "error": error,
                    "metadata": result.metadata,
                }

                return {
                    "success": False,
                    "answer": result.answer,
                    "rows": result.rows,
                    "row_count": result.row_count,
                    "sql": result.sql,
                    "execution_time_ms": (
                        result.execution_time_ms
                    ),
                    "error": error,
                    "metadata": result.metadata,
                }

            # ==================================================
            # Success
            # ==================================================

            context.raw_data = (
                result.rows
            )

            context.sql_query = (
                result.sql
            )

            context.metadata[
                "database"
            ] = {
                "success": True,
                "row_count": result.row_count,
                "execution_time_ms": (
                    result.execution_time_ms
                ),
                "metadata": result.metadata,
            }

            logger.info(
                "[Tool:%s] Success | rows=%s",
                self.name,
                result.row_count,
            )

            return {
                "success": True,
                "answer": result.answer,
                "rows": result.rows,
                "row_count": result.row_count,
                "sql": result.sql,
                "execution_time_ms": (
                    result.execution_time_ms
                ),
                "error": result.error,
                "metadata": result.metadata,
            }

        except Exception as exc:

            logger.exception(
                "[Tool:%s] Database error.",
                self.name,
            )

            error = str(exc)

            context.add_error(
                self.name,
                error,
            )

            return {
                "success": False,
                "answer": None,
                "rows": [],
                "row_count": 0,
                "sql": context.sql_query,
                "execution_time_ms": None,
                "error": error,
                "metadata": {},
            }

    # ==========================================================
    # Configuration
    # ==========================================================

    def set_query_engine(
        self,
        query_engine: QueryEngine,
    ) -> None:

        if query_engine is None:
            raise ValueError(
                "query_engine cannot be None."
            )

        self.query_engine = query_engine

    # ==========================================================
    # Status
    # ==========================================================

    @property
    def is_configured(self) -> bool:
        return self.query_engine is not None