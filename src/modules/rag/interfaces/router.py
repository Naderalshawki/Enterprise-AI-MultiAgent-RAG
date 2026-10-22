"""FastAPI Router exposing RAG endpoints."""

from pathlib import Path
import uuid
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from src.modules.rag.application.dtos import IngestDocumentDTO, QueryInputDTO
from src.modules.rag.application.ingestion_service import IngestionService
from src.modules.rag.application.retrieval_service import RetrievalService
from src.modules.rag.config.settings import rag_settings
from src.modules.rag.interfaces.schemas import (
    ChunkItemSchema,
    CitationSchema,
    DocumentItemSchema,
    DocumentListResponse,
    IngestFileResponse,
    IngestTextRequest,
    QueryRequestSchema,
    QueryResponseSchema,
)
from src.modules.rag.interfaces.security import (
    TenantContext,
    assert_requested_tenant,
    can_manage_documents,
    get_tenant_context,
)

def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    """Require a configured API key; empty configuration keeps local dev easy."""
    configured = rag_settings.api_key.strip()
    if configured and (not x_api_key or not secrets.compare_digest(x_api_key, configured)):
        raise HTTPException(status_code=401, detail="مفتاح API غير صالح أو مفقود")


rag_router = APIRouter(
    prefix="/rag",
    tags=["RAG & Document Intelligence"],
    dependencies=[Depends(require_api_key)],
)
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "csv", "txt", "md", "markdown", "log", "json"}

# Global shared service instances
_ingestion_service = IngestionService()
_retrieval_service = RetrievalService(
    vector_store=_ingestion_service.vector_store,
    bm25_searcher=_ingestion_service.bm25_searcher,
)


