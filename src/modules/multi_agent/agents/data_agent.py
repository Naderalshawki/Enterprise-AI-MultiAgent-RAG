from __future__ import annotations

import logging

from src.modules.chat_database.application.dtos import (
    AskDatabaseRequest,
)
from src.modules.chat_database.application.services import (
    ChatDatabaseService,
)
from src.modules.multi_agent.domain.base_agent import BaseAgent
from src.modules.multi_agent.domain.bi_context import BIContext


logger = logging.getLogger(__name__)


class DataAgent(BaseAgent):
    """
    وكيل استخراج البيانات الديناميكي (Dynamic Data Agent).

    يرسل سؤال المستخدم إلى ChatDatabaseService
    لاستخراج البيانات من Chat Database
    المعتمدة على Supabase / PostgreSQL.
    """

    def __init__(
        self,
        llm_service,
        chat_db_service: ChatDatabaseService | None = None,
    ):
        super().__init__(llm_service)

        self.chat_db_service = chat_db_service

    @property
    def name(self) -> str:
        return "Data_Agent"

    async def execute(
        self,
        context: BIContext,
    ) -> BIContext:

        self._log_start()

        try:

            if self.chat_db_service is None:
                raise RuntimeError(
                    "ChatDatabaseService is not configured."
                )

            # ==================================================
            # 1. Build Database Request
            # ==================================================

            request = AskDatabaseRequest(
                question=context.question,
                user_id=context.user_id,
                session_id=context.session_id,
                conversation_id=context.session_id,
                metadata={
                    "agent": self.name,
                },
            )

            # ==================================================
            # 2. Execute through Chat Database
            # ==================================================

            response = await self.chat_db_service.ask(
                request
            )

            if response is None:
                raise RuntimeError(
                    "ChatDatabaseService returned None."
                )

            # ==================================================
            # 3. Store Result in BI Context
            # ==================================================

            if not response.success:

                error = (
                    response.error
                    or "Database query failed."
                )

                context.add_error(
                    self.name,
                    error,
                )

                return context

            context.raw_data = response.rows

            context.sql_query = response.sql

            context.metadata["database"] = {
                "success": response.success,
                "row_count": response.row_count,
                "execution_time_ms": (
                    response.execution_time_ms
                ),
                "metadata": response.metadata,
            }

            logger.info(
                "[%s] Retrieved %s records.",
                self.name,
                response.row_count,
            )

            self._log_completion()

        except Exception as exc:

            logger.exception(
                "[%s] Critical error during "
                "database execution.",
                self.name,
            )

            context.add_error(
                self.name,
                str(exc),
            )

        return context