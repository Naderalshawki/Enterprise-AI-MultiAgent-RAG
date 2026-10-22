from __future__ import annotations

import logging
from typing import Dict

from src.modules.query_engine.domain.entities import (
    QueryContext,
    QueryRequest,
    QueryResult,
)
from src.modules.query_engine.domain.enums import (
    QueryIntent,
    QuerySource,
)
from src.modules.query_engine.domain.interfaces import (
    QuerySourceAdapter,
)

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    المسؤول عن توجيه Query إلى مصدر البيانات المناسب.

    QueryRouter لا يقوم بـ:
        - تصنيف السؤال.
        - إنشاء QueryContext.
        - توليد SQL.
        - تنفيذ RAG.

    دوره فقط:
        توجيه الـ QueryContext إلى الـ Adapter المناسب.

    في الإصدار الحالي:
        QuerySource.CHAT_DATABASE -> ChatDatabaseAdapter
        QuerySource.MULTI_AGENT -> MultiAgentAdapter (يدير SQL و RAG معاً)
    """

    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(
        self,
        adapters: dict[str, QuerySourceAdapter] | None = None,
    ) -> None:
        """
        إنشاء QueryRouter.
        """
        self._adapters: Dict[str, QuerySourceAdapter] = {}

        if adapters:
            for name, adapter in adapters.items():
                self.register_adapter(name, adapter)

    # ==========================================================
    # Route
    # ==========================================================

    async def route(
        self,
        request: QueryRequest,
        context: QueryContext,
    ) -> QueryResult:
        """
        توجيه الاستعلام إلى الـAdapter المناسب بناءً على التصنيف (Intent).
        """

        if request is None:
            raise ValueError("QueryRequest cannot be None.")

        if context is None:
            raise ValueError("QueryContext cannot be None.")

        # التوجيه الذكي بناءً على النية التي حددها المصنف (Classifier)
        if context.intent == QueryIntent.DOCUMENT:
            # إذا كان السؤال يخص المستندات (RAG)، نوجهه لوكيل المهام المتعددة (MultiAgent)
            # لأن Planner هو من يملك أداة RAGTool
            source_name = QuerySource.MULTI_AGENT.value
            logger.info("[QueryRouter] Intent is DOCUMENT. Routing to MULTI_AGENT.")
        else:
            # للبيانات والأرقام وباقي النوايا، يعتمد على المصدر الافتراضي (غالباً ChatDatabase)
            source_name = context.source.value

        adapter = self._resolve_adapter(source_name)

        logger.info(
            "[QueryRouter] Routing query | query_id=%s | source=%s | intent=%s",
            request.query_id,
            source_name,
            context.intent.value if context.intent else "unknown",
        )

        result = await adapter.execute(
            request=request,
            context=context,
        )

        if result is None:
            raise RuntimeError("QuerySourceAdapter returned None.")

        return result

    # ==========================================================
    # Resolve Adapter
    # ==========================================================

    def _resolve_adapter(self, source_name: str) -> QuerySourceAdapter:
        """الحصول على Adapter حسب اسم المصدر."""
        if not source_name:
            raise ValueError("Query source cannot be empty.")

        adapter = self._adapters.get(source_name)

        if adapter is None:
            raise ValueError(f"No QuerySourceAdapter registered for source: {source_name}")

        return adapter

    # ==========================================================
    # Register Adapter
    # ==========================================================

    def register_adapter(self, source_name: str, adapter: QuerySourceAdapter) -> None:
        if not source_name:
            raise ValueError("source_name cannot be empty.")

        if adapter is None:
            raise ValueError("adapter cannot be None.")

        if not isinstance(adapter, QuerySourceAdapter):
            raise TypeError("adapter must implement QuerySourceAdapter.")

        if source_name in self._adapters:
            raise ValueError(f"Adapter already registered for source: {source_name}")

        self._adapters[source_name] = adapter
        logger.info("[QueryRouter] Adapter registered | source=%s", source_name)

    # ==========================================================
    # Unregister Adapter
    # ==========================================================

    def unregister_adapter(self, source_name: str) -> bool:
        if not source_name:
            return False

        adapter = self._adapters.pop(source_name, None)
        if adapter is None:
            return False

        logger.info("[QueryRouter] Adapter unregistered | source=%s", source_name)
        return True

    # ==========================================================
    # Get/Has Adapter
    # ==========================================================

    def get_adapter(self, source_name: str) -> QuerySourceAdapter | None:
        return self._adapters.get(source_name)

    def has_adapter(self, source_name: str) -> bool:
        return source_name in self._adapters

    # ==========================================================
    # Supported Sources & Intents
    # ==========================================================

    @property
    def supported_sources(self) -> tuple[str, ...]:
        return tuple(self._adapters.keys())

    @staticmethod
    def is_supported_intent(intent: QueryIntent) -> bool:
        """
        التحقق من أن Intent مدعوم.
        تمت إضافة DOCUMENT ليتعرف النظام على أسئلة المستندات (RAG).
        """
        return intent in {
            QueryIntent.DATA,
            QueryIntent.DOCUMENT,  # التعديل هنا لدعم الـ RAG
            QueryIntent.SCHEMA,
            QueryIntent.DATABASE_INFO,
        }

    # ==========================================================
    # Health Check
    # ==========================================================

    async def health_check(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for source_name, adapter in self._adapters.items():
            try:
                results[source_name] = await adapter.health_check()
            except Exception:
                logger.exception(
                    "[QueryRouter] Adapter health check failed | source=%s",
                    source_name,
                )
                results[source_name] = False
        return results