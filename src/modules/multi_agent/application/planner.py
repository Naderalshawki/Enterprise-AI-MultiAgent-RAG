# from __future__ import annotations

# import json
# import logging
# import os
# from typing import Any

# from src.modules.llm.application.services import LLMService
# from src.modules.llm.domain.entities import LLMMessage, LLMRequest
# from src.modules.llm.domain.value_objects import ProviderName, Role

# from src.modules.multi_agent.domain.plan import Plan, PlanStatus
# from src.modules.multi_agent.domain.task import Task


# logger = logging.getLogger(__name__)


# class Planner:
#     """
#     Planner مسؤول عن تحويل سؤال المستخدم إلى Execution Plan.

#     المسؤوليات:
#         1. فهم طبيعة السؤال.
#         2. اختيار مصدر البيانات:
#            - database
#            - document
#            - both
#         3. اختيار الأدوات المناسبة.
#         4. بناء المهام.
#         5. تحديد Dependencies بين المهام.
#         6. التحقق من الخطة الناتجة.
#         7. منع الأدوات غير المسموح بها.
#         8. التعامل مع أخطاء الـLLM.
#         9. توفير fallback آمن ومنطقي.

#     Planner لا ينفذ أي Task.
#     التنفيذ مسؤولية TaskExecutor.
#     """

#     # ==========================================================
#     # Allowed Tools
#     # ==========================================================

#     ALLOWED_RETRIEVAL_TOOLS = {
#         "DatabaseTool",
#         "RAGTool",

        
#     }

#     ALLOWED_PROCESSING_TOOLS = {
#         "AnalysisTool",
#         "ReportTool",
#     }

#     ALLOWED_TOOLS = (
#         ALLOWED_RETRIEVAL_TOOLS
#         | ALLOWED_PROCESSING_TOOLS
#     )

#     # ==========================================================
#     # Planner Configuration
#     # ==========================================================

#     # التعديل هنا: توحيد النظام ليعمل محلياً بالكامل عبر Ollama
#     # ==========================================================
#     # Planner Configuration
#     # ==========================================================
#     DEFAULT_PROVIDER = ProviderName.GEMINI

#     DEFAULT_MODEL = os.getenv(
#     "GEMINI_MODEL",
#     "gemini-3.8-flash",
# )
#     MAX_TASKS = 10
#     # ==========================================================
#     # Initialization
#     # ==========================================================

#     def __init__(
#         self,
#         llm_service: LLMService,
#         provider: ProviderName = DEFAULT_PROVIDER,
#         model: str | None = None,
#         max_tasks: int = MAX_TASKS,
#     ):
#         """
#         إنشاء Planner.

#         provider:
#             مزود نموذج اللغة المستخدم للتخطيط.

#         model:
#             موديل التخطيط.
#             إذا لم يتم تمريره يستخدم AGENT_PLANNER_MODEL.

#         max_tasks:
#             الحد الأقصى لعدد المهام الناتجة.
#         """

#         if max_tasks < 1:
#             raise ValueError(
#                 "max_tasks must be greater than zero."
#             )

#         self._llm = llm_service
#         self._provider = provider
#         self._model = model or self.DEFAULT_MODEL
#         self._max_tasks = min(
#             max_tasks,
#             self.MAX_TASKS,
#         )

#     # ==========================================================
#     # Public API
#     # ==========================================================

#     async def create_plan(
#         self,
#         question: str,
#     ) -> Plan:
#         """
#         تحويل سؤال المستخدم إلى Plan.

#         يحاول أولًا استخدام الـLLM.
#         إذا فشل:
#             يستخدم fallback ذكي مبني على تحليل السؤال.
#         """

#         question = self._normalize_question(question)

#         self._log_start(question)

#         if not question:
#             logger.warning(
#                 "[Planner] Empty question received."
#             )
#             return self._create_fallback_plan(
#                 question="طلب فارغ"
#             )

#         try:

#             # --------------------------------------------------
#             # 1. Build Planner Prompt
#             # --------------------------------------------------

#             system_prompt = self._build_system_prompt()

#             # --------------------------------------------------
#             # 2. Build LLM Request
#             # --------------------------------------------------

#             request = LLMRequest(
#                 provider=self._provider,
#                 model=self._model,
#                 temperature=0.0,
#                 max_tokens=1200,
#                 messages=[
#                     LLMMessage(
#                         role=Role.SYSTEM,
#                         content=system_prompt,
#                     ),
#                     LLMMessage(
#                         role=Role.USER,
#                         content=question,
#                     ),
#                 ],
#             )

#             # --------------------------------------------------
#             # 3. Generate Plan
#             # --------------------------------------------------

#             response = await self._llm.generate(
#                 request
#             )

#             content = (response.content or "").strip()

#             if not content:
#                 raise ValueError(
#                     "Planner LLM returned an empty response."
#                 )

#             # --------------------------------------------------
#             # 4. Parse JSON
#             # --------------------------------------------------

#             raw_plan = self._parse_json(
#                 content
#             )

#             # --------------------------------------------------
#             # 5. Build and Validate Plan
#             # --------------------------------------------------

#             plan = self._build_plan(
#                 question=question,
#                 raw_plan=raw_plan,
#             )

#             logger.info(
#                 "[Planner] Plan created successfully. "
#                 "tasks=%s status=%s",
#                 len(plan.tasks),
#                 plan.status.value,
#             )

