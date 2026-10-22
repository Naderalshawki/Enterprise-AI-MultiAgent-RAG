"""Small deterministic quality gate; replace dataset with project-specific cases."""
import json
from pathlib import Path
from src.modules.rag.application.dtos import QueryInputDTO
from src.modules.rag.application.ingestion_service import IngestionService
from src.modules.rag.application.retrieval_service import RetrievalService
from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore
from tests.evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


CASES = [
    ("org_a", "remote_policy", "سياسة العمل عن بعد تسمح بيومين أسبوعياً بعد موافقة المدير."),
    ("org_a", "leave_policy", "الإجازة السنوية للموظف ثلاثون يوماً حسب السياسة."),
    ("org_b", "security_policy", "يجب تغيير كلمة المرور كل تسعين يوماً وعدم مشاركتها."),
]


def test_arabic_retrieval_quality_smoke():
    store = ChromaVectorStore(collection_name="quality_eval", in_memory=True)
    ingestion = IngestionService(vector_store=store)
    for tenant, name, text in CASES:
        result = ingestion.ingest_text(text, name, tenant)
        assert result.status == "success"
    service = RetrievalService(vector_store=store, bm25_searcher=ingestion.bm25_searcher)
    queries = [
        ("org_a", "remote_policy", "كم يوماً يسمح بالعمل عن بعد؟"),
        ("org_a", "leave_policy", "ما مدة الإجازة السنوية؟"),
        ("org_b", "security_policy", "ما قواعد كلمة المرور؟"),
    ]
    scores = []
    for tenant, relevant, query in queries:
        output = service.retrieve(QueryInputDTO(query=query, tenant_id=tenant, top_k=3, enable_hybrid=True, enable_rerank=False))
        ids = [citation.document_name for citation in output.citations]
        relevant_set = {relevant}
        scores.append((recall_at_k(ids, relevant_set, 3), precision_at_k(ids, relevant_set, 3), reciprocal_rank(ids, relevant_set), ndcg_at_k(ids, relevant_set, 3)))
        assert all(name in {case[1] for case in CASES if case[0] == tenant} for name in ids)
    assert sum(score[0] for score in scores) / len(scores) >= 0.66
