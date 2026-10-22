from __future__ import annotations

import logging
import asyncio
from typing import Any, Dict

from src.modules.multi_agent.domain.bi_context import BIContext
# استيراد المحول الخاص بزميلك كائن جاهز للاستخدام
from src.modules.rag.rag_tool_adapter import rag_tool_instance

logger = logging.getLogger(__name__)


class RAGTool:
    """
    RAG Tool
    ========

    طبقة الربط بين Multi-Agent وبين خدمة RAG المطورة.
    يقوم بالاتصال المباشر بـ rag_tool_adapter (بشكل غير متزامن)
    لاسترجاع السياق من المستندات.
    """

    def __init__(self):
        """
        إنشاء RAGTool.
        يعتمد الآن على النسخة المدمجة (Singleton) من rag_tool_adapter.
        """
        self.name = "RAGTool"
        self.description = (
            "يستخدم للبحث في المستندات والملفات النصية "
            "واستخراج المعلومات واللوائح والسياسات ذات الصلة بالسؤال."
        )
        self._adapter = rag_tool_instance

    # ==========================================================
    # Public API
    # ==========================================================

    async def execute(
        self,
        inputs: dict[str, Any],
        context: BIContext,
    ) -> Any:
        """
        تنفيذ مهمة البحث في المستندات.
        يتم تحويل الاتصال من Sync إلى Async لعدم إيقاف السيرفر.
        """

        query = self._extract_query(
            inputs=inputs,
            context=context,
        )

        logger.info(
            "[Tool: %s] Executing RAG query: %s",
            self.name,
            query,
        )

        try:
            # --------------------------------------------------
            # Execute RAG Adapter (Async Wrapper over Sync code)
            # --------------------------------------------------
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._adapter.search_knowledge(
                    query=query,
                    top_k=5,
                    tenant_id=None # يمكن استخدام session_id أو user_id كـ tenant إذا لزم الأمر
                )
            )

            # --------------------------------------------------
            # Validate Result
            # --------------------------------------------------
            if not result or not isinstance(result, dict):
                raise RuntimeError(
                    "RAG service returned an invalid or empty result."
                )

            total_found = result.get("total_found", 0)
            if total_found == 0:
                logger.warning(f"[Tool: {self.name}] No relevant context found for query: {query}")
                result["context"] = "لم يتم العثور على معلومات في المستندات تفيد في الإجابة على هذا السؤال."

            # --------------------------------------------------
            # Store Result in Context
            # --------------------------------------------------
            self._store_result(
                result=result,
                context=context,
            )

            logger.info(
                "[Tool: %s] RAG retrieval completed successfully. Found: %s chunks.",
                self.name,
                total_found
            )

            return result

        except Exception as exc:
            logger.exception(
                "[Tool: %s] RAG execution failed.",
                self.name,
            )

            context.add_error(
                self.name,
                str(exc),
            )

            raise

    # ==========================================================
    # Query Extraction
    # ==========================================================

    @staticmethod
    def _extract_query(
        inputs: dict[str, Any],
        context: BIContext,
    ) -> str:
        """
        استخراج سؤال البحث.
        """
        query = inputs.get("query")

        if query is None:
            query = context.question

        query = str(query).strip()

        if not query:
            raise ValueError(
                "RAG query cannot be empty."
            )

        return query

    # ==========================================================
    # Store Result
    # ==========================================================

    @staticmethod
    def _store_result(
        result: Dict[str, Any],
        context: BIContext,
    ) -> None:
        """
        تخزين نتيجة RAG (التي أعادها الـ Adapter) في BIContext 
        ليقرأها AnalysisTool و ReportTool لاحقاً.
        """
        rag_context_text = result.get("context", "")
        
        # حفظ النص الخام (الذي سيبني الـ LLM إجابته بناءً عليه)
        context.rag_context = rag_context_text

        # إعداد الـ MetaData الكاملة للرد النهائي
        context.set_rag_result(
            result=result,
            context=rag_context_text,
        )

        # دمج الاستشهادات (Citations) إن وجدت في الـ Metadata
        context.metadata["rag_citations"] = result.get("citations", [])