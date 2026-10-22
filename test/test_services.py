"""End-to-End tests for IngestionService and RetrievalService."""

import tempfile
from pathlib import Path
import pytest

from src.modules.rag.application.dtos import IngestDocumentDTO, QueryInputDTO
from src.modules.rag.application.ingestion_service import IngestionService
from src.modules.rag.application.retrieval_service import RetrievalService
from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore


def test_end_to_end_rag_pipeline():
    # Use in-memory Chroma client for isolated test
    test_store = ChromaVectorStore(collection_name="test_e2e_rag", in_memory=True)

    # 1. Prepare sample text document
    sample_content = (
        "سياسة العمل المرن في الشركة:\n\n"
        "يحق لجميع الموظفين تقديم طلب للعمل عن بعد لمدة يومين أسبوعياً بعد موافقة المدير المباشر.\n\n"
        "يجب على الموظف تسجيل الحضور عبر التطبيق الرقمي في تمام الساعة التاسعة صباحاً."
    )

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(sample_content)
        temp_file = f.name

    try:
        # 2. Ingestion
        ingest_service = IngestionService(vector_store=test_store)
        ingest_dto = IngestDocumentDTO(
            file_path=temp_file,
            file_name="remote_work_policy.txt",
            tenant_id="org_alpha",
        )
        ingest_result = ingest_service.ingest_file(ingest_dto)

        assert ingest_result.status == "success"
        assert ingest_result.chunks_count >= 1

        # 3. Retrieval
        retrieval_service = RetrievalService(
            vector_store=test_store,
            bm25_searcher=ingest_service.bm25_searcher,
        )

        query_dto = QueryInputDTO(
            query="كم يوماً يسمح بالعمل عن بعد؟",
            top_k=2,
            tenant_id="org_alpha",
            enable_hybrid=True,
            enable_rerank=True,
        )
        response = retrieval_service.retrieve(query_dto)

        assert response.total_retrieved >= 1
        assert len(response.citations) >= 1
        assert "يومين أسبوعياً" in response.context
        assert response.citations[0].document_name == "remote_work_policy.txt"
        assert "[مصدر 1:" in response.context

    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_direct_text_ingestion_and_deletion():
    test_store = ChromaVectorStore(collection_name="test_text_ingest", in_memory=True)
    ingest_service = IngestionService(vector_store=test_store)

    text = "قواعد استخدام البريد الإلكتروني: يمنع فتح المرفقات المشبوهة أو مشاركة كلمات السر."
    res = ingest_service.ingest_text(
        text=text,
        document_name="email_security.txt",
        tenant_id="tenant_sec",
    )

    assert res.status == "success"
    assert res.chunks_count >= 1
    assert res.document_name == "email_security.txt"
    assert test_store.count() >= 1

    # Check listing
    docs = ingest_service.list_documents()
    assert len(docs) >= 1
    assert any(d["document_name"] == "email_security.txt" for d in docs)

    # Delete
    ingest_service.delete_document(res.document_id)
    assert test_store.count() == 0
    assert len(ingest_service.get_indexed_chunks()) == 0


if __name__ == "__main__":
    pytest.main([__file__])
