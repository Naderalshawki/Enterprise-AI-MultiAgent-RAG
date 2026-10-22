from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional
from src.modules.schema_engine.domain.entities import DatabaseSchemaEntity
from src.modules.schema_engine.domain.interfaces import ISchemaCache

logger = logging.getLogger(__name__)

class SchemaCache(ISchemaCache):
    """إدارة التخزين المؤقت (In-Memory Cache) مع دعم التحديث التلقائي (TTL)"""

    def __init__(self, ttl_seconds: int = 3600):
        self._cached_schema: Optional[DatabaseSchemaEntity] = None
        self._expiry_time: Optional[datetime] = None
        self.ttl_seconds = ttl_seconds

    def get(self) -> Optional[DatabaseSchemaEntity]:
        """استرجاع الاسكيما من الكاش إذا كانت صالحة ولم تنتهِ مدتها"""
        if self._cached_schema and self._expiry_time:
            if datetime.now() < self._expiry_time:
                logger.info("⚡ [Schema Cache] Hit: Schema retrieved from memory cache.")
                return self._cached_schema
            else:
                logger.info("⏳ [Schema Cache] Expired: Schema TTL reached. Clearing cache.")
                self.clear()
        else:
            logger.info("❄️ [Schema Cache] Miss: No schema found in cache.")
        return None

    def set(self, schema: DatabaseSchemaEntity) -> None:
        """تخزين الاسكيما وتحديد وقت الانتهاء (TTL)"""
        self._cached_schema = schema
        self._expiry_time = datetime.now() + timedelta(seconds=self.ttl_seconds)
        logger.info(f"💾 [Schema Cache] Schema stored. Expires in {self.ttl_seconds} seconds.")

    def clear(self) -> None:
        """مسح الكاش قسراً لإعادة التحديث"""
        self._cached_schema = None
        self._expiry_time = None
        logger.info("🧹 [Schema Cache] Cache cleared.")