@rag_router.post("/upload", response_model=IngestFileResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Form(default=None),
    context: TenantContext = Depends(get_tenant_context),
):
    """Upload and ingest a document (PDF, Word, Excel, CSV, TXT)."""
    try:
        assert_requested_tenant(tenant_id, context)
        if not can_manage_documents(context):
            raise HTTPException(status_code=403, detail="لا تملك صلاحية إضافة مستندات")
        effective_tenant = context.tenant_id if rag_settings.require_trusted_context else (tenant_id or context.tenant_id)
        original_name = Path(file.filename or "upload.bin").name
        extension = Path(original_name).suffix.lower().lstrip(".")
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=415, detail="صيغة الملف غير مدعومة")
        # Ensure uploads directory exists; use a random server-side filename.
        rag_settings.upload_dir.mkdir(parents=True, exist_ok=True)
        save_path = rag_settings.upload_dir / f"{uuid.uuid4().hex}.{extension}"

        # Save uploaded bytes to disk
        with open(save_path, "wb") as buffer:
            total_bytes = 0
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > rag_settings.max_upload_bytes:
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="حجم الملف يتجاوز الحد المسموح")
                buffer.write(chunk)

        # Ingest document
        dto = IngestDocumentDTO(
            file_path=str(save_path),
            file_name=original_name,
            tenant_id=effective_tenant,
        )
        result = _ingestion_service.ingest_file(dto)

        return IngestFileResponse(
            document_id=result.document_id,
            document_name=result.document_name,
            chunks_count=result.chunks_count,
            status=result.status,
            message=result.message,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل في استيعاب الملف: {str(e)}")


@rag_router.post("/query", response_model=QueryResponseSchema)
async def query_documents(request: QueryRequestSchema, context: TenantContext = Depends(get_tenant_context)):
    """Query the indexed knowledge base using Hybrid Search and Reranking."""
    try:
        assert_requested_tenant(request.tenant_id, context)
        effective_tenant = context.tenant_id if rag_settings.require_trusted_context else (request.tenant_id or context.tenant_id)
        dto = QueryInputDTO(
            query=request.query,
            top_k=request.top_k,
            tenant_id=effective_tenant,
            filters=request.filters,
            enable_hybrid=request.enable_hybrid,
            enable_rerank=request.enable_rerank,
        )
        output = _retrieval_service.retrieve(dto)

        citations = [
            CitationSchema(
                document_id=c.document_id,
                document_name=c.document_name,
                chunk_id=c.chunk_id,
                page=c.page,
                score=c.score,
                snippet=c.snippet,
            )
            for c in output.citations
        ]

        return QueryResponseSchema(
            query=output.query,
            context=output.context,
            citations=citations,
            total_retrieved=output.total_retrieved,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل في استرجاع المعرفة: {str(e)}")


@rag_router.post("/ingest-text", response_model=IngestFileResponse)
async def ingest_direct_text(request: IngestTextRequest, context: TenantContext = Depends(get_tenant_context)):
    """Directly ingest and index text content without uploading a physical file."""
    try:
        assert_requested_tenant(request.tenant_id, context)
        if not can_manage_documents(context):
            raise HTTPException(status_code=403, detail="لا تملك صلاحية إضافة مستندات")
        effective_tenant = context.tenant_id if rag_settings.require_trusted_context else (request.tenant_id or context.tenant_id)
        result = _ingestion_service.ingest_text(
            text=request.text,
            document_name=request.document_name,
            tenant_id=effective_tenant,
            metadata=request.metadata,
        )
        return IngestFileResponse(
            document_id=result.document_id,
            document_name=result.document_name,
            chunks_count=result.chunks_count,
            status=result.status,
            message=result.message,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل في استيعاب النص: {str(e)}")


@rag_router.get("/documents", response_model=DocumentListResponse)
async def list_documents(tenant_id: Optional[str] = None, context: TenantContext = Depends(get_tenant_context)):
    """List all indexed documents and their chunk counts."""
    try:
        assert_requested_tenant(tenant_id, context)
        effective_tenant = context.tenant_id if rag_settings.require_trusted_context else (tenant_id or context.tenant_id)
        docs = _ingestion_service.list_documents(tenant_id=effective_tenant)
        items = [
            DocumentItemSchema(
                document_id=d.get("document_id", ""),
                document_name=d.get("document_name", ""),
                tenant_id=d.get("tenant_id"),
                chunks_count=d.get("chunks_count", 0),
                created_at=d.get("created_at"),
            )
            for d in docs
        ]
        return DocumentListResponse(total_documents=len(items), documents=items)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل في جلب قائمة المستندات: {str(e)}")


@rag_router.get("/document/{document_id}/chunks", response_model=list[ChunkItemSchema])
async def get_document_chunks(document_id: str, context: TenantContext = Depends(get_tenant_context)):
    """Retrieve all chunks belonging to a document."""
    try:
        scope = context.tenant_id if rag_settings.require_trusted_context else None
        all_chunks = _ingestion_service.get_document_chunks(document_id, tenant_id=scope)
        if not all_chunks and hasattr(_ingestion_service.vector_store, "get_all_chunks"):
            all_chunks = _ingestion_service.vector_store.get_all_chunks(tenant_id=scope)

        matched = [
            ChunkItemSchema(
                id=c.id,
                document_id=c.document_id,
                document_name=c.document_name,
                text=c.text,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                metadata=c.metadata,
            )
            for c in all_chunks
            if c.document_id == document_id or c.document_name == document_id
        ]
        if rag_settings.require_trusted_context and not matched:
            raise HTTPException(status_code=404, detail="المستند غير موجود ضمن نطاق المؤسسة")
        return matched
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل في جلب مقاطع المستند: {str(e)}")


@rag_router.delete("/document/{document_id}")
async def delete_document(document_id: str, context: TenantContext = Depends(get_tenant_context)):
    """Delete a document's chunks from both vector store and BM25 index."""
    try:
        if not can_manage_documents(context):
            raise HTTPException(status_code=403, detail="لا تملك صلاحية حذف المستندات")
        scope = context.tenant_id if rag_settings.require_trusted_context else None
        if not _ingestion_service.delete_document(document_id, tenant_id=scope):
            raise HTTPException(status_code=404, detail="المستند غير موجود ضمن نطاق المؤسسة")
        return {"status": "success", "message": f"تم حذف المستند {document_id} بنجاح من كافة الفهارس."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل في حذف المستند: {str(e)}")


@rag_router.get("/health")
async def health_check():
    """Health check for RAG service."""
    chunk_count = 0
    if hasattr(_ingestion_service.vector_store, "count"):
        chunk_count = _ingestion_service.vector_store.count()
    return {
        "status": "healthy",
        "module": "RAG & Document Intelligence",
        "total_indexed_chunks": chunk_count,
    }
