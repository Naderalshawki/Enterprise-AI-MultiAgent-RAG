from __future__ import annotations

import logging

from src.modules.query_engine.application.query_router import (
    QueryRouter,
)

from src.modules.query_engine.domain.entities import (
    QueryContext,
    QueryExecution,
    QueryRequest,
    QueryResult,
)

from src.modules.query_engine.domain.enums import (
    QueryIntent,
    QueryPriority,
    QuerySource,
    QueryStatus,
)

from src.modules.query_engine.domain.interfaces import (
    QueryClassifier,
    QueryContextBuilder,
    QueryEngine,
    QueryExecutionManager,
    QueryLogger,
)


logger = logging.getLogger(__name__)


class QueryEngineOrchestrator(QueryEngine):
    """
    المنسق الرئيسي لـ Query Engine.

    Flow:

        QueryRequest
             ↓
        ContextBuilder
             ↓
        Classifier
             ↓
        QueryRouter
             ↓
        Adapter
             ↓
        QueryResult
    """

    def __init__(
        self,
        router: QueryRouter,
        classifier: QueryClassifier,
        context_builder: QueryContextBuilder,
        execution_manager: QueryExecutionManager,
        query_logger: QueryLogger | None = None,
    ) -> None:

        if router is None:
            raise ValueError(
                "router cannot be None."
            )

        if classifier is None:
            raise ValueError(
                "classifier cannot be None."
            )

        if context_builder is None:
            raise ValueError(
                "context_builder cannot be None."
            )

        if execution_manager is None:
            raise ValueError(
                "execution_manager cannot be None."
            )

        self._router = router
        self._classifier = classifier
        self._context_builder = context_builder
        self._execution_manager = execution_manager
        self._query_logger = query_logger

    # ==========================================================
    # Execute
    # ==========================================================

    async def execute(
        self,
        request: QueryRequest,
    ) -> QueryResult:

        if request is None:
            raise ValueError(
                "QueryRequest cannot be None."
            )

        execution = self._create_execution(
            request
        )

        context: QueryContext | None = None

        try:

            # --------------------------------------------------
            # 1. Start Execution
            # --------------------------------------------------

            execution = await (
                self._execution_manager.start(
                    execution
                )
            )

            # --------------------------------------------------
            # 2. Build Context
            # --------------------------------------------------

            context = await (
                self._context_builder.build(
                    request
                )
            )

            if context is None:
                raise RuntimeError(
                    "QueryContextBuilder returned None."
                )

            # --------------------------------------------------
            # 3. Classify
            # --------------------------------------------------

            context = await self._classify(
                request=request,
                context=context,
            )

            # --------------------------------------------------
            # 4. Synchronize Execution
            # --------------------------------------------------

            execution.source = (
                context.source
            )

            execution.intent = (
                context.intent
            )

            execution.priority = (
                context.priority
            )

            execution.execution_mode = (
                context.execution_mode
            )

            # --------------------------------------------------
            # 5. Log Started
            # --------------------------------------------------

            await self._log_started(
                request=request,
                context=context,
            )

            # --------------------------------------------------
            # 6. Route
            # --------------------------------------------------

            result = await self._router.route(
                request=request,
                context=context,
            )

            if result is None:
                raise RuntimeError(
                    "QueryRouter returned None."
                )

            # --------------------------------------------------
            # 7. Complete / Fail
            # --------------------------------------------------

            if result.success:

                execution = await (
                    self._execution_manager.complete(
                        execution
                    )
                )

                if not context.is_terminal:
                    context.mark_completed()

                await self._log_completed(
                    request=request,
                    context=context,
                    result=result,
                )

            else:

                error = (
                    result.error
                    or "Query execution failed."
                )

                execution = await (
                    self._execution_manager.fail(
                        execution,
                        error,
                    )
                )

                if not context.is_terminal:
                    context.mark_failed(
                        error
                    )

                await self._log_failed(
                    request=request,
                    context=context,
                    error=error,
                )

            # --------------------------------------------------
            # 8. Final Result
            # --------------------------------------------------

            return self._finalize_result(
                request=request,
                context=context,
                execution=execution,
                result=result,
            )

        except Exception as exc:

            error = str(exc)

            await self._fail_execution(
                execution=execution,
                error=error,
            )

            if context is not None:

                try:

                    if not context.is_terminal:
                        context.mark_failed(
                            error
                        )

                except Exception:

                    logger.exception(
                        "[QueryEngine] "
                        "Failed to update QueryContext."
                    )

                await self._log_failed(
                    request=request,
                    context=context,
                    error=error,
                )

            logger.exception(
                "[QueryEngine] "
                "Query execution failed | "
                "query_id=%s",
                request.query_id,
            )

            return QueryResult(
                success=False,
                error=error,
                query_id=request.query_id,
                metadata={
                    "query_engine": (
                        self.__class__.__name__
                    ),
                    "execution_status": (
                        execution.status.value
                    ),
                    "attempt": execution.attempt,
                    "query_source": (
                        execution.source.value
                    ),
                },
            )

    # ==========================================================
    # Create Execution
    # ==========================================================

    @staticmethod
    def _create_execution(
        request: QueryRequest,
    ) -> QueryExecution:

        return QueryExecution(
            query_id=request.query_id,
            status=QueryStatus.PENDING,
            source=QuerySource.CHAT_DATABASE,
            intent=QueryIntent.UNKNOWN,
            priority=QueryPriority.NORMAL,
        )

    # ==========================================================
    # Classification
    # ==========================================================

    async def _classify(
        self,
        request: QueryRequest,
        context: QueryContext,
    ) -> QueryContext:

        classified_context = await (
            self._classifier.classify(
                request
            )
        )

        if classified_context is None:
            raise RuntimeError(
                "QueryClassifier returned None."
            )

        context.intent = (
            classified_context.intent
        )

        if classified_context.metadata:

            context.metadata.update(
                classified_context.metadata
            )

        return context

    # ==========================================================
    # Finalize
    # ==========================================================

    @staticmethod
    def _finalize_result(
        request: QueryRequest,
        context: QueryContext,
        execution: QueryExecution,
        result: QueryResult,
    ) -> QueryResult:

        result.query_id = (
            request.query_id
        )

        result.metadata = {
            **result.metadata,

            "query_intent": (
                context.intent.value
            ),

            "query_source": (
                context.source.value
            ),

            "execution_mode": (
                context.execution_mode.value
            ),

            "priority": (
                context.priority.value
            ),

            "execution_status": (
                execution.status.value
            ),

            "attempt": execution.attempt,

            "max_attempts": (
                execution.max_attempts
            ),

            "query_duration_ms": (
                context.duration_ms
            ),
        }

        return result

    # ==========================================================
    # Fail Execution
    # ==========================================================

    async def _fail_execution(
        self,
        execution: QueryExecution,
        error: str,
    ) -> None:

        try:

            if (
                execution is not None
                and not execution.is_terminal
            ):

                await self._execution_manager.fail(
                    execution,
                    error,
                )

        except Exception:

            logger.exception(
                "[QueryEngine] "
                "Failed to update QueryExecution."
            )

    # ==========================================================
    # Logging
    # ==========================================================

    async def _log_started(
        self,
        request: QueryRequest,
        context: QueryContext,
    ) -> None:

        if self._query_logger is None:
            return

        try:

            await self._query_logger.log_started(
                request=request,
                context=context,
            )

        except Exception:

            logger.exception(
                "[QueryEngine] "
                "Failed to log query start."
            )

    async def _log_completed(
        self,
        request: QueryRequest,
        context: QueryContext,
        result: QueryResult,
    ) -> None:

        if self._query_logger is None:
            return

        try:

            await self._query_logger.log_completed(
                request=request,
                context=context,
                result=result,
            )

        except Exception:

            logger.exception(
                "[QueryEngine] "
                "Failed to log query completion."
            )

    async def _log_failed(
        self,
        request: QueryRequest,
        context: QueryContext,
        error: str,
    ) -> None:

        if self._query_logger is None:
            return

        try:

            await self._query_logger.log_failed(
                request=request,
                context=context,
                error=error,
            )

        except Exception:

            logger.exception(
                "[QueryEngine] "
                "Failed to log query failure."
            )

    # ==========================================================
    # Properties
    # ==========================================================

    @property
    def router(self) -> QueryRouter:
        return self._router

    @property
    def classifier(self) -> QueryClassifier:
        return self._classifier

    @property
    def context_builder(
        self,
    ) -> QueryContextBuilder:
        return self._context_builder

    @property
    def execution_manager(
        self,
    ) -> QueryExecutionManager:
        return self._execution_manager

    @property
    def query_logger(
        self,
    ) -> QueryLogger | None:
        return self._query_logger

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
    ) -> dict[str, object]:

        try:

            adapter_health = (
                await self._router.health_check()
            )

            all_healthy = (
                all(adapter_health.values())
                if adapter_health
                else True
            )

            return {
                "status": (
                    "healthy"
                    if all_healthy
                    else "unhealthy"
                ),
                "engine": (
                    self.__class__.__name__
                ),
                "adapters": adapter_health,
            }

        except Exception as exc:

            logger.exception(
                "[QueryEngine] "
                "Health check failed."
            )

            return {
                "status": "unhealthy",
                "engine": (
                    self.__class__.__name__
                ),
                "error": str(exc),
            }