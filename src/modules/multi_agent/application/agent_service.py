from __future__ import annotations

import logging
import uuid

from src.modules.llm.application.services import LLMService

from src.modules.memory.application.dtos import SaveMemoryRequest
from src.modules.memory.application.services import MemoryService
from src.modules.memory.domain.value_objects import (
    MemoryImportance,
    MemoryType,
)

from src.modules.multi_agent.agents.analyzer_agent import AnalyzerAgent
from src.modules.multi_agent.agents.reporter_agent import ReporterAgent
from src.modules.multi_agent.application.executor import TaskExecutor
from src.modules.multi_agent.application.planner import Planner
from src.modules.multi_agent.domain.bi_context import BIContext
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
           Reporter
              ↓
         Final Response
              ↓
            Memory

    AgentService مسؤول عن:
        - إنشاء BIContext.
        - تحميل Memory المناسبة.
        - استدعاء Planner.
        - تنفيذ الخطة.
        - تمرير السياق بين المكونات.
        - حفظ النتيجة في Memory.
        - إدارة أخطاء orchestration.

    AgentService لا:
        - ينفذ SQL مباشرة.
        - ينفذ RAG مباشرة.
        - يحلل البيانات بنفسه.
        - يتعامل مع Repository الخاص بالـMemory مباشرة.
        - ينفذ منطق المصادقة أو Multi-Tenant.
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
    ) -> None:
        """
        إنشاء AgentService.

        Parameters
        ----------
        llm_service:
            خدمة LLM المشتركة.

        query_engine:
            Query Engine المسؤولة عن تنفيذ استعلامات
            قاعدة البيانات.

        memory_service:
            MemoryService المسؤول عن قراءة وحفظ الذاكرة.

        rag_service:
            تم دمجه مباشرة داخل RAGTool ولا داعي لاستخدامه هنا بعد الآن.
        """

        # ------------------------------------------------------
        # Validate LLM
        # ------------------------------------------------------

        if llm_service is None:
            raise ValueError(
                "llm_service cannot be None."
            )

        # ------------------------------------------------------
        # Validate Query Engine
        # ------------------------------------------------------

        if query_engine is None:
            raise ValueError(
                "query_engine cannot be None."
            )

        self._llm = llm_service
        self._query_engine = query_engine
        self._memory = memory_service

        # ======================================================
        # Planner
        # ======================================================

        self.planner = Planner(
            llm_service=self._llm,
        )

        # ======================================================
        # Tools Registry
        # ======================================================

        # تسجيل أدوات قاعدة البيانات والبحث في المستندات (RAG)
        self.tool_registry = {
            "DatabaseTool": DatabaseTool(
                query_engine=self._query_engine,
            ),
            # التعديل الرئيسي لحل الخطأ: 
            # استدعاء RAGTool بدون أي وسائط لأنه يتصل مباشرة بنظام المستندات.
            "RAGTool": RAGTool(),
        }

        # ======================================================
        # Specialist Agents
        # ======================================================

        self.analyzer = AnalyzerAgent(
            llm_service=self._llm,
        )

        self.reporter = ReporterAgent(
            llm_service=self._llm,
        )

        # ======================================================
        # Executor
        # ======================================================

        self.executor = TaskExecutor(
            tools_registry=self.tool_registry,
            analyzer_agent=self.analyzer,
            reporter_agent=self.reporter,
        )

        logger.info(
            "[AgentService] Initialized successfully with Database and RAG tools."
        )

    # ==========================================================
    # Main Entry Point
    # ==========================================================

    async def process_question(
        self,
        question: str,
        user_id: str,
        session_id: str | None = None,
    ) -> BIContext:
        """
        معالجة سؤال المستخدم من البداية إلى النهاية.

        Flow:

            1. Validate Request
            2. Create Context
            3. Load Memory
            4. Create Plan
            5. Execute Plan
            6. Synchronize Final State
            7. Save Conversation Memory
            8. Return BIContext
        """

        # ------------------------------------------------------
        # 1. Validate input
        # ------------------------------------------------------

        question = self._normalize_question(
            question
        )

        if not question:

            context = BIContext(
                question="",
                user_id=user_id,
                session_id=(
                    session_id
                    or str(uuid.uuid4())
                ),
            )

            context.add_error(
                "AgentService",
                "Question cannot be empty.",
            )

            return context

        # ------------------------------------------------------
        # 2. Create Context
        # ------------------------------------------------------

        context = BIContext(
            question=question,
            user_id=user_id,
            session_id=(
                session_id
                or str(uuid.uuid4())
            ),
        )

        logger.info(
            "[AgentService] Processing question | "
            "session_id=%s",
            context.session_id,
        )

        try:

            # ==================================================
            # 3. Load Memory
            # ==================================================

            await self._load_memory_into_context(
                context
            )

            # ==================================================
            # 4. Create Execution Plan
            # ==================================================

            plan = await self._create_plan(
                question=context.question,
            )

            # --------------------------------------------------
            # Save plan information for observability
            # --------------------------------------------------

            context.metadata["plan"] = {
                "status": (
                    "BLOCKED"
                    if plan.metadata.get("blocked")
                    else plan.status.value
                ),
                "task_count": len(plan.tasks),
                "generated_by": plan.metadata.get(
                    "generated_by"
                ),
                "planner_model": plan.metadata.get(
                    "planner_model"
                ),
                "detected_source": plan.metadata.get(
                    "detected_source"
                ),
            }

            # --------------------------------------------------
            # Infer selected sources from the Plan
            # --------------------------------------------------

            self._update_source_information(
                context=context,
                plan=plan,
            )

            # --------------------------------------------------
            # A blocked plan means the question requires a source
            # that is not available yet (currently document RAG).
            # Do not send an empty plan to the executor, and never
            # pretend a database-only query answered it.
            # --------------------------------------------------

            if plan.metadata.get("blocked"):
                blocked_reason = str(
                    plan.metadata.get(
                        "blocked_reason",
                        "The required data source is not available yet.",
                    )
                )

                context.add_error(
                    "AgentService",
                    blocked_reason,
                )
                context.final_report = (
                    "This question cannot be answered reliably yet "
                    "because the required document retrieval service "
                    "is not available. Please try again after RAG "
                    "has been integrated."
                )
                context.metadata["plan"]["status"] = "BLOCKED"
                context.metadata["plan"]["blocked_reason"] = blocked_reason

                self._finalize_context(context)

                logger.info(
                    "[AgentService] Request blocked because required source is unavailable."
                )
                return context

            # ==================================================
            # 5. Execute Plan
            # ==================================================

            context = await self.executor.execute_plan(
                plan=plan,
                context=context,
            )

            # ==================================================
            # 6. Synchronize final plan metadata
            # ==================================================

            context.metadata["plan"].update({
                "status": plan.status.value,
                "task_count": len(plan.tasks),
                "completed_task_count": sum(
                    1 for task in plan.tasks
                    if str(getattr(task.status, "value", task.status)).upper() == "COMPLETED"
                ),
                "failed_task_count": sum(
                    1 for task in plan.tasks
                    if str(getattr(task.status, "value", task.status)).upper() == "FAILED"
                ),
                "skipped_task_count": sum(
                    1 for task in plan.tasks
                    if str(getattr(task.status, "value", task.status)).upper() == "SKIPPED"
                ),
            })

            # ==================================================
            # 7. Final State Synchronization
            # ==================================================

            self._finalize_context(
                context
            )

            # ==================================================
            # 7. Save Memory
            # ==================================================

            if self._should_save_memory(
                context
            ):
                await self._save_memory(
                    context
                )

            logger.info(
                "[AgentService] Processing completed | "
                "success=%s | errors=%d",
                context.success,
                len(context.errors),
            )

            return context

        except Exception as exc:

            # ==================================================
            # Fatal Orchestration Error
            # ==================================================

            logger.exception(
                "[AgentService] Fatal orchestration error."
            )

            context.add_error(
                "AgentService",
                str(exc),
            )

            context.success = False

            return context

    # ==========================================================
    # Plan Creation
    # ==========================================================

    async def _create_plan(
        self,
        question: str,
    ):
        """
        إنشاء Execution Plan باستخدام Planner.
        """

        plan = await self.planner.create_plan(
            question
        )

        if plan is None:
            raise RuntimeError(
                "Planner returned None."
            )

        if plan.is_empty:
            raise RuntimeError(
                "Planner returned an empty plan."
            )

        logger.info(
            "[AgentService] Plan created | "
            "tasks=%d",
            len(plan.tasks),
        )

        return plan

    # ==========================================================
    # Memory Loading
    # ==========================================================

    async def _load_memory_into_context(
        self,
        context: BIContext,
        limit: int = 10,
    ) -> None:
        """
        استرجاع الذاكرة المناسبة ووضعها داخل BIContext.

        الأولوية:

            Session Memory
                ↓
            User Memory

        إذا حدث خطأ في Memory:
            لا نوقف الـAgent.
        """

        if self._memory is None:
            return

        try:

            memories = []

            # --------------------------------------------------
            # Session Memory
            # --------------------------------------------------

            if context.session_id:

                memories = (
                    await self._memory.get_session_memories(
                        session_id=context.session_id,
                        limit=limit,
                    )
                )

            # --------------------------------------------------
            # User Memory fallback
            # --------------------------------------------------

            if (
                not memories
                and context.user_id
            ):

                memories = (
                    await self._memory.get_user_memories(
                        user_id=context.user_id,
                        limit=limit,
                    )
                )

            if not memories:
                return

            # --------------------------------------------------
            # Convert Memory to Context
            # --------------------------------------------------

            memory_lines = []

            for memory in memories:

                memory_lines.append(
                    f"[{memory.memory_type.value}] "
                    f"{memory.content}"
                )

            memory_context = "\n".join(
                memory_lines
            ).strip()

            if not memory_context:
                return

            context.memory_context = (
                memory_context
            )

            # Keep backward-compatible metadata.
            context.metadata[
                "memory_context"
            ] = memory_context

            context.metadata[
                "memory_count"
            ] = len(memories)

            logger.info(
                "[AgentService] Loaded %d memories.",
                len(memories),
            )

        except Exception as exc:

            # Memory is auxiliary.
            # Its failure must never stop the request.

            logger.warning(
                "[AgentService] Memory loading failed: %s",
                exc,
            )

    # ==========================================================
    # Source Information
    # ==========================================================

    @staticmethod
    def _update_source_information(
        context: BIContext,
        plan,
    ) -> None:
        """
        تحديد مصادر البيانات المتوقعة من الخطة.

        DatabaseTool -> database
        RAGTool      -> document

        هذا لا ينفذ أي شيء.
        هو فقط يسجل قرار الـPlanner داخل السياق.
        """

        sources = {
            task.tool_name
            for task in plan.tasks
        }

        detected_source = plan.metadata.get("detected_source")
        has_database = (
            "DatabaseTool" in sources
            or detected_source == "both"
        )

        has_rag = (
            "RAGTool" in sources
            or detected_source in ("document", "both")
        )

        # ------------------------------------------------------
        # Both
        # ------------------------------------------------------

        if has_database and has_rag:

            context.source_type = "both"

            context.add_source(
                "database"
            )

            context.add_source(
                "rag"
            )

        # ------------------------------------------------------
        # Database
        # ------------------------------------------------------

        elif has_database:

            context.source_type = "database"

            context.add_source(
                "database"
            )

        # ------------------------------------------------------
        # Document
        # ------------------------------------------------------

        elif has_rag:

            context.source_type = "document"

            context.add_source(
                "rag"
            )

        # ------------------------------------------------------
        # Unknown
        # ------------------------------------------------------

        else:

            context.source_type = "unknown"

    # ==========================================================
    # Finalization
    # ==========================================================

    @staticmethod
    def _finalize_context(
        context: BIContext,
    ) -> None:
        """
        المزامنة النهائية لحالة BIContext.

        النجاح الحقيقي يعني:
            - لا توجد أخطاء.
            - يوجد تقرير نهائي عندما تكون الخطة مكتملة.
        """

        # ------------------------------------------------------
        # Existing errors always win
        # ------------------------------------------------------

        if context.errors:

            context.success = False

            return

        # ------------------------------------------------------
        # Report validation
        # ------------------------------------------------------

        if not context.final_report:

            context.add_error(
                "AgentService",
                "No final report was generated.",
            )

            context.success = False

            return

        context.success = True

    # ==========================================================
    # Memory Save Decision
    # ==========================================================

    @staticmethod
    def _should_save_memory(
        context: BIContext,
    ) -> bool:
        """
        تحديد هل يجب حفظ المحادثة.
        """

        return (
            context.success
            and bool(
                context.question.strip()
            )
            and bool(
                context.final_report
                and context.final_report.strip()
            )
        )

    # ==========================================================
    # Memory Saving
    # ==========================================================

    async def _save_memory(
        self,
        context: BIContext,
    ) -> None:
        """
        حفظ دورة المحادثة كاملة داخل MemoryService.

        يتم حفظ:

            User Question
                +
            Assistant Final Report
        """

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
                },
            )

            await self._memory.save(
                request
            )

            logger.info(
                "[AgentService] Conversation saved to memory."
            )

        except Exception as exc:

            # Saving memory is secondary.
            # Do not destroy a successful BI response.

            logger.warning(
                "[AgentService] Memory save failed: %s",
                exc,
            )

    # ==========================================================
    # Question Normalization
    # ==========================================================

    @staticmethod
    def _normalize_question(
        question: str | None,
    ) -> str:
        """
        تنظيف سؤال المستخدم.
        """

        if question is None:
            return ""

        return " ".join(
            str(question).strip().split()
        )