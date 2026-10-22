from __future__ import annotations

import logging
from typing import Any, Protocol

from src.modules.multi_agent.domain.bi_context import BIContext
from src.modules.multi_agent.domain.plan import (
    Plan,
    PlanStatus,
)
from src.modules.multi_agent.domain.task import (
    Task,
    TaskStatus,
)


logger = logging.getLogger(__name__)


class Executable(Protocol):
    """
    Contract بسيط لأي Tool أو Agent يتم تشغيله بواسطة Executor.
    """

    async def execute(
        self,
        inputs: dict[str, Any],
        context: BIContext,
    ) -> Any:
        ...


class TaskExecutor:
    """
    المحرك المركزي لتنفيذ Execution Plan.

    المسؤوليات:
        - تنفيذ المهام بالترتيب الصحيح.
        - احترام dependencies.
        - إدارة lifecycle الخاص بالـTask.
        - إعادة المحاولة عند الفشل.
        - تشغيل الأدوات المسجلة.
        - تشغيل Analyzer / Reporter.
        - تخزين نتائج المهام داخل BIContext.
        - منع تنفيذ المهام المحجوبة.
        - تحديث حالة Plan.
        - التعامل مع partial execution.

    TaskExecutor لا يقرر:
        - Database أم Document أم Both.
        - كيف يتم توليد SQL.
        - كيف يعمل RAG.
        - كيف يتم التحليل.

    هذه مسؤولية Planner / Tools / Agents.
    """

    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(
        self,
        tools_registry: dict[str, Any],
        analyzer_agent: Any | None = None,
        reporter_agent: Any | None = None,
    ):
        if tools_registry is None:
            raise ValueError(
                "tools_registry cannot be None."
            )

        self._tools = tools_registry
        self._analyzer = analyzer_agent
        self._reporter = reporter_agent

    # ==========================================================
    # Public API
    # ==========================================================

    async def execute_plan(
        self,
        plan: Plan,
        context: BIContext,
    ) -> BIContext:
        """
        تنفيذ الخطة بالكامل.

        كل دورة:
            1. تحديث حالة الخطة.
            2. البحث عن المهام الجاهزة.
            3. تنفيذ المهمة.
            4. حفظ النتيجة.
            5. التعامل مع الفشل والتبعيات.
        """

        logger.info(
            "[Executor] Starting plan execution | "
            "plan_id=%s | tasks=%d",
            plan.plan_id or "N/A",
            len(plan.tasks),
        )

        # ------------------------------------------------------
        # Validate input
        # ------------------------------------------------------

        if plan.is_empty:
            return self._fail_plan(
                plan=plan,
                context=context,
                error="Cannot execute an empty plan.",
            )

        # ------------------------------------------------------
        # Start plan
        # ------------------------------------------------------

        try:
            plan.start()

        except Exception as exc:
            return self._fail_plan(
                plan=plan,
                context=context,
                error=f"Failed to start plan: {exc}",
            )

        # ------------------------------------------------------
        # Execution Loop
        # ------------------------------------------------------

        while True:

            plan.update_status()

            # ==================================================
            # Completed
            # ==================================================

            if plan.is_completed:

                self._complete_plan(
                    plan=plan,
                    context=context,
                )

                break

            # ==================================================
            # Cancelled
            # ==================================================

            if plan.status == PlanStatus.CANCELLED:

                context.success = False

                logger.warning(
                    "[Executor] Plan cancelled."
                )

                break

            # ==================================================
            # Ready Tasks
            # ==================================================

            ready_tasks = self._get_ready_tasks(
                plan
            )

            # ==================================================
            # No Ready Tasks
            # ==================================================

            if not ready_tasks:

                if self._has_unresolved_tasks(plan):

                    self._handle_unresolved_plan(
                        plan=plan,
                        context=context,
                    )

                break

            # ==================================================
            # Execute Tasks
            # ==================================================

            # تنفيذ أول مهمة جاهزة.
            #
            # لاحقًا يمكننا إضافة Parallel Execution
            # للمهام المستقلة بدون تغيير الـDomain.
            task = ready_tasks[0]

            plan.set_current_task(
                task.id
            )

            await self._execute_task(
                task=task,
                context=context,
            )

            # --------------------------------------------------
            # Handle failed task
            # --------------------------------------------------

            if task.status == TaskStatus.FAILED:

                self._skip_blocked_tasks(
                    plan=plan,
                )

        # ------------------------------------------------------
        # Final synchronization
        # ------------------------------------------------------

        plan.update_status()

        self._synchronize_final_state(
            plan=plan,
            context=context,
        )

        logger.info(
            "[Executor] Plan finished | "
            "status=%s | completed=%d | failed=%d",
            plan.status.value,
            plan.completed_tasks,
            plan.failed_tasks,
        )

        return context

    # ==========================================================
    # Task Execution
    # ==========================================================

    async def _execute_task(
        self,
        task: Task,
        context: BIContext,
    ) -> None:
        """
        تنفيذ مهمة واحدة مع Retry.
        """

        logger.info(
            "[Executor] Starting task | "
            "id=%s | tool=%s",
            task.id,
            task.tool_name,
        )

        # ------------------------------------------------------
        # Start
        # ------------------------------------------------------

        try:
            task.start()

        except Exception as exc:

            self._mark_task_failure(
                task=task,
                context=context,
                error=str(exc),
            )

            return

        # ------------------------------------------------------
        # Retry loop
        # ------------------------------------------------------

        while True:

            try:

                result = await self._dispatch_task(
                    task=task,
                    context=context,
                )

                # ----------------------------------------------
                # Success
                # ----------------------------------------------

                task.mark_completed(
                    result
                )

                # نستخدم task.id وليس tool_name
                # حتى لا يتم overwrite للمهام المتكررة.
                context.set_tool_result(
                    task.id,
                    result,
                )

                logger.info(
                    "[Executor] Task completed | "
                    "id=%s | tool=%s",
                    task.id,
                    task.tool_name,
                )

                return

            except Exception as exc:

                logger.exception(
                    "[Executor] Task execution failed | "
                    "id=%s | attempt=%d",
                    task.id,
                    task.attempts,
                )

                # ----------------------------------------------
                # Retry
                # ----------------------------------------------

                if task.can_retry:

                    logger.warning(
                        "[Executor] Retrying task | "
                        "id=%s | attempt=%d/%d",
                        task.id,
                        task.attempts,
                        task.max_attempts,
                    )

                    task.status = TaskStatus.PENDING
                    task.result = None
                    task.error = str(exc)
                    task.completed_at = None

                    try:
                        task.start()

                    except Exception as retry_exc:

                        self._mark_task_failure(
                            task=task,
                            context=context,
                            error=str(retry_exc),
                        )

                        return

                    continue

                # ----------------------------------------------
                # Final Failure
                # ----------------------------------------------

                self._mark_task_failure(
                    task=task,
                    context=context,
                    error=str(exc),
                )

                return

    # ==========================================================
    # Task Dispatcher
    # ==========================================================

    async def _dispatch_task(
        self,
        task: Task,
        context: BIContext,
    ) -> Any:
        """
        توجيه المهمة إلى المنفذ المناسب.
        """

        tool_name = task.tool_name

        # ------------------------------------------------------
        # Registered Tool
        # ------------------------------------------------------

        tool = self._tools.get(
            tool_name
        )

        if tool is not None:

            execute = getattr(
                tool,
                "execute",
                None,
            )

            if not callable(execute):
                raise TypeError(
                    f"Tool '{tool_name}' does not "
                    "provide a callable execute()."
                )

            return await execute(
                task.inputs,
                context,
            )

        # ------------------------------------------------------
        # Analysis Agent
        # ------------------------------------------------------

        if tool_name == "AnalysisTool":

            if self._analyzer is None:
                raise RuntimeError(
                    "AnalyzerAgent is not configured."
                )

            return await self._analyzer.execute(
                context
            )

        # ------------------------------------------------------
        # Report Agent
        # ------------------------------------------------------

        if tool_name == "ReportTool":

            if self._reporter is None:
                raise RuntimeError(
                    "ReporterAgent is not configured."
                )

            return await self._reporter.execute(
                context
            )

        # ------------------------------------------------------
        # Unknown Tool
        # ------------------------------------------------------

        raise LookupError(
            f"Tool '{tool_name}' is not registered."
        )

    # ==========================================================
    # Ready Tasks
    # ==========================================================

    @staticmethod
    def _get_ready_tasks(
        plan: Plan,
    ) -> list[Task]:
        """
        الحصول على المهام الجاهزة للتنفيذ.
        """

        return [
            task
            for task in plan.ready_tasks
            if task.status == TaskStatus.PENDING
        ]

    # ==========================================================
    # Dependency Handling
    # ==========================================================

    @staticmethod
    def _skip_blocked_tasks(
        plan: Plan,
    ) -> None:
        """
        تخطي جميع المهام التي تعتمد على:
            FAILED
            أو SKIPPED

        بشكل مباشر أو غير مباشر.
        """

        changed = True

        while changed:

            changed = False

            for task in plan.tasks:

                if task.status != TaskStatus.PENDING:
                    continue

                for dependency_id in task.depends_on:

                    dependency = plan.get_task(
                        dependency_id
                    )

                    if dependency is None:
                        continue

                    if dependency.status in (
                        TaskStatus.FAILED,
                        TaskStatus.SKIPPED,
                    ):

                        reason = (
                            f"Task '{task.id}' was skipped "
                            f"because dependency "
                            f"'{dependency.id}' "
                            "did not complete successfully."
                        )

                        task.mark_skipped(
                            reason
                        )

                        logger.warning(
                            "[Executor] %s",
                            reason,
                        )

                        changed = True

                        break

    # ==========================================================
    # Unresolved Plan
    # ==========================================================

    @staticmethod
    def _has_unresolved_tasks(
        plan: Plan,
    ) -> bool:
        """
        هل ما زالت هناك مهام غير محسومة؟
        """

        return any(
            task.status
            in (
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
            )
            for task in plan.tasks
        )

    # ==========================================================
    # Handle Unresolved
    # ==========================================================

    def _handle_unresolved_plan(
        self,
        plan: Plan,
        context: BIContext,
    ) -> None:
        """
        معالجة Deadlock أو Dependencies غير قابلة للتحقيق.
        """

        unresolved = [
            task
            for task in plan.tasks
            if task.status
            in (
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
            )
        ]

        for task in unresolved:

            reason = (
                f"Task '{task.id}' could not be executed "
                "because its dependencies were not satisfied."
            )

            task.mark_skipped(
                reason
            )

            context.add_error(
                "Executor",
                reason,
            )

        plan.mark_partial()

    # ==========================================================
    # Failure Handling
    # ==========================================================

    @staticmethod
    def _mark_task_failure(
        task: Task,
        context: BIContext,
        error: str,
    ) -> None:
        """
        تسجيل فشل المهمة في Task وBIContext.
        """

        task.mark_failed(
            error
        )

        context.add_error(
            "Executor",
            f"Task '{task.id}' failed: {error}",
        )

    # ==========================================================
    # Plan Failure
    # ==========================================================

    @staticmethod
    def _fail_plan(
        plan: Plan,
        context: BIContext,
        error: str,
    ) -> BIContext:
        """
        إنهاء الخطة بفشل مباشر.
        """

        logger.error(
            "[Executor] %s",
            error,
        )

        context.add_error(
            "Executor",
            error,
        )

        plan.mark_failed(
            error
        )

        return context

    # ==========================================================
    # Plan Completion
    # ==========================================================

    @staticmethod
    def _complete_plan(
        plan: Plan,
        context: BIContext,
    ) -> None:
        """
        إنهاء الخطة بنجاح.
        """

        try:
            plan.mark_completed()

        except RuntimeError:
            # Defensive guard.
            plan.update_status()

        if plan.status == PlanStatus.COMPLETED:

            context.mark_success()

            logger.info(
                "[Executor] Plan completed successfully."
            )

    # ==========================================================
    # Final State Synchronization
    # ==========================================================

    @staticmethod
    def _synchronize_final_state(
        plan: Plan,
        context: BIContext,
    ) -> None:
        """
        مزامنة الحالة النهائية بين Plan وBIContext.
        """

        if plan.status == PlanStatus.COMPLETED:

            context.mark_success()
            return

        if plan.status in (
            PlanStatus.FAILED,
            PlanStatus.CANCELLED,
            PlanStatus.PARTIAL,
        ):

            context.success = False

    # ==========================================================
    # Registry API
    # ==========================================================

    def has_tool(
        self,
        tool_name: str,
    ) -> bool:
        """
        التحقق من وجود أداة.
        """

        return tool_name in self._tools

    def get_tool(
        self,
        tool_name: str,
    ) -> Any | None:
        """
        إرجاع أداة بالاسم.
        """

        return self._tools.get(
            tool_name
        )

    def register_tool(
        self,
        tool_name: str,
        tool: Any,
    ) -> None:
        """
        تسجيل Tool جديد.
        """

        if not isinstance(
            tool_name,
            str,
        ) or not tool_name.strip():

            raise ValueError(
                "tool_name must be a non-empty string."
            )

        if tool is None:
            raise ValueError(
                "tool cannot be None."
            )

        execute = getattr(
            tool,
            "execute",
            None,
        )

        if not callable(execute):
            raise TypeError(
                f"Tool '{tool_name}' must provide "
                "a callable execute()."
            )

        self._tools[tool_name] = tool

        logger.info(
            "[Executor] Registered tool '%s'.",
            tool_name,
        )

    def unregister_tool(
        self,
        tool_name: str,
    ) -> Any | None:
        """
        إزالة Tool.
        """

        tool = self._tools.pop(
            tool_name,
            None,
        )

        if tool is not None:

            logger.info(
                "[Executor] Unregistered tool '%s'.",
                tool_name,
            )

        return tool