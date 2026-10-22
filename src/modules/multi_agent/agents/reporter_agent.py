from __future__ import annotations
import logging
from src.modules.llm.application.services import LLMService
from src.modules.llm.domain.entities import LLMRequest, LLMMessage
from src.modules.llm.domain.value_objects import Role, ProviderName
from src.modules.multi_agent.domain.base_agent import BaseAgent
from src.modules.multi_agent.domain.bi_context import BIContext

logger = logging.getLogger(__name__)

class ReporterAgent(BaseAgent):
    """
    وكيل صياغة التقارير (Reporter Agent)
    """
    def __init__(
        self, 
        llm_service: LLMService, 
        default_provider: ProviderName = ProviderName.GEMINI,  
        default_model: str = "gemini-3.8-flash"# التعديل هنا: استخدمنا النموذج المضمون والشغال لديك
    ):
        super().__init__(llm_service)
        self._provider = default_provider
        self._model = default_model

    @property
    def name(self) -> str:
        return "Reporter_Agent"

    async def execute(self, context: BIContext) -> BIContext:
        self._log_start()

        if not context.success:
            logger.warning(f"[{self.name}] Context carries errors. Formatting fallback report.")
            context.final_report = "عذراً، لم نتمكن من إعداد التقرير بسبب مشكلة في استخراج أو تحليل البيانات."
            return context

        try:
            system_prompt = """
            You are a Data Analyst for a Business Intelligence platform.
            Your STRICT and ONLY task is to provide the final answer entirely in ARABIC (اللغة العربية).
            
            CRITICAL RULES FOR EXTREME SPEED:
            1. VERY SHORT: Write the final answer in ONE clear, direct sentence ONLY.
            2. NO FLUFF: DO NOT write introductions, headers, bullet points, summaries, or conclusions. 
            3. NO MARKDOWN: Do not use bold (**), headers (##), or any markdown formatting.
            4. Zero Data: If the data shows 0 or is empty, simply say "لا توجد بيانات مطابقة حالياً."
            5. Stop generating immediately after providing the specific requested data/number.
            """
            
            user_content = f"""
            User Question: {context.question}
            
            Key Insights (KPIs):
            {context.analysis_kpis}
            
            Give me the short answer in Arabic NOW:
            """

            request = LLMRequest(
                provider=self._provider,
                model=self._model,
                temperature=0.1,
                messages=[
                    LLMMessage(role=Role.SYSTEM, content=system_prompt.strip()),
                    LLMMessage(role=Role.USER, content=user_content.strip())
                ]
            )

            logger.info(f"[{self.name}] Drafting final executive report...")
            response = await self._llm.generate(request)

            context.final_report = response.content.strip()
            logger.info(f"[{self.name}] Final report drafted successfully.")
            self._log_completion()

        except Exception as e:
            logger.exception(f"[{self.name}] Critical error during report drafting.")
            context.add_error(self.name, str(e))
            context.final_report = "حدث خطأ غير متوقع أثناء صياغة التقرير النهائي."

        return context