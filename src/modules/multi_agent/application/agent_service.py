# from __future__ import annotations

# import logging
# import time
# import uuid
# from typing import Any

# from src.modules.llm.application.services import LLMService

# from src.modules.memory.application.dtos import SaveMemoryRequest
# from src.modules.memory.application.services import MemoryService
# from src.modules.memory.domain.value_objects import (
#     MemoryImportance,
#     MemoryType,
# )

# from src.modules.multi_agent.agents.analyzer_agent import AnalyzerAgent
# from src.modules.multi_agent.agents.reporter_agent import ReporterAgent
# from src.modules.multi_agent.agents.result_validator import ResultValidatorAgent
# from src.modules.multi_agent.application.executor import TaskExecutor
# from src.modules.multi_agent.application.planner import Planner
# from src.modules.multi_agent.domain.bi_context import BIContext
# from src.modules.multi_agent.domain.contracts import ToolResult
# from src.modules.multi_agent.tools.database_tool import DatabaseTool
# from src.modules.multi_agent.tools.rag_tool import RAGTool

# from src.modules.query_engine.domain.interfaces import QueryEngine


# logger = logging.getLogger(__name__)


# class AgentService:
#     r"""
#     الخدمة الرئيسية الخاصة بـMulti-Agent BI Platform.

#     تمثل طبقة orchestration العليا التي تدير رحلة السؤال كاملة:

#         User Question
#               ↓
#             Memory
#               ↓
#             Planner
#               ↓
#              Plan
#               ↓
#          TaskExecutor
#            /    |    \
#           /     |     \
#      Database  RAG   Analysis
#           \     |     /
#               ↓
#          Result Validator (Self-Correction)
#               ↓
#            Reporter
#               ↓
#          Final Response
#               ↓
#             Memory

#     AgentService مسؤول عن:
#         - إنشاء BIContext.
#         - تحميل Memory المناسبة.
#         - استدعاء Planner.
#         - تنفيذ الخطة.
#         - تمرير السياق بين المكونات.
#         - حفظ النتيجة في Memory.
#         - إدارة أخطاء orchestration.
#         - توفير عقد ToolResult للباك إند.
#         - تسجيل خطوات التنفيذ (Trace) للعرض في الواجهة.

#     AgentService لا:
#         - ينفذ SQL مباشرة.
#         - ينفذ RAG مباشرة.
#         - يحلل البيانات بنفسه.
#         - يتعامل مع Repository الخاص بالـMemory مباشرة.
#         - ينفذ منطق المصادقة أو Multi-Tenant.
#     """

#     # ==========================================================
#     # Initialization
#     # ==========================================================

#     def __init__(
#         self,
#         llm_service: LLMService,
#         query_engine: QueryEngine,
#         memory_service: MemoryService | None = None,
#         rag_service=None,
#         validator_agent: ResultValidatorAgent | None = None,
#     ) -> None:
#         """
#         إنشاء AgentService.

#         Parameters
#         ----------
#         llm_service:
#             خدمة LLM المشتركة.

#         query_engine:
#             Query Engine المسؤولة عن تنفيذ استعلامات
#             قاعدة البيانات.

#         memory_service:
#             MemoryService المسؤول عن قراءة وحفظ الذاكرة.

#         rag_service:
#             غير مستخدم حالياً. RAGTool يتصل مباشرة بنظام المستندات.

#         validator_agent:
#             وكيل التحقق الذاتي (Self-Correction).
#         """

#         if llm_service is None:
#             raise ValueError("llm_service cannot be None.")

#         if query_engine is None:
#             raise ValueError("query_engine cannot be None.")

#         self._llm = llm_service
#         self._query_engine = query_engine
#         self._memory = memory_service
#         self._validator = validator_agent

#         # ======================================================
#         # Planner
#         # ======================================================

#         self.planner = Planner(llm_service=self._llm)

#         # ======================================================
#         # Tools Registry
#         # ======================================================

#         self.tool_registry = {
#             "DatabaseTool": DatabaseTool(
#                 query_engine=self._query_engine,
#             ),
#             "RAGTool": RAGTool(),
#         }

#         # ======================================================
#         # Specialist Agents
#         # ======================================================

#         self.analyzer = AnalyzerAgent(llm_service=self._llm)

