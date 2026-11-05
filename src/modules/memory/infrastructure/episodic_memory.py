from __future__ import annotations

import json
import logging
import os
import hashlib
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    ذاكرة التجارب (Episodic Memory).
    
    تحفظ دروساً من محاولات النجاح والفشل، ليستخدمها Planner
    في المرات القادمة عندما يواجه سؤالاً مشابهاً.
    
    التخزين: ملف JSON بسيط (يمكن ترقيته لـ SQL/Chroma لاحقاً).
    """

    def __init__(self, storage_path: str | None = None):
        self._path = storage_path or os.getenv(
            "EPISODIC_MEMORY_PATH", 
            "./data/episodic_memory.json"
        )
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        if not os.path.exists(self._path):
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump([], f)

    @staticmethod
    def _signature(question: str) -> str:
        """بصمة السؤال (hash) للبحث السريع."""
        normalized = " ".join(question.strip().lower().split())
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()[:12]

    async def save_lesson(
        self,
        question: str,
        strategy: str,
        outcome: str,  # "success" | "failure"
        reason: str = "",
        correction_hint: str = "",
    ) -> None:
        """
        حفظ درس جديد.
        
        Args:
            question: السؤال الأصلي.
            strategy: الاستراتيجية المستخدمة (مثلاً "database_only", "fallback_document").
            outcome: "success" أو "failure".
            reason: سبب الفشل (لو موجود).
            correction_hint: نصيحة للتصحيح.
        """
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                lessons = json.load(f)

            lesson = {
                "signature": self._signature(question),
                "question": question,
                "strategy": strategy,
                "outcome": outcome,
                "reason": reason,
                "correction_hint": correction_hint,
                "timestamp": datetime.now().isoformat(),
            }

            # لا تكرر نفس الدرس لو محفوظ بالفعل
            if not any(
                l["signature"] == lesson["signature"] 
                and l["strategy"] == lesson["strategy"]
                for l in lessons
            ):
                lessons.append(lesson)
                # احتفظ فقط بآخر 1000 درس لتجنب نمو الملف
                lessons = lessons[-1000:]
                with open(self._path, "w", encoding="utf-8") as f:
                    json.dump(lessons, f, ensure_ascii=False, indent=2)
                logger.info(f"[EpisodicMemory] Saved lesson: {strategy} → {outcome}")

        except Exception as exc:
            logger.warning(f"[EpisodicMemory] Failed to save lesson: {exc}")

    async def get_lessons(self, question: str) -> list[dict[str, Any]]:
        """استرجاع الدروس المتعلقة بسؤال مشابه."""
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                lessons = json.load(f)

            signature = self._signature(question)
            return [l for l in lessons if l["signature"] == signature]

        except Exception as exc:
            logger.warning(f"[EpisodicMemory] Failed to get lessons: {exc}")
            return []

    async def get_warnings_for_planner(self, question: str) -> str:
        """
        ترجمة الدروس إلى نصائح نصية للـ Planner.
        """
        lessons = await self.get_lessons(question)
        if not lessons:
            return ""

        warnings = []
        for lesson in lessons:
            if lesson["outcome"] == "failure":
                warnings.append(
                    f"- استراتيجية '{lesson['strategy']}' فشلت سابقاً: "
                    f"{lesson['reason']}. "
                    f"النصيحة: {lesson['correction_hint']}"
                )

        if not warnings:
            return ""

        return (
            "⚠️ دروس من محاولات سابقة على أسئلة مشابهة:\n" +
            "\n".join(warnings)
        )