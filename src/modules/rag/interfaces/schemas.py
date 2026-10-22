"""Pydantic schemas for RAG REST API endpoints."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestFileResponse(BaseModel):
    document_id: str
    document_name: str
    chunks_count: int
    status: str
    message: str


class QueryRequestSchema(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="نص السؤال أو الاستعلام باللغة الطبيعية")
    top_k: int = Field(default=5, ge=1, le=50, description="عدد النتائج المسترجعة")
    tenant_id: Optional[str] = Field(default=None, description="معرف المؤسسة أو المستخدم")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="فلاتر مخصصة")
    enable_hybrid: bool = Field(default=True, description="تفعيل البحث الهجين (دلالي + مفتاحي)")
    enable_rerank: bool = Field(default=True, description="تفعيل إعادة الترتيب")


class CitationSchema(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    page: Optional[int] = None
    score: float
    snippet: str


class QueryResponseSchema(BaseModel):
    query: str
    context: str = Field(..., description="السياق المجمع والمنسق مع أرقام المصادر")
    citations: List[CitationSchema] = Field(default_factory=list, description="بيانات التوثيق التفصيلية")
    total_retrieved: int


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000_000, description="المحتوى النصي المراد فهرسته")
    document_name: str = Field(default="direct_note.txt", min_length=1, max_length=255, description="اسم الوثيقة أو الملاحظة")
    tenant_id: Optional[str] = Field(default=None, description="معرف المؤسسة أو المستخدم")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="بيانات وصفية إضافية")


class DocumentItemSchema(BaseModel):
    document_id: str
    document_name: str
    tenant_id: Optional[str] = None
    chunks_count: int = 0
    created_at: Optional[str] = None


class DocumentListResponse(BaseModel):
    total_documents: int
    documents: List[DocumentItemSchema]


class ChunkItemSchema(BaseModel):
    id: str
    document_id: str
    document_name: str
    text: str
    chunk_index: int
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