#         self.reporter = ReporterAgent(llm_service=self._llm)

#         # ======================================================
#         # Executor
#         # ======================================================

#         self.executor = TaskExecutor(
#             tools_registry=self.tool_registry,
#             analyzer_agent=self.analyzer,
#             reporter_agent=self.reporter,
#         )

#         logger.info(
#             "[AgentService] Initialized successfully with Database, RAG, and Validator tools."
#         )

#     # ==========================================================
#     # Public API (Primary) — returns BIContext
#     # ==========================================================

#     async def process_question(
#         self,
#         question: str,
#         user_id: str,
#         session_id: str | None = None,
#         tenant_id: str = "default-tenant",
#     ) -> BIContext:
#         """
#         معالجة سؤال المستخدم من البداية إلى النهاية.
#         """

#         # ------------------------------------------------------
#         # 1. Validate input
#         # ------------------------------------------------------

#         question = self._normalize_question(question)

#         if not question:

#             context = BIContext(
#                 question="",
#                 user_id=user_id,
#                 session_id=(session_id or str(uuid.uuid4())),
#             )

#             context.add_error(
#                 "AgentService",
#                 "Question cannot be empty.",
#             )

#             return context

#         # ------------------------------------------------------
#         # 2. Create Context
#         # ------------------------------------------------------

#         context = BIContext(
#             question=question,
#             user_id=user_id,
#             session_id=(session_id or str(uuid.uuid4())),
#         )

#         logger.info(
#             "[AgentService] Processing question | session_id=%s | tenant_id=%s",
#             context.session_id,
#             tenant_id,
#         )

#         try:

#             # ==================================================
#             # 3. Load Memory
#             # ==================================================

#             await self._load_memory_into_context(context)

#             # ==================================================
#             # 4. Create Execution Plan
#             # ==================================================
#             start_plan = time.time()
#             plan = await self._create_plan(question=context.question)

#             context.trace_steps.append({
#                 "step": "planning",
#                 "title": "التخطيط (Planner)",
#                 "duration_ms": int((time.time() - start_plan) * 1000),
#                 "details": f"تم إنشاء خطة بـ {len(plan.tasks)} مهام."
#             })

#             # --------------------------------------------------
#             # Record plan information for observability
#             # --------------------------------------------------

#             context.metadata["plan"] = {
#                 "status": plan.status.value,
#                 "task_count": len(plan.tasks),
#                 "generated_by": plan.metadata.get("generated_by"),
#                 "planner_model": plan.metadata.get("planner_model"),
#                 "detected_source": plan.metadata.get("detected_source"),
#                 "requires_clarification": bool(
#                     plan.metadata.get("requires_clarification")
#                 ),
#             }

#             # --------------------------------------------------
#             # Infer selected sources from the Plan
#             # --------------------------------------------------

#             self._update_source_information(
#                 context=context,
#                 plan=plan,
#             )

#             # ==================================================
#             # 5. Execute Plan
#             # ==================================================
#             start_exec = time.time()
#             context = await self.executor.execute_plan(
#                 plan=plan,
#                 context=context,
#             )

#             context.trace_steps.append({
#                 "step": "execution",
#                 "title": "التنفيذ (Executor)",
#                 "duration_ms": int((time.time() - start_exec) * 1000),
#                 "details": f"تم تنفيذ المهام. حالة الخطة: {plan.status.value}"
#             })

#             # ==================================================
#             # 5.5. Self-Correction (التحقق الجنائي)
#             # ==================================================
#             # 🔥 حماية: لا يعمل الـ Validator إلا إذا كان هناك تقرير نهائي حقيقي
            
#             if self._validator and context.final_report and context.final_report.strip():
#                 start_val = time.time()
#                 context = await self._validator.execute(context)
                
#                 val_passed = context.metadata.get("validation_passed", False)
#                 val_report = context.metadata.get("validation_report", {})
                
#                 details = "نجح التحقق من البيانات."
#                 if not val_passed:
#                     details = f"فشل التحقق: {val_report.get('reason', 'سبب غير معروف')}"

#                 context.trace_steps.append({
#                     "step": "validation",
#                     "title": "التحقق (Validator)",
#                     "duration_ms": int((time.time() - start_val) * 1000),
#                     "details": details
#                 })

