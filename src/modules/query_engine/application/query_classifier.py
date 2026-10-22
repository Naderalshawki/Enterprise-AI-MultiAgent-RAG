from __future__ import annotations

import logging
import re

from src.modules.query_engine.domain.entities import (
    QueryContext,
    QueryRequest,
)
from src.modules.query_engine.domain.enums import (
    QueryIntent,
)
from src.modules.query_engine.domain.interfaces import (
    QueryClassifier,
)

logger = logging.getLogger(__name__)


class DefaultQueryClassifier(QueryClassifier):
    """
    المصنف الافتراضي للاستعلامات داخل Query Engine.

    المسؤولية:
        تحديد QueryIntent فقط.

    التصنيفات المدعومة:

        DATA
            طلب بيانات فعلية ورقمية من قاعدة البيانات.

        DOCUMENT
            طلب معلومات نصية، لوائح، أو سياسات من المستندات (RAG).

        SCHEMA
            سؤال عن بنية قاعدة البيانات:
            الجداول، الأعمدة، العلاقات، أنواع البيانات...

        DATABASE_INFO
            سؤال عن معلومات عامة حول قاعدة البيانات.

        UNKNOWN
            لم يتم التعرف على نوع الطلب بثقة كافية.

    ملاحظة معمارية مهمة:
        هذا المصنف لا يقرر:
            Database / Document / Both بشكل تنفيذي (هذا دور الـ Planner).
        هو فقط يعطي نية مبدئية (Intent) لتسريع التوجيه وتقليل الهلوسة.
    """

    # ==========================================================
    # Keyword Groups
    # ==========================================================

    _SCHEMA_PATTERNS = (
        r"\btable\b", r"\btables\b", r"\bcolumn\b", r"\bcolumns\b",
        r"\bschema\b", r"\bfield\b", r"\bfields\b", r"\bprimary key\b",
        r"\bforeign key\b", r"\brelationship\b", r"\brelationships\b",
        r"\bdata type\b", r"\bdatatype\b", r"\bstructure\b", r"\bdatabase structure\b",

        # Arabic
        r"جدول", r"جداول", r"عمود", r"أعمدة", r"حقل", r"حقول",
        r"مخطط قاعدة البيانات", r"هيكل قاعدة البيانات", r"بنية قاعدة البيانات",
        r"المفتاح الأساسي", r"المفتاح الأجنبي", r"العلاقات", r"نوع البيانات",
    )

    _DATABASE_INFO_PATTERNS = (
        r"\bdatabase\b", r"\bdb\b", r"\bpostgres\b", r"\bpostgresql\b",
        r"\bconnection\b", r"\bconnected\b", r"\bserver\b", r"\bhost\b", r"\bversion\b",

        # Arabic
        r"قاعدة البيانات", r"الداتابيس", r"البيانات", r"الاتصال بقاعدة البيانات",
        r"اتصال قاعدة البيانات", r"إصدار قاعدة البيانات", r"الخادم",
    )

    _DOCUMENT_PATTERNS = (
        # RAG / Document terms
        r"\bdocument\b", r"\bdocuments\b", r"\bpdf\b", r"\bfile\b", r"\bfiles\b",
        r"\bpolicy\b", r"\bpolicies\b", r"\bcontract\b", r"\bcontracts\b",
        r"\brule\b", r"\brules\b", r"\bguideline\b", r"\bguidelines\b",
        r"\bexplain\b", r"\bwhat is the condition\b", r"\bhow to\b",

        # Arabic
        r"مستند", r"مستندات", r"ملف", r"ملفات", r"سياسة", r"سياسات",
        r"عقد", r"عقود", r"تقرير", r"تقارير", r"لوائح", r"لائحة", r"قانون", r"قوانين",
        r"شروط", r"شرط", r"آلية", r"الية", r"اشرح", r"شرح", r"كيف يمكن", r"ما هي خطوات",
        r"تعليمات"
    )

    _DATA_PATTERNS = (
        # Aggregation / analytical terms
        r"\bsales\b", r"\brevenue\b", r"\bprofit\b", r"\bcost\b", r"\borders\b",
        r"\bcustomers\b", r"\bproducts\b", r"\busers\b", r"\btransactions\b",
        r"\bpayments\b", r"\bquantity\b", r"\bamount\b", r"\btotal\b", r"\baverage\b",
        r"\bcount\b", r"\bsum\b", r"\bmaximum\b", r"\bminimum\b", r"\btop\b",
        r"\bmost\b", r"\bleast\b",

        # Query-oriented English
        r"\bhow many\b", r"\bhow much\b", r"\bshow\b", r"\blist\b", r"\bfind\b",
        r"\bget\b", r"\bcalculate\b", r"\bcompare\b", r"\banalyze\b", r"\bbetween\b",
        r"\bby month\b", r"\bby year\b", r"\bby category\b",

        # Arabic
        r"كم", r"إجمالي", r"اجمالي", r"مجموع", r"متوسط", r"أعلى", r"اعلى",
        r"أكبر", r"اكبر", r"أقل", r"اقل", r"أدنى", r"ادنى", r"مبيعات", r"إيرادات",
        r"ايرادات", r"أرباح", r"ارباح", r"تكلفة", r"طلبات", r"عملاء", r"منتجات",
        r"مستخدمين", r"معاملات", r"مدفوعات", r"كم عدد", r"اعرض", r"أظهر", r"اظهر",
        r"اعطني", r"أعطني", r"احسب", r"قارن", r"حلل", r"تحليل", r"خلال",
        r"حسب الشهر", r"حسب السنة", r"حسب الفئة", r"طالب", r"طلاب", r"قسم", r"أقسام"
    )

    # ==========================================================
    # Public API
    # ==========================================================

    async def classify(
        self,
        request: QueryRequest,
    ) -> QueryContext:
        """
        تصنيف QueryRequest وإرجاع QueryContext محدثًا.
        """

        if request is None:
            raise ValueError("QueryRequest cannot be None.")

        question = self._normalize(request.question)

        if not question:
            raise ValueError("Query question cannot be empty.")

        logger.info(
            "[QueryClassifier] Classifying query | query_id=%s",
            request.query_id,
        )

        context = QueryContext(request=request)
        context.start_planning()

        intent = self._detect_intent(question)
        context.intent = intent
        context.metadata["query_intent"] = intent.value
        context.metadata["classifier"] = self.__class__.__name__

        logger.info(
            "[QueryClassifier] Classification completed | query_id=%s | intent=%s",
            request.query_id,
            intent.value,
        )

        return context

    # ==========================================================
    # Intent Detection
    # ==========================================================

    def _detect_intent(self, question: str) -> QueryIntent:
        """
        اكتشاف Intent باستخدام مجموعة من القواعد والأولويات.
        """

        # 1. Schema
        if self._matches_any(question, self._SCHEMA_PATTERNS):
            return QueryIntent.SCHEMA

        # 2. Database Information
        if self._matches_any(question, self._DATABASE_INFO_PATTERNS):
            if not self._matches_any(question, self._DATA_PATTERNS):
                return QueryIntent.DATABASE_INFO

        # 3. Document (RAG)
        if self._matches_any(question, self._DOCUMENT_PATTERNS):
            # إذا كان السؤال يحتوي على كلمات بيانات ومستندات معاً، نصنفه كبيانات مؤقتاً
            # ليقوم الـ Planner بدمج الأداتين معاً (Both).
            if not self._matches_any(question, self._DATA_PATTERNS):
                return QueryIntent.DOCUMENT

        # 4. Data (SQL)
        if self._matches_any(question, self._DATA_PATTERNS):
            return QueryIntent.DATA

        # 5. Unknown Fallback
        return QueryIntent.UNKNOWN

    # ==========================================================
    # Pattern Matching
    # ==========================================================

    @staticmethod
    def _matches_any(
        question: str,
        patterns: tuple[str, ...],
    ) -> bool:
        """
        التحقق من وجود أي Pattern داخل السؤال.
        """
        return any(
            re.search(pattern, question, flags=re.IGNORECASE)
            for pattern in patterns
        )

    # ==========================================================
    # Text Normalization
    # ==========================================================

    @staticmethod
    def _normalize(question: str) -> str:
        """
        تنظيف السؤال قبل التصنيف.
        """
        question = question.strip()
        question = re.sub(r"\s+", " ", question)
        return question

    # ==========================================================
    # Intent Helpers
    # ==========================================================

    @staticmethod
    def is_data_query(context: QueryContext) -> bool:
        return context.intent == QueryIntent.DATA

    @staticmethod
    def is_document_query(context: QueryContext) -> bool:
        """هل الاستعلام يطلب معلومات من المستندات؟"""
        return context.intent == QueryIntent.DOCUMENT

    @staticmethod
    def is_schema_query(context: QueryContext) -> bool:
        return context.intent == QueryIntent.SCHEMA

    @staticmethod
    def is_database_info_query(context: QueryContext) -> bool:
        return context.intent == QueryIntent.DATABASE_INFO

    @staticmethod
    def is_unknown_query(context: QueryContext) -> bool:
        return context.intent == QueryIntent.UNKNOWN