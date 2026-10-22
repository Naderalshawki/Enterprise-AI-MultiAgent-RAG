"""Unit tests for BM25Searcher, RRFRanker, and FlashRankReranker."""

# pyrefly: ignore [missing-import]
import pytest
from src.modules.rag.domain.entities import Chunk, SearchResult
from src.modules.rag.infrastructure.hybrid_search.bm25_searcher import BM25Searcher
from src.modules.rag.infrastructure.hybrid_search.rrf_ranker import RRFRanker
from src.modules.rag.infrastructure.reranker.flashrank_reranker import FlashRankReranker


def test_bm25_arabic_search():
    chunks = [
        Chunk(id="1", document_name="doc1.txt", text="المبيعات السنوية لشركة الأمل بلغت 5 ملايين ريال."),
        Chunk(id="2", document_name="doc2.txt", text="سياسة الموارد البشرية تحدد الإجازات السنوية بـ 30 يوماً."),
        Chunk(id="3", document_name="doc3.txt", text="أمن المعلومات يتطلب استخدام كلمات مرور معقدة."),
    ]

    searcher = BM25Searcher()
    searcher.fit(chunks)

    # Search with variations in Arabic letters (إجازات / الاجازات)
    results = searcher.search(query="الاجازات السنويه للموظفين", top_k=1)
    assert len(results) == 1
    assert results[0].chunk.id == "2"
    assert results[0].retrieval_method == "sparse_bm25"


def test_rrf_ranker_fusion():
    chunk_a = Chunk(id="a", text="نص أ")
    chunk_b = Chunk(id="b", text="نص ب")
    chunk_c = Chunk(id="c", text="نص ج")

    dense_results = [
        SearchResult(chunk=chunk_a, score=0.9, retrieval_method="dense"),
        SearchResult(chunk=chunk_b, score=0.7, retrieval_method="dense"),
    ]

    sparse_results = [
        SearchResult(chunk=chunk_b, score=0.95, retrieval_method="bm25"),
        SearchResult(chunk=chunk_c, score=0.8, retrieval_method="bm25"),
    ]

    ranker = RRFRanker(rrf_k=60)
    fused = ranker.fuse(dense_results, sparse_results, top_k=3)

    assert len(fused) == 3
    # Chunk B appeared in both lists, so its RRF score should be highest!
    assert fused[0].chunk.id == "b"
    assert fused[0].retrieval_method == "hybrid_rrf"


def test_flashrank_reranker_fallback():
    chunk_1 = Chunk(id="1", text="سياسة العمل عن بعد")
    chunk_2 = Chunk(id="2", text="إجراءات الحضور والانصراف")

    candidates = [
        SearchResult(chunk=chunk_1, score=0.5),
        SearchResult(chunk=chunk_2, score=0.9),
    ]

    reranker = FlashRankReranker()
    reranked = reranker.rerank(query="ما هي ساعات الحضور؟", candidates=candidates, top_k=2)

    assert len(reranked) == 2


if __name__ == "__main__":
    pytest.main([__file__])
