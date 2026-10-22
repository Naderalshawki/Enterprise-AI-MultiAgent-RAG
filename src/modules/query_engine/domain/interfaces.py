from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.modules.query_engine.domain.entities import (
    QueryContext,
    QueryExecution,
    QueryRequest,
    QueryResult,
)


# ============================================================
# Query Engine
# ============================================================

class QueryEngine(ABC):
    """
    العقد الأساسي لمحرك الاستعلامات.

    QueryEngine يمثل الواجهة العامة التي تستخدمها
    طبقة Application لتنفيذ Business Query.

    QueryEngine لا يفرض كيف سيتم التنفيذ داخليًا.
    """

    @abstractmethod
    async def execute(
        self,
        request: QueryRequest,
    ) -> QueryResult:
        """
        تنفيذ طلب استعلام كامل وإرجاع النتيجة الموحدة.
        """

        raise NotImplementedError


# ============================================================
# Query Classifier
# ============================================================

class QueryClassifier(ABC):
    """
    مسؤول عن تحديد Intent الخاص بالاستعلام.

    مثال:

        "كم إجمالي المبيعات؟"
                    ↓
            QueryIntent.DATA

        "ما هي جداول قاعدة البيانات؟"
                    ↓
            QueryIntent.SCHEMA
    """

    @abstractmethod
    async def classify(
        self,
        request: QueryRequest,
    ) -> QueryContext:
        """
        تصنيف الاستعلام وإنشاء QueryContext.
        """

        raise NotImplementedError


# ============================================================
# Query Context Builder
# ============================================================

class QueryContextBuilder(ABC):
    """
    مسؤول عن بناء السياق الداخلي للاستعلام.

    يمكن أن يجمع:
        - Intent
        - Source
        - Execution Mode
        - Priority
        - Metadata
    """

    @abstractmethod
    async def build(
        self,
        request: QueryRequest,
    ) -> QueryContext:
        """
        إنشاء QueryContext من QueryRequest.
        """

        raise NotImplementedError


# ============================================================
# Query Source Adapter
# ============================================================

class QuerySourceAdapter(ABC):
    """
    واجهة الطبقة التي تربط Query Engine بمصدر البيانات.

    في المعمارية النهائية المصدر هو ChatDatabase،
    والذي يتعامل مع قاعدة البيانات النهائية
    Supabase / PostgreSQL.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        اسم المصدر الذي يتعامل معه الـAdapter.
        """

        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        request: QueryRequest,
        context: QueryContext,
    ) -> QueryResult:
        """
        تنفيذ الاستعلام على المصدر المناسب.
        """

        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """
        التحقق من جاهزية المصدر.
        """

        raise NotImplementedError


# ============================================================
# Query Execution Manager
# ============================================================

class QueryExecutionManager(ABC):
    """
    مسؤول عن إدارة دورة تنفيذ QueryExecution.

    هذه الواجهة تسمح لاحقًا بإضافة:
        - Retry
        - Timeout
        - Metrics
        - Cancellation
    """

    @abstractmethod
    async def start(
        self,
        execution: QueryExecution,
    ) -> QueryExecution:
        """
        بدء عملية التنفيذ.
        """

        raise NotImplementedError

    @abstractmethod
    async def complete(
        self,
        execution: QueryExecution,
    ) -> QueryExecution:
        """
        تسجيل نجاح التنفيذ.
        """

        raise NotImplementedError

    @abstractmethod
    async def fail(
        self,
        execution: QueryExecution,
        error: str,
    ) -> QueryExecution:
        """
        تسجيل فشل التنفيذ.
        """

        raise NotImplementedError

    @abstractmethod
    async def cancel(
        self,
        execution: QueryExecution,
        reason: str | None = None,
    ) -> QueryExecution:
        """
        إلغاء عملية التنفيذ.
        """

        raise NotImplementedError


# ============================================================
# Query Logger / Audit Port
# ============================================================

class QueryLogger(ABC):
    """
    عقد تسجيل أحداث الاستعلام.

    هذه الواجهة لا تعني أن Audit Log الخاص بالنظام
    قد تم تنفيذه هنا؛ هي فقط Port تسمح بإضافة
    logging/observability دون ربط Domain بتقنية تخزين محددة.
    """

    @abstractmethod
    async def log_started(
        self,
        request: QueryRequest,
        context: QueryContext,
    ) -> None:
        """
        تسجيل بداية الاستعلام.
        """

        raise NotImplementedError

    @abstractmethod
    async def log_completed(
        self,
        request: QueryRequest,
        context: QueryContext,
        result: QueryResult,
    ) -> None:
        """
        تسجيل اكتمال الاستعلام.
        """

        raise NotImplementedError

    @abstractmethod
    async def log_failed(
        self,
        request: QueryRequest,
        context: QueryContext,
        error: str,
    ) -> None:
        """
        تسجيل فشل الاستعلام.
        """

        raise NotImplementedError


# ============================================================
# Query Result Mapper
# ============================================================

class QueryResultMapper(ABC):
    """
    تحويل نتائج المصدر الخارجي إلى QueryResult.

    الهدف:
        منع Application/Domain من الاعتماد مباشرة
        على DTOs الخاصة بـChatDatabase أو أي مصدر آخر.
    """

    @abstractmethod
    def map(
        self,
        source_result: Any,
        request: QueryRequest,
        context: QueryContext,
    ) -> QueryResult:
        """
        تحويل نتيجة المصدر إلى QueryResult.
        """

        raise NotImplementedError