#             # ==================================================
#             # 6. Synchronize final plan metadata
#             # ==================================================

#             context.metadata["plan"].update({
#                 "status": plan.status.value,
#                 "task_count": len(plan.tasks),
#                 "completed_task_count": self._count_tasks_by_status(
#                     plan.tasks, "COMPLETED"
#                 ),
#                 "failed_task_count": self._count_tasks_by_status(
#                     plan.tasks, "FAILED"
#                 ),
#                 "skipped_task_count": self._count_tasks_by_status(
#                     plan.tasks, "SKIPPED"
#                 ),
#             })

#             # ==================================================
#             # 7. Final State Synchronization
#             # ==================================================

#             self._finalize_context(context)

#             # ==================================================
#             # 8. Save Memory (skip if clarification)
#             # ==================================================

#             if self._should_save_memory(context):
#                 await self._save_memory(context, tenant_id=tenant_id)

#             logger.info(
#                 "[AgentService] Processing completed | "
#                 "success=%s | errors=%d | clarification=%s",
#                 context.success,
#                 len(context.errors),
#                 bool(context.metadata.get("requires_clarification")),
#             )

#             return context

#         except Exception as exc:

#             logger.exception(
#                 "[AgentService] Fatal orchestration error."
#             )

#             context.add_error("AgentService", str(exc))

#             context.success = False

#             return context

#     # ==========================================================
#     # Public API (Backend Contract) — returns ToolResult
#     # ==========================================================

#     async def process_question_as_tool_result(
#         self,
#         question: str,
#         user_id: str,
#         session_id: str | None = None,
#         tenant_id: str = "default-tenant",
#     ) -> ToolResult:
#         """
#         نسخة من process_question ترجع ToolResult.
#         """

#         try:
#             context = await self.process_question(
#                 question=question,
#                 user_id=user_id,
#                 session_id=session_id,
#                 tenant_id=tenant_id,
#             )

#         except Exception as exc:

#             logger.exception(
#                 "[AgentService] process_question_as_tool_result failed."
#             )

#             return ToolResult(
#                 status="tool_error",
#                 tool_name="multi_agent_orchestrator",
#                 data={
#                     "answer": "",
#                     "chart": None,
#                     "trace": [],
#                 },
#                 sources=[],
#                 warnings=[str(exc)],
#                 error_code="AGENT_SERVICE_FATAL",
#                 trace_id=session_id,
#             )

#         return self._context_to_tool_result(context)

#     # ==========================================================
#     # Context → ToolResult
#     # ==========================================================

#     @staticmethod
#     def _context_to_tool_result(
#         context: BIContext,
#     ) -> ToolResult:

#         requires_clarification = bool(
#             context.metadata.get("requires_clarification")
#         )

#         has_answer = bool(
#             context.final_report
#             and context.final_report.strip()
#         )

#         if requires_clarification:
#             status = "insufficient_evidence"

#         elif not has_answer and not context.errors:
#             status = "no_results"

#         elif not context.success:
#             status = "tool_error"

#         else:
#             status = "success"

#         sources: list[dict] = []

#         for src in context.selected_sources or []:
#             sources.append({"name": src})

#         data = {
#             "answer": context.final_report or "",
#             "chart": context.chart_config or None,
#             "source_type": context.source_type,
#             "sql": context.sql_query,
#             "row_count": len(context.raw_data or []),
#             "trace": context.trace_steps,
#         }

#         warnings = list(context.errors or [])

#         return ToolResult(
#             status=status,
#             tool_name="multi_agent_orchestrator",
#             data=data,
#             sources=sources,
#             warnings=warnings,
#             error_code=None,
#             trace_id=context.session_id,
#         )

#     # ==========================================================
#     # Plan Creation
#     # ==========================================================

#     async def _create_plan(
#         self,
#         question: str,
#     ):
#         plan = await self.planner.create_plan(question)

#         if plan is None:
#             raise RuntimeError("Planner returned None.")

#         if plan.is_empty:
#             raise RuntimeError("Planner returned an empty plan.")

#         logger.info(
#             "[AgentService] Plan created | tasks=%d",
#             len(plan.tasks),
#         )

#         return plan

#     # ==========================================================
#     # Memory Loading
#     # ==========================================================

