"""Unit tests for ChromaVectorStore."""

# pyrefly: ignore [missing-import]
import pytest
from src.modules.rag.domain.entities import Chunk
from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore


def test_vector_store_add_and_search():
    # Use in-memory Chroma client for testing
    store = ChromaVectorStore(collection_name="test_collection", in_memory=True)

    chunks = [
        Chunk(
            document_id="doc_hr",
            document_name="hr_policy.pdf",
            text="يحق للموظف إجازة سنوية مدفوعة الأجر مدتها 30 يوماً بعد إتمام سنة من العمل.",
            chunk_index=0,
            page_number=4,
            tenant_id="tenant_a",
        ),
        Chunk(
            document_id="doc_finance",
            document_name="finance_report.xlsx",
            text="سجلت الشركة صافي أرباح تشغيلية بلغت 15 مليون ريال خلال الربع الثالث.",
            chunk_index=0,
            page_number=1,
            tenant_id="tenant_a",
        ),
        Chunk(
            document_id="doc_it",
            document_name="it_policy.docx",
            text="يجب تغيير كلمة المرور الخاصة بحسابات الأنظمة كل 90 يوماً لضمان الأمان.",
            chunk_index=0,
            page_number=2,
            tenant_id="tenant_b",
        ),
    ]

    # Add chunks (embeddings are generated automatically)
    store.add_chunks(chunks)
    assert store.count() == 3

    # Semantic search for HR policy
    results = store.search_by_text(query_text="كم عدد أيام الإجازة السنوية للموظف؟", top_k=1)
    assert len(results) == 1
    best_match = results[0]
    assert best_match.chunk.document_id == "doc_hr"
    assert best_match.chunk.page_number == 4
    assert best_match.score > 0.3

    # Search with tenant filter
    filtered_results = store.search_by_text(
        query_text="كلمة المرور والأمان",
        top_k=2,
        filters={"tenant_id": "tenant_b"},
    )
    assert len(filtered_results) == 1
    assert filtered_results[0].chunk.document_id == "doc_it"

    # Delete document
    store.delete_document("doc_hr")
    assert store.count() == 2


if __name__ == "__main__":
    pytest.main([__file__])