#             return plan

#         except Exception as exc:

#             logger.exception(
#                 "[Planner] Plan generation failed: %s",
#                 exc,
#             )

#             # --------------------------------------------------
#             # 6. Intelligent Fallback
#             # --------------------------------------------------

#             fallback = self._create_fallback_plan(
#                 question
#             )

#             fallback.add_error(
#                 f"LLM planner failed: {exc}"
#             )

#             return fallback

#     # ==========================================================
#     # System Prompt
#     # ==========================================================

#     def _build_system_prompt(self) -> str:
#         """
#         Prompt مركزي مسؤول عن تعريف قواعد التخطيط.
#         """

#         return """
# You are the Planner of an enterprise Business Intelligence
# platform.

# Your job is ONLY to create an execution plan.

# You MUST NOT:
# - answer the user's question
# - generate SQL
# - retrieve documents
# - perform analysis
# - write the final report

# You ONLY decide:
# 1. Which source is required.
# 2. Which tools must run.
# 3. The execution order.
# 4. The dependencies between tasks.

# AVAILABLE SOURCES:

# DATABASE
# Use DatabaseTool when the question requires:
# - numerical data
# - business metrics
# - KPIs
# - aggregations
# - records stored in databases
# - SQL/database information

# DOCUMENT
# Use RAGTool when the question requires:
# - uploaded documents
# - PDF files
# - policies
# - contracts
# - textual reports
# - unstructured document information

# BOTH
# Use both DatabaseTool and RAGTool when answering the
# question requires information from both structured database
# data and uploaded documents.

# PROCESSING TOOLS:

# AnalysisTool
# - Analyze retrieved information.
# - Extract business insights and KPIs.

# ReportTool
# - Produce the final executive response.

# PLANNING RULES:

# 1. Database-only question:
#    DatabaseTool -> AnalysisTool -> ReportTool

# 2. Document-only question:
#    RAGTool -> AnalysisTool -> ReportTool

# 3. Both-source question:
#    DatabaseTool
#    RAGTool
#    -> AnalysisTool
#    -> ReportTool

# 4. DatabaseTool and RAGTool are independent retrieval tasks
#    and may be placed before AnalysisTool.

# 5. AnalysisTool MUST depend on every retrieval task required
#    by the question.

# 6. ReportTool MUST depend on AnalysisTool.

# 7. Do not create unnecessary tasks.

# 8. Do not use unknown tools.

# 9. Use exactly these tool names:
#    DatabaseTool
#    RAGTool
#    AnalysisTool
#    ReportTool

# 10. Every task must contain:
#     id
#     name
#     description
#     tool_name
#     inputs
#     depends_on

# 11. The plan must contain at least one retrieval task and
#     normally end with AnalysisTool and ReportTool.

# 12. Return ONLY valid JSON.

# 13. Do not use Markdown.

# 14. Do not use comments inside JSON.

# 15. The JSON structure MUST be:

# {
#   "tasks": [
#     {
#       "id": "step_1",
#       "name": "Database Retrieval",
#       "description": "Retrieve required business data.",
#       "tool_name": "DatabaseTool",
#       "inputs": {
#         "query": "user question"
#       },
#       "depends_on": []
#     },
#     {
#       "id": "step_2",
#       "name": "Business Analysis",
#       "description": "Analyze retrieved information.",
#       "tool_name": "AnalysisTool",
#       "inputs": {},
#       "depends_on": ["step_1"]
#     },
#     {
#       "id": "step_3",
#       "name": "Executive Report",
#       "description": "Generate the final response.",
#       "tool_name": "ReportTool",
#       "inputs": {},
#       "depends_on": ["step_2"]
#     }
#   ]
# }

# Return JSON only.
# """.strip()

#     # ==========================================================
#     # JSON Parsing
#     # ==========================================================

#     @staticmethod
#     def _parse_json(
#         content: str,
#     ) -> dict[str, Any]:
#         """
#         تنظيف استجابة الـLLM واستخراج JSON.

#         يدعم:
#             - JSON مباشر
#             - ```json ... ```
#             - ``` ... ```
#         """

#         cleaned = content.strip()

#         if cleaned.startswith("```json"):
#             cleaned = cleaned[7:]

#         elif cleaned.startswith("```"):
#             cleaned = cleaned[3:]

#         if cleaned.endswith("```"):
#             cleaned = cleaned[:-3]

#         cleaned = cleaned.strip()

#         if not cleaned:
#             raise ValueError(
#                 "Planner returned empty JSON."
#             )

#         try:
#             data = json.loads(cleaned)

#         except json.JSONDecodeError as exc:
#             raise ValueError(
#                 f"Invalid planner JSON: {exc}"
#             ) from exc

#         if not isinstance(data, dict):
#             raise ValueError(
#                 "Planner JSON root must be an object."
#             )

#         return data

#     # ==========================================================
#     # Plan Construction
#     # ==========================================================

#     def _build_plan(
#         self,
#         question: str,
#         raw_plan: dict[str, Any],
#     ) -> Plan:
#         """
#         تحويل JSON الخام إلى Plan مع التحقق الكامل.
#         """

#         raw_tasks = raw_plan.get(
#             "tasks"
#         )