#     async def _load_memory_into_context(
#         self,
#         context: BIContext,
#         limit: int = 10,
#     ) -> None:

#         if self._memory is None:
#             return

#         try:

#             memories = []

#             if context.session_id:
#                 memories = await self._memory.get_by_session(
#                     session_id=context.session_id,
#                     limit=limit,
#                 )

#             if not memories and context.user_id:
#                 memories = await self._memory.get_by_user(
#                     user_id=context.user_id,
#                     limit=limit,
#                 )

#             if not memories:
#                 return

#             memory_lines = [
#                 f"[{memory.memory_type.value}] {memory.content}"
#                 for memory in memories
#             ]

#             memory_context = "\n".join(memory_lines).strip()

#             if not memory_context:
#                 return

#             context.memory_context = memory_context

#             context.metadata["memory_context"] = memory_context
#             context.metadata["memory_count"] = len(memories)

#             logger.info(
#                 "[AgentService] Loaded %d memories.",
#                 len(memories),
#             )

#         except Exception as exc:

#             logger.warning(
#                 "[AgentService] Memory loading failed: %s",
#                 exc,
#             )

#     # ==========================================================
#     # Source Information
#     # ==========================================================

#     @staticmethod
#     def _update_source_information(
#         context: BIContext,
#         plan,
#     ) -> None:

#         sources = {task.tool_name for task in plan.tasks}

#         detected_source = plan.metadata.get("detected_source")

#         has_database = (
#             "DatabaseTool" in sources
#             or detected_source == "both"
#         )

#         has_rag = (
#             "RAGTool" in sources
#             or detected_source in ("document", "both")
#         )

#         if has_database and has_rag:

#             context.source_type = "both"

#             context.add_source("database")
#             context.add_source("rag")

#         elif has_database:

#             context.source_type = "database"
#             context.add_source("database")

#         elif has_rag:

#             context.source_type = "document"
#             context.add_source("rag")

#         else:

#             context.source_type = "unknown"

#     # ==========================================================
#     # Task Counting Helper
#     # ==========================================================

#     @staticmethod
#     def _count_tasks_by_status(
#         tasks: list,
#         status_name: str,
#     ) -> int:

#         return sum(
#             1
#             for task in tasks
#             if str(
#                 getattr(task.status, "value", task.status)
#             ).upper() == status_name
#         )

#     # ==========================================================
#     # Finalization
#     # ==========================================================

#     @staticmethod
#     def _finalize_context(context: BIContext) -> None:

#         if context.metadata.get("requires_clarification"):

#             if context.final_report and context.final_report.strip():
#                 context.success = True
#                 return

#             context.add_error(
#                 "AgentService",
#                 "Clarification requested but no message generated.",
#             )
#             context.success = False
#             return

#         if context.errors:

#             context.success = False
#             return

#         if not context.final_report:

#             context.add_error(
#                 "AgentService",
#                 "No final report was generated.",
#             )

#             context.success = False
#             return

#         context.success = True

#     # ==========================================================
#     # Memory Save Decision
#     # ==========================================================

#     @staticmethod
#     def _should_save_memory(context: BIContext) -> bool:

#         if context.metadata.get("requires_clarification"):
#             return False

#         return (
#             context.success
#             and bool(context.question.strip())
#             and bool(
#                 context.final_report
#                 and context.final_report.strip()
#             )
#         )

#     # ==========================================================
#     # Memory Saving
#     # ==========================================================

#     async def _save_memory(self, context: BIContext, tenant_id: str) -> None:

#         if self._memory is None:
#             return

#         try:

#             conversation = (
#                 f"User: {context.question}\n\n"
#                 f"Assistant: {context.final_report}"
#             )

#             request = SaveMemoryRequest(
#                 user_id=context.user_id,
#                 session_id=context.session_id,
#                 content=conversation,
#                 memory_type=MemoryType.CONVERSATION,
#                 importance=MemoryImportance.MEDIUM,
#                 metadata={
#                     "source": "multi_agent",
#                     "source_type": context.source_type,
#                     "success": context.success,
#                     "tenant_id": tenant_id,
#                 },
#             )

#             await self._memory.save(request)

#             logger.info(
#                 "[AgentService] Conversation saved to memory."
#             )

