from __future__ import annotations

from src.modules.chat_database.domain.entities import (
    Question,
    SQLQuery,
    SQLResult,
    ChatDatabaseResponse,
)

from src.modules.chat_database.domain.interfaces import (
    ResultFormatter,
)

from src.modules.chat_database.domain.exceptions import (
    ResultFormattingError,
)


class DefaultResultFormatter(ResultFormatter):
    """
    Formats SQL execution results into a unified response.

    Responsibilities
    ----------------
    - Human-readable answer
    - Preserve SQL
    - Preserve raw result
    - Preserve metadata
    """

    async def format(
        self,
        question: Question,
        query: SQLQuery,
        result: SQLResult,
    ) -> ChatDatabaseResponse:

        try:

            answer = self._build_answer(result)

            return ChatDatabaseResponse(
                success=True,
                answer=answer,
                sql=query.query,
                result=result,
                metadata={
                    "question": question.text,
                    "generated_by": query.generated_by,
                    "model": query.model,
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms,
                },
            )

        except Exception as e:

            raise ResultFormattingError(
                str(e),
            ) from e

    # ======================================================
    # Private Helpers
    # ======================================================

    def _build_answer(
        self,
        result: SQLResult,
    ) -> str:

        if result.row_count == 0:
            return "No matching records were found."

        if result.row_count == 1:
            return "Query executed successfully. One record was returned."

        return (
            f"Query executed successfully. "
            f"{result.row_count} records were returned."
        )