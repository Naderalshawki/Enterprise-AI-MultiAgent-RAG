from __future__ import annotations

import difflib
import logging
import re
import unicodedata
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from src.modules.schema_engine.domain.entities import (
    ColumnEntity,
    DatabaseSchemaEntity,
    TableEntity,
)
from src.modules.schema_engine.domain.interfaces import ISchemaSearcher

logger = logging.getLogger(__name__)


class KeywordSchemaRetriever(ISchemaSearcher):
    """Rank schema tables against a user's question without changing the public API.

    The retriever uses deterministic lexical matching in English and Arabic:
    exact phrases, normalized tokens, snake/camel-case identifiers, fuzzy token
    similarity, descriptions, key columns, and declared relationships. It only
    ranks metadata already present in ``DatabaseSchemaEntity``; it does not
    inspect business rows or guess column values.
    """

    _STOP_WORDS: Set[str] = {
        # English function words / generic BI verbs
        "a", "an", "the", "of", "for", "to", "from", "in", "on", "by",
        "with", "and", "or", "is", "are", "was", "were", "be", "been",
        "what", "which", "who", "whom", "show", "give", "tell", "find",
        "get", "list", "display", "please", "me", "my", "all", "each",
        "total", "number", "count", "many", "much", "how", "does", "do",
        "can", "could", "would", "should", "about", "data", "database",
        "table", "tables", "record", "records", "row", "rows",
        # Arabic function words / generic BI verbs
        "من", "في", "على", "عن", "الى", "إلى", "مع", "و", "او", "أو",
        "ما", "ماذا", "كم", "كيف", "هل", "هو", "هي", "هم", "هن",
        "هذا", "هذه", "ذلك", "تلك", "الذي", "التي", "الذين", "اللاتي",
        "لي", "لنا", "لك", "لكم", "كل", "بعض", "عدد", "اجمالي", "إجمالي",
        "اعرض", "أعرض", "اظهر", "أظهر", "اريد", "أريد", "اعطني", "أعطني",
        "بيانات", "البيانات", "جدول", "جداول", "سجل", "سجلات", "قاعدة", "قاعده",
    }

    _BILINGUAL_ALIASES: Dict[str, Set[str]] = {
        "طالب": {"student", "students"}, "طلاب": {"student", "students"},
        "الطالب": {"student", "students"}, "الطلاب": {"student", "students"},
        "قسم": {"department", "departments"}, "الاقسام": {"department", "departments"},
        "التخصص": {"department", "major", "specialization"}, "تخصص": {"department", "major", "specialization"},
        "ماده": {"course", "courses", "subject", "subjects"}, "مواد": {"course", "courses", "subject", "subjects"},
        "مقرر": {"course", "courses", "subject", "subjects"}, "المقررات": {"course", "courses", "subject", "subjects"},
        "درجه": {"grade", "grades", "score", "scores"}, "درجات": {"grade", "grades", "score", "scores"},
        "موظف": {"employee", "employees", "staff"}, "موظفين": {"employee", "employees", "staff"},
        "عميل": {"customer", "customers", "client", "clients"}, "عملاء": {"customer", "customers", "client", "clients"},
        "مريض": {"patient", "patients"}, "مرضى": {"patient", "patients"},
        "مستشفى": {"hospital", "hospitals"}, "مستشفي": {"hospital", "hospitals"},
        "فاتوره": {"invoice", "invoices", "bill", "bills"}, "فواتير": {"invoice", "invoices", "bill", "bills"},
        "مبيعات": {"sale", "sales"}, "بيع": {"sale", "sales"},
        "مشتريات": {"purchase", "purchases"}, "منتج": {"product", "products"}, "منتجات": {"product", "products"},
        "طلب": {"order", "orders", "request", "requests"}, "طلبات": {"order", "orders", "request", "requests"},
        "مدينه": {"city", "cities"}, "مدن": {"city", "cities"}, "دوله": {"country", "countries"},
        "تاريخ": {"date", "time", "created", "updated"}, "المبلغ": {"amount", "total", "price"},
        "اسم": {"name", "title"}, "الاسم": {"name", "title"}, "رقم": {"number", "id", "code"},
    }

    _ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
    _NON_WORD = re.compile(r"[^\w]+", flags=re.UNICODE)
    _CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

    def search_relevant_tables(
        self,
        question: str,
        schema: DatabaseSchemaEntity,
        top_k: int = 5,
    ) -> List[TableEntity]:
        """Return up to ``top_k`` tables ranked by relevance to ``question``.

        The method intentionally retains the existing ISchemaSearcher signature
        so ``SchemaService`` and ``bootstrap.py`` need no changes.
        """
        if not isinstance(schema, DatabaseSchemaEntity) or not schema.tables and not schema.views:
            logger.warning("[Schema Retriever] Schema is empty; no tables can be selected.")
            return []
        if not isinstance(question, str) or not question.strip():
            logger.warning("[Schema Retriever] Empty question; returning no schema context.")
            return []
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            return []

        question_norm = self._normalize(question)
        question_tokens = self._meaningful_tokens(question)
        if not question_tokens:
            # A question can be meaningful even if it consists of stop words.
            question_tokens = self._tokens(question)

        candidates: List[Tuple[float, str, TableEntity]] = []
        objects: List[Tuple[str, TableEntity, str]] = []
        objects.extend((name, table, "table") for name, table in schema.tables.items())
        objects.extend((name, view, "view") for name, view in schema.views.items())

        for registry_name, entity, object_type in objects:
            score, evidence = self._score_table(
                question_norm=question_norm,
                question_tokens=question_tokens,
                registry_name=registry_name,
                table=entity,
            )
            if score > 0:
                # Stable tie-breaking avoids output changing between runs.
                candidates.append((score, f"{object_type}:{registry_name}", entity))
                logger.debug(
                    "[Schema Retriever] Candidate %s scored %.2f (%s).",
                    registry_name,
                    score,
                    ", ".join(evidence) if evidence else "lexical match",
                )

        candidates.sort(key=lambda item: (-item[0], item[1].casefold()))
        if candidates:
            selected = [item[2] for item in candidates[:top_k]]
            logger.info(
                "[Schema Retriever] Selected %d/%d schema objects by relevance.",
                len(selected),
                len(objects),
            )
            return selected

        # Preserve the old fallback behavior, but make it deterministic and
        # explicit. This is a fallback only; it is not evidence of relevance.
        fallback = sorted(objects, key=lambda item: (item[0].casefold(), item[2]))[:top_k]
        logger.warning(
            "[Schema Retriever] No lexical match found for question; using %d deterministic fallback objects. "
            "Consider adding table/column descriptions or a semantic retriever.",
            len(fallback),
        )
        return [item[1] for item in fallback]

    def _score_table(
        self,
        *,
        question_norm: str,
        question_tokens: Set[str],
        registry_name: str,
        table: TableEntity,
    ) -> Tuple[float, List[str]]:
        score = 0.0
        evidence: List[str] = []

        table_names = {registry_name, table.name}
        for name in table_names:
            normalized_name = self._normalize(name)
            name_tokens = self._meaningful_tokens(name)
            if normalized_name and normalized_name in question_norm:
                score += 12.0
                evidence.append(f"exact table phrase: {name}")
            score += self._token_overlap_score(question_tokens, name_tokens, exact_weight=7.0, fuzzy_weight=3.0)

        # Column names are often the strongest clue in natural-language questions.
        for column_name, column in table.columns.items():
            normalized_column = self._normalize(column_name)
            column_tokens = self._meaningful_tokens(column_name)
            if normalized_column and normalized_column in question_norm:
                score += 5.0
                evidence.append(f"exact column phrase: {column_name}")
            score += self._token_overlap_score(question_tokens, column_tokens, exact_weight=3.0, fuzzy_weight=1.25)

            if column.description:
                score += 0.8 * self._description_overlap(question_tokens, column.description)
            # PK/FK fields help when the question refers to identifiers or joins.
            key_terms = set()
            if column.is_primary_key:
                key_terms.update({"id", "identifier", "key", "معرف", "رقم", "هوية"})
            if column.is_foreign_key:
                key_terms.update({"id", "identifier", "reference", "foreign", "key", "معرف", "رقم", "مرتبط"})
            if key_terms & question_tokens:
                score += 0.6

        if table.description:
            description_score = self._description_overlap(question_tokens, table.description)
            score += min(description_score * 1.6, 8.0)
            if description_score:
                evidence.append("table description overlap")

        # Existing FK metadata can improve selection when the question mentions
        # the referenced table/column. No relationships are invented here.
        for fk in table.foreign_keys:
            if not isinstance(fk, dict):
                continue
            ref_parts = [
                str(fk.get("referenced_table", "")),
                *(str(value) for value in fk.get("referenced_columns", []) if value is not None),
            ]
            ref_tokens = set().union(*(self._meaningful_tokens(part) for part in ref_parts)) if ref_parts else set()
            score += 0.5 * self._token_overlap_score(question_tokens, ref_tokens, exact_weight=1.0, fuzzy_weight=0.5)

        return score, evidence

    @classmethod
    def _normalize(cls, text: str) -> str:
        value = unicodedata.normalize("NFKC", str(text)).casefold()
        value = cls._ARABIC_DIACRITICS.sub("", value)
        # Normalize common Arabic letter variants for better lexical matching.
        value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ؤ": "و", "ئ": "ي", "ة": "ه"}))
        value = cls._CAMEL_BOUNDARY.sub(" ", value)
        value = value.replace("_", " ").replace("-", " ")
        return " ".join(cls._NON_WORD.sub(" ", value).split())

    @classmethod
    def _tokens(cls, text: str) -> Set[str]:
        return {token for token in cls._normalize(text).split() if token}

    @classmethod
    def _meaningful_tokens(cls, text: str) -> Set[str]:
        tokens = {
            token for token in cls._tokens(text)
            if token not in cls._STOP_WORDS and (len(token) > 1 or token.isdigit())
        }
        # Expand common Arabic business terms to English schema vocabulary.
        # This improves table/column selection, but does not translate database
        # values or replace semantic matching for domain-specific terminology.
        for token in tuple(tokens):
            tokens.update(cls._BILINGUAL_ALIASES.get(token, set()))
        return tokens

    @classmethod
    def _token_overlap_score(
        cls,
        question_tokens: Set[str],
        target_tokens: Set[str],
        *,
        exact_weight: float,
        fuzzy_weight: float,
    ) -> float:
        if not question_tokens or not target_tokens:
            return 0.0
        score = 0.0
        for target in target_tokens:
            if target in question_tokens:
                score += exact_weight
                continue
            # Fuzzy matching is deliberately conservative to avoid ranking
            # unrelated short identifiers as matches.
            if len(target) < 4:
                continue
            best = max(
                (difflib.SequenceMatcher(None, target, question).ratio() for question in question_tokens if len(question) >= 4),
                default=0.0,
            )
            if best >= 0.84:
                score += fuzzy_weight * best
        return score

    @classmethod
    def _description_overlap(cls, question_tokens: Set[str], description: str) -> float:
        description_tokens = cls._meaningful_tokens(description)
        if not question_tokens or not description_tokens:
            return 0.0
        exact = question_tokens & description_tokens
        fuzzy = 0.0
        remaining_question = question_tokens - exact
        remaining_description = description_tokens - exact
        for target in remaining_description:
            if len(target) < 4:
                continue
            best = max(
                (difflib.SequenceMatcher(None, target, token).ratio() for token in remaining_question if len(token) >= 4),
                default=0.0,
            )
            if best >= 0.84:
                fuzzy += best
        return float(len(exact)) + fuzzy