#         except Exception as exc:

#             logger.warning(
#                 "[AgentService] Memory save failed: %s",
#                 exc,
#             )

#     # ==========================================================
#     # Question Normalization
#     # ==========================================================

#     @staticmethod
#     def _normalize_question(question: str | None) -> str:

#         if question is None:
#             return ""

#         return " ".join(str(question).strip().split())
        








from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from src.modules.llm.application.services import LLMService

from src.modules.memory.application.dtos import SaveMemoryRequest
from src.modules.memory.application.services import MemoryService
from src.modules.memory.domain.value_objects import (
    MemoryImportance,
    MemoryType,
)
# ✅ جديد: استيراد ذاكرة التجارب
from src.modules.memory.infrastructure.episodic_memory import EpisodicMemory

from src.modules.multi_agent.agents.analyzer_agent import AnalyzerAgent
from src.modules.multi_agent.agents.reporter_agent import ReporterAgent
from src.modules.multi_agent.agents.result_validator import ResultValidatorAgent
from src.modules.multi_agent.application.executor import TaskExecutor
from src.modules.multi_agent.application.planner import Planner
from src.modules.multi_agent.domain.bi_context import BIContext
from src.modules.multi_agent.domain.contracts import ToolResult
from src.modules.multi_agent.tools.database_tool import DatabaseTool
from src.modules.multi_agent.tools.rag_tool import RAGTool

from src.modules.query_engine.domain.interfaces import QueryEngine


logger = logging.getLogger(__name__)


