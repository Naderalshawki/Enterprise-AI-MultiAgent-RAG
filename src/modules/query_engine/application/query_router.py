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
        - تنفيذ RAG مباشرة.

    دوره فقط:
        توجيه QueryContext إلى الـ Adapter المناسب.

    المصادر المدعومة تعتمد على الـ Adapters المسجلة فعليًا.

    عند توفر MultiAgentAdapter:
        QuerySource.MULTI_AGENT -> MultiAgentAdapter

    وعند توفر ChatDatabaseAdapter:
        QuerySource.CHAT_DATABASE -> ChatDatabaseAdapter

    ملاحظة:
        تنفيذ RAG الفعلي يتم من خلال RAGTool داخل Multi-Agent،
        وليس داخل QueryRouter نفسه.
    """

    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(
        self,
        adapters: dict[str, QuerySourceAdapter] | None = None,
    ) -> None:
        """إنشاء QueryRouter وتسجيل مصادر البيانات المتاحة."""

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
        توجيه الاستعلام إلى الـ Adapter المناسب.

        DOCUMENT:
            يستخدم MultiAgent إذا كان مسجلاً،
            وإلا يحاول استخدام context.source.

        بقية النوايا:
            تستخدم context.source مباشرة.
        """

        if request is None:
            raise ValueError("QueryRequest cannot be None.")

        if context is None:
            raise ValueError("QueryContext cannot be None.")

        # المصدر الافتراضي المحدد في سياق الاستعلام
        source_name = context.source.value

        # أسئلة المستندات: استخدام Multi-Agent عند توفره
        if context.intent == QueryIntent.DOCUMENT:
            multi_agent_source = QuerySource.MULTI_AGENT.value

            if self.has_adapter(multi_agent_source):
                source_name = multi_agent_source

                logger.info(
                    "[QueryRouter] DOCUMENT intent. "
                    "Routing to MULTI_AGENT."
                )
            else:
                logger.warning(
                    "[QueryRouter] DOCUMENT intent, but no "
                    "MULTI_AGENT adapter is registered. "
                    "Falling back to context.source=%s.",
                    source_name,
                )

        # حل الـ Adapter الفعلي
        adapter = self._resolve_adapter(source_name)

        logger.info(
            "[QueryRouter] Routing query | query_id=%s | "
            "source=%s | intent=%s",
            request.query_id,
            source_name,
            context.intent.value if context.intent else "unknown",
        )

        # تنفيذ الاستعلام من خلال الـ Adapter
        result = await adapter.execute(
            request=request,
            context=context,
        )

        if result is None:
            raise RuntimeError(
                "QuerySourceAdapter returned None."
            )

        return result

    # ==========================================================
    # Resolve Adapter
    # ==========================================================

    def _resolve_adapter(
        self,
        source_name: str,
    ) -> QuerySourceAdapter:
        """الحصول على Adapter مسجل حسب اسم المصدر."""

        if not source_name:
            raise ValueError("Query source cannot be empty.")

        adapter = self._adapters.get(source_name)

        if adapter is None:
            # التوجيه التلقائي لتجاوز هلوسة النماذج المحلية
            fallback_source = "chat_database"
            if fallback_source in self._adapters:
                logger.warning(f"[QueryRouter] Source '{source_name}' not found. Falling back to '{fallback_source}'.")
                return self._adapters[fallback_source]
            elif self._adapters:
                # إذا لم يجد الافتراضية، يأخذ أول قاعدة بيانات متاحة
                fallback_source = next(iter(self._adapters.keys()))
                logger.warning(f"[QueryRouter] Source '{source_name}' not found. Falling back to '{fallback_source}'.")
                return self._adapters[fallback_source]
            else:
                available_sources = ", ".join(self.supported_sources) or "none"
                raise ValueError(
                    f"No QuerySourceAdapter registered for source: {source_name}. "
                    f"Available sources: {available_sources}"
                )

        return adapter

    # ==========================================================
    # Register Adapter
    # ==========================================================

    def register_adapter(
        self,
        source_name: str,
        adapter: QuerySourceAdapter,
    ) -> None:
        """تسجيل Adapter جديد."""

        if not source_name:
            raise ValueError(
                "source_name cannot be empty."
            )

        if adapter is None:
            raise ValueError(
                "adapter cannot be None."
            )

        if not isinstance(adapter, QuerySourceAdapter):
            raise TypeError(
                "adapter must implement QuerySourceAdapter."
            )

        if source_name in self._adapters:
            raise ValueError(
                f"Adapter already registered for source: "
                f"{source_name}"
            )

        self._adapters[source_name] = adapter

        logger.info(
            "[QueryRouter] Adapter registered | source=%s",
            source_name,
        )

    # ==========================================================
    # Unregister Adapter
    # ==========================================================

    def unregister_adapter(
        self,
        source_name: str,
    ) -> bool:
        """إلغاء تسجيل Adapter."""

        if not source_name:
            return False

        adapter = self._adapters.pop(
            source_name,
            None,
        )

        if adapter is None:
            return False

        logger.info(
            "[QueryRouter] Adapter unregistered | source=%s",
            source_name,
        )

        return True

    # ==========================================================
    # Get / Has Adapter
    # ==========================================================

    def get_adapter(
        self,
        source_name: str,
    ) -> QuerySourceAdapter | None:
        """إرجاع Adapter إن كان مسجلاً."""

        return self._adapters.get(source_name)

    def has_adapter(
        self,
        source_name: str,
    ) -> bool:
        """التحقق من وجود Adapter مسجل."""

        return source_name in self._adapters

    # ==========================================================
    # Supported Sources & Intents
    # ==========================================================

    @property
    def supported_sources(self) -> tuple[str, ...]:
        """المصادر المسجلة فعليًا."""

        return tuple(self._adapters.keys())

    @staticmethod
    def is_supported_intent(
        intent: QueryIntent,
    ) -> bool:
        """التحقق من أن نوع الاستعلام مدعوم."""

        return intent in {
            QueryIntent.DATA,
            QueryIntent.DOCUMENT,
            QueryIntent.SCHEMA,
            QueryIntent.DATABASE_INFO,
        }

    # ==========================================================
    # Health Check
    # ==========================================================

    async def health_check(self) -> dict[str, bool]:
        """فحص حالة جميع الـ Adapters المسجلة."""

        results: dict[str, bool] = {}

        for source_name, adapter in self._adapters.items():
            try:
                results[source_name] = (
                    await adapter.health_check()
                )

            except Exception:
                logger.exception(
                    "[QueryRouter] Adapter health check failed "
                    "| source=%s",
                    source_name,
                )

                results[source_name] = False

        return results