#         if not isinstance(
#             raw_tasks,
#             list,
#         ):
#             raise ValueError(
#                 "Planner response must contain a 'tasks' list."
#             )

#         if not raw_tasks:
#             raise ValueError(
#                 "Planner returned an empty task list."
#             )

#         if len(raw_tasks) > self._max_tasks:
#             raise ValueError(
#                 f"Planner returned too many tasks: "
#                 f"{len(raw_tasks)} > {self._max_tasks}"
#             )

#         tasks: list[Task] = []

#         for index, raw_task in enumerate(
#             raw_tasks,
#             start=1,
#         ):

#             if not isinstance(
#                 raw_task,
#                 dict,
#             ):
#                 raise ValueError(
#                     f"Task {index} must be an object."
#                 )

#             task = self._normalize_task(
#                 raw_task=raw_task,
#                 index=index,
#                 question=question,
#             )

#             tasks.append(task)

#         # ------------------------------------------------------
#         # Validate tool sequence
#         # ------------------------------------------------------

#         self._validate_task_sequence(
#             tasks
#         )

#         # ------------------------------------------------------
#         # Validate dependency graph
#         # ------------------------------------------------------

#         self._validate_dependencies(
#             tasks
#         )

#         # ------------------------------------------------------
#         # Create Plan
#         # ------------------------------------------------------

#         plan = Plan(
#             original_question=question,
#             tasks=tasks,
#             metadata={
#                 "planner_provider": self._provider.value,
#                 "planner_model": self._model,
#                 "generated_by": "llm",
#             },
#         )

#         return plan

#     # ==========================================================
#     # Task Normalization
#     # ==========================================================

#     def _normalize_task(
#         self,
#         raw_task: dict[str, Any],
#         index: int,
#         question: str,
#     ) -> Task:
#         """
#         تنظيف والتحقق من مهمة واحدة.
#         """

#         task_id = str(
#             raw_task.get(
#                 "id",
#                 f"step_{index}",
#             )
#         ).strip()

#         name = str(
#             raw_task.get(
#                 "name",
#                 f"Task {index}",
#             )
#         ).strip()

#         description = str(
#             raw_task.get(
#                 "description",
#                 "Execute the requested task.",
#             )
#         ).strip()

#         tool_name = str(
#             raw_task.get(
#                 "tool_name",
#                 "",
#             )
#         ).strip()

#         inputs = raw_task.get(
#             "inputs",
#             {},
#         )

#         depends_on = raw_task.get(
#             "depends_on",
#             [],
#         )

#         # ------------------------------------------------------
#         # Basic Validation
#         # ------------------------------------------------------

#         if not task_id:
#             raise ValueError(
#                 f"Task {index} has an empty id."
#             )

#         if not name:
#             raise ValueError(
#                 f"Task '{task_id}' has an empty name."
#             )

#         if not description:
#             raise ValueError(
#                 f"Task '{task_id}' has an empty description."
#             )

#         # ------------------------------------------------------
#         # Tool Validation
#         # ------------------------------------------------------

#         if tool_name not in self.ALLOWED_TOOLS:
#             raise ValueError(
#                 f"Unsupported tool: '{tool_name}'."
#             )

#         # ------------------------------------------------------
#         # Input Validation
#         # ------------------------------------------------------

#         if not isinstance(
#             inputs,
#             dict,
#         ):
#             raise ValueError(
#                 f"Task '{task_id}' inputs must be an object."
#             )

#         if not isinstance(
#             depends_on,
#             list,
#         ):
#             raise ValueError(
#                 f"Task '{task_id}' depends_on must be a list."
#             )

#         # ------------------------------------------------------
#         # Retrieval Queries
#         # ------------------------------------------------------

#         if tool_name in (
#             "DatabaseTool",
#             "RAGTool",
#         ):

#             query = inputs.get(
#                 "query",
#                 question,
#             )

#             if not isinstance(
#                 query,
#                 str,
#             ) or not query.strip():

#                 inputs = {
#                     **inputs,
#                     "query": question,
#                 }

#         # ------------------------------------------------------
#         # Normalize dependency IDs
#         # ------------------------------------------------------

#         normalized_dependencies = []

#         for dependency in depends_on:

#             dependency_id = str(
#                 dependency
#             ).strip()

#             if dependency_id:
#                 normalized_dependencies.append(
#                     dependency_id
#                 )

#         return Task(
#             id=task_id,
#             name=name,
#             description=description,
#             tool_name=tool_name,
#             inputs=inputs,
#             depends_on=normalized_dependencies,
#         )

#     # ==========================================================
#     # Task Sequence Validation
#     # ==========================================================

#     def _validate_task_sequence(
#         self,
#         tasks: list[Task],
#     ) -> None:
#         """
#         التأكد من أن الخطة تحتوي على تدفق منطقي.
#         """

#         tool_names = [
#             task.tool_name
#             for task in tasks
#         ]

#         retrieval_tools = [
#             tool
#             for tool in tool_names
#             if tool in self.ALLOWED_RETRIEVAL_TOOLS
#         ]

#         if not retrieval_tools:
#             raise ValueError(
#                 "Plan must contain at least one retrieval tool."
#             )

#         # Report should not execute before Analysis.
#         if "ReportTool" in tool_names:

#             report_index = tool_names.index(
#                 "ReportTool"
#             )