class AgentService:
    r"""
    الخدمة الرئيسية الخاصة بـMulti-Agent BI Platform.

    تمثل طبقة orchestration العليا التي تدير رحلة السؤال كاملة:

        User Question
              ↓
            Memory
              ↓
            Planner
              ↓
             Plan
              ↓
         TaskExecutor
           /    |    \
          /     |     \
     Database  RAG   Analysis
          \     |     /
              ↓
         Result Validator (Self-Correction)
              ↓
           Reporter
              ↓
         Final Response
              ↓
            Memory
    """

    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(
        self,
        llm_service: LLMService,
        query_engine: QueryEngine,
        memory_service: MemoryService | None = None,
        rag_service=None,
        validator_agent: ResultValidatorAgent | None = None,
    ) -> None:
        if llm_service is None:
            raise ValueError("llm_service cannot be None.")
        if query_engine is None:
            raise ValueError("query_engine cannot be None.")

        self._llm = llm_service
        self._query_engine = query_engine
        self._memory = memory_service
        self._validator = validator_agent

        # ======================================================
        # Planner
        # ======================================================
        self.planner = Planner(llm_service=self._llm)

        # ======================================================
        # Tools Registry
        # ======================================================
        self.tool_registry = {
            "DatabaseTool": DatabaseTool(query_engine=self._query_engine),
            "RAGTool": RAGTool(),
        }

        # ======================================================
        # Specialist Agents
        # ======================================================
        self.analyzer = AnalyzerAgent(llm_service=self._llm)
        self.reporter = ReporterAgent(llm_service=self._llm)

        # ======================================================
        # Executor
        # ======================================================
        self.executor = TaskExecutor(
            tools_registry=self.tool_registry,
            analyzer_agent=self.analyzer,
            reporter_agent=self.reporter,
        )

        # ======================================================
        # ✅ جديد: ذاكرة التجارب (Episodic Memory)
        # ======================================================
        self.episodic_memory = EpisodicMemory()

        logger.info(
            "[AgentService] Initialized with Database, RAG, Validator, "
            "and Episodic Memory."
        )

    # ==========================================================
    # Public API (Primary) — returns BIContext
    # ==========================================================

    async def process_question(
        self,
        question: str,
        user_id: str,
        session_id: str | None = None,
        tenant_id: str = "default-tenant",
    ) -> BIContext:
        """
        معالجة سؤال المستخدم من البداية إلى النهاية.
        """
        question = self._normalize_question(question)

        if not question:
            context = BIContext(
                question="",
                user_id=user_id,
                session_id=(session_id or str(uuid.uuid4())),
            )
            context.add_error("AgentService", "Question cannot be empty.")
            return context

        context = BIContext(
            question=question,
            user_id=user_id,
            session_id=(session_id or str(uuid.uuid4())),
        )

        logger.info(
            "[AgentService] Processing question | session_id=%s | tenant_id=%s",
            context.session_id,
            tenant_id,
        )

        try:
            # ==================================================
            # 1. Load Memory (الذاكرة التقليدية - المحادثات)
            # ==================================================
            await self._load_memory_into_context(context)

            # ==================================================
            # 2. Create Execution Plan (مع دروس من الذاكرة)
            # ==================================================
            start_plan = time.time()
            plan = await self._create_plan(question=context.question)

            context.trace_steps.append({
                "step": "planning",
                "title": "التخطيط (Planner)",
                "duration_ms": int((time.time() - start_plan) * 1000),
                "details": f"تم إنشاء خطة بـ {len(plan.tasks)} مهام.",
            })

            # سجل معلومات الخطة
            context.metadata["plan"] = {
                "status": plan.status.value,
                "task_count": len(plan.tasks),
                "generated_by": plan.metadata.get("generated_by"),
                "planner_model": plan.metadata.get("planner_model"),
                "detected_source": plan.metadata.get("detected_source"),
                "requires_clarification": bool(
                    plan.metadata.get("requires_clarification")
                ),
            }

            # حدد المصادر
            self._update_source_information(context=context, plan=plan)

            # ==================================================
            # 3. Execute Plan
            # ==================================================
            start_exec = time.time()
            context = await self.executor.execute_plan(plan=plan, context=context)

            context.trace_steps.append({
                "step": "execution",
                "title": "التنفيذ (Executor)",
                "duration_ms": int((time.time() - start_exec) * 1000),
                "details": f"تم تنفيذ المهام. حالة الخطة: {plan.status.value}",
            })

            # ==================================================
            # 4. Self-Correction (Validator)
            # ==================================================
            if self._validator and context.final_report and context.final_report.strip():
                start_val = time.time()
                context = await self._validator.execute(context)

                val_passed = context.metadata.get("validation_passed", False)
                val_report = context.metadata.get("validation_report", {})

                details = "نجح التحقق من البيانات."
                if not val_passed:
                    details = f"فشل التحقق: {val_report.get('reason', 'سبب غير معروف')}"

                context.trace_steps.append({
                    "step": "validation",
                    "title": "التحقق (Validator)",
                    "duration_ms": int((time.time() - start_val) * 1000),
                    "details": details,
                })

            # ==================================================
            # 5. Synchronize final plan metadata
            # ==================================================
            context.metadata["plan"].update({
                "status": plan.status.value,
                "task_count": len(plan.tasks),
                "completed_task_count": self._count_tasks_by_status(plan.tasks, "COMPLETED"),
                "failed_task_count": self._count_tasks_by_status(plan.tasks, "FAILED"),
                "skipped_task_count": self._count_tasks_by_status(plan.tasks, "SKIPPED"),
            })

            # ==================================================
            # 6. Final State Synchronization
            # ==================================================
            self._finalize_context(context)

            # ==================================================
            # 7. ✅ جديد: حفظ الدرس في Episodic Memory
            # ==================================================
            await self._save_lesson(context, plan)

            # ==================================================
            # 8. Save Memory (المحادثة التقليدية)
            # ==================================================
            if self._should_save_memory(context):
                await self._save_memory(context, tenant_id=tenant_id)

            logger.info(
                "[AgentService] Processing completed | "
                "success=%s | errors=%d | clarification=%s",
                context.success,
                len(context.errors),
                bool(context.metadata.get("requires_clarification")),
            )

            return context

        except Exception as exc:
            logger.exception("[AgentService] Fatal orchestration error.")
            context.add_error("AgentService", str(exc))
            context.success = False
            return context

    # ==========================================================
    # Public API (Backend Contract) — returns ToolResult
    # ==========================================================

    async def process_question_as_tool_result(
        self,
        question: str,
        user_id: str,
        session_id: str | None = None,
        tenant_id: str = "default-tenant",
    ) -> ToolResult:
        """نسخة من process_question ترجع ToolResult."""
        try:
            context = await self.process_question(
                question=question,
                user_id=user_id,
                session_id=session_id,
                tenant_id=tenant_id,
            )
        except Exception as exc:
            logger.exception("[AgentService] process_question_as_tool_result failed.")
            return ToolResult(
                status="tool_error",
                tool_name="multi_agent_orchestrator",
                data={"answer": "", "chart": None, "trace": []},
                sources=[],
                warnings=[str(exc)],
                error_code="AGENT_SERVICE_FATAL",
                trace_id=session_id,
            )

        return self._context_to_tool_result(context)

    # ==========================================================
    # Context → ToolResult
    # ==========================================================

    @staticmethod
    def _context_to_tool_result(context: BIContext) -> ToolResult:
        requires_clarification = bool(context.metadata.get("requires_clarification"))
        has_answer = bool(context.final_report and context.final_report.strip())

        if requires_clarification:
            status = "insufficient_evidence"
        elif not has_answer and not context.errors:
            status = "no_results"
        elif not context.success:
            status = "tool_error"
        else:
            status = "success"

        sources = [{"name": src} for src in (context.selected_sources or [])]

        data = {
            "answer": context.final_report or "",
            "chart": context.chart_config or None,
            "source_type": context.source_type,
            "sql": context.sql_query,
            "row_count": len(context.raw_data or []),
            "trace": context.trace_steps,
        }

        warnings = list(context.errors or [])

        return ToolResult(
            status=status,
            tool_name="multi_agent_orchestrator",
            data=data,
            sources=sources,
            warnings=warnings,
            error_code=None,
            trace_id=context.session_id,
        )

    # ==========================================================
    # Plan Creation (with Episodic Memory)
    # ==========================================================

    async def _create_plan(self, question: str):
        # ✅ جديد: استرجاع الدروس من الذاكرة قبل التخطيط
        episodic_warnings = await self.episodic_memory.get_warnings_for_planner(question)

        if episodic_warnings:
            logger.info("[AgentService] Found episodic lessons for question.")
        else:
            logger.info("[AgentService] No episodic lessons for this question.")

        plan = await self.planner.create_plan(
            question=question,
            episodic_warnings=episodic_warnings,
        )

        if plan is None:
            raise RuntimeError("Planner returned None.")
        if plan.is_empty:
            raise RuntimeError("Planner returned an empty plan.")

        # سجل إن الدروس استُخدمت
        if episodic_warnings:
            plan.metadata["episodic_warnings_used"] = True

        logger.info("[AgentService] Plan created | tasks=%d", len(plan.tasks))
        return plan

    # ==========================================================
    # ✅ جديد: Save Lesson to Episodic Memory
    # ==========================================================

    async def _save_lesson(self, context: BIContext, plan) -> None:
        """
        حفظ درس في ذاكرة التجارب بناءً على نتيجة التنفيذ.
        """
        try:
            strategy = plan.metadata.get("generated_by", "unknown")

            if context.success:
                await self.episodic_memory.save_lesson(
                    question=context.question,
                    strategy=strategy,
                    outcome="success",
                )
                logger.info("[AgentService] Success lesson saved: %s", strategy)
            else:
                reason = "; ".join(context.errors[:2]) if context.errors else "Unknown failure"

                await self.episodic_memory.save_lesson(
                    question=context.question,
                    strategy=strategy,
                    outcome="failure",
                    reason=reason[:200],
                    correction_hint=self._generate_correction_hint(context, strategy),
                )
                logger.info("[AgentService] Failure lesson saved: %s", strategy)

        except Exception as exc:
            logger.warning("[AgentService] Failed to save lesson: %s", exc)

    # ==========================================================
    # ✅ جديد: Generate Correction Hint
    # ==========================================================

    @staticmethod
    def _generate_correction_hint(context: BIContext, strategy: str) -> str:
        """
        توليد نصيحة تصحيح بناءً على نوع الفشل.
        """
        if not context.errors:
            return "جرب مصدر بيانات آخر أو أعد صياغة السؤال."

        error_text = " ".join(context.errors).lower()

        if "rag" in error_text or "document" in error_text:
            return "RAGTool فشل. جرب DatabaseTool أو تحقق من اتصال RAG API."
        if "sql" in error_text or "database" in error_text:
            return "DatabaseTool فشل. جرب RAGTool أو تحقق من الـ Schema."
        if "timeout" in error_text:
            return "حدث timeout. حاول تقليل حجم البيانات أو زيادة الـ timeout."
        if "validation" in error_text:
            return "فشل التحقق. جرب استراتيجية أكثر تحفظاً أو مصادر بيانات إضافية."

        return "جرب مصدر بيانات آخر أو أعد صياغة السؤال."

    # ==========================================================
    # Memory Loading (Conversation Memory)
    # ==========================================================

    async def _load_memory_into_context(self, context: BIContext, limit: int = 10) -> None:
        if self._memory is None:
            return

        try:
            memories = []
            if context.session_id:
                memories = await self._memory.get_by_session(
                    session_id=context.session_id, limit=limit
                )
            if not memories and context.user_id:
                memories = await self._memory.get_by_user(
                    user_id=context.user_id, limit=limit
                )
            if not memories:
                return

            memory_lines = [
                f"[{memory.memory_type.value}] {memory.content}"
                for memory in memories
            ]
            memory_context = "\n".join(memory_lines).strip()

            if not memory_context:
                return

            context.memory_context = memory_context
            context.metadata["memory_context"] = memory_context
            context.metadata["memory_count"] = len(memories)

            logger.info("[AgentService] Loaded %d memories.", len(memories))

        except Exception as exc:
            logger.warning("[AgentService] Memory loading failed: %s", exc)

    # ==========================================================
    # Source Information
    # ==========================================================

    @staticmethod
    def _update_source_information(context: BIContext, plan) -> None:
        sources = {task.tool_name for task in plan.tasks}
        detected_source = plan.metadata.get("detected_source")

        has_database = "DatabaseTool" in sources or detected_source == "both"
        has_rag = "RAGTool" in sources or detected_source in ("document", "both")

        if has_database and has_rag:
            context.source_type = "both"
            context.add_source("database")
            context.add_source("rag")
        elif has_database:
            context.source_type = "database"
            context.add_source("database")
        elif has_rag:
            context.source_type = "document"
            context.add_source("rag")
        else:
            context.source_type = "unknown"

    # ==========================================================
    # Task Counting Helper
    # ==========================================================

    @staticmethod
    def _count_tasks_by_status(tasks: list, status_name: str) -> int:
        return sum(
            1
            for task in tasks
            if str(getattr(task.status, "value", task.status)).upper() == status_name
        )

    # ==========================================================
    # Finalization
    # ==========================================================

    @staticmethod
    def _finalize_context(context: BIContext) -> None:
        if context.metadata.get("requires_clarification"):
            if context.final_report and context.final_report.strip():
                context.success = True
                return
            context.add_error("AgentService", "Clarification requested but no message generated.")
            context.success = False
            return

        if context.errors:
            context.success = False
            return

        if not context.final_report:
            context.add_error("AgentService", "No final report was generated.")
            context.success = False
            return

        context.success = True

    # ==========================================================
    # Memory Save Decision (Conversation Memory)
    # ==========================================================

    @staticmethod
    def _should_save_memory(context: BIContext) -> bool:
        if context.metadata.get("requires_clarification"):
            return False
        return (
            context.success
            and bool(context.question.strip())
            and bool(context.final_report and context.final_report.strip())
        )

    # ==========================================================
    # Memory Saving (Conversation Memory)
    # ==========================================================

    async def _save_memory(self, context: BIContext, tenant_id: str) -> None:
        if self._memory is None:
            return

        try:
            conversation = (
                f"User: {context.question}\n\n"
                f"Assistant: {context.final_report}"
            )

            request = SaveMemoryRequest(
                user_id=context.user_id,
                session_id=context.session_id,
                content=conversation,
                memory_type=MemoryType.CONVERSATION,
                importance=MemoryImportance.MEDIUM,
                metadata={
                    "source": "multi_agent",
                    "source_type": context.source_type,
                    "success": context.success,
                    "tenant_id": tenant_id,
                },
            )

            await self._memory.save(request)
            logger.info("[AgentService] Conversation saved to memory.")

        except Exception as exc:
            logger.warning("[AgentService] Memory save failed: %s", exc)

    # ==========================================================
    # Question Normalization
    # ==========================================================

    @staticmethod
    def _normalize_question(question: str | None) -> str:
        if question is None:
            return ""
        return " ".join(str(question).strip().split())