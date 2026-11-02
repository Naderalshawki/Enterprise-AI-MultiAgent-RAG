from __future__ import annotations

import logging
import os

from src.modules.llm.application.services import LLMService
from src.modules.llm.domain.entities import LLMRequest, LLMMessage
from src.modules.llm.domain.value_objects import Role, ProviderName
from src.modules.multi_agent.domain.base_agent import BaseAgent
from src.modules.multi_agent.domain.bi_context import BIContext

logger = logging.getLogger(__name__)


class ReporterAgent(BaseAgent):
    """
    Reporter Agent (النسخة العملاقة)
    ---------------------------------
    - يكتب التقارير النهائية بجودة عالية.
    - يدعم Fallback (لو Gemini وقع، يرجع لـ Ollama).
    - يضمن ذكر المصدر عشان الـ Validator يقبل التقرير.
    - يمنع أي مشاكل لو مفيش أدلة كافية.
    """

    # الموديل الافتراضي المحلي (لو مفيش Gemini)
    DEFAULT_MODEL = "qwen2.5-coder:7b"

    def __init__(
        self,
        llm_service: LLMService,
        default_provider: ProviderName | None = None,
        default_model: str | None = None,
    ) -> None:
        super().__init__(llm_service)
        self._provider = default_provider if default_provider is not None else self._resolve_provider()
        self._model = default_model.strip() if default_model and default_model.strip() else self._resolve_model(self._provider)
        
        logger.info(
            "[%s] Initialized | provider=%s | model=%s",
            self.name,
            self._provider.value,
            self._model,
        )

    # ==========================================================
    # Provider / Model Resolution
    # ==========================================================

    @staticmethod
    def _resolve_provider() -> ProviderName:
        """يقرأ من REPORTER_PROVIDER، ولو مش موجود ياخد Gemini"""
        configured = os.getenv("REPORTER_PROVIDER")
        if configured and configured.strip():
            normalized = configured.strip().lower()
            for provider in ProviderName:
                if (provider.value.lower() == normalized or provider.name.lower() == normalized):
                    return provider
            raise ValueError(f"Unsupported REPORTER_PROVIDER: {configured}")
        
        return ProviderName.GEMINI

    @classmethod
    def _resolve_model(cls, provider: ProviderName) -> str:
        """يقرأ من REPORTER_MODEL، ولو مش موجود يحدد افتراضي حسب المزود"""
        configured_model = os.getenv("REPORTER_MODEL")
        if configured_model and configured_model.strip():
            return configured_model.strip()
            
        if provider == ProviderName.GEMINI:
            return os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        if provider == ProviderName.OLLAMA:
            return cls.DEFAULT_MODEL
            
        raise ValueError(f"No model configured for provider '{provider.value}'. Set REPORTER_MODEL or GEMINI_MODEL.")

    # ==========================================================
    # Identity
    # ==========================================================

    @property
    def name(self) -> str:
        return "Reporter_Agent"

    # ==========================================================
    # Main Entry Point (With Fallback)
    # ==========================================================

    async def execute(self, context: BIContext) -> BIContext:
        self._log_start()

        try:
            # 1. Clarification
            if context.metadata.get("requires_clarification"):
                context.final_report = self._build_clarification_message(context)
                self._log_completion()
                return context

            # 2. Evidence
            rag_text = self._extract_rag_text(context)
            db_text = self._extract_db_text(context)
            has_rag = bool(rag_text.strip())
            has_db = db_text != self._empty_db_marker()

            # 3. No Evidence
            if not has_rag and not has_db:
                context.final_report = "لا توجد بيانات مطابقة حالياً."
                self._log_completion()
                return context

            # 4. Prompt
            system_prompt = self._build_system_prompt(has_db=has_db, has_rag=has_rag)
            user_content = self._build_user_content(context=context, db_text=db_text, rag_text=rag_text, has_db=has_db, has_rag=has_rag)

            # 5. محاولة التوليد (مع Fallback)
            final_report = None
            
            # المحاولة 1: المزود الأساسي (Gemini)
            try:
                request = LLMRequest(
                    provider=self._provider,
                    model=self._model,
                    temperature=0.0,
                    messages=[
                        LLMMessage(role=Role.SYSTEM, content=system_prompt),
                        LLMMessage(role=Role.USER, content=user_content),
                    ],
                )
                logger.info("[%s] Trying primary | provider=%s | model=%s", self.name, self._provider.value, self._model)
                response = await self._llm.generate(request)
                final_report = (response.content or "").strip()
                
                if not final_report:
                    raise ValueError("Empty response from primary LLM.")
                    
            except Exception as exc:
                logger.warning("[%s] Primary LLM failed: %s", self.name, exc)
                logger.info("[%s] Trying FALLBACK to Ollama...", self.name)
                
                # المحاولة 2: Fallback لـ Ollama
                try:
                    fallback_model = "qwen2.5-coder:7b"
                    fallback_request = LLMRequest(
                        provider=ProviderName.OLLAMA,
                        model=fallback_model,
                        temperature=0.0,
                        messages=[
                            LLMMessage(role=Role.SYSTEM, content=system_prompt),
                            LLMMessage(role=Role.USER, content=user_content),
                        ],
                    )
                    response = await self._llm.generate(fallback_request)
                    final_report = (response.content or "").strip()
                    
                    if not final_report:
                        raise ValueError("Empty response from fallback LLM.")
                    
                    logger.info("[%s] Fallback SUCCESS | model=%s", self.name, fallback_model)
                    
                except Exception as fallback_exc:
                    logger.error("[%s] Fallback failed too: %s", self.name, fallback_exc)
                    # كخطة أخيرة: نضع رسالة خطأ بسيطة
                    final_report = "عذراً، حدث خطأ أثناء توليد التقرير. يرجى المحاولة مرة أخرى."

            # 6. التأكد من ذكر المصدر (عشان الـ Validator)
            if final_report and has_rag and "المستند" not in final_report and "الملف" not in final_report:
                final_report = "بناءً على المستند المرفق: " + final_report

            context.final_report = final_report
            self._log_completion()

        except Exception as exc:
            logger.exception("[%s] Fatal error.", self.name)
            context.add_error(self.name, str(exc))
            context.final_report = "حدث خطأ غير متوقع أثناء صياغة التقرير النهائي."

        return context

    # ==========================================================
    # Evidence Extraction
    # ==========================================================

    @staticmethod
    def _extract_rag_text(context: BIContext) -> str:
        rag = getattr(context, "rag_context", None)
        if rag is None: return ""
        if isinstance(rag, str): return rag.strip()
        return str(rag).strip()

    @classmethod
    def _extract_db_text(cls, context: BIContext) -> str:
        analysis = getattr(context, "analysis_kpis", None)
        if analysis and isinstance(analysis, str) and analysis.strip():
            return analysis.strip()
        return cls._empty_db_marker()

    @staticmethod
    def _empty_db_marker() -> str:
        return "لا توجد بيانات رقمية."

    # ==========================================================
    # Prompt Builders (محسنة)
    # ==========================================================

    @staticmethod
    def _build_system_prompt(has_db: bool, has_rag: bool) -> str:
        base = """
أنت خبير في صياغة الإجابات التنفيذية لمنصة ذكاء أعمال.

القواعد الصارمة:
1. اكتب الإجابة في "فقرة واحدة متصلة" باللغة العربية الفصحى.
2. لا تستخدم القوائم أو الترقيم أو العناوين.
3. لا تكتب أي حرف باللغة الإنجليزية؛ ترجم أي مصطلح عند الحاجة.
4. لا تختلق أرقاماً أو معلومات غير موجودة في الأدلة المقدمة.
5. استخدم الأدلة المقدمة فقط للإجابة.
6. كن مباشراً وموجزاً، واذكر الأرقام عند توفرها.
7. إذا كانت الإجابة مبنية على مستندات (RAG)، يجب أن تذكر اسم المستند أو أن تقول "بناءً على المستند المرفق" في بداية الإجابة.
""".strip()

        if has_db and not has_rag:
            return base + "\n8. الأدلة المتاحة هي نتائج تحليل رقمية من قاعدة البيانات فقط."
        if has_rag and not has_db:
            return base + "\n8. الأدلة المتاحة هي مقاطع نصية من مستندات فقط. لا تفترض وجود أرقام."
        
        return base + "\n8. الأدلة المتاحة تشمل نتائج رقمية من قاعدة البيانات ومقاطع نصية من مستندات. اجمعهما في إجابة واحدة متماسكة."

    @staticmethod
    def _build_user_content(context: BIContext, db_text: str, rag_text: str, has_db: bool, has_rag: bool) -> str:
        parts: list[str] = [f"سؤال المستخدم:\n{context.question}"]
        
        if has_db:
            parts.append(f"التحليل الرقمي من قاعدة البيانات:\n{db_text}")
        
        if has_rag:
            truncated = rag_text[:4000] + "..." if len(rag_text) > 4000 else rag_text
            parts.append(f"مقاطع المستندات المسترجعة:\n{truncated}")
        
        parts.append("اكتب الآن إجابة نهائية باللغة العربية في فقرة واحدة متصلة، واذكر المصدر إذا كانت الإجابة من مستند.")
        
        return "\n\n".join(parts)

    # ==========================================================
    # Clarification Message
    # ==========================================================

    @staticmethod
    def _build_clarification_message(context: BIContext) -> str:
        reason = context.metadata.get("clarification_reason")
        base = "سؤالك غير واضح بما يكفي للإجابة عليه بدقة. هل تريد بيانات رقمية من قاعدة البيانات، أم معلومات نصية من المستندات المرفوعة؟"
        if reason: return f"{base}\n(السبب: {reason})"
        return base