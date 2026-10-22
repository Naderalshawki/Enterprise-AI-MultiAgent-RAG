from __future__ import annotations

from src.modules.chat_database.application.dtos import (
    AskDatabaseRequest,
    AskDatabaseResponse,
)

from src.modules.chat_database.application.prompt_builder import (
    SQLPromptBuilder,
)

from src.modules.chat_database.domain.entities import (
    Question,
)

from src.modules.chat_database.domain.interfaces import (
    SQLGenerator,
    SQLValidator,
    SQLExecutor,
    ResultFormatter,
)

# استيراد واجهة SchemaService المستقلة
from src.modules.schema_engine.application.services import SchemaService


class ChatDatabaseService:
    """
    Main Chat Database application service utilizing SchemaService Facade.

    Flow
    ----
    Question
        ↓
    SchemaService (Facade for Cache, Loader, Retriever, Formatter)
        ↓
    Prompt Builder
        ↓
    SQL Generator
        ↓
    SQL Validator
        ↓
    SQL Executor
        ↓
    Result Formatter
        ↓
    Response
    """

    def __init__(
        self,
        *,
        schema_service: SchemaService,
        prompt_builder: SQLPromptBuilder,
        sql_generator: SQLGenerator,
        sql_validator: SQLValidator,
        sql_executor: SQLExecutor,
        result_formatter: ResultFormatter,
    ):
        self._schema_service = schema_service
        self._prompt_builder = prompt_builder
        self._sql_generator = sql_generator
        self._sql_validator = sql_validator
        self._sql_executor = sql_executor
        self._result_formatter = result_formatter

    async def ask(
        self,
        request: AskDatabaseRequest,
    ) -> AskDatabaseResponse:

        # ==================================================
        # Build Domain Question
        # ==================================================

        question = Question(
            text=request.question,
            user_id=request.user_id,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            metadata=request.metadata,
        )

        # ==================================================
        # Get Schema Context via SchemaService (Facade)
        # ==================================================

        # جلب الاسكيما والـ Prompt المخصص والمُصفى للجداول ذات الصلة لتوفير الـ Tokens
        schema_prompt_context = await self._schema_service.get_relevant_schema_prompt(
            question=question.text
        )

        # ==================================================
        # Build Prompt
        # ==================================================

        prompt = self._prompt_builder.build(
            question=question,
            schema=schema_prompt_context,
        )

        # ==================================================
        # Generate SQL
        # ==================================================

        sql_query = await self._sql_generator.generate(
            prompt=prompt,
        )

        # ==================================================
        # Validate SQL
        # ==================================================

        validated_query = await self._sql_validator.validate(
            sql_query,
        )

        # ==================================================
        # Execute SQL
        # ==================================================

        sql_result = await self._sql_executor.execute(
            validated_query,
        )

        # ==================================================
        # Format Result
        # ==================================================

        response = await self._result_formatter.format(
            question=question,
            query=validated_query,
            result=sql_result,
        )

        # ==================================================
        # Return DTO
        # ==================================================

        return AskDatabaseResponse(
            success=response.success,
            answer=response.answer,
            sql=response.sql,
            rows=response.result.rows if response.result else [],
            row_count=response.result.row_count if response.result else 0,
            execution_time_ms=(
                response.result.execution_time_ms
                if response.result
                else None
            ),
            error=response.error,
            metadata=response.metadata,
            created_at=response.created_at,
        )