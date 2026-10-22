
from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.modules.chat_database.domain.entities import SQLQuery, SQLResult
from src.modules.chat_database.domain.exceptions import SQLExecutionError
from src.modules.chat_database.domain.interfaces import SQLExecutor
from src.modules.chat_database.infrastructure.database import Database

logger = logging.getLogger(__name__)


class PostgreSQLExecutor(SQLExecutor):
    """Execute validated, read-only SQL against PostgreSQL / Supabase."""

    def __init__(
        self,
        database: Database,
        *,
        max_rows: int = 1000,
        query_timeout_seconds: float = 30.0,
    ) -> None:
        if (
            isinstance(max_rows, bool)
            or not isinstance(max_rows, int)
            or max_rows < 1
        ):
            raise ValueError("max_rows must be a positive integer")

        if (
            isinstance(query_timeout_seconds, bool)
            or not isinstance(query_timeout_seconds, (int, float))
            or query_timeout_seconds <= 0
        ):
            raise ValueError("query_timeout_seconds must be positive")

        self._database = database
        self._max_rows = max_rows
        self._query_timeout_ms = max(
            1, int(query_timeout_seconds * 1000)
        )

    async def execute(self, query: SQLQuery) -> SQLResult:
        """Execute an SQLQuery and return a bounded SQLResult."""

        if not isinstance(query, SQLQuery):
            raise SQLExecutionError("Expected an SQLQuery object.")

        if not isinstance(query.query, str) or not query.query.strip():
            raise SQLExecutionError("Cannot execute an empty SQL query.")

        started = time.perf_counter()

        try:
            async with self._database.session() as session:
                # Must be the first statement in the transaction.
                await session.execute(
                    text("SET TRANSACTION READ ONLY")
                )

                # Apply a transaction-local PostgreSQL statement timeout.
                await session.execute(
                    text(
                        "SELECT set_config("
                        "'statement_timeout', :timeout, true)"
                    ),
                    {"timeout": str(self._query_timeout_ms)},
                )

                result = await session.execute(text(query.query))
                columns = list(result.keys())

                # Read at most max_rows + 1 rows to detect truncation.
                mappings = result.mappings().fetchmany(
                    self._max_rows + 1
                )
                truncated = len(mappings) > self._max_rows

                rows = [
                    dict(row)
                    for row in mappings[: self._max_rows]
                ]

                elapsed_ms = round(
                    (time.perf_counter() - started) * 1000,
                    2,
                )

                metadata: dict[str, Any] = {
                    "max_rows": self._max_rows,
                    "truncated": truncated,
                    "query_timeout_ms": self._query_timeout_ms,
                    "read_only": True,
                }

                logger.info(
                    "[PostgreSQL Executor] Query completed: "
                    "rows_returned=%d, truncated=%s, "
                    "execution_time_ms=%.2f",
                    len(rows),
                    truncated,
                    elapsed_ms,
                )

                return SQLResult(
                    rows=rows,
                    columns=columns,
                    row_count=len(rows),
                    execution_time_ms=elapsed_ms,
                    metadata=metadata,
                )

        except SQLAlchemyError as exc:
            message = str(exc)
            lower_message = message.lower()

            if (
                "read-only transaction" in lower_message
                or "read only transaction" in lower_message
            ):
                safe_message = (
                    "The query was rejected because the database "
                    "transaction is read-only. Only read operations "
                    "are permitted."
                )
            elif (
                "statement timeout" in lower_message
                or "canceling statement due to user request"
                in lower_message
            ):
                safe_message = (
                    "The query exceeded the configured timeout of "
                    f"{self._query_timeout_ms} ms."
                )
            else:
                safe_message = message

            logger.warning(
                "[PostgreSQL Executor] SQL execution failed: %s",
                safe_message,
            )
            raise SQLExecutionError(safe_message) from exc

        except Exception as exc:
            logger.exception(
                "[PostgreSQL Executor] Unexpected execution failure."
            )
            raise SQLExecutionError(
                f"Unexpected SQL execution failure: {exc}"
            ) from exc