#             if "AnalysisTool" not in tool_names:
#                 raise ValueError(
#                     "ReportTool requires AnalysisTool."
#                 )

#             analysis_index = tool_names.index(
#                 "AnalysisTool"
#             )

#             if analysis_index > report_index:
#                 raise ValueError(
#                     "AnalysisTool must appear before ReportTool."
#                 )

#         # Analysis should appear after retrieval tools.
#         if "AnalysisTool" in tool_names:

#             analysis_index = tool_names.index(
#                 "AnalysisTool"
#             )

#             for index, tool_name in enumerate(
#                 tool_names
#             ):

#                 if tool_name in self.ALLOWED_RETRIEVAL_TOOLS:
#                     if index > analysis_index:
#                         raise ValueError(
#                             "Retrieval tasks must appear before "
#                             "AnalysisTool."
#                         )

#     # ==========================================================
#     # Dependency Validation
#     # ==========================================================

#     def _validate_dependencies(
#         self,
#         tasks: list[Task],
#     ) -> None:
#         """
#         التحقق من:
#             - عدم وجود Dependencies غير موجودة.
#             - عدم وجود Self Dependency.
#             - عدم وجود Circular Dependency.
#         """

#         task_ids = {
#             task.id
#             for task in tasks
#         }

#         # ------------------------------------------------------
#         # Existing dependencies
#         # ------------------------------------------------------

#         for task in tasks:

#             for dependency in task.depends_on:

#                 if dependency not in task_ids:
#                     raise ValueError(
#                         f"Task '{task.id}' depends on "
#                         f"unknown task '{dependency}'."
#                     )

#                 if dependency == task.id:
#                     raise ValueError(
#                         f"Task '{task.id}' cannot depend on itself."
#                     )

#         # ------------------------------------------------------
#         # Cycle Detection
#         # ------------------------------------------------------

#         graph = {
#             task.id: list(task.depends_on)
#             for task in tasks
#         }

#         visiting: set[str] = set()
#         visited: set[str] = set()

#         def visit(
#             task_id: str,
#         ) -> None:

#             if task_id in visiting:
#                 raise ValueError(
#                     "Circular task dependency detected."
#                 )

#             if task_id in visited:
#                 return

#             visiting.add(task_id)

#             for dependency in graph[task_id]:
#                 visit(dependency)

#             visiting.remove(task_id)
#             visited.add(task_id)

#         for task_id in graph:
#             visit(task_id)

#     # ==========================================================
#     # Intelligent Fallback
#     # ==========================================================

#     def _create_fallback_plan(
#         self,
#         question: str,
#     ) -> Plan:
#         """
#         إنشاء خطة fallback بدون LLM.

#         بدل استخدام Database دائمًا، يتم محاولة تحديد المصدر
#         المطلوب من السؤال.
#         """

#         source = self._detect_source(
#             question
#         )

#         tasks: list[Task] = []

#         # ------------------------------------------------------
#         # Database
#         # ------------------------------------------------------

#         if source in (
#             "database",
#             "both",
#         ):

#             tasks.append(
#                 Task(
#                     id="step_1",
#                     name="Database Retrieval",
#                     description=(
#                         "Retrieve structured business "
#                         "data from the database."
#                     ),
#                     tool_name="DatabaseTool",
#                     inputs={
#                         "query": question
#                     },
#                     depends_on=[],
#                 )
#             )

#         # ------------------------------------------------------
#         # RAG
#         # ------------------------------------------------------

#         if source in (
#             "document",
#             "both",
#         ):

#             task_id = (
#                 "step_2"
#                 if tasks
#                 else "step_1"
#             )

#             tasks.append(
#                 Task(
#                     id=task_id,
#                     name="Document Retrieval",
#                     description=(
#                         "Retrieve relevant information "
#                         "from uploaded documents."
#                     ),
#                     tool_name="RAGTool",
#                     inputs={
#                         "query": question
#                     },
#                     depends_on=[],
#                 )
#             )

#         # ------------------------------------------------------
#         # Analysis
#         # ------------------------------------------------------

#         retrieval_ids = [
#             task.id
#             for task in tasks
#         ]

#         analysis_id = (
#             f"step_{len(tasks) + 1}"
#         )

#         tasks.append(
#             Task(
#                 id=analysis_id,
#                 name="Business Analysis",
#                 description=(
#                     "Analyze the retrieved information "
#                     "and extract business insights."
#                 ),
#                 tool_name="AnalysisTool",
#                 inputs={},
#                 depends_on=retrieval_ids,
#             )
#         )

#         # ------------------------------------------------------
#         # Report
#         # ------------------------------------------------------

#         report_id = (
#             f"step_{len(tasks) + 1}"
#         )

#         tasks.append(
#             Task(
#                 id=report_id,
#                 name="Executive Report",
#                 description=(
#                     "Generate the final executive response."
#                 ),
#                 tool_name="ReportTool",
#                 inputs={},
#                 depends_on=[
#                     analysis_id
#                 ],
#             )
#         )

#         return Plan(
#             original_question=question,
#             tasks=tasks,
#             metadata={
#                 "planner_provider": self._provider.value,
#                 "planner_model": self._model,
#                 "generated_by": "fallback",
#                 "detected_source": source,
#             },
#         )

#     # ==========================================================
#     # Source Detection
#     # ==========================================================

