from __future__ import annotations

import logging
import os
import httpx
from typing import Any, Dict

from src.modules.multi_agent.domain.bi_context import BIContext

logger = logging.getLogger(__name__)


class RAGTool:
    """
    RAG Tool (Robust & Smart Enterprise Edition)
    ============================================
    طبقة الربط بين Multi-Agent وبين خدمة RAG (عبر HTTP API).
    يتصل بسيرفر RAG المستقل على بورت 8001 باستخدام httpx مع دعم الاسترجاع الآمن (Fallback).
    """

    def __init__(self, base_url: str | None = None):
        self.name = "RAGTool"
        self.description = (
            "يستخدم للبحث في المستندات والملفات النصية "
            "واستخراج المعلومات واللوائح والسياسات ذات الصلة بالسؤال."
        )
        # ✅ توجيه RAGTool مباشرة إلى سيرفر الـ RAG المستقل على بورت 8001 عبر API
        self._base_url = (
            base_url or os.getenv("RAG_SERVICE_URL", "http://127.0.0.1:8001")
        ).rstrip("/")

    # ==========================================================
    # Public API
    # ==========================================================

    async def execute(
        self,
        inputs: dict[str, Any],
        context: BIContext,
    ) -> Any:
        query = self._extract_query(inputs=inputs, context=context)

        logger.info(
            "[Tool: %s] Executing RAG API query: %s",
            self.name,
            query,
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # --------------------------------------------------
                # 1. المحاولة الأولى باستخدام معرف الجلسة (Tenant Scope)
                # --------------------------------------------------
                response = await client.post(
                    f"{self._base_url}/api/v1/rag/query",
                    json={
                        "query": query,
                        "top_k": 20,  # ✅ جلب كمية كافية لتغطية كل المفاهيم
                        "tenant_id": context.session_id,
                    },
                )
                response.raise_for_status()
                result = response.json()

                # --------------------------------------------------
                # 2. خطة الطوارئ الذكية (Fallback): إذا لم يجد نتائج، نجرب بدون تحديد الجلسة
                # --------------------------------------------------
                if not result or result.get("total_retrieved", 0) == 0:
                    logger.warning(
                        "[Tool: %s] Zero results with session tenant. Forcing global fallback...",
                        self.name,
                    )
                    fallback_response = await client.post(
                        f"{self._base_url}/api/v1/rag/query",
                        json={
                            "query": query,
                            "top_k": 20,  # ✅ تعديل حاسم: توحيد الكمية في الـ Fallback لتجنب رفض الـ Validator
                            "tenant_id": None,  # إلغاء الفلتر لجلب الملف المتاح محلياً
                        },
                    )
                    if fallback_response.status_code == 200:
                        fallback_result = fallback_response.json()
                        if fallback_result.get("total_retrieved", 0) > 0:
                            result = fallback_result
                            logger.info(
                                "[Tool: %s] Global fallback succeeded. Retrieved: %s chunks.",
                                self.name,
                                result.get("total_retrieved", 0),
                            )

            # --------------------------------------------------
            # Validate Result
            # --------------------------------------------------
            if not result or not isinstance(result, dict):
                raise RuntimeError(
                    "RAG service returned an invalid or empty result."
                )

            total_found = result.get("total_retrieved", 0)
            if total_found == 0:
                logger.warning(f"[Tool: {self.name}] No relevant context found anywhere.")
                result["context"] = (
                    "لم يتم العثور على معلومات في المستندات المرفوعة تفيد في الإجابة على هذا السؤال."
                )

            # --------------------------------------------------
            # Store Result in Context
            # --------------------------------------------------
            self._store_result(result=result, context=context)

            logger.info(
                "[Tool: %s] RAG API retrieval completed. Found: %s chunks.",
                self.name,
                total_found,
            )

            return result

        except httpx.ConnectError as exc:
            logger.error(f"[Tool: {self.name}] Cannot connect to RAG API at {self._base_url}")
            context.add_error(self.name, f"Cannot connect to RAG API: {exc}")
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"[Tool: {self.name}] RAG API returned {exc.response.status_code}: "
                f"{exc.response.text[:200]}"
            )
            context.add_error(self.name, f"RAG API error ({exc.response.status_code})")
            raise
        except httpx.TimeoutException as exc:
            logger.error(f"[Tool: {self.name}] RAG API timeout after 60s")
            context.add_error(self.name, f"RAG API timeout: {exc}")
            raise
        except Exception as exc:
            logger.exception(f"[Tool: {self.name}] RAG execution failed.")
            context.add_error(self.name, str(exc))
            raise

    # ==========================================================
    # Query Extraction
    # ==========================================================

    @staticmethod
    def _extract_query(inputs: dict[str, Any], context: BIContext) -> str:
        query = inputs.get("query")
        if query is None:
            query = context.question
        query = str(query).strip()
        if not query:
            raise ValueError("RAG query cannot be empty.")
        return query

    # ==========================================================
    # Store Result
    # ==========================================================

    @staticmethod
    def _store_result(result: Dict[str, Any], context: BIContext) -> None:
        rag_context_text = result.get("context", "")
        context.rag_context = rag_context_text
        context.set_rag_result(result=result, context=rag_context_text)
        context.metadata["rag_citations"] = result.get("citations", [])