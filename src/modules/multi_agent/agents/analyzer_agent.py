from __future__ import annotations

import json
import logging
import os

from src.modules.llm.application.services import LLMService
from src.modules.llm.domain.entities import LLMRequest, LLMMessage
from src.modules.llm.domain.value_objects import Role, ProviderName
from src.modules.multi_agent.domain.base_agent import BaseAgent
from src.modules.multi_agent.domain.bi_context import BIContext

logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Analyzer Agent
    --------------
    Analyzes data retrieved by the Query Engine and extracts
    business insights, trends, and KPIs.

    The LLM provider and model can be configured through
    environment variables.

    Environment variables:
        MODEL_PROVIDER=ollama
        OLLAMA_MODEL=llama3

    MODEL_PROVIDER takes precedence over LLM_PROVIDER.
    """

    # تم التعديل هنا فقط ليتوافق مع النموذج المحلي الخاص بك
    DEFAULT_MODEL = "llama3"

    def __init__(
        self,
        llm_service: LLMService,
        default_provider: ProviderName | None = None,
        default_model: str | None = None,
    ) -> None:
        super().__init__(llm_service)

        self._provider = (
            default_provider
            if default_provider is not None
            else self._resolve_provider()
        )

        # --- التعديل الجذري هنا ---
        # إذا كان المزود جيميناي، نتجاهل أي قيم قديمة ممررة من الـ Planner 
        # ونجبره على استخدام الموديل الصحيح أو الأحدث
        if self._provider and self._provider.name.upper() == "GEMINI":
            self._model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        else:
            self._model = (
                default_model
                or self._resolve_model(self._provider)
            )

    @staticmethod
    def _resolve_provider() -> ProviderName:
        """
        Resolve the provider from environment variables.

        Priority:
            1. MODEL_PROVIDER
            2. LLM_PROVIDER
            3. Ollama
        """

        configured_provider = (
            os.getenv("MODEL_PROVIDER")
            or os.getenv("LLM_PROVIDER")
        )

        if configured_provider:
            normalized = configured_provider.strip().lower()

            for provider in ProviderName:
                if (
                    provider.value.lower() == normalized
                    or provider.name.lower() == normalized
                ):
                    return provider

            raise ValueError(
                "Unsupported LLM provider configured for "
                f"AnalyzerAgent: {configured_provider}"
            )

        # Ollama is the local default for this agent.
        if hasattr(ProviderName, "OLLAMA"):
            return ProviderName.OLLAMA

        raise RuntimeError(
            "Ollama is not available in ProviderName."
        )

    @classmethod
    def _resolve_model(
        cls,
        provider: ProviderName,
    ) -> str:
        """
        Resolve the model from the provider-specific environment
        variable, with a safe local default for Ollama.
        """

        provider_name = provider.name.upper()
        model_env_name = f"{provider_name}_MODEL"

        configured_model = os.getenv(model_env_name)

        if configured_model and configured_model.strip():
            return configured_model.strip()

        if provider == ProviderName.OLLAMA:
            return cls.DEFAULT_MODEL

        # If another provider is explicitly selected, use its
        # configured model or leave a clear configuration error.
        raise ValueError(
            f"No model configured for provider '{provider.value}'. "
            f"Set {model_env_name} in your environment."
        )

    @property
    def name(self) -> str:
        return "Analyzer_Agent"

    async def execute(self, context: BIContext) -> BIContext:
        self._log_start()

        if not context.success or not context.raw_data:
            logger.warning(
                "[%s] No raw data available. Skipping analysis.",
                self.name,
            )
            context.analysis_kpis = (
                "لم يتم العثور على بيانات كافية لإجراء التحليل."
            )
            return context

        try:
            # تم التعديل هنا فقط لإجبار النموذج على الرد بالعربية
            system_prompt = """
أنت خبير في تحليل البيانات ومستشار ذكاء الأعمال (BI).
مهمتك هي تحليل بيانات JSON المقدمة بناءً على سؤال المستخدم.

القواعد الأساسية:
1. استخرج 2 إلى 4 مؤشرات أداء رئيسية (KPIs) أو استنتاجات من البيانات.
2. يجب أن يكون التحليل والرد باللغة العربية الفصحى حصراً.
3. استخدم النقاط (Bullet points) لسهولة القراءة.
4. لا تقم بكتابة استعلامات SQL أبداً.
5. لا تخترع أي أرقام أو استنتاجات غير مدعومة بالبيانات المرفقة.
6. إذا كانت البيانات فارغة (مثل count: 0)، وضح بأسلوب احترافي أنه لا توجد بيانات مسجلة حالياً تلبي طلب المستخدم.
""".strip()

            # Limit the amount of data sent to the LLM.
            limited_data = context.raw_data[:100]

            data_str = json.dumps(
                limited_data,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

            user_content = (
                f"User Question: {context.question}\n\n"
                f"Raw Data:\n{data_str}"
            )

            request = LLMRequest(
                provider=self._provider,
                model=self._model,
                temperature=0.3,
                messages=[
                    LLMMessage(
                        role=Role.SYSTEM,
                        content=system_prompt,
                    ),
                    LLMMessage(
                        role=Role.USER,
                        content=user_content,
                    ),
                ],
            )

            logger.info(
                "[%s] Analyzing %s rows using provider=%s, model=%s",
                self.name,
                len(context.raw_data),
                self._provider.value,
                self._model,
            )

            response = await self._llm.generate(request)

            analysis = (response.content or "").strip()

            if not analysis:
                raise ValueError(
                    "The LLM returned an empty analysis response."
                )

            context.analysis_kpis = analysis

            logger.info(
                "[%s] Analysis completed successfully.",
                self.name,
            )

            self._log_completion()

        except Exception as exc:
            logger.exception(
                "[%s] Critical error during analysis.",
                self.name,
            )
            context.add_error(self.name, str(exc))

        return context
