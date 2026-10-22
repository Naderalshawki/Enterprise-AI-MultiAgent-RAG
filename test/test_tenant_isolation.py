"""Regression tests for tenant isolation in hybrid retrieval."""
from src.modules.rag.application.dtos import QueryInputDTO
from src.modules.rag.application.ingestion_service import IngestionService
from src.modules.rag.application.retrieval_service import RetrievalService
from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore


def test_hybrid_search_does_not_leak_other_tenants():
    store = ChromaVectorStore(collection_name="tenant_isolation", in_memory=True)
    ingestion = IngestionService(vector_store=store)
    for index in range(8):
        ingestion.ingest_text(
            f"وثيقة عامة رقم {index} عن الموارد البشرية والعمليات.",
            f"public-{index}.txt",
            "other",
        )
    ingestion.ingest_text(
        "رمز سري خاص بالمؤسسة ب هو العنقاء الزرقاء.",
        "tenant-b.txt",
        "tenant_b",
    )
    ingestion.ingest_text(
        "معلومات المؤسسة أ عن ساعات العمل والإجازات.",
        "tenant-a.txt",
        "tenant_a",
    )

    service = RetrievalService(vector_store=store, bm25_searcher=ingestion.bm25_searcher)
    result = service.retrieve(QueryInputDTO(
        query="ما هو رمز العنقاء الزرقاء؟",
        tenant_id="tenant_a",
        top_k=10,
        enable_hybrid=True,
        enable_rerank=False,
    ))

    assert all(c.document_name != "tenant-b.txt" for c in result.citations)
    assert all(c.document_name.startswith("tenant-a") for c in result.citations)
