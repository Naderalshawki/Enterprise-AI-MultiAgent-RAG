from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from src.modules.schema_engine.domain.entities import DatabaseSchemaEntity, TableEntity

class ISchemaLoader(ABC):
    """عقد قراءة الاسكيما من مصدر البيانات (Postgres, MySQL, etc.)"""
    @abstractmethod
    async def load_schema(self) -> DatabaseSchemaEntity:
        pass

class ISchemaCache(ABC):
    """عقد التخزين المؤقت للاسيما"""
    @abstractmethod
    def get(self) -> Optional[DatabaseSchemaEntity]:
        pass

    @abstractmethod
    def set(self, schema: DatabaseSchemaEntity) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

class ISchemaSearcher(ABC):
    """عقد البحث والفلترة الذكية للجداول المرتبطة بالسؤال (Token Optimization)"""
    @abstractmethod
    def search_relevant_tables(self, question: str, schema: DatabaseSchemaEntity, top_k: int = 5) -> List[TableEntity]:
        pass

class ISchemaValidator(ABC):
    """عقد التحقق من صحة الاستعلامات بناءً على الاسكيما"""
    @abstractmethod
    def validate_sql_identifiers(self, sql_query: str, schema: DatabaseSchemaEntity) -> bool:
        pass