"""Reciprocal Rank Fusion (RRF) for merging dense vector and sparse BM25 search results."""

from typing import Dict, List
from src.modules.rag.domain.entities import Chunk, SearchResult


class RRFRanker:
    """Combines and re-ranks multi-source retrieval lists using Reciprocal Rank Fusion."""

    def __init__(self, rrf_k: int = 60):
        """
        Args:
            rrf_k: Constant factor (typically 60) that balances weight between top and lower ranked items.
        """
        self.rrf_k = rrf_k

    def fuse(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[SearchResult],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Merge dense vector results and sparse BM25 results using RRF scoring."""
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Chunk] = {}

        # 1. Score dense vector rankings
        for rank, res in enumerate(dense_results, start=1):
            cid = res.chunk.id
            chunk_map[cid] = res.chunk
            score = 1.0 / (self.rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score

        # 2. Score sparse BM25 rankings
        for rank, res in enumerate(sparse_results, start=1):
            cid = res.chunk.id
            chunk_map[cid] = res.chunk
            score = 1.0 / (self.rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score

        if not rrf_scores:
            return []

        # 3. Sort by combined RRF score descending
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        max_score = sorted_chunks[0][1] if sorted_chunks else 1.0

        fused_results: List[SearchResult] = []
        for cid, raw_score in sorted_chunks[:top_k]:
            normalized_score = round(float(raw_score / max_score), 4)
            fused_results.append(
                SearchResult(
                    chunk=chunk_map[cid],
                    score=normalized_score,
                    retrieval_method="hybrid_rrf",
                )
            )

        return fused_results