#     @staticmethod
#     def _detect_source(
#         question: str,
#     ) -> str:
#         """
#         تحديد المصدر في حالة فشل LLM.

#         هذا ليس بديلًا عن الـLLM Planner،
#         بل fallback فقط.
#         """

#         normalized = question.lower()

#         document_keywords = (
#             "document",
#             "documents",
#             "pdf",
#             "file",
#             "files",
#             "policy",
#             "policies",
#             "contract",
#             "contracts",
#             "report",
#             "reports",
#             "document:",
#             "مستند",
#             "مستندات",
#             "ملف",
#             "ملفات",
#             "pdf",
#             "سياسة",
#             "سياسات",
#             "عقد",
#             "عقود",
#             "تقرير",
#             "تقارير",
#         )

#         database_keywords = (
#             "database",
#             "sql",
#             "sales",
#             "revenue",
#             "profit",
#             "orders",
#             "customers",
#             "users",
#             "count",
#             "total",
#             "average",
#             "sum",
#             "عدد",
#             "إجمالي",
#             "مبيعات",
#             "أرباح",
#             "طلبات",
#             "عملاء",
#             "عملاء",
#             "متوسط",
#             "مجموع",
#         )

#         document_match = any(
#             keyword in normalized
#             for keyword in document_keywords
#         )

#         database_match = any(
#             keyword in normalized
#             for keyword in database_keywords
#         )

#         if document_match and database_match:
#             return "both"

#         if document_match:
#             return "document"

#         return "database"

#     # ==========================================================
#     # Question Normalization
#     # ==========================================================

#     @staticmethod
#     def _normalize_question(
#         question: str,
#     ) -> str:
#         """
#         تنظيف سؤال المستخدم قبل إدخاله إلى Planner.
#         """

#         if question is None:
#             return ""

#         return " ".join(
#             str(question).strip().split()
#         )

#     # ==========================================================
#     # Logging
#     # ==========================================================

#     @staticmethod
#     def _log_start(
#         question: str,
#     ) -> None:
#         logger.info(
#             "[Planner] Creating execution plan for: %s",
#             question,
#         )







from __future__ import annotations

import json
import logging
import os
from typing import Any

from src.modules.llm.application.services import LLMService
from src.modules.llm.domain.entities import LLMMessage, LLMRequest
from src.modules.llm.domain.value_objects import ProviderName, Role

from src.modules.multi_agent.domain.plan import Plan, PlanStatus
from src.modules.multi_agent.domain.task import Task


logger = logging.getLogger(__name__)


