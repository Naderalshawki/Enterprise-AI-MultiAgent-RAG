from __future__ import annotations

import logging

from src.modules.chat_database.application.dtos import (
    AskDatabaseRequest,
)
from src.modules.chat_database.application.services import (
    ChatDatabaseService,
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
    QuerySourceAdapter,
)


logger = logging.getLogger(__name__)


class ChatDatabaseAdapter(QuerySourceAdapter):
    """
    Adapter يربط Query Engine مع ChatDatabaseService.

    مسؤولية هذا الكلاس:

        QueryRequest
            ↓
        AskDatabaseRequest
            ↓
        ChatDatabaseService
            ↓
        AskDatabaseResponse
            ↓
        QueryResultMapper
            ↓
        QueryResult

    لا يحتوي على منطق:
        - SQL Generation
        - SQL Validation
        - SQL Execution
        - Schema Discovery
        - Result Formatting
        - LLM
        - RAG
    """

    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(
        self,
        chat_database_service: ChatDatabaseService,
        result_mapper: QueryResultMapper,
    ) -> None:
        """
        إنشاء Adapter وربطه بخدمة Chat Database
        وResult Mapper.
        """

        if chat_database_service is None:
            raise ValueError(
                "chat_database_service cannot be None."
            )

        if result_mapper is None:
            raise ValueError(
                "result_mapper cannot be None."
            )

        if not isinstance(
            result_mapper,
            QueryResultMapper,
        ):
            raise TypeError(
                "result_mapper must implement "
                "QueryResultMapper."
            )

        self._chat_database = (
            chat_database_service
        )

        self._result_mapper = (
            result_mapper
        )

    # ==========================================================
    # Adapter Identity
    # ==========================================================

    @property
    def source_name(self) -> str:
        """
        اسم مصدر البيانات الذي يمثله Adapter.
        """

        return QuerySource.CHAT_DATABASE.value

    # ==========================================================
    # Execute
    # ==========================================================

    async def execute(
        self,
        request: QueryRequest,
        context: QueryContext,
    ) -> QueryResult:
        """
        تنفيذ Query من خلال ChatDatabaseService.

        يتم هنا فقط:
            1. تحويل QueryRequest إلى AskDatabaseRequest.
            2. استدعاء ChatDatabaseService.
            3. تمرير النتيجة إلى QueryResultMapper.
        """

        if request is None:
            raise ValueError(
                "QueryRequest cannot be None."
            )

        if context is None:
            raise ValueError(
                "QueryContext cannot be None."
            )

        logger.info(
            "[ChatDatabaseAdapter] "
            "Executing query | query_id=%s",
            request.query_id,
        )

        try:

            # --------------------------------------------------
            # 1. QueryRequest → AskDatabaseRequest
            # --------------------------------------------------

            database_request = (
                AskDatabaseRequest(
                    question=request.question,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    conversation_id=(
                        request.conversation_id
                    ),
                    metadata={
                        **request.metadata,
                        "query_id": str(
                            request.query_id
                        ),
                        "query_intent": (
                            context.intent.value
                        ),
                        "query_source": (
                            context.source.value
                        ),
                    },
                )
            )

            # --------------------------------------------------
            # 2. Execute through ChatDatabase
            # --------------------------------------------------

            response = await (
                self._chat_database.ask(
                    database_request
                )
            )

            if response is None:
                raise RuntimeError(
                    "ChatDatabaseService returned None."
                )

            # --------------------------------------------------
            # 3. AskDatabaseResponse → QueryResult
            # --------------------------------------------------

            result = self._result_mapper.map(
                source_result=response,
                request=request,
                context=context,
            )

            if result is None:
                raise RuntimeError(
                    "QueryResultMapper returned None."
                )

            logger.info(
                "[ChatDatabaseAdapter] "
                "Query completed | "
                "query_id=%s | success=%s",
                request.query_id,
                result.success,
            )

            return result

        except Exception as exc:

            logger.exception(
                "[ChatDatabaseAdapter] "
                "Query execution failed | "
                "query_id=%s",
                request.query_id,
            )

            return QueryResult(
                success=False,
                error=str(exc),
                query_id=request.query_id,
                metadata={
                    "source": self.source_name,
                    "adapter": (
                        self.__class__.__name__
                    ),
                },
            )

    # ==========================================================
    # Health Check
    # ==========================================================

    async def health_check(self) -> bool:
        """
        التحقق من جاهزية ChatDatabaseService.

        ChatDatabaseService الحالي يعتمد على ask()
        كواجهة التنفيذ الأساسية، لذلك نتحقق من
        وجودها وقابليتها للاستدعاء.
        """

        try:

            return callable(
                getattr(
                    self._chat_database,
                    "ask",
                    None,
                )
            )

        except Exception:

            logger.exception(
                "[ChatDatabaseAdapter] "
                "Health check failed."
            )

            return False

    # ==========================================================
    # Service Access
    # ==========================================================

    @property
    def chat_database_service(
        self,
    ) -> ChatDatabaseService:
        """
        إرجاع ChatDatabaseService المرتبط.
        """

        return self._chat_database

    # ==========================================================
    # Result Mapper Access
    # ==========================================================

    @property
    def result_mapper(
        self,
    ) -> QueryResultMapper:
        """
        إرجاع QueryResultMapper المرتبط.
        """

        return self._result_mapper