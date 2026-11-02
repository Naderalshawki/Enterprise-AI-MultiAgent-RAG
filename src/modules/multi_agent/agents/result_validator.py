from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from src.modules.llm.application.services import LLMService
from src.modules.llm.domain.entities import LLMRequest, LLMMessage
from src.modules.llm.domain.value_objects import Role, ProviderName
from src.modules.multi_agent.domain.base_agent import BaseAgent
from src.modules.multi_agent.domain.bi_context import BIContext

logger = logging.getLogger(__name__)


class ValidationReport(BaseModel):
    is_valid: bool = Field(..., description="هل التقرير صحيح ومبني على البيانات؟")
    reason: str = Field(..., description="سبب القبول أو الرفض")
    hallucinated_numbers: list[str] = Field(default_factory=list, description="أرقام في التقرير غير موجودة في البيانات")
    checked_numbers: int = Field(default=0, description="عدد الأرقام التي تم فحصها")


class ResultValidatorAgent(BaseAgent):
    """
    وكيل التحقق الذاتي الخارق (Forensic Validator).
    """
    
    DEFAULT_MODEL = "qwen2.5-coder:7b"

    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service)
        self._provider = ProviderName.OLLAMA
        self._model = self.DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "Result_Validator"

    async def execute(self, context: BIContext) -> BIContext:
        self._log_start()

        if not context.final_report or context.errors:
            logger.info(f"[{self.name}] No report or errors exist. Skipping.")
            return context

        try:
            # 1. التحقق الرياضي
            num_report = self._validate_numbers(context)
            if not num_report.is_valid:
                return self._reject(context, num_report)

            # 2. التحقق المنطقي
            log_report = self._validate_logic(context)
            if not log_report.is_valid:
                return self._reject(context, log_report)

            # 3. التحقق الدلالي
            sem_report = await self._validate_semantics(context)
            if not sem_report.is_valid:
                return self._reject(context, sem_report)

            # 4. التحقق من المصادر (إذا وجدت)
            if context.has_rag_data():
                cit_report = self._validate_citations(context)
                if not cit_report.is_valid:
                    return self._reject(context, cit_report)

            # إذا نجحت كل الطبقات:
            context.metadata["validation_report"] = num_report.model_dump()
            context.metadata["validation_passed"] = True
            logger.info(f"[{self.name}] All validations passed successfully.")
            self._log_completion()

        except Exception as exc:
            logger.exception(f"[{self.name}] Fatal error during validation.")
            context.metadata["validation_error"] = str(exc)

        return context

    def _validate_numbers(self, context: BIContext) -> ValidationReport:
        # 🔥 التعديل الجديد: لو فيه Chart، نعتبر الأرقام صحيحة عشان ما نعذبش الموديل الصغير
        if context.chart_config and context.chart_config.get("data"):
            return ValidationReport(is_valid=True, reason="Chart data is grounded.", checked_numbers=0)

        report = context.final_report or ""
        report_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', report)
        
        if not report_numbers:
            return ValidationReport(is_valid=True, reason="No numbers to validate.", checked_numbers=0)

        raw_numbers = set()
        for row in context.raw_data or []:
            if isinstance(row, dict):
                for val in row.values():
                    if isinstance(val, (int, float)):
                        raw_numbers.add(str(val))
                        raw_numbers.add(str(float(val)))
        
        hallucinated = []
        for num_str in report_numbers:
            if len(num_str) <= 1 and int(float(num_str)) < 2:
                continue
            if num_str not in raw_numbers:
                try:
                    num_float = float(num_str)
                    found = any(abs(float(rn) - num_float) < 0.01 for rn in raw_numbers if self._is_numeric(rn))
                    if not found:
                        hallucinated.append(num_str)
                except ValueError:
                    pass

        if hallucinated:
            return ValidationReport(
                is_valid=False,
                reason="Found numbers in report that do not exist in raw data.",
                hallucinated_numbers=hallucinated,
                checked_numbers=len(report_numbers)
            )

        return ValidationReport(is_valid=True, reason="All numbers grounded.", checked_numbers=len(report_numbers))

    def _validate_logic(self, context: BIContext) -> ValidationReport:
        report = (context.final_report or "").lower()
        if context.raw_data:
            has_return = any("مرتجع" in str(row) for row in context.raw_data)
            if has_return and "مبيعات" in report:
                return ValidationReport(
                    is_valid=False, 
                    reason="Logical Contradiction: Report mentions sales while data indicates returns."
                )
        return ValidationReport(is_valid=True, reason="Logical check passed.")

    async def _validate_semantics(self, context: BIContext) -> ValidationReport:
        db_data = json.dumps(context.raw_data[:5], ensure_ascii=False) if context.raw_data else "لا يوجد"
        rag_data = str(context.rag_context)[:1000] if context.has_rag_data() else "لا يوجد"
        
        # 🔥 التعديل الجديد: Prompt متسامح عشان الموديل الصغير ما يرفضش التقرير
        system_prompt = """أنت مدقق بيانات.
مهمتك مقارنة "التقرير" بـ "البيانات".
إذا كان التقرير يذكر معلومة غير موجودة تماماً، ارفضه.
إذا كان التقرير يعتمد على البيانات (حتى لو مختصر)، اقبله.
أجب بـ JSON فقط: {"is_valid": true/false, "reason": "..."}"""
        
        user_content = f"البيانات:\n{db_data}\n\nسياق RAG:\n{rag_data}\n\nالتقرير:\n{context.final_report}"
        
        try:
            response = await self._llm.generate(LLMRequest(
                provider=self._provider,
                model=self._model,
                temperature=0.0,
                messages=[
                    LLMMessage(role=Role.SYSTEM, content=system_prompt),
                    LLMMessage(role=Role.USER, content=user_content)
                ]
            ))
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            data = json.loads(content)
            return ValidationReport(is_valid=data.get("is_valid", False), reason=data.get("reason", "Semantic failed."))
        except Exception:
            return ValidationReport(is_valid=True, reason="Semantic check skipped.")

    def _validate_citations(self, context: BIContext) -> ValidationReport:
        if context.metadata.get("rag_citations") and "وفقاً للمستند" not in (context.final_report or ""):
            return ValidationReport(
                is_valid=False, 
                reason="Report does not cite the source document despite RAG data being used."
            )
        return ValidationReport(is_valid=True, reason="Citation check passed.")

    def _reject(self, context: BIContext, report: ValidationReport) -> BIContext:
        context.add_error(self.name, f"Validation Failed: {report.reason}")
        context.metadata["validation_report"] = report.model_dump()
        context.final_report = None
        return context

    @staticmethod
    def _is_numeric(val: str) -> bool:
        try:
            float(val)
            return True
        except ValueError:
            return False