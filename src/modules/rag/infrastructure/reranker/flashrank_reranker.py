"""Multilingual BGE reranker with FlashRank fallback."""

import os
from typing import List
from src.modules.rag.domain.entities import SearchResult
from src.modules.rag.domain.interfaces import IReranker


class FlashRankReranker(IReranker):
    """Reranker that prefers BGE's multilingual cross-encoder for Arabic."""

    def __init__(self, model_name: str = ""):
        self.model_name = model_name or os.getenv("RAG_RERANK_MODEL", "ms-marco-TinyBERT-L-2-v2")
        self._ranker = None
        self._backend = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        try:
            if self.model_name.startswith("BAAI/"):
                from sentence_transformers import CrossEncoder
                self._ranker = CrossEncoder(self.model_name, max_length=512)
                self._backend = "cross_encoder"
            else:
                from flashrank import Ranker
                self._ranker = Ranker(model_name=self.model_name)
                self._backend = "flashrank"
            self._initialized = True
        except Exception:
            # Fallback gracefully if model fails to load locally
            self._ranker = None
            self._initialized = True

    def rerank(
        self,
        query: str,
        candidates: List[SearchResult],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Rerank candidate search results using FlashRank."""
        if not candidates or not query.strip():
            return candidates[:top_k]

        self._ensure_initialized()

        # Prefer the multilingual BGE cross-encoder for Arabic and mixed text.
        if self._ranker:
            try:
                if self._backend == "cross_encoder":
                    pairs = [[query, res.chunk.text] for res in candidates]
                    scores = self._ranker.predict(pairs)
                    ranked = sorted(
                        zip(candidates, scores),
                        key=lambda item: float(item[1]),
                        reverse=True,
                    )[:top_k]
                    return [
                        SearchResult(
                            chunk=res.chunk,
                            score=round(float(score), 4),
                            retrieval_method="reranked_bge",
                        )
                        for res, score in ranked
                    ]
                from flashrank import RerankRequest

                passages = [
                    {"id": res.chunk.id, "text": res.chunk.text, "index": i}
                    for i, res in enumerate(candidates)
                ]

                rerank_request = RerankRequest(query=query, passages=passages)
                ranked_passages = self._ranker.rerank(rerank_request)

                reranked_results: List[SearchResult] = []
                for p in ranked_passages[:top_k]:
                    original_res = candidates[p["index"]]
                    reranked_results.append(
                        SearchResult(
                            chunk=original_res.chunk,
                            score=round(float(p.get("score", original_res.score)), 4),
                            retrieval_method="reranked_flashrank",
                        )
                    )
                return reranked_results
            except Exception:
                # Fallback to score-sorted candidates
                pass

        # Fallback: sort candidates by initial score
        sorted_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
        return sorted_candidates[:top_k]