class Planner:
    """
    Planner مسؤول عن تحويل سؤال المستخدم إلى Execution Plan.

    المسؤوليات:
        1. فهم طبيعة السؤال.
        2. اختيار مصدر البيانات:
           - database
           - document
           - both
        3. اختيار الأدوات المناسبة.
        4. بناء المهام.
        5. تحديد Dependencies بين المهام.
        6. التحقق من الخطة الناتجة.
        7. منع الأدوات غير المسموح بها.
        8. التعامل مع أخطاء الـLLM.
        9. توفير fallback آمن ومنطقي.

    Planner لا ينفذ أي Task.
    التنفيذ مسؤولية TaskExecutor.
    """

    # ==========================================================
    # Allowed Tools
    # ==========================================================

    ALLOWED_RETRIEVAL_TOOLS = {
        "DatabaseTool",
        "RAGTool",
    }

    ALLOWED_PROCESSING_TOOLS = {
        "AnalysisTool",
        "ReportTool",
    }

    ALLOWED_TOOLS = (
        ALLOWED_RETRIEVAL_TOOLS
        | ALLOWED_PROCESSING_TOOLS
    )

    # ==========================================================
    # Planner Configuration
    # ==========================================================
    DEFAULT_PROVIDER = ProviderName.GEMINI

    DEFAULT_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash",
    )
    MAX_TASKS = 10
    
    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(
        self,
        llm_service: LLMService,
        provider: ProviderName = DEFAULT_PROVIDER,
        model: str | None = None,
        max_tasks: int = MAX_TASKS,
    ):
        """
        إنشاء Planner.

        provider:
            مزود نموذج اللغة المستخدم للتخطيط.

        model:
            موديل التخطيط.
            إذا لم يتم تمريره يستخدم AGENT_PLANNER_MODEL.

        max_tasks:
            الحد الأقصى لعدد المهام الناتجة.
        """

        if max_tasks < 1:
            raise ValueError(
                "max_tasks must be greater than zero."
            )

        self._llm = llm_service
        self._provider = provider
        self._model = model or self.DEFAULT_MODEL
        self._max_tasks = min(
            max_tasks,
            self.MAX_TASKS,
        )

    # ==========================================================
    # Public API
    # ==========================================================

    async def create_plan(
        self,
        question: str,
    ) -> Plan:
        """
        تحويل سؤال المستخدم إلى Plan.

        يحاول أولًا استخدام الـLLM.
        إذا فشل:
            يستخدم fallback ذكي مبني على تحليل السؤال.
        """

        question = self._normalize_question(question)

        self._log_start(question)

        if not question:
            logger.warning(
                "[Planner] Empty question received."
            )
            return self._create_fallback_plan(
                question="طلب فارغ"
            )

        try:

            # --------------------------------------------------
            # 1. Build Planner Prompt
            # --------------------------------------------------

            system_prompt = self._build_system_prompt()

            # --------------------------------------------------
            # 2. Build LLM Request
            # --------------------------------------------------

            request = LLMRequest(
                provider=self._provider,
                model=self._model,
                temperature=0.0,
                max_tokens=1200,
                messages=[
                    LLMMessage(
                        role=Role.SYSTEM,
                        content=system_prompt,
                    ),
                    LLMMessage(
                        role=Role.USER,
                        content=question,
                    ),
                ],
            )

            # --------------------------------------------------
            # 3. Generate Plan
            # --------------------------------------------------

            response = await self._llm.generate(
                request
            )

            content = (response.content or "").strip()

            if not content:
                raise ValueError(
                    "Planner LLM returned an empty response."
                )

            # --------------------------------------------------
            # 4. Parse JSON
            # --------------------------------------------------

            raw_plan = self._parse_json(
                content
            )

            # --------------------------------------------------
            # 5. Build and Validate Plan
            # --------------------------------------------------

            plan = self._build_plan(
                question=question,
                raw_plan=raw_plan,
            )

            logger.info(
                "[Planner] Plan created successfully. "
                "tasks=%s status=%s",
                len(plan.tasks),
                plan.status.value,
            )

            return plan

        except Exception as exc:

            logger.exception(
                "[Planner] Plan generation failed: %s",
                exc,
            )

            # --------------------------------------------------
            # 6. Intelligent Fallback
            # --------------------------------------------------

            fallback = self._create_fallback_plan(
                question
            )

            fallback.add_error(
                f"LLM planner failed: {exc}"
            )

            return fallback

    # ==========================================================
    # System Prompt
    # ==========================================================

    def _build_system_prompt(self) -> str:
        """
        Prompt مركزي مسؤول عن تعريف قواعد التخطيط.
        """

        return """
You are the Planner of an enterprise Business Intelligence platform.

Your job is ONLY to create an execution plan.

You MUST NOT:
- answer the user's question
- generate SQL
- retrieve documents
- perform analysis
- write the final report

You ONLY decide:
1. Which source is required.
2. Which tools must run.
3. The execution order.
4. The dependencies between tasks.

AVAILABLE SOURCES:

DATABASE
Use DatabaseTool when the question requires:
- numerical data
- business metrics
- KPIs
- aggregations
- records stored in databases
- SQL/database information

DOCUMENT
Use RAGTool when the question requires:
- uploaded documents
- PDF files
- text files (docx, txt, csv)
- policies, rules, or guidelines
- textual explanations or context not found in a SQL database

BOTH
Use both DatabaseTool and RAGTool when answering the question requires information from both structured database data (numbers) and unstructured uploaded documents (context).

PROCESSING TOOLS:

AnalysisTool
- Analyze retrieved information from databases and/or documents.
- Extract business insights.

ReportTool
- Produce the final executive response in Arabic.

PLANNING RULES:

1. Database-only question:
   DatabaseTool -> AnalysisTool -> ReportTool

2. Document-only question:
   RAGTool -> AnalysisTool -> ReportTool

3. Both-source question:
   DatabaseTool
   RAGTool
   -> AnalysisTool
   -> ReportTool

4. DatabaseTool and RAGTool are independent retrieval tasks and may be placed before AnalysisTool.

5. AnalysisTool MUST depend on every retrieval task required by the question.

6. ReportTool MUST depend on AnalysisTool.

7. Use exactly these tool names: DatabaseTool, RAGTool, AnalysisTool, ReportTool.

8. Return ONLY valid JSON matching this structure:

{
  "tasks": [
    {
      "id": "step_1",
      "name": "Database Retrieval",
      "description": "Retrieve required business data.",
      "tool_name": "DatabaseTool",
      "inputs": {
        "query": "user question"
      },
      "depends_on": []
    },
    {
      "id": "step_2",
      "name": "Document Retrieval",
      "description": "Retrieve required textual context.",
      "tool_name": "RAGTool",
      "inputs": {
        "query": "user question"
      },
      "depends_on": []
    },
    {
      "id": "step_3",
      "name": "Business Analysis",
      "description": "Analyze retrieved information.",
      "tool_name": "AnalysisTool",
      "inputs": {},
      "depends_on": ["step_1", "step_2"]
    },
    {
      "id": "step_4",
      "name": "Executive Report",
      "description": "Generate the final response.",
      "tool_name": "ReportTool",
      "inputs": {},
      "depends_on": ["step_3"]
    }
  ]
}
""".strip()

    # ==========================================================
    # JSON Parsing
    # ==========================================================

    @staticmethod
    def _parse_json(
        content: str,
    ) -> dict[str, Any]:
        """
        تنظيف استجابة الـLLM واستخراج JSON.
        """

        cleaned = content.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        if not cleaned:
            raise ValueError(
                "Planner returned empty JSON."
            )

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid planner JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "Planner JSON root must be an object."
            )

        return data

    # ==========================================================
    # Plan Construction
    # ==========================================================

    def _build_plan(
        self,
        question: str,
        raw_plan: dict[str, Any],
    ) -> Plan:
        """
        تحويل JSON الخام إلى Plan مع التحقق الكامل.
        """

        raw_tasks = raw_plan.get(
            "tasks"
        )

        if not isinstance(
            raw_tasks,
            list,
        ):
            raise ValueError(
                "Planner response must contain a 'tasks' list."
            )

        if not raw_tasks:
            raise ValueError(
                "Planner returned an empty task list."
            )

        if len(raw_tasks) > self._max_tasks:
            raise ValueError(
                f"Planner returned too many tasks: "
                f"{len(raw_tasks)} > {self._max_tasks}"
            )

        tasks: list[Task] = []

        for index, raw_task in enumerate(
            raw_tasks,
            start=1,
        ):

            if not isinstance(
                raw_task,
                dict,
            ):
                raise ValueError(
                    f"Task {index} must be an object."
                )

            task = self._normalize_task(
                raw_task=raw_task,
                index=index,
                question=question,
            )

            tasks.append(task)

        # ------------------------------------------------------
        # Validate tool sequence
        # ------------------------------------------------------

        self._validate_task_sequence(
            tasks
        )

        # ------------------------------------------------------
        # Validate dependency graph
        # ------------------------------------------------------

        self._validate_dependencies(
            tasks
        )

        # ------------------------------------------------------
        # Create Plan
        # ------------------------------------------------------

        plan = Plan(
            original_question=question,
            tasks=tasks,
            metadata={
                "planner_provider": self._provider.value,
                "planner_model": self._model,
                "generated_by": "llm",
            },
        )

        return plan

    # ==========================================================
    # Task Normalization
    # ==========================================================

    def _normalize_task(
        self,
        raw_task: dict[str, Any],
        index: int,
        question: str,
    ) -> Task:
        """
        تنظيف والتحقق من مهمة واحدة.
        """

        task_id = str(
            raw_task.get(
                "id",
                f"step_{index}",
            )
        ).strip()

        name = str(
            raw_task.get(
                "name",
                f"Task {index}",
            )
        ).strip()

        description = str(
            raw_task.get(
                "description",
                "Execute the requested task.",
            )
        ).strip()

        tool_name = str(
            raw_task.get(
                "tool_name",
                "",
            )
        ).strip()

        inputs = raw_task.get(
            "inputs",
            {},
        )

        depends_on = raw_task.get(
            "depends_on",
            [],
        )

        # ------------------------------------------------------
        # Basic Validation
        # ------------------------------------------------------

        if not task_id:
            raise ValueError(
                f"Task {index} has an empty id."
            )

        if not name:
            raise ValueError(
                f"Task '{task_id}' has an empty name."
            )

        if not description:
            raise ValueError(
                f"Task '{task_id}' has an empty description."
            )

        # ------------------------------------------------------
        # Tool Validation
        # ------------------------------------------------------

        if tool_name not in self.ALLOWED_TOOLS:
            raise ValueError(
                f"Unsupported tool: '{tool_name}'."
            )

        # ------------------------------------------------------
        # Input Validation
        # ------------------------------------------------------

        if not isinstance(
            inputs,
            dict,
        ):
            raise ValueError(
                f"Task '{task_id}' inputs must be an object."
            )

        if not isinstance(
            depends_on,
            list,
        ):
            raise ValueError(
                f"Task '{task_id}' depends_on must be a list."
            )

        # ------------------------------------------------------
        # Retrieval Queries
        # ------------------------------------------------------

        if tool_name in (
            "DatabaseTool",
            "RAGTool",
        ):

            query = inputs.get(
                "query",
                question,
            )

            if not isinstance(
                query,
                str,
            ) or not query.strip():

                inputs = {
                    **inputs,
                    "query": question,
                }

        # ------------------------------------------------------
        # Normalize dependency IDs
        # ------------------------------------------------------

        normalized_dependencies = []

        for dependency in depends_on:

            dependency_id = str(
                dependency
            ).strip()

            if dependency_id:
                normalized_dependencies.append(
                    dependency_id
                )

        return Task(
            id=task_id,
            name=name,
            description=description,
            tool_name=tool_name,
            inputs=inputs,
            depends_on=normalized_dependencies,
        )

    # ==========================================================
    # Task Sequence Validation
    # ==========================================================

    def _validate_task_sequence(
        self,
        tasks: list[Task],
    ) -> None:
        """
        التأكد من أن الخطة تحتوي على تدفق منطقي.
        """

        tool_names = [
            task.tool_name
            for task in tasks
        ]

        retrieval_tools = [
            tool
            for tool in tool_names
            if tool in self.ALLOWED_RETRIEVAL_TOOLS
        ]

        if not retrieval_tools:
            raise ValueError(
                "Plan must contain at least one retrieval tool."
            )

        # Report should not execute before Analysis.
        if "ReportTool" in tool_names:

            report_index = tool_names.index(
                "ReportTool"
            )

            if "AnalysisTool" not in tool_names:
                raise ValueError(
                    "ReportTool requires AnalysisTool."
                )

            analysis_index = tool_names.index(
                "AnalysisTool"
            )

            if analysis_index > report_index:
                raise ValueError(
                    "AnalysisTool must appear before ReportTool."
                )

        # Analysis should appear after retrieval tools.
        if "AnalysisTool" in tool_names:

            analysis_index = tool_names.index(
                "AnalysisTool"
            )

            for index, tool_name in enumerate(
                tool_names
            ):

                if tool_name in self.ALLOWED_RETRIEVAL_TOOLS:
                    if index > analysis_index:
                        raise ValueError(
                            "Retrieval tasks must appear before "
                            "AnalysisTool."
                        )

    # ==========================================================
    # Dependency Validation
    # ==========================================================

    def _validate_dependencies(
        self,
        tasks: list[Task],
    ) -> None:
        """
        التحقق من:
            - عدم وجود Dependencies غير موجودة.
            - عدم وجود Self Dependency.
            - عدم وجود Circular Dependency.
        """

        task_ids = {
            task.id
            for task in tasks
        }

        # ------------------------------------------------------
        # Existing dependencies
        # ------------------------------------------------------

        for task in tasks:

            for dependency in task.depends_on:

                if dependency not in task_ids:
                    raise ValueError(
                        f"Task '{task.id}' depends on "
                        f"unknown task '{dependency}'."
                    )

                if dependency == task.id:
                    raise ValueError(
                        f"Task '{task.id}' cannot depend on itself."
                    )

        # ------------------------------------------------------
        # Cycle Detection
        # ------------------------------------------------------

        graph = {
            task.id: list(task.depends_on)
            for task in tasks
        }

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(
            task_id: str,
        ) -> None:

            if task_id in visiting:
                raise ValueError(
                    "Circular task dependency detected."
                )

            if task_id in visited:
                return

            visiting.add(task_id)

            for dependency in graph[task_id]:
                visit(dependency)

            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)

    # ==========================================================
    # Intelligent Fallback
    # ==========================================================

    def _create_fallback_plan(
        self,
        question: str,
    ) -> Plan:
        """
        إنشاء خطة fallback بدون LLM.
        """

        source = self._detect_source(
            question
        )

        tasks: list[Task] = []

        # ------------------------------------------------------
        # Database
        # ------------------------------------------------------

        if source in (
            "database",
            "both",
        ):

            tasks.append(
                Task(
                    id="step_1",
                    name="Database Retrieval",
                    description=(
                        "Retrieve structured business data from the database."
                    ),
                    tool_name="DatabaseTool",
                    inputs={
                        "query": question
                    },
                    depends_on=[],
                )
            )

        # ------------------------------------------------------
        # RAG
        # ------------------------------------------------------

        if source in (
            "document",
            "both",
        ):

            task_id = (
                "step_2"
                if tasks
                else "step_1"
            )

            tasks.append(
                Task(
                    id=task_id,
                    name="Document Retrieval",
                    description=(
                        "Retrieve relevant information from uploaded documents."
                    ),
                    tool_name="RAGTool",
                    inputs={
                        "query": question
                    },
                    depends_on=[],
                )
            )

        # ------------------------------------------------------
        # Analysis
        # ------------------------------------------------------

        retrieval_ids = [
            task.id
            for task in tasks
        ]

        analysis_id = (
            f"step_{len(tasks) + 1}"
        )

        tasks.append(
            Task(
                id=analysis_id,
                name="Business Analysis",
                description=(
                    "Analyze the retrieved information and extract business insights."
                ),
                tool_name="AnalysisTool",
                inputs={},
                depends_on=retrieval_ids,
            )
        )

        # ------------------------------------------------------
        # Report
        # ------------------------------------------------------

        report_id = (
            f"step_{len(tasks) + 1}"
        )

        tasks.append(
            Task(
                id=report_id,
                name="Executive Report",
                description=(
                    "Generate the final executive response."
                ),
                tool_name="ReportTool",
                inputs={},
                depends_on=[
                    analysis_id
                ],
            )
        )

        return Plan(
            original_question=question,
            tasks=tasks,
            metadata={
                "planner_provider": self._provider.value,
                "planner_model": self._model,
                "generated_by": "fallback",
                "detected_source": source,
            },
        )

    # ==========================================================
    # Source Detection
    # ==========================================================

    @staticmethod
    def _detect_source(
        question: str,
    ) -> str:
        """
        تحديد المصدر في حالة فشل LLM.
        """

        normalized = question.lower()

        document_keywords = (
            "document", "documents", "pdf", "file", "files", "policy", "policies",
            "contract", "contracts", "report", "reports", "document:", "مستند",
            "مستندات", "ملف", "ملفات", "pdf", "سياسة", "سياسات", "عقد", "عقود",
            "تقرير", "تقارير", "لوائح", "قانون", "ملخص"
        )

        database_keywords = (
            "database", "sql", "sales", "revenue", "profit", "orders", "customers",
            "users", "count", "total", "average", "sum", "عدد", "إجمالي", "مبيعات",
            "أرباح", "طلبات", "عملاء", "متوسط", "مجموع", "نسبة", "طالب", "طلاب", "قسم"
        )

        document_match = any(
            keyword in normalized
            for keyword in document_keywords
        )

        database_match = any(
            keyword in normalized
            for keyword in database_keywords
        )

        if document_match and database_match:
            return "both"

        if document_match:
            return "document"

        return "database"

    # ==========================================================
    # Question Normalization
    # ==========================================================

    @staticmethod
    def _normalize_question(
        question: str,
    ) -> str:
        """
        تنظيف سؤال المستخدم قبل إدخاله إلى Planner.
        """

        if question is None:
            return ""

        return " ".join(
            str(question).strip().split()
        )

    # ==========================================================
    # Logging
    # ==========================================================

    @staticmethod
    def _log_start(
        question: str,
    ) -> None:
        logger.info(
            "[Planner] Creating execution plan for: %s",
            question,
        )